import React, { useState } from 'react';
import { 
  LayoutDashboard, 
  Users, 
  FileText, 
  Briefcase, 
  BarChart3, 
  Settings, 
  ShieldCheck, 
  Zap, 
  ChevronRight, 
  ChevronLeft, 
  Bell, 
  Search, 
  ArrowUpRight,
  TrendingUp,
  Activity,
  LogOut,
  Target,
  Database,
  Lock,
  Menu,
  X
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { NavLink, Outlet } from 'react-router-dom';

const AdminLayout = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const adminNav = [
    { group: 'Overview', items: [
      { name: 'Admin Dashboard', icon: LayoutDashboard, path: '/admin/dashboard' },
      { name: 'Analytics', icon: BarChart3, path: '/admin/stats' },
    ]},
    { group: 'Management', items: [
      { name: 'User Directory', icon: Users, path: '/admin/users' },
      { name: 'Resumes Database', icon: FileText, path: '/admin/resumes' },
      { name: 'Job Board Manager', icon: Briefcase, path: '/admin/jobs' },
    ]},
    { group: 'System', items: [
      { name: 'Security & Logs', icon: ShieldCheck, path: '/admin/system' },
      { name: 'Platform Settings', icon: Settings, path: '/admin/settings' },
    ]}
  ];

  return (
    <div className="flex min-h-screen bg-[#020617] text-slate-200">
      {/* Sidebar */}
      <motion.aside
        initial={false}
        animate={{ width: isCollapsed ? 80 : 280 }}
        className="fixed left-0 top-0 h-screen bg-slate-900 border-r border-white/5 z-50 flex flex-col transition-all duration-300 shadow-2xl"
      >
        <div className="p-8 flex items-center gap-3">
          <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <ShieldCheck className="text-white fill-white" size={24} />
          </div>
          {!isCollapsed && <span className="text-2xl font-black text-white tracking-tighter uppercase italic">ADMIN</span>}
        </div>

        <nav className="flex-1 px-4 space-y-8 mt-10 overflow-y-auto custom-scrollbar">
           {adminNav.map((group, idx) => (
             <div key={idx} className="space-y-2">
                {!isCollapsed && <h3 className="text-[10px] font-black text-slate-600 uppercase tracking-[0.2em] px-3 mb-2">{group.group}</h3>}
                {group.items.map(item => (
                   <NavLink
                    key={item.name}
                    to={item.path}
                    className={({ isActive }) => `flex items-center gap-3 px-4 py-3 rounded-xl transition-all group ${isActive ? 'bg-indigo-600/10 border border-indigo-500/20 text-indigo-400' : 'text-slate-500 hover:text-white hover:bg-white/5 border border-transparent'}`}
                   >
                    <item.icon size={18} />
                    {!isCollapsed && <span className="text-sm font-bold">{item.name}</span>}
                   </NavLink>
                ))}
             </div>
           ))}
        </nav>

        <div className="p-4 border-t border-white/5">
           <button onClick={() => setIsCollapsed(!isCollapsed)} className="w-full py-4 flex items-center justify-center text-slate-600 hover:text-white transition-colors">
              {isCollapsed ? <ChevronRight size={20} /> : <div className="flex items-center gap-2"><ChevronLeft size={20} /> <span className="text-xs font-bold uppercase tracking-widest">Collapse Menu</span></div>}
           </button>
        </div>
      </motion.aside>

      {/* Main Content */}
      <motion.main
        initial={false}
        animate={{ marginLeft: isCollapsed ? 80 : 280 }}
        className="flex-1 min-h-screen p-8 pt-24 transition-all duration-300 relative"
      >
        {/* Topbar */}
        <header className="fixed top-0 right-0 left-0 bg-[#020617]/80 backdrop-blur-xl border-b border-white/5 h-20 flex items-center justify-between px-12 z-40" style={{ left: isCollapsed ? 80 : 280 }}>
           <div className="flex-1 max-w-xl relative group">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-600 group-focus-within:text-indigo-400" size={18} />
              <input placeholder="Search users, records, audit logs..." className="w-full bg-slate-900/50 border border-white/5 rounded-2xl py-3 pl-12 pr-4 text-sm text-white focus:ring-2 focus:ring-indigo-500/30" />
           </div>
           
           <div className="flex items-center gap-6">
              <div className="flex items-center gap-2 px-6 border-r border-white/5">
                 <button className="p-2.5 rounded-xl bg-white/5 text-slate-500 hover:text-white transition-all"><Bell size={18} /></button>
                 <button className="p-2.5 rounded-xl bg-white/5 text-slate-500 hover:text-white transition-all"><Activity size={18} /></button>
              </div>
              <div className="flex items-center gap-4 group cursor-pointer pl-4">
                 <div className="text-right">
                    <h4 className="text-sm font-black text-white">System Admin</h4>
                    <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Master Control</p>
                 </div>
                 <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center font-black text-white shadow-xl shadow-indigo-500/20">SA</div>
              </div>
           </div>
        </header>

        <div className="max-w-7xl mx-auto py-10">
           <Outlet />
        </div>
      </motion.main>
    </div>
  );
};

export default AdminLayout;
