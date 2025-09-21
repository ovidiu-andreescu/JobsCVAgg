
import * as React from 'react'
export const Textarea = React.forwardRef<HTMLTextAreaElement, React.TextareaHTMLAttributes<HTMLTextAreaElement>>(function Textarea({className='', ...props}, ref){
  return <textarea ref={ref} className={`w-full rounded-xl border px-3 py-2 shadow-sm focus:outline-none focus:ring-2 focus:ring-black/20 ${className}`} {...props} />
})
