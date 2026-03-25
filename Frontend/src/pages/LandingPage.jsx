import React from 'react';
import { motion } from 'framer-motion';
import { 
  Zap, 
  ShieldCheck, 
  Target, 
  Sparkles, 
  ChevronRight, 
  Rocket, 
  Star, 
  Award, 
  ArrowRight,
  MousePointerClick,
  CheckCircle2
} from 'lucide-react';
import { Link } from 'react-router-dom';
import PublicLayout from '../layouts/PublicLayout/PublicLayout';

const LandingPage = () => {
  return (
    <PublicLayout>
      <div className="relative overflow-hidden">
        {/* Background Gradients */}
        <div className="fixed inset-0 pointer-events-none -z-10">
          <div className="absolute top-0 right-0 w-[800px] h-[800px] bg-blue-600/10 blur-[150px] -translate-y-1/2 translate-x-1/2"></div>
          <div className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-indigo-600/10 blur-[120px] translate-y-1/2 -translate-x-1/2"></div>
          <div className="absolute top-1/2 left-1/2 w-[800px] h-[800px] bg-purple-600/5 blur-[180px] -translate-x-1/2 -translate-y-1/2"></div>
        </div>

        {/* Hero Section */}
        <section className="relative pt-20 pb-32 md:pt-32 md:pb-48 px-6 overflow-hidden">
          <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <motion.div 
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              className="space-y-8 text-center lg:text-left"
            >
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500/10 border border-blue-500/20 rounded-full text-blue-400 text-sm font-bold shadow-lg shadow-blue-500/5">
                <Sparkles size={16} />
                <span>AI-Powered Career Evolution</span>
              </div>
              
              <h1 className="text-6xl md:text-8xl font-black text-white leading-[1.05] tracking-tight">
                Unlock Your <br />
                <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-500 italic">True Potential</span>
              </h1>
              
              <p className="text-xl md:text-2xl text-slate-400 leading-relaxed max-w-xl mx-auto lg:mx-0">
                GROBS.AI uses next-generation artificial intelligence to optimize your career journey from resume creation to salary negotiation.
              </p>

              <div className="flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-6 pt-4">
                <Link to="/register" className="group px-8 py-5 bg-blue-600 hover:bg-blue-500 text-white font-black text-lg rounded-2xl shadow-2xl shadow-blue-500/30 transition-all hover:scale-105 active:scale-[0.98] flex items-center gap-3">
                  Start Building Free <ChevronRight size={22} className="group-hover:translate-x-1 transition-transform" />
                </Link>
                <div className="flex items-center gap-3 text-slate-400 font-medium">
                  <div className="flex -space-x-3">
                    {[1, 2, 3].map((i) => (
                      <img 
                        key={i}
                        src={`https://i.pravatar.cc/40?img=${i+10}`} 
                        className="w-10 h-10 rounded-full border-2 border-slate-900 shadow-xl"
                        alt="User"
                      />
                    ))}
                  </div>
                  <span>Joined by 10k+ users</span>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-8 pt-12 border-t border-white/5 opacity-60">
                <div>
                  <h4 className="text-3xl font-black text-white">98%</h4>
                  <p className="text-sm text-slate-500">ATS Success</p>
                </div>
                <div>
                  <h4 className="text-3xl font-black text-white">2.5x</h4>
                  <p className="text-sm text-slate-500">More Interviews</p>
                </div>
                <div>
                  <h4 className="text-3xl font-black text-white">AI</h4>
                  <p className="text-sm text-slate-500">First Platform</p>
                </div>
              </div>
            </motion.div>

            <motion.div 
              initial={{ opacity: 0, scale: 0.8, rotate: 5 }}
              animate={{ opacity: 1, scale: 1, rotate: 0 }}
              className="relative hidden lg:block"
            >
              <div className="relative z-10 p-10 card-glass border-2 border-white/10 shadow-[0_64px_128px_-24px_rgba(0,0,0,0.6)] rotate-2 group transition-all duration-500 hover:rotate-0 hover:scale-105">
                <img 
                  src="https://images.unsplash.com/photo-1460925895917-afdab827c52f?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80" 
                  alt="Dashboard Preview" 
                  className="rounded-2xl shadow-2xl grayscale group-hover:grayscale-0 transition-all duration-700"
                />
                
                {/* Floating Widgets */}
                <motion.div 
                  animate={{ y: [0, -10, 0] }}
                  transition={{ duration: 3, repeat: Infinity }}
                  className="absolute -top-12 -right-12 p-6 glass-dark border border-white/20 rounded-3xl shadow-2xl flex items-center gap-4"
                >
                  <div className="p-3 bg-green-500/20 text-green-400 rounded-xl">
                    <Target size={24} />
                  </div>
                  <div>
                    <h5 className="text-xs text-slate-400">ATS Score</h5>
                    <p className="text-xl font-black text-white">92%</p>
                  </div>
                </motion.div>

                <motion.div 
                   animate={{ y: [0, 10, 0] }}
                   transition={{ duration: 4, repeat: Infinity }}
                  className="absolute -bottom-8 -left-12 p-6 glass-dark border border-white/20 rounded-3xl shadow-2xl flex items-center gap-4"
                >
                  <div className="p-3 bg-blue-500/20 text-blue-400 rounded-xl">
                    <Zap size={24} />
                  </div>
                  <div>
                    <h5 className="text-xs text-slate-400">AI Resume</h5>
                    <p className="text-xl font-black text-white">Generated</p>
                  </div>
                </motion.div>
              </div>
            </motion.div>
          </div>
        </section>

        {/* Features Grid */}
        <section className="py-32 px-6 relative">
          <div className="max-w-7xl mx-auto space-y-20">
            <div className="text-center space-y-6 max-w-2xl mx-auto">
              <h2 className="text-4xl md:text-5xl font-black text-white">Engineering Your <span className="text-blue-500 italic">Success</span></h2>
              <p className="text-xl text-slate-400 leading-relaxed">
                Everything you need to dominate the job market in the era of AI.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {[
                { 
                  title: 'AI Resume Builder', 
                  desc: 'Craft production-quality resumes that beat every applicant tracking system.', 
                  icon: Rocket, 
                  color: 'blue' 
                },
                { 
                  title: 'ATS Checker', 
                  desc: 'Deep-scan your resume against job descriptions for maximum match rate.', 
                  icon: ShieldCheck, 
                  color: 'indigo' 
                },
                { 
                  title: 'Smart Job Search', 
                  desc: 'Our AI finds jobs that match your skills and salary expectations perfectly.', 
                  icon: MousePointerClick, 
                  color: 'purple' 
                },
                { 
                  title: 'Interview Preparation', 
                  desc: 'Practice with AI avatars tailored to your target company and role.', 
                  icon: Award, 
                  color: 'rose' 
                },
                { 
                  title: 'Career Insights', 
                  desc: 'Receive data-driven predictions on your career path and skill gaps.', 
                  icon: Target, 
                  color: 'amber' 
                },
                { 
                  title: 'AI Career Chat', 
                  desc: 'Your 24/7 personal career coach powered by advanced LLMs.', 
                  icon: Sparkles, 
                  color: 'teal' 
                },
              ].map((feature, idx) => (
                <motion.div 
                  key={idx}
                  whileHover={{ y: -10 }}
                  className="card-glass p-10 space-y-6 group cursor-default"
                >
                  <div className={`w-16 h-16 bg-white/5 rounded-2xl flex items-center justify-center border border-white/10 group-hover:scale-110 group-hover:bg-blue-600/10 transition-all duration-300`}>
                    <feature.icon className={`text-slate-400 group-hover:text-blue-400 transition-colors`} size={32} />
                  </div>
                  <h3 className="text-2xl font-bold text-white group-hover:text-blue-400 transition-colors">{feature.title}</h3>
                  <p className="text-slate-400 leading-relaxed">{feature.desc}</p>
                  <Link to="/register" className="flex items-center gap-2 text-sm font-bold text-white opacity-0 group-hover:opacity-100 translate-y-2 group-hover:translate-y-0 transition-all">
                    Learn more <ArrowRight size={16} />
                  </Link>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* Social Proof */}
        <section className="py-24 border-y border-white/5 bg-slate-900/40">
           <div className="max-w-7xl mx-auto px-6 text-center">
              <p className="text-sm font-bold text-slate-500 uppercase tracking-widest mb-12">Trusted by talent at world-class companies</p>
              <div className="flex flex-wrap items-center justify-center gap-12 md:gap-24 grayscale opacity-40">
                  <h3 className="text-2xl font-black text-white">GOOGLE</h3>
                  <h3 className="text-2xl font-black text-white">MICROSOFT</h3>
                  <h3 className="text-2xl font-black text-white">AMAZON</h3>
                  <h3 className="text-2xl font-black text-white">TESLA</h3>
                  <h3 className="text-2xl font-black text-white">META</h3>
              </div>
           </div>
        </section>

        {/* Pricing Teaser */}
        <section className="py-32 px-6 relative">
          <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">
             <div className="space-y-8">
                <h2 className="text-4xl md:text-6xl font-black text-white leading-tight">Elite Tools for <span className="text-blue-500 italic">Elite Careers</span></h2>
                <p className="text-xl text-slate-400 leading-relaxed">
                  Start for free, upgrade when you are ready to dominate. Our plans are built to scale with your career growth.
                </p>
                <div className="space-y-4 pt-4">
                  {['AI-Generated Resumes', 'Full ATS Optimization', 'Interview Simulation', 'Career Roadmap Prediction'].map((feat) => (
                    <div key={feat} className="flex items-center gap-3">
                      <CheckCircle2 className="text-blue-500" size={20} />
                      <span className="text-slate-300 font-medium">{feat}</span>
                    </div>
                  ))}
                </div>
                <div className="pt-6">
                   <Link to="/pricing" className="text-lg font-bold text-white border-b-2 border-blue-600 pb-1 hover:text-blue-400 transition-colors">See all plans & pricing</Link>
                </div>
             </div>

             <div className="card-glass p-10 md:p-16 border-2 border-blue-500/20 shadow-2xl relative overflow-hidden group">
                <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/20 blur-3xl -z-10"></div>
                <div className="space-y-8 text-center">
                   <div>
                      <h4 className="text-sm font-bold text-blue-400 uppercase tracking-wider mb-2">Most Popular</h4>
                      <h3 className="text-4xl font-black text-white">Professional</h3>
                      <div className="flex items-center justify-center gap-1 mt-4">
                        <span className="text-2xl text-slate-500 font-medium">$</span>
                        <span className="text-6xl font-black text-white">19</span>
                        <span className="text-slate-500 font-medium">/mo</span>
                      </div>
                   </div>
                   <p className="text-slate-400">Perfect for active job seekers looking for a competitive edge.</p>
                   <Link to="/register" className="block w-full py-5 bg-white text-slate-900 font-black text-lg rounded-2xl hover:bg-blue-500 hover:text-white transition-all shadow-xl">Get Started Now</Link>
                   <p className="text-xs text-slate-500">7-day free trial. No credit card required.</p>
                </div>
             </div>
          </div>
        </section>

        {/* Final CTA */}
        <section className="py-32 px-6 text-center relative overflow-hidden">
          <div className="max-w-4xl mx-auto space-y-12">
            <h2 className="text-5xl md:text-7xl font-black text-white tracking-tight">Your Dream Career <br /> Starts <span className="italic text-indigo-500 underline decoration-indigo-500/30">Right Here</span></h2>
            <p className="text-xl md:text-2xl text-slate-400 max-w-2xl mx-auto leading-relaxed">
              Stop guessing. Start knowing. Join the thousands of professionals using GROBS.AI to land their ideal roles.
            </p>
            <div className="pt-8">
               <Link to="/register" className="inline-flex items-center gap-3 px-10 py-6 bg-blue-600 hover:bg-blue-500 text-white font-black text-xl rounded-3xl shadow-[0_32px_64px_-16px_rgba(59,130,246,0.6)] transition-all hover:scale-105 active:scale-[0.98]">
                 Create Your Free Account <ArrowRight size={24} />
               </Link>
            </div>
          </div>
        </section>
      </div>
    </PublicLayout>
  );
};

export default LandingPage;
