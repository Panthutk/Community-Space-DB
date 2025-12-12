import React from "react";
import { useNavigate } from "react-router-dom";

export default function Dashboard() {
    const navigate = useNavigate();
    const user = JSON.parse(localStorage.getItem("user"));
    const token = localStorage.getItem("token");

    if (!token) return navigate("/login");

    return (
        <div style={{ fontSize: 24 }}>
            <p>Welcome, {user?.name || user?.email}</p>

            <button
                onClick={() => {
                    localStorage.clear();
                    navigate("/login");
                }}
                style={{ padding: "8px 18px", border: "2px solid #000", borderRadius: 6, marginTop: 20 }}
            >
                Logout
            </button>
        </div>
    );
}
