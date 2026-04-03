import React, { useState, useEffect } from 'react';
import { 
  Users, 
  FileText, 
  Briefcase, 
  ShieldCheck, 
  ArrowUpRight, 
  ArrowDownRight, 
  Activity,
  Zap,
  CheckCircle2,
  AlertTriangle,
  Clock,
  TrendingUp,
  Target,
  Search
} from 'lucide-react';
import { motion } from 'framer-motion';
import { adminAPI } from '../../services/api';

const AdminDashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        const response = await adminAPI.getStats();
        setData(response.data);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch admin stats:', err);
        setError('Failed to load system metrics. Please ensure you have admin privileges.');
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  const getIcon = (type) => {
    switch (type) {
      case 'users': return Users;
      case 'resumes': return FileText;
      case 'jobs': return Briefcase;
      case 'uptime': return Activity;
      default: return Activity;
    }
  };

  const getColorClass = (type) => {
    switch (type) {
      case 'users': return { color: 'text-blue-400', bg: 'bg-blue-600/10' };
      case 'resumes': return { color: 'text-indigo-400', bg: 'bg-indigo-600/10' };
      case 'jobs': return { color: 'text-purple-400', bg: 'bg-purple-600/10' };
      case 'uptime': return { color: 'text-green-400', bg: 'bg-green-600/10' };
      default: return { color: 'text-slate-400', bg: 'bg-slate-600/10' };
    }
  };

  const getActivityIcon = (type) => {
    switch (type) {
      case 'user': return { icon: Users, color: 'text-blue-400', bg: 'bg-blue-600/10' };
      case 'resume': return { icon: FileText, color: 'text-indigo-400', bg: 'bg-indigo-600/10' };
      case 'application': return { icon: Briefcase, color: 'text-purple-400', bg: 'bg-purple-600/10' };
      default: return { icon: Activity, color: 'text-slate-400', bg: 'bg-slate-600/10' };
    }
  };

  const formatTime = (timeStr) => {
    try {
      const date = new Date(timeStr);
      const now = new Date();
      const diffMs = now - date;
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMins / 60);
      const diffDays = Math.floor(diffHours / 24);

      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffHours < 24) return `${diffHours}h ago`;
      return `${diffDays}d ago`;
    } catch {
      return timeStr;
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <div className="w-12 h-12 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
        <p className="text-slate-500 font-black uppercase tracking-widest text-xs">Accessing Secure Core...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-rose-500/10 border border-rose-500/20 p-8 rounded-4xl text-center space-y-4">
        <AlertTriangle className="mx-auto text-rose-500" size={48} />
        <h3 className="text-xl font-black text-white uppercase tracking-tighter">Access Denied</h3>
        <p className="text-slate-400 font-bold text-sm max-w-md mx-auto">{error}</p>
      </div>
    );
  }

  const stats = data?.stats || [];
  const activity = data?.activity || [];
  const health = data?.health || [];

  return (
    <div className="space-y-12 pb-20">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 px-2">
        <div className="space-y-2">
          <h1 className="text-4xl font-black text-white tracking-tighter uppercase italic">System Overview</h1>
          <p className="text-slate-500 font-bold uppercase tracking-widest text-xs">Platform Master Control Panel</p>
        </div>
        <div className="flex items-center gap-3 w-full md:w-auto">
          <button className="flex-1 md:flex-none px-6 py-4 bg-white/5 border border-white/10 text-white font-black rounded-2xl hover:bg-white/10 transition-all text-xs uppercase tracking-widest flex items-center justify-center gap-2">
            <Activity size={18} /> Logs
          </button>
          <button className="flex-1 md:flex-none px-6 py-4 bg-indigo-600 text-white font-black rounded-2xl shadow-xl shadow-indigo-500/20 hover:bg-indigo-500 transition-all text-xs uppercase tracking-widest flex items-center justify-center gap-2">
            <Zap size={20} /> System Report
          </button>
        </div>
      </div>

      {/* Admin Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
         {stats.map((stat, i) => {
           const Icon = getIcon(stat.type);
           const { color, bg } = getColorClass(stat.type);
           return (
             <motion.div 
               key={stat.label}
               initial={{ opacity: 0, y: 20 }}
               animate={{ opacity: 1, y: 0 }}
               transition={{ delay: i * 0.1 }}
               className="bg-slate-900/40 p-8 rounded-4xl border border-white/5 hover:border-indigo-500/30 transition-all group relative overflow-hidden"
             >
                <div className="absolute top-0 right-0 -mr-10 -mt-10 w-40 h-40 bg-indigo-600/5 blur-3xl group-hover:bg-indigo-600/10 transition-all"></div>
                <div className="flex items-start justify-between relative z-10">
                   <div className="space-y-4">
                      <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">{stat.label}</p>
                      <h3 className="text-4xl font-black text-white tabular-nums tracking-tighter">{stat.value}</h3>
                   </div>
                   <div className={`p-4 rounded-2xl ${bg} ${color} shadow-lg`}>
                      <Icon size={24} />
                   </div>
                </div>
                <div className="mt-6 flex items-center gap-2 text-xs font-black text-green-400 uppercase tracking-widest relative z-10">
                   <ArrowUpRight size={14} />
                   <span>{stat.change} increase</span>
                </div>
             </motion.div>
           );
         })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
         {/* Recent System Logs */}
         <div className="lg:col-span-2 bg-slate-900/40 p-10 rounded-[40px] border border-white/5 space-y-10">
            <div className="flex items-center justify-between">
               <h3 className="text-xl font-black text-white uppercase tracking-widest flex items-center gap-4">
                  <Activity className="text-indigo-400" /> Recent Activity Audit
               </h3>
               <button className="text-[10px] font-black text-slate-500 hover:text-white transition-colors uppercase tracking-widest">See all logs</button>
            </div>
            
            <div className="space-y-2">
               {activity.map((log, idx) => {
                 const { icon: Icon, color, bg } = getActivityIcon(log.type);
                 return (
                   <div key={idx} className="flex items-center justify-between p-6 bg-white/5 border border-white/5 rounded-2xl group hover:bg-white/10 transition-all cursor-default">
                      <div className="flex items-center gap-6">
                         <div className={`p-3 rounded-xl ${bg} ${color}`}>
                            <Icon size={20} />
                         </div>
                         <div>
                            <h4 className="text-sm font-black text-white group-hover:text-indigo-400 transition-colors uppercase tracking-widest">{log.action}</h4>
                            <p className="text-xs text-slate-500 font-bold uppercase tracking-widest mt-1 opacity-60">{log.user}</p>
                         </div>
                      </div>
                      <div className="text-right">
                         <p className="text-[10px] font-black text-slate-600 uppercase tracking-widest">{formatTime(log.time)}</p>
                         <span className="text-[8px] font-black text-indigo-500 uppercase tracking-widest mt-1 inline-block opacity-40">AUDIT_VERIFIED</span>
                      </div>
                   </div>
                 );
               })}
            </div>
         </div>

         {/* System Health */}
         <div className="bg-slate-900/40 p-10 rounded-[40px] border border-white/5 space-y-10">
            <h3 className="text-xl font-black text-white uppercase tracking-widest flex items-center gap-4">
               <ShieldCheck className="text-green-400" /> Health Check
            </h3>
            
            <div className="space-y-8">
               {health.map(h => {
                 const statusColor = h.type === 'success' ? 'text-green-500' : (h.type === 'warning' ? 'text-amber-500' : 'text-rose-500');
                 const Icon = h.type === 'success' ? CheckCircle2 : (h.type === 'warning' ? AlertTriangle : AlertTriangle);
                 
                 return (
                   <div key={h.label} className="flex items-center justify-between p-4 bg-slate-900 rounded-2xl border border-white/5 group">
                      <div className="flex items-center gap-4">
                         <h4 className="text-xs font-black text-slate-500 uppercase tracking-widest">{h.label}</h4>
                      </div>
                      <div className={`flex items-center gap-2 text-[10px] font-black uppercase tracking-widest ${statusColor}`}>
                         <Icon size={14} />
                         {h.status}
                      </div>
                   </div>
                 );
               })}
               
               <div className="pt-4 space-y-4">
                  <div className="p-6 bg-indigo-600/10 border border-indigo-500/20 rounded-3xl space-y-3">
                     <p className="text-[10px] font-black text-indigo-400 uppercase tracking-widest">Next Maintenance Window</p>
                     <p className="text-lg font-black text-white uppercase tracking-tighter flex items-center gap-2 italic">
                        <Clock size={18} /> Sunday 02:00 AM
                     </p>
                  </div>
                  <button className="w-full py-4 bg-indigo-600 hover:bg-indigo-500 text-white font-black rounded-2xl transition-all text-xs uppercase tracking-[0.2em] shadow-2xl shadow-indigo-500/20">
                     Force Flush Cache
                  </button>
               </div>
            </div>
         </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
