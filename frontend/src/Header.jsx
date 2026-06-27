import React from "react";
import "./style.css";
import Login from "./Login";

function Header({ isLoggedIn, setIsLoggedIn, setShowLogin }) {

  const role = localStorage.getItem("role");

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    setIsLoggedIn(false);
  };

  return (
    <div className="header">

      <div className="header-left">
        <img src="/ntpclogo.PNG" alt="logo" className="logo" />
        <h2 className="title">SIMHADRI LMI MATRIX</h2>
      </div>
{/* 
      <div className="header-center">
       {!isLoggedIn ? (
          <button
            className="login-btn"
            onClick={() => setShowLogin(true)}
          >
            🔐 Login
          </button>
        ) : (
          <>
            <span>👤 {localStorage.getItem("role")}</span>
            <button onClick={() => {
              localStorage.clear();
              setIsLoggedIn(false);
            }}>
              🚪 Logout
            </button>
          </>
        )}
      </div> */}

      <div className="header-right">

        

      </div>

    </div>
  );
}

export default Header;