import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Lock, Eye, EyeOff, LogIn, ChevronRight, Globe, Github, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import AuthLayout from '../layouts/AuthLayout/AuthLayout';
import { authAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

const LoginPage = () => {
  const navigate = useNavigate();
  const { login: authLogin } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    
    try {
      const response = await authAPI.login(formData.email, formData.password);

      const { access_token, refresh_token } = response.data;
      
      // Store token in localStorage FIRST so the interceptor can use it
      localStorage.setItem('token', access_token);
      if (refresh_token) {
        localStorage.setItem('refresh_token', refresh_token);
      }
      
      // Fetch user profile (now the interceptor will have the token)
      const userResponse = await authAPI.getCurrentUser();
      
      // Update global auth state
      authLogin(access_token, userResponse.data, refresh_token);

      navigate('/app/dashboard');
    } catch (err) {
      console.error('Login error:', err);
      const status = err.response?.status;
      const rawDetail = err.response?.data?.detail || {};
      const errorData = typeof rawDetail === 'object' ? rawDetail : {};
      
      let message = 'Invalid email or password. Please try again.';
      if (status === 401 && errorData.message) {
        message = errorData.message;
      } else if (typeof rawDetail === 'string') {
        message = rawDetail;
      } else if (Array.isArray(rawDetail)) {
        message = rawDetail.map(e => e.msg).join(', ');
      }
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthLayout 
      title="Welcome Back" 
      subtitle="Continue your journey to a better career."
    >
      <form onSubmit={handleSubmit} className="space-y-6">
        {error && (
          <motion.div 
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-4 bg-red-500/10 border border-red-500/20 rounded-2xl flex items-center gap-3 text-red-400 text-sm"
          >
            <AlertCircle size={18} />
            <p>{error}</p>
          </motion.div>
        )}
        <div className="space-y-4">
          <div className="relative group">
            <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-blue-400 transition-colors" size={18} />
            <input 
              required
              type="email" 
              placeholder="Email address"
              className="w-full bg-slate-900/50 border border-white/10 rounded-2xl py-4 pl-12 pr-4 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/30 transition-all placeholder:text-slate-500"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            />
          </div>

          <div className="relative group">
            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-blue-400 transition-colors" size={18} />
            <input 
              required
              type={showPassword ? 'text' : 'password'} 
              placeholder="Password"
              className="w-full bg-slate-900/50 border border-white/10 rounded-2xl py-4 pl-12 pr-12 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/30 transition-all placeholder:text-slate-500"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            />
            <button 
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white transition-colors"
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
        </div>

        <div className="flex items-center justify-between px-1">
          <label className="flex items-center gap-2 cursor-pointer group">
            <input type="checkbox" className="w-4 h-4 rounded border-white/10 bg-slate-900 checked:bg-blue-600 focus:ring-blue-500/30" />
            <span className="text-sm text-slate-400 group-hover:text-slate-200 transition-colors">Remember me</span>
          </label>
          <Link to="/forgot-password" size="sm" className="text-sm font-semibold text-blue-400 hover:text-blue-300 transition-colors">
            Forgot password?
          </Link>
        </div>

        <button 
          disabled={isLoading}
          type="submit" 
          className="w-full py-4 bg-blue-600 hover:bg-blue-500 text-white font-black text-lg rounded-2xl shadow-xl shadow-blue-500/20 transition-all active:scale-[0.98] flex items-center justify-center gap-3 disabled:opacity-50"
        >
          {isLoading ? (
            <div className="w-6 h-6 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
          ) : (
            <>Sign In <ChevronRight size={20} /></>
          )}
        </button>

        <div className="relative py-4">
           <div className="absolute inset-0 flex items-center">
             <div className="w-full border-t border-white/5"></div>
           </div>
           <div className="relative flex justify-center text-xs uppercase">
             <span className="bg-slate-900 px-3 text-slate-500 font-bold tracking-widest">Or continue with</span>
           </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
           <button type="button" className="flex items-center justify-center gap-3 py-3 px-4 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 transition-all text-sm font-semibold text-white">
              <Globe size={18} className="text-slate-400" /> Google
           </button>
           <button type="button" className="flex items-center justify-center gap-3 py-3 px-4 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 transition-all text-sm font-semibold text-white">
              <Github size={18} className="text-slate-400" /> Github
           </button>
        </div>

        <p className="text-center text-slate-400 text-sm">
          Don't have an account? <Link to="/register" className="text-blue-400 font-bold hover:underline">Sign up for free</Link>
        </p>
      </form>
    </AuthLayout>
  );
};

export default LoginPage;
