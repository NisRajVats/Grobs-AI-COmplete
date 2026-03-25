import React, { useState, useEffect } from 'react';
import { Check, Zap, Star, Crown, Loader2, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../../services/api';

const SubscriptionPage = () => {
  const [plans, setPlans] = useState([]);
  const [currentSubscription, setCurrentSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [subscribing, setSubscribing] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [plansRes, subRes] = await Promise.allSettled([
          api.get('/api/subscriptions/plans'),
          api.get('/api/subscriptions/my')
        ]);
        if (plansRes.status === 'fulfilled') setPlans(plansRes.value.data || []);
        if (subRes.status === 'fulfilled') setCurrentSubscription(subRes.value.data);
      } catch {
        // If no plans configured, show default free plan UI
      } finally { setLoading(false); }
    };
    load();
  }, []);

  const handleSubscribe = async (planId) => {
    setSubscribing(planId); setError(null);
    try {
      await api.post('/api/subscriptions/subscribe', { plan_id: planId });
      const subRes = await api.get('/api/subscriptions/my');
      setCurrentSubscription(subRes.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Subscription failed. Please try again.');
    } finally { setSubscribing(null); }
  };

  const defaultPlans = [
    { id: 'free', name: 'Free', price: 0, features: ['3 Resume uploads', 'Basic ATS analysis', '5 Job searches/day', 'Email support'], icon: Star, color: 'from-slate-600 to-slate-700' },
    { id: 'pro', name: 'Pro', price: 1900, features: ['Unlimited resumes', 'Advanced AI analysis', 'Unlimited job search', 'Mock interviews', 'Priority support', 'Resume optimization'], icon: Zap, color: 'from-blue-600 to-blue-700', popular: true },
    { id: 'enterprise', name: 'Enterprise', price: 4900, features: ['Everything in Pro', 'Team management', 'Custom branding', 'API access', 'Dedicated support', 'Analytics dashboard'], icon: Crown, color: 'from-purple-600 to-purple-700' },
  ];

  const displayPlans = plans.length > 0 ? plans.map((p, i) => ({
    ...p,
    price: p.price,
    features: p.features ? p.features.split(',') : [],
    icon: [Star, Zap, Crown][i % 3],
    color: ['from-slate-600 to-slate-700', 'from-blue-600 to-blue-700', 'from-purple-600 to-purple-700'][i % 3],
    popular: i === 1
  })) : defaultPlans;

  if (loading) return <div className="flex items-center justify-center py-20"><Loader2 className="animate-spin text-blue-400" size={40} /></div>;

  return (
    <div className="space-y-12 max-w-5xl mx-auto">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-black text-white">Choose Your Plan</h1>
        <p className="text-slate-400 text-lg">Unlock the full power of AI-driven career tools</p>
      </div>

      {error && <div className="flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400"><AlertCircle size={20} /><p className="text-sm">{error}</p></div>}

      {currentSubscription && (
        <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-xl text-green-400 text-sm flex items-center gap-2">
          <Check size={18} /> Current plan: <strong>{currentSubscription.plan_name || currentSubscription.plan?.name || 'Active'}</strong>
          {currentSubscription.end_date && ` · Renews ${new Date(currentSubscription.end_date).toLocaleDateString()}`}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {displayPlans.map((plan) => (
          <motion.div key={plan.id || plan.name} whileHover={{ y: -8 }} className={`card-glass p-8 space-y-6 relative overflow-hidden ${plan.popular ? 'ring-2 ring-blue-500/50' : ''}`}>
            {plan.popular && (
              <div className="absolute top-0 right-0 px-4 py-2 bg-blue-600 text-white text-xs font-black rounded-bl-2xl">MOST POPULAR</div>
            )}
            <div className={`w-14 h-14 bg-linear-to-br ${plan.color} rounded-2xl flex items-center justify-center shadow-lg`}>
              <plan.icon size={28} className="text-white" />
            </div>
            <div>
              <h3 className="text-2xl font-bold text-white">{plan.name}</h3>
              <div className="mt-2">
                {plan.price === 0 ? (
                  <span className="text-4xl font-black text-white">Free</span>
                ) : (
                  <><span className="text-4xl font-black text-white">${(plan.price / 100).toFixed(0)}</span><span className="text-slate-400">/mo</span></>
                )}
              </div>
            </div>
            <ul className="space-y-3">
              {(Array.isArray(plan.features) ? plan.features : []).map((f, i) => (
                <li key={i} className="flex items-center gap-3 text-slate-300 text-sm">
                  <Check size={16} className="text-green-400 shrink-0" /> {f.trim()}
                </li>
              ))}
            </ul>
            <button
              onClick={() => plan.price > 0 && handleSubscribe(plan.id)}
              disabled={subscribing === plan.id || plan.price === 0}
              className={`w-full py-4 font-bold rounded-2xl transition-all flex items-center justify-center gap-2 ${plan.price === 0 ? 'bg-slate-800 text-slate-500 cursor-default' : plan.popular ? 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-500/20' : 'bg-slate-800 hover:bg-slate-700 text-white'} disabled:opacity-50`}
            >
              {subscribing === plan.id ? <Loader2 size={20} className="animate-spin" /> : null}
              {plan.price === 0 ? 'Current Plan' : `Get ${plan.name}`}
            </button>
          </motion.div>
        ))}
      </div>

      <p className="text-center text-slate-600 text-sm">Payments powered by Stripe. Cancel anytime.</p>
    </div>
  );
};

export default SubscriptionPage;
