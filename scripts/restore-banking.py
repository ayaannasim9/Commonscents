"""Build the reviewed banking curriculum and its additive migration from the original snapshot."""
import json,itertools
from pathlib import Path
source=json.loads(Path('content/original/overview-banking.json').read_text())
data=json.loads(json.dumps(source))
# Preserve every original lesson and exercise; correct misleading security/product wording.
replacements={
'Your card is linked to your account. When you pay, the money leaves your account straight away.':'Your debit card uses money from your account. A payment may first appear as pending before it is fully processed.',
'An account number has 8 numbers. It points to your account and nobody else’s.':'A NatWest account number has 8 digits. Together with the sort code, it identifies your account.',
'Like a safe that the government backs up.':'Like a safety net for eligible deposits if an authorised bank fails. Check which accounts and firms are covered.',
'At the top you see how much money you can spend.':'Your account shows balances and transactions. Check pending payments and bills still to come before deciding what you can spend.',
'Tap Confirm. Most payments arrive in minutes. You will see a tick.':'Follow the confirmation steps only when you are sure. Check the payment status afterwards: it may be pending, completed or unsuccessful.',
'Look for natwest.com and a padlock in the address bar.':'Start from the official NatWest website and check the address carefully. HTTPS or a padlock means an encrypted connection, not proof that a website is genuine.',
'Safe connection':'Encrypted connection, not proof of a genuine site',
'A sign the connection is safe':'An encrypted connection; not proof a site is genuine',
'Look for the padlock and natwest.com in the address bar.':'Check the website address carefully. A padlock or HTTPS alone does not prove a site is genuine.',
'In a branch, you can see the person helping you.':'Ask staff through a bank branch or a contact route you found independently; appearances alone do not prove identity.',
'If unsure, hang up. Call the number on the back of your card.':'If unsure, hang up. Use another phone, or make sure the call has ended, then contact your bank using the number on your card.',
'Your savings are protected, up to a limit.':'Eligible deposits at authorised firms are protected up to a limit; check the FSCS website.',
'A safe number to call':'A number you can check independently',
'Your balance is at the top. Below it is a list of money in and money out.':'Find your balances and transactions in the app. Consider pending payments and upcoming bills too.',
'Like asking the cashier for your balance, but open 24 hours a day.':'Like asking the cashier for your balance, when the service is available.',
}
def review(x):
    if isinstance(x,str):
        for a,b in replacements.items(): x=x.replace(a,b)
        return x
    if isinstance(x,list): return [review(v) for v in x]
    if isinstance(x,dict): return {k:review(v) for k,v in x.items()}
    return x
data=review(data)
sources=[{'title':'NatWest · Using the app','url':'https://www.natwest.com/banking-with-natwest/natwest-app/how-to-use-the-natwest-app.html'}, {'title':'NatWest · Account details','url':'https://www.natwest.com/support-centre/view-or-change-your-details/find-account-details/where-can-i-find-my-account-number-and-sort-code.html'}, {'title':'NatWest · Pending payments','url':'https://www.natwest.com/current-accounts/bank-account-guides/pending-transactions.html'}, {'title':'FSCS · Deposit protection','url':'https://www.fscs.org.uk/what-we-cover/banks-building-societies-credit-unions/deposit-limit/'}, {'title':'Government cyber security · Website checks','url':'https://www.cyber.gc.ca/en/guidance/shopping-online-safely-itsap00071'}]
course={'id':'banking-basics','title':'Banking basics: app, website and branch','description':'The original 10 lessons: learn everyday banking with comparisons, matching and step-by-step practice.','units':[u['n'] for u in data['units']],'flexible':True,'lessons':[]}
for ui,unit in enumerate(data['units']):
    for original in unit['L']:
        lid='bank-'+original['id']; teach=[s for s in original['s'] if s['k']=='t']; questions=[]
        for n,s in enumerate([s for s in original['s'] if s['k']!='t'],1):
            interaction=None
            if s['k']=='c': options=s['o']; correct=s['a']; prompt=s['q']; explanation='The correct answer is: '+options[correct]+'.'
            elif s['k']=='f': options=s['w'];correct=options.index(s['a']);prompt=s['q']+': '+s['s'];explanation=s['s'].replace('___',s['a']);interaction={'kind':'fill'}
            else:
                items=sorted([p[1] for p in s['p']] if s['k']=='m' else s['it'])
                indices=list(itertools.product(range(len(items)),repeat=len(items))) if s['k']=='m' else list(itertools.permutations(range(len(items))))
                options=[json.dumps(list(p),separators=(',',':')) for p in indices]
                solution=[items.index(p[1]) for p in s['p']] if s['k']=='m' else [items.index(p) for p in s['it']]
                correct=options.index(json.dumps(solution,separators=(',',':')))
                interaction={'kind':'match' if s['k']=='m' else 'order','items':items}
                if s['k']=='m': interaction['left']=[p[0] for p in s['p']]
                prompt=s['q'];explanation='; '.join(a+' → '+b for a,b in s['p']) if s['k']=='m' else ' → '.join(s['it'])
            questions.append({'id':lid+'-'+str(n),'position':n,'prompt':prompt,'options':options,'correct_index':correct,'explanation':explanation,'interaction':interaction})
        course['lessons'].append({'id':lid,'title':original['t'],'description':teach[0]['h']+'. Learn with everyday examples.','unit_index':ui,'position':200+len(course['lessons']),'journey_position':len(course['lessons'])+1,'reading_cards':[s['h']+'\n\n'+s['a']+'\n\nIn everyday terms / at a branch: '+s['b'] for s in teach],'checklist':['Practise explaining one thing from this lesson in your own words.','Write down anything you want to ask your bank. Never enter real account details in this prototype.'],'sources':sources,'questions':questions})
Path('content/banking-course.json').write_text(json.dumps(course,ensure_ascii=False,indent=2)+'\n')
Path('content/banking-guide.json').write_text(json.dumps({'units':course['units'],'guides':data['guides'],'placement':data['placement'],'source':data['source']},ensure_ascii=False,indent=2)+'\n')
def sql(x):
    if isinstance(x,(dict,list)): return "'"+json.dumps(x,ensure_ascii=False).replace("'","''")+"'::jsonb"
    if x is None: return 'null'
    if isinstance(x,int):return str(x)
    return "'"+x.replace("'","''")+"'"
lines=['-- Restore all 10 original overview banking lessons. Existing progress is untouched.','begin;','alter table public.cs_lessons add column if not exists unit_index integer;','alter table public.cs_questions add column if not exists interaction jsonb;']
lines.append('insert into public.cs_journeys(id,title,description,units,flexible,position) values ('+','.join([sql(course['id']),sql(course['title']),sql(course['description']),sql(course['units']),'true','5'])+') on conflict (id) do nothing;')
for l in course['lessons']:
    fields=['id','position','title','description','reading','journey_id','journey_position','unit_index','reading_cards','checklist','sources','reviewed_at']
    row={**l,'reading':'\n\n'.join(l['reading_cards']),'journey_id':course['id'],'reviewed_at':'2026-11-07'}
    lines.append('insert into public.cs_lessons('+','.join(fields)+') values ('+','.join(sql(row[k]) for k in fields)+') on conflict (id) do nothing;')
    for q in l['questions']:
        fields=['id','lesson_id','position','prompt','options','correct_index','explanation','interaction'];row={**q,'lesson_id':l['id']}
        lines.append('insert into public.cs_questions('+','.join(fields)+') values ('+','.join(sql(row[k]) for k in fields)+') on conflict (id) do nothing;')
lines.extend(["notify pgrst, 'reload schema';",'commit;'])
Path('supabase/migrations/202611070004_restore_original_banking.sql').write_text('\n'.join(lines)+'\n')
print('Restored',len(course['lessons']),'lessons; 30 reading cards and',sum(len(l['questions']) for l in course['lessons']),'exercises')
