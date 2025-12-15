import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function Register() {
    const navigate = useNavigate();

    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [phone, setPhone] = useState("");

    const [countryOption, setCountryOption] = useState({});
    const [country, setCountry] = useState("TH");
    const [password, setPassword] = useState("");
    const [msg, setMsg] = useState("");

    async function submit(e) {
        e.preventDefault();
        setMsg("Creating account...");
        try {
            const res = await fetch(`${API_BASE}/api/auth/register/`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name, email, phone, country, password }),
            });

            const data = await res.json();

            if (!res.ok) return setMsg(JSON.stringify(data));

            // Auto login after register
            localStorage.setItem("token", data.token);
            localStorage.setItem("user", JSON.stringify(data.user));

            navigate("/dashboard");
        } catch (err) {
            setMsg("Network error");
        }
    }

    useEffect(() => {
        fetch(`${API_BASE}/api/calling-codes/`)
            .then(res => res.json())
            .then(data => setCountryOption(data))
            .catch(console.error);
    }, []);


    return (
        <div style={{ border: "3px solid #000", borderRadius: 8, padding: 32, background: "#fff" }}>
            <form onSubmit={submit}>
                <h2 style={{ fontSize: 36 }}>Create account</h2>

                <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Full name" style={inp} />
                <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" style={inp} />
                <div
                    style={{
                        display: "grid",
                        gridTemplateColumns: "90px 1fr",
                        gap: 8,
                        alignItems: "center",
                    }}
                >

                    <select
                        value={country}
                        onChange={(e) => setCountry(e.target.value)}
                        style={{
                            height: 45,
                            fontSize: 13,
                            border: "3px solid #000",
                            borderRadius: 8,
                            background: "#fff",
                        }}
                    >
                        {Object.entries(countryOption).map(([key, value]) => (
                            <option key={key} value={key}>
                                {key} ({value.code})
                            </option>
                        ))}
                    </select>


                    <input value={phone} onChange={(e) => setPhone(e.target.value)}
                        placeholder="Phone" style={{ ...inp, width: '100%' }} />
                </div>
                <input value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" type="password" style={inp} />

                <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <button type="submit" style={btn}>Register</button>
                    <button onClick={() => navigate("/login")} style={linkBtn}>Back to Login</button>
                </div>

                {msg && <p style={{ marginTop: 12 }}>{msg}</p>}
            </form>
        </div>
    );
}

const inp = { width: "100%", padding: 14, border: "3px solid #000", borderRadius: 8, marginBottom: 10 };
const btn = { padding: "8px 18px", border: "2px solid #000", borderRadius: 6, fontWeight: 700 };
const linkBtn = { background: "none", border: "none", fontWeight: 700 };
