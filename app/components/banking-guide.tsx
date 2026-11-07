'use client';
import { useState } from 'react';
import data from '@/content/banking-guide.json';
const firstLessons=['bank-a1','bank-b1','bank-c1','bank-d1'];
export default function BankingGuide({onStart,busy}: {onStart:(id:string)=>void;busy:boolean}) {
  const [answers,setAnswers]=useState<number[]>([-1,-1,-1,-1]);
  const [checked,setChecked]=useState(false);
  const score=data.placement.filter((q,i)=>answers[i]===q[2]).length;
  const firstGap=data.placement.findIndex((q,i)=>answers[i]!==q[2]);
  return <>
    <details className="learning-guidebook"><summary>Quick knowledge check · optional</summary><div className="guide-section-body"><p>Four questions from the original banking course. Find a useful starting point, or open any lesson below. No points or completions are awarded by this check.</p>{data.placement.map((q,i)=><fieldset className="answers" key={i}><legend>{String(q[0])}</legend>{(q[1] as string[]).map((option,n)=><label className="answer" key={option}><input type="radio" name={`placement-${i}`} checked={answers[i]===n} onChange={()=>{setAnswers(answers.map((v,j)=>j===i?n:v));setChecked(false);}}/>{option}</label>)}</fieldset>)}<button className="text-button" disabled={answers.includes(-1)} onClick={()=>setChecked(true)}>Show my starting point</button>{checked&&<div role="status"><h3>{score} of 4 correct</h3><p>{firstGap<0?'You know these basics. Review any lesson, or explore your life-situation journey.':`A useful place to start: ${data.units[firstGap]}.`}</p>{data.placement.map((q,i)=><p key={i}><strong>{i+1}. {answers[i]===q[2]?'Correct':'Worth revisiting'}:</strong> {(q[1] as string[])[q[2] as number]}</p>)}<button className="primary" disabled={busy} onClick={()=>onStart(firstLessons[Math.max(0,firstGap)])}>Open recommended lesson</button></div>}</div></details>
    <details className="learning-guidebook"><summary>Banking unit guidebooks · four original units</summary>{data.guides.map((guide,i)=><details className="guide-section" key={i}><summary>{data.units[i]}</summary><div className="guide-section-body"><p>{guide.sum}</p><ul>{guide.pts.map(point=><li key={point}>{point}</li>)}</ul><dl>{guide.words.map(([word,meaning])=><div key={word}><dt><strong>{word}</strong></dt><dd>{meaning}</dd></div>)}</dl><p>{guide.rem}</p></div></details>)}</details>
  </>;
}
