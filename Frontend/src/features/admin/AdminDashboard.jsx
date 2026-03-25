import React from 'react';
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

const AdminDashboard = () => {
  const stats = [
    { label: 'Total Users', value: '10,245', change: '+12%', icon: Users, color: 'text-blue-400', bg: 'bg-blue-600/10' },
    { label: 'Active Resumes', value: '25,841', change: '+8%', icon: FileText, color: 'text-indigo-400', bg: 'bg-indigo-600/10' },
    { label: 'Jobs Scraped', value: '154,203', change: '+24%', icon: Briefcase, color: 'text-purple-400', bg: 'bg-purple-600/10' },
    { label: 'System Uptime', value: '99.98%', change: '+0.01%', icon: Activity, color: 'text-green-400', bg: 'bg-green-600/10' },
  ];

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
         {stats.map((stat, i) => (
           <motion.div 
             key={stat.label}
             initial={{ opacity: 0, y: 20 }}
             animate={{ opacity: 1, y: 0 }}
             transition={{ delay: i * 0.1 }}
             className="bg-slate-900/40 p-8 rounded-[32px] border border-white/5 hover:border-indigo-500/30 transition-all group relative overflow-hidden"
           >
              <div className="absolute top-0 right-0 -mr-10 -mt-10 w-40 h-40 bg-indigo-600/5 blur-3xl group-hover:bg-indigo-600/10 transition-all"></div>
              <div className="flex items-start justify-between relative z-10">
                 <div className="space-y-4">
                    <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">{stat.label}</p>
                    <h3 className="text-4xl font-black text-white tabular-nums tracking-tighter">{stat.value}</h3>
                 </div>
                 <div className={`p-4 rounded-2xl ${stat.bg} ${stat.color} shadow-lg`}>
                    <stat.icon size={24} />
                 </div>
              </div>
              <div className="mt-6 flex items-center gap-2 text-xs font-black text-green-400 uppercase tracking-widest relative z-10">
                 <ArrowUpRight size={14} />
                 <span>{stat.change} increase</span>
              </div>
           </motion.div>
         ))}
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
               {[
                 { action: 'New User Registered', user: 'sarah.smith@example.com', time: '2 mins ago', icon: Users, color: 'text-blue-400', bg: 'bg-blue-600/10' },
                 { action: 'Resume Analyzed (AI)', user: 'john.doe@test.com', time: '5 mins ago', icon: FileText, color: 'text-indigo-400', bg: 'bg-indigo-600/10' },
                 { action: 'Job Scrape Completed', user: 'System Bot', time: '12 mins ago', icon: Briefcase, color: 'text-purple-400', bg: 'bg-purple-600/10' },
                 { action: 'Security Protocol Alpha', user: 'Admin 01', time: '1 hour ago', icon: ShieldCheck, color: 'text-rose-400', bg: 'bg-rose-600/10' },
               ].map((log, idx) => (
                 <div key={idx} className="flex items-center justify-between p-6 bg-white/5 border border-white/5 rounded-2xl group hover:bg-white/10 transition-all cursor-default">
                    <div className="flex items-center gap-6">
                       <div className={`p-3 rounded-xl ${log.bg} ${log.color}`}>
                          <log.icon size={20} />
                       </div>
                       <div>
                          <h4 className="text-sm font-black text-white group-hover:text-indigo-400 transition-colors uppercase tracking-widest">{log.action}</h4>
                          <p className="text-xs text-slate-500 font-bold uppercase tracking-widest mt-1 opacity-60">{log.user}</p>
                       </div>
                    </div>
                    <div className="text-right">
                       <p className="text-[10px] font-black text-slate-600 uppercase tracking-widest">{log.time}</p>
                       <span className="text-[8px] font-black text-indigo-500 uppercase tracking-widest mt-1 inline-block opacity-40">AUDIT_VERIFIED</span>
                    </div>
                 </div>
               ))}
            </div>
         </div>

         {/* System Health */}
         <div className="bg-slate-900/40 p-10 rounded-[40px] border border-white/5 space-y-10">
            <h3 className="text-xl font-black text-white uppercase tracking-widest flex items-center gap-4">
               <ShieldCheck className="text-green-400" /> Health Check
            </h3>
            
            <div className="space-y-8">
               {[
                 { label: 'Database Integrity', status: 'Optimal', icon: CheckCircle2, color: 'text-green-500' },
                 { label: 'AI Inference API', status: 'Stable', icon: CheckCircle2, color: 'text-green-500' },
                 { label: 'Memory Usage', status: '82%', icon: AlertTriangle, color: 'text-amber-500' },
                 { label: 'API Latency', status: '124ms', icon: CheckCircle2, color: 'text-green-500' },
               ].map(h => (
                 <div key={h.label} className="flex items-center justify-between p-4 bg-slate-900 rounded-2xl border border-white/5 group">
                    <div className="flex items-center gap-4">
                       <h4 className="text-xs font-black text-slate-500 uppercase tracking-widest">{h.label}</h4>
                    </div>
                    <div className={`flex items-center gap-2 text-[10px] font-black uppercase tracking-widest ${h.color}`}>
                       <h.icon size={14} />
                       {h.status}
                    </div>
                 </div>
               ))}
               
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
