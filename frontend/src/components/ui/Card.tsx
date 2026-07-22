import React from 'react'
import { cn } from '../../utils/cn'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'outlined' | 'elevated'
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = 'default', ...props }, ref) => {
    const variants = {
      default: 'bg-surface border border-surface-light',
      outlined: 'border-2 border-surface-light bg-surface/50',
      elevated: 'bg-surface border border-surface-light shadow-lg shadow-primary/10',
    }

    return (
      <div
        ref={ref}
        className={cn('rounded-lg p-6 backdrop-blur-sm', variants[variant], className)}
        {...props}
      />
    )
  }
)

Card.displayName = 'Card'
