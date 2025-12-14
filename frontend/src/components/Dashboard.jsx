import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

// static GIF for mockup
const PLACEHOLDER_GIF =
  "https://pulse.com.mx/wp-content/uploads/2023/07/IMG_0529.gif";

export default function Dashboard() {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem("user"));
  const token = localStorage.getItem("token");

  const [venues, setVenues] = useState([]);
  const [loading, setLoading] = useState(true);

  if (!token) {
    navigate("/login");
    return null;
  }

  useEffect(() => {
    fetch(`${API_BASE}/api/venues/`)
      .then((res) => res.json())
      .then((data) => {
        setVenues(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load venues", err);
        setLoading(false);
      });
  }, []);

  return (
    <div style={{ maxWidth: 1100, margin: "24px auto", padding: 16 }}>

      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 20,
        }}
      >
        <div>
          <h1 style={{ fontSize: 36, marginBottom: 4 }}>Community Space</h1>
          <p>Welcome, {user?.name || user?.email}</p>
        </div>

        {/* Logout button (top-right) */}
        <button
          onClick={() => {
            localStorage.clear();
            navigate("/login");
          }}
          style={{
            padding: "10px 18px",
            border: "2px solid #000",
            borderRadius: 8,
            background: "#f5f5f5",
          }}
        >
          Logout
        </button>
      </div>

      {/* Create venue */}
      <div style={{ margin: "20px 0" }}>
        <Link to="/venues/create">
          <button
            style={{
              padding: "10px 20px",
              border: "2px solid #000",
              borderRadius: 8,
            }}
          >
            Create Venue
          </button>
        </Link>
      </div>

      {loading && <p>Loading venues...</p>}
      {!loading && venues.length === 0 && <p>No venues created yet.</p>}

      {/* Venue cards */}
      <div style={{ display: "grid", gap: 20 }}>
        {venues.map((v) => (
          <div
            key={v.id}
            style={{
              border: "4px solid black",
              borderRadius: 16,
              padding: 16,
              display: "flex",
              gap: 20,
              alignItems: "center",
            }}
          >
            {/* GIF preview */}
            <img
              src={PLACEHOLDER_GIF}
              alt="Venue preview"
              style={{
                width: 180,
                height: 180,
                objectFit: "cover",
                borderRadius: 12,
                border: "2px solid #000",
              }}
            />

            {/* Info */}
            <div style={{ flex: 1 }}>
              <h2 style={{ marginBottom: 6 }}>{v.name}</h2>
              <p style={{ marginBottom: 8 }}>
                {v.description || "No description"}
              </p>

              <p><b>Type:</b> {v.venue_type}</p>

              <p>
                <b>Location:</b>{" "}
                {[v.address, v.city, v.province, v.country]
                  .filter(Boolean)
                  .join(", ")}
              </p>

              <p>
                <b>Spaces:</b>{" "}
                {v.summary?.published_spaces} / {v.summary?.total_spaces}
              </p>

              <p>
                <b>Created:</b>{" "}
                {new Date(v.created_at).toLocaleDateString()}
              </p>
            </div>

            {/* Actions (UI only) */}
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              <button
                onClick={() => navigate(`/venues/${v.id}/spaces`)}
                style={{
                  padding: "10px",
                  background: "#7CFC7C",
                  border: "2px solid #000",
                  borderRadius: 8,
                }}
              >
                Booking
              </button>

              <button
                style={{
                  padding: "10px",
                  background: "#FFD966",
                  border: "2px solid #000",
                  borderRadius: 8,
                }}
              >
                Reviewing
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
