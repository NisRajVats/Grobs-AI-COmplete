import React, { useState, useEffect } from 'react';
import { NavLink, Link } from 'react-router-dom';
import { Zap, Menu, X, ChevronRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const PublicLayout = ({ children }) => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="min-h-screen text-slate-200 selection:bg-blue-500/30">
      {/* Navbar */}
      <nav className={`fixed top-0 w-full z-[100] transition-all duration-300 ${isScrolled ? 'py-4 glass-dark shadow-2xl backdrop-blur-3xl' : 'py-6 bg-transparent'}`}>
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/30">
              <Zap className="text-white fill-white" size={24} />
            </div>
            <span className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-blue-400">
              GROBS.AI
            </span>
          </Link>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-10">
            {['Features', 'Pricing', 'About', 'Contact'].map((item) => (
              <NavLink 
                key={item} 
                to={`/${item.toLowerCase()}`} 
                className={({ isActive }) => `text-sm font-medium transition-colors hover:text-blue-400 ${isActive ? 'text-blue-400' : 'text-slate-400'}`}
              >
                {item}
              </NavLink>
            ))}
          </div>

          <div className="hidden md:flex items-center gap-4">
            <Link to="/login" className="px-6 py-2.5 text-sm font-semibold text-white hover:text-blue-400 transition-colors">
              Log in
            </Link>
            <Link to="/register" className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-sm font-bold rounded-xl shadow-lg shadow-blue-500/20 transition-all active:scale-[0.98]">
              Get Started
            </Link>
          </div>

          {/* Mobile Toggle */}
          <button className="md:hidden text-white" onClick={() => setIsMenuOpen(!isMenuOpen)}>
            {isMenuOpen ? <X size={28} /> : <Menu size={28} />}
          </button>
        </div>

        {/* Mobile Menu */}
        <AnimatePresence>
          {isMenuOpen && (
            <motion.div 
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="md:hidden glass-dark border-b border-white/10 overflow-hidden"
            >
              <div className="px-6 py-8 flex flex-col gap-6">
                {['Features', 'Pricing', 'About', 'Contact'].map((item) => (
                  <Link key={item} to={`/${item.toLowerCase()}`} className="text-lg font-medium text-slate-300" onClick={() => setIsMenuOpen(false)}>
                    {item}
                  </Link>
                ))}
                <hr className="border-white/5" />
                <Link to="/login" className="text-lg font-medium text-white" onClick={() => setIsMenuOpen(false)}>Login</Link>
                <Link to="/register" className="py-4 bg-blue-600 text-white text-center font-bold rounded-2xl" onClick={() => setIsMenuOpen(false)}>Get Started</Link>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </nav>

      {/* Content */}
      <main className="relative z-10 pt-20">
        {children}
      </main>

      {/* Footer */}
      <footer className="relative z-10 bg-slate-900/40 border-t border-white/5 pt-20 pb-10">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-4 gap-12 mb-20">
          <div className="col-span-1 md:col-span-1 space-y-6">
            <Link to="/" className="flex items-center gap-3">
              <Zap className="text-blue-500 fill-blue-500" size={32} />
              <span className="text-2xl font-bold text-white">GROBS.AI</span>
            </Link>
            <p className="text-slate-400 leading-relaxed">
              Empowering your career with next-generation AI tools. Optimize your resume, discover hidden jobs, and ace every interview.
            </p>
          </div>
          
          <div>
            <h4 className="text-white font-bold mb-6">Product</h4>
            <ul className="space-y-4 text-slate-400 text-sm">
              <li><Link to="/features" className="hover:text-blue-400 transition-colors">AI Resume Builder</Link></li>
              <li><Link to="/features" className="hover:text-blue-400 transition-colors">ATS Checker</Link></li>
              <li><Link to="/features" className="hover:text-blue-400 transition-colors">Interview Prep</Link></li>
              <li><Link to="/features" className="hover:text-blue-400 transition-colors">Job Search</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="text-white font-bold mb-6">Company</h4>
            <ul className="space-y-4 text-slate-400 text-sm">
              <li><Link to="/about" className="hover:text-blue-400 transition-colors">About Us</Link></li>
              <li><Link to="/blog" className="hover:text-blue-400 transition-colors">Career Blog</Link></li>
              <li><Link to="/privacy" className="hover:text-blue-400 transition-colors">Privacy Policy</Link></li>
              <li><Link to="/terms" className="hover:text-blue-400 transition-colors">Terms of Service</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="text-white font-bold mb-6">Newsletter</h4>
            <p className="text-sm text-slate-400 mb-4">Get career tips and updates directly in your inbox.</p>
            <div className="relative">
              <input 
                type="email" 
                placeholder="Enter email" 
                className="w-full bg-slate-800/50 border border-white/10 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/30 transition-all"
              />
              <button className="absolute right-1.5 top-1.5 p-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-500 transition-colors">
                <ChevronRight size={18} />
              </button>
            </div>
          </div>
        </div>
        <div className="max-w-7xl mx-auto px-6 pt-10 border-t border-white/5 text-center text-slate-500 text-sm">
          © 2026 GROBS.AI. All rights reserved. Built with ❤️ for your career.
        </div>
      </footer>
    </div>
  );
};

export default PublicLayout;
