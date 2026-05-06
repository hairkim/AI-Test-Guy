import { Box } from "@mui/material";
import { Outlet } from "react-router-dom";
import Sidebar from "../SupportingComponents/Sidebar.jsx";
import React from 'react'

export default function DashboardLayout() {
  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
      <Sidebar />

      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Outlet />
      </Box>
    </Box>
  );
}