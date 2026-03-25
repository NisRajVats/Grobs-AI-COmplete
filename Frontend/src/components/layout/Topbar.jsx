import React, { useState, useRef, useEffect } from 'react';
import { Search, Bell, HelpCircle, Moon, Sun, User, ChevronDown, Zap, LogOut, Settings as SettingsIcon, UserCircle, Activity } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import { useNavigate, Link } from 'react-router-dom';
import NotificationBell from '../NotificationBell';

const Topbar = ({ isCollapsed }) => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [showProfileDropdown, setShowProfileDropdown] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowProfileDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/jobs?search=${encodeURIComponent(searchQuery)}`);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <motion.header
      initial={false}
      animate={{ left: isCollapsed ? 80 : 280 }}
      className="fixed top-0 right-0 h-20 glass-dark z-40 px-8 flex items-center justify-between transition-all duration-300 border-b border-white/5 shadow-2xl backdrop-blur-3xl no-print"
    >
      {/* Global Search */}
      <div className="flex-1 max-w-md">
        <form onSubmit={handleSearch} className="relative group">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-400 transition-colors" size={18} />
          <input 
            type="text" 
            placeholder="Search resumes, jobs, tools..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full h-11 bg-slate-900/50 border border-white/10 rounded-2xl pl-12 pr-4 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500/50 transition-all placeholder:text-slate-500 backdrop-blur-xl"
          />
        </form>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2 pr-6 border-r border-white/10">
          <button 
            onClick={() => navigate('/app/evaluation')}
            className="p-2.5 rounded-xl hover:bg-white/5 text-slate-400 hover:text-white transition-all"
            title="Model Evaluation"
          >
            <Activity size={20} />
          </button>
          
          <NotificationBell />
          
          <button 
            onClick={() => navigate('/settings')}
            className="p-2.5 rounded-xl hover:bg-white/5 text-slate-400 hover:text-white transition-all"
            title="Help & Support"
          >
            <HelpCircle size={20} />
          </button>
          
          <button 
            onClick={toggleTheme}
            className="p-2.5 rounded-xl hover:bg-white/5 text-slate-400 hover:text-white transition-all"
            title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          >
            {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
          </button>
        </div>

        {/* User Profile */}
        <div className="relative" ref={dropdownRef}>
          <div 
            className="flex items-center gap-3 pl-4 cursor-pointer group"
            onClick={() => setShowProfileDropdown(!showProfileDropdown)}
          >
            <div className="relative">
              <div className="w-10 h-10 rounded-xl overflow-hidden border-2 border-blue-500/30 group-hover:border-blue-400 transition-all shadow-lg bg-slate-800 flex items-center justify-center">
                {user?.avatar_url ? (
                  <img 
                    src={user.avatar_url} 
                    alt="User avatar" 
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <User size={20} className="text-slate-400" />
                )}
              </div>
              <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-slate-900"></div>
            </div>
            
            <div className="hidden lg:block text-left">
              <h4 className="text-sm font-semibold text-white group-hover:text-blue-400 transition-colors">
                {user?.full_name || user?.email?.split('@')[0] || 'User'}
              </h4>
              <p className="text-xs text-slate-400">{user?.title || 'Job Seeker'}</p>
            </div>
            <ChevronDown size={16} className={`text-slate-500 group-hover:text-white transition-colors ml-1 transition-colorsduration-200 ${showProfileDropdown ? 'rotate-180' : ''}`} />
          </div>

          <AnimatePresence>
            {showProfileDropdown && (
              <motion.div
                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 10, scale: 0.95 }}
                className="absolute right-0 mt-4 w-56 bg-slate-900/90 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl overflow-hidden z-50"
              >
                <div className="p-4 border-b border-white/5">
                  <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Signed in as</p>
                  <p className="text-sm font-semibold text-white truncate">{user?.email}</p>
                </div>
                
                <div className="p-2">
                  <Link 
                    to="/profile" 
                    className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-slate-300 hover:text-white hover:bg-white/5 transition-all group"
                    onClick={() => setShowProfileDropdown(false)}
                  >
                    <UserCircle size={18} className="text-slate-400 group-hover:text-blue-400 transition-colors" />
                    <span className="text-sm font-medium">My Profile</span>
                  </Link>
                  <Link 
                    to="/settings" 
                    className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-slate-300 hover:text-white hover:bg-white/5 transition-all group"
                    onClick={() => setShowProfileDropdown(false)}
                  >
                    <SettingsIcon size={18} className="text-slate-400 group-hover:text-blue-400 transition-colors" />
                    <span className="text-sm font-medium">Settings</span>
                  </Link>
                </div>

                <div className="p-2 border-t border-white/5">
                  <button 
                    onClick={handleLogout}
                    className="flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 transition-all group"
                  >
                    <LogOut size={18} />
                    <span className="text-sm font-medium">Sign Out</span>
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.header>
  );
};

export default Topbar;
  