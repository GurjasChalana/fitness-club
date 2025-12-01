import React, { useState, useEffect } from "react";

function TrainerPage() {
  const [trainers, setTrainers] = useState([]);
  const [selectedTrainerId, setSelectedTrainerId] = useState(localStorage.getItem("trainerId"));
  const [selectedTrainer, setSelectedTrainer] = useState(null);
  const [classes, setClasses] = useState([]);

  // ✅ Member search state
  const [searchTerm, setSearchTerm] = useState("");
  const [memberResults, setMemberResults] = useState([]);

  useEffect(() => {
    fetchTrainers();
    if (selectedTrainerId) fetchTrainer(selectedTrainerId);
  }, []);

  // Fetch all trainers for the buttons
  const fetchTrainers = async () => {
    const res = await fetch("http://127.0.0.1:5000/trainers");
    const data = await res.json();
    setTrainers(data);
  };

  // Fetch trainer info by ID
  const fetchTrainer = async (id) => {
    const res = await fetch(`http://127.0.0.1:5000/trainers/${id}`);
    const data = await res.json();
    setSelectedTrainer(data);
    fetchClasses(id);
  };

  // Fetch assigned classes for trainer
  const fetchClasses = async (id) => {
    const res = await fetch(`http://127.0.0.1:5000/trainers/${id}/classes`);
    const data = await res.json();
    setClasses(data);
  };

  const selectTrainer = (trainerId) => {
    localStorage.setItem("trainerId", trainerId);
    setSelectedTrainerId(trainerId);
    fetchTrainer(trainerId);
  };

  // ✅ Member search
  const searchMembers = async () => {
    if (!searchTerm.trim()) {
      setMemberResults([]);
      return;
    }

    const res = await fetch(
      `http://127.0.0.1:5000/members/search?name=${searchTerm}`
    );
    const data = await res.json();
    setMemberResults(data);
  };

  return (
    <div style={{ padding: "20px" }}>
      <h1>Trainer Dashboard</h1>

      {selectedTrainer && (
        <h2>
          Logged in as: {selectedTrainer.first_name} {selectedTrainer.last_name}
        </h2>
      )}

      {/* Trainer selector */}
      <div style={{ margin: "10px 0" }}>
        {trainers.map(t => (
          <button
            key={t.trainer_id}
            onClick={() => selectTrainer(t.trainer_id)}
            style={{ marginRight: 8 }}
          >
            {t.full_name} ({t.certification})
          </button>
        ))}
      </div>

      {/* Assigned classes */}
      {selectedTrainerId && (
        <>
          <h3>Assigned Classes</h3>
          {classes.length === 0 ? (
            <p>No classes assigned.</p>
          ) : (
            <ul>
              {classes.map(c => (
                <li key={c.class_id}>
                  {c.class_name} at{" "}
                  {new Date(c.class_time).toLocaleString()} –{" "}
                  {c.room_name}
                </li>
              ))}
            </ul>
          )}
        </>
      )}

      {/* ✅ MEMBER LOOKUP SECTION */}
      <hr />

      <h3>Member Lookup</h3>

      <input
        type="text"
        placeholder="Search member by name"
        value={searchTerm}
        onChange={e => setSearchTerm(e.target.value)}
        style={{ marginRight: 8 }}
      />
      <button onClick={searchMembers}>Search</button>

      <div style={{ marginTop: 10 }}>
        {memberResults.length === 0 && searchTerm && (
          <p>No members found.</p>
        )}

        {memberResults.map(m => (
          <div key={m.member_id}>
            {m.first_name} {m.last_name} (ID: {m.member_id})
          </div>
        ))}
      </div>
    </div>
  );
}

export default TrainerPage;
