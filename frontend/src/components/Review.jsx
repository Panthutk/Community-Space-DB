import React, { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";

// Base API URL. Falls back to localhost when not provided by the build env.
const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

/**
 * Review page component.
 *
 * This page allows a logged‑in user to leave a review for a specific venue.
 * A review consists of a required star rating (1–5) and an optional comment.
 * If the user decides not to review, they can simply navigate back via the
 * provided Back button. The page fetches the venue name for display but
 * gracefully handles cases where it fails to load.
 */
export default function Review() {
  const { venueId } = useParams();
  const navigate = useNavigate();
  const token = localStorage.getItem("token");

  // Local state for venue information, rating, comment and feedback messages.
  const [venueName, setVenueName] = useState("Venue");
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [comment, setComment] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState(null);

  // Redirect unauthenticated users to the login page.
  useEffect(() => {
    if (!token) {
      navigate("/login");
      return;
    }
    // Fetch venue details for display. We do not block the UI on failure.
    async function fetchVenue() {
      try {
        const res = await fetch(`${API_BASE}/api/venues/${venueId}/`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const data = await res.json();
          setVenueName(data.name || "Venue");
        }
      } catch (err) {
        // Silently ignore fetch errors; venueName remains the default value.
        console.error("Failed to fetch venue info", err);
      }
    }
    fetchVenue();
  }, [venueId, token, navigate]);

  /**
   * Submit the review to the backend. A rating of 0 (no stars selected)
   * indicates the user hasn't actually provided a review, so we prevent
   * submission in that case and prompt for a rating instead.
   */
  async function handleSubmit() {
    // Guard against submission without a rating.
    if (rating === 0) {
      alert("Please select a star rating before submitting your review.");
      return;
    }

    setError(null);
    try {
      const payload = {
        venue: Number(venueId),
        rating,
        comment: comment.trim(),
      };
      const res = await fetch(`${API_BASE}/api/reviews/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(
          data?.detail || data?.message || "Failed to submit review."
        );
      }
      setSubmitted(true);
    } catch (err) {
      console.error("Review submission error:", err);
      setError(err.message);
    }
  }

  // Render a simple thank‑you view after submission.
  if (submitted) {
    return (
      <div
        style={{
          maxWidth: 600,
          margin: "40px auto",
          padding: 20,
          textAlign: "center",
          border: "4px solid #000",
          borderRadius: 16,
          background: "#e6e6e6",
        }}
      >
        <h2>Thank you for your review!</h2>
        <p>Your feedback helps improve the community space.</p>
        <button
          onClick={() => navigate(-1)}
          style={{
            marginTop: 20,
            padding: "10px 18px",
            border: "2px solid #000",
            borderRadius: 8,
            background: "#7CFC7C",
          }}
        >
          ← Back
        </button>
      </div>
    );
  }

  // Helper to render a single star. Uses Unicode characters for simplicity.
  const renderStar = (starValue) => {
    const isActive = starValue <= (hoverRating || rating);
    return (
      <span
        key={starValue}
        style={{
          cursor: "pointer",
          fontSize: 32,
          color: isActive ? "#FFD700" : "#A9A9A9",
          userSelect: "none",
        }}
        onClick={() => setRating(starValue)}
        onMouseEnter={() => setHoverRating(starValue)}
        onMouseLeave={() => setHoverRating(0)}
      >
        {isActive ? "★" : "☆"}
      </span>
    );
  };

  return (
    <div style={{ maxWidth: 700, margin: "24px auto", padding: 16 }}>
      {/* Back Button */}
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

      {/* Review Card */}
      <div
        style={{
          border: "4px solid black",
          borderRadius: 16,
          padding: 24,
          background: "#e6e6e6",
          marginTop: 20,
        }}
      >
        <h1 style={{ marginBottom: 12 }}>Review {venueName}</h1>
        <p style={{ marginBottom: 20 }}>
          Please select a star rating and leave a comment (optional).
        </p>

        {/* Star Rating */}
        <div style={{ marginBottom: 20 }}>
          {[1, 2, 3, 4, 5].map((n) => renderStar(n))}
        </div>

        {/* Comment Field */}
        <div style={{ marginBottom: 20 }}>
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Leave your comment here (optional)"
            rows={4}
            style={{
              width: "100%",
              padding: 10,
              border: "2px solid #000",
              borderRadius: 8,
              fontFamily: "inherit",
              fontSize: 16,
              resize: "vertical",
            }}
          />
        </div>

        {/* Submit and Skip Buttons */}
        <div style={{ display: "flex", gap: 12 }}>
          <button
            onClick={handleSubmit}
            style={{
              padding: "10px 20px",
              background: "#7CFC7C",
              border: "2px solid #000",
              borderRadius: 8,
              cursor: "pointer",
            }}
          >
            Submit Review
          </button>
          <button
            onClick={() => navigate(-1)}
            style={{
              padding: "10px 20px",
              background: "#FFD966",
              border: "2px solid #000",
              borderRadius: 8,
              cursor: "pointer",
            }}
          >
            Skip
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <p style={{ color: "#D70040", marginTop: 16 }}>{error}</p>
        )}
      </div>
    </div>
  );
}