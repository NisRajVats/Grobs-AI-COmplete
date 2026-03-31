import React from 'react';
import Button from './Button';

const EmptyState = ({ 
  icon: Icon, 
  title, 
  description, 
  actionText, 
  onAction 
}) => {
  return (
    <div className="flex flex-col items-center justify-center py-20 px-4 text-center space-y-6 card-glass border-dashed border-white/10">
      {Icon && (
        <div className="p-6 bg-slate-900/50 rounded-3xl border border-white/5 shadow-2xl">
          <Icon size={48} className="text-slate-600" />
        </div>
      )}
      <div className="max-w-md space-y-2">
        <h3 className="text-2xl font-bold text-white">{title}</h3>
        <p className="text-slate-400">{description}</p>
      </div>
      {actionText && onAction && (
        <Button onClick={onAction}>
          {actionText}
        </Button>
      )}
    </div>
  );
};

export default EmptyState;
