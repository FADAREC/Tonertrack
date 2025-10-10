import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Settings as SettingsIcon, LogOut, UserPlus, UserX } from 'lucide-react';
import api from '../services/api';  // Default api for users

const Settings: React.FC<{ darkMode: boolean; toggleDarkMode: () => void }> = ({ darkMode, toggleDarkMode }) => {
  const role = localStorage.getItem('role') || 'staff';
  const [users, setUsers] = useState([]);
  const [newUser, setNewUser] = useState({ username: '', password: '', role: 'staff' });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (role === 'admin') fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const res = await api.get('/users');
      setUsers(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const addUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post('/users', newUser);
      fetchUsers();
      setNewUser({ username: '', password: '', role: 'staff' });
    } catch (err) {
      alert('Add failed');
    } finally {
      setLoading(false);
    }
  };

  const deleteUser = async (id: number) => {
    const userConfirmed = window.confirm('Are you sure you want to delete this user?');
    if (userConfirmed) {
      try {
        await api.delete(`/users/${id}`);
        fetchUsers();
      } catch (err) {
        alert('Delete failed');
      }
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    window.location.reload();
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white/5 backdrop-blur-lg rounded-2xl p-6 border border-white/10"
    >
      <h2 className="text-2xl font-bold text-white mb-4">Settings</h2>
      <p className="text-white/70 mb-6">Customize your experience.</p>
      <div className="space-y-4">
        <div className="flex items-center justify-between p-4 bg-white/10 rounded-xl">
          <span className="text-white">Dark Mode</span>
          <label className="relative inline-flex items-center cursor-pointer">
            <input type="checkbox" checked={darkMode} onChange={toggleDarkMode} className="sr-only" />
            <div className="w-11 h-6 bg-white/20 rounded-full peer dark:bg-white/20">
              <div className="w-5 h-5 bg-white rounded-full peer-checked:translate-x-5 transition-transform"></div>
            </div>
          </label>
        </div>
        {role === 'admin' && (
          <>
            <h3 className="text-xl font-semibold text-white mt-6">Manage Users</h3>
            <form onSubmit={addUser} className="space-y-4 mb-6">
              <input
                type="text"
                value={newUser.username}
                onChange={(e) => setNewUser({...newUser, username: e.target.value})}
                placeholder="Username"
                required
                className="w-full p-3 bg-white/5 border border-white/20 rounded-xl text-white"
              />
              <input
                type="password"
                value={newUser.password}
                onChange={(e) => setNewUser({...newUser, password: e.target.value})}
                placeholder="Password"
                required
                className="w-full p-3 bg-white/5 border border-white/20 rounded-xl text-white"
              />
              <select
                value={newUser.role}
                onChange={(e) => setNewUser({...newUser, role: e.target.value})}
                className="w-full p-3 bg-white/5 border border-white/20 rounded-xl text-white"
              >
                <option value="staff">Staff</option>
                <option value="admin">Admin</option>
              </select>
              <button type="submit" disabled={loading} className="w-full bg-blue-500 text-white p-3 rounded-xl">
                {loading ? 'Adding...' : 'Add User'}
              </button>
            </form>
            <div className="space-y-2">
              {users.map((user: {id: number, username: string, role: string}) => (
                <div key={user.id} className="flex justify-between p-3 bg-white/10 rounded-xl">
                  <span>{user.username} ({user.role})</span>
                  <button onClick={() => deleteUser(user.id)} className="text-red-300 hover:text-red-500">
                    <UserX className="h-5 w-5" />
                  </button>
                </div>
              ))}
            </div>
          </>
        )}
        <motion.button
          onClick={handleLogout}
          whileHover={{ scale: 1.02 }}
          className="w-full flex items-center justify-center space-x-2 p-3 bg-red-500/20 text-red-300 rounded-xl hover:bg-red-500/30 transition-all duration-300"
        >
          <LogOut className="h-5 w-5" />
          <span>Logout</span>
        </motion.button>
      </div>
    </motion.div>
  );
};

export default Settings;