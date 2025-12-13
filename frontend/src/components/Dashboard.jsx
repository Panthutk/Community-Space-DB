import React from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";

export default function Dashboard() {
    const navigate = useNavigate();
    const user = JSON.parse(localStorage.getItem("user"));
    const token = localStorage.getItem("token");

    if (!token) return navigate("/login");

    return (
        <div style={{ fontSize: 24 }}>
          <p>Welcome, {user?.name || user?.email}</p>

          {/*: Create Venue */}
          <div style={{ marginTop: 16 }}>
            <Link to="/venues/create" style={{ textDecoration: "none" }}>
              <button
                style={{
                  padding: "8px 18px",
                  border: "2px solid #000",
                  borderRadius: 6,
                  marginRight: 12,
                }}
              >
                Create Venue
              </button>
            </Link>
          </div>

          <button
            onClick={() => {
              localStorage.clear();
              navigate("/login");
            }}
            style={{
              padding: "8px 18px",
              border: "2px solid #000",
              borderRadius: 6,
              marginTop: 20,
            }}
          >
            Logout
          </button>
        </div>
      );
    }
