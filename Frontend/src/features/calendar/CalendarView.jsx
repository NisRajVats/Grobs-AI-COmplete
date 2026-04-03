import React, { useState, useEffect } from 'react';
import { 
  Calendar, 
  Plus, 
  Edit, 
  Trash2, 
  Video, 
  Users, 
  Clock, 
  MapPin,
  Calendar as CalendarIcon,
  CheckCircle,
  XCircle,
  Eye,
  Download,
  Share2,
  ChevronLeft,
  ChevronRight,
  Sun,
  Moon,
  Coffee,
  Briefcase
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { calendarAPI } from '../../services/api';

const CalendarView = () => {
  const [events, setEvents] = useState([]);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [showModal, setShowModal] = useState(false);
  const [editingEvent, setEditingEvent] = useState(null);
  const [viewMode, setViewMode] = useState('month'); // 'month', 'week', 'day'
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async () => {
    try {
      setLoading(true);
      const response = await calendarAPI.getEvents();
      setEvents(response.data);
    } catch (error) {
      console.error('Failed to fetch events:', error);
    } finally {
      setLoading(false);
    }
  };

  const addEvent = async (eventData) => {
    try {
      const response = await calendarAPI.createEvent(eventData);
      setEvents([...events, response.data]);
      setShowModal(false);
    } catch (error) {
      console.error('Failed to add event:', error);
    }
  };

  const deleteEvent = async (eventId) => {
    try {
      await calendarAPI.deleteEvent(eventId);
      setEvents(events.filter(event => event.id !== eventId));
    } catch (error) {
      console.error('Failed to delete event:', error);
    }
  };

  const updateEvent = async (eventId, updates) => {
    try {
      const response = await calendarAPI.updateEvent(eventId, updates);
      setEvents(events.map(event => 
        event.id === eventId ? response.data : event
      ));
      setEditingEvent(null);
      setShowModal(false);
    } catch (error) {
      console.error('Failed to update event:', error);
    }
  };

  const getEventsForDate = (date) => {
    const dateString = date.toISOString().split('T')[0];
    return events.filter(event => event.date === dateString);
  };

  const getEventIcon = (type) => {
    switch(type) {
      case 'interview': return Briefcase;
      case 'networking': return Users;
      case 'preparation': return CalendarIcon;
      default: return CalendarIcon;
    }
  };

  const getEventColor = (type, status) => {
    if (status === 'completed') return 'bg-green-600/20 text-green-400';
    if (status === 'cancelled') return 'bg-red-600/20 text-red-400';
    
    switch(type) {
      case 'interview': return 'bg-blue-600/20 text-blue-400';
      case 'networking': return 'bg-purple-600/20 text-purple-400';
      case 'preparation': return 'bg-amber-600/20 text-amber-400';
      default: return 'bg-slate-600/20 text-slate-400';
    }
  };

  const CalendarHeader = () => {
    const monthNames = [
      'January', 'February', 'March', 'April', 'May', 'June',
      'July', 'August', 'September', 'October', 'November', 'December'
    ];

    const prevMonth = () => {
      setSelectedDate(new Date(selectedDate.getFullYear(), selectedDate.getMonth() - 1, 1));
    };

    const nextMonth = () => {
      setSelectedDate(new Date(selectedDate.getFullYear(), selectedDate.getMonth() + 1, 1));
    };

    return (
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <button onClick={prevMonth} className="p-2 hover:bg-white/10 rounded-lg transition-colors">
            <ChevronLeft size={20} />
          </button>
          <h2 className="text-2xl font-bold text-white">
            {monthNames[selectedDate.getMonth()]} {selectedDate.getFullYear()}
          </h2>
          <button onClick={nextMonth} className="p-2 hover:bg-white/10 rounded-lg transition-colors">
            <ChevronRight size={20} />
          </button>
        </div>
        
        <div className="flex gap-2">
          {['month', 'week', 'day'].map(mode => (
            <button
              key={mode}
              onClick={() => setViewMode(mode)}
              className={`px-4 py-2 rounded-lg font-semibold capitalize ${
                viewMode === mode 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              } transition-all`}
            >
              {mode}
            </button>
          ))}
        </div>
      </div>
    );
  };

  const MonthView = () => {
    const daysInMonth = new Date(selectedDate.getFullYear(), selectedDate.getMonth() + 1, 0).getDate();
    const firstDayOfMonth = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), 1).getDay();
    
    const days = [];
    const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

    // Add day names
    for (let i = 0; i < 7; i++) {
      days.push(
        <div key={`day-name-${i}`} className="text-center text-slate-500 font-semibold text-sm py-2">
          {dayNames[i]}
        </div>
      );
    }

    // Add empty cells for days before the first day of the month
    for (let i = 0; i < firstDayOfMonth; i++) {
      days.push(<div key={`empty-${i}`} className="h-20"></div>);
    }

    // Add days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      const currentDate = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), day);
      const dayEvents = getEventsForDate(currentDate);
      const isToday = currentDate.toDateString() === new Date().toDateString();
      const isSelected = currentDate.toDateString() === selectedDate.toDateString();

      days.push(
        <motion.div
          key={day}
          whileHover={{ scale: 1.02 }}
          className={`h-20 border border-white/10 p-2 rounded-lg cursor-pointer ${
            isToday ? 'bg-blue-600/10 border-blue-500/30' : 'hover:bg-white/5'
          } ${isSelected ? 'ring-2 ring-blue-500' : ''}`}
          onClick={() => setSelectedDate(currentDate)}
        >
          <div className="flex items-center justify-between mb-1">
            <span className={`text-sm font-semibold ${isToday ? 'text-blue-400' : 'text-white'}`}>
              {day}
            </span>
            {dayEvents.length > 0 && (
              <span className="text-xs text-slate-400">{dayEvents.length}</span>
            )}
          </div>
          <div className="space-y-1">
            {dayEvents.slice(0, 2).map(event => (
              <div
                key={event.id}
                className={`text-xs p-1 rounded ${getEventColor(event.type, event.status)} truncate`}
              >
                {event.title}
              </div>
            ))}
            {dayEvents.length > 2 && (
              <div className="text-xs text-slate-400 text-center">+{dayEvents.length - 2}</div>
            )}
          </div>
        </motion.div>
      );
    }

    return (
      <div className="grid grid-cols-7 gap-2">
        {days}
      </div>
    );
  };

  const EventCard = ({ event, onDelete, onEdit }) => {
    const EventIcon = getEventIcon(event.type);
    
    return (
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        className="p-4 bg-slate-800/50 rounded-xl border border-white/10 hover:border-white/30 transition-all cursor-pointer group"
      >
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${getEventColor(event.type, event.status)}`}>
              <EventIcon size={16} />
            </div>
            <div>
              <h4 className="font-semibold text-white group-hover:text-blue-400 transition-colors">
                {event.title}
              </h4>
              {event.company && (
                <p className="text-sm text-slate-400">{event.company}</p>
              )}
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={() => onEdit(event)} className="p-2 text-slate-400 hover:text-white transition-colors">
              <Edit size={16} />
            </button>
            <button onClick={() => onDelete(event.id)} className="p-2 text-slate-400 hover:text-red-400 transition-colors">
              <Trash2 size={16} />
            </button>
          </div>
        </div>
        
        <p className="text-sm text-slate-400 mb-3">{event.description}</p>
        
        <div className="flex items-center justify-between text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <Clock size={12} />
            <span>{event.time}</span>
          </div>
          <div className="flex items-center gap-2">
            <MapPin size={12} />
            <span>{event.platform}</span>
          </div>
        </div>
        
        {event.status && (
          <div className="mt-3 flex items-center gap-2 text-xs">
            <div className={`w-2 h-2 rounded-full ${
              event.status === 'completed' ? 'bg-green-400' :
              event.status === 'cancelled' ? 'bg-red-400' : 'bg-amber-400'
            }`}></div>
            <span className="capitalize text-slate-400">{event.status}</span>
          </div>
        )}
      </motion.div>
    );
  };

  const EventModal = ({ event, onSave, onClose, onUpdate }) => {
    const [formData, setFormData] = useState({
      title: event?.title || '',
      description: event?.description || '',
      date: event?.date || '',
      time: event?.time || '',
      platform: event?.platform || 'Google Meet',
      type: event?.type || 'interview',
      status: event?.status || 'scheduled'
    });

    const handleSubmit = (e) => {
      e.preventDefault();
      if (event) {
        onUpdate(event.id, formData);
      } else {
        onSave(formData);
      }
    };

    return (
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="card-glass p-6 w-full max-w-md rounded-2xl border-white/10"
        >
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-bold text-white">
              {event ? 'Edit Event' : 'Add New Event'}
            </h3>
            <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
              <XCircle size={24} />
            </button>
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs font-bold text-slate-500 uppercase mb-2 block">Title</label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({...formData, title: e.target.value})}
                className="w-full bg-slate-900/60 border border-white/10 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-blue-500/30"
                required
              />
            </div>
            
            <div>
              <label className="text-xs font-bold text-slate-500 uppercase mb-2 block">Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                className="w-full bg-slate-900/60 border border-white/10 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-blue-500/30"
                rows={3}
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-bold text-slate-500 uppercase mb-2 block">Date</label>
                <input
                  type="date"
                  value={formData.date}
                  onChange={(e) => setFormData({...formData, date: e.target.value})}
                  className="w-full bg-slate-900/60 border border-white/10 rounded-lg px-3 py-2 text-white"
                  required
                />
              </div>
              <div>
                <label className="text-xs font-bold text-slate-500 uppercase mb-2 block">Time</label>
                <input
                  type="time"
                  value={formData.time}
                  onChange={(e) => setFormData({...formData, time: e.target.value})}
                  className="w-full bg-slate-900/60 border border-white/10 rounded-lg px-3 py-2 text-white"
                  required
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-bold text-slate-500 uppercase mb-2 block">Platform</label>
                <select
                  value={formData.platform}
                  onChange={(e) => setFormData({...formData, platform: e.target.value})}
                  className="w-full bg-slate-900/60 border border-white/10 rounded-lg px-3 py-2 text-white"
                >
                  <option value="Google Meet">Google Meet</option>
                  <option value="Zoom">Zoom</option>
                  <option value="Teams">Microsoft Teams</option>
                  <option value="In Person">In Person</option>
                </select>
              </div>
              <div>
                <label className="text-xs font-bold text-slate-500 uppercase mb-2 block">Type</label>
                <select
                  value={formData.type}
                  onChange={(e) => setFormData({...formData, type: e.target.value})}
                  className="w-full bg-slate-900/60 border border-white/10 rounded-lg px-3 py-2 text-white"
                >
                  <option value="interview">Interview</option>
                  <option value="networking">Networking</option>
                  <option value="preparation">Preparation</option>
                </select>
              </div>
            </div>
            
            <div className="flex gap-3 pt-4">
              <button type="submit" className="flex-1 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-500 transition-all font-bold">
                {event ? 'Update Event' : 'Add Event'}
              </button>
              <button type="button" onClick={onClose} className="flex-1 py-3 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-all font-bold">
                Cancel
              </button>
            </div>
          </form>
        </motion.div>
      </div>
    );
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Interview Calendar</h1>
          <p className="text-slate-400 mt-1">Manage your interview schedule and career events</p>
        </div>
        <div className="flex gap-3">
          <button className="flex items-center gap-2 px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-all">
            <Download size={18} />
            Export Calendar
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-500 transition-all">
            <Share2 size={18} />
            Share Schedule
          </button>
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-500 transition-all shadow-lg shadow-blue-500/20"
          >
            <Plus size={20} />
            Add Event
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Calendar View */}
        <div className="lg:col-span-2 card-glass p-6 border-white/5">
          <CalendarHeader />
          <MonthView />
        </div>

        {/* Event Details */}
        <div className="card-glass p-6 border-white/5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-white">
              Events for {selectedDate.toLocaleDateString()}
            </h3>
            <div className="text-sm text-slate-400">
              {getEventsForDate(selectedDate).length} event(s)
            </div>
          </div>
          
          <div className="space-y-4">
            {getEventsForDate(selectedDate).map(event => (
              <EventCard 
                key={event.id}
                event={event}
                onDelete={deleteEvent}
                onEdit={setEditingEvent}
              />
            ))}
            
            {getEventsForDate(selectedDate).length === 0 && (
              <div className="text-center py-8 text-slate-500">
                <Calendar size={48} className="mx-auto mb-4 opacity-50" />
                <p>No events scheduled for this date</p>
                <button
                  onClick={() => setShowModal(true)}
                  className="mt-4 text-blue-400 hover:text-blue-300 font-bold"
                >
                  Add an event
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Upcoming Events */}
      <div className="card-glass p-6 border-white/5">
        <h3 className="text-lg font-bold text-white mb-6">Upcoming Events</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {events
            .filter(event => new Date(event.date) >= new Date())
            .sort((a, b) => new Date(a.date) - new Date(b.date))
            .slice(0, 6)
            .map(event => (
              <EventCard 
                key={event.id}
                event={event}
                onDelete={deleteEvent}
                onEdit={setEditingEvent}
              />
            ))}
        </div>
      </div>

      {showModal && (
        <EventModal 
          event={editingEvent}
          onSave={addEvent}
          onUpdate={updateEvent}
          onClose={() => {
            setShowModal(false);
            setEditingEvent(null);
          }}
        />
      )}
    </div>
  );
};

export default CalendarView;