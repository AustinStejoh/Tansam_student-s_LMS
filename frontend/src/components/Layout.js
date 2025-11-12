import React from 'react';
import { Route, Routes, Navigate } from 'react-router-dom';
import { Box } from '@mui/material';
import Navbar from './Navbar';
import Sidebar from './Sidebar';
import Dashboard from '../pages/Dashboard';
import CourseDetail from '../pages/CourseDetail';
import TopicDetail from '../pages/TopicDetail';
import { useApp } from '../contexts/AppContext';

const Layout = () => {
  const { user } = useApp();

  if (!user) {
    return <Navigate to="/login" />;
  }

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar />
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <Navbar />
        <Box component="main" sx={{ flex: 1, p: 3, backgroundColor: 'background.default' }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/course/:id" element={<CourseDetail />} />
            <Route path="/topic/:id" element={<TopicDetail />} />
          </Routes>
        </Box>
      </Box>
    </Box>
  );
};

export default Layout;