import React from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import MemberPage from "./pages/MemberPage";
import TrainerPage from "./pages/TrainerPage";
import AdminPage from "./pages/AdminPage";

function App() {
  return (
    <Router>
      <Routes>
        <Route
          path="/"
          element={
            <div style={{ padding: "20px" }}>
              <h1>Gym App Home</h1>
              <div style={{ display: "flex", gap: "10px" }}>
                <Link to="/member">
                  <button>Member</button>
                </Link>
                <Link to="/trainer">
                  <button>Trainer</button>
                </Link>
                <Link to="/admin">
                  <button>Admin</button>
                </Link>
              </div>
            </div>
          }
        />
        <Route path="/member" element={<MemberPage />} />
        <Route path="/trainer" element={<TrainerPage />} />
        <Route path="/admin" element={<AdminPage />} />
      </Routes>
    </Router>
  );
}

export default App;
