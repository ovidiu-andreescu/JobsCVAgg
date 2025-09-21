
import * as React from 'react'
type TabsCtx = { value: string, setValue: (v:string)=>void }
const Ctx = React.createContext<TabsCtx | null>(null)
export function Tabs({ value, onValueChange, children, className='' }:{value:string, onValueChange:(v:string)=>void, children:React.ReactNode, className?:string}){
  return <Ctx.Provider value={{ value, setValue: onValueChange }}><div className={className}>{children}</div></Ctx.Provider>
}
export function TabsList({children, className=''}:{children:React.ReactNode, className?:string}){
  return <div className={`inline-flex rounded-xl border bg-muted p-1 ${className}`}>{children}</div>
}
export function TabsTrigger({value, children}:{value:string, children:React.ReactNode}){
  const ctx = React.useContext(Ctx)!
  const active = ctx.value === value
  return <button onClick={()=>ctx.setValue(value)} className={`px-3 py-1.5 rounded-lg text-sm ${active?'bg-white shadow':''}`}>{children}</button>
}
export function TabsContent({value, children}:{value:string, children:React.ReactNode}){
  const ctx = React.useContext(Ctx)!
  if (ctx.value !== value) return null
  return <div className="mt-3">{children}</div>
}
