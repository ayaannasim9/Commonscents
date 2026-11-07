'use client';
import { useEffect, useState } from 'react';
import type { Question } from '@/lib/types';

export default function ExerciseChoices({question,selected,onSelect,disabled,correctIndex}: {
  question:Question;selected:number|null;onSelect:(value:number|null)=>void;disabled:boolean;correctIndex?:number;
}) {
  const interaction=question.interaction;
  const items=interaction?.items??[];
  const [values,setValues]=useState<number[]>(()=>interaction?.kind==='order'?items.map((_,i)=>i):items.map(()=>-1));
  const [announcement,setAnnouncement]=useState('');
  function encode(next:number[]) { const index=question.options.indexOf(JSON.stringify(next));onSelect(index<0?null:index); }
  useEffect(()=>{if(interaction?.kind==='order')encode(values);},[]);
  function update(next:number[]) {setValues(next);encode(next);}
  if(interaction?.kind==='match')return <fieldset className="answers matching" disabled={disabled}><legend>Choose a meaning for each item</legend>{interaction.left?.map((label,i)=><label key={label} className="match-row"><span>{label}</span><select value={values[i]} onChange={e=>update(values.map((v,n)=>n===i?Number(e.target.value):v))}><option value={-1}>Choose a meaning</option>{items.map((item,n)=><option key={item} value={n}>{item}</option>)}</select></label>)}<p>Use each meaning once. Choose every match, then check your answer.</p></fieldset>;
  if(interaction?.kind==='order')return <fieldset className="answers ordering" disabled={disabled}><legend>Put the steps in order</legend><p>Use Move up and Move down. You can use these buttons with a keyboard; dragging is not needed.</p><ol>{values.map((value,i)=><li key={value}><span>{items[value]}</span><div>{[-1,1].map(direction=><button type="button" key={direction} aria-label={`Move ${items[value]} ${direction<0?'up':'down'}`} disabled={disabled} aria-disabled={i+direction<0||i+direction>=values.length} onClick={()=>{if(i+direction<0||i+direction>=values.length)return;const next=[...values];[next[i],next[i+direction]]=[next[i+direction],next[i]];update(next);setAnnouncement(`${items[value]} moved to position ${i+direction+1} of ${values.length}.`);}}>{direction<0?'↑ Move up':'↓ Move down'}</button>)}</div></li>)}</ol><p role="status" className="move-status">{announcement}</p></fieldset>;
  return <fieldset className="answers" disabled={disabled}><legend>{interaction?.kind==='fill'?'Choose the missing word':'Choose one answer'}</legend>{question.options.map((option,i)=><label key={option} className={`answer ${selected===i?'selected':''} ${correctIndex===i?'correct':''}`}><input type="radio" name={`answer-${question.id}`} checked={selected===i} onChange={()=>onSelect(i)}/><span>{option}</span>{correctIndex===i&&<strong className="answer-status">✓ Correct answer</strong>}{correctIndex!==undefined&&selected===i&&correctIndex!==i&&<strong className="answer-status">Your answer — try again next time</strong>}</label>)}</fieldset>;
}
