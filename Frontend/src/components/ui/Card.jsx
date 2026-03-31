import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

const Card = ({ 
  children, 
  className, 
  padding = 'md',
  ...props 
}) => {
  const paddings = {
    none: 'p-0',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-10',
  };

  return (
    <div 
      className={twMerge(clsx(
        'card-glass border-white/5 relative overflow-hidden',
        paddings[padding],
        className
      ))}
      {...props}
    >
      {children}
    </div>
  );
};

export default Card;
