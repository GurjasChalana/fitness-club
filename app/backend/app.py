from flask import Flask, jsonify, request
from flask_cors import CORS
from db import execute_query

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

# POST endpoint to create a new member
@app.route("/members/register", methods=["POST"])
def register_member():
    data = request.get_json()
    query = """
        INSERT INTO members (first_name, last_name, email, date_of_birth, gender, phone)
        VALUES (%s, %s, %s, %s, %s, %s) RETURNING member_id;
    """
    params = (
        data["first_name"],
        data["last_name"],
        data["email"],
        data.get("date_of_birth"),
        data.get("gender"),
        data.get("phone")
    )
    member_id = execute_query(query, params=params, fetch=True)
    return jsonify({"member_id": member_id[0]["member_id"]}), 201

@app.route("/members/search", methods=["GET"])
def search_members():
    name = request.args.get("name")

    if not name:
        return jsonify({"error": "Name query required"}), 400

    query = """
        SELECT member_id, first_name, last_name, email
        FROM members
        WHERE 
            first_name ILIKE %s
            OR last_name ILIKE %s
        ORDER BY last_name;
    """

    like_pattern = f"%{name}%"
    members = execute_query(query, (like_pattern, like_pattern), fetch=True)

    return jsonify(members), 200

@app.route("/members/<int:member_id>", methods=["GET"])
def get_member(member_id):
    try:
        query = "SELECT member_id, first_name, last_name, email, date_of_birth, gender, phone FROM members WHERE member_id = %s;"
        result = execute_query(query, params=(member_id,), fetch=True)
        if result:
            return jsonify(result[0]), 200
        else:
            return jsonify({"error": "Member not found"}), 404
    except Exception as e:
        print("Error fetching member:", e)
        return jsonify({"error": str(e)}), 400


@app.route("/members/<int:member_id>", methods=["PUT"], strict_slashes=False)
def update_member(member_id):
    data = request.get_json()
    key, value = list(data.items())[0]  
    query = f"UPDATE members SET {key} = %s WHERE member_id = %s RETURNING *;"
    result = execute_query(query, params=(value, member_id), fetch=True)
    if result:
        return jsonify(result[0]), 200  #
    return jsonify({"error": "Member not found"}), 404


@app.route("/members/<int:member_id>/goals", methods=["GET"])
def get_goals(member_id):
    query = "SELECT * FROM fitness_goals WHERE member_id = %s AND is_active = TRUE;"
    goals = execute_query(query, params=(member_id,), fetch=True)
    return jsonify(goals)


@app.route("/members/<int:member_id>/goals", methods=["POST"])
def add_goal(member_id):
    data = request.get_json()
    query = """
        INSERT INTO fitness_goals (member_id, goal_type, target_value)
        VALUES (%s, %s, %s)
        RETURNING *;
    """
    params = (member_id, data["goal_type"], data["target_value"])
    goal = execute_query(query, params=params, fetch=True)
    return jsonify(goal[0])


@app.route("/goals/<int:goal_id>", methods=["DELETE"])
def delete_goal(goal_id):
    query = "DELETE FROM fitness_goals WHERE goal_id = %s;"
    execute_query(query, params=(goal_id,))
    return jsonify({"message": "Goal deleted"})

@app.route("/members/<int:member_id>/health-metrics", methods=["GET"])
def get_health_metrics(member_id):
    query = """
        SELECT metric_id, weight, heart_rate, body_fat, recorded_at
        FROM health_metrics
        WHERE member_id = %s
        ORDER BY recorded_at DESC;
    """

    metrics = execute_query(query, params=(member_id,), fetch=True)
    return jsonify(metrics), 200


@app.route("/members/<int:member_id>/health-metrics", methods=["POST"])
def add_health_metric(member_id):
    data = request.get_json()

    query = """
        INSERT INTO health_metrics (member_id, weight, heart_rate, body_fat)
        VALUES (%s, %s, %s, %s)
        RETURNING *;
    """

    params = (
        member_id,
        data.get("weight"),
        data.get("heart_rate"),
        data.get("body_fat")
    )

    metric = execute_query(query, params=params, fetch=True)
    return jsonify(metric[0]), 201

@app.route("/classes/available", methods=["GET"])
def get_available_classes():
    query = """
        SELECT 
            gc.class_id,
            gc.class_name,
            gc.class_time,
            gc.capacity,
            CONCAT(t.first_name, ' ', t.last_name) AS trainer_name,
            COUNT(cr.member_id) AS enrolled
        FROM group_classes gc
        LEFT JOIN class_registrations cr ON gc.class_id = cr.class_id
        LEFT JOIN trainers t ON gc.trainer_id = t.trainer_id
        WHERE gc.class_time > NOW()
        GROUP BY gc.class_id, gc.class_name, gc.class_time, gc.capacity, t.first_name, t.last_name
        HAVING COUNT(cr.member_id) < gc.capacity
        ORDER BY gc.class_time;
    """
    classes = execute_query(query, fetch=True)
    return jsonify(classes), 200

@app.route("/members/<int:member_id>/classes", methods=["GET"])
def get_registered_classes(member_id):
    query = """
        SELECT gc.class_id, gc.class_name, gc.class_time, r.room_name, 
               CONCAT(t.first_name, ' ', t.last_name) AS trainer_name
        FROM class_registrations cr
        JOIN group_classes gc ON cr.class_id = gc.class_id
        JOIN trainers t ON gc.trainer_id = t.trainer_id
        JOIN rooms r ON gc.room_id = r.room_id
        WHERE cr.member_id = %s
        ORDER BY gc.class_time;
    """
    classes = execute_query(query, (member_id,), fetch=True)
    return jsonify(classes), 200


@app.route("/classes/register", methods=["POST"])
def register_for_class():
    data = request.get_json()
    member_id = data["member_id"]
    class_id = data["class_id"]

    # Prevent duplicate registration
    check_query = """
        SELECT 1 FROM class_registrations
        WHERE member_id = %s AND class_id = %s;
    """
    exists = execute_query(check_query, (member_id, class_id), fetch=True)
    if exists:
        return jsonify({"error": "Already registered"}), 400

    # Ensure class is not full
    capacity_query = """
        SELECT capacity,
               COUNT(cr.member_id) AS enrolled
        FROM group_classes gc
        LEFT JOIN class_registrations cr
            ON gc.class_id = cr.class_id
        WHERE gc.class_id = %s
        GROUP BY capacity;
    """
    result = execute_query(capacity_query, (class_id,), fetch=True)
    if not result or result[0]["enrolled"] >= result[0]["capacity"]:
        return jsonify({"error": "Class is full"}), 400

    insert_query = """
        INSERT INTO class_registrations (member_id, class_id)
        VALUES (%s, %s);
    """
    execute_query(insert_query, (member_id, class_id))

    return jsonify({"message": "Registered successfully"}), 201

@app.route("/classes/unregister", methods=["POST"])
def unregister_class():
    data = request.get_json()
    member_id = data["member_id"]
    class_id = data["class_id"]
    query = "DELETE FROM class_registrations WHERE member_id = %s AND class_id = %s;"
    execute_query(query, (member_id, class_id))
    return jsonify({"message": "Unregistered successfully"}), 200

# trainers

@app.route("/trainers/<int:trainer_id>", methods=["GET"])
def get_trainer_by_id(trainer_id):
    query = """
        SELECT trainer_id, first_name, last_name, certification, email
        FROM trainers
        WHERE trainer_id = %s;
    """
    result = execute_query(query, (trainer_id,), fetch=True)
    if result:
        return jsonify(result[0]), 200
    return jsonify({"error": "Trainer not found"}), 404

@app.route("/trainers", methods=["GET"])
def get_trainers():
    query = """
        SELECT 
            trainer_id,
            CONCAT(first_name, ' ', last_name) AS full_name,
            certification
        FROM trainers;
    """
    trainers = execute_query(query, fetch=True)
    return jsonify(trainers), 200

@app.route("/trainers/<int:trainer_id>/classes", methods=["GET"])
def get_trainer_classes(trainer_id):
    query = """
        SELECT 
            gc.class_id,
            gc.class_name,
            gc.class_time,
            r.room_name
        FROM group_classes gc
        JOIN rooms r ON gc.room_id = r.room_id
        WHERE gc.trainer_id = %s
        ORDER BY gc.class_time;
    """
    classes = execute_query(query, (trainer_id,), fetch=True)
    return jsonify(classes), 200


if __name__ == "__main__":
    app.run(debug=True)

