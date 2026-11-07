-- Applied in order by the pinned Supabase CLI; see README.md.
-- This module uses its own tables; existing application tables are untouched.
begin;
create table public.cs_learners (id uuid primary key, name text not null);
create table public.cs_lessons (
 id text primary key, position integer unique not null, title text not null,
 description text not null, reading text not null, minutes integer not null default 3, xp integer not null default 30
);
create table public.cs_questions (
 id text primary key, lesson_id text not null references public.cs_lessons(id),
 position integer not null, prompt text not null, options jsonb not null,
 correct_index integer not null, explanation text not null,
 unique(lesson_id,position)
);
create table public.cs_attempts (
 id uuid primary key, learner_id uuid not null references public.cs_learners(id),
 lesson_id text not null references public.cs_lessons(id), answers jsonb not null,
 score integer not null, total integer not null, passed boolean not null,
 created_at timestamptz not null default now()
);
create table public.cs_completions (
 learner_id uuid not null references public.cs_learners(id), lesson_id text not null references public.cs_lessons(id),
 xp integer not null, completed_at timestamptz not null default now(), primary key(learner_id,lesson_id)
);
alter table public.cs_learners enable row level security;
alter table public.cs_lessons enable row level security;
alter table public.cs_questions enable row level security;
alter table public.cs_attempts enable row level security;
alter table public.cs_completions enable row level security;
-- No browser policies: only the server's secret/service-role key may access the demo.
revoke all on public.cs_learners, public.cs_lessons, public.cs_questions, public.cs_attempts, public.cs_completions from anon, authenticated;
grant all on public.cs_learners, public.cs_lessons, public.cs_questions, public.cs_attempts, public.cs_completions to service_role;
insert into public.cs_learners values ('00000000-0000-4000-8000-000000000001','Demo learner');
insert into public.cs_lessons(id,position,title,description,reading) values
('money-map',1,'Give every pound a purpose','Meet your money. Make a simple plan.','A budget is a plan for your income. Start with take-home pay, then list your spending and savings. Needs are essentials such as rent and basic groceries. Wants are things you can choose to go without. A useful budget fits your circumstances and changes when your life does.'),
('budget-balance',2,'Find your balance','Turn a monthly budget into a useful habit.','Subtract spending from take-home income to see what remains. If spending is higher than income, review flexible costs and look for support or ways to increase income. Include irregular expenses, such as annual bills, by setting aside a little each month. Review your plan regularly.'),
('saving-buffer',3,'Build a little breathing room','Understand savings goals and unexpected costs.','Savings can help with planned goals and unexpected costs. An emergency fund is money set aside for unplanned essentials. Keep it accessible and separate from everyday spending where practical. Start with an amount that fits your circumstances; consistency matters more than a particular starting amount.'),
('saving-habit',4,'Make saving a habit','Small steps, future-you energy.','A specific savings goal has an amount and a timeframe. Divide the amount you still need by the months available to estimate a monthly contribution. An automatic transfer can help you remember, but check that it leaves enough for essential spending. Adjust your goal when circumstances change.'),
('interest-intro',5,'Meet compound interest','Discover how growth can build on itself.','Interest is an amount earned on savings or charged on borrowing. With compound interest, future interest is calculated on the original amount plus earlier interest. In a simplified example, £100 earning 10% a year becomes £110 after one year and £121 after two. Actual results depend on rates, fees, taxes and timing. These are learning examples, not promised returns.'),
('interest-time',6,'Let time do its thing','Put your new interest knowledge to work.','Compounding can grow savings, but it can also increase debt when interest is added to the balance. A higher rate or a longer period changes the result. Inflation reduces what money can buy, so growth in a balance is not the same as growth in purchasing power. Compare assumptions carefully.');
insert into public.cs_questions values
('m1','money-map',1,'What is a budget?','["A plan for income, spending and saving","A rule that you cannot have fun","A list of things you want to buy"]',0,'A budget helps you decide how to use the money coming in.'),
('m2','money-map',2,'Which expense is usually a need?','["A streaming upgrade","Basic groceries","Concert tickets"]',1,'Basic groceries meet an essential need. Circumstances can affect how you classify spending.'),
('m3','money-map',3,'Your income changes. What should you do with your budget?','["Ignore the change","Stop tracking spending","Review and update the plan"]',2,'A budget should adapt to your current income and needs.'),
('b1','budget-balance',1,'You take home £1,800 and spend £1,500. What remains?','["£200","£300","£500"]',1,'£1,800 − £1,500 = £300 before any other costs or savings contributions.'),
('b2','budget-balance',2,'An annual bill is £240. How much would you set aside monthly?','["£20","£24","£120"]',0,'£240 divided by 12 months is £20 per month.'),
('b3','budget-balance',3,'Your planned spending exceeds your income. What helps first?','["Pretend the gap is not there","Add more optional spending","Review the plan and identify adjustments"]',2,'Understanding the gap lets you consider changes and support suited to your situation.'),
('s1','saving-buffer',1,'What is an emergency fund for?','["Unplanned essential costs","Everyday treats","Guaranteed investment profits"]',0,'An emergency fund is a buffer for unexpected essentials.'),
('s2','saving-buffer',2,'Which feature matters for emergency savings?','["Being impossible to withdraw","Being accessible when needed","Having an unpredictable value"]',1,'Emergency money should be available when an unexpected cost arrives.'),
('s3','saving-buffer',3,'You can only save a small amount. What is a useful start?','["Wait until you can save a fortune","Borrow to fill the savings pot","Choose a manageable regular amount"]',2,'Small, manageable contributions can help build a habit without straining essentials.'),
('h1','saving-habit',1,'You need £300 in six months. Starting from zero, what is the monthly target?','["£30","£50","£60"]',1,'£300 divided by six months is £50, ignoring any interest.'),
('h2','saving-habit',2,'What can an automatic savings transfer help with?','["Remembering to save regularly","Guaranteeing high returns","Removing the need for a budget"]',0,'Automation can support consistency, but the amount still needs to fit your budget.'),
('h3','saving-habit',3,'An essential bill increases. What should happen to your savings plan?','["Keep it unchanged at any cost","Ignore the bill","Review what remains affordable"]',2,'A sustainable savings plan responds to changes in essential costs.'),
('i1','interest-intro',1,'What makes interest compound?','["Interest also earns interest","The balance never changes","Only deposits earn interest"]',0,'Compounding includes earlier interest in the balance used for future calculations.'),
('i2','interest-intro',2,'£100 earns 10% interest for one year. With no fees or withdrawals, what is the balance?','["£101","£110","£120"]',1,'10% of £100 is £10. The simplified ending balance is £110.'),
('i3','interest-intro',3,'That £110 earns another 10%. What is the new balance?','["£120","£111","£121"]',2,'10% of £110 is £11, so the balance becomes £121.'),
('t1','interest-time',1,'Can compounding affect debt?','["Yes, when interest is added to the balance","No, only savings","Only if the balance is zero"]',0,'Interest added to a debt balance can itself incur interest.'),
('t2','interest-time',2,'What can inflation do?','["Guarantee a profit","Reduce the purchasing power of money","Make all prices stay fixed"]',1,'When prices rise, the same amount of money generally buys less.'),
('t3','interest-time',3,'Which statement about the 10% examples is true?','["They promise a real return","They include every possible cost","They illustrate a calculation using assumptions"]',2,'The examples use a fixed rate and omit fees and taxes. They are not forecasts.');
create function public.cs_complete_lesson(p_learner uuid,p_lesson text,p_answers jsonb,p_attempt uuid)
returns jsonb language plpgsql security invoker set search_path = public as $$
declare
 l cs_lessons%rowtype; a cs_attempts%rowtype; score_count integer; total_count integer;
 passed_result boolean; awarded integer := 0;
begin
 -- Serialize submissions for this learner, including repeated requests.
 perform 1 from cs_learners where id=p_learner for update;
 if not found then raise exception 'Unknown learner'; end if;
 select * into a from cs_attempts where id=p_attempt;
 if found then
  if a.learner_id <> p_learner or a.lesson_id <> p_lesson or a.answers <> p_answers then raise exception 'Attempt mismatch'; end if;
  return jsonb_build_object('score',a.score,'total',a.total,'passed',a.passed,'awarded',0);
 end if;
 select * into l from cs_lessons where id=p_lesson;
 if not found then raise exception 'Unknown lesson'; end if;
 if exists(select 1 from cs_lessons prior where prior.position < l.position and not exists(select 1 from cs_completions c where c.learner_id=p_learner and c.lesson_id=prior.id)) then raise exception 'Lesson locked'; end if;
 select count(*) into total_count from cs_questions where lesson_id=p_lesson;
 if jsonb_typeof(p_answers) <> 'array' or jsonb_array_length(p_answers) <> total_count or total_count = 0 then raise exception 'Invalid answers'; end if;
 if exists(select 1 from cs_questions q where q.lesson_id=p_lesson and (jsonb_typeof(p_answers->(q.position-1)) <> 'number' or (p_answers->>(q.position-1)) !~ '^[0-9]+$' or (p_answers->>(q.position-1))::integer >= jsonb_array_length(q.options))) then raise exception 'Invalid answer'; end if;
 select count(*) into score_count from cs_questions q where q.lesson_id=p_lesson and (p_answers->>(q.position-1))::integer=q.correct_index;
 passed_result := score_count >= ceil(total_count * 0.66);
 insert into cs_attempts values(p_attempt,p_learner,p_lesson,p_answers,score_count,total_count,passed_result,now());
 if passed_result then
  insert into cs_completions(learner_id,lesson_id,xp) values(p_learner,p_lesson,l.xp) on conflict do nothing;
  if found then awarded := l.xp; end if;
 end if;
 return jsonb_build_object('score',score_count,'total',total_count,'passed',passed_result,'awarded',awarded);
end $$;
revoke all on function public.cs_complete_lesson(uuid,text,jsonb,uuid) from public, anon, authenticated;
grant execute on function public.cs_complete_lesson(uuid,text,jsonb,uuid) to service_role;
commit;
