const $=s=>document.querySelector(s),R=document.documentElement;
const tabs=[["start","🚀","Start"],["dashboard","💷","Dashboard"],["future","🔮","Future"],["wrapped","🎉","Wrapped"],["learn","🎓","Learn"],["support","🧭","Support"],["report","📬","Report"]];
const nav=$("#nav");
tabs.forEach(([id,i,l],n)=>{const b=document.createElement("button");b.id="t-"+id;b.setAttribute("role","tab");b.setAttribute("aria-selected",n==0);b.setAttribute("aria-controls","s-"+id);b.tabIndex=n===0?0:-1;b.innerHTML='<span class="i" aria-hidden="true">'+i+'</span>'+l;b.onclick=()=>go(id);nav.appendChild(b)});
function go(id){history.replaceState(null,"","#"+id);tabs.forEach(([t])=>{$("#s-"+t).hidden=t!=id;$("#t-"+t).setAttribute("aria-selected",t==id);$("#t-"+t).tabIndex=t===id?0:-1});if(id=="future")drawTl();if(id=="support")sup();$("#main").focus({preventScroll:true});window.scrollTo({top:0})}
document.addEventListener("click",e=>{const g=e.target.closest("[data-go]");if(g)go(g.dataset.go)});
nav.addEventListener("keydown",e=>{const b=[...nav.children],i=b.indexOf(document.activeElement);let next;if(e.key==="ArrowRight")next=(i+1)%b.length;if(e.key==="ArrowLeft")next=(i-1+b.length)%b.length;if(e.key==="Home")next=0;if(e.key==="End")next=b.length-1;if(next!==undefined){e.preventDefault();b.forEach((tab,n)=>tab.tabIndex=n===next?0:-1);b[next].focus()}});

/* display settings */
const sizes=[["18px","normal"],["22px","large"],["26px","extra large"]];let si=0;
$("#tsz").onclick=()=>{si=(si+1)%3;R.style.setProperty("--fs",sizes[si][0]);$("#tsz").setAttribute("aria-label","Change text size. Current: "+sizes[si][1])};
$("#thc").onclick=e=>{const on=e.target.getAttribute("aria-pressed")!="true";e.target.setAttribute("aria-pressed",on);on?R.dataset.contrast="high":delete R.dataset.contrast};
$("#tdk").onclick=e=>{const on=e.target.getAttribute("aria-pressed")!="true";e.target.setAttribute("aria-pressed",on);R.dataset.theme=on?"dark":"light"};

/* onboarding */
const Q=[
["How easy do you find managing money?",[["😊","Easy"],["😐","Okay"],["😟","Hard"]]],
["What worries you most about your finances?",[["💡","Bills going up"],["🛟","Not enough savings"],["💳","Debt"],["🌅","Retirement"]]],
["What is your main financial goal?",[["🛟","Build savings"],["🏡","Buy a home"],["✂️","Cut spending"],["📈","Earn more"]]],
["Expecting any big life changes in the next 12 months?",[["👶","New baby"],["💼","New job"],["🏠","Moving"],["➖","None"]]],
["If a surprise £500 bill came tomorrow, how would you pay?",[["💷","From savings"],["💳","Credit card"],["🤝","Borrow from family"],["😬","I’m not sure"]]],
["Do you rent, own, or live with family?",[["🔑","Rent"],["🏡","Own"],["👪","Live with family"]]],
["Do you have any dependants?",[["👧","Yes"],["🙂","No"]]],
["Do you own or regularly use a vehicle?",[["🚗","Yes"],["🚌","No"]]],
["How would you like things explained?",[["💬","Simple"],["📚","Detailed"]]],
["Would you like a printed report posted to you each year?",[["📬","Yes please"],["📱","No, digital only"]]]];
let step=-1;const ans=[];
function ob(){const el=$("#ob");
if(step<0){el.innerHTML='<div class="card bank"><span class="big" aria-hidden="true">🏦</span><div><h3 style="margin:0">Connect your NatWest account</h3><p class="lead" style="margin:.2rem 0 .8rem">Read-only. We can see your money, but we can’t move it. You can disconnect any time.</p><button class="btn pri" id="conn">🔒 Connect NatWest</button></div></div>';$("#conn").onclick=()=>{step=0;ob()};return}
if(step>=Q.length){el.innerHTML='<div class="card" style="text-align:center"><div style="font-size:4rem" aria-hidden="true">✅</div><h3>All done. Well done!</h3><p class="lead">We’re building your future timelines.</p><button class="btn pri" data-go="future">🔮 See my future</button></div>';$("#main").focus({preventScroll:true});return}
const [q,o]=Q[step];
el.innerHTML='<p id="pg" style="font-weight:800;margin:0">Question '+(step+1)+' of 10</p><div class="bar" role="progressbar" aria-valuemin="0" aria-valuemax="10" aria-valuenow="'+step+'" aria-labelledby="pg"><i style="width:'+(step*10)+'%"></i></div><div class="card"><h3 id="q" style="margin-top:0;font-size:1.4rem" tabindex="-1">'+q+'</h3><div class="opts" role="group" aria-labelledby="q">'+o.map((x,i)=>'<button class="opt" aria-pressed="'+(ans[step]===i)+'" data-i="'+i+'"><span class="i" aria-hidden="true">'+x[0]+'</span>'+x[1]+'</button>').join("")+'</div></div><div style="display:flex;gap:.7rem;flex-wrap:wrap"><button class="btn ghost" id="bk"'+(step==0?' disabled':'')+'>← Back</button><button class="btn pri" id="nx" disabled>Next →</button></div>';
if(ans[step]!==undefined)$("#nx").disabled=false;
el.querySelectorAll(".opt").forEach(b=>b.onclick=()=>{ans[step]=+b.dataset.i;el.querySelectorAll(".opt").forEach(x=>x.setAttribute("aria-pressed",x===b));$("#nx").disabled=false});
$("#nx").onclick=()=>{step++;ob();const q=$("#q");q&&q.focus()};$("#bk").onclick=()=>{step--;ob();$("#q").focus()}}
ob();

/* PLACEHOLDER – replace with ML engine.
   MOCK PERSON: Sam, 34, care assistant, rents, two children, uses a car.
   getTimelines() must return A, B, C. Each has: pts (net money, years 0-5), end (accounts + monthly flow after 5 years),
   ms (milestones: [when, icon, headline, example written for this person]). */
const SAM={name:"Sam",now:{cur:480,sav:720,inv:150,debt:0,in:1850,out:1790,sv:40,iv:20}};
window.TimeTravelEngine={getTimelines(answers){return{
A:{name:"Stay the same",icon:"➡️",c:"#007a78",sub:"What happens if nothing changes?",pts:[1200,1100,900,500,150,-200],why:"Based on your spending and income staying as they are today.",
end:{cur:-200,sav:0,inv:150,debt:0,in:1850,out:1880,sv:0,iv:0},
ms:[["1 month","💷","£1,200 savings left","Your pay of £1,850 lands on the 28th. Rent (£725) and energy (£142) leave in the first week, so by the 20th you are often down to about £300."],
["3 months","📉","Savings slowly going down","Gas and electric go up about £18 a month this winter. That is £54 more over 3 months. The gym (£29.99) and two streaming apps (£22.98) also still leave every month."],
["1 year","⚠️","You may start using your overdraft","Your car insurance (£412) renews in March. With only about £150 left that month, you would probably dip into your overdraft."],
["5 years","🪫","Very little growth","In 2031 you would still have about £150 in your investment account, the same as today. Prices will probably be higher, so £150 would buy less."]]},
B:{name:"Worst case",icon:"⛈️",c:"#b0123a",sub:"A risk check, not a prediction. Knowing helps you prepare.",pts:[1200,900,200,-600,-1500,-2600],why:"Includes higher prices, a surprise bill, rising energy costs and a gap in income.",
end:{cur:-600,sav:0,inv:0,debt:2000,in:1700,out:1950,sv:0,iv:0},
ms:[["1 year","🪫","Savings used up","If your hours were cut by 20% (£370 less a month) and your boiler broke (£650), your £1,200 would be gone in about 3 months."],
["3 years","💳","Relying on credit","£2,000 on a credit card at 24% interest would cost about £480 a year, before you pay off any of the £2,000."],
["5 years","🛡️","Real financial risk. But there are ways to prepare.","With rent and two children to look after, one missed month could mean rent arrears. Council Tax Reduction and Citizens Advice can help before it gets that far."]]},
C:{name:"Best realistic",icon:"🌱",c:"#0b6b3a",sub:"If you follow our suggestions.",pts:[1200,1500,2300,3600,5500,9600],why:"Includes an emergency fund, cancelling unused subscriptions, using an ISA and claiming support you’re entitled to.",
end:{cur:1600,sav:8000,inv:3100,debt:0,in:1950,out:1800,sv:110,iv:40},
ms:[["Step 1","🛟","Build an emergency fund","Move £60 on payday (the 28th) into a separate “Emergency” pot. In 12 months you would have £1,440 with today’s £720. That covers your car insurance and a boiler repair."],
["Step 2","✂️","Cancel unused subscriptions","Your gym (£29.99) was used twice in 3 months. Netflix (£10.99) was last watched 4 months ago. Cancelling both saves £40.98 a month, or £491.76 a year."],
["Step 3","🏦","Use an ISA","Put your £110 a month of savings in a Cash ISA. The interest is tax-free. At an example rate of 4% that is about £26 in year one, and more each year after."],
["5 years","🎉","About £8,400 extra savings","£8,400 is nearly 5 months of all your rent and bills (£1,790 a month). That is a real safety net for you and your two children."]]}}}};
const gbp=v=>(v<0?"−":"")+"£"+Math.abs(v).toLocaleString("en-GB");
/* Accounts the app can already see (mock). In the real product these come from the connected NatWest account. */
const ACCTS=[["🏦","Everyday Current Account","••4821","cur"],["🐷","Flexible Saver","••3307","sav"],["📈","Stocks & Shares ISA","••7712","inv"],["💳","Credit card","••0056","debt"]];
const MONTH=[["⬇️","Money coming in","in",1],["⬆️","Money going out","out",0],["🐷","Saved","sv",1],["📈","Invested","iv",1]];
/* The recommendations: [icon, what to do, what it is worth, how (specific to the person), button, optional tab to open] */
const ACTS=[
["✂️","Cancel 2 subscriptions you don’t use","Saves £492 a year","Gym £29.99 (used twice in 3 months) and Netflix £10.99 (last watched 4 months ago). Both come out of your Everyday Current Account.","Cancel them in the app"],
["🛟","Move £60 to an Emergency pot on payday","£1,440 safety net in a year","On the 28th, £60 moves from your Everyday Current Account into a new pot in your Flexible Saver.","Set up the £60 transfer"],
["🏦","Put your £110 a month into a Cash ISA","Tax-free interest","At an example rate of 4%, that is about £26 in year one. It grows every year.","Open a Cash ISA"],
["🧭","Claim help you may be owed","Could be £200 to £2,000 a year","You rent and have two children. Council Tax Reduction may apply to you.","See what you can claim","support"]];
const PLAN=new Set();
let cur="A";
const chg=(a,b,ug)=>{const d=b-a;if(!d)return"";const g=(d>0)==ug;return' <span class="chg '+(g?'gd':'bd')+'" aria-hidden="true">'+(d>0?'▲':'▼')+(g?'✔':'✖')+'</span><span class="sr">'+(d>0?'up':'down')+', '+(g?'better':'worse')+'</span>'};
const tbl=(cap,first,rows)=>'<div class="wrapx"><table class="tb"><caption class="sr">'+cap+'</caption><thead><tr><th scope="col">'+first+'</th><th scope="col">Now</th><th scope="col">In 5 years</th></tr></thead><tbody>'+rows+'</tbody></table></div>';
const card=(a,i)=>'<div class="act"><span class="num" aria-hidden="true">'+(i+1)+'</span><div class="ab"><h4><span aria-hidden="true">'+a[0]+'</span> '+a[1]+'</h4><p class="val">💷 '+a[2]+'</p><p>'+a[3]+'</p>'+(a[5]?'<button class="btn pri" data-go="'+a[5]+'">'+a[4]+' →</button>':'<button class="btn pri" data-pl="'+i+'" aria-pressed="'+PLAN.has(i)+'">'+(PLAN.has(i)?'✔ In my plan':a[4])+'</button>')+'</div></div>';
function acts(){const f=ACTS.findIndex((a,i)=>!a[5]&&!PLAN.has(i));
$("#next").innerHTML=f<0?'<div class="act"><span class="num" aria-hidden="true">✔</span><div class="ab"><h4>🎉 All set. Your plan is ready.</h4></div></div>':card(ACTS[f],f);
$("#allacts").innerHTML=ACTS.map((a,i)=>i==f?'':card(a,i)).join("")+'<p class="lead" style="margin:.6rem 0 0" aria-live="polite">'+PLAN.size+' of 3 in your plan</p>';
document.querySelectorAll("[data-pl]").forEach(b=>b.onclick=()=>{const i=+b.dataset.pl;PLAN.has(i)?PLAN.delete(i):PLAN.add(i);acts();const x=document.querySelector('[data-pl="'+i+'"]')||$("#next .act");x&&x.focus&&x.focus()})}
function drawTl(){const T=TimeTravelEngine.getTimelines(ans),t=T[cur],n=SAM.now,e=t.end;
$("#tlbtns").innerHTML=Object.entries(T).map(([k,x])=>'<button style="--c:'+x.c+'" aria-pressed="'+(k==cur)+'" data-k="'+k+'" aria-label="Timeline '+k+': '+x.name+'"><span class="i" aria-hidden="true">'+x.icon+'</span><b><span class="lt" aria-hidden="true">'+k+'</span></b>'+x.name+'</button>').join("");
document.querySelectorAll("#tlbtns button").forEach(b=>b.onclick=()=>{cur=b.dataset.k;drawTl();document.querySelector('#tlbtns [data-k="'+cur+'"]').focus()});
$("#tltitle").textContent="Timeline "+cur+": "+t.name;$("#tlsub").textContent=t.sub;$("#tlwhy").textContent=t.why;
$("#bn0").textContent=gbp(t.pts[0]);$("#bn5").textContent=gbp(t.pts[5]);$("#bn5").style.borderBottom="6px solid "+t.c;
acts();
const ac=ACCTS.filter(a=>n[a[3]]||e[a[3]]);
$("#pv-acc").textContent=ac.length+" accounts, already connected";
$("#acc").innerHTML=tbl("Your accounts now and in 5 years","Account",ac.map(a=>{const k=a[3];return'<tr><th scope="row"><span aria-hidden="true">'+a[0]+'</span> '+a[1]+'<small>'+a[2]+'</small></th><td>'+gbp(n[k])+'</td><td><b>'+gbp(e[k])+'</b>'+chg(n[k],e[k],k!="debt")+(k=="cur"&&e.cur<0?'<br><span class="chg bd">⚠️ overdraft</span>':'')+'</td></tr>'}).join(""));
$("#pv-mon").textContent="Left over each month: "+gbp(n.in-n.out)+" ➜ "+gbp(e.in-e.out);
$("#mon").innerHTML=tbl("Your month, now and in 5 years","Each month",MONTH.map(m=>'<tr><th scope="row"><span aria-hidden="true">'+m[0]+'</span> '+m[1]+'</th><td>'+gbp(n[m[2]])+'</td><td><b>'+gbp(e[m[2]])+'</b>'+chg(n[m[2]],e[m[2]],m[3])+'</td></tr>').join(""));
$("#pv-st").textContent=t.ms.length+" steps, with examples for "+SAM.name;
$("#tlsteps").innerHTML=t.ms.map(m=>'<li style="--c:'+t.c+'"><span class="t">'+m[0]+'</span><span class="i" aria-hidden="true">'+m[1]+'</span><div><b>'+m[2]+'</b><p class="ex">💡 <b>For '+SAM.name+':</b> '+m[3]+'</p></div></li>').join("");
const all=Object.values(T).flatMap(x=>x.pts),mn=Math.min(...all,0),mx=Math.max(...all),X=i=>50+i*100,Y=v=>165-(v-mn)/(mx-mn)*135;
let s='<rect width="600" height="210" fill="var(--card)" rx="10"/><line x1="50" x2="560" y1="'+Y(0)+'" y2="'+Y(0)+'" stroke="var(--mut)" stroke-dasharray="6 5" stroke-width="2"/><text x="52" y="'+(Y(0)-5)+'" fill="var(--mut)" font-size="12">£0</text>';
["Now","1 yr","2 yrs","3 yrs","4 yrs","5 yrs"].forEach((l,i)=>s+='<text x="'+X(i)+'" y="200" text-anchor="middle" font-size="13" fill="var(--mut)">'+l+'</text>');
Object.entries(T).forEach(([k,x])=>{if(k!=cur)s+='<polyline fill="none" stroke="'+x.c+'" stroke-width="3" opacity=".3" points="'+x.pts.map((v,i)=>X(i)+","+Y(v)).join(" ")+'"/>'});
s+='<polyline fill="none" stroke="'+t.c+'" stroke-width="7" stroke-linecap="round" stroke-linejoin="round" points="'+t.pts.map((v,i)=>X(i)+","+Y(v)).join(" ")+'"/>';
t.pts.forEach((v,i)=>{s+='<circle cx="'+X(i)+'" cy="'+Y(v)+'" r="8" fill="var(--card)" stroke="'+t.c+'" stroke-width="4"/>'});
$("#chart").innerHTML=s;
$("#chartdesc").textContent="The money you could use goes from "+gbp(t.pts[0])+" now to "+gbp(t.pts[5])+" in 5 years. Example data.";}

/* ===== SUPPORT HUB: data ported 1:1 from recommendations.py (edit or regenerate from the Python) ===== */
const RECS=[
{n:"Council Tax Reduction",cat:"Government Support",url:"https://www.gov.uk/apply-council-tax-reduction",d:"Reduce your council tax bill if you're on a low income.",p:"High",sv:"£200-£2,000/year",g:["Low Income","Renters","Families"],c:"Local Council",t:["housing","bills","support"]},
{n:"Universal Credit Check",cat:"Government Support",url:"https://www.gov.uk/universal-credit",d:"Check if you may be entitled to Universal Credit.",p:"High",sv:"Varies",g:["Low Income","Unemployed"],c:"DWP",t:["benefits","income","support"]},
{n:"Pension Credit",cat:"Government Support",url:"https://www.gov.uk/pension-credit",d:"Extra support for pensioners on a low income.",p:"High",sv:"£1,000+/year",g:["65+"],c:"DWP",t:["elderly","benefits"]},
{n:"Winter Fuel Payment",cat:"Government Support",url:"https://www.gov.uk/winter-fuel-payment",d:"Help with winter heating costs.",p:"Medium",g:["65+"],c:"Government",t:["energy","elderly"]},
{n:"Warm Home Discount",cat:"Energy Support",url:"https://www.gov.uk/the-warm-home-discount-scheme",d:"Discount on electricity bills for eligible households.",p:"High",g:["Low Income","Pensioners"],c:"Energy Supplier",t:["energy","bills"]},
{n:"Household Support Fund",cat:"Crisis Support",url:"https://www.gov.uk/cost-living-help-local-council",d:"Emergency support through local councils.",p:"High",g:["Financial Hardship"],c:"Local Council",t:["crisis","food","energy"]},
{n:"Skills Bootcamp",cat:"Education",url:"https://www.gov.uk/guidance/find-a-skills-bootcamp",d:"Free career-focused training.",p:"High",sv:"Potential salary increase",ib:1,g:["Career Growth","Universal Credit"],c:"Training Provider",t:["education","career"]},
{n:"Apprenticeships",cat:"Education",url:"https://www.gov.uk/apply-apprenticeship",d:"Earn while you learn.",p:"High",g:["16-30","Career Changers"],c:"Employer",t:["education","earnings"]},
{n:"Adult Learning Courses",cat:"Education",url:"https://nationalcareers.service.gov.uk",d:"Local free and subsidised training programmes.",p:"Medium",g:["No Qualifications"],c:"College / Provider",t:["education"]},
{n:"Student Hardship Fund",cat:"Education Support",url:"https://www.gov.uk/student-finance",d:"Additional support for struggling students.",p:"High",g:["Students"],c:"University",t:["student","hardship"]},
{n:"Turn2Us Grants",cat:"Grants",url:"https://www.turn2us.org.uk",d:"Search thousands of grants and charitable funds.",p:"High",g:["Low Income","Disabled","Students"],c:"Turn2Us",t:["grants","support"]},
{n:"Free School Meals",cat:"Family Support",url:"https://www.gov.uk/apply-free-school-meals",d:"Support for families with children.",p:"High",g:["Families"],c:"Local Authority",t:["family","children"]},
{n:"Child Benefit",cat:"Family Support",url:"https://www.gov.uk/child-benefit",d:"Financial support for raising children.",p:"High",g:["Parents"],c:"HMRC",t:["family"]},
{n:"First Homes Scheme",cat:"Housing",url:"https://www.gov.uk/first-homes-scheme",d:"Support for first-time buyers.",p:"Medium",g:["Under 40","First Time Buyers"],c:"Local Authority",t:["housing","property"]},
{n:"Debt Advice",cat:"Financial Support",url:"https://www.moneyhelper.org.uk",d:"Free and confidential debt guidance.",p:"High",g:["Debt Risk"],c:"MoneyHelper",t:["debt","support"]},
{n:"Citizens Advice",cat:"Advice",url:"https://www.citizensadvice.org.uk",d:"Independent financial and legal guidance.",p:"Medium",g:["Everyone"],c:"Local Branch",t:["advice","support"]}];
const CI={"Government Support":"🏛️","Energy Support":"⚡","Crisis Support":"🆘","Education":"🎓","Education Support":"🎒","Grants":"🎁","Family Support":"👨‍👩‍👧","Housing":"🏠","Financial Support":"💷","Advice":"💬"};
const P={age:34,inc:"Low",work:"Employed",uc:0,kids:0,rent:0,ftb:0,dis:0,noq:0,hard:0,debt:0,grow:0,edited:false};
let catF="All";
const CK=[["uc","I get Universal Credit"],["kids","I have children"],["rent","I rent my home"],["ftb","I want to buy my first home"],["dis","I have a disability"],["noq","I have no formal qualifications"],["hard","I’m struggling to pay for essentials"],["debt","I’m worried about debt"],["grow","I want to earn more or change career"]];
function fromAns(){if(P.edited||!ans.length)return;const a=ans;
if(a[5]!==undefined)P.rent=+(a[5]===0);if(a[6]!==undefined)P.kids=+(a[6]===0);if(a[2]!==undefined){P.ftb=+(a[2]===1);P.grow=+(a[2]===3||a[3]===1)}
if(a[1]!==undefined||a[4]!==undefined){P.debt=+(a[1]===2||a[4]===1);P.hard=+(a[4]===3||a[0]===2)}}
function groups(){const g=new Set(["Everyone"]);
if(P.inc=="Low")g.add("Low Income");if(P.age>=65)g.add("65+");if(P.age>=16&&P.age<=30)g.add("16-30");if(P.age<40)g.add("Under 40");
if(P.work=="Unemployed")g.add("Unemployed");if(P.work=="Student")g.add("Students");if(P.work=="Retired"||P.age>=66)g.add("Pensioners");
if(P.uc)g.add("Universal Credit");if(P.kids){g.add("Families");g.add("Parents")}if(P.rent)g.add("Renters");if(P.ftb)g.add("First Time Buyers");
if(P.dis)g.add("Disabled");if(P.noq)g.add("No Qualifications");if(P.hard)g.add("Financial Hardship");if(P.debt)g.add("Debt Risk");if(P.grow){g.add("Career Growth");g.add("Career Changers")}return g}
function supList(){const g=groups();
const all=RECS.map(r=>({r,m:r.g.filter(x=>g.has(x))})).filter(x=>x.m.length).map(x=>({...x,s:x.m.filter(y=>y!="Everyone").length*10+(x.r.p=="High"?3:2)})).sort((a,b)=>b.s-a.s);
const cats=["All",...new Set(all.map(x=>x.r.cat))];if(!cats.includes(catF))catF="All";
const v=all.filter(x=>catF=="All"||x.r.cat==catF);
$("#suplist").innerHTML='<p class="lead" aria-live="polite"><b>'+v.length+' thing'+(v.length==1?'':'s')+' you may be able to get.</b> Best matches first.</p><div class="bank" role="group" aria-label="Filter by type" style="justify-content:flex-start">'+cats.map(c=>'<button class="chip" aria-pressed="'+(c==catF)+'" data-cf="'+c+'">'+(CI[c]||"📋")+' '+c+'</button>').join("")+'</div><div class="sup">'+v.map(({r,m})=>'<article class="card" style="--c:'+(r.p=="High"?"var(--pink)":"var(--teal)")+'"><span class="i" aria-hidden="true">'+(CI[r.cat]||"📋")+'</span><h3>'+r.n+'</h3><p class="pri">'+(r.p=="High"?"⭐ High priority":"◆ Medium priority")+' · '+r.cat+'</p><p>'+r.d+'</p>'+(r.sv?'<p><b>'+(r.ib?'📈 Income boost: ':'💷 Possible saving: ')+r.sv+'</b></p>':'')+'<p>📞 <b>Who to contact:</b> '+r.c+'</p><div>'+r.t.map(t=>'<span class="tagc">#'+t+'</span>').join("")+'</div><div class="why"><b>Why am I seeing this?</b> It matches: '+m.join(", ")+'.</div><p><a class="btn pri" href="'+r.url+'" target="_blank" rel="noopener" aria-label="Find out more about '+r.n+' (opens in a new tab)">Find out more ↗</a></p></article>').join("")+'</div>';
document.querySelectorAll("[data-cf]").forEach(b=>b.onclick=()=>{catF=b.dataset.cf;supList();document.querySelector('[data-cf="'+catF+'"]').focus()})}
function sup(){fromAns();
$("#supform").innerHTML='<div class="card"><h3 style="margin-top:0">About you <span class="badge">Example: would come from your NatWest account</span></h3><div class="pf"><label>Your age<input type="number" id="pa" min="16" max="110" value="'+P.age+'"></label><label>Your income<select id="pi">'+["Low","Medium","High"].map(x=>'<option'+(P.inc==x?' selected':'')+'>'+x+'</option>').join("")+'</select></label><label>Your work<select id="pw">'+["Employed","Self-employed","Unemployed","Student","Retired"].map(x=>'<option'+(P.work==x?' selected':'')+'>'+x+'</option>').join("")+'</select></label></div><fieldset><legend><b>Tick what applies to you</b></legend>'+CK.map(([k,t])=>'<label class="ck"><input type="checkbox" data-k="'+k+'" '+(P[k]?'checked':'')+'>'+t+'</label>').join("")+'</fieldset></div>';
const up=()=>{P.edited=true;P.age=+$("#pa").value||0;P.inc=$("#pi").value;P.work=$("#pw").value;document.querySelectorAll("[data-k]").forEach(c=>P[c.dataset.k]=+c.checked);supList()};
$("#pa").oninput=up;$("#pi").onchange=up;$("#pw").onchange=up;document.querySelectorAll("[data-k]").forEach(c=>c.onchange=up);supList()}
sup();

const initialSection=location.hash.slice(1);
if(tabs.some(([id])=>id===initialSection))go(initialSection);
window.addEventListener("hashchange",()=>{const id=location.hash.slice(1);if(tabs.some(([tab])=>tab===id))go(id)});
