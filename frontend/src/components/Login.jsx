// frontend/src/components/Login.jsx
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function Login() {
    const navigate = useNavigate();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [msg, setMsg] = useState("");

    useEffect(() => {
        console.log("API_BASE:", API_BASE);
    }, []);

    async function submit(e) {
        e.preventDefault();
        setMsg("Logging in...");
        try {
            const res = await fetch(`${API_BASE}/api/auth/login/`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            });

            const text = await res.text(); // read raw for debugging
            let data;
            try { data = JSON.parse(text); } catch (err) { data = { raw: text }; }

            console.log("LOGIN RESPONSE status:", res.status, "body:", data);

            if (!res.ok) {
                // show detailed server response to the user
                const errMsg = data.detail || (data.raw ? data.raw : JSON.stringify(data));
                setMsg(`Login failed (${res.status}): ${errMsg}`);
                return;
            }

            // success
            const token = data.token;
            const user = data.user;
            localStorage.setItem("token", token);
            localStorage.setItem("user", JSON.stringify(user));
            setMsg("Logged in");
            navigate("/dashboard");
        } catch (err) {
            console.error("Network error during login:", err);
            setMsg("Network error: " + String(err));
        }
    }

    return (
        <div style={{ border: "3px solid #000", borderRadius: 8, padding: 32, background: "#fff" }}>
            <form onSubmit={submit}>
                <h2 style={{ fontSize: 36 }}>Email</h2>
                <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" style={{ width: "100%", padding: 14, border: "3px solid #000", borderRadius: 8, marginBottom: 18 }} />

                <h2 style={{ fontSize: 36 }}>Password</h2>
                <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" placeholder="Password" style={{ width: "100%", padding: 14, border: "3px solid #000", borderRadius: 8, marginBottom: 18 }} />

                <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <button type="submit" style={{ padding: "8px 18px", border: "2px solid #000", borderRadius: 6, fontWeight: 700 }}>Login</button>
                    <button type="button" onClick={() => navigate("/register")} style={{ background: "none", border: "none", fontWeight: 700 }}>Create New Account</button>
                </div>

                {msg && <p style={{ marginTop: 12, whiteSpace: "pre-wrap" }}>{msg}</p>}
            </form>
        </div>
    );
}
