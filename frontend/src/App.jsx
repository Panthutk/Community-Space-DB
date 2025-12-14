import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Login from "./components/Login";
import Register from "./components/Register";
import Dashboard from "./components/Dashboard";
import CreateVenue from "./components/CreateVenue";
import VenueSpaces from "./components/VenueSpaces";
import Booking from "./components/Booking";
export default function App() {
  return (
    <div>
      <header style={{ fontFamily: "Georgia, serif", fontSize: 48, margin: "32px 64px" }}>
        Community Space
      </header>

      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/venues/create" element={<CreateVenue />} />
        <Route path="/venues/:venueId/spaces" element={<VenueSpaces />} />
        <Route path="/spaces/:spaceId/book" element={<Booking />} />
      </Routes>
    </div>
  );
}
