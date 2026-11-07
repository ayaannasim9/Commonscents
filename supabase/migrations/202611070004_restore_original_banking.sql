-- Restore all 10 original overview banking lessons. Existing progress is untouched.
begin;
alter table public.cs_lessons add column if not exists unit_index integer;
alter table public.cs_questions add column if not exists interaction jsonb;
insert into public.cs_journeys(id,title,description,units,flexible,position) values ('banking-basics','Banking basics: app, website and branch','The original 10 lessons: learn everyday banking with comparisons, matching and step-by-step practice.','["Banking in the UK", "Your NatWest app", "The NatWest website", "Stay safe and get help"]'::jsonb,true,5) on conflict (id) do nothing;
insert into public.cs_lessons(id,position,title,description,reading,journey_id,journey_position,unit_index,reading_cards,checklist,sources,reviewed_at) values ('bank-a1',200,'What is a current account?','Your everyday account. Learn with everyday examples.','Your everyday account

A current account is where your pay goes in and your bills come out.

In everyday terms / at a branch: Like a locked drawer behind the counter. Only you have the key.

Your debit card

Your debit card uses money from your account. A payment may first appear as pending before it is fully processed.

In everyday terms / at a branch: Like handing over cash, but you don’t have to carry the cash.

Check it any time

You can see your money in the app, on the website, or at a cash machine.

In everyday terms / at a branch: Like asking the cashier for your balance, when the service is available.','banking-basics',1,0,'["Your everyday account\n\nA current account is where your pay goes in and your bills come out.\n\nIn everyday terms / at a branch: Like a locked drawer behind the counter. Only you have the key.", "Your debit card\n\nYour debit card uses money from your account. A payment may first appear as pending before it is fully processed.\n\nIn everyday terms / at a branch: Like handing over cash, but you don’t have to carry the cash.", "Check it any time\n\nYou can see your money in the app, on the website, or at a cash machine.\n\nIn everyday terms / at a branch: Like asking the cashier for your balance, when the service is available."]'::jsonb,'["Practise explaining one thing from this lesson in your own words.", "Write down anything you want to ask your bank. Never enter real account details in this prototype."]'::jsonb,'[{"title": "NatWest · Using the app", "url": "https://www.natwest.com/banking-with-natwest/natwest-app/how-to-use-the-natwest-app.html"}, {"title": "NatWest · Account details", "url": "https://www.natwest.com/support-centre/view-or-change-your-details/find-account-details/where-can-i-find-my-account-number-and-sort-code.html"}, {"title": "NatWest · Pending payments", "url": "https://www.natwest.com/current-accounts/bank-account-guides/pending-transactions.html"}, {"title": "FSCS · Deposit protection", "url": "https://www.fscs.org.uk/what-we-cover/banks-building-societies-credit-unions/deposit-limit/"}, {"title": "Government cyber security · Website checks", "url": "https://www.cyber.gc.ca/en/guidance/shopping-online-safely-itsap00071"}]'::jsonb,'2026-11-07') on conflict (id) do nothing;
insert into public.cs_questions(id,lesson_id,position,prompt,options,correct_index,explanation,interaction) values ('bank-a1-1','bank-a1',1,'Match each item to what it does','["[0,0,0]", "[0,0,1]", "[0,0,2]", "[0,1,0]", "[0,1,1]", "[0,1,2]", "[0,2,0]", "[0,2,1]", "[0,2,2]", "[1,0,0]", "[1,0,1]", "[1,0,2]", "[1,1,0]", "[1,1,1]", "[1,1,2]", "[1,2,0]", "[1,2,1]", "[1,2,2]", "[2,0,0]", "[2,0,1]", "[2,0,2]", "[2,1,0]", "[2,1,1]", "[2,1,2]", "[2,2,0]", "[2,2,1]", "[2,2,2]"]'::jsonb,11,'💳 Debit card → Pay in shops; 🗄️ Current account → Holds everyday money; 🏧 Cash machine → Take out cash','{"kind": "match", "items": ["Holds everyday money", "Pay in shops", "Take out cash"], "left": ["💳 Debit card", "🗄️ Current account", "🏧 Cash machine"]}'::jsonb) on conflict (id) do nothing;
insert into public.cs_questions(id,lesson_id,position,prompt,options,correct_index,explanation,interaction) values ('bank-a1-2','bank-a1',2,'Fill in the gap: A debit card takes money from your ___.','["account", "pocket", "friend"]'::jsonb,0,'A debit card takes money from your account.','{"kind": "fill"}'::jsonb) on conflict (id) do nothing;
insert into public.cs_questions(id,lesson_id,position,prompt,options,correct_index,explanation,interaction) values ('bank-a1-3','bank-a1',3,'Which one is like a locked drawer in a branch?','["Your current account", "A cash machine", "A shop"]'::jsonb,0,'The correct answer is: Your current account.',null) on conflict (id) do nothing;
insert into public.cs_lessons(id,position,title,description,reading,journey_id,journey_position,unit_index,reading_cards,checklist,sources,reviewed_at) values ('bank-a2',201,'Sort code and account number','Sort code. Learn with everyday examples.','Sort code

A sort code has 6 numbers, like 12-34-56. It shows which bank you use.

In everyday terms / at a branch: Like the address of the building.

Account number

A NatWest account number has 8 digits. Together with the sort code, it identifies your account.

In everyday terms / at a branch: Like the number on your drawer inside.

Getting paid

To get paid, give your name, sort code and account number. Never give your PIN.

In everyday terms / at a branch: Like writing your details on a paying-in slip.','banking-basics',2,0,'["Sort code\n\nA sort code has 6 numbers, like 12-34-56. It shows which bank you use.\n\nIn everyday terms / at a branch: Like the address of the building.", "Account number\n\nA NatWest account number has 8 digits. Together with the sort code, it identifies your account.\n\nIn everyday terms / at a branch: Like the number on your drawer inside.", "Getting paid\n\nTo get paid, give your name, sort code and account number. Never give your PIN.\n\nIn everyday terms / at a branch: Like writing your details on a paying-in slip."]'::jsonb,'["Practise explaining one thing from this lesson in your own words.", "Write down anything you want to ask your bank. Never enter real account details in this prototype."]'::jsonb,'[{"title": "NatWest · Using the app", "url": "https://www.natwest.com/banking-with-natwest/natwest-app/how-to-use-the-natwest-app.html"}, {"title": "NatWest · Account details", "url": "https://www.natwest.com/support-centre/view-or-change-your-details/find-account-details/where-can-i-find-my-account-number-and-sort-code.html"}, {"title": "NatWest · Pending payments", "url": "https://www.natwest.com/current-accounts/bank-account-guides/pending-transactions.html"}, {"title": "FSCS · Deposit protection", "url": "https://www.fscs.org.uk/what-we-cover/banks-building-societies-credit-unions/deposit-limit/"}, {"title": "Government cyber security · Website checks", "url": "https://www.cyber.gc.ca/en/guidance/shopping-online-safely-itsap00071"}]'::jsonb,'2026-11-07') on conflict (id) do nothing;
insert into public.cs_questions(id,lesson_id,position,prompt,options,correct_index,explanation,interaction) values ('bank-a2-1','bank-a2',1,'Match the numbers','["[0,0,0]", "[0,0,1]", "[0,0,2]", "[0,1,0]", "[0,1,1]", "[0,1,2]", "[0,2,0]", "[0,2,1]", "[0,2,2]", "[1,0,0]", "[1,0,1]", "[1,0,2]", "[1,1,0]", "[1,1,1]", "[1,1,2]", "[1,2,0]", "[1,2,1]", "[1,2,2]", "[2,0,0]", "[2,0,1]", "[2,0,2]", "[2,1,0]", "[2,1,1]", "[2,1,2]", "[2,2,0]", "[2,2,1]", "[2,2,2]"]'::jsonb,19,'6 numbers → Sort code; 8 numbers → Account number; 4 numbers → Card PIN (secret)','{"kind": "match", "items": ["Account number", "Card PIN (secret)", "Sort code"], "left": ["6 numbers", "8 numbers", "4 numbers"]}'::jsonb) on conflict (id) do nothing;
insert into public.cs_questions(id,lesson_id,position,prompt,options,correct_index,explanation,interaction) values ('bank-a2-2','bank-a2',2,'Fill in the gap: A sort code has ___ numbers.','["6", "8", "4"]'::jsonb,0,'A sort code has 6 numbers.','{"kind": "fill"}'::jsonb) on conflict (id) do nothing;
insert into public.cs_questions(id,lesson_id,position,prompt,options,correct_index,explanation,interaction) values ('bank-a2-3','bank-a2',3,'What should you NEVER tell anyone?','["Your PIN", "Your sort code", "Your name"]'::jsonb,0,'The correct answer is: Your PIN.',null) on conflict (id) do nothing;
insert into public.cs_lessons(id,position,title,description,reading,journey_id,journey_position,unit_index,reading_cards,checklist,sources,reviewed_at) values ('bank-a3',202,'Is my money safe?','Banks follow rules. Learn with everyday examples.','Banks follow rules

UK banks must follow strict rules. Official bodies check them.

In everyday terms / at a branch: Like a branch that gets visits from an inspector.

The FSCS

If a bank fails, a scheme called the FSCS can pay back your savings, up to a limit.

In everyday terms / at a branch: Like a safety net for eligible deposits if an authorised bank fails. Check which accounts and firms are covered.

Check the limit

The limit can change. Check it on the FSCS website before you save a lot.

In everyday terms / at a branch: Or ask an adviser at the desk.','banking-basics',3,0,'["Banks follow rules\n\nUK banks must follow strict rules. Official bodies check them.\n\nIn everyday terms / at a branch: Like a branch that gets visits from an inspector.", "The FSCS\n\nIf a bank fails, a scheme called the FSCS can pay back your savings, up to a limit.\n\nIn everyday terms / at a branch: Like a safety net for eligible deposits if an authorised bank fails. Check which accounts and firms are covered.", "Check the limit\n\nThe limit can change. Check it on the FSCS website before you save a lot.\n\nIn everyday terms / at a branch: Or ask an adviser at the desk."]'::jsonb,'["Practise explaining one thing from this lesson in your own words.", "Write down anything you want to ask your bank. Never enter real account details in this prototype."]'::jsonb,'[{"title": "NatWest · Using the app", "url": "https://www.natwest.com/banking-with-natwest/natwest-app/how-to-use-the-natwest-app.html"}, {"title": "NatWest · Account details", "url": "https://www.natwest.com/support-centre/view-or-change-your-details/find-account-details/where-can-i-find-my-account-number-and-sort-code.html"}, {"title": "NatWest · Pending payments", "url": "https://www.natwest.com/current-accounts/bank-account-guides/pending-transactions.html"}, {"title": "FSCS · Deposit protection", "url": "https://www.fscs.org.uk/what-we-cover/banks-building-societies-credit-unions/deposit-limit/"}, {"title": "Government cyber security · Website checks", "url": "https://www.cyber.gc.ca/en/guidance/shopping-online-safely-itsap00071"}]'::jsonb,'2026-11-07') on conflict (id) do nothing;
insert into public.cs_questions(id,lesson_id,position,prompt,options,correct_index,explanation,interaction) values ('bank-a3-1','bank-a3',1,'Fill in the gap: The FSCS protects your ___ up to a limit.','["savings", "shoes", "phone"]'::jsonb,0,'The FSCS protects your savings up to a limit.','{"kind": "fill"}'::jsonb) on conflict (id) do nothing;
insert into public.cs_questions(id,lesson_id,position,prompt,options,correct_index,explanation,interaction) values ('bank-a3-2','bank-a3',2,'Match the word to its job','["[0,0,0]", "[0,0,1]", "[0,0,2]", "[0,1,0]", "[0,1,1]", "[0,1,2]", "[0,2,0]", "[0,2,1]", "[0,2,2]", "[1,0,0]", "[1,0,1]", "[1,0,2]", "[1,1,0]", "[1,1,1]", "[1,1,2]", "[1,2,0]", "[1,2,1]", "[1,2,2]", "[2,0,0]", "[2,0,1]", "[2,0,2]", "[2,1,0]", "[2,1,1]", "[2,1,2]", "[2,2,0]", "[2,2,1]", "[2,2,2]"]'::jsonb,11,'🛡️ FSCS → Protects savings; 📜 Regulator → Checks the rules; 📞 Your bank → Where you ask questions','{"kind": "match", "items": ["Checks the rules", "Protects savings", "Where you ask questions"], "left": ["🛡️ FSCS", "📜 Regulator", "📞 Your bank"]}'::jsonb) on conflict (id) do nothing;
insert into public.cs_questions(id,lesson_id,position,prompt,options,correct_index,explanation,interaction) values ('bank-a3-3','bank-a3',3,'Where do you check the FSCS limit?','["The FSCS website", "A text from a stranger", "Social media"]'::jsonb,0,'The correct answer is: The FSCS website.',null) on conflict (id) do nothing;
insert into public.cs_lessons(id,position,title,description,reading,journey_id,journey_position,unit_index,reading_cards,checklist,sources,reviewed_at) values ('bank-b1',203,'Download and log in','Find the app. Learn with everyday examples.','Find the app

Open your phone’s app store and search for NatWest. Choose the one made by NatWest.

In everyday terms / at a branch: Like finding the right branch on the high street.

Log in

Enter your details. The app may send a code to your phone.

In everyday terms / at a branch: Like showing your ID at the counter.

Make it quick

Set Face ID, a fingerprint or a passcode. Next time you log in faster.

In everyday terms / at a branch: Like staff who know your face.','banking-basics',4,1,'["Find the app\n\nOpen your phone’s app store and search for NatWest. Choose the one made by NatWest.\n\nIn everyday terms / at a branch: Like finding the right branch on the high street.", "Log in\n\nEnter your details. The app may send a code to your phone.\n\nIn everyday terms / at a branch: Like showing your ID at the counter.", "Make it quick\n\nSet Face ID, a fingerprint or a passcode. Next time you log in faster.\n\nIn everyday terms / at a branch: Like staff who know your face."]'::jsonb,'["Practise explaining one thing from this lesson in your own words.", "Write down anything you want to ask your bank. Never enter real account details in this prototype."]'::jsonb,'[{"title": "NatWest · Using the app", "url": "https://www.natwest.com/banking-with-natwest/natwest-app/how-to-use-the-natwest-app.html"}, {"title": "NatWest · Account details", "url": "https://www.natwest.com/support-centre/view-or-change-your-details/find-account-details/where-can-i-find-my-account-number-and-sort-code.html"}, {"title": "NatWest · Pending payments", "url": "https://www.natwest.com/current-accounts/bank-account-guides/pending-transactions.html"}, {"title": "FSCS · Deposit protection", "url": "https://www.fscs.org.uk/what-we-cover/banks-building-societies-credit-unions/deposit-limit/"}, {"title": "Government cyber security · Website checks", "url": "https://www.cyber.gc.ca/en/guidance/shopping-online-safely-itsap00071"}]'::jsonb,'2026-11-07') on conflict (id) do nothing;
insert into public.cs_questions(id,lesson_id,position,prompt,options,correct_index,explanation,interaction) values ('bank-b1-1','bank-b1',1,'Put these in order','["[0,1,2,3]", "[0,1,3,2]", "[0,2,1,3]", "[0,2,3,1]", "[0,3,1,2]", "[0,3,2,1]", "[1,0,2,3]", "[1,0,3,2]", "[1,2,0,3]", "[1,2,3,0]", "[1,3,0,2]", "[1,3,2,0]", "[2,0,1,3]", "[2,0,3,1]", "[2,1,0,3]", "[2,1,3,0]", "[2,3,0,1]", "[2,3,1,0]", "[3,0,1,2]", "[3,0,2,1]", "[3,1,0,2]", "[3,1,2,0]", "[3,2,0,1]", "[3,2,1,0]"]'::jsonb,16,'Open the app store → Search for NatWest → Download the app → Log in','{"kind": "order", "items": ["Download the app", "Log in", "Open the app store", "Search for NatWest"]}'::jsonb) on conflict (id) do nothing;
insert into public.cs_questions(id,lesson_id,position,prompt,options,correct_index,explanation,interaction) values ('bank-b1-2','bank-b1',2,'Fill in the gap: Always download apps from your phone’s official ___.','["app store", "text message", "stranger"]'::jsonb,0,'Always download apps from your phone’s official app store.','{"kind": "fill"}'::jsonb) on conflict (id) do nothing;
insert into public.cs_questions(id,lesson_id,position,prompt,options,correct_index,explanation,interaction) values ('bank-b1-3','bank-b1',3,'What makes logging in faster?','["Face ID or a passcode", "Sharing your PIN", "A paper form"]'::jsonb,0,'The correct answer is: Face ID or a passcode.',null) on conflict (id) do nothing;
insert into public.cs_lessons(id,position,title,description,reading,journey_id,journey_position,unit_index,reading_cards,checklist,sources,reviewed_at) values ('bank-b2',204,'Your home screen','Your balance. Learn with everyday examples.','Your balance

Your account shows balances and transactions. Check pending payments and bills still to come before deciding what you can spend.

In everyday terms / at a branch: Like asking the cashier for your balance.

Payments list

Under it is a list of money in and money out. Tap one to see more.

In everyday terms / at a branch: Like a printed statement.

Alerts

Switch on alerts to get a message when money arrives or leaves.

In everyday terms / at a branch: Like a friendly cashier giving you a ring.','banking-basics',5,1,'["Your balance\n\nYour account shows balances and transactions. Check pending payments and bills still to come before deciding what you can spend.\n\nIn everyday terms / at a branch: Like asking the cashier for your balance.", "Payments list\n\nUnder it is a list of money in and money out. Tap one to see more.\n\nIn everyday terms / at a branch: Like a printed statement.", "Alerts\n\nSwitch on alerts to get a message when money arrives or leaves.\n\nIn everyday terms / at a branch: Like a friendly cashier giving you a ring."]'::jsonb,'["Practise explaining one thing from this lesson in your own words.", "Write down anything you want to ask your bank. Never enter real account details in this prototype."]'::jsonb,'[{"title": "NatWest · Using the app", "url": "https://www.natwest.com/banking-with-natwest/natwest-app/how-to-use-the-natwest-app.html"}, {"title": "NatWest · Account details", "url": "https://www.natwest.com/support-centre/view-or-change-your-details/find-account-details/where-can-i-find-my-account-number-and-sort-code.html"}, {"title": "NatWest · Pending payments", "url": "https://www.natwest.com/current-accounts/bank-account-guides/pending-transactions.html"}, {"title": "FSCS · Deposit protection", "url": "https://www.fscs.org.uk/what-we-cover/banks-building-societies-credit-unions/deposit-limit/"}, {"title": "Government cyber security · Website checks", "url": "https://www.cyber.gc.ca/en/guidance/shopping-online-safely-itsap00071"}]'::jsonb,'2026-11-07') on conflict (id) do nothing;
insert into public.cs_questions(id,lesson_id,position,prompt,options,correct_index,explanation,interaction) values ('bank-b2-1','bank-b2',1,'Match the item to its meaning','["[0,0,0]", "[0,0,1]", "[0,0,2]", "[0,1,0]", "[0,1,1]", "[0,1,2]", "[0,2,0]", "[0,2,1]", "[0,2,2]", "[1,0,0]", "[1,0,1]", "[1,0,2]", "[1,1,0]", "[1,1,1]", "[1,1,2]", "[1,2,0]", "[1,2,1]", "[1,2,2]", "[2,0,0]", "[2,0,1]", "[2,0,2]", "[2,1,0]", "[2,1,1]", "[2,1,2]", "[2,2,0]", "[2,2,1]", "[2,2,2]"]'::jsonb,21,'💷 Balance → Money you have now; 🧾 Payments list → Money in and out; 🔔 Alerts → Messages about your money','{"kind": "match", "items": ["Messages about your money", "Money in and out", "Money you have now"], "left": ["💷 Balance", "🧾 Payments list", "🔔 Alerts"]}'::jsonb) on conflict (id) do nothing;
insert into public.cs_questions(id,lesson_id,position,prompt,options,correct_index,explanation,interaction) values ('bank-b2-2','bank-b2',2,'Fill in the gap: Your ___ is shown at the top of the screen.','["balance", "photo", "PIN"]'::jsonb,0,'Your balance is shown at the top of the screen.','{"kind": "fill"}'::jsonb) on conflict (id) do nothing;
insert into public.cs_questions(id,lesson_id,position,prompt,options,correct_index,explanation,interaction) values ('bank-b2-3','bank-b2',3,'Money leaving your account is called…','["A payment", "A prize", "A password"]'::jsonb,0,'The correct answer is: A payment.',null) on conflict (id) do nothing;
insert into public.cs_lessons(id,position,title,description,reading,journey_id,journey_position,unit_index,reading_cards,checklist,sources,reviewed_at) values ('bank-b3',205,'Pay someone','Add the person. Learn with everyday examples.','Add the person

Tap Pay. Add their name, sort code and account number.

In everyday terms / at a branch: Like filling in a paying-in slip.

Check carefully

Check every number. A wrong number can send money to the wrong person.

In everyday terms / at a branch: Like reading the slip twice before you hand it over.

Confirm

Follow the confirmation steps only when you are sure. Check the payment status afterwards: it may be pending, completed or unsuccessful.

In everyday terms / at a branch: Like the cashier stamping your slip.','banking-basics',6,1,'["Add the person\n\nTap Pay. Add their name, sort code and account number.\n\nIn everyday terms / at a branch: Like filling in a paying-in slip.", "Check carefully\n\nCheck every number. A wrong number can send money to the wrong person.\n\nIn everyday terms / at a branch: Like reading the slip twice before you hand it over.", "Confirm\n\nFollow the confirmation steps only when you are sure. Check the payment status afterwards: it may be pending, completed or unsuccessful.\n\nIn everyday terms / at a branch: Like the cashier stamping your slip."]'::jsonb,'["Practise explaining one thing from this lesson in your own words.", "Write down anything you want to ask your bank. Never enter real account details in this prototype."]'::jsonb,'[{"title": "NatWest · Using the app", "url": "https://www.natwest.com/banking-with-natwest/natwest-app/how-to-use-the-natwest-app.html"}, {"title": "NatWest · Account details", "url": "https://www.natwest.com/support-centre/view-or-change-your-details/find-account-details/where-can-i-find-my-account-number-and-sort-code.html"}, {"title": "NatWest · Pending payments", "url": "https://www.natwest.com/current-accounts/bank-account-guides/pending-transactions.html"}, {"title": "FSCS · Deposit protection", "url": "https://www.fscs.org.uk/what-we-cover/banks-building-societies-credit-unions/deposit-limit/"}, {"title": "Government cyber security · Website checks", "url": "https://www.cyber.gc.ca/en/guidance/shopping-online-safely-itsap00071"}]'::jsonb,'2026-11-07') on conflict (id) do nothing;
insert into public.cs_questions(id,lesson_id,position,prompt,options,correct_index,explanation,interaction) values ('bank-b3-1','bank-b3',1,'Put the steps in order','["[0,1,2,3]", "[0,1,3,2]", "[0,2,1,3]", "[0,2,3,1]", "[0,3,1,2]", "[0,3,2,1]", "[1,0,2,3]", "[1,0,3,2]", "[1,2,0,3]", "[1,2,3,0]", "[1,3,0,2]", "[1,3,2,0]", "[2,0,1,3]", "[2,0,3,1]", "[2,1,0,3]", "[2,1,3,0]", "[2,3,0,1]", "[2,3,1,0]", "[3,0,1,2]", "[3,0,2,1]", "[3,1,0,2]", "[3,1,2,0]", "[3,2,0,1]", "[3,2,1,0]"]'::jsonb,18,'Tap Pay → Add name, sort code, account number → Check the numbers → Confirm','{"kind": "order", "items": ["Add name, sort code, account number", "Check the numbers", "Confirm", "Tap Pay"]}'::jsonb) on conflict (id) do nothing;
insert into public.cs_questions(id,lesson_id,position,prompt,options,correct_index,explanation,interaction) values ('bank-b3-2','bank-b3',2,'Fill in the gap: Always ___ the numbers before you pay.','["check", "guess", "hide"]'::jsonb,0,'Always check the numbers before you pay.','{"kind": "fill"}'::jsonb) on conflict (id) do nothing;
insert into public.cs_questions(id,lesson_id,position,prompt,options,correct_index,explanation,interaction) values ('bank-b3-3','bank-b3',3,'Match the numbers','["[0,0,0]", "[0,0,1]", "[0,0,2]", "[0,1,0]", "[0,1,1]", "[0,1,2]", "[0,2,0]", "[0,2,1]", "[0,2,2]", "[1,0,0]", "[1,0,1]", "[1,0,2]", "[1,1,0]", "[1,1,1]", "[1,1,2]", "[1,2,0]", "[1,2,1]", "[1,2,2]", "[2,0,0]", "[2,0,1]", "[2,0,2]", "[2,1,0]", "[2,1,1]", "[2,1,2]", "[2,2,0]", "[2,2,1]", "[2,2,2]"]'::jsonb,19,'6 numbers → Sort code; 8 numbers → Account number; £ → Amount to pay','{"kind": "match", "items": ["Account number", "Amount to pay", "Sort code"], "left": ["6 numbers", "8 numbers", "£"]}'::jsonb) on conflict (id) do nothing;
insert into public.cs_lessons(id,position,title,description,reading,journey_id,journey_position,unit_index,reading_cards,checklist,sources,reviewed_at) values ('bank-c1',206,'Log in online','Go to the website. Learn with everyday examples.','Go to the website

Type natwest.com into your web browser.

In everyday terms / at a branch: Like walking up to the right shop front.

Check the address

Start from the official NatWest website and check the address carefully. HTTPS or a padlock means an encrypted connection, not proof that a website is genuine.

In everyday terms / at a branch: Like checking the sign above the door.

Extra security

You may get a code by text. This is normal. Only you should use it.

In everyday terms / at a branch: Like the cashier asking one more question.','banking-basics',7,2,'["Go to the website\n\nType natwest.com into your web browser.\n\nIn everyday terms / at a branch: Like walking up to the right shop front.", "Check the address\n\nStart from the official NatWest website and check the address carefully. HTTPS or a padlock means an encrypted connection, not proof that a website is genuine.\n\nIn everyday terms / at a branch: Like checking the sign above the door.", "Extra security\n\nYou may get a code by text. This is normal. Only you should use it.\n\nIn everyday terms / at a branch: Like the cashier asking one more question."]'::jsonb,'["Practise explaining one thing from this lesson in your own words.", "Write down anything you want to ask your bank. Never enter real account details in this prototype."]'::jsonb,'[{"title": "NatWest · Using the app", "url": "https://www.natwest.com/banking-with-natwest/natwest-app/how-to-use-the-natwest-app.html"}, {"title": "NatWest · Account details", "url": "https://www.natwest.com/support-centre/view-or-change-your-details/find-account-details/where-can-i-find-my-account-number-and-sort-code.html"}, {"title": "NatWest · Pending payments", "url": "https://www.natwest.com/current-accounts/bank-account-guides/pending-transactions.html"}, {"title": "FSCS · Deposit protection", "url": "https://www.fscs.org.uk/what-we-cover/banks-building-societies-credit-unions/deposit-limit/"}, {"title": "Government cyber security · Website checks", "url": "https://www.cyber.gc.ca/en/guidance/shopping-online-safely-itsap00071"}]'::jsonb,'2026-11-07') on conflict (id) do nothing;
insert into public.cs_questions(id,lesson_id,position,prompt,options,correct_index,explanation,interaction) values ('bank-c1-1','bank-c1',1,'Fill in the gap: The address should say ___.com','["natwest", "free-money", "bank-help"]'::jsonb,0,'The address should say natwest.com','{"kind": "fill"}'::jsonb) on conflict (id) do nothing;
insert into public.cs_questions(id,lesson_id,position,prompt,options,correct_index,explanation,interaction) values ('bank-c1-2','bank-c1',2,'A code arrives by text when you log in. It is…','["Extra security for you", "Something to read to a caller", "A prize"]'::jsonb,0,'The correct answer is: Extra security for you.',null) on conflict (id) do nothing;
insert into public.cs_questions(id,lesson_id,position,prompt,options,correct_index,explanation,interaction) values ('bank-c1-3','bank-c1',3,'Match the word to its meaning','["[0,0,0]", "[0,0,1]", "[0,0,2]", "[0,1,0]", "[0,1,1]", "[0,1,2]", "[0,2,0]", "[0,2,1]", "[0,2,2]", "[1,0,0]", "[1,0,1]", "[1,0,2]", "[1,1,0]", "[1,1,1]", "[1,1,2]", "[1,2,0]", "[1,2,1]", "[1,2,2]", "[2,0,0]", "[2,0,1]", "[2,0,2]", "[2,1,0]", "[2,1,1]", "[2,1,2]", "[2,2,0]", "[2,2,1]", "[2,2,2]"]'::jsonb,7,'🔒 Padlock → Encrypted connection, not proof of a genuine site; 🌐 Browser → Where you open websites; 🔑 Code → Only you use it','{"kind": "match", "items": ["Encrypted connection, not proof of a genuine site", "Only you use it", "Where you open websites"], "left": ["🔒 Padlock", "🌐 Browser", "🔑 Code"]}'::jsonb) on conflict (id) do nothing;
insert into public.cs_lessons(id,position,title,description,reading,journey_id,journey_position,unit_index,reading_cards,checklist,sources,reviewed_at) values ('bank-c2',207,'Statements and settings','Statements. Learn with everyday examples.','Statements

Open Statements to read or download your monthly statements.

In everyday terms / at a branch: Like asking staff for a copy.

Settings

Open Settings to change your phone number or address.

In everyday terms / at a branch: Like filling in a change of address form.

Proof of address

Some places accept a statement as proof of address. Ask them first.

In everyday terms / at a branch: Like asking the branch for a letter.','banking-basics',8,2,'["Statements\n\nOpen Statements to read or download your monthly statements.\n\nIn everyday terms / at a branch: Like asking staff for a copy.", "Settings\n\nOpen Settings to change your phone number or address.\n\nIn everyday terms / at a branch: Like filling in a change of address form.", "Proof of address\n\nSome places accept a statement as proof of address. Ask them first.\n\nIn everyday terms / at a branch: Like asking the branch for a letter."]'::jsonb,'["Practise explaining one thing from this lesson in your own words.", "Write down anything you want to ask your bank. Never enter real account details in this prototype."]'::jsonb,'[{"title": "NatWest · Using the app", "url": "https://www.natwest.com/banking-with-natwest/natwest-app/how-to-use-the-natwest-app.html"}, {"title": "NatWest · Account details", "url": "https://www.natwest.com/support-centre/view-or-change-your-details/find-account-details/where-can-i-find-my-account-number-and-sort-code.html"}, {"title": "NatWest · Pending payments", "url": "https://www.natwest.com/current-accounts/bank-account-guides/pending-transactions.html"}, {"title": "FSCS · Deposit protection", "url": "https://www.fscs.org.uk/what-we-cover/banks-building-societies-credit-unions/deposit-limit/"}, {"title": "Government cyber security · Website checks", "url": "https://www.cyber.gc.ca/en/guidance/shopping-online-safely-itsap00071"}]'::jsonb,'2026-11-07') on conflict (id) do nothing;
insert into public.cs_questions(id,lesson_id,position,prompt,options,correct_index,explanation,interaction) values ('bank-c2-1','bank-c2',1,'Match the item to its job','["[0,0,0]", "[0,0,1]", "[0,0,2]", "[0,1,0]", "[0,1,1]", "[0,1,2]", "[0,2,0]", "[0,2,1]", "[0,2,2]", "[1,0,0]", "[1,0,1]", "[1,0,2]", "[1,1,0]", "[1,1,1]", "[1,1,2]", "[1,2,0]", "[1,2,1]", "[1,2,2]", "[2,0,0]", "[2,0,1]", "[2,0,2]", "[2,1,0]", "[2,1,1]", "[2,1,2]", "[2,2,0]", "[2,2,1]", "[2,2,2]"]'::jsonb,19,'📄 Statement → Record of your money; ⚙️ Settings → Change your details; 🏠 Address → Keep it up to date','{"kind": "match", "items": ["Change your details", "Keep it up to date", "Record of your money"], "left": ["📄 Statement", "⚙️ Settings", "🏠 Address"]}'::jsonb) on conflict (id) do nothing;
insert into public.cs_questions(id,lesson_id,position,prompt,options,correct_index,explanation,interaction) values ('bank-c2-2','bank-c2',2,'Fill in the gap: Keep your phone number and ___ up to date.','["address", "shoe size", "PIN"]'::jsonb,0,'Keep your phone number and address up to date.','{"kind": "fill"}'::jsonb) on conflict (id) do nothing;
insert into public.cs_questions(id,lesson_id,position,prompt,options,correct_index,explanation,interaction) values ('bank-c2-3','bank-c2',3,'Where do you change your phone number?','["Settings", "A cash machine", "A shop"]'::jsonb,0,'The correct answer is: Settings.',null) on conflict (id) do nothing;
insert into public.cs_lessons(id,position,title,description,reading,journey_id,journey_position,unit_index,reading_cards,checklist,sources,reviewed_at) values ('bank-d1',208,'Spot a scam','Scams are common. Learn with everyday examples.','Scams are common

Scammers pretend to be your bank. They call, text or email.

In everyday terms / at a branch: Ask staff through a bank branch or a contact route you found independently; appearances alone do not prove identity.

Never share

Your bank will never ask for your PIN, or ask you to move money to a “safe account”.

In everyday terms / at a branch: A cashier would never ask for your PIN.

Hang up and call back

If unsure, hang up. Use another phone, or make sure the call has ended, then contact your bank using the number on your card.

In everyday terms / at a branch: Or walk into a branch and ask.','banking-basics',9,3,'["Scams are common\n\nScammers pretend to be your bank. They call, text or email.\n\nIn everyday terms / at a branch: Ask staff through a bank branch or a contact route you found independently; appearances alone do not prove identity.", "Never share\n\nYour bank will never ask for your PIN, or ask you to move money to a “safe account”.\n\nIn everyday terms / at a branch: A cashier would never ask for your PIN.", "Hang up and call back\n\nIf unsure, hang up. Use another phone, or make sure the call has ended, then contact your bank using the number on your card.\n\nIn everyday terms / at a branch: Or walk into a branch and ask."]'::jsonb,'["Practise explaining one thing from this lesson in your own words.", "Write down anything you want to ask your bank. Never enter real account details in this prototype."]'::jsonb,'[{"title": "NatWest · Using the app", "url": "https://www.natwest.com/banking-with-natwest/natwest-app/how-to-use-the-natwest-app.html"}, {"title": "NatWest · Account details", "url": "https://www.natwest.com/support-centre/view-or-change-your-details/find-account-details/where-can-i-find-my-account-number-and-sort-code.html"}, {"title": "NatWest · Pending payments", "url": "https://www.natwest.com/current-accounts/bank-account-guides/pending-transactions.html"}, {"title": "FSCS · Deposit protection", "url": "https://www.fscs.org.uk/what-we-cover/banks-building-societies-credit-unions/deposit-limit/"}, {"title": "Government cyber security · Website checks", "url": "https://www.cyber.gc.ca/en/guidance/shopping-online-safely-itsap00071"}]'::jsonb,'2026-11-07') on conflict (id) do nothing;
insert into public.cs_questions(id,lesson_id,position,prompt,options,correct_index,explanation,interaction) values ('bank-d1-1','bank-d1',1,'A caller says “move your money to a safe account”. You…','["Hang up and call your bank", "Do it quickly", "Give your PIN"]'::jsonb,0,'The correct answer is: Hang up and call your bank.',null) on conflict (id) do nothing;
insert into public.cs_questions(id,lesson_id,position,prompt,options,correct_index,explanation,interaction) values ('bank-d1-2','bank-d1',2,'Fill in the gap: Your bank will never ask for your ___.','["PIN", "hello", "time"]'::jsonb,0,'Your bank will never ask for your PIN.','{"kind": "fill"}'::jsonb) on conflict (id) do nothing;
insert into public.cs_questions(id,lesson_id,position,prompt,options,correct_index,explanation,interaction) values ('bank-d1-3','bank-d1',3,'Match the item to its meaning','["[0,0,0]", "[0,0,1]", "[0,0,2]", "[0,1,0]", "[0,1,1]", "[0,1,2]", "[0,2,0]", "[0,2,1]", "[0,2,2]", "[1,0,0]", "[1,0,1]", "[1,0,2]", "[1,1,0]", "[1,1,1]", "[1,1,2]", "[1,2,0]", "[1,2,1]", "[1,2,2]", "[2,0,0]", "[2,0,1]", "[2,0,2]", "[2,1,0]", "[2,1,1]", "[2,1,2]", "[2,2,0]", "[2,2,1]", "[2,2,2]"]'::jsonb,7,'🚨 Scam → A trick to steal money; 📞 Hang up → Stop the call; 💳 Number on card → Safe number to call','{"kind": "match", "items": ["A trick to steal money", "Safe number to call", "Stop the call"], "left": ["🚨 Scam", "📞 Hang up", "💳 Number on card"]}'::jsonb) on conflict (id) do nothing;
insert into public.cs_lessons(id,position,title,description,reading,journey_id,journey_position,unit_index,reading_cards,checklist,sources,reviewed_at) values ('bank-d2',209,'Getting help','Ask in the app. Learn with everyday examples.','Ask in the app

Use Help in the app to chat or call. No question is silly.

In everyday terms / at a branch: Like going to the help desk.

Find a branch

Use the branch finder to see opening times and your nearest branch.

In everyday terms / at a branch: Like asking where the nearest branch is.

Bring someone

You can ask a trusted person to come with you.

In everyday terms / at a branch: Staff are used to helping people who are new.','banking-basics',10,3,'["Ask in the app\n\nUse Help in the app to chat or call. No question is silly.\n\nIn everyday terms / at a branch: Like going to the help desk.", "Find a branch\n\nUse the branch finder to see opening times and your nearest branch.\n\nIn everyday terms / at a branch: Like asking where the nearest branch is.", "Bring someone\n\nYou can ask a trusted person to come with you.\n\nIn everyday terms / at a branch: Staff are used to helping people who are new."]'::jsonb,'["Practise explaining one thing from this lesson in your own words.", "Write down anything you want to ask your bank. Never enter real account details in this prototype."]'::jsonb,'[{"title": "NatWest · Using the app", "url": "https://www.natwest.com/banking-with-natwest/natwest-app/how-to-use-the-natwest-app.html"}, {"title": "NatWest · Account details", "url": "https://www.natwest.com/support-centre/view-or-change-your-details/find-account-details/where-can-i-find-my-account-number-and-sort-code.html"}, {"title": "NatWest · Pending payments", "url": "https://www.natwest.com/current-accounts/bank-account-guides/pending-transactions.html"}, {"title": "FSCS · Deposit protection", "url": "https://www.fscs.org.uk/what-we-cover/banks-building-societies-credit-unions/deposit-limit/"}, {"title": "Government cyber security · Website checks", "url": "https://www.cyber.gc.ca/en/guidance/shopping-online-safely-itsap00071"}]'::jsonb,'2026-11-07') on conflict (id) do nothing;
insert into public.cs_questions(id,lesson_id,position,prompt,options,correct_index,explanation,interaction) values ('bank-d2-1','bank-d2',1,'Where can you ask for help?','["The Help section in the app", "Nowhere", "Only by post"]'::jsonb,0,'The correct answer is: The Help section in the app.',null) on conflict (id) do nothing;
insert into public.cs_questions(id,lesson_id,position,prompt,options,correct_index,explanation,interaction) values ('bank-d2-2','bank-d2',2,'Match the way to get help','["[0,0,0]", "[0,0,1]", "[0,0,2]", "[0,1,0]", "[0,1,1]", "[0,1,2]", "[0,2,0]", "[0,2,1]", "[0,2,2]", "[1,0,0]", "[1,0,1]", "[1,0,2]", "[1,1,0]", "[1,1,1]", "[1,1,2]", "[1,2,0]", "[1,2,1]", "[1,2,2]", "[2,0,0]", "[2,0,1]", "[2,0,2]", "[2,1,0]", "[2,1,1]", "[2,1,2]", "[2,2,0]", "[2,2,1]", "[2,2,2]"]'::jsonb,19,'💬 Chat → Type your question; 📞 Call → Speak to someone; 📍 Branch → Talk face to face','{"kind": "match", "items": ["Speak to someone", "Talk face to face", "Type your question"], "left": ["💬 Chat", "📞 Call", "📍 Branch"]}'::jsonb) on conflict (id) do nothing;
insert into public.cs_questions(id,lesson_id,position,prompt,options,correct_index,explanation,interaction) values ('bank-d2-3','bank-d2',3,'Fill in the gap: You can ___ for help at any time.','["ask", "hide", "wait"]'::jsonb,0,'You can ask for help at any time.','{"kind": "fill"}'::jsonb) on conflict (id) do nothing;
notify pgrst, 'reload schema';
commit;
