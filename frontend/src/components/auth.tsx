import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { User, Lock, Globe, Twitter, ArrowRight } from 'lucide-react'; // Fixed: Replaced Google with Globe
import { authAPI } from '../services/api';

const Auth: React.FC<{ darkMode: boolean }> = ({ darkMode }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isRegister, setIsRegister] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      const res = isRegister ? await authAPI.register(username, password) : await authAPI.login(username, password);
      if (!isRegister) {
        localStorage.setItem('token', res.data.access_token);
        window.location.reload();
      } else {
        alert('Registered! Please login.');
      }
    } catch (err: any) {
      if (err.response) {
        setError(err.response.data?.detail || `HTTP Error: ${err.response.status}`);
      } else if (err.request) {
        setError('No response from server. Is the backend running?');
      } else {
        setError(`Error: ${err.message}`);
      }
      console.error('Auth error:', err);
    }
  };

  const SocialButton = ({ provider, Icon }: { provider: string; Icon: React.FC<{ className?: string }> }) => (
    <motion.button
      whileHover={{ scale: 1.02 }}
      className="w-full flex items-center justify-center space-x-2 p-3 bg-white/10 backdrop-blur-md border border-white/20 rounded-xl hover:border-white/30 transition-all duration-300 text-white"
    >
      <Icon className="h-5 w-5" />
      <span>Continue with {provider}</span>
    </motion.button>
  );

  return (
    <motion.form
      onSubmit={handleSubmit}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.6, type: 'spring' }}
      className="space-y-6 bg-white/5 backdrop-blur-lg rounded-3xl p-8 border border-white/10 shadow-2xl"
    >
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mb-2">
          Welcome Back
        </h2>
        <p className="text-white/70 text-sm">
          {isRegister ? 'Create your account' : 'Sign in to your account'}
        </p>
      </motion.div>

      <div className="space-y-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="relative"
        >
          <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-white/50 h-5 w-5" />
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Email or Username"
            required
            minLength={3}
            className="w-full pl-10 p-3 bg-white/5 backdrop-blur-md border border-white/20 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-400/50 text-white placeholder-white/50 transition-all duration-300"
          />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="relative"
        >
          <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-white/50 h-5 w-5" />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            required
            minLength={6}
            className="w-full pl-10 p-3 bg-white/5 backdrop-blur-md border border-white/20 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-400/50 text-white placeholder-white/50 transition-all duration-300"
          />
        </motion.div>
      </div>

      <motion.button
        type="submit"
        whileHover={{ scale: 1.02, boxShadow: '0 10px 20px rgba(59, 130, 246, 0.3)' }}
        whileTap={{ scale: 0.98 }}
        className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white p-3 rounded-xl shadow-lg hover:from-blue-600 hover:to-purple-700 transition-all duration-300 font-medium"
      >
        <ArrowRight className="inline h-5 w-5 mr-2" />
        {isRegister ? 'Sign Up' : 'Sign In'}
      </motion.button>

      <div className="space-y-3">
        <SocialButton provider="Google" Icon={Globe} /> {/* Fixed: Used Globe for Google */}
        <SocialButton provider="X" Icon={Twitter} />
      </div>

      <motion.button
        type="button"
        onClick={() => setIsRegister(!isRegister)}
        whileHover={{ scale: 1.02 }}
        className="w-full text-white/70 hover:text-white text-sm font-medium transition-colors duration-200"
      >
        {isRegister ? 'Already have an account? Sign In' : "Don't have an account? Sign Up"}
      </motion.button>

      {error && (
        <motion.p
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-red-400 text-center text-sm bg-red-500/10 p-3 rounded-xl backdrop-blur-md border border-red-400/30"
        >
          {error}
        </motion.p>
      )}
    </motion.form>
  );
};

export default Auth;