import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

const Button = ({ 
  children, 
  className, 
  variant = 'primary', 
  size = 'md', 
  leftIcon: LeftIcon, 
  rightIcon: RightIcon,
  loading = false,
  disabled = false,
  ...props 
}) => {
  const variants = {
    primary: 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-500/20 border-transparent',
    secondary: 'bg-slate-800 hover:bg-slate-700 text-white border-white/10',
    outline: 'bg-transparent border-white/10 hover:border-white/20 text-white',
    ghost: 'bg-transparent border-transparent hover:bg-white/5 text-slate-400 hover:text-white',
    danger: 'bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-500/20 border-transparent',
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-xs rounded-lg',
    md: 'px-5 py-2.5 text-sm rounded-xl',
    lg: 'px-8 py-3.5 text-base rounded-2xl',
    icon: 'p-2.5 rounded-xl',
  };

  const baseStyles = 'inline-flex items-center justify-center font-bold transition-all active:scale-95 disabled:opacity-50 disabled:pointer-events-none border gap-2';
  
  return (
    <button 
      className={twMerge(clsx(baseStyles, variants[variant], sizes[size], className))}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
      ) : (
        <>
          {LeftIcon && <LeftIcon size={size === 'sm' ? 14 : 18} />}
          {children}
          {RightIcon && <RightIcon size={size === 'sm' ? 14 : 18} />}
        </>
      )}
    </button>
  );
};

export default Button;
