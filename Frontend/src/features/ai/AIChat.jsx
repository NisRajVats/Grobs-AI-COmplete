import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, Send, User, Sparkles, Zap, Brain, Target, TrendingUp, X, Plus, Bot, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../../services/api';

const AIChat = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'assistant',
      text: "Hi! I'm your AI career assistant. I can help you with resume tips, interview prep, job search strategy, and career growth advice. What would you like to explore?",
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isTyping) return;
    const userText = input.trim();
    const userMsg = { id: Date.now(), role: 'user', text: userText, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    try {
      // Build conversation history for context
      const history = messages.slice(-6).map(m => ({
        role: m.role === 'assistant' ? 'assistant' : 'user',
        content: m.text
      }));
      history.push({ role: 'user', content: userText });

      const res = await api.post('/api/interview/ai-chat', { messages: history, context: 'career_assistant' });
      const reply = res.data?.reply || res.data?.message || "I'd be happy to help with that! Could you provide more details?";
      setMessages(prev => [...prev, { id: Date.now() + 1, role: 'assistant', text: reply, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }]);
    } catch {
      // Graceful fallback using client-side AI hints
      const fallbackReplies = {
        resume: "For a strong resume: use action verbs, quantify achievements (e.g. 'increased revenue by 30%'), tailor it to each job description, and keep it to 1-2 pages. Want me to review specific sections?",
        interview: "Great interview prep involves: researching the company, preparing STAR-format answers for behavioral questions, and practicing technical skills. Which type of interview are you preparing for?",
        salary: "Salary negotiation tips: research market rates on Glassdoor/Levels.fyi, anchor high with data to back it up, consider the full package (equity, benefits), and never give the first number if possible.",
        default: "That's a great career question! I recommend focusing on your unique value proposition, continuous skill development, and building a strong professional network. What specific aspect would you like to dig into?"
      };
      const lower = userText.toLowerCase();
      const reply = lower.includes('resume') ? fallbackReplies.resume
                  : lower.includes('interview') ? fallbackReplies.interview
                  : lower.includes('salary') || lower.includes('negotiat') ? fallbackReplies.salary
                  : fallbackReplies.default;
      setMessages(prev => [...prev, { id: Date.now() + 1, role: 'assistant', text: reply, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }]);
    } finally { setIsTyping(false); }
  };

  const suggestions = [
    { label: 'Analyze my skill gaps', icon: Brain },
    { label: 'Resume optimization tips', icon: Sparkles },
    { label: 'Interview prep strategies', icon: Target },
    { label: 'Salary negotiation advice', icon: TrendingUp },
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] max-w-4xl mx-auto space-y-0">
      {/* Header */}
      <div className="card-glass p-6 rounded-t-2xl rounded-b-none border-b border-white/5">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-linear-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Bot size={24} className="text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">AI Career Assistant</h1>
            <p className="text-slate-400 text-sm flex items-center gap-2">
              <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" /> Online · Powered by AI
            </p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4 card-glass rounded-none border-b border-white/5">
        {messages.length === 1 && (
          <div className="space-y-3">
            <p className="text-slate-500 text-sm text-center">Quick suggestions:</p>
            <div className="grid grid-cols-2 gap-3">
              {suggestions.map((s, i) => (
                <button key={i} onClick={() => { setInput(s.label); }} className="flex items-center gap-3 p-3 bg-white/5 border border-white/10 rounded-xl text-left hover:bg-white/10 transition-all group">
                  <s.icon size={18} className="text-blue-400 shrink-0 group-hover:scale-110 transition-transform" />
                  <span className="text-slate-300 text-sm">{s.label}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        <AnimatePresence initial={false}>
          {messages.map(msg => (
            <motion.div key={msg.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
              <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${msg.role === 'user' ? 'bg-blue-600' : 'bg-purple-600'}`}>
                {msg.role === 'user' ? <User size={16} className="text-white" /> : <Bot size={16} className="text-white" />}
              </div>
              <div className={`max-w-[75%] p-4 rounded-2xl ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-tr-none' : 'bg-slate-800/60 text-slate-200 rounded-tl-none'}`}>
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.text}</p>
                <p className="text-xs mt-1 opacity-50">{msg.time}</p>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {isTyping && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-xl bg-purple-600 flex items-center justify-center shrink-0"><Bot size={16} className="text-white" /></div>
            <div className="p-4 bg-slate-800/60 rounded-2xl rounded-tl-none">
              <div className="flex gap-1">
                {[0, 1, 2].map(i => <div key={i} className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />)}
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="card-glass p-4 rounded-t-none rounded-b-2xl">
        <div className="flex gap-3 items-end">
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }}}
            placeholder="Ask about your career, resume, interviews..."
            rows={1}
            className="flex-1 bg-slate-900/60 border border-white/10 rounded-xl px-4 py-3 text-white text-sm resize-none focus:ring-2 focus:ring-blue-500/30 min-h-[48px] max-h-[120px]"
            style={{ height: 'auto' }}
            onInput={e => { e.target.style.height = 'auto'; e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'; }}
          />
          <button onClick={handleSend} disabled={!input.trim() || isTyping} className="p-3 bg-blue-600 text-white rounded-xl hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-blue-500/20 shrink-0">
            {isTyping ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} />}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AIChat;
