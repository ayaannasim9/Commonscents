'use client';
import { useState } from 'react';
import type { Journey } from '@/lib/types';

export default function StartingPoint({journeys,busy,onChoose}: {journeys:Journey[];busy:boolean;onChoose:(id:string)=>Promise<void>}) {
  const [selected,setSelected] = useState('');
  const choices = [
    ['independent','I’m taking care of my money myself'],
    ['university','I’m moving to university'],
    ['bills','I’m finding bills hard to manage'],
    ['first-job','I’ve started my first job'],
  ];
  const recommended=journeys.find(j=>j.id===selected);
  return <details className="starting-point guide-section">
    <summary>Not sure where to start? Ask Penny</summary>
    <div className="guide-section-body">
      <p>What would help you most today? There are no wrong answers. You can change journeys any time.</p>
      <fieldset className="answers"><legend>Choose the situation closest to yours</legend>{choices.map(([id,label])=><label className={`answer ${selected===id?'selected':''}`} key={id}><input type="radio" name="starting-point" checked={selected===id} onChange={()=>setSelected(id)}/>{label}</label>)}</fieldset>
      {recommended&&<div className="recommendation" role="status"><h3>{recommended.title}</h3><p>{recommended.description}</p><button className="primary" disabled={busy} onClick={()=>onChoose(selected)}>Use this journey</button></div>}
      <p className="muted">This helps you choose a path. It does not award points or skip lessons.</p>
    </div>
  </details>;
}
