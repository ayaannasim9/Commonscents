'use client';
import { useEffect, useState } from 'react';
import { ArrowRight, ArrowDown, BookOpen, Check, ChevronRight, Flame, Leaf, LockKeyhole, Map, Sparkles, Sprout, GraduationCap, Wallet, BriefcaseBusiness, LifeBuoy, ExternalLink, Star, Target, Trophy, X, Zap, RotateCcw, Gem, Flag } from 'lucide-react';
import type { LearningState, Lesson, Question } from '@/lib/types';
type Feedback = { correct: boolean; correctIndex: number; explanation: string };
type Result = { score: number; total: number; passed: boolean; awarded: number };
import { journeyOptions, previewLessons } from '@/lib/journey-preview';
import JourneyGuide from './journey-guide';
function Penny({ celebrating = false }: { celebrating?: boolean }) {
  return <svg className={`penny ${celebrating ? 'celebrating' : ''}`} viewBox="0 0 180 180" fill="none" aria-hidden="true">
    <ellipse cx="88" cy="163" rx="53" ry="9" fill="#e9e1f2"/>
    <path d="M55 136L45 156M113 138L125 157" stroke="#401664" strokeWidth="13" strokeLinecap="round"/>
    <path d={celebrating?'M39 94L16 54M139 94L162 54':'M39 94L18 109M139 94L160 79'} stroke="#7545b2" strokeWidth="12" strokeLinecap="round"/>
    <rect x="41" y="24" width="104" height="119" rx="43" fill="#401664"/>
    <rect x="33" y="19" width="104" height="119" rx="43" fill="#9b6bdf"/>
    <rect x="43" y="29" width="84" height="98" rx="35" fill="#bd98ef"/>
    <path d="M67 42Q82 31 99 42" stroke="#e6d4ff" strokeWidth="7" strokeLinecap="round"/>
    <ellipse cx="68" cy="73" rx="6" ry="8" fill="#35134f"/><ellipse cx="103" cy="73" rx="6" ry="8" fill="#35134f"/>
    <circle cx="56" cy="89" r="7" fill="#ec7fba"/><circle cx="115" cy="89" r="7" fill="#ec7fba"/>
    <path d="M75 91Q86 105 98 91" stroke="#35134f" strokeWidth="5" strokeLinecap="round"/>
    <path d="M83 111H94M87 107V117" stroke="#7545b2" strokeWidth="3" strokeLinecap="round"/>
    <path d="M151 25V40M144 32H158M21 35V45M16 40H26" stroke="#f4b749" strokeWidth="4" strokeLinecap="round"/>
  </svg>;
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
  useEffect(() => { window.scrollTo({top:0,behavior:'instant'}); }, [lesson?.id, readingStep, step, result]);
  const [showJourneys,setShowJourneys] = useState(false);
  const [largeText,setLargeText] = useState(false);
  useEffect(()=>{ document.documentElement.dataset.largeText=String(largeText); return ()=>{delete document.documentElement.dataset.largeText;}; },[largeText]);
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
  function jumpToCurrent() { document.getElementById(`node-${next?.id || lessons[0].id}`)?.scrollIntoView({behavior:'smooth',block:'center'}); }
  async function start(l: Lesson) {
    if (state.error) { document.getElementById('setup')?.scrollIntoView({behavior:'smooth'}); return; }
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
    <header className="lesson-top"><button aria-label="Exit lesson" className="icon-button" disabled={busy} onClick={()=>{setLesson(null);setError('');}}><X/></button><div className="progress-track"><span style={{width:result?'100%':`${Math.max(0,step+ (feedback?1:0))/questions.length*100}%`}}/></div><button className="text-size-control lesson-text-size" aria-pressed={largeText} onClick={()=>setLargeText(!largeText)}><span aria-hidden="true">Aa</span>{largeText?"Standard text":"Larger text"}</button><span className="xp-label">{calm?<a className="lesson-help" href="https://www.moneyhelper.org.uk/en/money-troubles/dealing-with-debt/debt-advice-locator" target="_blank" rel="noreferrer">Free support <ExternalLink size={14}/></a>:<><Zap size={19}/> {lesson.xp} XP</>}</span></header>
    <main className="exercise">
      {result ? <div className="result"><Penny celebrating={result.passed}/><span className="eyebrow">{calm?'ONE USEFUL STEP':result.passed?'A LITTLE WISER ALREADY':'EVERY TRY IS PROGRESS'}</span><h1>{calm?(result.passed?'You’ve taken a useful step.':'You can revisit this whenever you need.'):(result.passed?'Look at you grow.':'Let’s give it another go.')}</h1><p>{result.passed?'One more skill for your everyday life. Your progress is saved.':(journey.flexible?'You can review the explanation, try again or choose another topic.':'Get at least 2 out of 3 questions right to unlock the next lesson.')}</p><div className="result-stats"><div><strong>{result.score}/{result.total}</strong><span>Correct answers</span></div>{!calm&&<div><strong>+{result.awarded}</strong><span>XP earned</span></div>}</div><button className="primary" onClick={()=>result.passed?setLesson(null):start(lesson)} disabled={busy}>{result.passed?'Back to my path':'Try again'} <ArrowRight size={18}/></button>{!result.passed&&journey.flexible&&<button className="text-button" onClick={()=>setLesson(null)}>Choose another topic</button>}</div>
      : step === -1 ? <><span className="eyebrow">READ AT YOUR PACE · {readingStep+1} / {readingCards.length}</span><h1>{lesson.title}</h1><div className="coach-scene"><Penny/><div className="coach-bubble">{readingStep===0?(calm?'One thing at a time. You can pause whenever you need.':'Let’s make this money thing simple.'):'A little more knowledge. A lot more confidence.'}</div></div><div className="reading" key={readingStep}><span className="discovery-label"><Sparkles size={17}/> MONEY, MADE SIMPLE</span><p>{readingCards[readingStep]}</p></div><div className="reading-dots" aria-label={`Discovery ${readingStep+1} of ${readingCards.length}`}>{readingCards.map((_,i)=><span key={i} className={i<=readingStep?'filled':''}/>)}</div><div className="exercise-actions">{readingStep>0&&<button className="reading-back" onClick={()=>setReadingStep(readingStep-1)}>Previous explanation</button>}<span>{readingStep===readingCards.length-1?'Next up: 3 quick questions':(calm?'No rush. Read at your own pace.':'Small steps. You’ve got this.')}</span><button className="primary" onClick={()=>readingStep<readingCards.length-1?setReadingStep(readingStep+1):setStep(0)}>{readingStep===readingCards.length-1?'Let’s practise':'Got it'} <ArrowRight size={18}/></button></div></>
      : <><span className="eyebrow">PUT IT INTO PRACTICE · QUESTION {step+1} / {questions.length}</span><h1>{questions[step].prompt}</h1><div className="question-coach"><Penny/><span>Choose the answer that makes the most sense.</span></div><div className="answers" role="group" aria-label="Answer choices">{questions[step].options.map((option,i)=><button key={option} aria-pressed={selected===i} disabled={!!feedback||busy} className={`answer ${selected===i?'selected':''} ${feedback?.correctIndex===i?'correct':''} ${feedback && selected===i && !feedback.correct?'incorrect':''}`} onClick={()=>setSelected(i)}><span className="answer-letter">{String.fromCharCode(65+i)}</span>{option}{feedback?.correctIndex===i&&<Check size={21}/>}</button>)}</div><div className={`exercise-actions ${feedback?(feedback.correct?'feedback-good':'feedback-try'):''}`}>{feedback?<div role="status" className="feedback"><strong>{feedback.correct?'Nicely done!':'You’re learning. That’s what counts.'}</strong><p>{feedback.explanation}</p></div>:<span>Take your time. Every question is a step forward.</span>}<button className="primary" disabled={busy||selected===null} onClick={feedback?advance:check}>{busy?'Saving…':feedback?(step===questions.length-1?'Finish lesson':'Continue'):'Check answer'}<ArrowRight size={18}/></button></div></>}
      {(step === -1 || result) && lesson.checklist?.length ? <details className="real-world" open={!!result}><summary>Try this in real life · optional</summary><ul>{lesson.checklist.map(item=><li key={item}><Check size={16}/><span>{item}</span></li>)}</ul><p>Use your own notes. You do not need to enter private financial information here.</p></details> : null}
      {lesson.sources?.length ? <details className="lesson-sources"><summary>UK guidance & sources · checked {lesson.reviewed_at}</summary><p>Practice figures are examples. Eligibility and rules can vary by UK nation and personal circumstances.</p>{lesson.sources.map(source=><a key={source.url} href={source.url} target="_blank" rel="noreferrer">{source.title}<ExternalLink size={13}/></a>)}</details> : null}
      {error&&<p role="alert" className="error">{error}</p>}
    </main><footer className="lesson-footer"><Leaf size={16}/> Small lessons. Lasting confidence.</footer>
  </div>;
  return <div className="app-shell"><aside className="sidebar"><a className="brand" href="/"><span className="brand-icon"><Gem size={28}/></span>commonscents<span className="brand-dot">.</span></a><span className="nav-label">YOUR MONEY JOURNEY</span><nav>{([{id:'learn',label:'Learn',icon:Map},{id:'progress',label:'Achievements',icon:Trophy},{id:'library',label:'Lesson library',icon:BookOpen}] as const).map(item=><button key={item.id} className={view===item.id?'active':''} onClick={()=>{setView(item.id);setError('');}}><item.icon size={21}/>{item.label}{view===item.id&&<ChevronRight size={17}/>}</button>)}</nav><div className="sidebar-progress"><span className="eyebrow">YOUR JOURNEY PROGRESS</span><strong>{percent}%</strong><p>{journey.title}</p><div className="progress-track" role="progressbar" aria-label="Journey completion" aria-valuemin={0} aria-valuemax={100} aria-valuenow={percent}><span style={{width:`${percent}%`}}/></div><small>{journeyProgress.completed.length} of {lessons.length} lessons completed</small></div><div className="profile"><span className="avatar">Y</span><div><strong>Your learning space</strong><small>Demo learner</small></div><span className="online-dot"/></div></aside>
    <div className="workspace"><header className="topbar"><span>Personal finance <ChevronRight size={14}/> <strong>{view==='learn'?'My learning path':view==='progress'?'My progress':'Lesson library'}</strong></span><div className="top-stats"><button className="text-size-control" aria-pressed={largeText} onClick={()=>setLargeText(!largeText)}><span aria-hidden="true">Aa</span>{largeText?"Standard text":"Larger text"}</button>{calm?<span className="calm-label"><LifeBuoy size={19}/> At your pace</span>:<><span className="streak"><Flame size={20}/> {state.progress.streak} <small>day streak</small></span><span className="xp-label"><Zap size={20}/> {state.progress.xp} <small>total XP</small></span></>}</div></header>
    <main className="dashboard"><div className="page-heading"><div><span className="eyebrow">{calm?'PRACTICAL SUPPORT, ONE STEP AT A TIME':'YOUR DAILY DOSE OF MONEY CONFIDENCE'}</span><h1>{view==='learn'?(calm?'A little clarity. A manageable next step.':'Money skills for the life you’re living.'):view==='progress'?'Every little step adds up.':'A little knowledge goes a long way.'}</h1><p>{view==='learn'?journey.description:view==='progress'?'Your learning journey, all in one place.':'Explore the foundations of everyday money.'}</p></div><span className="course-pill"><span/> UK EDITION</span></div>
    <section className="journey-picker" aria-label="Choose your learning journey"><div className="journey-picker-heading"><div><span className="eyebrow">WHAT ARE YOU NAVIGATING?</span><h2>{journey.title}</h2></div><button className="text-button" aria-expanded={showJourneys} onClick={()=>setShowJourneys(!showJourneys)}>{showJourneys?'Hide journeys':'Switch journey'}<ChevronRight size={17}/></button></div>{showJourneys&&<div className="journey-options">{journeys.map((j,i)=>{const Icon=({university:GraduationCap,independent:Wallet,bills:LifeBuoy,'first-job':BriefcaseBusiness})[j.id as 'university'|'independent'|'bills'|'first-job'] || Map;const completed=state.progress.completed.filter(id=>state.lessons.some(l=>l.id===id&&l.journey_id===j.id)).length;return <button key={j.id} className={`journey-option ${j.id===journey.id?'chosen':''}`} disabled={busy||!!state.error} aria-pressed={j.id===journey.id} onClick={()=>chooseJourney(j.id)}><Icon size={26}/><strong>{j.title}</strong><span>{j.description}</span><small>{completed} / {(state.lessons.length?state.lessons:previewLessons).filter(l=>l.journey_id===j.id).length} lessons {j.flexible?'· Explore in any order':'· Guided path'}</small></button>;})}</div>}</section>
    {calm&&<div className="support-banner"><LifeBuoy size={23}/><div><strong>Need help now? You do not have to finish a lesson first.</strong><p>For urgent bill problems or deadlines, seek free, confidential advice.</p></div><a href="https://www.moneyhelper.org.uk/en/money-troubles/dealing-with-debt/debt-advice-locator" target="_blank" rel="noreferrer">Find free advice <ExternalLink size={15}/></a></div>}
    {state.error&&<div id="setup" className="setup-banner"><div><strong>Connect your Supabase project to start learning</strong><p>{state.error} This is a layout preview; no progress is stored locally.</p></div><button className="text-button" onClick={()=>window.location.reload()}>Check connection <RotateCcw size={16}/></button></div>}
    {error&&<p className="error" role="alert">{error}</p>}
    <div className="dashboard-grid"><section className="main-column">
    {view==='learn'?<><JourneyGuide key={journey.id} journey={journey} busy={busy} available={!!scamLesson&&!state.error} onScamLesson={()=>{if(scamLesson)start(scamLesson);}}/><div className="path-intro" id="learning-path"><div><span className="eyebrow">YOUR JOURNEY · UK MONEY SKILLS</span><h2>{journey.title}</h2><p>{journey.flexible?'Choose any topic that helps you today.':'Follow the path, one practical decision at a time.'}</p></div><button className="jump-button" onClick={jumpToCurrent} aria-label="Jump to current lesson"><ArrowDown size={20}/></button></div>
    <div className="learning-trail">{journey.units.map((unitTitle,unit)=>{
      const unitLessons=lessons.slice(unit*2,unit*2+2);
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
      <div className={`trail-coach coach-${unit}`}><Penny celebrating={unitComplete}/><span>{calm?'One step at a time.':unitComplete?'You did that!':['Your future self is cheering.','Little by little adds up.','Pause. Check. Stay in control.'][unit]}</span></div>
      <div className={`unit-milestone ${unitComplete?'earned':''}`}><div><Trophy size={31}/></div><strong>{calm?(unitComplete?'Topics explored':'Useful skills to explore'):(unitComplete?'Unit complete!':'Your next milestone')}</strong><span>{calm?'Come back whenever it helps.':unitComplete?'Keep that momentum going.':`Finish ${unitLessons.length===1?'this lesson':'both lessons'} to earn your trophy.`}</span></div>
      </div></section>;
    })}<div className="path-finish"><Flag size={27}/><h3>Big confidence starts with small steps.</h3><p>{lessons.length} practical lessons. Skills you can use outside the app.</p><button className="text-button" onClick={jumpToCurrent}>{next?'Back to my next lesson':'Revisit the foundations'}<ArrowRight size={17}/></button></div></div>
</>:view==='progress'?<><div className="progress-hero"><Trophy size={40}/><h2>{journeyProgress.completed.length? 'A strong start, and more to come.':'Your first step is waiting.'}</h2><p>{calm?"A record of topics you have explored. There is no deadline to finish.":"Complete lessons to earn XP and grow your streak."}</p><div className="result-stats">{!calm&&<div><strong>{state.progress.xp}</strong><span>Total XP</span></div>}<div><strong>{journeyProgress.completed.length}/{lessons.length}</strong><span>Lessons finished</span></div>{!calm&&<div><strong>{state.progress.streak}</strong><span>Day streak</span></div>}</div></div><h2 className="subheading">Milestones to grow into</h2>{[{title:'First little step',description:'Complete your first lesson',unlocked:journeyProgress.completed.length>=1},{title:'Finding your feet',description:'Complete two lessons in this journey',unlocked:journeyProgress.completed.length>=2},{title:'Ready for the next step',description:'Complete this journey',unlocked:journeyProgress.completed.length===lessons.length}].map(b=><div className="badge-card" key={b.title}><span className={b.unlocked?'badge earned':'badge'}>{b.unlocked?<Trophy/>:<LockKeyhole/>}</span><div><strong>{b.title}</strong><p>{b.description}</p></div><small>{b.unlocked?'EARNED':'TO UNLOCK'}</small></div>)}</>:<div className="library">{lessons.map(l=><article key={l.id}><span className="eyebrow">LESSON {l.position} · {l.minutes} MIN</span><h2>{l.title}</h2><p>{l.description}</p><button className="text-button" disabled={busy||!!state.error||(!journey.flexible&&l.position>1&&!journeyProgress.completed.includes(lessons[l.position-2].id))} onClick={()=>start(l)}>{journeyProgress.completed.includes(l.id)?'Review lesson':'Open lesson'}<ArrowRight size={17}/></button></article>)}</div>}
    </section><aside className="right-column">{calm?<div className="goal-card"><div className="card-heading"><h3>Your pace is the right pace</h3><LifeBuoy size={21}/></div><p>Open any topic. Pause whenever you need. There is no daily target for this journey.</p><a className="text-button" href="https://www.moneyhelper.org.uk/en/money-troubles/dealing-with-debt/debt-advice-locator" target="_blank" rel="noreferrer">Free debt advice <ExternalLink size={14}/></a></div>:<div className="goal-card"><div className="card-heading"><h3>Daily quest</h3><Target size={21}/></div><p>Earn 30 XP. Keep your momentum going.</p><div className="goal-numbers"><strong>{Math.min(state.progress.todayXp,30)} <span>/ 30 XP</span></strong><span>{state.progress.todayXp>=30?'Complete!':'You’ve got this'}</span></div><div className="progress-track"><span style={{width:`${Math.min(state.progress.todayXp/30*100,100)}%`}}/></div><small>{state.progress.todayXp>=30?'Daily goal reached. Nice work.':'Finish a new lesson to reach your goal.'}</small></div>}<div className="journey-card"><div className="card-heading"><h3>Growing your confidence</h3><Leaf size={20}/></div><div className="progress-ring" style={{background:`conic-gradient(#7836b0 ${percent}%, #eee8f5 0)`}}><div><strong>{percent}%</strong><small>of this journey</small></div></div><p>{journeyProgress.completed.length} lessons down.<br/>{lessons.length-journeyProgress.completed.length} little steps ahead.</p></div><div className="tip-card"><span className="eyebrow"><Sparkles size={15}/> A PENNY FOR YOUR THOUGHTS</span><blockquote>“You don’t need to know everything to take the first step.”</blockquote><span>A good place to start? Right here.</span></div><div className="education-note"><BookOpen size={16}/><p>Built for learning, at your pace.<br/>Examples are educational, not personal financial advice.</p></div></aside></div><footer className="dashboard-footer"><span><Sprout size={16}/> A little wiser, every day.</span><span>Your money. Your pace. Your progress.</span></footer>
    </main></div></div>;
}
