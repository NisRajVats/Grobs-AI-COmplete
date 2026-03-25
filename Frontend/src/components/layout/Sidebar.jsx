import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  FileText, 
  Briefcase, 
  UserCircle, 
  Settings, 
  MessageSquare, 
  Zap,
  ChevronLeft,
  ChevronRight,
  Plus,
  Upload,
  Eye,
  Edit3,
  Target,
  Sparkles,
  Download,
  Search,
  Bookmark,
  ClipboardList,
  Calendar,
  Bell,
  Users,
  BarChart3,
  ChevronDown,
  LogOut,
  User
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { useAuth } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';

function cn(...inputs) {
  return twMerge(clsx(inputs));
}

const navItems = [
  { 
    group: 'Main', 
    icon: LayoutDashboard,
    path: '/app/dashboard',
    name: 'Dashboard' 
  },
  { 
    group: 'Resume Center', 
    icon: FileText,
    name: 'Resume Center',
    path: '/app/resumes',
    children: [
      { name: 'My Resumes', path: '/app/resumes', icon: FileText },
      { name: 'Create Resume', path: '/app/resumes/create', icon: Plus },
      { name: 'Upload Resume', path: '/app/resumes/upload', icon: Upload },
    ]
  },
  { 
    group: 'Job Center', 
    icon: Briefcase,
    name: 'Job Center',
    path: '/app/jobs',
    children: [
      { name: 'Recommended Jobs', path: '/app/jobs/recommended', icon: Search },
      { name: 'Saved Jobs', path: '/app/jobs/saved', icon: Bookmark },
      { name: 'Applications', path: '/app/jobs/applications', icon: ClipboardList },
      { name: 'Application Tracker', path: '/app/jobs/tracker', icon: Calendar },
    ]
  },
  { 
    group: 'Interview Preparation', 
    icon: Zap,
    name: 'Interview Prep',
    path: '/app/interview',
    children: [
      { name: 'Select Role', path: '/app/interview', icon: Users },
      { name: 'Practice Questions', path: '/app/interview/questions', icon: MessageSquare },
      { name: 'AI Mock Interview', path: '/app/interview/mock', icon: Zap },
    ]
  },
  { 
    group: 'Profile', 
    icon: UserCircle,
    name: 'Profile',
    path: '/app/profile',
    children: [
      { name: 'View Profile', path: '/app/profile', icon: UserCircle },
      { name: 'Edit Information', path: '/app/profile/edit', icon: Edit3 },
      { name: 'Settings', path: '/app/settings', icon: Settings },
    ]
  }
];

const Sidebar = ({ isCollapsed, setIsCollapsed }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [expandedGroups, setExpandedGroups] = useState(['Resume Center', 'Job Center', 'Interview Preparation', 'Profile']);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const toggleGroup = (groupName) => {
    setExpandedGroups(prev => 
      prev.includes(groupName) 
        ? prev.filter(g => g !== groupName)
        : [...prev, groupName]
    );
  };

  const isGroupExpanded = (groupName) => expandedGroups.includes(groupName);

  return (
    <motion.aside
      initial={false}
      animate={{ width: isCollapsed ? 80 : 280 }}
      className="fixed left-0 top-0 h-screen sidebar-glass z-50 overflow-y-auto overflow-x-hidden flex flex-col no-print"
    >
      {/* Logo */}
      <div className="p-6 flex items-center gap-3">
        <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center shrink-0 shadow-lg shadow-blue-500/30">
          <Zap className="text-white fill-white" size={24} />
        </div>
        {!isCollapsed && (
          <motion.span 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-2xl font-bold bg-clip-text text-transparent bg-linear-to-r from-white to-blue-400"
          >
            GROBS.AI
          </motion.span>
        )}
      </div>

      {/* Nav Items */}
      <nav className="flex-1 px-4 space-y-2 mt-4">
        {navItems.map((item, idx) => (
          <div key={item.group || item.name} className="space-y-1">
            {item.children ? (
              // Group with children
              <>
                <button
                  onClick={() => toggleGroup(item.group)}
                  className={cn(
                    "w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group relative",
                    "text-slate-400 hover:text-white hover:bg-white/5"
                  )}
                >
                  <item.icon size={20} className="shrink-0" />
                  {!isCollapsed && (
                    <motion.span
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="font-medium truncate flex-1 text-left"
                    >
                      {item.group}
                    </motion.span>
                  )}
                  {!isCollapsed && (
                    <ChevronDown 
                      size={16} 
                      className={cn(
                        "transition-transform duration-200", 
                        isGroupExpanded(item.group) ? "rotate-180" : ""
                      )} 
                    />
                  )}
                </button>
                
                {/* Children */}
                <AnimatePresence>
                  {isCollapsed && (
                    <div className="absolute left-full ml-4 px-3 py-1 bg-slate-800 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-100 border border-white/10 shadow-xl">
                      {item.group}
                    </div>
                  )}
                </AnimatePresence>
                
                {!isCollapsed && isGroupExpanded(item.group) && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="ml-4 pl-3 border-l border-white/10 space-y-1"
                  >
                    {item.children.map((child) => (
                      <NavLink
                        key={child.name}
                        to={child.path}
                        end={child.path === '/app/resumes' || child.path === '/app/jobs' || child.path === '/app/interview' || child.path === '/app/profile'}
                        className={({ isActive }) => cn(
                          "flex items-center gap-3 px-3 py-2 rounded-xl transition-all duration-200 group",
                          isActive 
                            ? "bg-blue-600/20 text-blue-400 border border-blue-500/20" 
                            : "text-slate-500 hover:text-white hover:bg-white/5"
                        )}
                      >
                        <child.icon size={16} className="shrink-0" />
                        <span className="text-sm font-medium truncate">{child.name}</span>
                      </NavLink>
                    ))}
                  </motion.div>
                )}
              </>
            ) : (
              // Simple item (Dashboard)
              <NavLink
                to={item.path}
                className={({ isActive }) => cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group relative",
                  isActive 
                    ? "bg-blue-600/20 text-blue-400 border border-blue-500/20" 
                    : "text-slate-400 hover:text-white hover:bg-white/5"
                )}
              >
                <item.icon size={20} className="shrink-0" />
                {!isCollapsed && (
                  <motion.span
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="font-medium truncate"
                  >
                    {item.name}
                  </motion.span>
                )}
                
                {/* Tooltip for collapsed mode */}
                {isCollapsed && (
                  <div className="absolute left-full ml-4 px-3 py-1 bg-slate-800 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-100 border border-white/10 shadow-xl">
                    {item.name}
                  </div>
                )}
              </NavLink>
            )}
          </div>
        ))}
      </nav>
      
      {/* Profile Section */}
      <div className="mt-auto p-4 border-t border-white/10">
        <div className={cn(
          "flex items-center gap-3 p-3 rounded-2xl bg-white/5 border border-white/5 transition-all",
          isCollapsed ? "justify-center" : "justify-between"
        )}>
          <div 
            className="flex items-center gap-3 cursor-pointer overflow-hidden"
            onClick={() => navigate('/app/profile')}
          >
            <div className="relative shrink-0">
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
              <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-green-500 rounded-full border-2 border-slate-900"></div>
            </div>
            
            {!isCollapsed && (
              <div className="text-left overflow-hidden">
                <h4 className="text-sm font-semibold text-white truncate">
                  {user?.full_name || user?.email?.split('@')[0] || 'User'}
                </h4>
                <p className="text-xs text-slate-400 truncate">{user?.title || 'Job Seeker'}</p>
              </div>
            )}
          </div>
          
          {!isCollapsed && (
            <button 
              onClick={handleLogout}
              className="p-2 rounded-lg hover:bg-rose-500/10 text-slate-400 hover:text-rose-400 transition-all shrink-0"
              title="Sign Out"
            >
              <LogOut size={18} />
            </button>
          )}
        </div>
      </div>

      {/* Collapse Toggle */}
      <div className="p-4 border-t border-white/10">
        <button 
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="w-full flex items-center justify-center p-2 rounded-lg hover:bg-white/5 transition-colors text-slate-400"
        >
          {isCollapsed ? <ChevronRight size={20} /> : <div className="flex items-center gap-2"><ChevronLeft size={20} /> <span className="text-sm">Collapse</span></div>}
        </button>
      </div>
    </motion.aside>
  );
};

export default Sidebar;
