import { Drawer, ListItemButton, ListItemText, List } from '@mui/material'
import React from 'react'
import { useProtectedNavigation } from '../../ClientStuff/UserProtectedNav.js'
import '../CSS/Sidebar.css'

function Sidebar() {
    const { navigateWithAuth } = useProtectedNavigation()

    return (
        <Drawer
            variant="permanent"
            sx={{
            width: '15vw',
            flexShrink: 0,
            "& .MuiDrawer-paper": {
                width: '15vw',
                boxSizing: "border-box",
            },
            }}
        >
            {/* replace with a photo later or like logo */}
            <div className='top'>
                <h2>AI Tutor Guy</h2>
            </div>
            <List>
            <ListItemButton onClick={() => navigateWithAuth('/home')}>
                <ListItemText primary="Home" />
            </ListItemButton>

            <ListItemButton onClick={() => navigateWithAuth('/take_a_test')}>
                <ListItemText primary="Start Exam" />
            </ListItemButton>

            <ListItemButton>
                <ListItemText primary="Quick Actions" />
            </ListItemButton>

            <ListItemButton onClick={() => navigateWithAuth("/survival")}>
                <ListItemText primary="Survival" />
            </ListItemButton>

            <ListItemButton onClick={() => navigateWithAuth("/query")}>
                <ListItemText primary="Ask Tutor Guy" />
            </ListItemButton>

            <ListItemButton onClick={() => navigateWithAuth("/exam_history")}>
                <ListItemText primary="Exam History" />
            </ListItemButton>
            </List>
        </Drawer>
    )
}

export default Sidebar;
