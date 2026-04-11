import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { UserCircle, Mail, Phone, MapPin, Briefcase, Calendar, Edit3, Settings, Shield, CreditCard, Activity } from 'lucide-react';
import { motion } from 'framer-motion';
import { usersAPI } from '../../services/api';

const Profile = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [userRes, statsRes] = await Promise.all([
        usersAPI.getProfile(),
        usersAPI.getDashboardStats()
      ]);
      setUser(userRes.data);
      setStats(statsRes.data);
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setLoading(false);
    }
  };

  const menuItems = [
    { id: 'view', icon: UserCircle, label: 'View Profile', path: '/app/profile' },
    { id: 'edit', icon: Edit3, label: 'Edit Information', path: '/app/profile/edit' },
    { id: 'preferences', icon: Settings, label: 'Preferences', path: '/app/settings' },
    { id: 'subscription', icon: CreditCard, label: 'Subscription', path: '/app/settings' },
    { id: 'activity', icon: Activity, label: 'Activity History', path: '/app/settings' },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold text-white">Profile & Settings</h1>
        <p className="text-slate-400 text-lg">Manage your account and preferences</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <div className="card-glass p-8">
            <div className="flex items-start gap-6">
              <div className="w-24 h-24 bg-blue-600/20 rounded-2xl flex items-center justify-center">
                <UserCircle size={48} className="text-blue-400" />
              </div>
              <div className="flex-1">
                <h2 className="text-2xl font-bold text-white">{user?.full_name || user?.email?.split('@')[0] || 'User'}</h2>
                <p className="text-slate-400">{user?.title || 'Software Developer'}</p>
                {user?.experience_level && <p className="text-sm text-blue-400 mt-1">{user.experience_level}</p>}
                <div className="flex flex-wrap gap-4 mt-4 text-sm text-slate-500">
                  <span className="flex items-center gap-1"><Mail size={14} /> {user?.email}</span>
                  {user?.location && <span className="flex items-center gap-1"><MapPin size={14} /> {user.location}</span>}
                  {user?.created_at && <span className="flex items-center gap-1"><Calendar size={14} /> Joined {new Date(user.created_at).toLocaleDateString()}</span>}
                </div>
                {user?.bio && (
                  <div className="mt-4 pt-4 border-t border-white/10">
                    <p className="text-sm text-slate-400 leading-relaxed">{user.bio}</p>
                  </div>
                )}
                {user?.website && (
                  <div className="mt-2">
                    <a href={user.website} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1">
                      <Briefcase size={14} /> {user.website.replace(/^https?:\/\//, '')}
                    </a>
                  </div>
                )}
              </div>
              <button onClick={() => navigate('/app/profile/edit')} className="p-3 bg-slate-800 rounded-xl text-slate-400 hover:text-white hover:bg-slate-700 transition-all">
                <Edit3 size={20} />
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {menuItems.slice(1).map((item) => (
              <motion.div
                key={item.id}
                whileHover={{ y: -2 }}
                onClick={() => navigate(item.path)}
                className="card-glass p-6 cursor-pointer hover:bg-white/10 transition-all border-white/5 hover:border-blue-500/30"
              >
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-slate-800 rounded-xl flex items-center justify-center">
                    <item.icon size={20} className="text-blue-400" />
                  </div>
                  <div>
                    <h3 className="font-bold text-white">{item.label}</h3>
                    <p className="text-sm text-slate-500">Manage your {item.label.toLowerCase()}</p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        <div className="space-y-6">
          <div className="card-glass p-6">
            <h3 className="font-bold text-white mb-4">Account Stats</h3>
            <div className="space-y-4">
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Resumes</span>
                <span className="text-white font-bold">{stats?.total_resumes || 0}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Applications</span>
                <span className="text-white font-bold">{stats?.total_applications || 0}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Saved Jobs</span>
                <span className="text-white font-bold">{stats?.total_saved_jobs || 0}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Avg. ATS Score</span>
                <span className="text-white font-bold">{stats?.avg_ats_score || 0}%</span>
              </div>
            </div>
          </div>

          <div className="card-glass p-6">
            <h3 className="font-bold text-white mb-4">Subscription</h3>
            <div className="p-4 bg-linear-to-r from-blue-600/20 to-purple-600/20 border border-blue-500/30 rounded-xl">
              <p className="text-blue-400 font-bold">Pro Plan</p>
              <p className="text-sm text-slate-400">$19.99/month</p>
            </div>
            <button onClick={() => navigate('/app/settings')} className="w-full mt-4 py-3 bg-slate-800 text-white font-bold rounded-xl hover:bg-slate-700 transition-all">
              Manage Subscription
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;

