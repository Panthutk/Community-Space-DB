import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export default function VenueSpaces() {
    const { venueId } = useParams();
    const navigate = useNavigate();
    const token = localStorage.getItem("token");

    const [venue, setVenue] = useState(null);
    const [spaces, setSpaces] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch(`${API_BASE}/api/venues/${venueId}/spaces/`, {
            headers: {
                Authorization: `Bearer ${token}`,
            },
        })
            .then((res) => res.json())
            .then((data) => {
                setVenue(data.venue);
                setSpaces(data.spaces);
                setLoading(false);
            })
            .catch((err) => {
                console.error("Failed to load spaces", err);
                setLoading(false);
            });
    }, [venueId]);

    if (loading) return <p>Loading spaces...</p>;

    return (
        <div style={{ maxWidth: 1100, margin: "24px auto", padding: 16 }}>
            <button
                onClick={() => navigate(-1)}
                style={{
                    padding: "10px 18px",
                    border: "2px solid #000",
                    borderRadius: 8,
                    background: "#f5f5f5",
                    cursor: "pointer",
                }}
            >
                ← Back
            </button>


            <h1 style={{ fontSize: 32, marginTop: 16 }}>{venue?.name}</h1>

            {spaces.length === 0 && <p>No spaces available.</p>}

            <div style={{ marginTop: 24, display: "grid", gap: 20 }}>
                {spaces.map((s) => (
                    <div
                        key={s.id}
                        style={{
                            border: "4px solid black",
                            borderRadius: 16,
                            padding: 20,
                            background: "#e6e6e6",
                        }}
                    >
                        <h3>{s.name || "Unnamed Space"}</h3>
                        <p>{s.description || "No description"}</p>

                        <p>
                            <b>Size:</b> {s.space_width} × {s.space_height}
                        </p>

                        <p>
                            <b>Price/day:</b> ${s.price_per_day}
                        </p>

                        {!s.is_published && (
                            <p style={{ color: "red" }}>Not published</p>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}
