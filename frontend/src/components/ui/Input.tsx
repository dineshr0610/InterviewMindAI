import React from 'react'
import { cn } from '../../utils/cn'

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className, ...props }, ref) => {
    return (
      <div className="w-full space-y-2">
        {label && <label className="block text-sm font-medium text-text">{label}</label>}
        <input
          ref={ref}
          className={cn(
            'w-full px-4 py-2.5 rounded-lg bg-surface border-2 border-surface-light text-text placeholder-text-secondary transition-all duration-200 focus:outline-none focus:border-primary focus:bg-surface-light',
            error && 'border-error focus:border-error',
            className
          )}
          {...props}
        />
        {error && <p className="text-sm text-error">{error}</p>}
      </div>
    )
  }
)

Input.displayName = 'Input'
