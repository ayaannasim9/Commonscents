 'use client';
import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import Script from 'next/script';
import LearningApp from './learning-app';
import DashboardModule from './dashboard-module';
import type { LearningState } from '@/lib/types';

export default function OverviewApp({markup, initial}: {markup:string;initial:LearningState}) {
  const shell = useRef<HTMLDivElement>(null);
  const [panels,setPanels]=useState<{dashboard:HTMLElement;report:HTMLElement}|null>(null);
  useEffect(()=>{const dashboard=shell.current?.querySelector<HTMLElement>("#dashboard-root");const report=shell.current?.querySelector<HTMLElement>("#report-root");if(dashboard&&report)setPanels({dashboard,report});},[]);
  const [slot, setSlot] = useState<HTMLElement|null>(null);
  useEffect(()=>{ setSlot(shell.current?.querySelector<HTMLElement>('#learning-root') ?? null); },[]);
  return <>
    <div ref={shell} dangerouslySetInnerHTML={{__html:markup}}/>
    {slot && createPortal(<div className="integrated-learning"><LearningApp initial={initial}/></div>,slot)}
    {panels&&<DashboardModule {...panels}/>}
    <Script src="/overview/app.js" strategy="afterInteractive"/>
  </>;
}
