import React from 'react';
import FleetHome from './FleetHome';

/** Step 1: reuse fleet home as dashboard. */
const Dashboard: React.FC<{ darkMode: boolean }> = ({ darkMode }) => {
  return <FleetHome darkMode={darkMode} />;
};

export default Dashboard;
