'use client';
import { useState } from 'react';
import { BookOpen, Check, ChevronDown, ExternalLink, Search, ShieldCheck } from 'lucide-react';
import guide from '@/content/money-guide.json';
import type { Journey } from '@/lib/types';
export default function JourneyGuide({journey,onScamLesson,busy,available}: {journey:Journey;onScamLesson:()=>void;busy:boolean;available:boolean}) {
  const [query,setQuery] = useState('');
  const [showAll,setShowAll] = useState(false);
  const intro = guide.journeys[journey.id as keyof typeof guide.journeys];
  if (!intro) return null;
  const search=query.trim().toLowerCase();
  const terms=search ? guide.terms.filter(t=>`${t.term} ${t.meaning} ${t.example}`.toLowerCase().includes(search)) : guide.terms.slice(0,showAll?undefined:6);
  return <section className="journey-guide" aria-labelledby="journey-guide-title">
    <div className="guide-heading"><span className="guide-icon"><BookOpen size={26}/></span><div><span className="eyebrow">BEFORE YOU START · COME BACK ANYTIME</span><h2 id="journey-guide-title">{intro.heading}</h2></div></div>
    <p className="guide-welcome">{intro.welcome}</p>
    <ul className="guide-outcomes">{intro.steps.map(step=><li key={step}><Check size={18}/><span>{step}</span></li>)}</ul>
    <p className="guide-note">{intro.note}</p><a className="guide-path-link" href="#learning-path">Go to the lessons</a>
    <div className="money-words-heading"><h3>Money words, explained</h3><span>Tap a word to read more</span></div>
    <label className="word-search" htmlFor="money-word-search"><Search size={20}/><span className="sr-only">Search money terms</span><input id="money-word-search" type="search" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search a word, such as debit or bonds"/></label>
    <div className="money-terms">{terms.map(term=><details className="money-term" key={term.id}><summary>{term.term}<ChevronDown size={18}/></summary><div><p>{term.meaning}</p><p className="term-example"><strong>For example</strong>{term.example}</p><a href={term.source.url} target="_blank" rel="noreferrer">Read the source <ExternalLink size={14}/><span className="sr-only">: {term.source.title}, opens in a new tab</span></a></div></details>)}</div>
    {!terms.length&&<p role="status" className="empty-terms">No matching words yet. Try “card”, “saving” or “payment”.</p>}
    {!search&&<button className="guide-toggle" aria-expanded={showAll} onClick={()=>setShowAll(!showAll)}>{showAll?'Show the six starting terms':`See all ${guide.terms.length} money terms`}<ChevronDown size={18}/></button>}
    <div className="scam-intro"><ShieldCheck size={30}/><div><h3>Keep your money safe</h3><p>Anyone can be targeted by a scam. Learn how to pause, check a request and get help. This lesson is available from every journey.</p><button className="primary" onClick={onScamLesson} disabled={busy||!available}>Learn about scam protection</button><a href="https://www.fca.org.uk/consumers/banking-online-account-scams" target="_blank" rel="noreferrer">Already worried? Read what to do <ExternalLink size={14}/></a></div></div>
    <p className="guide-source-note">UK explanations · sources checked {guide.reviewedAt}. Learning information, not a recommendation to borrow or invest.</p>
  </section>;
}
