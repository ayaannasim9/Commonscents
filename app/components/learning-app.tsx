'use client';
import { useEffect, useRef, useState } from 'react';
import { ArrowRight, ArrowDown, BookOpen, Check, ChevronRight, Flame, Leaf, LockKeyhole, Map, Sparkles, Sprout, GraduationCap, Wallet, BriefcaseBusiness, LifeBuoy, ExternalLink, Star, Target, Trophy, X, Zap, RotateCcw, Gem, Flag } from 'lucide-react';
import type { LearningState, Lesson, Question } from '@/lib/types';
type Feedback = { correct: boolean; correctIndex: number; explanation: string };
type Result = { score: number; total: number; passed: boolean; awarded: number };
import { journeyOptions, previewLessons } from '@/lib/journey-preview';
import JourneyGuide from './journey-guide';
import StartingPoint from './starting-point';
import ExerciseChoices from './exercise-choices';
import BankingGuide from './banking-guide';
function Penny({ celebrating = false }: { celebrating?: boolean }) {
  return <svg className={`penny ${celebrating ? 'celebrating' : ''}`} viewBox="0 0 100 110" aria-hidden="true"><ellipse cx="50" cy="103" rx="30" ry="6" fill="rgba(0,0,0,.15)"/><circle cx="50" cy="52" r="42" fill="#ffc72c" stroke="#c98f00" strokeWidth="6"/><circle cx="50" cy="52" r="31" fill="none" stroke="#c98f00" strokeWidth="3"/><path d="M14 42q36-26 72 0" fill="none" stroke="#5a287d" strokeWidth="10" strokeLinecap="round"/><circle cx="38" cy="54" r="6" fill="#fff"/><circle cx="62" cy="54" r="6" fill="#fff"/><circle cx="39" cy="55" r="3" fill="#3c1053"/><circle cx="63" cy="55" r="3" fill="#3c1053"/><path d="M36 68q14 13 28 0" fill="none" stroke="#3c1053" strokeWidth="5" strokeLinecap="round"/></svg>;
}
async function api(body: object) {
  const response = await fetch('/api/learn', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Something went wrong. Please retry.');
  return data;
}
export default function LearningApp({initial}: {initial: LearningState}) {
  const [state,setState] = useState(initial);
  const [view,setView] = useState<'learn'|'progress'|'library'>('learn');
  const [lesson,setLesson] = useState<Lesson|null>(null);
  const [questions,setQuestions] = useState<Question[]>([]);
  const [step,setStep] = useState(-1);
  const [selected,setSelected] = useState<number|null>(null);
  const [feedback,setFeedback] = useState<Feedback|null>(null);
  const [answers,setAnswers] = useState<number[]>([]);
  const [result,setResult] = useState<Result|null>(null);
  const [attemptId,setAttemptId] = useState('');
  const [busy,setBusy] = useState(false);
  const [error,setError] = useState('');
  const [selectedNode,setSelectedNode] = useState<string|null>(null);
  const [readingStep,setReadingStep] = useState(0);
  const contentRef = useRef<HTMLElement>(null);
  const feedbackRef = useRef<HTMLDivElement>(null);
  useEffect(()=>{if(feedback)feedbackRef.current?.focus();},[feedback]);
  const screenKey = `${lesson?.id ?? "path"}:${readingStep}:${step}:${result?.score ?? ""}:${view}:${state.activeJourney}`;
  const previousScreen = useRef(screenKey);
  useEffect(() => {
    if (previousScreen.current === screenKey) return;
    previousScreen.current = screenKey;
    contentRef.current?.querySelector<HTMLElement>('h2')?.focus({preventScroll:true});
    document.getElementById('s-learn')?.scrollIntoView({block:'start',behavior:'instant'});
  }, [screenKey]);
  const [showJourneys,setShowJourneys] = useState(false);


  const journeys = state.journeys.length ? state.journeys : journeyOptions;
  const journey = journeys.find(j => j.id === state.activeJourney) || journeys.find(j => j.id === 'independent') || journeys[0];
  const calm = journey.id === 'bills';
  const scamLesson = state.lessons.find(l=>l.id==='own-scams');
  const lessons = (state.lessons.length ? state.lessons : previewLessons).filter(l => l.journey_id === journey.id).map(l => ({...l,position:l.journey_position ?? l.position}));
  const journeyProgress = {...state.progress, completed:state.progress.completed.filter(id => lessons.some(l => l.id === id))};
  const next = lessons.find(l => !journeyProgress.completed.includes(l.id));
  const percent = lessons.length ? Math.round(journeyProgress.completed.length / lessons.length * 100) : 0;
  const readingCards = lesson?.reading_cards?.length ? lesson.reading_cards : (lesson?.reading.match(/[^.!?]+[.!?]+(?: |$)|[^.!?]+$/g) || []).reduce<string[]>((cards, sentence, i) => { const index = Math.floor(i / 2); cards[index] = (cards[index] || '') + sentence; return cards; }, []);
  async function chooseJourney(id: string) {
    setBusy(true); setError('');
    try { const data = await api({action:'journey',journeyId:id}); if (data.state.error) throw new Error(data.state.error); setState(data.state); setShowJourneys(false); setSelectedNode(null); setView('learn'); }
    catch(e) { setError(e instanceof Error ? e.message : 'Could not switch journey.'); }
    finally { setBusy(false); }
  }
  function jumpToCurrent() { document.getElementById(`node-${next?.id || lessons[0].id}`)?.scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'center'}); }
  async function start(l: Lesson) {
    if (state.error) { document.getElementById('setup')?.scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'}); return; }
    setBusy(true); setError('');
    try {
      const response = await fetch(`/api/learn?lesson=${encodeURIComponent(l.id)}`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.error);
      setQuestions(data.questions); setReadingStep(0); setLesson(l); setStep(-1); setAnswers([]); setSelected(null); setFeedback(null); setResult(null); setAttemptId(crypto.randomUUID());
    } catch(e) { setError(e instanceof Error ? e.message : 'Could not load lesson.'); }
    finally { setBusy(false); }
  }
  async function check() {
    if (selected === null) return;
    setBusy(true); setError('');
    try { setFeedback(await api({action:'check',questionId:questions[step].id,answer:selected})); setAnswers([...answers,selected]); }
    catch(e) { setError(e instanceof Error ? e.message : 'Could not check answer.'); }
    finally { setBusy(false); }
  }
  async function advance() {
    if (step < questions.length - 1) { setStep(step+1); setSelected(null); setFeedback(null); return; }
    setBusy(true); setError('');
    try {
      const data = await api({action:'complete',lessonId:lesson!.id,answers,attemptId});
      setResult(data); setState(data.state);
    } catch(e) { setError(e instanceof Error ? e.message : 'Could not save progress.'); }
    finally { setBusy(false); }
  }
  if (lesson) return <div className="lesson-shell">
    <header className="lesson-top"><button aria-label="Exit lesson" className="icon-button" disabled={busy} onClick={()=>{setLesson(null);setError('');}}><X/></button><div className="progress-track" role="progressbar" aria-label="Practice questions completed" aria-valuemin={0} aria-valuemax={questions.length} aria-valuenow={result?questions.length:Math.max(0,step+(feedback?1:0))}><span style={{width:result?'100%':`${Math.max(0,step+ (feedback?1:0))/questions.length*100}%`}}/></div><span className="xp-label">{calm?<a className="lesson-help" href="https://www.moneyhelper.org.uk/en/money-troubles/dealing-with-debt/debt-advice-locator" target="_blank" rel="noreferrer">Free support <ExternalLink size={14}/></a>:<><Zap size={19}/> {lesson.xp} XP</>}</span></header>
    <section className="exercise" ref={contentRef} id="main-content">
      {result ? <div className="result"><Penny celebrating={result.passed}/><span className="eyebrow">{calm?'ONE USEFUL STEP':result.passed?'A LITTLE WISER ALREADY':'EVERY TRY IS PROGRESS'}</span><h2 tabIndex={-1}>{calm?(result.passed?'You’ve taken a useful step.':'You can revisit this whenever you need.'):(result.passed?'Look at you grow.':'Let’s give it another go.')}</h2><p>{result.passed?'One more skill for your everyday life. Your progress is saved.':(journey.flexible?'You can review the explanation, try again or choose another topic.':'Get at least 2 out of 3 questions right to unlock the next lesson.')}</p><div className="result-stats"><div><strong>{result.score}/{result.total}</strong><span>Correct answers</span></div>{!calm&&<div><strong>+{result.awarded}</strong><span>XP earned</span></div>}</div><button className="primary" onClick={()=>result.passed?setLesson(null):start(lesson)} disabled={busy}>{result.passed?'Back to my path':'Try again'} <ArrowRight size={18}/></button>{!result.passed&&journey.flexible&&<button className="text-button" onClick={()=>setLesson(null)}>Choose another topic</button>}</div>
      : step === -1 ? <><span className="eyebrow">READ AT YOUR PACE · {readingStep+1} / {readingCards.length}</span><h2 tabIndex={-1}>{lesson.title}</h2><div className="coach-scene"><Penny/><div className="coach-bubble">{readingStep===0?(calm?'One thing at a time. You can pause whenever you need.':'Let’s make this money thing simple.'):'A little more knowledge. A lot more confidence.'}</div></div><div className="reading" key={readingStep}><span className="discovery-label"><Sparkles size={17}/> MONEY, MADE SIMPLE</span><p className="reading-copy">{readingCards[readingStep]}</p></div><div className="reading-dots" aria-label={`Discovery ${readingStep+1} of ${readingCards.length}`}>{readingCards.map((_,i)=><span key={i} className={i<=readingStep?'filled':''}/>)}</div><div className="exercise-actions">{readingStep>0&&<button className="reading-back" onClick={()=>setReadingStep(readingStep-1)}>Previous explanation</button>}<span>{readingStep===readingCards.length-1?'Next up: 3 quick questions':(calm?'No rush. Read at your own pace.':'Small steps. You’ve got this.')}</span><button className="primary" onClick={()=>readingStep<readingCards.length-1?setReadingStep(readingStep+1):setStep(0)}>{readingStep===readingCards.length-1?'Let’s practise':'Got it'} <ArrowRight size={18}/></button></div></>
      : <><span className="eyebrow">PUT IT INTO PRACTICE · QUESTION {step+1} / {questions.length}</span><h2 tabIndex={-1}>{questions[step].prompt}</h2><div className="question-coach"><Penny/><span>Choose the answer that makes the most sense.</span></div><ExerciseChoices key={questions[step].id} question={questions[step]} selected={selected} onSelect={setSelected} disabled={!!feedback||busy} correctIndex={feedback?.correctIndex}/><div className={`exercise-actions ${feedback?(feedback.correct?'feedback-good':'feedback-try'):''}`}>{feedback?<div role="status" tabIndex={-1} ref={feedbackRef} className="feedback"><strong>{feedback.correct?'Correct — nicely done!':'Not quite — here is the answer.'}</strong><p>{feedback.explanation}</p></div>:<span>Take your time. Every question is a step forward.</span>}<button className="primary" disabled={busy||selected===null} onClick={feedback?advance:check}>{busy?'Saving…':feedback?(step===questions.length-1?'Finish lesson':'Continue'):'Check answer'}<ArrowRight size={18}/></button></div></>}
      {result && lesson.checklist?.length ? <details className="real-world" open={!!result}><summary>Try this in real life · optional</summary><ul>{lesson.checklist.map(item=><li key={item}><Check size={16}/><span>{item}</span></li>)}</ul><p>Use your own notes. You do not need to enter private financial information here.</p></details> : null}
      {result && lesson.sources?.length ? <details className="lesson-sources"><summary>UK guidance & sources · checked {lesson.reviewed_at}</summary><p>Practice figures are examples. Eligibility and rules can vary by UK nation and personal circumstances.</p>{lesson.sources.map(source=><a key={source.url} href={source.url} target="_blank" rel="noreferrer">{source.title}<ExternalLink size={13}/></a>)}</details> : null}
      {error&&<p role="alert" className="error">{error}</p>}
    </section><footer className="lesson-footer"><Leaf size={16}/> Small lessons. Lasting confidence.</footer>
  </div>;
  return <div className="app-shell"><div className="learning-nav" role="group" aria-label="Learning views">{([{id:'learn',label:'My path'},{id:'progress',label:'My progress'},{id:'library',label:'All lessons'}] as const).map(item=><button key={item.id} className="text-button" aria-pressed={view===item.id} onClick={()=>setView(item.id)}>{item.label}</button>)}</div><div className="workspace">
    <section className="dashboard" ref={contentRef} id="main-content" tabIndex={-1}><div className="page-heading"><Penny/><div><span className="eyebrow">UK MONEY SKILLS</span><h2 tabIndex={-1}>{view==='learn'?journey.title:view==='progress'?'Your progress':'Lesson library'}</h2><p>{view==='learn'?journey.description:view==='progress'?'Your learning journey, at your pace.':'Find a topic you want to learn about.'}</p></div></div>
    <section className="journey-picker" aria-label="Choose your learning journey"><div className="journey-picker-heading"><p className="compact-progress"><strong>{percent}% complete</strong><span>{journeyProgress.completed.length} of {lessons.length} lessons</span></p><button className="text-button" aria-expanded={showJourneys} aria-controls="journey-options" onClick={()=>setShowJourneys(!showJourneys)}>{showJourneys?'Hide journeys':'Switch journey'}<ChevronRight size={17}/></button></div>{showJourneys&&<div className="journey-options" id="journey-options">{journeys.map((j,i)=>{const Icon=({university:GraduationCap,independent:Wallet,bills:LifeBuoy,'first-job':BriefcaseBusiness})[j.id as 'university'|'independent'|'bills'|'first-job'] || Map;const completed=state.progress.completed.filter(id=>state.lessons.some(l=>l.id===id&&l.journey_id===j.id)).length;return <button key={j.id} className={`journey-option ${j.id===journey.id?'chosen':''}`} disabled={busy||!!state.error} aria-pressed={j.id===journey.id} onClick={()=>chooseJourney(j.id)}><Icon size={26}/><strong>{j.title}</strong><span>{j.description}</span><small>{completed} / {(state.lessons.length?state.lessons:previewLessons).filter(l=>l.journey_id===j.id).length} lessons {j.flexible?'· Explore in any order':'· Guided path'}</small></button>;})}</div>}</section>
    {journey.id!=='banking-basics'&&<div className="banking-course-link"><BookOpen aria-hidden="true"/><div><strong>New to banking?</strong><p>Explore the original 10 lessons: accounts, the NatWest app, online banking and staying safe.</p></div><button className="text-button" disabled={busy||!!state.error} onClick={()=>chooseJourney('banking-basics')}>Open banking basics</button></div>}
    {calm&&<div className="support-banner"><LifeBuoy size={23}/><div><strong>Need help now? You do not have to finish a lesson first.</strong><p>For urgent bill problems or deadlines, seek free, confidential advice.</p></div><a href="https://www.moneyhelper.org.uk/en/money-troubles/dealing-with-debt/debt-advice-locator" target="_blank" rel="noreferrer">Find free advice <ExternalLink size={15}/></a></div>}
    {state.error&&<div id="setup" className="setup-banner"><div><strong>Connect your Supabase project to start learning</strong><p>{state.error} This is a layout preview; no progress is stored locally.</p></div><button className="text-button" onClick={()=>window.location.reload()}>Check connection <RotateCcw size={16}/></button></div>}
    {error&&<p className="error" role="alert">{error}</p>}
    <div className="dashboard-grid"><section className="main-column">
    {view==='learn'?<><section className="next-lesson" aria-labelledby="next-lesson-title"><div><span className="eyebrow">{next?'YOUR NEXT STEP':'JOURNEY COMPLETE'}</span><h2 id="next-lesson-title">{next?.title || 'Keep your skills fresh'}</h2><p>{next?`${next.minutes} minutes · Read, then practise at your pace.`:'You can revisit any lesson below.'}</p></div>{next&&<button className="primary" disabled={busy||!!state.error} onClick={()=>start(next)}>{busy?'Loading…':journeyProgress.completed.length?'Continue learning':'Start learning'}<ArrowRight size={18}/></button>}</section>{journey.id==='banking-basics'&&<BankingGuide onStart={id=>{const l=lessons.find(l=>l.id===id);if(l)start(l);}} busy={busy||!!state.error}/>}<StartingPoint journeys={journeys} busy={busy||!!state.error} onChoose={chooseJourney}/><details className="learning-guidebook"><summary>📒 Guidebook · money basics and staying safe</summary><JourneyGuide key={journey.id} journey={journey} busy={busy} available={!!scamLesson&&!state.error} onScamLesson={()=>{if(scamLesson)start(scamLesson);}}/></details><div className="path-intro" id="learning-path"><div><h2>Your lesson path</h2><p>{journey.flexible?'You can also choose any topic below.':'Complete each lesson to unlock the next.'}</p></div></div>
    <div className="learning-trail">{journey.units.map((unitTitle,unit)=>{
      const unitLessons=lessons.some(l=>l.unit_index!=null)?lessons.filter(l=>l.unit_index===unit):lessons.slice(unit*2,unit*2+2);
      const unitComplete=unitLessons.length>0&&unitLessons.every(l=>journeyProgress.completed.includes(l.id));
      return <section className={`trail-unit trail-unit-${unit}`} key={unit} aria-label={`Unit ${unit+1}`}><header className="trail-heading"><div><span>UNIT {unit+1} · {journey.id==='first-job'?'WORK & PAY':journey.id==='university'?'STUDENT LIFE':journey.id==='bills'?'BILLS & SUPPORT':'EVERYDAY MONEY'}</span><h3>{unitTitle}</h3></div><span className="unit-progress">{unitLessons.filter(l=>journeyProgress.completed.includes(l.id)).length}/{unitLessons.length} <Flag size={20}/></span></header><div className={`trail-stage ${unitLessons.length===1?"single-lesson-unit":""}`}>
      <svg className="trail-line" viewBox="0 0 440 540" preserveAspectRatio="none" aria-hidden="true"><path d="M220 0 C220 60 140 55 140 115 S300 185 300 270 S220 355 220 450 L220 540" fill="none" stroke="#eee8f5" strokeWidth="14" strokeLinecap="round" strokeDasharray="3 24"/></svg>
      {unitLessons.map((l,i)=>{
        const done=journeyProgress.completed.includes(l.id); const unlocked=journey.flexible||l.position===1||journeyProgress.completed.includes(lessons[l.position-2]?.id); const current=next?.id===l.id; const expanded=selectedNode===l.id;
        return <div id={`node-${l.id}`} className={`trail-stop stop-${i} ${current?'current':''}`} key={l.id}>
          {current&&<span className="start-bubble">{busy?'LOADING…':journey.flexible?'EXPLORE':'START HERE'}</span>}
          <button className={`path-node ${done?'done':''} ${!unlocked?'locked':''}`} aria-label={`${done?'Review':unlocked?'Start':'Locked'}: ${l.title}`} aria-expanded={expanded} disabled={busy||!!state.error} onClick={()=>setSelectedNode(expanded?null:l.id)}>{done?<Check size={35}/>:unlocked?<Star size={35} fill="currentColor"/>:<LockKeyhole size={27}/>}</button><span className="path-caption">{l.title}</span>
          {expanded&&<div className="node-popover"><strong>{l.title}</strong><p>{unlocked?l.description:'Complete the previous lesson to unlock this step.'}</p>{unlocked&&<><small>{l.minutes} MIN{!calm&&` · ${l.xp} XP`}{done?' · COMPLETED':''}</small><button className="primary" disabled={busy} onClick={()=>start(l)}>{done?'Practise again':'Let’s go'}<ArrowRight size={16}/></button></>}</div>}
        </div>;
      })}
      <div className="unit-completion"><Trophy size={24}/><span>{unitComplete?'Unit complete — well done!':`Complete ${unitLessons.length} ${unitLessons.length===1?"lesson":"lessons"} to finish this unit`}</span></div></div></section>;
    })}<div className="path-finish"><Flag size={27}/><h3>Big confidence starts with small steps.</h3><p>{lessons.length} practical lessons. Skills you can use outside the app.</p><button className="text-button" onClick={jumpToCurrent}>{next?'Back to my next lesson':'Revisit the foundations'}<ArrowRight size={17}/></button></div></div>
</>:view==='progress'?<><div className="progress-hero"><Trophy size={40}/><h2>{journeyProgress.completed.length? 'A strong start, and more to come.':'Your first step is waiting.'}</h2><p>{calm?"A record of topics you have explored. There is no deadline to finish.":"Complete lessons to earn XP and grow your streak."}</p><div className="result-stats">{!calm&&<div><strong>{state.progress.xp}</strong><span>Total XP</span></div>}<div><strong>{journeyProgress.completed.length}/{lessons.length}</strong><span>Lessons finished</span></div>{!calm&&<div><strong>{state.progress.streak}</strong><span>Day streak</span></div>}</div></div><h2 className="subheading">Milestones to grow into</h2>{[{title:'First little step',description:'Complete your first lesson',unlocked:journeyProgress.completed.length>=1},{title:'Finding your feet',description:'Complete two lessons in this journey',unlocked:journeyProgress.completed.length>=2},{title:'Ready for the next step',description:'Complete this journey',unlocked:journeyProgress.completed.length===lessons.length}].map(b=><div className="badge-card" key={b.title}><span className={b.unlocked?'badge earned':'badge'}>{b.unlocked?<Trophy/>:<LockKeyhole/>}</span><div><strong>{b.title}</strong><p>{b.description}</p></div><small>{b.unlocked?'EARNED':'TO UNLOCK'}</small></div>)}</>:<div className="library">{lessons.map(l=><article key={l.id}><span className="eyebrow">LESSON {l.position} · {l.minutes} MIN</span><h2>{l.title}</h2><p>{l.description}</p><button className="text-button" disabled={busy||!!state.error||(!journey.flexible&&l.position>1&&!journeyProgress.completed.includes(lessons[l.position-2].id))} onClick={()=>start(l)}>{journeyProgress.completed.includes(l.id)?'Review lesson':'Open lesson'}<ArrowRight size={17}/></button></article>)}</div>}
    </section></div><footer className="dashboard-footer">Educational examples, not personal financial advice.</footer>
    </section></div></div>;
}
