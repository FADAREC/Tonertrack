import React from 'react';
import FleetHome from './FleetHome';

/** Step 1: same fleet view. */
const PrinterList: React.FC<{ darkMode: boolean }> = ({ darkMode }) => {
  return <FleetHome darkMode={darkMode} />;
};

export default PrinterList;
