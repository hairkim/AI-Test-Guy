import React from 'react';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';
import Menu from '@mui/material/Menu';
import Avatar from '@mui/material/Avatar';
import Tooltip from '@mui/material/Tooltip';
import MenuItem from '@mui/material/MenuItem';
import { useAuth } from '../../contexts/AuthContext.jsx';
import { useNavigate } from 'react-router-dom';

export default function ProfilePicture() {
    const navigate = useNavigate();
    const { user, userData, signOut } = useAuth();
    const settings = user ? ['Profile', 'Logout'] : ['Login', 'Sign Up'];

    const [anchorElUser, setAnchorElUser] = React.useState(null);
    const handleOpenUserMenu = (event) => {
      setAnchorElUser(event.currentTarget);
    };
    const handleCloseUserMenu = () => {
      setAnchorElUser(null);
    };

    const handleNavigation = async (page) => {
        switch (page) {
          case 'Profile':
            navigate('/profile');
            break;
          case 'Logout':
            console.log("signing out")
            await signOut();
            navigate('/');
            break;
          case 'Login':
            navigate('/login');
            break;
          case 'Sign Up':
            navigate('/signup');
            break;
        }
    }
    
    return (
        <div>
            <Box sx={{ flexGrow: 0 }}>
            <Tooltip title="Open settings">
              <IconButton onClick={handleOpenUserMenu} sx={{ p: 0 }}>
                <Avatar alt={userData?.name} src={userData?.picture_url} 
                sx={{ width: 70, height: 80 }}/>
              </IconButton>
            </Tooltip>
            <Menu
              sx={{ mt: '45px' }}
              id="menu-appbar"
              anchorEl={anchorElUser}
              anchorOrigin={{
                vertical: 'top',
                horizontal: 'right',
              }}
              keepMounted
              transformOrigin={{
                vertical: 'top',
                horizontal: 'right',
              }}
              open={Boolean(anchorElUser)}
              onClose={handleCloseUserMenu}
            >
              {settings.map((setting) => (
                <MenuItem key={setting} onClick={handleCloseUserMenu}>
                  <Typography onClick={() => handleNavigation(setting)} sx={{ textAlign: 'center' }}>{setting}</Typography>
                </MenuItem>
              ))}
            </Menu>
          </Box>
        </div>
    )
}
