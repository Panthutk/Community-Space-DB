import React, { useEffect, useState, useMemo } from "react";
import { useNavigate, useParams } from "react-router-dom";
import qrImage from "../assets/qr-code.png";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

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

const setupInitialDates = () => {
    const todayThailand = getThailandDate();

    // Tomorrow is the minimum booking date
    const tomorrow = addDays(todayThailand, 1);

    // Maximum is tomorrow + 6 days (7 day window starting from tomorrow)
    const maxDate = addDays(tomorrow, 6);

    return {
        minDate: formatDate(tomorrow),
        maxDate: formatDate(maxDate)
    };
};

function getDisabledDates(reservations) {
    const disabledDates = new Set();

    for (const res of reservations) {
        let current = createDateFromString(res.start);
        const end = createDateFromString(res.end);

        while (current.getTime() <= end.getTime()) {
            disabledDates.add(formatDate(current));
            current = addDays(current, 1);
        }
    }

    return disabledDates;
}

function getNextSevenDays(minDateStr) {
    const dates = [];
    let current = createDateFromString(minDateStr);

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

const INITIAL_BOUNDS = setupInitialDates();

export default function Booking() {
    const { spaceId } = useParams();
    const navigate = useNavigate();
    const token = localStorage.getItem("token");

    const [bookingData, setBookingData] = useState({
        SpaceName: "Loading...",
        SpaceDescription: "Fetching space details...",
        width: "0m",
        height: "0m",
        PricePerDay: 0,
        CleaningFee: 0,
        amenities: [],
    });
    const [reservations, setReservations] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const minDate = INITIAL_BOUNDS.minDate;
    const maxDate = INITIAL_BOUNDS.maxDate;

    const [currentPage, setCurrentPage] = useState("booking");
    const [startDate, setStartDate] = useState(minDate);
    const [endDate, setEndDate] = useState(minDate); // Start with just tmr

    const disabledDates = useMemo(() => getDisabledDates(reservations), [reservations]);
    const nextSevenDays = useMemo(() => getNextSevenDays(minDate), [minDate]);

    const validateDates = (startStr, endStr) => {
        if (!startStr || !endStr) return true;

        let current = createDateFromString(startStr);
        const end = createDateFromString(endStr);

        while (current.getTime() <= end.getTime()) {
            if (disabledDates.has(formatDate(current))) {
                return false;
            }
            current = addDays(current, 1);
        }

        return true;
    };

    const calculateDays = () => {
        const start = createDateFromString(startDate);
        const end = createDateFromString(endDate);
        const diffTime = end.getTime() - start.getTime();
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
        return diffDays > 0 ? diffDays : 0;
    };

    const totalDays = calculateDays();
    const baseCost = totalDays * bookingData.PricePerDay;
    const totalCost = baseCost + bookingData.CleaningFee;

    const handleContinue = () => {
        if (!validateDates(startDate, endDate)) {
            alert("Selected dates overlap with an existing reservation. Please choose different dates.");
            return;
        }
        setCurrentPage("qr");
    };

    const handleConfirm = async () => {
        const payload = {
            StartDate: startDate,
            EndDate: endDate,
            totalCost: totalCost,
        };

        try {
            const res = await fetch(`${API_BASE}/api/bookings/${spaceId}/confirm/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify(payload),
            });

            const data = await res.json().catch(() => ({}));
            if (!res.ok) {
                throw new Error(data?.detail || JSON.stringify(data) || "Booking failed.");
            }

            setCurrentPage("confirmed");

        } catch (error) {
            console.error("Booking submission error:", error);
            alert(`Booking submission error: ${error.message}`);
            setCurrentPage("booking");
        }
    };

    useEffect(() => {
        async function fetchData() {
            if (!token) {
                navigate("/login");
                return;
            }

            try {
                setLoading(true);
                setError(null);

                const spaceRes = await fetch(`${API_BASE}/api/spaces/${spaceId}/`, {
                    headers: { Authorization: `Bearer ${token}` },
                });
                if (!spaceRes.ok) throw new Error("Failed to fetch space data.");
                const spaceData = await spaceRes.json();

                setBookingData({
                    SpaceName: spaceData.name,
                    SpaceDescription: spaceData.description,
                    width: spaceData.space_width + 'm',
                    height: spaceData.space_height + 'm',
                    PricePerDay: Number(spaceData.price_per_day),
                    CleaningFee: Number(spaceData.cleaning_fee || 0),
                    amenities: spaceData.amenities_enabled ? (Array.isArray(spaceData.amenities) ? spaceData.amenities : []) : [],
                });

                const resRes = await fetch(`${API_BASE}/api/bookings/${spaceId}/reservations/`, {
                    headers: { Authorization: `Bearer ${token}` },
                });
                if (!resRes.ok) throw new Error("Failed to fetch reservations.");
                const resData = await resRes.json();

                console.log("Fetched reservations:", resData); // Debug log
                setReservations(resData);

            } catch (err) {
                console.error("Fetch Data Error:", err);
                setError("Failed to load booking data. Check network/server configuration.");
            } finally {
                setLoading(false);
            }
        }

        if (spaceId) {
            fetchData();
        }
    }, [spaceId, navigate, token]);

    if (loading) return <p style={{ textAlign: 'center', marginTop: '50px' }}>Loading space details...</p>;
    if (error) return <p style={{ textAlign: 'center', color: 'red', marginTop: '50px' }}>Error: {error}</p>;

    const dateOverlap = !validateDates(startDate, endDate);

    const styles = {
        container: {
            minHeight: "100vh",
            backgroundColor: "#f9fafb",
            padding: "24px"
        },
        maxWidth: {
            maxWidth: "1200px",
            margin: "0 auto"
        },
        title: {
            fontSize: "36px",
            fontWeight: "bold",
            textAlign: "center",
            marginBottom: "32px"
        },
        gridContainer: {
            display: "grid",
            gridTemplateColumns: "2fr 1fr",
            gap: "24px"
        },
        leftColumn: {
            display: "flex",
            flexDirection: "column",
            gap: "24px"
        },
        card: {
            backgroundColor: "white",
            padding: "24px",
            border: "4px solid black",
            borderRadius: "24px"
        },
        cardContent: {
            display: "flex",
            flexDirection: "column",
            gap: "16px"
        },
        label: {
            fontWeight: "600",
            fontSize: "18px"
        },
        labelRed: {
            fontWeight: "600",
            fontSize: "18px",
            color: "#dc2626"
        },
        value: {
            color: "#374151",
            marginTop: "4px"
        },
        dimensionRow: {
            display: "flex",
            gap: "48px"
        },
        rightColumn: {
            position: "sticky",
            top: "24px",
            height: "fit-content"
        },
        costRow: {
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "12px"
        },
        costLabel: {
            color: "#374151"
        },
        costValue: {
            fontWeight: "600",
            fontSize: "18px"
        },
        divider: {
            borderTop: "2px solid #d1d5db",
            paddingTop: "12px",
            marginTop: "12px"
        },
        totalRow: {
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center"
        },
        totalLabel: {
            fontWeight: "bold",
            color: "#dc2626",
            fontSize: "20px"
        },
        totalValue: {
            fontWeight: "bold",
            fontSize: "20px"
        },
        button: {
            width: "100%",
            backgroundColor: "#22c55e",
            color: "white",
            fontWeight: "bold",
            fontSize: "18px",
            borderRadius: "16px",
            padding: "16px 24px",
            border: "none",
            cursor: "pointer",
            marginTop: "24px",
            boxShadow: "0 4px 6px rgba(0,0,0,0.1)"
        },
        qrContainer: {
            minHeight: "100vh",
            backgroundColor: "#f9fafb",
            padding: "24px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center"
        },
        qrCard: {
            maxWidth: "500px",
            width: "100%",
            backgroundColor: "white",
            padding: "32px",
            border: "4px solid black",
            borderRadius: "24px",
            textAlign: "center"
        },
        qrTitle: {
            fontSize: "30px",
            fontWeight: "bold",
            marginBottom: "24px"
        },
        qrInfo: {
            backgroundColor: "#f3f4f6",
            padding: "24px",
            borderRadius: "16px",
            marginBottom: "24px"
        },
        qrPrice: {
            fontSize: "32px",
            fontWeight: "bold",
            marginBottom: "12px"
        },
        qrImageContainer: {
            backgroundColor: "white",
            padding: "16px",
            display: "inline-block",
            borderRadius: "12px",
            border: "4px solid #d1d5db",
            marginBottom: "24px"
        },
        qrImage: {
            width: "256px",
            height: "256px"
        },
        backButton: {
            width: "100%",
            backgroundColor: "#d1d5db",
            color: "#1f2937",
            fontWeight: "600",
            borderRadius: "16px",
            padding: "12px 24px",
            border: "none",
            cursor: "pointer",
            marginTop: "12px"
        },
        confirmButton: {
            width: "100%",
            backgroundColor: "#3b82f6",
            color: "white",
            fontWeight: "bold",
            fontSize: "18px",
            borderRadius: "16px",
            padding: "16px 24px",
            border: "none",
            cursor: "pointer",
            boxShadow: "0 4px 6px rgba(0,0,0,0.1)"
        },
        successCard: {
            maxWidth: "500px",
            width: "100%",
            backgroundColor: "white",
            padding: "32px",
            border: "4px solid #22c55e",
            borderRadius: "24px",
            textAlign: "center"
        },
        checkmark: {
            fontSize: "80px",
            color: "#22c55e",
            marginBottom: "24px"
        },
        successTitle: {
            fontSize: "30px",
            fontWeight: "bold",
            color: "#15803d",
            marginBottom: "16px"
        },
        successMessage: {
            fontSize: "20px",
            color: "#374151",
            marginBottom: "24px"
        },
        summaryBox: {
            backgroundColor: "#f9fafb",
            padding: "24px",
            borderRadius: "16px",
            textAlign: "left",
            marginBottom: "24px"
        },
        summaryTitle: {
            fontWeight: "bold",
            fontSize: "18px",
            marginBottom: "12px",
            textAlign: "center"
        },
        summaryItem: {
            fontSize: "14px",
            marginBottom: "4px"
        }
    };

    if (currentPage === "booking") {
        return (
            <div style={styles.container}>
                <div style={styles.maxWidth}>
                    <h1 style={styles.title}>Booking</h1>

                    <div style={styles.gridContainer}>
                        <div style={styles.leftColumn}>
                            <div style={styles.card}>
                                <div style={styles.cardContent}>
                                    <div>
                                        <div style={styles.labelRed}>Space Name:</div>
                                        <div style={styles.value}>{bookingData.SpaceName}</div>
                                    </div>

                                    <div>
                                        <div style={styles.label}>Space Description:</div>
                                        <div style={styles.value}>{bookingData.SpaceDescription}</div>
                                    </div>

                                    <div style={styles.dimensionRow}>
                                        <div>
                                            <span style={styles.label}>width:</span>
                                            <span style={{ ...styles.value, marginLeft: "12px" }}>{bookingData.width}</span>
                                        </div>
                                        <div>
                                            <span style={styles.label}>height:</span>
                                            <span style={{ ...styles.value, marginLeft: "12px" }}>{bookingData.height}</span>
                                        </div>
                                    </div>

                                    <div>
                                        <div style={styles.label}>price per day</div>
                                        <div style={styles.value}>${bookingData.PricePerDay}</div>
                                    </div>

                                    <div>
                                        <div style={styles.label}>cleaning fee</div>
                                        <div style={styles.value}>${bookingData.CleaningFee}</div>
                                    </div>

                                    {/* display amenities for this space.  If the list is empty,
                                        display 'None'. */}
                                    <div>
                                        <div style={styles.label}>amenities:</div>
                                        {Array.isArray(bookingData.amenities) && bookingData.amenities.length > 0 ? (
                                            <div style={{ ...styles.value }}>
                                                {bookingData.amenities.join(", ")}
                                            </div>
                                        ) : (
                                            <div style={styles.value}>None</div>
                                        )}
                                    </div>
                                </div>
                            </div>

                            <div style={styles.card}>
                                <div style={{ ...styles.cardContent, position: 'relative', flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' }}>

                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                                        <div>
                                            <div style={styles.labelRed}>start date:</div>
                                            <input
                                                type="date"
                                                value={startDate}
                                                min={minDate}
                                                max={maxDate}
                                                onChange={(e) => {
                                                    setStartDate(e.target.value);
                                                    if (e.target.value > endDate) {
                                                        setEndDate(e.target.value);
                                                    }
                                                }}
                                                style={{
                                                    padding: "12px",
                                                    borderRadius: "12px",
                                                    border: "2px solid #d1d5db",
                                                    fontSize: "16px"
                                                }}
                                            />
                                        </div>

                                        <div>
                                            <div style={styles.labelRed}>end date:</div>
                                            <input
                                                type="date"
                                                value={endDate}
                                                min={startDate}
                                                max={maxDate}
                                                onChange={(e) => setEndDate(e.target.value)}
                                                style={{
                                                    padding: "12px",
                                                    borderRadius: "12px",
                                                    border: "2px solid #d1d5db",
                                                    fontSize: "16px"
                                                }}
                                            />
                                        </div>
                                        {dateOverlap && (
                                            <p style={{ color: 'red', fontWeight: 'bold', marginTop: '10px' }}>
                                                ⚠️ Selected range includes already reserved dates.
                                            </p>
                                        )}
                                    </div>

                                    <div
                                        style={{
                                            position: 'absolute',
                                            top: 0,
                                            right: 0,
                                            padding: '10px 0',
                                            maxWidth: 320,
                                            textAlign: 'center'
                                        }}
                                    >
                                        <div style={{ fontWeight: 'bold', marginBottom: 5, fontSize: 16 }}>Available Dates For Reservation:</div>
                                        <div style={{ display: 'flex', gap: 5, justifyContent: 'flex-end' }}>
                                            {nextSevenDays.map((day, index) => {
                                                const isAvailable = !disabledDates.has(day.dateStr);
                                                const backgroundColor = isAvailable ? '#5cb85c' : '#d9534f';
                                                const tooltipText = `${day.dateStr}: ${isAvailable ? 'Available' : 'Reserved'}`;
                                                const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

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
                                </div>
                            </div>
                        </div>

                        <div style={styles.rightColumn}>
                            <div style={styles.card}>
                                <h2 style={{ fontSize: "24px", fontWeight: "bold", textAlign: "center", marginBottom: "24px" }}>
                                    Total Cost
                                </h2>

                                <div>
                                    <div style={styles.costRow}>
                                        <span style={styles.costLabel}>start - end ({totalDays} {totalDays === 1 ? 'day' : 'days'})</span>
                                        <span style={styles.costValue}>{baseCost} $</span>
                                    </div>
                                    <div style={styles.costRow}>
                                        <span style={styles.costLabel}>cleaning</span>
                                        <span style={styles.costValue}>{bookingData.CleaningFee} $</span>
                                    </div>
                                    <div style={styles.costRow}>
                                        <span style={styles.costLabel}>amenity</span>
                                        <span style={styles.costValue}>Free</span>
                                    </div>

                                    <div style={styles.divider}>
                                        <div style={styles.totalRow}>
                                            <span style={styles.totalLabel}>Total Price</span>
                                            <span style={styles.totalValue}>{totalCost} $</span>
                                        </div>
                                    </div>
                                </div>

                                <button
                                    style={{
                                        ...styles.button,
                                        opacity: dateOverlap ? 0.5 : 1,
                                        cursor: dateOverlap ? 'not-allowed' : 'pointer'
                                    }}
                                    onClick={handleContinue}
                                    disabled={dateOverlap}
                                    onMouseEnter={(e) => !dateOverlap && (e.target.style.backgroundColor = "#16a34a")}
                                    onMouseLeave={(e) => !dateOverlap && (e.target.style.backgroundColor = "#22c55e")}
                                >
                                    {dateOverlap ? "Cannot Continue (Dates Reserved)" : "Continue to QR Payment"}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    if (currentPage === "qr") {
        return (
            <div style={styles.qrContainer}>
                <div style={styles.qrCard}>
                    <h2 style={styles.qrTitle}>Scan to Pay</h2>

                    <div style={styles.qrInfo}>
                        <p style={styles.qrPrice}>${totalCost}</p>
                        <p style={{ color: "#374151", fontWeight: "600" }}>{bookingData.SpaceName}</p>
                        <p style={{ color: "#6b7280", fontSize: "14px", marginTop: "8px" }}>
                            {startDate} to {endDate}
                        </p>
                        <p style={{ color: "#6b7280", fontSize: "14px" }}>
                            ({totalDays} {totalDays === 1 ? 'day' : 'days'})
                        </p>
                    </div>

                    <div style={styles.qrImageContainer}>
                        <img
                            src={qrImage}
                            alt="Payment QR"
                            style={styles.qrImage}
                        />
                    </div>

                    <p style={{ color: "#6b7280", marginBottom: "24px" }}>
                        Please scan the QR code to complete your payment
                    </p>

                    <button
                        style={styles.confirmButton}
                        onClick={handleConfirm}
                        onMouseEnter={(e) => e.target.style.backgroundColor = "#2563eb"}
                        onMouseLeave={(e) => e.target.style.backgroundColor = "#3b82f6"}
                    >
                        Confirm Payment
                    </button>

                    <button
                        style={styles.backButton}
                        onClick={() => setCurrentPage("booking")}
                        onMouseEnter={(e) => e.target.style.backgroundColor = "#9ca3af"}
                        onMouseLeave={(e) => e.target.style.backgroundColor = "#d1d5db"}
                    >
                        ← Back
                    </button>
                </div>
            </div>
        );
    }

    if (currentPage === "confirmed") {
        return (
            <div style={styles.qrContainer}>
                <div style={styles.successCard}>
                    <div style={styles.checkmark}>✓</div>

                    <h2 style={styles.successTitle}>Payment Successful</h2>

                    <p style={styles.successMessage}>
                        Your booking has been confirmed. Thank you for your reservation!
                    </p>

                    <div style={styles.summaryBox}>
                        <p style={styles.summaryTitle}>Booking Summary</p>
                        <p style={styles.summaryItem}>
                            <span style={{ fontWeight: "600" }}>Space:</span> {bookingData.SpaceName}
                        </p>
                        <p style={styles.summaryItem}>
                            <span style={{ fontWeight: "600" }}>Check-in:</span> {startDate}
                        </p>
                        <p style={styles.summaryItem}>
                            <span style={{ fontWeight: "600" }}>Check-out:</span> {endDate}
                        </p>
                        <p style={styles.summaryItem}>
                            <span style={{ fontWeight: "600" }}>Duration:</span> {totalDays} {totalDays === 1 ? 'day' : 'days'}
                        </p>
                        <div style={{ borderTop: "2px solid #d1d5db", paddingTop: "8px", marginTop: "12px" }}>
                            <p style={{ fontSize: "16px", fontWeight: "bold" }}>
                                <span>Total Paid:</span> ${totalCost}
                            </p>
                        </div>
                    </div>

                    <button
                        style={styles.button}
                        onClick={() => {
                            navigate("/dashboard");
                            setCurrentPage("");
                        }}
                        onMouseEnter={(e) => e.target.style.backgroundColor = "#16a34a"}
                        onMouseLeave={(e) => e.target.style.backgroundColor = "#22c55e"}
                    >
                        Done
                    </button>
                </div>
            </div>
        );
    }
}