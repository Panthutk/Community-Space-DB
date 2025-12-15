import React, { useEffect, useState, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

// --- THAILAND TIMEZONE (UTC+7) Utilities ---
const THAILAND_OFFSET_MS = 7 * 60 * 60 * 1000;

const getThailandDate = () => {
    const now = new Date();
    const thailandTime = new Date(now.getTime() + THAILAND_OFFSET_MS);
    return new Date(Date.UTC(
        thailandTime.getUTCFullYear(),
        thailandTime.getUTCMonth(),
        thailandTime.getUTCDate(),
        0, 0, 0, 0
    ));
};

const createDateFromString = (dateStr) => {
    const [year, month, day] = dateStr.split('-').map(Number);
    return new Date(Date.UTC(year, month - 1, day, 0, 0, 0, 0));
};

const formatDate = (date) => {
    const year = date.getUTCFullYear();
    const month = String(date.getUTCMonth() + 1).padStart(2, '0');
    const day = String(date.getUTCDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
};

const addDays = (date, days) => {
    const result = new Date(date.getTime());
    result.setUTCDate(result.getUTCDate() + days);
    return result;
};

function getNextSevenDays() {
    const dates = [];
    const todayThailand = getThailandDate();
    let current = addDays(todayThailand, 1); // Start from tomorrow

    for (let i = 0; i < 7; i++) {
        dates.push({
            date: new Date(current.getTime()),
            dateStr: formatDate(current),
            day: current.getUTCDate(),
            month: current.getUTCMonth()
        });
        current = addDays(current, 1);
    }
    return dates;
}

export default function VenueSpaces() {
    const { venueId } = useParams();
    const navigate = useNavigate();
    const token = localStorage.getItem("token");

    const [venue, setVenue] = useState(null);
    const [spaces, setSpaces] = useState([]);
    const [loading, setLoading] = useState(true);
    const [reservationData, setReservationData] = useState({});

    const nextSevenDays = useMemo(() => getNextSevenDays(), []);

    useEffect(() => {
        async function fetchVenueData() {
            try {
                const venueRes = await fetch(`${API_BASE}/api/venues/${venueId}/spaces/`, {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                });
                if (!venueRes.ok) throw new Error("Failed to fetch venue data.");
                const data = await venueRes.json();
                
                setVenue(data.venue);
                setSpaces(data.spaces);

                const reservationPromises = data.spaces.map(s => 
                    s.is_published 
                        ? fetch(`${API_BASE}/api/bookings/${s.id}/reservations/`, {
                            headers: { Authorization: `Bearer ${token}` },
                          }).then(res => res.json().catch(() => []))
                        : Promise.resolve([])
                );

                const allReservations = await Promise.all(reservationPromises);
                
                const newReservationData = {};
                data.spaces.forEach((s, index) => {
                    const reservations = allReservations[index];
                    const disabledDates = new Set();
                    
                    console.log(`Space ${s.id} reservations:`, reservations);
                    
                    reservations.forEach(res => {
                        let current = createDateFromString(res.start);
                        const end = createDateFromString(res.end);
                        
                        while (current.getTime() <= end.getTime()) {
                            const dateStr = formatDate(current);
                            disabledDates.add(dateStr);
                            console.log(`  Marking ${dateStr} as reserved`);
                            current = addDays(current, 1);
                        }
                    });
                    newReservationData[s.id] = disabledDates;
                });
                
                setReservationData(newReservationData);
                setLoading(false);

            } catch (err) {
                console.error("Failed to load spaces or reservations", err);
                setLoading(false);
            }
        }
        
        if (token && venueId) {
            fetchVenueData();
        }
    }, [venueId, token]);

    if (loading) return <p>Loading spaces and availability...</p>;

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
                {spaces.map((s) => {
                    const disabledDates = reservationData[s.id] || new Set();

                    return (
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

                            {/* Display amenities*/}
                            {s.amenities_enabled && (
                                <p>
                                    <b>Amenities:</b> {Array.isArray(s.amenities) && s.amenities.length > 0 ? s.amenities.join(", ") : "None"}
                                </p>
                            )}
                            
                            <div style={{ marginTop: 15, marginBottom: 15, padding: '10px 0' }}>
                                <div style={{ fontWeight: 'bold', marginBottom: 5 }}>Available Dates For Reservation:</div>
                                <div style={{ display: 'flex', gap: 5, justifyContent: 'flex-start' }}>
                                    {nextSevenDays.map((day, index) => {
                                        const isAvailable = !disabledDates.has(day.dateStr);
                                        const backgroundColor = isAvailable ? '#5cb85c' : '#d9534f';
                                        const tooltipText = `${day.dateStr}: ${isAvailable ? 'Available' : 'Reserved'}`;
                                        const monthNames = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
                                        
                                        return (
                                            <div
                                                key={index}
                                                title={tooltipText}
                                                style={{
                                                    width: 40,
                                                    height: 40,
                                                    backgroundColor: backgroundColor,
                                                    borderRadius: 8,
                                                    display: 'flex',
                                                    flexDirection: 'column',
                                                    justifyContent: 'center',
                                                    alignItems: 'center',
                                                    color: 'white',
                                                    fontSize: 10,
                                                    fontWeight: 'bold',
                                                    border: '1px solid #00000030'
                                                }}
                                            >
                                                <span>{monthNames[day.month]}</span>
                                                <span>{day.day}</span>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>

                            {!s.is_published && (
                                <p style={{ color: "red" }}>Not published</p>
                            )}
                            
                            {s.is_published && (
                                <button
                                    onClick={() => navigate(`/spaces/${s.id}/book`)}
                                    style={{
                                        padding: "10px",
                                        background: "#7CFC7C",
                                        border: "2px solid #000",
                                        borderRadius: 8,
                                        marginTop: 10,
                                        cursor: "pointer",
                                    }}
                                >
                                    Book This Space
                                </button>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}