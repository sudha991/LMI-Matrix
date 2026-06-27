import React, { useState } from "react";
import axios from "axios";


const API = "http://10.0.180.28:5000";

function Login({ setIsLoggedIn, closeModal }) {

  const [empId, setEmpId] = useState("");
  const [dob, setDob] = useState("");
  const [role, setRole] = useState("");
  const [error, setError] = useState("");

const formatDOB = (date) => {
        if (!date) return "";

        const d = new Date(date);
        const day = String(d.getDate()).padStart(2, "0");
        const month = String(d.getMonth() + 1).padStart(2, "0");
        const year = d.getFullYear();

        return `${day}${month}${year}`;
      };
console.log({
  emp_id: empId,
  dob: formatDOB(dob),
  role: role
});
  const handleLogin = async () => {
    try {

      const formattedDOB = formatDOB(dob);

      console.log({
        emp_id: empId,
        dob: formattedDOB,
        role: role
      });

      const res = await axios.post(`${API}/login`, {
        emp_id: empId,
        dob: formattedDOB,   // ✅ send this
        role: role
      });
      localStorage.setItem("token", res.data.token);
      localStorage.setItem("role", res.data.role);

      setIsLoggedIn(true);
      closeModal();

    } catch (err) {
      setError("Invalid credentials");
    }
  };
console.log(empId, dob, role);
  return (
    <div className="login-container">

      <h2>Login</h2>

      <input
        placeholder="Employee ID"
        value={empId}
        onChange={(e) => setEmpId(e.target.value)}
      />

      <input
        type="date"
        value={dob}
        onChange={(e) => setDob(e.target.value)}
      />

      <select value={role} onChange={(e) => setRole(e.target.value)}>
        <option value="">Select Role</option>
        <option value="ADMIN">ADMIN</option>
        <option value="USER">USER</option>
      </select>

      <button onClick={handleLogin}>Login</button>

      {error && <p style={{ color: "red" }}>{error}</p>}

    </div>
  );
}

export default Login;