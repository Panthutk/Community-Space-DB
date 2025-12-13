import React, { useEffect, useMemo, useRef, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

// fields we copy from base space -> other spaces
const COPY_FIELDS = [
  "space_width",
  "space_height",
  "price_per_day",
  "cleaning_fee",
  "is_published",
  "have_amenity",
  "amenities", // ✅ copy list too
];

const makeEmptySpace = () => ({
  name: "",
  description: "",
  space_width: 5,
  space_height: 5,
  price_per_day: 0,
  cleaning_fee: 0,
  is_published: true,

  have_amenity: false,
  amenity_input: "",   // UI-only
  amenities: [],       // ✅ multi amenities
});

function uniqAmenities(arr) {
  const seen = new Set();
  const out = [];
  for (const raw of arr) {
    const name = String(raw || "").trim();
    if (!name) continue;
    const key = name.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(name);
  }
  return out;
}

export default function CreateVenue() {
  const [venue, setVenue] = useState({
    name: "",
    description: "",
    location: "",
    venue_type: "WHOLE", // WHOLE or GRID
    contact: "",
    spaceGridCount: 1,
  });

  const [spaces, setSpaces] = useState([makeEmptySpace()]);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState("");

  // suggestions (shared)
  const [suggestions, setSuggestions] = useState([]);
  const [suggestForIndex, setSuggestForIndex] = useState(null);
  const [suggestOpen, setSuggestOpen] = useState(false);
  const suggestAbortRef = useRef(null);

  const isWhole = venue.venue_type === "WHOLE";
  const canEditCount = venue.venue_type !== "WHOLE";

  function updateVenue(key, value) {
    setVenue((v) => {
      const next = { ...v, [key]: value };
      if (key === "venue_type" && value === "WHOLE") {
        next.spaceGridCount = 1;
        setSpaces((prev) => prev.slice(0, 1));
      }
      return next;
    });
  }

  function setCount(newCount) {
    const count = Math.max(1, Number(newCount || 1));
    setVenue((v) => ({ ...v, spaceGridCount: count }));

    setSpaces((prev) => {
      const next = [...prev];
      if (count < next.length) return next.slice(0, count);
      while (next.length < count) next.push(makeEmptySpace());
      return next;
    });
  }

  function updateSpace(index, patch) {
    setSpaces((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], ...patch };

      // if amenities disabled, clear inputs + list
      if (patch.have_amenity === false) {
        next[index].amenity_input = "";
        next[index].amenities = [];
      }
      return next;
    });
  }

  function applyDefaultsToAll() {
    if (spaces.length <= 1) return;

    const base = spaces[0];
    setSpaces((prev) => {
      const next = [...prev];
      for (let i = 1; i < next.length; i++) {
        const copied = { ...next[i] };
        COPY_FIELDS.forEach((f) => {
          copied[f] = Array.isArray(base[f]) ? [...base[f]] : base[f];
        });
        // UI-only field should not be copied
        copied.amenity_input = "";
        next[i] = copied;
      }
      return next;
    });

    setMessage("✅ Defaults applied to all spaces.");
    setTimeout(() => setMessage(""), 1500);
  }

  // ---- Amenity UI helpers ----

  async function fetchAmenitySuggestions(q, index) {
    const query = (q || "").trim();
    if (!query) {
      setSuggestions([]);
      setSuggestOpen(false);
      return;
    }

    // cancel old request
    if (suggestAbortRef.current) suggestAbortRef.current.abort();
    const controller = new AbortController();
    suggestAbortRef.current = controller;

    try {
      const res = await fetch(`${API_BASE}/api/amenities/?q=${encodeURIComponent(query)}`, {
        signal: controller.signal,
      });
      const data = await res.json();
      if (!Array.isArray(data)) return;

      // filter out ones already selected in this space
      const chosen = new Set((spaces[index]?.amenities || []).map((a) => a.toLowerCase()));
      const filtered = data.filter((name) => !chosen.has(String(name).toLowerCase()));

      setSuggestions(filtered);
      setSuggestForIndex(index);
      setSuggestOpen(true);
    } catch (e) {
      // ignore aborted requests
      if (e?.name !== "AbortError") {
        setSuggestions([]);
        setSuggestOpen(false);
      }
    }
  }

  function addAmenity(index, name) {
    const trimmed = String(name || "").trim();
    if (!trimmed) return;

    setSpaces((prev) => {
      const next = [...prev];
      const s = { ...next[index] };
      s.amenities = uniqAmenities([...(s.amenities || []), trimmed]);
      s.amenity_input = "";
      next[index] = s;
      return next;
    });

    setSuggestions([]);
    setSuggestOpen(false);
  }

  function removeAmenity(index, name) {
    const key = String(name || "").toLowerCase();
    setSpaces((prev) => {
      const next = [...prev];
      const s = { ...next[index] };
      s.amenities = (s.amenities || []).filter((a) => String(a).toLowerCase() !== key);
      next[index] = s;
      return next;
    });
  }

  // close suggestions on click outside
  useEffect(() => {
    function onDocClick() {
      setSuggestOpen(false);
    }
    document.addEventListener("click", onDocClick);
    return () => document.removeEventListener("click", onDocClick);
  }, []);

  // ---- Submit ----

  async function onSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setMessage("");

    try {
      const payload = {
        venue: {
          name: venue.name,
          description: venue.description,
          location: venue.location,
          venue_type: venue.venue_type,
          contact: venue.contact,
        },
        spaces: spaces.map((s, idx) => ({
          name: s.name || (venue.venue_type === "WHOLE" ? "Entire Venue" : `Space ${idx + 1}`),
          description: s.description || "",
          space_width: String(s.space_width),
          space_height: String(s.space_height),
          price_per_day: String(s.price_per_day),
          cleaning_fee: s.cleaning_fee === "" || s.cleaning_fee === null ? null : String(s.cleaning_fee),
          is_published: !!s.is_published,

          have_amenity: !!s.have_amenity,
          amenities: s.have_amenity ? uniqAmenities(s.amenities || []) : [],
        })),
      };

      const res = await fetch(`${API_BASE}/api/venues/create-with-spaces/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data?.detail || JSON.stringify(data) || "Request failed");

      setMessage("✅ Created venue successfully!");
      setSpaces([makeEmptySpace()]);
      setVenue((v) => ({ ...v, name: "", description: "", location: "", contact: "", spaceGridCount: v.venue_type === "WHOLE" ? 1 : v.spaceGridCount }));
    } catch (err) {
      setMessage(`❌ ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div style={{ maxWidth: 980, margin: "24px auto", padding: 16 }}>
      <h1 style={{ fontSize: 40, marginBottom: 16 }}>Create Venue</h1>

      <form onSubmit={onSubmit} style={{ border: "4px solid #111", padding: 20, borderRadius: 16 }}>
        {/* Venue */}
        <div style={{ display: "grid", gap: 12 }}>
          <label>
            <div>Name</div>
            <input value={venue.name} onChange={(e) => updateVenue("name", e.target.value)} style={{ width: "100%", padding: 10 }} required />
          </label>

          <label>
            <div>Description</div>
            <textarea value={venue.description} onChange={(e) => updateVenue("description", e.target.value)} style={{ width: "100%", padding: 10, minHeight: 80 }} />
          </label>

          <label>
            <div>Location</div>
            <input value={venue.location} onChange={(e) => updateVenue("location", e.target.value)} style={{ width: "100%", padding: 10 }} />
          </label>

          <label>
            <div>Venue type</div>
            <select value={venue.venue_type} onChange={(e) => updateVenue("venue_type", e.target.value)} style={{ width: 260, padding: 10 }}>
              <option value="WHOLE">WHOLE (entire space)</option>
              <option value="GRID">GRID (multiple spaces)</option>
            </select>
          </label>

          <label>
            <div>Contact</div>
            <input value={venue.contact} onChange={(e) => updateVenue("contact", e.target.value)} style={{ width: "100%", padding: 10 }} />
          </label>

          <label>
            <div>SpaceGrid count</div>
            <input
              type="number"
              min={1}
              value={venue.spaceGridCount}
              disabled={!canEditCount}
              onChange={(e) => setCount(e.target.value)}
              style={{ width: 140, padding: 10, opacity: canEditCount ? 1 : 0.6 }}
            />
            {isWhole && <div style={{ fontSize: 12, opacity: 0.7 }}>Locked to 1 when WHOLE</div>}
          </label>
        </div>

        {/* Spaces */}
        <div style={{ marginTop: 22 }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center" }}>
            <div style={{ fontSize: 22, fontWeight: 700 }}>SpaceGrid</div>
            <button type="button" onClick={applyDefaultsToAll} disabled={spaces.length <= 1} style={{ padding: "8px 12px" }}>
              Apply defaults to all spaces
            </button>
          </div>

          <div style={{ display: "grid", gap: 16, marginTop: 12 }}>
            {spaces.map((s, idx) => (
              <div key={idx} style={{ border: "4px solid #111", borderRadius: 16, padding: 16 }}>
                <div style={{ fontWeight: 800, marginBottom: 10 }}>
                  Space #{idx + 1} {idx === 0 ? "(base card)" : ""}
                </div>

                <div style={{ display: "grid", gap: 10 }}>
                  <label>
                    <div>SpaceName</div>
                    <input value={s.name} onChange={(e) => updateSpace(idx, { name: e.target.value })} style={{ width: "100%", padding: 10 }} />
                  </label>

                  <label>
                    <div>SpaceDescription</div>
                    <textarea value={s.description} onChange={(e) => updateSpace(idx, { description: e.target.value })} style={{ width: "100%", padding: 10, minHeight: 70 }} />
                  </label>

                  <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                    <label>
                      <div>width</div>
                      <input type="number" value={s.space_width} onChange={(e) => updateSpace(idx, { space_width: Number(e.target.value) })} style={{ width: 160, padding: 10 }} />
                    </label>

                    <label>
                      <div>height</div>
                      <input type="number" value={s.space_height} onChange={(e) => updateSpace(idx, { space_height: Number(e.target.value) })} style={{ width: 160, padding: 10 }} />
                    </label>

                    <label>
                      <div>price_per_day</div>
                      <input type="number" value={s.price_per_day} onChange={(e) => updateSpace(idx, { price_per_day: Number(e.target.value) })} style={{ width: 200, padding: 10 }} />
                    </label>

                    <label>
                      <div>cleaning_fee</div>
                      <input type="number" value={s.cleaning_fee} onChange={(e) => updateSpace(idx, { cleaning_fee: Number(e.target.value) })} style={{ width: 200, padding: 10 }} />
                    </label>
                  </div>

                  <div style={{ display: "flex", gap: 16, alignItems: "center", flexWrap: "wrap" }}>
                    <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
                      <input type="checkbox" checked={s.is_published} onChange={(e) => updateSpace(idx, { is_published: e.target.checked })} />
                      is_published
                    </label>

                    <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
                      <input type="checkbox" checked={s.have_amenity} onChange={(e) => updateSpace(idx, { have_amenity: e.target.checked })} />
                      have_amenity
                    </label>
                  </div>

                  {/* Amenities */}
                  <div style={{ marginTop: 6 }}>
                    <div style={{ fontWeight: 700, marginBottom: 6 }}>Amenities</div>

                    {/* selected tags */}
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 10 }}>
                      {(s.amenities || []).map((a) => (
                        <span key={a} style={{ border: "2px solid #111", padding: "4px 8px", borderRadius: 999, display: "inline-flex", gap: 8, alignItems: "center" }}>
                          {a}
                          <button type="button" onClick={() => removeAmenity(idx, a)} style={{ border: "none", background: "transparent", cursor: "pointer" }}>
                            ✕
                          </button>
                        </span>
                      ))}
                    </div>

                    {/* input + suggestions */}
                    <div style={{ position: "relative", maxWidth: 520 }}>
                      <div style={{ display: "flex", gap: 8 }}>
                        <input
                          value={s.amenity_input}
                          disabled={!s.have_amenity}
                          onClick={(e) => {
                            e.stopPropagation();
                            setSuggestForIndex(idx);
                            setSuggestOpen(true);
                          }}
                          onChange={(e) => {
                            const val = e.target.value;
                            updateSpace(idx, { amenity_input: val });
                            fetchAmenitySuggestions(val, idx);
                          }}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") {
                              e.preventDefault();
                              addAmenity(idx, s.amenity_input);
                            }
                          }}
                          placeholder={s.have_amenity ? "Type amenity (Wi-Fi), press Add" : "(disabled)"}
                          style={{ width: "100%", padding: 10, opacity: s.have_amenity ? 1 : 0.6 }}
                        />
                        <button type="button" disabled={!s.have_amenity} onClick={() => addAmenity(idx, s.amenity_input)} style={{ padding: "10px 12px" }}>
                          Add
                        </button>
                      </div>

                      {suggestOpen && suggestForIndex === idx && s.have_amenity && suggestions.length > 0 && (
                        <div
                          onClick={(e) => e.stopPropagation()}
                          style={{
                            position: "absolute",
                            top: "44px",
                            left: 0,
                            right: 0,
                            border: "2px solid #111",
                            background: "#fff",
                            zIndex: 10,
                            maxHeight: 180,
                            overflow: "auto",
                          }}
                        >
                          {suggestions.map((name) => (
                            <div
                              key={name}
                              style={{ padding: "8px 10px", cursor: "pointer" }}
                              onClick={() => addAmenity(idx, name)}
                            >
                              {name}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    <div style={{ fontSize: 12, opacity: 0.75, marginTop: 6 }}>
                      Suggestions come from existing amenities in DB. You can also add a new name.
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {message && <div style={{ marginTop: 14, fontWeight: 700 }}>{message}</div>}

        <div style={{ display: "flex", justifyContent: "flex-end", gap: 12, marginTop: 18 }}>
          <button type="button" style={{ padding: "10px 18px" }} onClick={() => window.history.back()} disabled={submitting}>
            cancel
          </button>
          <button type="submit" style={{ padding: "10px 18px", background: "#7CFC7C" }} disabled={submitting}>
            {submitting ? "Submitting..." : "confirmation"}
          </button>
        </div>
      </form>
    </div>
  );
}
