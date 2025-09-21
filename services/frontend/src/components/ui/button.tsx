
import * as React from 'react'
type Props = React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'default'|'secondary'|'ghost', size?: 'sm'|'md' }
export function Button({ className='', variant='default', size='md', ...props }: Props) {
  const base = 'rounded-2xl px-4 py-2 shadow transition disabled:opacity-50 disabled:cursor-not-allowed'
  const v = variant==='secondary' ? 'bg-muted text-black' : variant==='ghost' ? 'bg-transparent hover:bg-muted' : 'bg-black text-white'
  const s = size==='sm' ? 'text-sm py-1.5 px-3' : ''
  return <button className={`${base} ${v} ${s} ${className}`} {...props} />
}
