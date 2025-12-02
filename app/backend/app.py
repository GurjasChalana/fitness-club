import base64
import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from functools import wraps
from flask import Flask, jsonify, request, g
from flask_cors import CORS
from sqlalchemy import and_, func, or_
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_session, SessionLocal
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

load_dotenv()

from models import (
    Base,
    ClassRegistration,
    Equipment,
    FitnessGoal,
    GroupClass,
    HealthMetric,
    Invoice,
    InvoiceItem,
    MaintenanceLog,
    Member,
    Payment,
    PersonalTrainingSession,
    Room,
    Trainer,
    TrainerAvailability,
)

app = Flask(__name__)

# Basic auth defaults (override via env for demos if needed)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

# Allow local dev frontends (Vite on 5173, CRA on 3000) to call the API
default_origins = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173"
origins = [o for o in os.getenv("CORS_ORIGINS", default_origins).split(",") if o]
CORS(app, resources={r"/*": {"origins": origins}})


# ---- Helpers ----
def basic_auth_header():
    return {"WWW-Authenticate": 'Basic realm="Login required"'}


def parse_basic_auth_header():
    header = request.headers.get("Authorization")
    if not header or not header.startswith("Basic "):
        return None, None
    try:
        decoded = base64.b64decode(header.split(" ", 1)[1]).decode("utf-8")
        username, password = decoded.split(":", 1)
        return username, password
    except Exception:
        return None, None


def verify_credentials(username, password):
    """Return role context dict if credentials are valid, else None."""
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        return {"role": "admin", "username": username}

    session = SessionLocal()
    try:
        member = session.query(Member).filter(Member.username == username).first()
        if member and check_password_hash(member.password_hash, password):
            return {"role": "member", "member_id": member.member_id, "username": username}

        trainer = session.query(Trainer).filter(Trainer.username == username).first()
        if trainer and check_password_hash(trainer.password_hash, password):
            return {"role": "trainer", "trainer_id": trainer.trainer_id, "username": username}
    finally:
        session.close()
    return None


def require_role(*allowed_roles):
    """Decorator enforcing Basic Auth and optional role filtering."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            username, password = parse_basic_auth_header()
            if not username:
                return jsonify({"error": "Authentication required"}), 401, basic_auth_header()

            auth_ctx = verify_credentials(username, password)
            if not auth_ctx:
                return jsonify({"error": "Invalid credentials"}), 401, basic_auth_header()

            if allowed_roles and auth_ctx["role"] not in allowed_roles:
                return jsonify({"error": "Forbidden"}), 403

            g.current_auth = auth_ctx
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def decimal_to_float(val):
    if isinstance(val, Decimal):
        return float(val)
    return val


def member_dict(m: Member):
    return {
        "member_id": m.member_id,
        "first_name": m.first_name,
        "last_name": m.last_name,
        "username": m.username,
        "email": m.email,
        "date_of_birth": m.date_of_birth.isoformat() if m.date_of_birth else None,
        "gender": m.gender,
        "phone": m.phone,
    }


def trainer_dict(t: Trainer):
    return {
        "trainer_id": t.trainer_id,
        "first_name": t.first_name,
        "last_name": t.last_name,
        "full_name": f"{t.first_name} {t.last_name}",
        "username": t.username,
        "email": t.email,
        "certification": t.certification,
    }


def class_dict(c: GroupClass, enrolled=0):
    return {
        "class_id": c.class_id,
        "class_name": c.class_name,
        "class_time": c.class_time.isoformat(),
        "capacity": c.capacity,
        "trainer_id": c.trainer_id,
        "room_id": c.room_id,
        "status": c.status,
        "enrolled": enrolled,
        "trainer_name": f"{c.trainer.first_name} {c.trainer.last_name}" if c.trainer else None,
        "room_name": c.room.room_name if c.room else None,
    }


def pt_session_dict(pt: PersonalTrainingSession):
    return {
        "session_id": pt.session_id,
        "member_id": pt.member_id,
        "trainer_id": pt.trainer_id,
        "room_id": pt.room_id,
        "start_time": pt.start_time.isoformat(),
        "end_time": pt.end_time.isoformat(),
        "session_type": pt.session_type,
        "notes": pt.notes,
        "status": pt.status,
        "trainer_name": f"{pt.trainer.first_name} {pt.trainer.last_name}" if pt.trainer else None,
        "room_name": pt.room.room_name if pt.room else None,
        "member_name": f"{pt.member.first_name} {pt.member.last_name}" if pt.member else None,
    }


def invoice_to_dict(inv: Invoice):
    items = [
        {
            "item_id": it.item_id,
            "description": it.description,
            "quantity": it.quantity,
            "unit_price": decimal_to_float(it.unit_price),
        }
        for it in inv.items
    ]
    payments = [
        {
            "payment_id": p.payment_id,
            "amount": decimal_to_float(p.amount),
            "payment_method": p.payment_method,
            "status": p.status,
            "payment_date": p.payment_date.isoformat() if p.payment_date else None,
            "reference": p.reference,
        }
        for p in inv.payments
    ]
    return {
        "invoice_id": inv.invoice_id,
        "member_id": inv.member_id,
        "issue_date": inv.issue_date.isoformat() if inv.issue_date else None,
        "due_date": inv.due_date.isoformat() if inv.due_date else None,
        "total_amount": decimal_to_float(inv.total_amount),
        "status": inv.status,
        "notes": inv.notes,
        "items": items,
        "payments": payments,
        }


# ---- Auth introspection ----
@app.route("/auth/whoami", methods=["GET"])
@require_role("member", "trainer", "admin")
def whoami():
    return jsonify(g.current_auth)


# ---- Member endpoints ----
@app.route("/members/register", methods=["POST"])
def register_member():
    data = request.get_json()
    required = ["first_name", "last_name", "email", "username", "password"]
    if not all(data.get(r) for r in required):
        return jsonify({"error": "first_name, last_name, email, username, password are required"}), 400

    with get_session() as session:
        existing = (
            session.query(Member)
            .filter(or_(Member.email == data["email"], Member.username == data["username"]))
            .first()
        )
        if existing:
            return jsonify({"error": "email or username already exists"}), 400
        member = Member(
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            username=data["username"],
            password_hash=generate_password_hash(data["password"]),
            date_of_birth=data.get("date_of_birth"),
            gender=data.get("gender"),
            phone=data.get("phone"),
        )
        session.add(member)
        session.flush()
        return jsonify({"member_id": member.member_id}), 201


@app.route("/members/search", methods=["GET"])
@require_role("trainer", "admin")
def search_members():
    name = request.args.get("name")
    if not name:
        return jsonify({"error": "Name query required"}), 400

    like_pattern = f"%{name}%"
    with get_session() as session:
        members = (
            session.query(Member)
            .filter(or_(Member.first_name.ilike(like_pattern), Member.last_name.ilike(like_pattern)))
            .order_by(Member.last_name)
            .all()
        )
        return jsonify([member_dict(m) for m in members]), 200


@app.route("/members/<int:member_id>", methods=["GET"])
@require_role("member", "admin")
def get_member(member_id):
    auth = g.current_auth
    if auth["role"] == "member" and auth.get("member_id") != member_id:
        return jsonify({"error": "Forbidden"}), 403
    with get_session() as session:
        m = session.get(Member, member_id)
        if not m:
            return jsonify({"error": "Member not found"}), 404
        return jsonify(member_dict(m)), 200


@app.route("/members/<int:member_id>", methods=["PUT"], strict_slashes=False)
@require_role("member", "admin")
def update_member(member_id):
    auth = g.current_auth
    if auth["role"] == "member" and auth.get("member_id") != member_id:
        return jsonify({"error": "Forbidden"}), 403
    data = request.get_json()
    if not data:
        return jsonify({"error": "No fields provided"}), 400

    with get_session() as session:
        m = session.get(Member, member_id)
        if not m:
            return jsonify({"error": "Member not found"}), 404

        key, value = list(data.items())[0]
        if not hasattr(m, key):
            return jsonify({"error": f"Invalid field {key}"}), 400
        if key in ("email", "username"):
            exists = (
                session.query(Member)
                .filter(getattr(Member, key) == value, Member.member_id != member_id)
                .first()
            )
            if exists:
                return jsonify({"error": f"{key} already in use"}), 400
        setattr(m, key, value)
        session.flush()
        return jsonify(member_dict(m)), 200


@app.route("/members/<int:member_id>/goals", methods=["GET"])
@require_role("member", "admin")
def get_goals(member_id):
    auth = g.current_auth
    if auth["role"] == "member" and auth.get("member_id") != member_id:
        return jsonify({"error": "Forbidden"}), 403
    with get_session() as session:
        goals = (
            session.query(FitnessGoal)
            .filter(FitnessGoal.member_id == member_id)
            .all()
        )
        return jsonify(
            [
                {
                    "goal_id": g.goal_id,
                    "goal_type": g.goal_type,
                    "target_value": decimal_to_float(g.target_value),
                    "is_active": g.is_active,
                }
                for g in goals
            ]
        )


@app.route("/members/<int:member_id>/goals", methods=["POST"])
@require_role("member", "admin")
def add_goal(member_id):
    auth = g.current_auth
    if auth["role"] == "member" and auth.get("member_id") != member_id:
        return jsonify({"error": "Forbidden"}), 403
    data = request.get_json()
    if not data.get("goal_type") or data.get("target_value") is None:
        return jsonify({"error": "goal_type and target_value required"}), 400

    with get_session() as session:
        goal = FitnessGoal(
            member_id=member_id, goal_type=data["goal_type"], target_value=data["target_value"]
        )
        session.add(goal)
        session.flush()
        return (
            jsonify(
                {
                    "goal_id": goal.goal_id,
                    "goal_type": goal.goal_type,
                    "target_value": decimal_to_float(goal.target_value),
                    "is_active": goal.is_active,
                }
            ),
            201,
        )


@app.route("/members/<int:member_id>/goals/<int:goal_id>", methods=["PUT"])
@require_role("member", "admin")
def update_goal(member_id, goal_id):
    auth = g.current_auth
    if auth["role"] == "member" and auth.get("member_id") != member_id:
        return jsonify({"error": "Forbidden"}), 403
    data = request.get_json()
    with get_session() as session:
        goal = session.get(FitnessGoal, goal_id)
        if not goal or goal.member_id != member_id:
            return jsonify({"error": "Goal not found"}), 404
        if "goal_type" in data:
            goal.goal_type = data["goal_type"]
        if "target_value" in data and data["target_value"] is not None:
            goal.target_value = data["target_value"]
        if "is_active" in data:
            goal.is_active = bool(data["is_active"])
        session.flush()
        return jsonify(
            {
                "goal_id": goal.goal_id,
                "goal_type": goal.goal_type,
                "target_value": decimal_to_float(goal.target_value),
                "is_active": goal.is_active,
            }
        )


@app.route("/goals/<int:goal_id>", methods=["DELETE"])
@require_role("member", "admin")
def delete_goal(goal_id):
    auth = g.current_auth
    with get_session() as session:
        goal = session.get(FitnessGoal, goal_id)
        if not goal:
            return jsonify({"error": "Goal not found"}), 404
        if auth["role"] == "member" and auth.get("member_id") != goal.member_id:
            return jsonify({"error": "Forbidden"}), 403
        session.delete(goal)
        return jsonify({"message": "Goal deleted"})


@app.route("/members/<int:member_id>/health-metrics", methods=["GET"])
@require_role("member", "admin")
def get_health_metrics(member_id):
    auth = g.current_auth
    if auth["role"] == "member" and auth.get("member_id") != member_id:
        return jsonify({"error": "Forbidden"}), 403
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    with get_session() as session:
        query = session.query(HealthMetric).filter(HealthMetric.member_id == member_id)
        if start_date:
            query = query.filter(HealthMetric.recorded_at >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.filter(HealthMetric.recorded_at <= datetime.fromisoformat(end_date))
        metrics = query.order_by(HealthMetric.recorded_at.desc()).all()
        return (
            jsonify(
                [
                    {
                        "metric_id": m.metric_id,
                        "weight": decimal_to_float(m.weight),
                        "heart_rate": m.heart_rate,
                        "body_fat": decimal_to_float(m.body_fat),
                        "recorded_at": m.recorded_at.isoformat() if m.recorded_at else None,
                    }
                    for m in metrics
                ]
            ),
            200,
        )


@app.route("/members/<int:member_id>/health-metrics", methods=["POST"])
@require_role("member", "admin")
def add_health_metric(member_id):
    auth = g.current_auth
    if auth["role"] == "member" and auth.get("member_id") != member_id:
        return jsonify({"error": "Forbidden"}), 403
    data = request.get_json()
    with get_session() as session:
        metric = HealthMetric(
            member_id=member_id,
            weight=data.get("weight"),
            heart_rate=data.get("heart_rate"),
            body_fat=data.get("body_fat"),
        )
        session.add(metric)
        session.flush()
        return (
            jsonify(
                {
                    "metric_id": metric.metric_id,
                    "weight": decimal_to_float(metric.weight),
                    "heart_rate": metric.heart_rate,
                    "body_fat": decimal_to_float(metric.body_fat),
                    "recorded_at": metric.recorded_at.isoformat() if metric.recorded_at else None,
                }
            ),
            201,
        )


# ---- Class registration ----
@app.route("/classes/available", methods=["GET"])
@require_role("member", "trainer", "admin")
def get_available_classes():
    now = datetime.utcnow()
    with get_session() as session:
        classes = (
            session.query(
                GroupClass,
                func.count(ClassRegistration.member_id).label("enrolled"),
            )
            .outerjoin(ClassRegistration, GroupClass.class_id == ClassRegistration.class_id)
            .filter(GroupClass.class_time > now, GroupClass.status == "SCHEDULED")
            .group_by(GroupClass.class_id)
            .order_by(GroupClass.class_time)
            .all()
        )
        result = [class_dict(gc, enrolled=count) for gc, count in classes if count < gc.capacity]
        return jsonify(result), 200


@app.route("/members/<int:member_id>/classes", methods=["GET"])
@require_role("member", "admin")
def get_registered_classes(member_id):
    auth = g.current_auth
    if auth["role"] == "member" and auth.get("member_id") != member_id:
        return jsonify({"error": "Forbidden"}), 403
    with get_session() as session:
        classes = (
            session.query(GroupClass)
            .join(ClassRegistration, GroupClass.class_id == ClassRegistration.class_id)
            .filter(ClassRegistration.member_id == member_id)
            .order_by(GroupClass.class_time)
            .all()
        )
        return jsonify([class_dict(c) for c in classes]), 200


@app.route("/classes/register", methods=["POST"])
@require_role("member", "admin")
def register_for_class():
    data = request.get_json()
    member_id = data["member_id"]
    class_id = data["class_id"]
    auth = g.current_auth
    if auth["role"] == "member" and auth.get("member_id") != member_id:
        return jsonify({"error": "Forbidden"}), 403

    with get_session() as session:
        group_class = session.get(GroupClass, class_id)
        if not group_class or group_class.status != "SCHEDULED":
            return jsonify({"error": "Class not available"}), 400
        if group_class.class_time <= datetime.utcnow():
            return jsonify({"error": "Class is in the past"}), 400

        exists = (
            session.query(ClassRegistration)
            .filter(ClassRegistration.member_id == member_id, ClassRegistration.class_id == class_id)
            .first()
        )
        if exists:
            return jsonify({"error": "Already registered"}), 400

        enrolled = (
            session.query(func.count(ClassRegistration.member_id))
            .filter(ClassRegistration.class_id == class_id)
            .scalar()
        )
        if enrolled >= group_class.capacity:
            return jsonify({"error": "Class is full"}), 400

        if member_has_time_conflict(session, member_id, group_class.class_time):
            return jsonify({"error": "Schedule conflict with another class or PT session"}), 400

        session.add(ClassRegistration(member_id=member_id, class_id=class_id))
        return jsonify({"message": "Registered successfully"}), 201


@app.route("/classes/unregister", methods=["POST"])
@require_role("member", "admin")
def unregister_class():
    data = request.get_json()
    member_id = data["member_id"]
    class_id = data["class_id"]
    auth = g.current_auth
    if auth["role"] == "member" and auth.get("member_id") != member_id:
        return jsonify({"error": "Forbidden"}), 403
    with get_session() as session:
        reg = (
            session.query(ClassRegistration)
            .filter(ClassRegistration.member_id == member_id, ClassRegistration.class_id == class_id)
            .first()
        )
        if reg:
            session.delete(reg)
        return jsonify({"message": "Unregistered successfully"}), 200


# ---- Trainer endpoints ----
@app.route("/trainers", methods=["GET"])
@require_role("member", "trainer", "admin")
def get_trainers():
    with get_session() as session:
        trainers = session.query(Trainer).all()
        return jsonify([trainer_dict(t) for t in trainers]), 200


@app.route("/trainers/<int:trainer_id>", methods=["GET"])
@require_role("member", "trainer", "admin")
def get_trainer_by_id(trainer_id):
    with get_session() as session:
        t = session.get(Trainer, trainer_id)
        if not t:
            return jsonify({"error": "Trainer not found"}), 404
        return jsonify(trainer_dict(t)), 200


@app.route("/trainers/<int:trainer_id>/classes", methods=["GET"])
@require_role("trainer", "admin")
def get_trainer_classes(trainer_id):
    auth = g.current_auth
    if auth["role"] == "trainer" and auth.get("trainer_id") != trainer_id:
        return jsonify({"error": "Forbidden"}), 403
    with get_session() as session:
        classes = (
            session.query(GroupClass)
            .filter(GroupClass.trainer_id == trainer_id)
            .order_by(GroupClass.class_time)
            .all()
        )
        return jsonify([class_dict(c) for c in classes]), 200


@app.route("/trainers/<int:trainer_id>/schedule", methods=["GET"])
@require_role("trainer", "admin")
def get_trainer_schedule(trainer_id):
    auth = g.current_auth
    if auth["role"] == "trainer" and auth.get("trainer_id") != trainer_id:
        return jsonify({"error": "Forbidden"}), 403
    now = datetime.utcnow()
    with get_session() as session:
        pt_sessions = (
            session.query(PersonalTrainingSession)
            .filter(
                PersonalTrainingSession.trainer_id == trainer_id,
                PersonalTrainingSession.status == "SCHEDULED",
                PersonalTrainingSession.end_time >= now,
            )
            .order_by(PersonalTrainingSession.start_time)
            .all()
        )
        classes = (
            session.query(GroupClass)
            .filter(
                GroupClass.trainer_id == trainer_id,
                GroupClass.class_time >= now,
                GroupClass.status == "SCHEDULED",
            )
            .order_by(GroupClass.class_time)
            .all()
        )
        return jsonify(
            {
                "pt_sessions": [pt_session_dict(s) for s in pt_sessions],
                "classes": [class_dict(c) for c in classes],
            }
        )


@app.route("/trainers/<int:trainer_id>/availability", methods=["GET"])
@require_role("trainer", "admin")
def list_availability(trainer_id):
    auth = g.current_auth
    if auth["role"] == "trainer" and auth.get("trainer_id") != trainer_id:
        return jsonify({"error": "Forbidden"}), 403
    with get_session() as session:
        slots = (
            session.query(TrainerAvailability)
            .filter(TrainerAvailability.trainer_id == trainer_id)
            .order_by(TrainerAvailability.start_time)
            .all()
        )
        return jsonify(
            [
                {
                    "availability_id": a.availability_id,
                    "start_time": a.start_time.isoformat(),
                    "end_time": a.end_time.isoformat(),
                    "notes": a.notes,
                }
                for a in slots
            ]
        )


@app.route("/trainers/<int:trainer_id>/availability", methods=["POST"])
@require_role("trainer", "admin")
def create_availability(trainer_id):
    auth = g.current_auth
    if auth["role"] == "trainer" and auth.get("trainer_id") != trainer_id:
        return jsonify({"error": "Forbidden"}), 403
    data = request.get_json()
    start_time = datetime.fromisoformat(data["start_time"])
    end_time = datetime.fromisoformat(data["end_time"])
    if start_time >= end_time:
        return jsonify({"error": "start_time must be before end_time"}), 400

    with get_session() as session:
        overlap = (
            session.query(TrainerAvailability)
            .filter(
                TrainerAvailability.trainer_id == trainer_id,
                TrainerAvailability.start_time < end_time,
                TrainerAvailability.end_time > start_time,
            )
            .first()
        )
        if overlap:
            return jsonify({"error": "Availability overlaps existing slot"}), 400

        slot = TrainerAvailability(
            trainer_id=trainer_id,
            start_time=start_time,
            end_time=end_time,
            notes=data.get("notes"),
        )
        session.add(slot)
        session.flush()
        return jsonify({"availability_id": slot.availability_id}), 201


@app.route("/trainers/<int:trainer_id>/availability/<int:availability_id>", methods=["PUT"])
@require_role("trainer", "admin")
def update_availability(trainer_id, availability_id):
    auth = g.current_auth
    if auth["role"] == "trainer" and auth.get("trainer_id") != trainer_id:
        return jsonify({"error": "Forbidden"}), 403
    data = request.get_json()
    start_time = datetime.fromisoformat(data["start_time"])
    end_time = datetime.fromisoformat(data["end_time"])
    with get_session() as session:
        slot = session.get(TrainerAvailability, availability_id)
        if not slot or slot.trainer_id != trainer_id:
            return jsonify({"error": "Availability not found"}), 404

        overlap = (
            session.query(TrainerAvailability)
            .filter(
                TrainerAvailability.trainer_id == trainer_id,
                TrainerAvailability.availability_id != availability_id,
                TrainerAvailability.start_time < end_time,
                TrainerAvailability.end_time > start_time,
            )
            .first()
        )
        if overlap:
            return jsonify({"error": "Availability overlaps existing slot"}), 400

        slot.start_time = start_time
        slot.end_time = end_time
        slot.notes = data.get("notes")
        return jsonify({"message": "Updated"})


@app.route("/trainers/<int:trainer_id>/availability/<int:availability_id>", methods=["DELETE"])
@require_role("trainer", "admin")
def delete_availability(trainer_id, availability_id):
    auth = g.current_auth
    if auth["role"] == "trainer" and auth.get("trainer_id") != trainer_id:
        return jsonify({"error": "Forbidden"}), 403
    with get_session() as session:
        slot = session.get(TrainerAvailability, availability_id)
        if slot and slot.trainer_id == trainer_id:
            session.delete(slot)
            return jsonify({"message": "Deleted"})
        return jsonify({"error": "Availability not found"}), 404


# ---- PT Sessions (member + trainer) ----
def validate_pt_conflicts(session, member_id, trainer_id, room_id, start_time, end_time, exclude_session_id=None):
    active_filter = PersonalTrainingSession.status == "SCHEDULED"
    overlap = and_(PersonalTrainingSession.start_time < end_time, PersonalTrainingSession.end_time > start_time)
    if (
        session.query(PersonalTrainingSession)
        .filter(active_filter, overlap, PersonalTrainingSession.trainer_id == trainer_id)
        .filter(PersonalTrainingSession.session_id != exclude_session_id if exclude_session_id else True)
        .first()
    ):
        return "Trainer has a conflicting session"
    if (
        session.query(PersonalTrainingSession)
        .filter(active_filter, overlap, PersonalTrainingSession.member_id == member_id)
        .filter(PersonalTrainingSession.session_id != exclude_session_id if exclude_session_id else True)
        .first()
    ):
        return "Member has a conflicting session"
    if room_id:
        if (
            session.query(PersonalTrainingSession)
            .filter(active_filter, overlap, PersonalTrainingSession.room_id == room_id)
            .filter(PersonalTrainingSession.session_id != exclude_session_id if exclude_session_id else True)
            .first()
        ):
            return "Room is already booked"
    # Ensure trainer availability
    available = (
        session.query(TrainerAvailability)
        .filter(
            TrainerAvailability.trainer_id == trainer_id,
            TrainerAvailability.start_time <= start_time,
            TrainerAvailability.end_time >= end_time,
        )
        .first()
    )
    if not available:
        return "Trainer is not available in that interval"
    return None


def trainer_available_for_class(session, trainer_id, class_time):
    """Ensure trainer has a slot covering class_time."""
    return (
        session.query(TrainerAvailability)
        .filter(
            TrainerAvailability.trainer_id == trainer_id,
            TrainerAvailability.start_time <= class_time,
            TrainerAvailability.end_time >= class_time,
        )
        .first()
        is not None
    )


def member_has_time_conflict(session, member_id, class_time):
    """Check if member has overlapping class/PT within 1 hour window."""
    window_start = class_time - timedelta(hours=1)
    window_end = class_time + timedelta(hours=1)
    class_conflict = (
        session.query(ClassRegistration)
        .join(GroupClass, GroupClass.class_id == ClassRegistration.class_id)
        .filter(
            ClassRegistration.member_id == member_id,
            GroupClass.class_time >= window_start,
            GroupClass.class_time <= window_end,
            GroupClass.status == "SCHEDULED",
        )
        .first()
        is not None
    )
    pt_conflict = (
        session.query(PersonalTrainingSession)
        .filter(
            PersonalTrainingSession.member_id == member_id,
            PersonalTrainingSession.status == "SCHEDULED",
            PersonalTrainingSession.start_time < window_end,
            PersonalTrainingSession.end_time > window_start,
        )
        .first()
        is not None
    )
    return class_conflict or pt_conflict


def room_has_class_conflict(session, room_id, start_time, end_time, exclude_class_id=None):
    """Return True if the room is occupied by a class overlapping the interval."""
    if not room_id:
        return False
    classes = (
        session.query(GroupClass)
        .filter(
            GroupClass.room_id == room_id,
            GroupClass.status == "SCHEDULED",
            GroupClass.class_time < end_time,
        )
        .all()
    )
    for gc in classes:
        if exclude_class_id and gc.class_id == exclude_class_id:
            continue
        class_start = gc.class_time
        class_end = class_start + timedelta(hours=1)
        if class_start < end_time and class_end > start_time:
            return True
    return False


@app.route("/pt-sessions", methods=["POST"])
@require_role("member", "trainer", "admin")
def create_pt_session():
    data = request.get_json()
    auth = g.current_auth
    try:
        start_time = datetime.fromisoformat(data["start_time"])
        end_time = datetime.fromisoformat(data["end_time"])
    except Exception:
        return jsonify({"error": "Invalid datetime format"}), 400
    if start_time >= end_time:
        return jsonify({"error": "start_time must be before end_time"}), 400
    if auth["role"] == "member" and auth.get("member_id") != data.get("member_id"):
        return jsonify({"error": "Forbidden"}), 403
    if auth["role"] == "trainer" and auth.get("trainer_id") != data.get("trainer_id"):
        return jsonify({"error": "Forbidden"}), 403

    with get_session() as session:
        if end_time <= datetime.utcnow():
            return jsonify({"error": "Session must be in the future"}), 400
        if room_has_class_conflict(session, data.get("room_id"), start_time, end_time):
            return jsonify({"error": "Room has a scheduled class in that interval"}), 400
        conflict = validate_pt_conflicts(
            session,
            member_id=data["member_id"],
            trainer_id=data["trainer_id"],
            room_id=data.get("room_id"),
            start_time=start_time,
            end_time=end_time,
        )
        if conflict:
            return jsonify({"error": conflict}), 400

        pt = PersonalTrainingSession(
            member_id=data["member_id"],
            trainer_id=data["trainer_id"],
            room_id=data.get("room_id"),
            start_time=start_time,
            end_time=end_time,
            session_type=data.get("session_type"),
            notes=data.get("notes"),
            status="SCHEDULED",
        )
        session.add(pt)
        session.flush()
        return jsonify(pt_session_dict(pt)), 201


@app.route("/pt-sessions/<int:session_id>", methods=["PUT"])
@require_role("member", "trainer", "admin")
def reschedule_pt_session(session_id):
    data = request.get_json()
    start_time = datetime.fromisoformat(data["start_time"])
    end_time = datetime.fromisoformat(data["end_time"])

    with get_session() as session:
        pt = session.get(PersonalTrainingSession, session_id)
        if not pt:
            return jsonify({"error": "Session not found"}), 404
        auth = g.current_auth
        if auth["role"] == "member" and auth.get("member_id") != pt.member_id:
            return jsonify({"error": "Forbidden"}), 403
        if auth["role"] == "trainer" and auth.get("trainer_id") != pt.trainer_id:
            return jsonify({"error": "Forbidden"}), 403
        if end_time <= datetime.utcnow():
            return jsonify({"error": "Session must be in the future"}), 400
        if room_has_class_conflict(session, data.get("room_id", pt.room_id), start_time, end_time):
            return jsonify({"error": "Room has a scheduled class in that interval"}), 400
        conflict = validate_pt_conflicts(
            session,
            member_id=pt.member_id,
            trainer_id=pt.trainer_id,
            room_id=data.get("room_id", pt.room_id),
            start_time=start_time,
            end_time=end_time,
            exclude_session_id=session_id,
        )
        if conflict:
            return jsonify({"error": conflict}), 400

        pt.start_time = start_time
        pt.end_time = end_time
        pt.room_id = data.get("room_id", pt.room_id)
        pt.session_type = data.get("session_type", pt.session_type)
        pt.notes = data.get("notes", pt.notes)
        return jsonify(pt_session_dict(pt)), 200


@app.route("/pt-sessions/<int:session_id>", methods=["DELETE"])
@require_role("member", "trainer", "admin")
def cancel_pt_session(session_id):
    with get_session() as session:
        pt = session.get(PersonalTrainingSession, session_id)
        if not pt:
            return jsonify({"error": "Session not found"}), 404
        auth = g.current_auth
        if auth["role"] == "member" and auth.get("member_id") != pt.member_id:
            return jsonify({"error": "Forbidden"}), 403
        if auth["role"] == "trainer" and auth.get("trainer_id") != pt.trainer_id:
            return jsonify({"error": "Forbidden"}), 403
        pt.status = "CANCELLED"
        return jsonify({"message": "Session cancelled"})


@app.route("/members/<int:member_id>/pt-sessions", methods=["GET"])
@require_role("member", "admin")
def member_pt_sessions(member_id):
    auth = g.current_auth
    if auth["role"] == "member" and auth.get("member_id") != member_id:
        return jsonify({"error": "Forbidden"}), 403
    now = datetime.utcnow()
    with get_session() as session:
        pts = (
            session.query(PersonalTrainingSession)
            .filter(PersonalTrainingSession.member_id == member_id, PersonalTrainingSession.end_time >= now)
            .order_by(PersonalTrainingSession.start_time)
            .all()
        )
        return jsonify([pt_session_dict(pt) for pt in pts])


# ---- Admin/general endpoints ----
@app.route("/rooms", methods=["GET"])
@require_role("member", "trainer", "admin")
def list_rooms():
    with get_session() as session:
        rooms = session.query(Room).order_by(Room.room_name).all()
        return jsonify(
            [{"room_id": r.room_id, "room_name": r.room_name, "capacity": r.capacity} for r in rooms]
        )


@app.route("/admin/rooms", methods=["POST"])
@require_role("admin")
def create_room():
    data = request.get_json()
    with get_session() as session:
        room = Room(room_name=data["room_name"], capacity=data["capacity"])
        session.add(room)
        session.flush()
        return jsonify({"room_id": room.room_id}), 201


@app.route("/admin/rooms/<int:room_id>", methods=["PUT"])
@require_role("admin")
def update_room(room_id):
    data = request.get_json()
    with get_session() as session:
        room = session.get(Room, room_id)
        if not room:
            return jsonify({"error": "Room not found"}), 404
        room.room_name = data.get("room_name", room.room_name)
        room.capacity = data.get("capacity", room.capacity)
        return jsonify({"message": "Updated"})


@app.route("/admin/rooms/<int:room_id>", methods=["DELETE"])
@require_role("admin")
def delete_room(room_id):
    with get_session() as session:
        room = session.get(Room, room_id)
        if room:
            session.delete(room)
            return jsonify({"message": "Deleted"})
        return jsonify({"error": "Room not found"}), 404


@app.route("/admin/classes", methods=["GET"])
@require_role("admin")
def admin_list_classes():
    with get_session() as session:
        classes = session.query(GroupClass).order_by(GroupClass.class_time).all()
        return jsonify([class_dict(c) for c in classes])


@app.route("/admin/classes", methods=["POST"])
@require_role("admin")
def admin_create_class():
    data = request.get_json()
    with get_session() as session:
        class_time = datetime.fromisoformat(data["class_time"])
        if class_time <= datetime.utcnow():
            return jsonify({"error": "Class time must be in the future"}), 400
        trainer_id = data.get("trainer_id")
        if trainer_id and not trainer_available_for_class(session, trainer_id, class_time):
            return jsonify({"error": "Trainer not available at that time"}), 400
        room_id = data.get("room_id")
        class_end = class_time + timedelta(hours=1)
        pt_conflict = (
            session.query(PersonalTrainingSession)
            .filter(
                PersonalTrainingSession.room_id == room_id,
                PersonalTrainingSession.status == "SCHEDULED",
                PersonalTrainingSession.start_time < class_end,
                PersonalTrainingSession.end_time > class_time,
            )
            .first()
            if room_id
            else None
        )
        if pt_conflict:
            return jsonify({"error": "Room has a PT session in that interval"}), 400
        gc = GroupClass(
            class_name=data["class_name"],
            trainer_id=trainer_id,
            room_id=room_id,
            class_time=class_time,
            capacity=data.get("capacity", 10),
            status=data.get("status", "SCHEDULED"),
        )
        session.add(gc)
        session.flush()
        return jsonify({"class_id": gc.class_id}), 201


@app.route("/admin/classes/<int:class_id>", methods=["PUT"])
@require_role("admin")
def admin_update_class(class_id):
    data = request.get_json()
    with get_session() as session:
        gc = session.get(GroupClass, class_id)
        if not gc:
            return jsonify({"error": "Class not found"}), 404
        new_time = datetime.fromisoformat(data["class_time"]) if "class_time" in data else gc.class_time
        trainer_id = data.get("trainer_id", gc.trainer_id)
        if new_time <= datetime.utcnow():
            return jsonify({"error": "Class time must be in the future"}), 400
        if trainer_id and not trainer_available_for_class(session, trainer_id, new_time):
            return jsonify({"error": "Trainer not available at that time"}), 400
        new_room_id = data.get("room_id", gc.room_id)
        class_end = new_time + timedelta(hours=1)
        pt_conflict = (
            session.query(PersonalTrainingSession)
            .filter(
                PersonalTrainingSession.room_id == new_room_id,
                PersonalTrainingSession.status == "SCHEDULED",
                PersonalTrainingSession.start_time < class_end,
                PersonalTrainingSession.end_time > new_time,
            )
            .first()
            if new_room_id
            else None
        )
        if pt_conflict:
            return jsonify({"error": "Room has a PT session in that interval"}), 400
        if "class_name" in data:
            gc.class_name = data["class_name"]
        if "trainer_id" in data:
            gc.trainer_id = data["trainer_id"]
        if "room_id" in data:
            gc.room_id = data["room_id"]
        if "class_time" in data:
            gc.class_time = new_time
        if "capacity" in data:
            gc.capacity = data["capacity"]
        if "status" in data:
            gc.status = data["status"]
        return jsonify({"message": "Updated"})


@app.route("/admin/classes/<int:class_id>/cancel", methods=["POST"])
@require_role("admin")
def admin_cancel_class(class_id):
    with get_session() as session:
        gc = session.get(GroupClass, class_id)
        if not gc:
            return jsonify({"error": "Class not found"}), 404
        gc.status = "CANCELLED"
        return jsonify({"message": "Cancelled"})


@app.route("/admin/equipment", methods=["GET"])
@require_role("admin")
def list_equipment():
    with get_session() as session:
        items = session.query(Equipment).all()
        return jsonify(
            [
                {
                    "equipment_id": e.equipment_id,
                    "equipment_name": e.equipment_name,
                    "status": e.status,
                    "room_id": e.room_id,
                }
                for e in items
            ]
        )


@app.route("/admin/equipment", methods=["POST"])
@require_role("admin")
def create_equipment():
    data = request.get_json()
    with get_session() as session:
        eq = Equipment(
            room_id=data.get("room_id"),
            equipment_name=data["equipment_name"],
            status=data.get("status", "OPERATIONAL"),
        )
        session.add(eq)
        session.flush()
        return jsonify({"equipment_id": eq.equipment_id}), 201


@app.route("/admin/maintenance", methods=["GET"])
@require_role("admin")
def list_maintenance():
    with get_session() as session:
        logs = session.query(MaintenanceLog).order_by(MaintenanceLog.created_at.desc()).all()
        return jsonify(
            [
                {
                    "log_id": l.log_id,
                    "equipment_id": l.equipment_id,
                    "issue_description": l.issue_description,
                    "status": l.status,
                    "created_at": l.created_at.isoformat() if l.created_at else None,
                    "resolved_timestamp": l.resolved_timestamp.isoformat() if l.resolved_timestamp else None,
                    "resolution_notes": l.resolution_notes,
                }
                for l in logs
            ]
        )


@app.route("/admin/equipment/<int:equipment_id>/maintenance", methods=["POST"])
@require_role("admin")
def create_maintenance(equipment_id):
    data = request.get_json()
    with get_session() as session:
        log = MaintenanceLog(
            equipment_id=equipment_id,
            issue_description=data.get("issue_description"),
            status=data.get("status", "OPEN"),
        )
        session.add(log)
        session.flush()
        return jsonify({"log_id": log.log_id}), 201


@app.route("/admin/maintenance/<int:log_id>", methods=["PUT"])
@require_role("admin")
def update_maintenance(log_id):
    data = request.get_json()
    with get_session() as session:
        log = session.get(MaintenanceLog, log_id)
        if not log:
            return jsonify({"error": "Log not found"}), 404
        log.status = data.get("status", log.status)
        log.resolution_notes = data.get("resolution_notes", log.resolution_notes)
        if log.status.upper() == "RESOLVED" and not log.resolved_timestamp:
            log.resolved_timestamp = datetime.utcnow()
        return jsonify({"message": "Updated"})


# ---- Billing ----
@app.route("/admin/invoices", methods=["GET"])
@require_role("admin")
def list_invoices():
    with get_session() as session:
        invoices = session.query(Invoice).all()
        return jsonify([invoice_to_dict(inv) for inv in invoices])


@app.route("/admin/invoices", methods=["POST"])
@require_role("admin")
def create_invoice():
    data = request.get_json()
    items = data.get("items", [])
    if not items:
        return jsonify({"error": "At least one line item required"}), 400

    with get_session() as session:
        invoice = Invoice(
            member_id=data["member_id"],
            due_date=data.get("due_date"),
            notes=data.get("notes"),
            status="UNPAID",
        )
        session.add(invoice)
        session.flush()

        total = Decimal("0")
        for item in items:
            qty = item.get("quantity", 1)
            price = Decimal(str(item["unit_price"]))
            total += price * qty
            session.add(
                InvoiceItem(
                    invoice_id=invoice.invoice_id,
                    description=item.get("description"),
                    quantity=qty,
                    unit_price=price,
                )
            )
        invoice.total_amount = total
        session.flush()
        return jsonify(invoice_to_dict(invoice)), 201


@app.route("/admin/invoices/<int:invoice_id>/payments", methods=["POST"])
@require_role("admin")
def create_payment(invoice_id):
    data = request.get_json()
    amount = Decimal(str(data["amount"]))
    with get_session() as session:
        inv = session.get(Invoice, invoice_id)
        if not inv:
            return jsonify({"error": "Invoice not found"}), 404

        paid_so_far = (
            session.query(func.coalesce(func.sum(Payment.amount), 0))
            .filter(Payment.invoice_id == invoice_id)
            .scalar()
        )
        if paid_so_far + amount > inv.total_amount:
            return jsonify({"error": "Payment exceeds invoice total"}), 400

        payment = Payment(
            invoice_id=invoice_id,
            amount=amount,
            payment_method=data.get("payment_method", "CASH"),
            status="SUCCESS",
            reference=data.get("reference"),
        )
        session.add(payment)

        new_total = paid_so_far + amount
        if new_total == inv.total_amount:
            inv.status = "PAID"
        else:
            inv.status = "PARTIAL"

        session.flush()
        return jsonify(invoice_to_dict(inv)), 201


@app.route("/members/<int:member_id>/invoices", methods=["GET"])
@require_role("member", "admin")
def member_invoices(member_id):
    auth = g.current_auth
    if auth["role"] == "member" and auth.get("member_id") != member_id:
        return jsonify({"error": "Forbidden"}), 403
    with get_session() as session:
        invoices = session.query(Invoice).filter(Invoice.member_id == member_id).all()
        return jsonify([invoice_to_dict(inv) for inv in invoices])


@app.route("/members/<int:member_id>/invoices/<int:invoice_id>/payments", methods=["POST"])
@require_role("member", "admin")
def member_pay_invoice(member_id, invoice_id):
    auth = g.current_auth
    if auth["role"] == "member" and auth.get("member_id") != member_id:
        return jsonify({"error": "Forbidden"}), 403
    data = request.get_json()
    amount = Decimal(str(data["amount"]))
    with get_session() as session:
        inv = session.get(Invoice, invoice_id)
        if not inv or inv.member_id != member_id:
            return jsonify({"error": "Invoice not found"}), 404
        paid_so_far = (
            session.query(func.coalesce(func.sum(Payment.amount), 0))
            .filter(Payment.invoice_id == invoice_id)
            .scalar()
        )
        if paid_so_far + amount > inv.total_amount:
            return jsonify({"error": "Payment exceeds invoice total"}), 400

        payment = Payment(
            invoice_id=invoice_id,
            amount=amount,
            payment_method=data.get("payment_method", "CARD"),
            status="SUCCESS",
            reference=data.get("reference"),
        )
        session.add(payment)

        new_total = paid_so_far + amount
        inv.status = "PAID" if new_total == inv.total_amount else "PARTIAL"
        session.flush()
        return jsonify(invoice_to_dict(inv)), 201


# ---- Member dashboard summary ----
@app.route("/members/<int:member_id>/dashboard", methods=["GET"])
@require_role("member", "admin")
def member_dashboard(member_id):
    auth = g.current_auth
    if auth["role"] == "member" and auth.get("member_id") != member_id:
        return jsonify({"error": "Forbidden"}), 403
    with get_session() as session:
        member = session.get(Member, member_id)
        if not member:
            return jsonify({"error": "Member not found"}), 404

        last_metric = (
            session.query(HealthMetric)
            .filter(HealthMetric.member_id == member_id)
            .order_by(HealthMetric.recorded_at.desc())
            .first()
        )
        active_goals = (
            session.query(FitnessGoal).filter(FitnessGoal.member_id == member_id, FitnessGoal.is_active.is_(True)).count()
        )
        upcoming_classes = (
            session.query(GroupClass)
            .join(ClassRegistration, GroupClass.class_id == ClassRegistration.class_id)
            .filter(ClassRegistration.member_id == member_id, GroupClass.class_time >= datetime.utcnow())
            .count()
        )
        past_classes = (
            session.query(ClassRegistration)
            .join(GroupClass, GroupClass.class_id == ClassRegistration.class_id)
            .filter(
                ClassRegistration.member_id == member_id,
                GroupClass.class_time < datetime.utcnow(),
                GroupClass.status == "SCHEDULED",
            )
            .count()
        )
        upcoming_sessions = (
            session.query(PersonalTrainingSession)
            .filter(
                PersonalTrainingSession.member_id == member_id,
                PersonalTrainingSession.start_time >= datetime.utcnow(),
                PersonalTrainingSession.status == "SCHEDULED",
            )
            .count()
        )
        past_sessions = (
            session.query(PersonalTrainingSession)
            .filter(
                PersonalTrainingSession.member_id == member_id,
                PersonalTrainingSession.end_time < datetime.utcnow(),
                PersonalTrainingSession.status == "SCHEDULED",
            )
            .count()
        )

        # Simple progress: count of completed goals vs active
        total_goals = session.query(FitnessGoal).filter(FitnessGoal.member_id == member_id).count()
        active_goals = session.query(FitnessGoal).filter(FitnessGoal.member_id == member_id, FitnessGoal.is_active.is_(True)).count()
        completed_goals = total_goals - active_goals

        return jsonify(
            {
                "member": member_dict(member),
                "active_goals": active_goals,
                "completed_goals": completed_goals,
                "latest_metric": {
                    "recorded_at": last_metric.recorded_at.isoformat() if last_metric else None,
                    "weight": decimal_to_float(last_metric.weight) if last_metric else None,
                    "heart_rate": last_metric.heart_rate if last_metric else None,
                    "body_fat": decimal_to_float(last_metric.body_fat) if last_metric else None,
                }
                if last_metric
                else None,
                "upcoming_class_count": upcoming_classes,
                "past_class_count": past_classes,
                "upcoming_pt_session_count": upcoming_sessions,
                "past_pt_session_count": past_sessions,
            }
        )


# ---- Trainer member lookup with context ----
@app.route("/trainers/<int:trainer_id>/members/search", methods=["GET"])
@require_role("trainer", "admin")
def trainer_member_lookup(trainer_id):
    auth = g.current_auth
    if auth["role"] == "trainer" and auth.get("trainer_id") != trainer_id:
        return jsonify({"error": "Forbidden"}), 403
    name = request.args.get("name", "")
    like_pattern = f"%{name}%"
    with get_session() as session:
        # Limit to members that have a PT session or class with this trainer (assigned context)
        member_ids_subq = (
            session.query(ClassRegistration.member_id.label("member_id"))
            .join(GroupClass, GroupClass.class_id == ClassRegistration.class_id)
            .filter(GroupClass.trainer_id == trainer_id)
            .union(
                session.query(PersonalTrainingSession.member_id.label("member_id")).filter(
                    PersonalTrainingSession.trainer_id == trainer_id
                )
            )
        ).subquery().alias("member_ids_subq")
        members = (
            session.query(Member)
            .filter(
                Member.member_id.in_(session.query(member_ids_subq.c.member_id)),
                or_(Member.first_name.ilike(like_pattern), Member.last_name.ilike(like_pattern)),
            )
            .all()
        )
        result = []
        for m in members:
            last_metric = (
                session.query(HealthMetric)
                .filter(HealthMetric.member_id == m.member_id)
                .order_by(HealthMetric.recorded_at.desc())
                .first()
            )
            primary_goal = (
                session.query(FitnessGoal.goal_type)
                .filter(FitnessGoal.member_id == m.member_id, FitnessGoal.is_active.is_(True))
                .first()
            )
            last_class = (
                session.query(GroupClass.class_name, GroupClass.class_time)
                .join(ClassRegistration, ClassRegistration.class_id == GroupClass.class_id)
                .filter(ClassRegistration.member_id == m.member_id, GroupClass.trainer_id == trainer_id)
                .order_by(GroupClass.class_time.desc())
                .first()
            )
            result.append(
                {
                    "member_id": m.member_id,
                    "first_name": m.first_name,
                    "last_name": m.last_name,
                    "email": m.email,
                    "primary_goal": primary_goal[0] if primary_goal else None,
                    "last_metric": {
                        "recorded_at": last_metric.recorded_at.isoformat() if last_metric else None,
                        "weight": decimal_to_float(last_metric.weight) if last_metric else None,
                        "heart_rate": last_metric.heart_rate if last_metric else None,
                        "body_fat": decimal_to_float(last_metric.body_fat) if last_metric else None,
                    }
                    if last_metric
                    else None,
                    "last_class": {
                        "class_name": last_class.class_name,
                        "class_time": last_class.class_time.isoformat(),
                    }
                    if last_class
                    else None,
                }
            )
        return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)
