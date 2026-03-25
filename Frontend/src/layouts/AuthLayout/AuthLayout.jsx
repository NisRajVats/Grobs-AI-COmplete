import React from 'react';
import { Zap, ShieldCheck, Target, Sparkles, ChevronLeft } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';

const AuthLayout = ({ children, title, subtitle }) => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex text-slate-200 overflow-hidden">
      {/* Background Orbs */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        <div className="absolute top-0 left-0 w-[1000px] h-[1000px] bg-blue-600/10 blur-[200px] -translate-x-1/2 -translate-y-1/2"></div>
        <div className="absolute bottom-0 right-0 w-[800px] h-[800px] bg-purple-600/10 blur-[150px] translate-x-1/2 translate-y-1/2"></div>
      </div>

      {/* Left Column: Brand & Messaging (Hidden on mobile) */}
      <motion.div 
        initial={{ opacity: 0, x: -50 }}
        animate={{ opacity: 1, x: 0 }}
        className="hidden lg:flex w-[45%] p-16 flex-col justify-between relative z-10 border-r border-white/5 bg-slate-900/40 backdrop-blur-3xl"
      >
        <Link to="/" className="flex items-center gap-4 group">
          <div className="w-12 h-12 bg-blue-600 rounded-2xl flex items-center justify-center shadow-xl shadow-blue-500/20 group-hover:scale-110 transition-transform">
            <Zap className="text-white fill-white" size={28} />
          </div>
          <span className="text-3xl font-extrabold text-white tracking-tight">GROBS.AI</span>
        </Link>

        <div className="space-y-12">
          <div className="space-y-6">
            <h1 className="text-6xl font-black text-white leading-[1.1]">
              Elevate Your <br />
              <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-500 italic">Career Potential</span>
            </h1>
            <p className="text-xl text-slate-400 leading-relaxed max-w-lg">
              Unlock the power of AI to build high-performance resumes, analyze job markets, and master your career journey.
            </p>
          </div>

          <div className="space-y-6">
            {[
              { icon: ShieldCheck, text: 'ATS-Proof Resume Optimization', color: 'text-blue-400' },
              { icon: Target, text: 'Smart Career Path Predictions', color: 'text-indigo-400' },
              { icon: Sparkles, text: 'AI-Generated Professional Content', color: 'text-purple-400' },
            ].map((item, idx) => (
              <motion.div 
                key={idx}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 + idx * 0.1 }}
                className="flex items-center gap-4 group cursor-default"
              >
                <div className={`p-3 bg-white/5 rounded-xl border border-white/10 ${item.color} group-hover:bg-blue-600/10 transition-colors`}>
                  <item.icon size={22} />
                </div>
                <span className="text-lg font-semibold text-slate-200 group-hover:text-white transition-colors">{item.text}</span>
              </motion.div>
            ))}
          </div>
        </div>

        <div className="text-slate-500 text-sm">
          © 2026 GROBS.AI — Precision Career Engineering
        </div>
      </motion.div>

      {/* Right Column: Form */}
      <div className="flex-1 flex flex-col p-8 md:p-16 lg:p-24 overflow-y-auto relative z-10">
        <div className="max-w-md w-full mx-auto flex-1 flex flex-col justify-center">
          <div className="mb-12 space-y-4">
            <button 
              onClick={() => navigate(-1)}
              className="flex items-center gap-2 text-slate-500 hover:text-white transition-colors mb-8 group"
            >
              <ChevronLeft size={18} className="group-hover:-translate-x-1 transition-transform" />
              <span>Back</span>
            </button>
            <h2 className="text-4xl font-bold text-white tracking-tight">{title}</h2>
            <p className="text-lg text-slate-400">{subtitle}</p>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="card-glass p-8 md:p-10 border border-white/10 shadow-[0_32px_64px_-12px_rgba(0,0,0,0.5)]"
          >
            {children}
          </motion.div>

          <div className="mt-12 text-center text-slate-500 text-sm">
            By continuing, you agree to our <Link to="/terms" className="text-blue-400 hover:underline">Terms of Service</Link> and <Link to="/privacy" className="text-blue-400 hover:underline">Privacy Policy</Link>.
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthLayout;
