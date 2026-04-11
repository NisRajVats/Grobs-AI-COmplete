import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Save, User, Mail, Phone, MapPin, Briefcase, Loader2, CheckCircle2 } from 'lucide-react';
import { motion } from 'framer-motion';
import { usersAPI, authAPI } from '../../services/api';
import { useAuth } from '../../context/AuthContext';

const ProfileEdit = () => {
  const navigate = useNavigate();
  const { updateUser } = useAuth();
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    full_name: '', email: '', phone: '', location: '', title: '', linkedin_url: '', avatar_url: '', bio: '', website: '', experience_level: ''
  });

  useEffect(() => {
    const load = async () => {
      try {
        const res = await usersAPI.getProfile();
        const u = res.data;
        setFormData({
          full_name: u.full_name || '',
          email: u.email || '',
          phone: u.phone || '',
          location: u.location || '',
          title: u.title || '',
          linkedin_url: u.linkedin_url || '',
          avatar_url: u.avatar_url || '',
          bio: u.bio || '',
          website: u.website || '',
          experience_level: u.experience_level || ''
        });
      } catch { setError('Failed to load profile.'); }
      finally { setLoading(false); }
    };
    load();
  }, []);

  const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });

  const handleSave = async () => {
    setSaving(true); setError(null);
    try {
      const updatedProfile = {
        full_name: formData.full_name,
        phone: formData.phone,
        location: formData.location,
        title: formData.title,
        linkedin_url: formData.linkedin_url,
        avatar_url: formData.avatar_url,
        bio: formData.bio,
        website: formData.website,
        experience_level: formData.experience_level
      };
      await usersAPI.updateProfile(updatedProfile);
      updateUser(updatedProfile);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch { setError('Failed to save profile.'); }
    finally { setSaving(false); }
  };

  if (loading) return <div className="flex items-center justify-center py-20"><Loader2 className="animate-spin text-blue-400" size={40} /></div>;

  const fields = [
    { label: 'Full Name', name: 'full_name', icon: User, type: 'text', placeholder: 'Your full name' },
    { label: 'Email', name: 'email', icon: Mail, type: 'email', placeholder: 'email@example.com', disabled: true },
    { label: 'Phone', name: 'phone', icon: Phone, type: 'text', placeholder: '+1 234 567 890' },
    { label: 'Location', name: 'location', icon: MapPin, type: 'text', placeholder: 'City, Country' },
    { label: 'Job Title', name: 'title', icon: Briefcase, type: 'text', placeholder: 'e.g. Software Engineer' },
    { label: 'Experience Level', name: 'experience_level', icon: Briefcase, type: 'text', placeholder: 'e.g. Entry, Mid, Senior, Lead' },
    { label: 'LinkedIn URL', name: 'linkedin_url', icon: User, type: 'url', placeholder: 'https://linkedin.com/in/...' },
    { label: 'Website/Portfolio', name: 'website', icon: User, type: 'url', placeholder: 'https://yourwebsite.com' },
    { label: 'Avatar URL', name: 'avatar_url', icon: User, type: 'url', placeholder: 'https://...' },
  ];

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div className="flex items-center gap-4">
        <button onClick={() => navigate('/app/profile')} className="p-2 hover:bg-white/10 rounded-xl text-slate-400 hover:text-white">
          <ArrowRight className="rotate-180" size={20} />
        </button>
        <div>
          <h1 className="text-3xl font-bold text-white">Edit Profile</h1>
          <p className="text-slate-400">Update your personal information</p>
        </div>
      </div>

      {error && <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">{error}</div>}
      {saved && (
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="p-4 bg-green-500/10 border border-green-500/20 rounded-xl text-green-400 text-sm flex items-center gap-2">
          <CheckCircle2 size={18} /> Profile saved successfully!
        </motion.div>
      )}

      <div className="card-glass p-8 space-y-6">
        {fields.map(f => (
          <div key={f.name}>
            <label className="text-xs font-bold text-slate-500 uppercase mb-2 block">{f.label}</label>
            <div className="relative">
              <f.icon className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
              <input
                type={f.type}
                name={f.name}
                value={formData[f.name]}
                onChange={handleChange}
                placeholder={f.placeholder}
                disabled={f.disabled}
                className="w-full bg-slate-900/60 border border-white/10 rounded-xl py-3 pl-12 pr-4 text-white text-sm focus:ring-2 focus:ring-blue-500/30 disabled:opacity-50 disabled:cursor-not-allowed"
              />
            </div>
          </div>
        ))}
        
        {/* Bio/Summary field - textarea */}
        <div>
          <label className="text-xs font-bold text-slate-500 uppercase mb-2 block">Bio / Summary</label>
          <textarea
            name="bio"
            value={formData.bio}
            onChange={handleChange}
            placeholder="Tell us about yourself, your skills, and career goals..."
            rows={4}
            className="w-full bg-slate-900/60 border border-white/10 rounded-xl py-3 px-4 text-white text-sm focus:ring-2 focus:ring-blue-500/30 resize-none"
          />
        </div>
      </div>

      <div className="flex gap-3">
        <button onClick={() => navigate('/app/profile')} className="flex-1 py-4 bg-slate-800 text-slate-300 font-bold rounded-2xl hover:bg-slate-700 transition-all">Cancel</button>
        <button onClick={handleSave} disabled={saving} className="flex-1 py-4 bg-blue-600 text-white font-bold rounded-2xl hover:bg-blue-500 disabled:opacity-50 transition-all flex items-center justify-center gap-2">
          {saving ? <Loader2 size={20} className="animate-spin" /> : <Save size={20} />}
          {saving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </div>
  );
};

export default ProfileEdit;
