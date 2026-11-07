const $=s=>document.querySelector(s),R=document.documentElement;
const tabs=[["start","🚀","Start"],["future","🔮","Future"],["wrapped","🎉","Wrapped"],["learn","🎓","Learn"],["support","🧭","Support"],["report","📬","Report"]];
const nav=$("#nav");
tabs.forEach(([id,i,l],n)=>{const b=document.createElement("button");b.id="t-"+id;b.setAttribute("role","tab");b.setAttribute("aria-selected",n==0);b.innerHTML='<span class="i" aria-hidden="true">'+i+'</span>'+l;b.onclick=()=>go(id);nav.appendChild(b)});
function go(id){tabs.forEach(([t])=>{$("#s-"+t).hidden=t!=id;$("#t-"+t).setAttribute("aria-selected",t==id)});if(id=="future")drawTl();if(id=="support")sup();$("#main").focus({preventScroll:true});window.scrollTo({top:0})}
document.addEventListener("click",e=>{const g=e.target.closest("[data-go]");if(g)go(g.dataset.go)});
nav.addEventListener("keydown",e=>{const b=[...nav.children],i=b.indexOf(document.activeElement);if(e.key=="ArrowRight")b[(i+1)%b.length].focus();if(e.key=="ArrowLeft")b[(i-1+b.length)%b.length].focus()});

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

/* learn: Duolingo-style path, UK banking basics, app/web vs high street branch */
/* ===== LESSON CONTENT: edit here =====
   Step types: T teach slide, M match pairs, F fill the gap, C choose, O put in order */
const T=(e,h,a,b)=>({k:"t",e,h,a,b}),M=(q,p)=>({k:"m",q,p}),F=(q,s,w,a)=>({k:"f",q,s,w,a}),C=(q,o,a)=>({k:"c",q,o,a}),O=(q,it)=>({k:"o",q,it});
const U=[
{n:"Banking in the UK",c:"#5a287d",tip:"Most people in the UK use a current account for everyday money and pay by debit card, phone or bank transfer. Cheques are now rare. Banks are regulated, and savings are protected by a government-backed scheme (the FSCS) up to a limit.",L:[
{id:"a1",i:"🏦",t:"What is a current account?",s:[
T("🗄️","Your everyday account","A current account is where your pay goes in and your bills come out.","Like a locked drawer behind the counter. Only you have the key."),
T("💳","Your debit card","Your card is linked to your account. When you pay, the money leaves your account straight away.","Like handing over cash, but you don’t have to carry the cash."),
T("📱","Check it any time","You can see your money in the app, on the website, or at a cash machine.","Like asking the cashier for your balance, but open 24 hours a day."),
M("Match each item to what it does",[["💳 Debit card","Pay in shops"],["🗄️ Current account","Holds everyday money"],["🏧 Cash machine","Take out cash"]]),
F("Fill in the gap","A debit card takes money from your ___.",["account","pocket","friend"],"account"),
C("Which one is like a locked drawer in a branch?",["Your current account","A cash machine","A shop"],0)]},
{id:"a2",i:"🔢",t:"Sort code and account number",s:[
T("📍","Sort code","A sort code has 6 numbers, like 12-34-56. It shows which bank you use.","Like the address of the building."),
T("🔢","Account number","An account number has 8 numbers. It points to your account and nobody else’s.","Like the number on your drawer inside."),
T("🤝","Getting paid","To get paid, give your name, sort code and account number. Never give your PIN.","Like writing your details on a paying-in slip."),
M("Match the numbers",[["6 numbers","Sort code"],["8 numbers","Account number"],["4 numbers","Card PIN (secret)"]]),
F("Fill in the gap","A sort code has ___ numbers.",["6","8","4"],"6"),
C("What should you NEVER tell anyone?",["Your PIN","Your sort code","Your name"],0)]},
{id:"a3",i:"🛡️",t:"Is my money safe?",s:[
T("📜","Banks follow rules","UK banks must follow strict rules. Official bodies check them.","Like a branch that gets visits from an inspector."),
T("🛡️","The FSCS","If a bank fails, a scheme called the FSCS can pay back your savings, up to a limit.","Like a safe that the government backs up."),
T("🔍","Check the limit","The limit can change. Check it on the FSCS website before you save a lot.","Or ask an adviser at the desk."),
F("Fill in the gap","The FSCS protects your ___ up to a limit.",["savings","shoes","phone"],"savings"),
M("Match the word to its job",[["🛡️ FSCS","Protects savings"],["📜 Regulator","Checks the rules"],["📞 Your bank","Where you ask questions"]]),
C("Where do you check the FSCS limit?",["The FSCS website","A text from a stranger","Social media"],0)]}]},
{n:"Your NatWest app",c:"#006a68",tip:"The app is a branch in your pocket. Always download it from your phone’s official app store and check it says NatWest.",L:[
{id:"b1",i:"📲",t:"Download and log in",s:[
T("🔎","Find the app","Open your phone’s app store and search for NatWest. Choose the one made by NatWest.","Like finding the right branch on the high street."),
T("🔐","Log in","Enter your details. The app may send a code to your phone.","Like showing your ID at the counter."),
T("👆","Make it quick","Set Face ID, a fingerprint or a passcode. Next time you log in faster.","Like staff who know your face."),
O("Put these in order",["Open the app store","Search for NatWest","Download the app","Log in"]),
F("Fill in the gap","Always download apps from your phone’s official ___.",["app store","text message","stranger"],"app store"),
C("What makes logging in faster?",["Face ID or a passcode","Sharing your PIN","A paper form"],0)]},
{id:"b2",i:"💷",t:"Your home screen",s:[
T("💷","Your balance","At the top you see how much money you can spend.","Like asking the cashier for your balance."),
T("🧾","Payments list","Under it is a list of money in and money out. Tap one to see more.","Like a printed statement."),
T("🔔","Alerts","Switch on alerts to get a message when money arrives or leaves.","Like a friendly cashier giving you a ring."),
M("Match the item to its meaning",[["💷 Balance","Money you have now"],["🧾 Payments list","Money in and out"],["🔔 Alerts","Messages about your money"]]),
F("Fill in the gap","Your ___ is shown at the top of the screen.",["balance","photo","PIN"],"balance"),
C("Money leaving your account is called…",["A payment","A prize","A password"],0)]},
{id:"b3",i:"✍️",t:"Pay someone",s:[
T("✍️","Add the person","Tap Pay. Add their name, sort code and account number.","Like filling in a paying-in slip."),
T("🔎","Check carefully","Check every number. A wrong number can send money to the wrong person.","Like reading the slip twice before you hand it over."),
T("✅","Confirm","Tap Confirm. Most payments arrive in minutes. You will see a tick.","Like the cashier stamping your slip."),
O("Put the steps in order",["Tap Pay","Add name, sort code, account number","Check the numbers","Confirm"]),
F("Fill in the gap","Always ___ the numbers before you pay.",["check","guess","hide"],"check"),
M("Match the numbers",[["6 numbers","Sort code"],["8 numbers","Account number"],["£","Amount to pay"]])]}]},
{n:"The NatWest website",c:"#a8004f",tip:"Online banking is the same account as the app, just on a bigger screen. Always check the address bar says natwest.com.",L:[
{id:"c1",i:"💻",t:"Log in online",s:[
T("💻","Go to the website","Type natwest.com into your web browser.","Like walking up to the right shop front."),
T("🔒","Check the address","Look for natwest.com and a padlock in the address bar.","Like checking the sign above the door."),
T("🔑","Extra security","You may get a code by text. This is normal. Only you should use it.","Like the cashier asking one more question."),
F("Fill in the gap","The address should say ___.com",["natwest","free-money","bank-help"],"natwest"),
C("A code arrives by text when you log in. It is…",["Extra security for you","Something to read to a caller","A prize"],0),
M("Match the word to its meaning",[["🔒 Padlock","Safe connection"],["🌐 Browser","Where you open websites"],["🔑 Code","Only you use it"]])]},
{id:"c2",i:"📄",t:"Statements and settings",s:[
T("📄","Statements","Open Statements to read or download your monthly statements.","Like asking staff for a copy."),
T("⚙️","Settings","Open Settings to change your phone number or address.","Like filling in a change of address form."),
T("🏠","Proof of address","Some places accept a statement as proof of address. Ask them first.","Like asking the branch for a letter."),
M("Match the item to its job",[["📄 Statement","Record of your money"],["⚙️ Settings","Change your details"],["🏠 Address","Keep it up to date"]]),
F("Fill in the gap","Keep your phone number and ___ up to date.",["address","shoe size","PIN"],"address"),
C("Where do you change your phone number?",["Settings","A cash machine","A shop"],0)]}]},
{n:"Stay safe and get help",c:"#9a3b00",tip:"Your bank will never ask for your PIN or full password, or ask you to move money to a “safe account”. If in doubt, hang up and call the number on your card.",L:[
{id:"d1",i:"🚨",t:"Spot a scam",s:[
T("🚨","Scams are common","Scammers pretend to be your bank. They call, text or email.","In a branch, you can see the person helping you."),
T("🛑","Never share","Your bank will never ask for your PIN, or ask you to move money to a “safe account”.","A cashier would never ask for your PIN."),
T("📞","Hang up and call back","If unsure, hang up. Call the number on the back of your card.","Or walk into a branch and ask."),
C("A caller says “move your money to a safe account”. You…",["Hang up and call your bank","Do it quickly","Give your PIN"],0),
F("Fill in the gap","Your bank will never ask for your ___.",["PIN","hello","time"],"PIN"),
M("Match the item to its meaning",[["🚨 Scam","A trick to steal money"],["📞 Hang up","Stop the call"],["💳 Number on card","Safe number to call"]])]},
{id:"d2",i:"💬",t:"Getting help",s:[
T("💬","Ask in the app","Use Help in the app to chat or call. No question is silly.","Like going to the help desk."),
T("📍","Find a branch","Use the branch finder to see opening times and your nearest branch.","Like asking where the nearest branch is."),
T("🧑‍🤝‍🧑","Bring someone","You can ask a trusted person to come with you.","Staff are used to helping people who are new."),
C("Where can you ask for help?",["The Help section in the app","Nowhere","Only by post"],0),
M("Match the way to get help",[["💬 Chat","Type your question"],["📞 Call","Speak to someone"],["📍 Branch","Talk face to face"]]),
F("Fill in the gap","You can ___ for help at any time.",["ask","hide","wait"],"ask")]}]}];

const QZ=[["Which two numbers do you share so someone can pay money into your UK account?",["Sort code and account number","Passport and phone number","Card PIN and password","🤷 I’m not sure"],0],["Where do you usually see your balance in a banking app?",["Only in a letter","On the home screen after you log in","You have to call","🤷 I’m not sure"],1],["Online banking on a computer is…",["A different account","A shop","The same account, on the NatWest website","🤷 I’m not sure"],2],["Someone rings saying they are your bank and asks you to move money to a “safe account”. You…",["Do what they say","Give them your PIN","Hang up and call your bank on a number you trust","🤷 I’m not sure"],2]];
const LV={done:new Set(),skip:new Set(),placed:false,qi:-1,pts:120,chest:new Set()};
const allL=()=>U.flatMap((u,ui)=>u.L.map(l=>({u,ui,l})));
const unitDone=ui=>LV.skip.has(ui)||U[ui].L.every(l=>LV.done.has(l.id));
const MAS='<svg viewBox="0 0 100 110" width="100%" aria-hidden="true"><ellipse cx="50" cy="103" rx="30" ry="6" fill="rgba(0,0,0,.18)"/><circle cx="50" cy="52" r="42" fill="#ffc72c" stroke="#c98f00" stroke-width="6"/><circle cx="50" cy="52" r="31" fill="none" stroke="#c98f00" stroke-width="3" opacity=".6"/><path d="M14 42q36-26 72 0" fill="none" stroke="#5a287d" stroke-width="10" stroke-linecap="round"/><circle cx="38" cy="54" r="6" fill="#fff"/><circle cx="62" cy="54" r="6" fill="#fff"/><circle cx="39" cy="55" r="3" fill="#3c1053"/><circle cx="63" cy="55" r="3" fill="#3c1053"/><path d="M36 68q14 13 28 0" fill="none" stroke="#3c1053" stroke-width="5" stroke-linecap="round"/></svg>';
function learn(){const el=$("#learn");
if(!LV.placed){
if(LV.qi<0){el.innerHTML='<div class="card" style="text-align:center"><div style="width:120px;margin:auto">'+MAS+'</div><h3 style="margin:.2rem 0">Hi, I’m Penny. Let’s find your starting point</h3><p class="lead">4 quick questions so you can skip what you already know. “I’m not sure” is a perfectly good answer.</p><button class="btn pri" id="qs">Start quick check</button> <button class="btn ghost" id="qk">Skip: start from the beginning</button></div>';$("#qs").onclick=()=>{LV.qi=0;learn();$("#qq").focus()};$("#qk").onclick=()=>{LV.placed=true;learn()};return}
const [q,o,c]=QZ[LV.qi];
el.innerHTML='<p style="font-weight:800;margin:0" aria-live="polite">Question '+(LV.qi+1)+' of 4</p><div class="bar" aria-hidden="true"><i style="width:'+(LV.qi*25)+'%"></i></div><div class="card"><h3 id="qq" tabindex="-1" style="margin-top:0;font-size:1.3rem">'+q+'</h3><div class="opts">'+o.map((x,i)=>'<button class="opt" data-i="'+i+'">'+x+'</button>').join("")+'</div></div>';
el.querySelectorAll(".opt").forEach(b=>b.onclick=()=>{if(+b.dataset.i==c)LV.skip.add(LV.qi);LV.qi++;if(LV.qi>=QZ.length)LV.placed=true;learn();const n=$("#qq")||$("#lnote");n&&n.focus()});return}
const cur=allL().find(x=>!LV.done.has(x.l.id)&&!LV.skip.has(x.ui)),off=[0,-40,-64,-40,0,40,64,40];let k=0;
const nb=[...U.keys()].filter(i=>unitDone(i)).length;
let h='<div class="stats" aria-live="polite"><div class="stat"><span class="i">🔥</span>3 day streak</div><div class="stat"><span class="i">⭐</span>'+LV.pts+' points</div><div class="stat"><span class="i">🏅</span>'+nb+' of '+U.length+' units</div></div>';
h+='<p id="lnote" tabindex="-1" class="lead">'+(LV.skip.size?'⭐ Nice! You skipped '+LV.skip.size+' unit'+(LV.skip.size>1?'s':'')+' you already know. You can still open them any time.':'Tap the pink button to start your first lesson.')+'</p>';
U.forEach((u,ui)=>{const sk=LV.skip.has(ui);
h+='<div class="ub" style="background:'+u.c+'"><div><small>SECTION 1 · UNIT '+(ui+1)+(sk?' · ⭐ SKIPPED':'')+'</small><b>'+u.n+'</b></div><button class="gb" data-gb="'+ui+'">📒 Guidebook</button></div><div class="path"><div class="mas '+(ui%2?'r':'l')+'">'+MAS+'</div>';
u.L.forEach(l=>{const d=LV.done.has(l.id),isc=cur&&cur.l.id==l.id,st=sk?'skip':d?'done':isc?'cur':'lock',lab={skip:'skipped, tap to review',done:'completed',cur:'start here',lock:'locked'}[st];
h+='<div class="row" style="transform:translateX('+off[k++%8]+'px)">'+(isc?'<div class="bub">START ▾</div>':'')+'<button class="nd '+st+'" data-l="'+l.id+'" '+(st=='lock'?'disabled':'')+' aria-label="'+l.t+', '+lab+'"><span aria-hidden="true">'+(st=='done'?'✔':st=='skip'?'⭐':st=='lock'?'🔒':l.i)+'</span></button><span class="lb">'+l.t+'</span></div>'});
const ud=unitDone(ui),cl=LV.chest.has(ui);
h+='<div class="row" style="transform:translateX('+off[k++%8]+'px)"><button class="nd chest" data-ch="'+ui+'" '+(ud&&!cl?'':'disabled')+' aria-label="Reward chest, '+(cl?'claimed':ud?'tap to open':'locked until the unit is complete')+'"><span aria-hidden="true">'+(cl?'✔':ud?'🎁':'🔒')+'</span></button><span class="lb">'+(cl?'+50 points claimed':'Unit reward')+'</span></div></div>'});
el.innerHTML=h;
el.querySelectorAll("[data-l]").forEach(b=>b.onclick=()=>lesson(b.dataset.l));
el.querySelectorAll("[data-gb]").forEach(b=>b.onclick=()=>guide(+b.dataset.gb));
el.querySelectorAll("[data-ch]").forEach(b=>b.onclick=()=>{LV.chest.add(+b.dataset.ch);LV.pts+=50;learn()})}
const GB=[
{sum:"A UK current account is where your money lives day to day. You get a debit card, a sort code and an account number. Your savings are protected, up to a limit.",
pts:["Your pay goes into your current account. Your bills and shopping come out of it.","You pay with a debit card, your phone or a bank transfer. Cheques are rare now.","Your sort code (6 numbers) and account number (8 numbers) are how people pay you.","Never share your PIN or your full password. Not with anyone.","UK banks follow strict rules. Savings are protected by a scheme called the FSCS, up to a limit.","In a branch you talk to a person. In the app you do the same jobs yourself, at any time."],
words:[["Current account","The account you use every day"],["Debit card","A card that takes money from your account"],["Sort code","6 numbers that show your bank"],["Account number","8 numbers for your account"],["PIN","Your secret 4 numbers. Never share"],["FSCS","A scheme that protects savings, up to a limit"]],
rem:"If you are not sure, stop and ask. A real bank never minds questions."},
{sum:"The NatWest app is a bank branch on your phone. You can check your balance, pay people and get help at any time.",
pts:["Download it only from your phone’s official app store. Check that it says NatWest.","Log in, then set Face ID, a fingerprint or a passcode so it is quick next time.","Your balance is at the top. Below it is a list of money in and money out.","To pay someone, you need their name, sort code and account number. Check every number.","Turn on alerts. You get a message when money comes in or goes out.","If something looks wrong, use Help in the app."],
words:[["App store","Where you safely download apps"],["Balance","How much money you have now"],["Payment","Money going out"],["Alert","A message about your money"],["Confirm","Press to say yes, go ahead"]],
rem:"Take your time. You can always stop before you press Confirm."},
{sum:"Online banking is the same account as the app, on a bigger screen. Always check the address says natwest.com.",
pts:["Type natwest.com into your browser. Do not click links in texts or emails.","Look for the padlock and natwest.com in the address bar.","You may get a code by text. This is normal. The code is only for you.","Open Statements to read or download your monthly statements.","Open Settings to change your phone number or address.","Log out when you finish, especially on a shared computer."],
words:[["Browser","The program you use to open websites"],["Padlock","A sign the connection is safe"],["Statement","A record of your money in and out"],["Log out","Close your account when you finish"]],
rem:"Only you should ever use your codes."},
{sum:"Scammers pretend to be your bank. Your bank will never ask for your PIN, or ask you to move money to a “safe account”.",
pts:["Scammers can call, text or email. They sound kind, and in a hurry.","Your bank will never ask for your PIN or your full password.","Your bank will never ask you to move money to a “safe account”.","If you are unsure, hang up. Call the number on the back of your card.","Never read out a code from a text to someone who rang you.","You can walk into a branch, or use Help in the app, at any time."],
words:[["Scam","A trick to steal your money"],["Phishing","A fake text or email that looks real"],["Safe account","A lie scammers use. There is no such thing"],["Hang up","End the call. You are allowed to"]],
rem:"Real banks never rush you. If you feel rushed, stop."}];
function guide(ui){const u=U[ui],g=GB[ui],d=$("#dlg");
d.innerHTML='<div class="dh" style="background:'+u.c+'"><b>📒 Guidebook: '+u.n+'</b><button class="x" id="dx" aria-label="Close guidebook">✕</button></div><div class="db"><p class="gsum" id="gs" tabindex="-1" style="border-color:'+u.c+'"><b>In short:</b> '+g.sum+'</p><h3 class="sh">📝 The main points</h3><ol class="gp">'+g.pts.map(x=>'<li>'+x+'</li>').join("")+'</ol><h3 class="sh">📖 Words to know</h3><div class="gl">'+g.words.map(w=>'<div><b>'+w[0]+'</b><br>'+w[1]+'</div>').join("")+'</div><div class="fb g" role="note"><b>💡 Remember:</b> '+g.rem+'</div></div>';
$("#dx").onclick=()=>d.close();d.showModal();$("#gs").focus()}
const shuf=a=>{let r,t=0;do{r=[...a].sort(()=>Math.random()-.5)}while(a.length>1&&r.join("|")==a.join("|")&&t++<9);return r};
function lesson(id){
const {u,ui,l}=allL().find(x=>x.l.id==id),d=$("#dlg"),S=[...l.s],tot=S.filter(x=>x.k!="t").length;
let n=0,ok=0,sel=null,seq=[],pool=[],stage="next";
const draw=()=>{const s=S[n];sel=null;seq=[];let body="",lab="Continue",dis=false;
if(!s){body='<div style="text-align:center"><div style="width:130px;margin:auto">'+MAS+'</div><h3 class="th">🎉 Lesson complete!</h3><p class="lead">You got '+ok+' of '+tot+' right first time.'+(S.length>l.s.length?' You went back over '+(S.length-l.s.length)+' you missed and got them right. That is how learning works.':' Brilliant.')+'</p><div class="stat" style="max-width:240px;margin:auto">⭐ +'+(20+ok*10)+' points</div></div>';lab="Finish"}
else if(s.k=="t")body='<div class="hero" style="border-color:'+u.c+'" aria-hidden="true">'+s.e+'</div><h3 class="th">'+s.h+'</h3><div class="cmp"><div class="phn"><span class="tg">📱 App or website</span><p>'+s.a+'</p></div><div class="brn"><span class="tg">🏦 In a high street branch</span><p>'+s.b+'</p></div></div>';
else{body='<h3 class="th" id="qq">'+(s.r?'🔁 ':'')+s.q+'</h3>';dis=true;stage="check";lab="Check";
if(s.k=="c")body+='<div class="opts">'+s.o.map((x,i)=>'<button class="opt" data-i="'+i+'">'+x+'</button>').join("")+'</div>';
if(s.k=="f"){const p=s.s.split("___");body+='<p class="sentence">'+p[0]+'<span class="gap" id="gap">&nbsp;</span>'+p[1]+'</p><div class="bank">'+s.w.map(x=>'<button class="chip" data-w="'+x+'">'+x+'</button>').join("")+'</div>'}
if(s.k=="o"){pool=shuf(s.it);body+='<div class="ans" id="ans" aria-live="polite"></div><div class="bank" id="bk"></div>'}
if(s.k=="m"){const r=shuf(s.p.map((_,i)=>i));body+='<div class="mt"><div class="col">'+s.p.map((x,i)=>'<button class="chip" data-l="'+i+'">'+x[0]+'</button>').join("")+'</div><div class="col">'+r.map(i=>'<button class="chip" data-r="'+i+'">'+s.p[i][1]+'</button>').join("")+'</div></div>'}}
if(s&&(s.k=="t"||s.k=="m"))stage="next";
d.innerHTML='<div class="dh" style="background:'+u.c+'"><b>'+l.i+' '+l.t+'</b><button class="x" id="dx" aria-label="Close lesson">✕</button></div><div class="db"><p id="dp" tabindex="-1" style="font-weight:800;margin:0 0 .4rem">'+(s?(s.r?'🔁 Review: ':'')+'Step '+(n+1)+' of '+S.length:'Lesson complete')+'</p><div class="bar" aria-hidden="true"><i style="width:'+(n/S.length*100)+'%"></i></div>'+body+'<div id="fb" aria-live="polite"></div><div style="margin-top:1rem"><button class="btn pri" id="ck" '+(dis?'disabled':'')+'>'+lab+'</button></div></div>';
const btn=$("#ck");$("#dx").onclick=()=>d.close();
const lock=()=>d.querySelectorAll(".opt,.chip").forEach(x=>x.disabled=true);
const fin=(good,ans)=>{if(good&&!s.r)ok++;if(!good)S.push({...s,r:1});$("#fb").innerHTML='<div class="fb '+(good?'g':'b')+'" role="status"><b>'+(good?'✔ Correct! Well done.':'✖ Not quite.')+'</b>'+(good?'':' The answer is: '+ans+'. 🔁 We’ll ask this again at the end so you can master it.')+'</div>';btn.textContent="Continue";stage="next";lock()};
if(s&&s.k=="c")d.querySelectorAll(".opt").forEach(b=>b.onclick=()=>{sel=+b.dataset.i;d.querySelectorAll(".opt").forEach(x=>x.setAttribute("aria-pressed",x===b));btn.disabled=false});
if(s&&s.k=="f")d.querySelectorAll("[data-w]").forEach(b=>b.onclick=()=>{sel=b.dataset.w;$("#gap").textContent=sel;d.querySelectorAll("[data-w]").forEach(x=>x.classList.toggle("sel",x===b));btn.disabled=false});
if(s&&s.k=="o"){const rend=()=>{$("#ans").innerHTML=seq.map((x,i)=>'<button class="chip on" data-r="'+i+'">'+(i+1)+'. '+x+'</button>').join("")||'<span class="lead" style="margin:0">Tap the steps in order</span>';$("#bk").innerHTML=pool.filter(x=>!seq.includes(x)).map(x=>'<button class="chip" data-a="'+pool.indexOf(x)+'">'+x+'</button>').join("");
$("#ans").querySelectorAll("[data-r]").forEach(b=>b.onclick=()=>{seq.splice(+b.dataset.r,1);rend()});$("#bk").querySelectorAll("[data-a]").forEach(b=>b.onclick=()=>{seq.push(pool[+b.dataset.a]);rend()});btn.disabled=seq.length!=pool.length};rend()}
if(s&&s.k=="m"){let L=null,got=0,mis=0;d.querySelectorAll("[data-l]").forEach(b=>b.onclick=()=>{L=+b.dataset.l;d.querySelectorAll("[data-l]").forEach(x=>x.classList.toggle("sel",x===b))});
d.querySelectorAll("[data-r]").forEach(b=>b.onclick=()=>{if(L===null)return;const lb=d.querySelector('[data-l="'+L+'"]');if(lb.disabled)return;
if(+b.dataset.r===L){lb.classList.remove("sel");lb.classList.add("ok");b.classList.add("ok");lb.disabled=b.disabled=true;got++;L=null;if(got==s.p.length){if(!mis&&!s.r)ok++;if(mis)S.push({...s,r:1});$("#fb").innerHTML='<div class="fb g" role="status"><b>✔ All matched!</b>'+(mis?' 🔁 We’ll ask this again at the end.':'')+'</div>';btn.disabled=false}}
else{mis++;b.classList.add("no");lb.classList.add("no");setTimeout(()=>{b.classList.remove("no");lb.classList.remove("no")},700);lb.classList.remove("sel");L=null}})}
btn.onclick=()=>{if(!s){if(!LV.done.has(id)&&!LV.skip.has(ui)){LV.done.add(id);LV.pts+=20+ok*10}d.close();learn();return}
if(stage=="check"){if(s.k=="c")fin(sel==s.a,s.o[s.a]);if(s.k=="f")fin(sel==s.a,s.a);if(s.k=="o")fin(seq.join("|")==s.it.join("|"),s.it.map((x,i)=>(i+1)+". "+x).join("  "));return}
n++;draw()};
$("#dp").focus()};
draw();d.showModal()}
learn();
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
