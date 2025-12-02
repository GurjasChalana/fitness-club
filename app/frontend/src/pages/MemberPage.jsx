import React, { useState, useEffect } from "react";
import { API_BASE } from "../config";
import { useAuth } from "../AuthContext";

function MemberPage() {
  const { auth, authHeader, logout } = useAuth();
  const [form, setForm] = useState({
    first_name: "", last_name: "", email: "", username: "", password: "", date_of_birth: "", gender: "", phone: ""
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

  // Trainers / rooms / PT sessions
  const [trainers, setTrainers] = useState([]);
  const [rooms, setRooms] = useState([]);
  const [ptSessions, setPtSessions] = useState([]);
  const [ptForm, setPtForm] = useState({ trainer_id: "", room_id: "", start_time: "", end_time: "", session_type: "" });

  // Billing / dashboard
  const [dashboard, setDashboard] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [paymentDrafts, setPaymentDrafts] = useState({});

  const apiFetch = async (path, options = {}) => {
    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: { ...(options.headers || {}), ...authHeader },
    });
    if (res.status === 401) {
      // Session expired or bad credentials; force logout so user can sign in again.
      logout();
      throw new Error("Unauthorized. Please log in again.");
    }
    return res;
  };

  const getJson = async (res) => {
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const message = data?.error || data?.message || "Request failed";
      throw new Error(message);
    }
    return data;
  };

  useEffect(() => {
    if (!auth || auth.role !== "member") return;
    const resolvedId = auth.member_id || localStorage.getItem("memberId");
    if (resolvedId) {
      setMemberId(resolvedId);
    }
    fetchTrainersList();
    fetchRoomsList();
  }, [auth]);

  useEffect(() => {
    if (!auth || auth.role !== "member" || !memberId) return;
    localStorage.setItem("memberId", memberId);
    fetchMemberDetails(memberId);
    fetchGoals(memberId);
    fetchMetrics(memberId);
    fetchAvailableClasses();
    fetchRegisteredClasses(memberId);
    fetchPtSessions(memberId);
    fetchDashboard(memberId);
    fetchInvoices(memberId);
  }, [auth, memberId]);

  // Member details
  const fetchMemberDetails = async (id) => {
    const res = await apiFetch(`/members/${id}`);
    const data = await getJson(res);
    setMemberData(data);
  };
  const handleChange = e => setForm({ ...form, [e.target.name]: e.target.value });
  const registerMember = async e => {
    e.preventDefault();
    const res = await apiFetch(`/members/register`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(form)
    });
    const data = await res.json();
    setMemberId(data.member_id);
    localStorage.setItem("memberId", data.member_id);
    fetchMemberDetails(data.member_id);
    fetchRegisteredClasses(data.member_id);
    fetchPtSessions(data.member_id);
    fetchDashboard(data.member_id);
    fetchInvoices(data.member_id);
  };
  const updateField = async field => {
    const res = await apiFetch(`/members/${memberId}`, {
      method: "PUT", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ [field]: editValue })
    });
    const data = await res.json();
    if (!res.ok) {
      alert(data.error || "Update failed");
      setEditingField(null);
      setEditValue("");
      return;
    }
    setMemberData(data);
    setEditingField(null);
  };

  // Fitness goals
  const fetchGoals = async id => {
    const res = await apiFetch(`/members/${id}/goals`);
    const data = await getJson(res);
    setGoals(Array.isArray(data) ? data : []);
  };
  const updateGoal = async (goalId, payload) => {
    await apiFetch(`/members/${memberId}/goals/${goalId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    fetchGoals(memberId);
  };
  const addGoal = async () => {
    await apiFetch(`/members/${memberId}/goals`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(newGoal)
    });
    setNewGoal({ goal_type: "", target_value: "" });
    fetchGoals(memberId);
  };
  const deleteGoal = async id => {
    await apiFetch(`/goals/${id}`, { method: "DELETE" });
    fetchGoals(memberId);
  };

  // Health metrics
  const fetchMetrics = async id => {
    const res = await apiFetch(`/members/${id}/health-metrics`);
    const data = await getJson(res);
    setMetrics(Array.isArray(data) ? data : []);
  };
  const addMetric = async () => {
    await apiFetch(`/members/${memberId}/health-metrics`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(newMetric)
    });
    setNewMetric({ weight: "", heart_rate: "", body_fat: "" });
    fetchMetrics(memberId);
  };

  // Classes
  const fetchAvailableClasses = async () => {
    const res = await apiFetch(`/classes/available`);
    const data = await getJson(res);
    setAvailableClasses(Array.isArray(data) ? data : []);
  };
  const fetchRegisteredClasses = async (id) => {
    const res = await apiFetch(`/members/${id}/classes`);
    const data = await getJson(res);
    setRegisteredClasses(Array.isArray(data) ? data : []);
  };
  const registerClass = async (class_id) => {
    await apiFetch(`/classes/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ member_id: memberId, class_id })
    });
    fetchAvailableClasses();
    fetchRegisteredClasses(memberId);
  };
  const unregisterClass = async (class_id) => {
    await apiFetch(`/classes/unregister`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ member_id: memberId, class_id })
    });
    fetchAvailableClasses();
    fetchRegisteredClasses(memberId);
  };

  // Trainers / rooms
  const fetchTrainersList = async () => {
    const res = await apiFetch(`/trainers`);
    const data = await getJson(res);
    setTrainers(Array.isArray(data) ? data : []);
  };

  const fetchRoomsList = async () => {
    const res = await apiFetch(`/rooms`);
    const data = await getJson(res);
    setRooms(Array.isArray(data) ? data : []);
  };

  // PT sessions
  const fetchPtSessions = async (id) => {
    const res = await apiFetch(`/members/${id}/pt-sessions`);
    const data = await getJson(res);
    setPtSessions(Array.isArray(data) ? data : []);
  };

  const schedulePtSession = async () => {
    if (!ptForm.trainer_id || !ptForm.start_time || !ptForm.end_time) return;
    await apiFetch(`/pt-sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        member_id: memberId,
        trainer_id: Number(ptForm.trainer_id),
        room_id: ptForm.room_id ? Number(ptForm.room_id) : null,
        start_time: ptForm.start_time,
        end_time: ptForm.end_time,
        session_type: ptForm.session_type
      })
    });
    setPtForm({ trainer_id: "", room_id: "", start_time: "", end_time: "", session_type: "" });
    fetchPtSessions(memberId);
  };

  // Dashboard + billing
  const fetchDashboard = async (id) => {
    const res = await apiFetch(`/members/${id}/dashboard`);
    const data = await getJson(res);
    setDashboard(data);
  };

  const fetchInvoices = async (id) => {
    const res = await apiFetch(`/members/${id}/invoices`);
    const data = await getJson(res);
    setInvoices(Array.isArray(data) ? data : []);
  };

  const payInvoice = async (invoiceId, remaining) => {
    const amount = paymentDrafts[invoiceId] ?? remaining;
    if (!amount) return;
    await apiFetch(`/members/${memberId}/invoices/${invoiceId}/payments`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ amount: Number(amount) })
    });
    fetchInvoices(memberId);
  };

  if (!auth || auth.role !== "member") {
    return <p className="muted">Members only. Please log in with a member account.</p>;
  }

  // Render registration form
  if (!memberId) return (
    <section className="section card stack" style={{ maxWidth: 520 }}>
      <h1 style={{ color: "#0b1224" }}>Member Registration</h1>
      <p className="muted" style={{ color: "#1f2937" }}>Create your account to get started.</p>
      <form onSubmit={registerMember} className="stack">
        <div className="grid-2">
          {Object.keys(form).map(key => (
            <label key={key} className="stack" style={{ gap: "0.25rem" }}>
              <span style={{ color: "#0f172a", textTransform: "capitalize" }}>{key.replace("_", " ")}</span>
              <input
                name={key}
                type={key === "password" ? "password" : key === "date_of_birth" ? "date" : "text"}
                placeholder={key.replace("_", " ")}
                value={form[key]}
                onChange={handleChange}
                required={["first_name","last_name","email","username","password"].includes(key)}
              />
            </label>
          ))}
        </div>
        <button type="submit">Register</button>
      </form>
    </section>
  );

  if (!memberData) return <p>Loading...</p>;

  return (
    <section className="section">
      <h1>Welcome, {memberData.first_name}</h1>

      {dashboard && (
        <article className="card section stack">
          <div className="row" style={{ justifyContent: "space-between" }}>
            <div>
              <strong>Dashboard</strong>
              <p className="muted">Quick glance at your stats</p>
            </div>
            <span className="pill">ID: {memberId}</span>
          </div>
          <div className="grid-2">
            <div>
              <p><strong>Active goals:</strong> {dashboard.active_goals}</p>
              <p><strong>Completed goals:</strong> {dashboard.completed_goals}</p>
              <p><strong>Upcoming classes:</strong> {dashboard.upcoming_class_count}</p>
              <p><strong>Past classes:</strong> {dashboard.past_class_count}</p>
              <p><strong>Upcoming PT sessions:</strong> {dashboard.upcoming_pt_session_count}</p>
              <p><strong>Past PT sessions:</strong> {dashboard.past_pt_session_count}</p>
            </div>
            {dashboard.latest_metric && (
              <div>
                <p className="muted">Latest metric ({new Date(dashboard.latest_metric.recorded_at).toLocaleString()})</p>
                <p>
                  {dashboard.latest_metric.weight && `Weight ${dashboard.latest_metric.weight} lbs `}
                  {dashboard.latest_metric.heart_rate && `HR ${dashboard.latest_metric.heart_rate} bpm `}
                  {dashboard.latest_metric.body_fat && `BF ${dashboard.latest_metric.body_fat}%`}
                </p>
              </div>
            )}
          </div>
        </article>
      )}

      <article className="card section">
        <h2>Personal Details</h2>
        <div className="stack">
          {["first_name","last_name","email","date_of_birth","gender","phone"].map(field => (
            <div key={field} className="row" style={{ alignItems: "center", justifyContent: "space-between" }}>
              <div>
                <strong>{field.replace("_"," ")}:</strong> {memberData[field] || "N/A"}
              </div>
              {editingField === field ? (
                <div className="row">
                  <input autoFocus value={editValue} onChange={e => setEditValue(e.target.value)} />
                  <button type="button" onClick={() => updateField(field)}>Save</button>
                  <button type="button" className="secondary" onClick={() => setEditingField(null)}>Cancel</button>
                </div>
              ) : (
                <button type="button" className="secondary" onClick={() => {setEditingField(field); setEditValue(memberData[field] || "")}}>
                  Update
                </button>
              )}
            </div>
          ))}
        </div>
      </article>

      <article className="card section stack">
        <h2>Fitness Goals</h2>
        <div className="row">
          <input placeholder="Goal Type" value={newGoal.goal_type} onChange={e => setNewGoal({...newGoal, goal_type:e.target.value})}/>
          <input type="number" placeholder="Target" value={newGoal.target_value} onChange={e => setNewGoal({...newGoal, target_value:e.target.value})}/>
          <button type="button" onClick={addGoal}>Add Goal</button>
        </div>
        <div className="stack">
          <h4>Goals</h4>
          {goals.length === 0 ? <p className="muted">No goals yet</p> :
            goals.map(goal => (
              <div key={goal.goal_id} className="row" style={{ justifyContent: "space-between", alignItems: "center", gap: "0.5rem" }}>
                <div className="stack" style={{ gap: "0.1rem" }}>
                  <span><strong>{goal.goal_type}</strong> – target {goal.target_value}</span>
                  <span className="muted">Status: {goal.is_active ? "Active" : "Inactive"}</span>
                </div>
                <div className="row" style={{ gap: "0.35rem" }}>
                  <button
                    type="button"
                    className="secondary"
                    onClick={() => updateGoal(goal.goal_id, { is_active: !goal.is_active })}
                  >
                    {goal.is_active ? "Deactivate" : "Activate"}
                  </button>
                  <button
                    type="button"
                    className="secondary"
                    onClick={() => {
                      const updated = window.prompt("Update target value", goal.target_value);
                      if (updated !== null && updated !== "") {
                        updateGoal(goal.goal_id, { target_value: Number(updated) });
                      }
                    }}
                  >
                    Edit Target
                  </button>
                  <button type="button" className="secondary" onClick={() => deleteGoal(goal.goal_id)}>Delete</button>
                </div>
              </div>
            ))
          }
        </div>
      </article>

      <article className="card section stack">
        <h2>Health Metrics</h2>
        <div className="row">
          <input type="number" placeholder="Weight (lbs)" value={newMetric.weight} onChange={e => setNewMetric({...newMetric, weight:e.target.value})}/>
          <input type="number" placeholder="Heart Rate (bpm)" value={newMetric.heart_rate} onChange={e => setNewMetric({...newMetric, heart_rate:e.target.value})}/>
          <input type="number" placeholder="Body Fat (%)" value={newMetric.body_fat} onChange={e => setNewMetric({...newMetric, body_fat:e.target.value})}/>
          <button type="button" onClick={addMetric}>Add Entry</button>
        </div>
        <div className="stack">
          <h4>Health History</h4>
          {metrics.length === 0 ? <p className="muted">There is no health history</p> :
            metrics.map(metric => (
              <div key={metric.metric_id} className="row" style={{ justifyContent: "space-between" }}>
                <strong>{new Date(metric.recorded_at).toLocaleString()}:</strong>
                <span>
                  {metric.weight && <>Weight: {metric.weight} (lbs) </>} 
                  {metric.heart_rate && <> | HR: {metric.heart_rate} (bpm)</>}
                  {metric.body_fat && <> | BF: {metric.body_fat}%</>}
                </span>
              </div>
            ))
          }
        </div>
      </article>

      <article className="card section stack">
        <h2>Personal Training Sessions</h2>
        <div className="row">
          <select value={ptForm.trainer_id} onChange={e => setPtForm({...ptForm, trainer_id: e.target.value})}>
            <option value="">Select trainer</option>
            {trainers.map(t => (
              <option key={t.trainer_id} value={t.trainer_id}>{t.full_name}</option>
            ))}
          </select>
          <select value={ptForm.room_id} onChange={e => setPtForm({...ptForm, room_id: e.target.value})}>
            <option value="">Room (optional)</option>
            {rooms.map(r => (
              <option key={r.room_id} value={r.room_id}>{r.room_name}</option>
            ))}
          </select>
          <input type="datetime-local" value={ptForm.start_time} onChange={e => setPtForm({...ptForm, start_time: e.target.value})}/>
          <input type="datetime-local" value={ptForm.end_time} onChange={e => setPtForm({...ptForm, end_time: e.target.value})}/>
          <input placeholder="Type (optional)" value={ptForm.session_type} onChange={e => setPtForm({...ptForm, session_type: e.target.value})}/>
          <button type="button" onClick={schedulePtSession}>Schedule</button>
        </div>
        <div className="stack">
          {ptSessions.length === 0 ? <p className="muted">No upcoming sessions</p> : (
            ptSessions.map(pt => (
              <div key={pt.session_id} className="row" style={{ justifyContent: "space-between" }}>
                <span>{pt.session_type || "Session"} with {pt.trainer_name} on {new Date(pt.start_time).toLocaleString()}</span>
                <span className="pill">{pt.status}</span>
              </div>
            ))
          )}
        </div>
      </article>

      <article className="card section stack">
        <h2>Classes</h2>
        <div className="grid-2">
          <div className="stack">
            <h4>Available</h4>
            {availableClasses.length === 0 ? <p className="muted">No classes available</p> :
              availableClasses.map(cls => (
                <div key={cls.class_id} className="row" style={{ justifyContent: "space-between" }}>
                  <div>
                    <strong>{cls.class_name}</strong> with {cls.trainer_name}
                    <div className="muted">{new Date(cls.class_time).toLocaleString()} · {cls.enrolled}/{cls.capacity}</div>
                  </div>
                  <button onClick={() => registerClass(cls.class_id)}>Register</button>
                </div>
              ))
            }
          </div>
          <div className="stack">
            <h4>Registered</h4>
            {registeredClasses.length === 0 ? <p className="muted">You are not registered for any classes</p> :
              registeredClasses.map(cls => (
                <div key={cls.class_id} className="row" style={{ justifyContent: "space-between" }}>
                  <div>
                    <strong>{cls.class_name}</strong> with {cls.trainer_name}
                    <div className="muted">{cls.room_name} · {new Date(cls.class_time).toLocaleString()}</div>
                  </div>
                  <button className="secondary" onClick={() => unregisterClass(cls.class_id)}>Unregister</button>
                </div>
              ))
            }
          </div>
        </div>
      </article>

      <article className="card section stack">
        <h2>Billing</h2>
        {invoices.length === 0 ? <p className="muted">No invoices yet</p> : invoices.map(inv => {
          const paid = inv.payments?.reduce((sum, p) => sum + (p.amount || 0), 0) || 0;
          const remaining = (inv.total_amount || 0) - paid;
          return (
            <div key={inv.invoice_id} className="card stack" style={{ borderColor: "var(--muted-border-color)" }}>
              <div className="row" style={{ justifyContent: "space-between" }}>
                <strong>Invoice #{inv.invoice_id}</strong>
                <span className="pill">{inv.status}</span>
              </div>
              <div className="muted">Due: {inv.due_date || "N/A"}</div>
              <div>Items: {inv.items?.map(it => `${it.description} (${it.quantity} x ${it.unit_price})`).join(", ")}</div>
              <div>Paid: ${paid} | Remaining: ${remaining}</div>
              {remaining > 0 && (
                <div className="row" style={{ alignItems: "center" }}>
                  <input
                    type="number"
                    placeholder="Amount"
                    value={paymentDrafts[inv.invoice_id] ?? remaining}
                    onChange={e => setPaymentDrafts({...paymentDrafts, [inv.invoice_id]: e.target.value})}
                  />
                  <button onClick={() => payInvoice(inv.invoice_id, remaining)}>Pay</button>
                </div>
              )}
            </div>
          );
        })}
      </article>

    </section>
  );
}

export default MemberPage;
