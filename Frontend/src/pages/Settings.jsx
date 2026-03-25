import React, { useState } from 'react';
import { User, Lock, Bell, Moon, Globe, LogOut, ChevronRight, CheckCircle2, Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { authAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

const Settings = () => {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [passwords, setPasswords] = useState({ old_password: '', new_password: '', confirm: '' });
  const [pwSaving, setPwSaving] = useState(false);
  const [pwMsg, setPwMsg] = useState('');
  const [pwError, setPwError] = useState('');
  const [darkMode, setDarkMode] = useState(true);
  const [emailNotifs, setEmailNotifs] = useState(true);

  const handlePasswordChange = async () => {
    if (passwords.new_password !== passwords.confirm) {
      setPwError('Passwords do not match'); return;
    }
    if (passwords.new_password.length < 8) {
      setPwError('Password must be at least 8 characters'); return;
    }
    setPwSaving(true); setPwError(''); setPwMsg('');
    try {
      await authAPI.changePassword(passwords.old_password, passwords.new_password);
      setPwMsg('Password changed successfully!');
      setPasswords({ old_password: '', new_password: '', confirm: '' });
    } catch (err) {
      setPwError(err.response?.data?.detail || 'Failed to change password.');
    } finally { setPwSaving(false); }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const sections = [
    {
      title: 'Account', icon: User, items: [
        { label: 'Edit Profile', action: () => navigate('/app/profile/edit'), arrow: true },
        { label: 'Subscription & Billing', action: () => navigate('/app/subscriptions'), arrow: true },
      ]
    },
    {
      title: 'Preferences', icon: Globe, items: [
        { label: 'Dark Mode', toggle: true, value: darkMode, onChange: setDarkMode },
        { label: 'Email Notifications', toggle: true, value: emailNotifs, onChange: setEmailNotifs },
      ]
    },
  ];

  return (
    <div className="max-w-2xl mx-auto space-y-8 pb-20">
      <div>
        <h1 className="text-3xl font-bold text-white">Settings</h1>
        <p className="text-slate-400">Manage your account and preferences</p>
      </div>

      {sections.map(section => (
        <div key={section.title} className="card-glass overflow-hidden">
          <div className="px-6 py-4 border-b border-white/5 flex items-center gap-2">
            <section.icon size={18} className="text-slate-400" />
            <h3 className="font-bold text-white">{section.title}</h3>
          </div>
          {section.items.map((item, i) => (
            <div key={i} onClick={item.action} className={`flex items-center justify-between px-6 py-4 ${item.action ? 'cursor-pointer hover:bg-white/5 transition-colors' : ''} border-b border-white/5 last:border-0`}>
              <span className="text-slate-300">{item.label}</span>
              {item.arrow && <ChevronRight size={18} className="text-slate-500" />}
              {item.toggle !== undefined && (
                <button onClick={e => { e.stopPropagation(); item.onChange(!item.value); }} className={`w-12 h-6 rounded-full transition-all ${item.value ? 'bg-blue-600' : 'bg-slate-600'} relative`}>
                  <span className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-all ${item.value ? 'left-7' : 'left-1'}`} />
                </button>
              )}
            </div>
          ))}
        </div>
      ))}

      {/* Change Password */}
      <div className="card-glass overflow-hidden">
        <div className="px-6 py-4 border-b border-white/5 flex items-center gap-2">
          <Lock size={18} className="text-slate-400" />
          <h3 className="font-bold text-white">Change Password</h3>
        </div>
        <div className="p-6 space-y-4">
          {pwError && <p className="text-red-400 text-sm">{pwError}</p>}
          {pwMsg && <p className="text-green-400 text-sm flex items-center gap-2"><CheckCircle2 size={16} />{pwMsg}</p>}
          {['old_password', 'new_password', 'confirm'].map(field => (
            <div key={field}>
              <label className="text-xs font-bold text-slate-500 uppercase mb-2 block">
                {field === 'old_password' ? 'Current Password' : field === 'new_password' ? 'New Password' : 'Confirm New Password'}
              </label>
              <input
                type="password"
                value={passwords[field]}
                onChange={e => setPasswords({ ...passwords, [field]: e.target.value })}
                className="w-full bg-slate-900/60 border border-white/10 rounded-xl px-4 py-3 text-white text-sm focus:ring-2 focus:ring-blue-500/30"
              />
            </div>
          ))}
          <button onClick={handlePasswordChange} disabled={pwSaving || !passwords.old_password || !passwords.new_password} className="w-full py-3 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-500 disabled:opacity-50 transition-all flex items-center justify-center gap-2">
            {pwSaving ? <Loader2 size={18} className="animate-spin" /> : <Lock size={18} />}
            Update Password
          </button>
        </div>
      </div>

      {/* Logout */}
      <button onClick={handleLogout} className="w-full py-4 bg-red-600/10 border border-red-500/20 text-red-400 font-bold rounded-2xl hover:bg-red-600/20 transition-all flex items-center justify-center gap-2">
        <LogOut size={20} /> Sign Out
      </button>
    </div>
  );
};

export default Settings;
