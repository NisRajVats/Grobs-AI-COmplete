import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, ChevronRight, MessageSquare, Lightbulb, CheckCircle2, Sparkles, RefreshCw, BookOpen, Target } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../../services/api';

const defaultQuestions = {
  behavioral: [
    { id: 1, question: "Tell me about yourself", answer: "Start with your current role, highlight key achievements, and connect to the position." },
    { id: 2, question: "Describe a challenging project", answer: "Use the STAR method: Situation, Task, Action, Result." },
    { id: 3, question: "Tell me about a time you failed", answer: "Be honest, show what you learned, and how you improved." },
    { id: 4, question: "Why do you want to work here?", answer: "Research the company and align your goals with their mission." },
  ],
  technical: [
    { id: 5, question: "Explain [technology] in simple terms", answer: "Start with the basics and build up to complex concepts." },
    { id: 6, question: "How would you design [system]?", answer: "Consider scalability, maintainability, and user experience." },
    { id: 7, question: "What is your approach to debugging?", answer: "Describe your systematic approach to identifying and fixing issues." },
  ],
  situational: [
    { id: 8, question: "How would you handle a difficult teammate?", answer: "Focus on communication, empathy, and finding common ground." },
    { id: 9, question: "What would you do if deadlines are unrealistic?", answer: "Discuss prioritization, communication, and negotiation skills." },
  ],
  cultural: [
    { id: 10, question: "What type of work environment do you prefer?", answer: "Be honest but also show adaptability." },
    { id: 11, question: "How do you stay updated with technology?", answer: "Discuss your learning habits and curiosity." },
  ],
};

const PracticeQuestions = () => {
  const navigate = useNavigate();
  const { resumeId } = useParams();
  const [selectedCategory, setSelectedCategory] = useState('behavioral');
  const [selectedQuestion, setSelectedQuestion] = useState(null);
  const [resumes, setResumes] = useState([]);
  const [selectedResumeId, setSelectedResumeId] = useState(resumeId || null);
  const [generatedQuestions, setGeneratedQuestions] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchResumes = useCallback(async () => {
    try {
      const response = await api.get('/api/resumes');
      setResumes(response.data);
      if (response.data.length > 0 && !selectedResumeId) {
        setSelectedResumeId(response.data[0].id);
      }
    } catch (_error) {
      console.error("Error fetching resumes:", _error);
    }
  }, [selectedResumeId]);

  const generateQuestionsFromResume = useCallback(async (resId) => {
    if (!resId) return;
    try {
      setLoading(true);
      const response = await api.post('/api/interview/questions', {
        resume_id: parseInt(resId),
        job_description: ''
      });
      setGeneratedQuestions(response.data);
      // Reset selected question when generating new ones
      setSelectedQuestion(null);
    } catch (_error) {
      console.error("Error generating questions:", _error);
      setGeneratedQuestions(null);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch user's resumes
  useEffect(() => {
    fetchResumes();
  }, [fetchResumes]);

  // Generate questions when resume is selected
  useEffect(() => {
    if (selectedResumeId) {
      generateQuestionsFromResume(selectedResumeId);
    }
  }, [selectedResumeId, generateQuestionsFromResume]);

  const categories = [
    { id: 'behavioral', label: 'Behavioral', count: generatedQuestions?.interview_structure?.behavioral_questions?.length || defaultQuestions.behavioral.length },
    { id: 'technical', label: 'Technical', count: generatedQuestions?.interview_structure?.technical_questions?.length || defaultQuestions.technical.length },
    { id: 'role_specific', label: 'Role-Specific', count: generatedQuestions?.interview_structure?.role_specific_questions?.length || defaultQuestions.situational.length },
    { id: 'job_specific', label: 'Job-Specific', count: generatedQuestions?.interview_structure?.job_specific_questions?.length || defaultQuestions.cultural.length },
  ];

  const getQuestions = () => {
    if (!generatedQuestions) {
      switch (selectedCategory) {
        case 'behavioral': return defaultQuestions.behavioral;
        case 'technical': return defaultQuestions.technical;
        case 'role_specific': return defaultQuestions.situational;
        case 'job_specific': return defaultQuestions.cultural;
        default: return defaultQuestions.behavioral;
      }
    }
    
    const structure = generatedQuestions.interview_structure || {};
    
    switch (selectedCategory) {
      case 'behavioral':
        return structure.behavioral_questions || [];
      case 'technical':
        return structure.technical_questions || [];
      case 'role_specific':
        return structure.role_specific_questions || [];
      case 'job_specific':
        return structure.job_specific_questions || [];
      default:
        return [];
    }
  };

  const questions = getQuestions();

  return (
    <div className="space-y-8 pb-12">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate('/app/interview')} className="p-2.5 bg-white/5 hover:bg-white/10 rounded-xl text-slate-400 hover:text-white border border-white/10 transition-all">
            <ArrowLeft size={20} />
          </button>
          <div>
            <h1 className="text-3xl font-black text-white">Practice Questions</h1>
            <p className="text-slate-400">Master common interview scenarios with AI-guided answers</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1 space-y-6">
          {/* Resume Selection */}
          <div className="card-glass p-6 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-600/20 rounded-lg flex items-center justify-center">
                <Target size={20} className="text-blue-400" />
              </div>
              <h3 className="font-bold text-white text-lg">Personalize Practice</h3>
            </div>
            <p className="text-slate-400 text-sm">Select a resume to generate questions tailored to your experience.</p>
            
            <div className="space-y-3">
              <select
                value={selectedResumeId || ''}
                onChange={(e) => setSelectedResumeId(e.target.value)}
                className="w-full bg-slate-900 border border-white/10 rounded-xl px-4 py-3 text-white focus:ring-2 focus:ring-blue-500/30 transition-all"
              >
                <option value="">Select a resume</option>
                {resumes.map(resume => (
                  <option key={resume.id} value={resume.id}>
                    {resume.title || resume.full_name}
                  </option>
                ))}
              </select>
              <button 
                onClick={() => generateQuestionsFromResume(selectedResumeId)}
                disabled={!selectedResumeId || loading}
                className="w-full py-3 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-500 transition-all flex items-center justify-center gap-2 disabled:opacity-50 shadow-lg shadow-blue-600/20"
              >
                {loading ? <RefreshCw className="animate-spin" size={18} /> : <Sparkles size={18} />}
                Generate Questions
              </button>
            </div>

            {generatedQuestions?.preparation_tips && (
              <div className="mt-6 p-4 bg-green-500/10 border border-green-500/20 rounded-2xl">
                <h4 className="font-bold text-green-400 text-sm mb-3 flex items-center gap-2">
                  <Lightbulb size={16} /> Preparation Tips
                </h4>
                <ul className="space-y-2">
                  {generatedQuestions.preparation_tips.slice(0, 4).map((tip, idx) => (
                    <li key={idx} className="text-slate-300 text-xs flex gap-2">
                      <span className="text-green-500">•</span> {tip}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>

        <div className="lg:col-span-2 space-y-6">
          {/* Category Tabs */}
          <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
            {categories.map(cat => (
              <button
                key={cat.id}
                onClick={() => {
                  setSelectedCategory(cat.id);
                  setSelectedQuestion(null);
                }}
                className={`px-6 py-3 rounded-xl font-bold text-sm whitespace-nowrap transition-all border ${
                  selectedCategory === cat.id 
                    ? 'bg-blue-600 text-white border-blue-500 shadow-lg shadow-blue-600/20' 
                    : 'bg-slate-800 text-slate-400 border-white/5 hover:text-white hover:bg-slate-700'
                }`}
              >
                {cat.label} <span className="ml-2 opacity-60 text-xs">{cat.count}</span>
              </button>
            ))}
          </div>

          {/* Questions List and Detail */}
          <div className="grid grid-cols-1 gap-6">
            <div className="space-y-3">
<AnimatePresence>
                {questions.length > 0 ? (
                  questions.map((q, idx) => (
                    <motion.div
                      key={q.id || idx}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: idx * 0.05 }}
                      onClick={() => setSelectedQuestion(selectedQuestion?.id === q.id ? null : q)}
                      className={`card-glass p-6 cursor-pointer transition-all border group ${
                        selectedQuestion?.id === q.id ? 'border-blue-500/50 bg-blue-500/5' : 'border-white/5 hover:bg-white/5'
                      }`}
                    >
                      <div className="flex justify-between items-start gap-4">
                        <div className="flex-1">
                          <h3 className="font-bold text-white group-hover:text-blue-400 transition-colors">{q.question}</h3>
                          {q.question_type && (
                            <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest mt-2 inline-block px-2 py-0.5 bg-white/5 rounded-md">
                              {q.question_type}
                            </span>
                          )}
                        </div>
                        <div className={`mt-1 transition-transform duration-300 ${selectedQuestion?.id === q.id ? 'rotate-90 text-blue-400' : 'text-slate-600 group-hover:text-slate-400'}`}>
                          <ChevronRight size={20} />
                        </div>
                      </div>

                      {selectedQuestion?.id === q.id && (
                        <motion.div 
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          className="mt-6 pt-6 border-t border-white/10 space-y-4"
                        >
                          <div className="p-5 bg-blue-600/10 border border-blue-500/20 rounded-2xl relative overflow-hidden group/tip">
                            <div className="absolute -top-12 -right-12 w-24 h-24 bg-blue-500/10 rounded-full blur-2xl group-hover/tip:bg-blue-500/20 transition-all"></div>
                            <div className="flex items-center gap-3 mb-3">
                              <Lightbulb size={18} className="text-blue-400" />
                              <span className="font-bold text-blue-400 text-sm">Expert Strategy</span>
                            </div>
                            <p className="text-slate-300 text-sm leading-relaxed relative z-10">
                              {q.answer || q.tips || 'Provide a structured response using specific examples from your past experience. Focus on your actions and the positive outcomes achieved.'}
                            </p>
                          </div>

                          <div className="flex gap-4">
                            <button 
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate('/app/interview/mock', { state: { target_role: generatedQuestions?.role || '', initial_question: q.question } });
                              }}
                              className="flex-1 py-3.5 bg-white text-slate-900 font-bold rounded-xl hover:bg-blue-50 transition-all flex items-center justify-center gap-2 text-sm"
                            >
                              <Sparkles size={16} /> Practice with AI
                            </button>
                            <button 
                              onClick={(e) => e.stopPropagation()}
                              className="px-4 py-3.5 bg-white/5 text-white font-bold rounded-xl hover:bg-white/10 border border-white/10 transition-all"
                            >
                              <CheckCircle2 size={18} />
                            </button>
                          </div>
                        </motion.div>
                      )}
                    </motion.div>
                  ))
                ) : (
                  <div className="text-center py-20 card-glass border-dashed border-white/10">
                    <MessageSquare size={48} className="mx-auto text-slate-700 mb-4" />
                    <h3 className="text-xl font-bold text-white mb-2">No questions found</h3>
                    <p className="text-slate-500 max-w-sm mx-auto">Try selecting a different category or generate personalized questions from your resume.</p>
                  </div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PracticeQuestions;