import React, { useEffect, useMemo, useRef, useState } from 'react'
import { cn } from '../../utils/cn'
import { ChevronDown, PenLine } from 'lucide-react'

export const CUSTOM_ROLE_OPTION = 'Other — Type your own role'

export const JOB_ROLES = [
  'Frontend Developer',
  'Backend Developer',
  'Full Stack Developer',
  'Software Engineer',
  'DevOps Engineer',
  'Data Scientist',
  'Data Analyst',
  'Machine Learning Engineer',
  'AI Engineer',
  'Product Designer',
  'UI/UX Designer',
  'Product Manager',
  'Project Manager',
  'QA / Test Engineer',
  'Mobile Developer',
  'Cloud Engineer',
  'Cybersecurity Engineer',
  'Technical Support Engineer',
  'Business Analyst',
  'Scrum Master',
]

interface JobRoleComboboxProps {
  label?: string
  name?: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
  error?: string
  suggested?: string[]
}

export const JobRoleCombobox = React.forwardRef<
  HTMLInputElement,
  JobRoleComboboxProps
>(({ label, name, value, onChange, placeholder, error, suggested }, ref) => {
  const [open, setOpen] = useState(false)
  const [highlighted, setHighlighted] = useState(0)
  const [isCustom, setIsCustom] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement | null>(null)

  const options = useMemo(() => {
    const pool = suggested && suggested.length > 0
      ? [...suggested, ...JOB_ROLES.filter((r) => !suggested.includes(r))]
      : JOB_ROLES

    const q = value.trim().toLowerCase()
    if (!q) return pool

    return pool.filter((role) => role.toLowerCase().includes(q))
  }, [value, suggested])

  // Reflect an externally-saved custom role (one not in the predefined list)
  // as "custom" so the Other entry shows as the active choice.
  useEffect(() => {
    if (value.trim() && !JOB_ROLES.includes(value.trim())) {
      setIsCustom(true)
    }
  }, [value])

  const commitValue = (next: string) => {
    onChange(next.trim())
    setIsCustom(false)
  }

  const selectCustom = () => {
    // Clear the field and focus it so the candidate can type their own role.
    setIsCustom(true)
    setOpen(false)
    onChange('')
    requestAnimationFrame(() => inputRef.current?.focus())
  }

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  useEffect(() => {
    setHighlighted(0)
  }, [options, isCustom])

  const renderOptions = [...options, CUSTOM_ROLE_OPTION]
  const customIndex = renderOptions.length - 1

  return (
    <div className="w-full space-y-2" ref={containerRef}>
      {label && <label className="block text-sm font-medium text-text">{label}</label>}
      <div className="relative">
        <input
          ref={(el) => {
            inputRef.current = el
            if (typeof ref === 'function') ref(el)
            else if (ref) ref.current = el
          }}
          name={name}
          value={value}
          onChange={(e) => {
            onChange(e.target.value)
            setOpen(true)
          }}
          onFocus={() => {
            if (!isCustom) setOpen(true)
          }}
          onKeyDown={(e) => {
            if (!open) return
            if (e.key === 'ArrowDown') {
              e.preventDefault()
              setHighlighted((i) => Math.min(i + 1, renderOptions.length - 1))
            } else if (e.key === 'ArrowUp') {
              e.preventDefault()
              setHighlighted((i) => Math.max(i - 1, 0))
            } else if (e.key === 'Enter') {
              const picked = renderOptions[highlighted]
              if (picked) {
                e.preventDefault()
                if (picked === CUSTOM_ROLE_OPTION) selectCustom()
                else {
                  commitValue(picked)
                  setOpen(false)
                }
              }
            } else if (e.key === 'Escape') {
              setOpen(false)
            }
          }}
          placeholder={isCustom ? (placeholder || 'Type your own role') : placeholder}
          autoComplete="off"
          aria-expanded={open}
          className={cn(
            'w-full px-4 py-2.5 rounded-lg bg-surface border-2 border-surface-light text-text placeholder-text-secondary transition-all duration-200 focus:outline-none focus:border-primary focus:bg-surface-light',
            error && 'border-error focus:border-error'
          )}
        />
        <ChevronDown
          className={cn(
            'h-5 w-5 absolute right-3 top-1/2 -translate-y-1/2 text-text-secondary pointer-events-none transition-transform',
            open && 'rotate-180'
          )}
        />
        {open && (
          <ul className="absolute z-20 w-full mt-1 max-h-64 overflow-y-auto rounded-lg bg-surface border-2 border-surface-light shadow-lg">
            {options.length === 0 ? (
              <li className="px-4 py-2.5 text-sm text-text-secondary">No matching role</li>
            ) : (
              options.map((role, i) => (
                <li
                  key={role}
                  onMouseEnter={() => setHighlighted(i)}
                  onMouseDown={(e) => {
                    e.preventDefault()
                    commitValue(role)
                    setOpen(false)
                  }}
                  className={cn(
                    'px-4 py-2.5 text-sm cursor-pointer text-text transition-colors',
                    i === highlighted && 'bg-primary/15 text-primary'
                  )}
                >
                  {role}
                </li>
              ))
            )}

            {/* Final option: custom role entry */}
            <li
              role="option"
              aria-selected={isCustom}
              onMouseEnter={() => setHighlighted(customIndex)}
              onMouseDown={(e) => {
                e.preventDefault()
                selectCustom()
              }}
              className={cn(
                'mt-1 border-t border-surface-light px-4 py-2.5 text-sm cursor-pointer text-text transition-colors',
                highlighted === customIndex && 'bg-primary/15 text-primary'
              )}
            >
              <span className="flex items-center gap-2">
                <PenLine className="h-4 w-4 text-primary" />
                {CUSTOM_ROLE_OPTION}
              </span>
            </li>
          </ul>
        )}
      </div>
      {error && <p className="text-sm text-error">{error}</p>}
    </div>
  )
})

JobRoleCombobox.displayName = 'JobRoleCombobox'
