import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";

// Base API URL. Defaults to local development server if env not provided.
const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

/**
 * VenueReviews component
 *
 * Displays a list of reviews for a given venue. Each review shows a star
 * rating and optional comment. A button allows the user to navigate to the
 * create review page for the same venue. Users must be authenticated; if
 * not, they are redirected to the login page.
 */
export default function VenueReviews() {
  const { venueId } = useParams();
  const navigate = useNavigate();
  const token = localStorage.getItem("token");

  const [reviews, setReviews] = useState([]);
  const [venueName, setVenueName] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!token) {
      navigate("/login");
      return;
    }
    async function fetchData() {
      try {
        setLoading(true);
        // Fetch venue details to show its name
        const venueRes = await fetch(`${API_BASE}/api/venues/${venueId}/`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (venueRes.ok) {
          const vd = await venueRes.json();
          setVenueName(vd.name || "");
        }
        // Fetch all reviews for this venue via the API query param
        const res = await fetch(`${API_BASE}/api/reviews/?venue=${venueId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) {
          throw new Error("Failed to fetch reviews.");
        }
        const data = await res.json();
        setReviews(data);
        setError(null);
      } catch (err) {
        console.error(err);
        setError(err.message || "An error occurred fetching reviews.");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [venueId, token, navigate]);

  // Helper to render stars for a rating
  const renderStars = (count) => {
    const stars = [];
    for (let i = 1; i <= 5; i++) {
      stars.push(
        <span
          key={i}
          style={{ fontSize: 20, color: i <= count ? "#FFD700" : "#A9A9A9" }}
        >
          {i <= count ? "★" : "☆"}
        </span>
      );
    }
    return <div>{stars}</div>;
  };

  if (loading) {
    return (
      <p style={{ textAlign: "center", marginTop: 40 }}>Loading reviews...</p>
    );
  }

  return (
    <div style={{ maxWidth: 800, margin: "24px auto", padding: 16 }}>
      {/* Back button */}
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

      {/* Reviews card */}
      <div
        style={{
          border: "4px solid #000",
          borderRadius: 16,
          padding: 24,
          background: "#e6e6e6",
          marginTop: 20,
        }}
      >
        <h1 style={{ marginBottom: 16 }}>
          Reviews for {venueName || "Venue"}
        </h1>
        {reviews.length === 0 && <p>No reviews yet.</p>}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {reviews.map((r) => (
            <div
              key={r.id}
              style={{
                border: "2px solid #000",
                borderRadius: 12,
                padding: 16,
                background: "#fff",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                {/* Reviewer name */}
                <span style={{ fontWeight: 600 }}>{r.reviewer_name || "Anonymous"}</span>
                {/* Star rating */}
                {renderStars(r.rating)}
              </div>
              {r.comment && (
                <p style={{ marginTop: 8, whiteSpace: "pre-wrap" }}>{r.comment}</p>
              )}
            </div>
          ))}
        </div>
        {/* Button to create a new review */}
        <button
          onClick={() => navigate(`/venues/${venueId}/review`)}
          style={{
            marginTop: 24,
            padding: "10px 20px",
            border: "2px solid #000",
            borderRadius: 8,
            background: "#90EE90",
            cursor: "pointer",
          }}
        >
          Create your review
        </button>
      </div>
      {error && (
        <p style={{ color: "#D70040", marginTop: 16 }}>{error}</p>
      )}
    </div>
  );
}