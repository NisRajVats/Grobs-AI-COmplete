import React, { useState, useEffect } from 'react';
import { Plus, Search, Filter, Calendar, MapPin, ChevronRight, Clock, CheckCircle2, AlertTriangle, Mail, Zap, Kanban } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { applicationsAPI } from '../../services/api';

// UI Components
import Button from '../../components/ui/Button';
import Card from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import Input from '../../components/ui/Input';
import EmptyState from '../../components/ui/EmptyState';

const ApplicationTracker = () => {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    fetchApplications();
  }, []);

  const fetchApplications = async () => {
    try {
      setLoading(true);
      const response = await applicationsAPI.getApplications();
      setApplications(response.data || []);
    } catch (error) {
      console.error("Error fetching applications:", error);
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    { id: 'applied', label: 'Applied', color: 'bg-blue-500', text: 'text-blue-400', border: 'border-blue-500/20' },
    { id: 'interview', label: 'Interview', color: 'bg-amber-500', text: 'text-amber-400', border: 'border-amber-500/20' },
    { id: 'offer', label: 'Offer', color: 'bg-emerald-500', text: 'text-emerald-400', border: 'border-emerald-500/20' },
    { id: 'rejected', label: 'Rejected', color: 'bg-rose-500', text: 'text-rose-400', border: 'border-rose-500/20' },
  ];

  const filteredApps = applications.filter(app => 
    app.job_title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    app.company?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-10 max-w-[1600px] mx-auto pb-20">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-8">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-blue-600/10 rounded-xl">
              <Kanban className="text-blue-500" size={24} />
            </div>
            <h1 className="text-4xl font-black text-white tracking-tight">Application Tracker</h1>
          </div>
          <p className="text-slate-400 font-medium text-lg ml-12">Manage and track your job applications</p>
        </div>
        
        <div className="flex flex-wrap items-center gap-4 w-full md:w-auto">
          <div className="relative flex-1 md:w-72">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
            <input 
              type="text"
              placeholder="Search companies, roles..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-900/50 border border-white/5 rounded-2xl pl-12 pr-4 py-3.5 text-white placeholder:text-slate-600 focus:outline-hidden focus:ring-2 focus:ring-blue-500/30 transition-all font-medium"
            />
          </div>
          <Button variant="outline" leftIcon={Filter} className="border-white/5 bg-slate-900/50 h-13">Filters</Button>
          <Button leftIcon={Plus} className="bg-blue-600 hover:bg-blue-500 shadow-xl shadow-blue-500/20 h-13 font-black">
            New Application
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center h-96 gap-4">
          <div className="relative">
            <div className="w-16 h-16 border-4 border-blue-500/10 border-t-blue-500 rounded-full animate-spin"></div>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-8 h-8 border-4 border-slate-900/50 rounded-full animate-pulse"></div>
            </div>
          </div>
          <p className="text-slate-500 font-bold uppercase tracking-widest text-xs animate-pulse">Syncing with pipeline...</p>
        </div>
      ) : applications.length === 0 ? (
        <EmptyState 
          icon={Kanban}
          title="No applications yet"
          description="Your job search journey starts here. Add your first application to begin tracking."
          actionText="Add Application"
          onAction={() => {}}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {columns.map(col => {
            const columnApps = filteredApps.filter(a => (a.status?.toLowerCase() || 'applied') === col.id);
            
            return (
              <div key={col.id} className="space-y-6 flex flex-col h-full">
                {/* Column Header */}
                <div className={`flex items-center justify-between p-4 bg-slate-900/40 border-b-2 ${col.border} rounded-t-2xl`}>
                  <div className="flex items-center gap-3">
                    <div className={`w-2.5 h-2.5 rounded-full ${col.color} shadow-[0_0_12px_rgba(0,0,0,0.2)] shadow-${col.id}-500`}></div>
                    <h3 className="text-sm font-black text-white uppercase tracking-widest">{col.label}</h3>
                  </div>
                  <Badge variant="ghost" className={`${col.text} bg-white/5 font-black px-2.5`}>
                    {columnApps.length}
                  </Badge>
                </div>

                {/* Column Body */}
                <div className="space-y-4 flex-1 overflow-y-auto max-h-[70vh] pr-2 custom-scrollbar">
                  <AnimatePresence mode="popLayout">
                    {columnApps.map(app => (
                      <motion.div
                        layout
                        key={app.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        whileHover={{ y: -4, scale: 1.02 }}
                        transition={{ type: "spring", stiffness: 300, damping: 25 }}
                      >
                        <Card padding="none" className="group overflow-hidden border-white/5 hover:border-blue-500/30 hover:bg-slate-900/80 cursor-pointer shadow-lg transition-all">
                          <div className="p-5 space-y-5">
                            <div className="flex items-start gap-4">
                              <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center text-slate-900 font-black text-xl shadow-inner shrink-0 uppercase">
                                {app.company ? app.company[0] : '?'}
                              </div>
                              <div className="flex-1 min-w-0">
                                <h4 className="font-black text-white text-base truncate group-hover:text-blue-400 transition-colors leading-tight">
                                  {app.job_title}
                                </h4>
                                <p className="text-sm text-slate-500 font-bold">{app.company}</p>
                              </div>
                            </div>

                            <div className="flex flex-wrap gap-3 items-center pt-2 border-t border-white/5">
                              <div className="flex items-center gap-1.5 text-[11px] text-slate-500 font-black uppercase tracking-wider">
                                <Calendar size={12} className="text-slate-600" />
                                {app.applied_date ? new Date(app.applied_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) : 'N/A'}
                              </div>
                              <div className="flex items-center gap-1.5 text-[11px] text-slate-500 font-black uppercase tracking-wider">
                                <MapPin size={12} className="text-slate-600" />
                                Remote
                              </div>
                            </div>

                            {app.next_step && (
                              <div className="mt-2 p-3 bg-blue-500/5 border border-blue-500/10 rounded-xl flex items-center gap-2 group/step">
                                <div className="p-1 bg-blue-500/20 rounded-md">
                                  <Zap size={10} className="text-blue-400" />
                                </div>
                                <div className="flex-1 min-w-0">
                                  <p className="text-[10px] text-slate-500 font-black uppercase tracking-widest leading-none mb-1">Next Action</p>
                                  <p className="text-[11px] font-bold text-blue-400 truncate leading-none uppercase tracking-wide">
                                    {app.next_step}
                                  </p>
                                </div>
                              </div>
                            )}
                          </div>
                          
                          {/* Bottom Action Bar (Hidden by default, shown on hover) */}
                          <div className="px-5 py-3 bg-white/5 flex items-center justify-between opacity-0 group-hover:opacity-100 transition-opacity">
                             <div className="flex gap-2">
                                <div className="w-2 h-2 rounded-full bg-slate-700"></div>
                                <div className="w-2 h-2 rounded-full bg-slate-700"></div>
                             </div>
                             <ChevronRight size={14} className="text-slate-500" />
                          </div>
                        </Card>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                  
                  {columnApps.length === 0 && (
                    <div className="h-24 border-2 border-dashed border-white/5 rounded-2xl flex items-center justify-center">
                       <p className="text-slate-700 text-[10px] font-black uppercase tracking-[0.2em]">Empty Stage</p>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default ApplicationTracker;


