import React, { useState, useEffect } from "react";

function MemberPage() {
  const [form, setForm] = useState({
    first_name: "", last_name: "", email: "", date_of_birth: "", gender: "", phone: ""
  });
  const [memberId, setMemberId] = useState(null);
  const [memberData, setMemberData] = useState(null);
  const [editingField, setEditingField] = useState(null);
  const [editValue, setEditValue] = useState("");
  const [goals, setGoals] = useState([]);
  const [newGoal, setNewGoal] = useState({ goal_type: "", target_value: "" });
  const [metrics, setMetrics] = useState([]);
  const [newMetric, setNewMetric] = useState({ weight: "", heart_rate: "", body_fat: "" });

  // Classes
  const [availableClasses, setAvailableClasses] = useState([]);
  const [registeredClasses, setRegisteredClasses] = useState([]);

  useEffect(() => {
    const savedMemberId = localStorage.getItem("memberId");
    if (savedMemberId) {
      setMemberId(savedMemberId);
      fetchMemberDetails(savedMemberId);
      fetchGoals(savedMemberId);
      fetchMetrics(savedMemberId);
      fetchAvailableClasses();
      fetchRegisteredClasses(savedMemberId);
    }
  }, []);

  // Member details
  const fetchMemberDetails = async (id) => {
    const res = await fetch(`http://127.0.0.1:5000/members/${id}`);
    const data = await res.json();
    setMemberData(data);
  };
  const handleChange = e => setForm({ ...form, [e.target.name]: e.target.value });
  const registerMember = async e => {
    e.preventDefault();
    const res = await fetch("http://127.0.0.1:5000/members/register", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(form)
    });
    const data = await res.json();
    setMemberId(data.member_id);
    localStorage.setItem("memberId", data.member_id);
    fetchMemberDetails(data.member_id);
    fetchRegisteredClasses(data.member_id);
  };
  const updateField = async field => {
    const res = await fetch(`http://127.0.0.1:5000/members/${memberId}`, {
      method: "PUT", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ [field]: editValue })
    });
    const data = await res.json();
    setMemberData(data);
    setEditingField(null);
  };

  // Fitness goals
  const fetchGoals = async id => {
    const res = await fetch(`http://127.0.0.1:5000/members/${id}/goals`);
    const data = await res.json();
    setGoals(data);
  };
  const addGoal = async () => {
    await fetch(`http://127.0.0.1:5000/members/${memberId}/goals`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(newGoal)
    });
    setNewGoal({ goal_type: "", target_value: "" });
    fetchGoals(memberId);
  };
  const deleteGoal = async id => {
    await fetch(`http://127.0.0.1:5000/goals/${id}`, { method: "DELETE" });
    fetchGoals(memberId);
  };

  // Health metrics
  const fetchMetrics = async id => {
    const res = await fetch(`http://127.0.0.1:5000/members/${id}/health-metrics`);
    const data = await res.json();
    setMetrics(data);
  };
  const addMetric = async () => {
    await fetch(`http://127.0.0.1:5000/members/${memberId}/health-metrics`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(newMetric)
    });
    setNewMetric({ weight: "", heart_rate: "", body_fat: "" });
    fetchMetrics(memberId);
  };

  // Classes
  const fetchAvailableClasses = async () => {
    const res = await fetch(`http://127.0.0.1:5000/classes/available`);
    const data = await res.json();
    setAvailableClasses(data);
  };
  const fetchRegisteredClasses = async (id) => {
    const res = await fetch(`http://127.0.0.1:5000/members/${id}/classes`);
    const data = await res.json();
    setRegisteredClasses(data);
  };
  const registerClass = async (class_id) => {
    await fetch(`http://127.0.0.1:5000/classes/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ member_id: memberId, class_id })
    });
    fetchAvailableClasses();
    fetchRegisteredClasses(memberId);
  };
  const unregisterClass = async (class_id) => {
    await fetch(`http://127.0.0.1:5000/classes/unregister`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ member_id: memberId, class_id })
    });
    fetchAvailableClasses();
    fetchRegisteredClasses(memberId);
  };

  // Render registration form
  if (!memberId) return (
    <div>
      <h1>Register</h1>
      <form onSubmit={registerMember}>
        {Object.keys(form).map(key => (
          <input
            key={key} name={key} placeholder={key.replace("_", " ")} value={form[key]} onChange={handleChange} />
        ))}
        <button type="submit">Register</button>
      </form>
    </div>
  );

  if (!memberData) return <p>Loading...</p>;

  return (
    <div style={{ padding: "20px" }}>
      <h1>Welcome, {memberData.first_name}</h1>

      {/* Personal Details */}
      {["first_name","last_name","email","date_of_birth","gender","phone"].map(field => (
        <p key={field} style={{ marginBottom: 10 }}>
          <strong>{field.replace("_"," ")}:</strong>{" "}
          {editingField === field ? (
            <>
              <input autoFocus value={editValue} onChange={e => setEditValue(e.target.value)} />
              <button type="button" onClick={() => updateField(field)} style={{ marginLeft: 8 }}>Save</button>
              <button type="button" onClick={() => setEditingField(null)} style={{ marginLeft: 4 }}>Cancel</button>
            </>
          ) : (
            <>
              {memberData[field] || "N/A"}
              <button type="button" onClick={() => {setEditingField(field); setEditValue(memberData[field] || "")}} style={{ marginLeft: 12 }}>
                Update
              </button>
            </>
          )}
        </p>
      ))}

      <hr style={{ border: "1px solid #ccc", margin: "20px 0" }} />

      {/* Fitness Goals */}
      <h2>Fitness Goals</h2>
      <input placeholder="Goal Type" value={newGoal.goal_type} onChange={e => setNewGoal({...newGoal, goal_type:e.target.value})} style={{ marginRight: 8 }}/>
      <input type="number" placeholder="Target" value={newGoal.target_value} onChange={e => setNewGoal({...newGoal, target_value:e.target.value})} style={{ marginRight: 8 }}/>
      <button type="button" onClick={addGoal}>Add Goal</button>

      <h2>Active Goals</h2>
      {goals.length === 0 ? <p>There is no active goals</p> :
        goals.map(goal => (
          <div key={goal.goal_id} style={{ marginBottom: 8 }}>
            {goal.goal_type} – {goal.target_value}
            <button type="button" style={{ marginLeft: 10 }} onClick={() => deleteGoal(goal.goal_id)}>Delete</button>
          </div>
        ))
      }

      <hr style={{ border: "1px solid #ccc", margin: "20px 0" }} />

      {/* Health Metrics */}
      <h2>Health Metrics</h2>
      <div style={{ marginBottom: 12 }}>
        <input type="number" placeholder="Weight (lbs)" value={newMetric.weight} onChange={e => setNewMetric({...newMetric, weight:e.target.value})} style={{ marginRight: 8 }}/>
        <input type="number" placeholder="Heart Rate (bpm)" value={newMetric.heart_rate} onChange={e => setNewMetric({...newMetric, heart_rate:e.target.value})} style={{ marginRight: 8 }}/>
        <input type="number" placeholder="Body Fat (%)" value={newMetric.body_fat} onChange={e => setNewMetric({...newMetric, body_fat:e.target.value})} style={{ marginRight: 8 }}/>
        <button type="button" onClick={addMetric}>Add Entry</button>
      </div>

      <h3>Health History</h3>
      {metrics.length === 0 ? <p>There is no health history</p> :
        metrics.map(metric => (
          <div key={metric.metric_id} style={{ marginBottom: 8 }}>
            <strong>{new Date(metric.recorded_at).toLocaleString()}:</strong>{" "}
            {metric.weight && <>Weight: {metric.weight} (lbs)</>} 
            {metric.heart_rate && <> | HR: {metric.heart_rate} (bpm)</>}
            {metric.body_fat && <> | BF: {metric.body_fat}%</>}
          </div>
        ))
      }

      <hr style={{ border: "1px solid #ccc", margin: "20px 0" }} />

      {/* Classes */}
      <h2>Available Classes</h2>
      {availableClasses.length === 0 ? <p>No classes available</p> :
        availableClasses.map(cls => (
          <div key={cls.class_id} style={{ marginBottom: 8 }}>
            {cls.class_name} with {cls.trainer_name} at {new Date(cls.class_time).toLocaleString()} (Capacity: {cls.enrolled}/{cls.capacity})
            <button style={{ marginLeft: 8 }} onClick={() => registerClass(cls.class_id)}>Register</button>
          </div>
        ))
      }

      <h2>Registered Classes</h2>
      {registeredClasses.length === 0 ? <p>You are not registered for any classes</p> :
        registeredClasses.map(cls => (
          <div key={cls.class_id} style={{ marginBottom: 8 }}>
            {cls.class_name} with {cls.trainer_name} in {cls.room_name} at {new Date(cls.class_time).toLocaleString()}
            <button style={{ marginLeft: 8 }} onClick={() => unregisterClass(cls.class_id)}>Unregister</button>
          </div>
        ))
      }

    </div>
  );
}

export default MemberPage;
