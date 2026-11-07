import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import { useVersion } from '../useVersion'

/** Same letter wording as the PDF, with screen-only reflow and shared display preferences. */
export function LetterFrame({ customerId, frameRef }: { customerId: string; frameRef?: React.RefObject<HTMLIFrameElement | null> }) {
  const [html, setHtml] = useState<string | null>(null)
  const [err, setErr] = useState(false)
  const [h, setH] = useState(900)
  const [loaded, setLoaded] = useState(0)
  const inner = useRef<HTMLIFrameElement>(null)
  const ref = frameRef ?? inner
  const version = useVersion()
  useEffect(() => {
    let on = true
    setErr(false)
    api.letterHtml(customerId).then((t) => { if (on) setHtml(t) }).catch(() => { if (on) setErr(true) })
    return () => { on = false }
  }, [customerId, version])
  useEffect(()=>{
    const frame=ref.current, doc=frame?.contentDocument
    if(!frame||!doc?.body)return
    const sync=()=>{
      const root=getComputedStyle(document.documentElement)
      doc.documentElement.style.setProperty('--letter-size',root.fontSize)
      doc.documentElement.style.setProperty('--letter-ink',root.getPropertyValue('--tx'))
      doc.documentElement.style.setProperty('--letter-paper',root.getPropertyValue('--card'))
      if(frame.getBoundingClientRect().width>0)setH(Math.ceil(doc.body.getBoundingClientRect().height)+32)
    }
    sync()
    const theme=new MutationObserver(sync)
    theme.observe(document.documentElement,{attributes:true,attributeFilter:['style','data-theme','data-contrast']})
    const size=new ResizeObserver(sync);size.observe(doc.body);size.observe(frame)
    return()=>{theme.disconnect();size.disconnect()}
  },[loaded,ref])
  if (err && !html) return <p className="errbox" role="alert">We could not load the letter. Check the dashboard service is running, then reopen Report.</p>
  if (!html) return <div className="skel" style={{ height: 900 }} aria-busy="true" />
  const screenStyle='<style>@media screen {body{max-width:none;margin:0;padding:16px;box-sizing:border-box;font-size:var(--letter-size,18px);color:var(--letter-ink,#2b0d3e);background:var(--letter-paper,white);overflow-wrap:anywhere}h1{font-size:1.5em}h2{font-size:1.2em}.ref{font-size:1em}}</style>'
  return <div className="paper"><iframe ref={ref} title="Your monthly letter" srcDoc={html.replace('</head>',screenStyle+'</head>')} sandbox="allow-same-origin allow-modals" style={{height:h}} onLoad={()=>setLoaded(n=>n+1)}/></div>
}
