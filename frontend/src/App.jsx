import React, { useEffect, useState } from "react";

const apiBase = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function App() {
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${apiBase}/api/items/`)
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(data => setItems(data))
      .catch(e => setError(e.message));
  }, []);

  return (
    <div style={{ padding: 24 }}>
      <h1>Community Space — Items</h1>

      {error && <p style={{ color: "red" }}>Error: {error}</p>}

      <ul>
        {items.map(item => (
          <li key={item.id}>
            {item.name} — {item.description}
          </li>
        ))}
      </ul>
    </div>
  );
}
