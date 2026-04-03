import React, { useState, useEffect } from 'react';
import { 
  BarChart, 
  Bar, 
  LineChart, 
  Line, 
  PieChart, 
  Pie, 
  Cell, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';
import { 
  TrendingUp, 
  Users, 
  FileText, 
  Target, 
  Clock, 
  DollarSign,
  Calendar,
  TrendingDown,
  CheckCircle,
  AlertTriangle,
  Eye,
  Download,
  Share2,
  Filter,
  ChevronDown,
  Sparkles
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../../services/api';

const AnalyticsDashboard = () => {
  const [timeRange, setTimeRange] = useState('30d');
  const [analyticsData, setAnalyticsData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await api.get(`/api/analytics/user?time_range=${timeRange}`);
        setAnalyticsData(response.data);
      } catch (err) {
        console.error('Failed to fetch analytics:', err);
        setError('Failed to load analytics data');
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, [timeRange]);

  const keyMetrics = [
    { 
      label: 'Total Applications', 
      value: analyticsData?.keyMetrics.totalApplications || 0, 
      change: '+12%', 
      trend: 'up',
      icon: Users,
      color: 'text-blue-400',
      bg: 'bg-blue-600/10'
    },
    { 
      label: 'Avg. Resume Score', 
      value: `${analyticsData?.keyMetrics.avgResumeScore || 0}%`, 
      change: '+5%', 
      trend: 'up',
      icon: FileText,
      color: 'text-green-400',
      bg: 'bg-green-600/10'
    },
    { 
      label: 'Interview Rate', 
      value: `${analyticsData?.keyMetrics.interviewRate || 0}%`, 
      change: '+3%', 
      trend: 'up',
      icon: Target,
      color: 'text-amber-400',
      bg: 'bg-amber-600/10'
    },
    { 
      label: 'Offer Rate', 
      value: `${analyticsData?.keyMetrics.offerRate || 0}%`, 
      change: '-2%', 
      trend: 'down',
      icon: DollarSign,
      color: 'text-rose-400',
      bg: 'bg-rose-600/10'
    },
  ];

  const statusColors = {
    'application': 'text-blue-400',
    'interview': 'text-amber-400', 
    'resume': 'text-green-400',
    'offer': 'text-purple-400'
  };

  const getActivityIcon = (type) => {
    switch(type) {
      case 'application': return Users;
      case 'interview': return Calendar;
      case 'resume': return FileText;
      case 'offer': return DollarSign;
      default: return Eye;
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Analytics Dashboard</h1>
          <p className="text-slate-400 mt-1">Track your job search performance and career growth</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex gap-2">
            {['7d', '30d', '90d', '1y'].map(range => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={`px-4 py-2 rounded-lg font-semibold ${
                  timeRange === range 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                } transition-all`}
              >
                {range}
              </button>
            ))}
          </div>
          <div className="flex gap-2">
            <button className="flex items-center gap-2 px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-all">
              <Download size={18} />
              Export
            </button>
            <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-500 transition-all">
              <Share2 size={18} />
              Share
            </button>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {keyMetrics.map((metric, index) => (
          <motion.div
            key={metric.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="card-glass p-6 border-white/5"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">{metric.label}</p>
                <p className="text-2xl font-bold text-white">{metric.value}</p>
              </div>
              <div className={`p-3 rounded-xl ${metric.bg} ${metric.color}`}>
                <metric.icon size={24} />
              </div>
            </div>
            <div className="flex items-center justify-between mt-4">
              <p className={`text-sm font-medium ${
                metric.trend === 'up' ? 'text-green-400' : 'text-red-400'
              }`}>
                {metric.change} from last period
              </p>
              <div className={`w-2 h-2 rounded-full ${
                metric.trend === 'up' ? 'bg-green-400' : 'bg-red-400'
              }`}></div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Application Trends */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card-glass p-6 border-white/5"
        >
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-bold text-white">Application Trends</h3>
            <div className="flex gap-2 text-sm">
              <span className="flex items-center gap-1.5 text-blue-400">
                <div className="w-2 h-2 rounded-full bg-blue-400"></div>
                Applications
              </span>
              <span className="flex items-center gap-1.5 text-amber-400">
                <div className="w-2 h-2 rounded-full bg-amber-400"></div>
                Interviews
              </span>
              <span className="flex items-center gap-1.5 text-green-400">
                <div className="w-2 h-2 rounded-full bg-green-400"></div>
                Offers
              </span>
            </div>
          </div>
          <div className="h-75 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={analyticsData?.keyMetrics.applicationTrend || []}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8' }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: '#94a3b8' }} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                  itemStyle={{ color: '#e2e8f0' }}
                />
                <Legend />
                <Bar dataKey="applications" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="interviews" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                <Bar dataKey="offers" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Resume Performance Over Time */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card-glass p-6 border-white/5"
        >
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-bold text-white">Resume Performance</h3>
            <div className="flex gap-2 text-sm">
              <span className="flex items-center gap-1.5 text-blue-400">
                <div className="w-2 h-2 rounded-full bg-blue-400"></div>
                Score Trend
              </span>
            </div>
          </div>
          <div className="h-75 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={analyticsData?.keyMetrics.resumePerformance || []}>
                <defs>
                  <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8' }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: '#94a3b8' }} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                  itemStyle={{ color: '#e2e8f0' }}
                />
                <Area 
                  type="monotone" 
                  dataKey="score" 
                  stroke="#3b82f6" 
                  strokeWidth={2}
                  fillOpacity={1} 
                  fill="url(#colorScore)" 
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Application Status Distribution */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card-glass p-6 border-white/5"
        >
          <h3 className="text-lg font-bold text-white mb-6">Application Status</h3>
          <div className="h-75 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={analyticsData?.keyMetrics.applicationStatus || []}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {(analyticsData?.keyMetrics.applicationStatus || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                  itemStyle={{ color: '#e2e8f0' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-col gap-3 mt-6">
            {(analyticsData?.keyMetrics.applicationStatus || []).map((item) => (
              <div key={item.name} className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }}></div>
                  <span className="text-sm text-slate-400">{item.name}</span>
                </div>
                <span className="text-sm font-bold text-white">{item.value}%</span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Skill Gap Analysis */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card-glass p-6 border-white/5"
        >
          <h3 className="text-lg font-bold text-white mb-6">Skill Gap Analysis</h3>
          <div className="space-y-6">
            {(analyticsData?.keyMetrics.skillGapAnalysis || []).map((skill) => (
              <div key={skill.skill} className="space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-white font-medium">{skill.skill}</span>
                  <span className="text-sm font-bold" style={{ color: skill.color }}>{skill.gap}%</span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-3">
                  <div 
                    className="h-3 rounded-full transition-all duration-500"
                    style={{ 
                      width: `${skill.gap}%`, 
                      backgroundColor: skill.color 
                    }}
                  ></div>
                </div>
                <p className="text-xs text-slate-500">
                  {skill.gap > 70 ? 'Strong skill - Keep improving' : 
                   skill.gap > 40 ? 'Needs improvement - Focus here' : 
                   'Critical gap - Priority learning'}
                </p>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Recent Activity */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card-glass p-6 border-white/5"
        >
          <h3 className="text-lg font-bold text-white mb-6">Recent Activity</h3>
          <div className="space-y-4">
            {(analyticsData?.keyMetrics.recentActivity || []).map((activity) => {
              const Icon = getActivityIcon(activity.type);
              return (
                <div key={activity.id} className="flex items-center gap-4 p-4 bg-white/5 rounded-xl border border-white/10">
                  <div className={`p-2 rounded-lg ${
                    activity.status === 'success' ? 'bg-green-600/20 text-green-400' :
                    activity.status === 'warning' ? 'bg-amber-600/20 text-amber-400' :
                    'bg-blue-600/20 text-blue-400'
                  }`}>
                    <Icon size={20} />
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold text-white">{activity.title}</h4>
                    <p className="text-xs text-slate-400 mt-1">{activity.time}</p>
                  </div>
                  <div className={`w-2 h-2 rounded-full ${
                    activity.status === 'success' ? 'bg-green-400' :
                    activity.status === 'warning' ? 'bg-amber-400' :
                    'bg-blue-400'
                  }`}></div>
                </div>
              );
            })}
          </div>
          <button className="w-full mt-6 py-3 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-all">
            View All Activity
          </button>
        </motion.div>
      </div>

      {/* Insights & Recommendations */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="card-glass p-8 border-white/5"
      >
        <h3 className="text-xl font-bold text-white mb-6">AI Insights & Recommendations</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {(analyticsData?.keyMetrics.aiInsights || []).length > 0 ? (
            (analyticsData?.keyMetrics.aiInsights || []).map((insight, idx) => {
              const colors = {
                success: 'from-green-600/10 to-green-800/10 border-green-500/20',
                warning: 'from-amber-600/10 to-amber-800/10 border-amber-500/20',
                info: 'from-blue-600/10 to-blue-800/10 border-blue-500/20',
                tip: 'from-purple-600/10 to-purple-800/10 border-purple-500/20'
              };
              const iconColors = {
                success: 'bg-green-600/20 text-green-400',
                warning: 'bg-amber-600/20 text-amber-400',
                info: 'bg-blue-600/20 text-blue-400',
                tip: 'bg-purple-600/20 text-purple-400'
              };
              const Icons = {
                success: CheckCircle,
                warning: AlertTriangle,
                info: Eye,
                tip: Target
              };
              
              const type = insight.type || 'info';
              const Icon = Icons[type] || Icons.info;
              
              return (
                <div key={idx} className={`p-6 bg-linear-to-br ${colors[type] || colors.info} border rounded-xl`}>
                  <div className="flex items-center gap-3 mb-4">
                    <div className={`p-2 rounded-lg ${iconColors[type] || iconColors.info}`}>
                      <Icon size={20} />
                    </div>
                    <h4 className="font-bold text-white capitalize">{type}</h4>
                  </div>
                  <p className="text-sm text-slate-300 mb-4">{insight.message}</p>
                  <button className={`text-sm font-bold ${iconColors[type].split(' ')[1]} hover:opacity-80`}>
                    {insight.action}
                  </button>
                </div>
              );
            })
          ) : (
            <div className="col-span-3 p-12 text-center bg-white/5 rounded-2xl border border-white/10">
              <Sparkles className="mx-auto text-slate-500 mb-4" size={32} />
              <p className="text-slate-400 italic">Complete more applications and optimize your resume to receive AI-powered insights!</p>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
};

export default AnalyticsDashboard;