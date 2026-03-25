import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import { ArrowRight, Zap, Mic, Video, MessageSquare, Send, RefreshCw, CheckCircle2, XCircle, Play, Pause, Volume2 } from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../../services/api';

const MockInterview = () => {
  const navigate = useNavigate();
  const { sessionId } = useParams();
  const location = useLocation();
  const [session, setSession] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [showSetup, setShowSetup] = useState(!sessionId);
  const [setupData, setSetupData] = useState({
    job_title: location.state?.target_role || '',
    company: '',
    job_description: '',
    question_count: 5,
    interview_type: 'mixed'
  });
  
  const timerRef = useRef(null);
  const [timeElapsed, setTimeElapsed] = useState(0);

  // Load existing session if sessionId provided
  useEffect(() => {
    if (sessionId) {
      loadSession(sessionId);
    }
  }, [sessionId]);

  // Timer for answer duration
  useEffect(() => {
    if (!showSetup && session?.status === 'in_progress') {
      timerRef.current = setInterval(() => {
        setTimeElapsed(prev => prev + 1);
      }, 1000);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [showSetup, session?.status]);

  const loadSession = async (id) => {
    try {
      setLoading(true);
      const response = await api.get(`/api/interview/sessions/${id}`);
      setSession(response.data);
      
      // Load questions
      const questionsResponse = await api.get(`/api/interview/sessions/${id}/questions`);
      setQuestions(questionsResponse.data);
      
      // Set current question index
      setCurrentQuestionIndex(response.data.current_question_index || 0);
    } catch (error) {
      console.error("Error loading session:", error);
    } finally {
      setLoading(false);
    }
  };

  const startNewSession = async () => {
    try {
      setLoading(true);
      const response = await api.post('/api/interview/sessions', setupData);
      setSession(response.data);
      setQuestions(response.data.questions || []);
      setCurrentQuestionIndex(0);
      setShowSetup(false);
      setTimeElapsed(0);
    } catch (error) {
      console.error("Error creating session:", error);
      // Fallback to local mode
      setSession({
        id: Date.now(),
        status: 'in_progress',
        job_title: setupData.job_title,
        ...setupData
      });
      setQuestions([
        { id: 1, question_text: 'Tell me about yourself and why you\'re interested in this role.', question_type: 'behavioral', tips: 'Use the present-past-future format' },
        { id: 2, question_text: 'Describe a challenging technical problem you solved.', question_type: 'technical', tips: 'Use the STAR method' },
        { id: 3, question_text: 'How do you handle disagreements with teammates?', question_type: 'behavioral', tips: 'Focus on communication and empathy' },
        { id: 4, question_text: 'Where do you see yourself in 5 years?', question_type: 'behavioral', tips: 'Show ambition and alignment with the role' },
      ]);
      setShowSetup(false);
      setTimeElapsed(0);
    } finally {
      setLoading(false);
    }
  };

  const submitAnswer = async () => {
    if (!answer.trim()) return;
    
    const currentQuestion = questions[currentQuestionIndex];
    if (!currentQuestion) return;

    try {
      setLoading(true);
      await api.post(`/api/interview/sessions/${session.id}/answer`, {
        question_id: currentQuestion.id,
        answer_text: answer,
        time_taken_seconds: timeElapsed
      });
      
      // Get feedback
      await getFeedback(currentQuestion.id);
      
      // Move to next question
      if (currentQuestionIndex < questions.length - 1) {
        setCurrentQuestionIndex(prev => prev + 1);
        setAnswer('');
        setTimeElapsed(0);
        setFeedback(null);
      } else {
        // Complete session
        await completeSession();
      }
    } catch (error) {
      console.error("Error submitting answer:", error);
      // Continue locally
      if (currentQuestionIndex < questions.length - 1) {
        setCurrentQuestionIndex(prev => prev + 1);
        setAnswer('');
        setTimeElapsed(0);
      }
    } finally {
      setLoading(false);
    }
  };

  const getFeedback = async (questionId) => {
    try {
      const response = await api.post(`/api/interview/sessions/${session.id}/feedback/${questionId}`);
      setFeedback(response.data.answer);
    } catch (error) {
      console.error("Error getting feedback:", error);
      // Mock feedback
      setFeedback({
        score: Math.floor(Math.random() * 30) + 60,
        feedback: "Good attempt! Consider adding more specific examples.",
        strengths: ["Clear communication", "Structured response"],
        improvements: ["Add more quantifiable metrics", "Be more specific about your role"],
        suggested_improvements: ["Use the STAR method more explicitly"]
      });
    }
  };

  const completeSession = async () => {
    try {
      const response = await api.post(`/api/interview/sessions/${session.id}/complete`);
      setSession(response.data.session);
    } catch (error) {
      console.error("Error completing session:", error);
      setSession(prev => ({ ...prev, status: 'completed', overall_score: 75 }));
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (loading && !session) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center gap-4">
        <button onClick={() => navigate('/app/interview')} className="p-2 hover:bg-white/10 rounded-xl text-slate-400 hover:text-white">
          <ArrowRight className="rotate-180" size={20} />
        </button>
        <div>
          <h1 className="text-3xl font-bold text-white">AI Mock Interview</h1>
          <p className="text-slate-400">
            {session?.job_title ? `Practice for ${session.job_title} at ${session.company || 'your target company'}` 
              : 'Practice with AI-powered interviews'}
          </p>
        </div>
      </div>

      {/* Setup Form */}
      {showSetup ? (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="card-glass p-8 space-y-6">
          <div className="text-center mb-6">
            <div className="w-20 h-20 bg-linear-to-br from-green-500 to-blue-600 rounded-2xl flex items-center justify-center mx-auto shadow-lg shadow-green-500/30 mb-4">
              <Zap size={40} className="text-white" />
            </div>
            <h2 className="text-2xl font-bold text-white">Set Up Your Mock Interview</h2>
            <p className="text-slate-400">We'll customize questions based on your target role</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-bold text-slate-300">Target Job Title</label>
              <input
                type="text"
                value={setupData.job_title}
                onChange={(e) => setSetupData(prev => ({ ...prev, job_title: e.target.value }))}
                placeholder="e.g., Software Engineer"
                className="w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3 text-white"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-bold text-slate-300">Company (Optional)</label>
              <input
                type="text"
                value={setupData.company}
                onChange={(e) => setSetupData(prev => ({ ...prev, company: e.target.value }))}
                placeholder="e.g., Google"
                className="w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3 text-white"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-bold text-slate-300">Job Description (Optional - for customized questions)</label>
            <textarea
              value={setupData.job_description}
              onChange={(e) => setSetupData(prev => ({ ...prev, job_description: e.target.value }))}
              placeholder="Paste the job description here for more targeted practice..."
              className="w-full h-32 bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3 text-white resize-none"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-bold text-slate-300">Interview Type</label>
            <div className="flex gap-3">
              {['behavioral', 'technical', 'mixed'].map(type => (
                <button
                  key={type}
                  onClick={() => setSetupData(prev => ({ ...prev, interview_type: type }))}
                  className={`flex-1 py-3 rounded-xl font-bold text-sm capitalize transition-all ${
                    setupData.interview_type === type 
                      ? 'bg-green-600 text-white' 
                      : 'bg-slate-800 text-slate-400 hover:text-white'
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>

          <button 
            onClick={startNewSession}
            disabled={loading}
            className="w-full py-4 bg-green-600 text-white font-bold rounded-2xl hover:bg-green-500 transition-all flex items-center justify-center gap-3 disabled:opacity-50"
          >
            {loading ? <RefreshCw className="animate-spin" size={20} /> : <Zap size={20} />}
            Start Interview
          </button>
        </motion.div>
      ) : session?.status === 'completed' ? (
        // Results View
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="card-glass p-8 space-y-6">
          <div className="text-center">
            <div className="w-20 h-20 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle2 size={40} className="text-green-400" />
            </div>
            <h2 className="text-2xl font-bold text-white">Interview Complete!</h2>
            {session.overall_score && (
              <div className="mt-4">
                <div className="text-5xl font-black text-white">{Math.round(session.overall_score)}%</div>
                <p className="text-slate-400">Overall Score</p>
              </div>
            )}
          </div>
          
          <div className="flex gap-4">
            <button 
              onClick={() => { setShowSetup(true); setSession(null); }}
              className="flex-1 py-4 bg-slate-800 text-white font-bold rounded-xl hover:bg-slate-700 transition-all flex items-center justify-center gap-2"
            >
              <RefreshCw size={20} /> New Interview
            </button>
            <button 
              onClick={() => navigate('/app/interview')}
              className="flex-1 py-4 bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-500 transition-all"
            >
              Back to Prep
            </button>
          </div>
        </motion.div>
      ) : (
        // Interview In Progress
        <div className="space-y-6">
          {/* Progress Bar */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <span className="text-slate-400">Question {currentQuestionIndex + 1} of {questions.length}</span>
              <div className="flex gap-1">
                {questions.map((_, i) => (
                  <div 
                    key={i} 
                    className={`w-8 h-1.5 rounded-full ${
                      i < currentQuestionIndex ? 'bg-green-500' : 
                      i === currentQuestionIndex ? 'bg-blue-500' : 'bg-slate-700'
                    }`}
                  />
                ))}
              </div>
            </div>
            <div className="flex items-center gap-2 text-slate-400">
              <span className="font-mono">{formatTime(timeElapsed)}</span>
            </div>
          </div>

          {/* Question Card */}
          <div className="card-glass p-8">
            <div className="flex items-start gap-4 mb-6">
              <div className={`p-3 rounded-xl ${
                questions[currentQuestionIndex]?.question_type === 'technical' 
                  ? 'bg-purple-500/20 text-purple-400' 
                  : 'bg-blue-500/20 text-blue-400'
              }`}>
                <MessageSquare size={24} />
              </div>
              <div className="flex-1">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                  {questions[currentQuestionIndex]?.question_type}
                </span>
                <h3 className="text-xl font-bold text-white mt-1">
                  {questions[currentQuestionIndex]?.question_text}
                </h3>
                {questions[currentQuestionIndex]?.tips && (
                  <p className="text-sm text-slate-400 mt-2 flex items-center gap-2">
                    💡 {questions[currentQuestionIndex].tips}
                  </p>
                )}
              </div>
            </div>
            
            {/* Answer Input */}
            <textarea
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder="Type your answer here..."
              className="w-full h-40 bg-slate-900/50 border border-white/10 rounded-xl p-4 text-white resize-none focus:ring-2 focus:ring-green-500/30"
            />

            {/* Feedback Display */}
            {feedback && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }} 
                animate={{ opacity: 1, y: 0 }}
                className="mt-6 p-6 bg-slate-900/60 rounded-xl border border-white/10"
              >
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-bold text-white">AI Feedback</h4>
                  <span className="text-2xl font-black text-green-400">{feedback.score}%</span>
                </div>
                <p className="text-slate-300 text-sm mb-4">{feedback.feedback}</p>
                {feedback.strengths && feedback.strengths.length > 0 && (
                  <div className="mb-3">
                    <span className="text-xs font-bold text-green-400 uppercase">Strengths</span>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {feedback.strengths.map((s, i) => (
                        <span key={i} className="px-2 py-1 bg-green-500/10 text-green-400 text-xs rounded-lg">{s}</span>
                      ))}
                    </div>
                  </div>
                )}
                {feedback.suggested_improvements && feedback.suggested_improvements.length > 0 && (
                  <div>
                    <span className="text-xs font-bold text-amber-400 uppercase">Suggestions</span>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {feedback.suggested_improvements.map((s, i) => (
                        <span key={i} className="px-2 py-1 bg-amber-500/10 text-amber-400 text-xs rounded-lg">{s}</span>
                      ))}
                    </div>
                  </div>
                )}
              </motion.div>
            )}

            {/* Actions */}
            <div className="flex items-center justify-between mt-6">
              <div className="flex gap-3">
                <button className="p-3 bg-slate-800 rounded-xl text-slate-400 hover:text-white transition-all">
                  <Mic size={20} />
                </button>
                <button className="p-3 bg-slate-800 rounded-xl text-slate-400 hover:text-white transition-all">
                  <Video size={20} />
                </button>
              </div>
              <div className="flex gap-3">
                <button 
                  onClick={() => { setShowSetup(true); setSession(null); }}
                  className="px-4 py-3 bg-slate-800 text-slate-400 font-bold rounded-xl hover:text-white transition-all"
                >
                  Exit
                </button>
                <button 
                  onClick={submitAnswer}
                  disabled={!answer.trim() || loading}
                  className="px-6 py-3 bg-green-600 text-white font-bold rounded-xl hover:bg-green-500 transition-all disabled:opacity-50 flex items-center gap-2"
                >
                  {loading ? (
                    <RefreshCw className="animate-spin" size={18} />
                  ) : currentQuestionIndex === questions.length - 1 ? (
                    <>Finish <CheckCircle2 size={18} /></>
                  ) : (
                    <>Next Question <Send size={18} /></>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MockInterview;

