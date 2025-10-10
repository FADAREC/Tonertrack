import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Printer, AlertTriangle, Droplet } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, Cell } from 'recharts';
import toast, { Toaster } from 'react-hot-toast';
import { printersAPI } from '../services/api';

interface Printer {
  id: number;
  ip: string;
  model?: string;
  toner_levels: { [key: string]: number };
  errors: string[];
  connection_mode: string;
  department?: string;
  location?: string;
}

const Dashboard: React.FC<{ darkMode: boolean }> = ({ darkMode }) => {
  const [printers, setPrinters] = useState<Printer[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPrinters();
    const interval = setInterval(fetchPrinters, 300000); // 5min
    return () => clearInterval(interval);
  }, []);

  const fetchPrinters = async () => {
    try {
      const res = await printersAPI.list();
      const printersWithStatus = await Promise.all(
        res.data.printers.map(async (p: Printer) => ({
          ...p,
          ...(await printersAPI.status(p.id).catch(() => ({}))),
        }))
      );
      setPrinters(printersWithStatus);
      checkLowToner(printersWithStatus);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const checkLowToner = (printers: Printer[]) => {
    printers.forEach(p => {
      Object.entries(p.toner_levels).forEach(([color, level]) => {
        if (level < 20) {
          toast.error(`Low toner in ${p.model || 'Printer'} (${p.ip}, ${p.department || 'N/A'}, ${p.location || 'N/A'}): ${color} at ${level}% - ${new Date().toLocaleString()}`);
        }
      });
    });
  };

  if (loading) return <p>Loading...</p>;

  return (
    <div>
      <Toaster />
      {/* Stats, charts, printer summaries from history */}
    </div>
  );
};

export default Dashboard;