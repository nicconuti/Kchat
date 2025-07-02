import React, { useState } from 'react';
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Avatar,
  Chip,
  Divider,
  Paper,
  useTheme,
  useMediaQuery,
  SwipeableDrawer,
  BottomNavigation,
  BottomNavigationAction,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Settings as SettingsIcon,
  Chat as ChatIcon,
  Upload as UploadIcon,
  Assessment as AssessmentIcon,
  Science as ScienceIcon,
  Android as BotIcon,
  Home as HomeIcon,
  Help as HelpIcon,
  Brightness4 as DarkModeIcon,
  Brightness7 as LightModeIcon,
  Notifications as NotificationsIcon,
} from '@mui/icons-material';
import { useContext } from 'react';
import ColorModeContext from '../theme/ColorModeContext';

function MUIResponsiveLayout({ children }) {
  const colorMode = useContext(ColorModeContext);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [bottomNavValue, setBottomNavValue] = useState(0);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const navigationItems = [
    { text: 'Chat AI', icon: <ChatIcon />, path: '/', isNew: true },
    { text: 'Upload Documenti', icon: <UploadIcon />, path: '/upload' },
    { text: 'Stato Sistema', icon: <AssessmentIcon />, path: '/status' },
    { text: 'Test Lab', icon: <ScienceIcon />, path: '/test' },
  ];

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const drawerContent = (
    <Box sx={{ width: 280 }}>
      {/* Header */}
      <Box
        sx={{
          p: 3,
          background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
          color: 'white',
        }}
      >
        <Box display="flex" alignItems="center" gap={2} mb={2}>
          <Avatar
            sx={{
              width: 56,
              height: 56,
              background: 'rgba(255, 255, 255, 0.2)',
              backdropFilter: 'blur(10px)',
            }}
          >
            <BotIcon sx={{ fontSize: 28 }} />
          </Avatar>
          <Box>
            <Typography variant="h6" fontWeight={700}>
              K-Array AI
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.9 }}>
              v2.0 • Powered by MUI
            </Typography>
          </Box>
        </Box>
        
        <Chip
          label="Sistema Online"
          size="small"
          sx={{
            background: 'rgba(34, 197, 94, 0.2)',
            color: 'rgba(34, 197, 94, 1)',
            border: '1px solid rgba(34, 197, 94, 0.3)',
            fontWeight: 600,
          }}
        />
      </Box>

      <Divider />

      {/* Navigation Items */}
      <List sx={{ px: 2, py: 1 }}>
        {navigationItems.map((item, index) => (
          <ListItem key={index} disablePadding sx={{ mb: 0.5 }}>
            <ListItemButton
              sx={{
                borderRadius: 2,
                '&:hover': {
                  backgroundColor: 'rgba(59, 130, 246, 0.08)',
                },
                '&.Mui-selected': {
                  backgroundColor: 'rgba(59, 130, 246, 0.12)',
                  '&:hover': {
                    backgroundColor: 'rgba(59, 130, 246, 0.16)',
                  },
                },
              }}
            >
              <ListItemIcon sx={{ color: 'primary.main', minWidth: 40 }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText 
                primary={item.text}
                primaryTypographyProps={{
                  fontWeight: 500,
                  fontSize: '0.95rem',
                }}
              />
              {item.isNew && (
                <Chip
                  label="NEW"
                  size="small"
                  sx={{
                    height: 20,
                    fontSize: '0.625rem',
                    fontWeight: 700,
                    background: 'linear-gradient(135deg, #ff3366 0%, #ff6b9d 100%)',
                    color: 'white',
                  }}
                />
              )}
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      <Divider sx={{ my: 2 }} />

      {/* Quick Settings */}
      <List sx={{ px: 2 }}>
        <ListItem disablePadding>
          <ListItemButton sx={{ borderRadius: 2 }}>
            <ListItemIcon sx={{ color: 'text.secondary', minWidth: 40 }}>
              <SettingsIcon />
            </ListItemIcon>
            <ListItemText primary="Impostazioni" />
          </ListItemButton>
        </ListItem>
        <ListItem disablePadding>
          <ListItemButton sx={{ borderRadius: 2 }}>
            <ListItemIcon sx={{ color: 'text.secondary', minWidth: 40 }}>
              <HelpIcon />
            </ListItemIcon>
            <ListItemText primary="Aiuto & Supporto" />
          </ListItemButton>
        </ListItem>
      </List>

      {/* Footer Info */}
      <Box sx={{ p: 2, mt: 'auto' }}>
        <Paper
          elevation={0}
          sx={{
            p: 2,
            background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.05) 0%, rgba(139, 92, 246, 0.05) 100%)',
            border: '1px solid rgba(59, 130, 246, 0.1)',
            borderRadius: 2,
          }}
        >
          <Typography variant="caption" color="text.secondary" display="block">
            RAG System: ✅ Operativo
          </Typography>
          <Typography variant="caption" color="text.secondary" display="block">
            K-Framework: ✅ Connesso
          </Typography>
          <Typography variant="caption" color="primary.main" fontWeight={600}>
            Confidence: 0.85/1.0
          </Typography>
        </Paper>
      </Box>
    </Box>
  );

  const drawerWidth = 280;

  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      {/* App Bar */}
      <AppBar 
        position="fixed" 
        elevation={0}
        sx={{ 
          zIndex: (theme) => theme.zIndex.drawer + 1,
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(20px)',
          borderBottom: '1px solid rgba(226, 232, 240, 0.6)',
          color: 'text.primary',
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>

          {/* Desktop Logo */}
          <Box 
            display="flex" 
            alignItems="center" 
            gap={2}
            sx={{ display: { xs: 'none', md: 'flex' } }}
          >
            <Avatar
              sx={{
                background: 'linear-gradient(135deg, #0a0a0a 0%, #1e1e1e 100%)',
                width: 40,
                height: 40,
              }}
            >
              <BotIcon />
            </Avatar>
            <Typography variant="h6" fontWeight={700}>
              K-Array AI Assistant
            </Typography>
          </Box>

          {/* Mobile Logo */}
          <Typography 
            variant="h6" 
            fontWeight={700}
            sx={{ 
              flexGrow: 1,
              display: { xs: 'block', md: 'none' }
            }}
          >
            K-Array AI
          </Typography>

          {/* Desktop Actions */}
          <Box sx={{ ml: 'auto', display: { xs: 'none', md: 'flex' } }}>
            <IconButton color="inherit" size="large">
              <NotificationsIcon />
            </IconButton>
            <IconButton color="inherit" size="large" onClick={colorMode.toggleColorMode}>
              {theme.palette.mode === 'light' ? <DarkModeIcon /> : <LightModeIcon />}
            </IconButton>
            <IconButton color="inherit" size="large">
              <SettingsIcon />
            </IconButton>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Desktop Sidebar */}
      <Drawer
        variant="permanent"
        sx={{
          display: { xs: 'none', md: 'block' },
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
            border: 'none',
            boxShadow: '4px 0 20px rgba(0, 0, 0, 0.05)',
          },
        }}
      >
        <Toolbar />
        {drawerContent}
      </Drawer>

      {/* Mobile Drawer */}
      <SwipeableDrawer
        variant="temporary"
        open={mobileOpen}
        onOpen={handleDrawerToggle}
        onClose={handleDrawerToggle}
        ModalProps={{
          keepMounted: true,
        }}
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
          },
        }}
      >
        {drawerContent}
      </SwipeableDrawer>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          height: '100vh',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <Toolbar />
        <Box sx={{ flex: 1, overflow: 'hidden', pb: { xs: 7, md: 0 } }}>
          {children}
        </Box>
      </Box>

      {/* Mobile Bottom Navigation */}
      <Paper
        sx={{ 
          position: 'fixed', 
          bottom: 0, 
          left: 0, 
          right: 0,
          display: { xs: 'block', md: 'none' },
          zIndex: (theme) => theme.zIndex.appBar,
        }}
        elevation={8}
      >
        <BottomNavigation
          value={bottomNavValue}
          onChange={(event, newValue) => {
            setBottomNavValue(newValue);
          }}
          sx={{
            '& .MuiBottomNavigationAction-root': {
              '&.Mui-selected': {
                color: 'primary.main',
              },
            },
          }}
        >
          <BottomNavigationAction
            label="Chat"
            icon={<ChatIcon />}
          />
          <BottomNavigationAction
            label="Upload"
            icon={<UploadIcon />}
          />
          <BottomNavigationAction
            label="Status"
            icon={<AssessmentIcon />}
          />
          <BottomNavigationAction
            label="Test"
            icon={<ScienceIcon />}
          />
        </BottomNavigation>
      </Paper>
    </Box>
  );
}

export default MUIResponsiveLayout;