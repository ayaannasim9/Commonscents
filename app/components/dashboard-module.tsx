'use client';
import { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { MemoryRouter, NavLink, Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { AppProvider, useApp } from '@/dashboard-and-letter/frontend/src/state';
import DashboardPage from '@/dashboard-and-letter/frontend/src/pages/DashboardPage';
import LetterPage from '@/dashboard-and-letter/frontend/src/pages/LetterPage';
import QueuePage from '@/dashboard-and-letter/frontend/src/pages/QueuePage';
import CasePage from '@/dashboard-and-letter/frontend/src/pages/CasePage';
import DemoPage from '@/dashboard-and-letter/frontend/src/pages/DemoPage';
import PersonasPage from '@/dashboard-and-letter/frontend/src/pages/PersonasPage';
import WhatWeKnowPage from '@/dashboard-and-letter/frontend/src/pages/WhatWeKnowPage';

function Toolbar({report=false}:{report?:boolean}) {
  const {role,setRole,customer}=useApp();
  return <div className="module-toolbar">
    <p><strong>{customer?`${customer.name}’s money`:'Your money'}</strong> · Fictional demo data</p>
    <fieldset className="role-control"><legend>View as</legend>{(['customer','helper'] as const).map(r=><label key={r}><input type="radio" name={report?'report-role':'dashboard-role'} checked={role===r} onChange={()=>setRole(r)}/>{r==='customer'?'Customer':'Helper'}</label>)}</fieldset>
    {!report&&<nav className="module-nav" aria-label="Dashboard tools"><NavLink to="/dashboard">Your money</NavLink>{role==='helper'&&<><NavLink to="/queue">Questions</NavLink><NavLink to="/personas">People</NavLink><NavLink to="/demo">Demo tools</NavLink></>}<NavLink to="/what-we-know">What we know</NavLink><button onClick={()=>document.getElementById('t-report')?.click()}>Monthly letter</button></nav>}
    {role==='helper'&&<p className="demo-helper-note">Helper demo · Daria, community banker. Approvals are recorded locally; nothing is posted or sent.</p>}
  </div>;
}
function Guard({children}:{children:React.ReactNode}){const {role}=useApp();return role==='helper'?children:<Navigate to="/dashboard" replace/>;}
function Panels({dashboard,report}:{dashboard:HTMLElement;report:HTMLElement}) {
  const {customerId,live}=useApp();
  const {pathname}=useLocation();
  const body=useRef<HTMLDivElement>(null);
  const previous=useRef(pathname);
  useEffect(()=>{if(previous.current!==pathname){previous.current=pathname;body.current?.focus();}},[pathname]);
  useEffect(()=>{
    const stop=()=>{if(document.getElementById('s-dashboard')?.hidden&&'speechSynthesis' in window)window.speechSynthesis.cancel();};
    const observer=new MutationObserver(stop);const panel=document.getElementById('s-dashboard');if(panel)observer.observe(panel,{attributes:true,attributeFilter:['hidden']});return()=>observer.disconnect();
  },[]);
  return <>
    {createPortal(<div className="counterpart"><Toolbar/><div className="page" ref={body} tabIndex={-1}><Routes>
      <Route path="/dashboard" element={<DashboardPage/>}/>
      <Route path="/queue" element={<Guard><QueuePage/></Guard>}/>
      <Route path="/cases/:id" element={<Guard><CasePage/></Guard>}/>
      <Route path="/personas" element={<Guard><PersonasPage/></Guard>}/>
      <Route path="/demo" element={<Guard><DemoPage/></Guard>}/>
      <Route path="/what-we-know" element={<WhatWeKnowPage/>}/>
      <Route path="*" element={<Navigate to="/dashboard" replace/>}/>
    </Routes></div><p className="module-footnote">Prototype only. The dashboard and monthly letter use the same calculated facts.</p><div className="visually-hidden" role="status">{live}</div></div>,dashboard)}
    {createPortal(<div className="counterpart"><Toolbar report/><LetterPage key={customerId}/><div className="visually-hidden" role="status">{live}</div></div>,report)}
  </>;
}
export default function DashboardModule(props:{dashboard:HTMLElement;report:HTMLElement}) {
  return <AppProvider><MemoryRouter initialEntries={['/dashboard']}><Panels {...props}/></MemoryRouter></AppProvider>;
}
