import React, { useState, useEffect } from "react";
import { API_BASE } from "../config";
import { useAuth } from "../AuthContext";

function TrainerPage() {
  const { auth, authHeader } = useAuth();
  const [trainers, setTrainers] = useState([]);
  const [selectedTrainerId, setSelectedTrainerId] = useState(null);
  const [selectedTrainer, setSelectedTrainer] = useState(null);
  const [classes, setClasses] = useState([]);
  const [ptSessions, setPtSessions] = useState([]);
  const [availability, setAvailability] = useState([]);
  const [newSlot, setNewSlot] = useState({ start_time: "", end_time: "", notes: "" });

  // ✅ Member search state
  const [searchTerm, setSearchTerm] = useState("");
  const [memberResults, setMemberResults] = useState([]);

  const apiFetch = (path, options = {}) =>
    fetch(`${API_BASE}${path}`, {
      ...options,
      headers: { ...(options.headers || {}), ...authHeader },
    });

  useEffect(() => {
    if (!auth || auth.role !== "trainer") return;
    const id = auth.trainer_id;
    setSelectedTrainerId(id);
    fetchTrainer(id);
  }, [auth]);

  // Fetch trainer info by ID
  const fetchTrainer = async (id) => {
    const res = await apiFetch(`/trainers/${id}`);
    if (!res.ok) {
      return;
    }
    const data = await res.json();
    setSelectedTrainer(data);
    setTrainers([data]);
    fetchClasses(id);
    fetchSchedule(id);
    fetchAvailability(id);
  };

  // Fetch assigned classes for trainer
  const fetchClasses = async (id) => {
    const res = await apiFetch(`/trainers/${id}/classes`);
    const data = await res.json();
    setClasses(data);
  };

  // Full schedule for trainer (PT + classes)
  const fetchSchedule = async (id) => {
    const res = await apiFetch(`/trainers/${id}/schedule`);
    const data = await res.json();
    setPtSessions(data.pt_sessions || []);
    setClasses(data.classes || []);
  };

  // Availability
  const fetchAvailability = async (id) => {
    const res = await apiFetch(`/trainers/${id}/availability`);
    const data = await res.json();
    setAvailability(data);
  };

  const createSlot = async () => {
    if (!selectedTrainerId || !newSlot.start_time || !newSlot.end_time) return;
    await apiFetch(`/trainers/${selectedTrainerId}/availability`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(newSlot)
    });
    setNewSlot({ start_time: "", end_time: "", notes: "" });
    fetchAvailability(selectedTrainerId);
  };

  const deleteSlot = async (availability_id) => {
    await apiFetch(`/trainers/${selectedTrainerId}/availability/${availability_id}`, { method: "DELETE" });
    fetchAvailability(selectedTrainerId);
  };

  const selectTrainer = (trainerId) => {
    setSelectedTrainerId(trainerId);
    fetchTrainer(trainerId);
  };

  // ✅ Member search
  const searchMembers = async () => {
    if (!searchTerm.trim()) {
      setMemberResults([]);
      return;
    }

    const base = selectedTrainerId
      ? `/trainers/${selectedTrainerId}/members/search?name=${searchTerm}`
      : `/members/search?name=${searchTerm}`;
    const res = await apiFetch(base);
    const data = await res.json();
    setMemberResults(data);
  };

  if (!auth || auth.role !== "trainer") {
    return <p className="muted">Trainers only. Please log in with a trainer account.</p>;
  }

  return (
    <section className="section stack">
      <header className="card stack">
        <div className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <h1 style={{ color: "#0b1224" }}>Trainer Dashboard</h1>
            {selectedTrainer && (
              <p className="muted" style={{ color: "#1f2937" }}>
                Logged in as: {selectedTrainer.first_name} {selectedTrainer.last_name} ({selectedTrainer.certification})
              </p>
            )}
          </div>
          <div className="row">
            {trainers.map(t => (
              <button
                key={t.trainer_id}
                className={selectedTrainerId == t.trainer_id ? "" : "secondary"}
                onClick={() => selectTrainer(t.trainer_id)}
              >
                {t.full_name}
              </button>
            ))}
          </div>
        </div>
      </header>

      {selectedTrainerId && (
        <div className="grid-2">
          <article className="card stack">
            <h3>Assigned Classes</h3>
            {classes.length === 0 ? (
              <p className="muted">No classes assigned.</p>
            ) : (
              <div className="stack">
                {classes.map(c => (
                  <div key={c.class_id} className="row" style={{ justifyContent: "space-between" }}>
                    <div>
                      <strong>{c.class_name}</strong>
                      <div className="muted">{new Date(c.class_time).toLocaleString()} · {c.room_name}</div>
                    </div>
                    <span className="pill">{c.status || "Scheduled"}</span>
                  </div>
                ))}
              </div>
            )}
          </article>

          <article className="card stack">
            <h3>PT Sessions</h3>
            {ptSessions.length === 0 ? <p className="muted">No upcoming PT sessions</p> : (
              <div className="stack">
                {ptSessions.map(s => (
                  <div key={s.session_id} className="row" style={{ justifyContent: "space-between" }}>
                    <div>
                      <strong>{s.member_name}</strong> – {s.session_type || "Session"}
                      <div className="muted">{new Date(s.start_time).toLocaleString()}</div>
                    </div>
                    <span className="pill">{s.status}</span>
                  </div>
                ))}
              </div>
            )}
          </article>
        </div>
      )}

      {selectedTrainerId && (
        <article className="card stack">
          <h3>Availability</h3>
          <div className="row">
            <input type="datetime-local" value={newSlot.start_time} onChange={e => setNewSlot({...newSlot, start_time: e.target.value})} />
            <input type="datetime-local" value={newSlot.end_time} onChange={e => setNewSlot({...newSlot, end_time: e.target.value})} />
            <input placeholder="Notes" value={newSlot.notes} onChange={e => setNewSlot({...newSlot, notes: e.target.value})} />
            <button onClick={createSlot}>Add Slot</button>
          </div>
          {availability.length === 0 ? <p className="muted">No availability defined.</p> : (
            <div className="stack">
              {availability.map(a => (
                <div key={a.availability_id} className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
                  <span>{new Date(a.start_time).toLocaleString()} - {new Date(a.end_time).toLocaleString()} {a.notes && `(${a.notes})`}</span>
                  <button className="secondary" onClick={() => deleteSlot(a.availability_id)}>Delete</button>
                </div>
              ))}
            </div>
          )}
        </article>
      )}

      <article className="card stack">
        <h3>Member Lookup</h3>

        <div className="row">
          <input
            type="text"
            placeholder="Search member by name"
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
          />
          <button onClick={searchMembers}>Search</button>
        </div>

        <div className="stack">
          {memberResults.length === 0 && searchTerm && (
            <p className="muted">No members found.</p>
          )}

          {memberResults.map(m => (
            <div key={m.member_id} className="row result-item" style={{ justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ color: "#0f172a" }}>{m.first_name} {m.last_name} (ID: {m.member_id})</span>
              {m.primary_goal && <span className="pill">{m.primary_goal}</span>}
            </div>
          ))}
        </div>
      </article>
    </section>
  );
}

export default TrainerPage;
