 'use client';
import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import Script from 'next/script';
import LearningApp from './learning-app';
import type { LearningState } from '@/lib/types';

export default function OverviewApp({markup, initial}: {markup:string;initial:LearningState}) {
  const shell = useRef<HTMLDivElement>(null);
  const [slot, setSlot] = useState<HTMLElement|null>(null);
  const [engineReady, setEngineReady] = useState(false);
  useEffect(()=>{ setSlot(shell.current?.querySelector<HTMLElement>('#learning-root') ?? null); },[]);
  return <>
    <div ref={shell} dangerouslySetInnerHTML={{__html:markup}}/>
    {slot && createPortal(<div className="integrated-learning"><LearningApp initial={initial}/></div>,slot)}
    <Script src="/overview/app.js" strategy="afterInteractive" onLoad={()=>setEngineReady(true)}/>
    {engineReady && <Script src="/overview/ml-bridge.js" strategy="afterInteractive"/>}
  </>;
}
