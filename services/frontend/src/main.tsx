
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './styles.css'

import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './styles.css'

type FetchDebug = {
  ts: string
  request: {
    url: string
    method: string
    headers: Record<string, string>
    bodyPreview?: string
  }
  response?: {
    ok: boolean
    status: number
    statusText: string
    headers: Record<string, string>
    bodyText?: string
  }
  error?: string
}

declare global {
  interface Window {
    __fetchDebug?: { last?: FetchDebug }
  }
}

(function attachFetchDebugger() {
  if (typeof window === 'undefined') return
  if ((window as any).__fetchDebuggerInstalled) return
  ;(window as any).__fetchDebuggerInstalled = true

  const orig = window.fetch.bind(window)

  window.fetch = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const startedAt = new Date().toISOString()
    const req = new Request(input as any, init)

    const dbgBase: FetchDebug = {
      ts: startedAt,
      request: {
        url: req.url,
        method: req.method || (init?.method ?? 'GET'),
        headers: {},
      },
    }
    req.headers.forEach((v, k) => (dbgBase.request.headers[k] = v))

    try {
      const m = (dbgBase.request.method || 'GET').toUpperCase()
      if (m !== 'GET' && m !== 'HEAD' && init?.body && typeof init.body === 'string') {
        const s = init.body as string
        dbgBase.request.bodyPreview = s.length > 2000 ? s.slice(0, 2000) + '…[truncated]' : s
      }
    } catch { /* ignore */ }

    try {
      const res = await orig(input as any, init)

      if (!res.ok) {
        const clone = res.clone()
        const bodyText = await clone.text().catch(() => undefined)
        const headers: Record<string, string> = {}
        res.headers.forEach((v, k) => (headers[k] = v))
        const dbg: FetchDebug = {
          ...dbgBase,
          response: {
            ok: res.ok,
            status: res.status,
            statusText: res.statusText,
            headers,
            bodyText,
          },
        }
        window.__fetchDebug = { last: dbg }
        window.dispatchEvent(new CustomEvent('fetch-debug', { detail: dbg }))
      }
      return res
    } catch (e: any) {
      const dbg: FetchDebug = {
        ...dbgBase,
        error: e?.message || String(e),
      }
      window.__fetchDebug = { last: dbg }
      window.dispatchEvent(new CustomEvent('fetch-debug', { detail: dbg }))
      throw e
    }
  }
})()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
