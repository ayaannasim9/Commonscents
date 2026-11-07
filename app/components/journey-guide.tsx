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
    <h2 id="journey-guide-title" className="sr-only">Help before you start</h2>
    <details className="guide-section"><summary>About this journey</summary><div className="guide-section-body"><p className="guide-welcome">{intro.welcome}</p><ul className="guide-outcomes">{intro.steps.map(step=><li key={step}><Check size={18}/><span>{step}</span></li>)}</ul><p className="guide-note">{intro.note}</p></div></details>
    <details className="guide-section"><summary>Money words explained <span>Debit, credit, investments and more</span></summary><div className="guide-section-body">
    <label className="word-search" htmlFor="money-word-search"><Search size={20}/><span className="sr-only">Search money terms</span><input id="money-word-search" type="search" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search a word, such as debit or bonds"/></label>
    <div className="money-terms">{terms.map(term=><details className="money-term" key={term.id}><summary>{term.term}<ChevronDown size={18}/></summary><div><p>{term.meaning}</p><p className="term-example"><strong>For example</strong>{term.example}</p><a href={term.source.url} target="_blank" rel="noreferrer">Read the source <ExternalLink size={14}/><span className="sr-only">: {term.source.title}, opens in a new tab</span></a></div></details>)}</div>
    {!terms.length&&<p role="status" className="empty-terms">No matching words yet. Try “card”, “saving” or “payment”.</p>}
    {!search&&<button className="guide-toggle" aria-expanded={showAll} onClick={()=>setShowAll(!showAll)}>{showAll?'Show the six starting terms':`See all ${guide.terms.length} money terms`}<ChevronDown size={18}/></button>}
    </div></details>
    <details className="guide-section"><summary>Banking on a screen or in a branch</summary><div className="guide-section-body"><p>You do not have to be confident with an app to start learning. Choose the way you feel comfortable asking for help.</p><div className="banking-comparison"><div><h3>On your phone or computer</h3><p>Your balance shows how much money is in the account. Your transactions or statement show money coming in and going out.</p><p>Use your bank’s official app or website. If a payment is unfamiliar, use its help options to ask about it.</p></div><div><h3>With someone at your bank</h3><p>You can ask someone to explain your balance or help you read a statement. Take a note of the payment you want to ask about.</p><p>Try saying: “I’m learning to manage this myself. Please explain it one step at a time.”</p></div></div><p>Never share your PIN or full password. You can pause and ask for an explanation before making a decision.</p></div></details>
    <details className="guide-section"><summary>Protect yourself from scams</summary><div className="scam-intro"><ShieldCheck size={30}/><div><h3>Keep your money safe</h3><p>Anyone can be targeted by a scam. Learn how to pause, check a request and get help. This lesson is available from every journey.</p><button className="primary" onClick={onScamLesson} disabled={busy||!available}>Learn about scam protection</button><a href="https://www.fca.org.uk/consumers/banking-online-account-scams" target="_blank" rel="noreferrer">Already worried? Read what to do <ExternalLink size={14}/></a></div></div>
    </details>
    <p className="guide-source-note">UK explanations · sources checked {guide.reviewedAt}. Learning information, not a recommendation to borrow or invest.</p>
  </section>;
}
