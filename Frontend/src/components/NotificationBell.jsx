import React, { useState, useEffect, useCallback } from 'react';
import { Bell, Mail, Clock, Check, X, Eye, EyeOff, Trash2, Settings, Calendar, Briefcase, Target, Star, AlertTriangle, CheckCircle, MessageSquare, Download, Share2, Filter, ChevronDown, ChevronUp, FileText, BarChart3 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../services/api';

const NotificationSettings = ({ setIsSettingsOpen }) => (
  <motion.div
    initial={{ opacity: 0, scale: 0.95 }}
    animate={{ opacity: 1, scale: 1 }}
    className="absolute right-0 mt-2 w-80 bg-slate-900 border border-white/10 rounded-xl shadow-2xl z-50"
  >
    <div className="p-4 border-b border-white/10">
      <h3 className="font-bold text-white flex items-center gap-2">
        <Settings size={18} />
        Notification Settings
      </h3>
    </div>
    
    <div className="p-4 space-y-4">
      <div className="space-y-2">
        <label className="text-xs font-bold text-slate-500 uppercase">Notification Types</label>
        <div className="space-y-2">
          {[
            { key: 'resume', label: 'Resume Updates', checked: true },
            { key: 'interview', label: 'Interview Scheduling', checked: true },
            { key: 'job', label: 'Job Matches', checked: true },
            { key: 'application', label: 'Application Status', checked: true },
            { key: 'skill', label: 'Skill Recommendations', checked: false },
            { key: 'analytics', label: 'Weekly Reports', checked: true }
          ].map(setting => (
            <label key={setting.key} className="flex items-center gap-3 cursor-pointer">
              <input type="checkbox" defaultChecked={setting.checked} className="rounded" />
              <span className="text-sm text-slate-300">{setting.label}</span>
            </label>
          ))}
        </div>
      </div>
      
      <div className="space-y-2">
        <label className="text-xs font-bold text-slate-500 uppercase">Email Notifications</label>
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-300">Send email summaries</span>
          <input type="checkbox" defaultChecked className="rounded" />
        </div>
      </div>
      
      <div className="flex gap-2 pt-2">
        <button className="flex-1 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-all text-sm">
          Save Settings
        </button>
        <button 
          onClick={() => setIsSettingsOpen(false)}
          className="flex-1 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-all text-sm"
        >
          Close
        </button>
      </div>
    </div>
  </motion.div>
);

const NotificationBell = () => {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [filter, setFilter] = useState('all');
  const [sortBy, setSortBy] = useState('newest');

  const fetchNotifications = useCallback(async () => {
    try {
      const response = await api.get('/api/notifications');
      const data = response.data || [];
      setNotifications(data);
      setUnreadCount(data.filter(n => !n.is_read).length);
    } catch {
      setNotifications([]);
      setUnreadCount(0);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, [fetchNotifications]);

  const markAsRead = async (notificationId) => {
    try {
      await api.put(`/api/notifications/${notificationId}/read`);
      setNotifications(prev => prev.map(n => n.id === notificationId ? { ...n, is_read: true } : n));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      await api.put('/api/notifications/read-all');
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (error) {
      console.error('Error marking all as read:', error);
    }
  };

  const deleteNotification = async (notificationId) => {
    try {
      await api.delete(`/api/notifications/${notificationId}`);
      setNotifications(prev => prev.filter(n => n.id !== notificationId));
      if (!notifications.find(n => n.id === notificationId)?.is_read) {
        setUnreadCount(prev => Math.max(0, prev - 1));
      }
    } catch (error) {
      console.error('Error deleting notification:', error);
    }
  };

  const deleteAllRead = async () => {
    try {
      // In a real app, you'd have an endpoint for this
      // For now, we'll just filter locally after a hypothetical API call
      setNotifications(prev => prev.filter(n => !n.is_read));
      setUnreadCount(0);
    } catch (error) {
      console.error('Error deleting read notifications:', error);
    }
  };

  const getNotificationIcon = (category) => {
    switch(category) {
      case 'resume': return FileText;
      case 'interview': return Calendar;
      case 'job': return Briefcase;
      case 'application': return Target;
      case 'skill': return Star;
      case 'analytics': return BarChart3;
      default: return Mail;
    }
  };

  const getNotificationColor = (type) => {
    switch(type) {
      case 'success': return 'text-green-400';
      case 'warning': return 'text-amber-400';
      case 'error': return 'text-red-400';
      default: return 'text-blue-400';
    }
  };

  const filteredNotifications = notifications.filter(notification => {
    if (filter === 'unread') return !notification.is_read;
    if (filter === 'read') return notification.is_read;
    return true;
  });

  const sortedNotifications = [...filteredNotifications].sort((a, b) => {
    if (sortBy === 'newest') {
      return new Date(b.created_at || b.time) - new Date(a.created_at || a.time);
    } else {
      return new Date(a.created_at || a.time) - new Date(b.created_at || b.time);
    }
  });

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2.5 text-white hover:bg-white/10 rounded-lg transition-all group"
      >
        <Bell size={20} />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center font-bold">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -10 }}
            className="absolute right-0 mt-2 w-96 bg-slate-900 border border-white/10 rounded-xl shadow-2xl z-50 overflow-hidden"
          >
            {/* Header */}
            <div className="p-4 border-b border-white/10 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <h3 className="font-bold text-white">Notifications</h3>
                {unreadCount > 0 && (
                  <span className="text-xs text-slate-400">({unreadCount} unread)</span>
                )}
              </div>
              <div className="flex gap-2">
                {unreadCount > 0 && (
                  <button onClick={markAllAsRead} className="text-sm text-blue-400 hover:text-blue-300">
                    Mark all read
                  </button>
                )}
                <button onClick={() => setIsSettingsOpen(!isSettingsOpen)} className="p-1 text-slate-400 hover:text-white transition-colors">
                  <Settings size={16} />
                </button>
              </div>
            </div>

            {/* Filters */}
            <div className="p-3 border-b border-white/10 bg-slate-950/50">
              <div className="flex items-center justify-between gap-2">
                <div className="flex gap-1">
                  {['all', 'unread', 'read'].map(filterType => (
                    <button
                      key={filterType}
                      onClick={() => setFilter(filterType)}
                      className={`px-3 py-1 rounded-lg text-xs font-bold capitalize ${
                        filter === filterType 
                          ? 'bg-blue-600 text-white' 
                          : 'bg-slate-800 text-slate-400 hover:text-white'
                      } transition-all`}
                    >
                      {filterType}
                    </button>
                  ))}
                </div>
                <div className="flex gap-1">
                  {['newest', 'oldest'].map(sortType => (
                    <button
                      key={sortType}
                      onClick={() => setSortBy(sortType)}
                      className={`px-3 py-1 rounded-lg text-xs font-bold capitalize ${
                        sortBy === sortType 
                          ? 'bg-slate-700 text-white' 
                          : 'bg-slate-800 text-slate-400 hover:text-white'
                      } transition-all`}
                    >
                      {sortType}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Notifications List */}
            <div className="max-h-96 overflow-y-auto">
              {sortedNotifications.length === 0 ? (
                <div className="p-6 text-center text-slate-500">
                  <div className="w-12 h-12 bg-slate-800 rounded-full mx-auto mb-4 flex items-center justify-center">
                    <Check size={24} className="text-slate-500" />
                  </div>
                  <p>No notifications</p>
                  <p className="text-xs text-slate-600 mt-1">You're all caught up!</p>
                </div>
              ) : (
                sortedNotifications.map(notification => {
                  const Icon = getNotificationIcon(notification.category);
                  return (
                    <motion.div
                      key={notification.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      className={`p-4 border-b border-white/5 hover:bg-white/5 cursor-pointer transition-all ${
                        notification.is_read ? 'opacity-75' : 'bg-blue-600/10'
                      }`}
                      onClick={() => !notification.is_read && markAsRead(notification.id)}
                    >
                      <div className="flex items-start gap-3">
                        <div className={`p-2 rounded-lg ${
                          notification.type === 'success' ? 'bg-green-600/20' :
                          notification.type === 'warning' ? 'bg-amber-600/20' :
                          notification.type === 'error' ? 'bg-red-600/20' :
                          'bg-blue-600/20'
                        }`}>
                          <Icon size={16} className={getNotificationColor(notification.type)} />
                        </div>
                        <div className="flex-1 space-y-1">
                          <div className="flex items-center justify-between">
                            <h4 className="font-semibold text-white">{notification.title}</h4>
                            <div className="flex gap-1">
                              {!notification.is_read && (
                                <button 
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    markAsRead(notification.id);
                                  }}
                                  className="p-1 text-slate-400 hover:text-green-400 transition-colors"
                                >
                                  <Eye size={14} />
                                </button>
                              )}
                              <button 
                                onClick={(e) => {
                                  e.stopPropagation();
                                  deleteNotification(notification.id);
                                }}
                                className="p-1 text-slate-400 hover:text-red-400 transition-colors"
                              >
                                <Trash2 size={14} />
                              </button>
                            </div>
                          </div>
                          <p className="text-sm text-slate-400">{notification.message}</p>
                          <div className="flex items-center justify-between text-xs text-slate-600">
                            <span>{new Date(notification.created_at || notification.time).toLocaleDateString()}</span>
                            <span className="capitalize text-slate-500">{notification.category}</span>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  );
                })
              )}
            </div>

            {/* Footer Actions */}
            <div className="p-3 border-t border-white/10 bg-slate-950/50">
              <div className="flex items-center justify-between gap-2">
                <button 
                  onClick={deleteAllRead}
                  className="text-xs text-slate-400 hover:text-red-400 transition-colors"
                >
                  Clear read notifications
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {isSettingsOpen && <NotificationSettings setIsSettingsOpen={setIsSettingsOpen} />}
    </div>
  );
};

export default NotificationBell;