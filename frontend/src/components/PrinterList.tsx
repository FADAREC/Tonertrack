import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Printer, AlertTriangle, Droplet, Link } from 'lucide-react';
import { printersAPI } from '../services/api';

interface Printer {
  id: number;
  ip: string;
  model?: string;
  toner_levels: { [key: string]: number };
  errors: string[];
  connection_mode: string;
}

const PrinterList: React.FC<{ darkMode: boolean }> = ({ darkMode }) => {
  const [printers, setPrinters] = useState<Printer[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPrinters();
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
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div></div>;

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-6"
    >
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">All Printers</h2>
        <Link to="/add-printer" className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-4 py-2 rounded-xl hover:from-blue-600 hover:to-purple-700 transition-all">
          Add New Printer
        </Link>
      </div>

      {printers.length === 0 ? (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center py-12 bg-white/5 rounded-2xl"
        >
          <Printer className="mx-auto h-16 w-16 text-white/50 mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">No Printers Added</h3>
          <p className="text-white/70">Start by adding your first printer or scanning the network.</p>
        </motion.div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {printers.map((printer, index) => (
            <motion.div
              key={printer.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-white/5 backdrop-blur-lg rounded-2xl p-6 border border-white/10 hover:border-white/20 transition-all"
            >
              <h3 className="text-lg font-semibold text-white mb-2">{printer.model || 'Unknown'}</h3>
              <p className="text-white/70 mb-4">{printer.ip} • {printer.connection_mode.toUpperCase()}</p>
              <div className="space-y-2 mb-4">
                <h4 className="text-sm font-medium text-white/70">Toner Levels</h4>
                {Object.entries(printer.toner_levels).map(([color, level]) => (
                  <div key={color} className="flex items-center space-x-2">
                    <div className={`h-2 w-2 rounded-full bg-${color}-400`}></div>
                    <span className="text-white/70 text-sm capitalize">{color}</span>
                    <div className="flex-1 bg-white/10 rounded-full h-1.5">
                      <div className="bg-gradient-to-r from-blue-500 to-purple-500 h-1.5 rounded-full" style={{ width: `${level}%` }} />
                    </div>
                    <span className="text-white font-medium">{level}%</span>
                  </div>
                ))}
              </div>
              {printer.errors.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-red-400 mb-2">Errors</h4>
                  <ul className="space-y-1">
                    {printer.errors.map((err, i) => (
                      <li key={i} className="text-red-300 text-sm flex items-center">
                        <AlertTriangle className="h-3 w-3 mr-2" />
                        {err}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              <div className="flex space-x-3">
                <button onClick={() => printersAPI.delete(printer.id).then(fetchPrinters)} className="flex-1 bg-red-500/20 text-red-300 py-2 rounded-xl hover:bg-red-500/30">
                  Delete
                </button>
                <button onClick={() => printersAPI.status(printer.id).then((res) => setPrinters(printers.map(p => p.id === printer.id ? {...p, ...res.data} : p)))} className="flex-1 bg-blue-500/20 text-blue-300 py-2 rounded-xl hover:bg-blue-500/30">
                  Refresh
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </motion.div>
  );
};

export default PrinterList;