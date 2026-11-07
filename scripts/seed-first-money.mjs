import {createClient} from '@supabase/supabase-js';
import {readFile} from 'node:fs/promises';
const db=createClient(process.env.SUPABASE_URL,process.env.SUPABASE_SECRET_KEY||process.env.SUPABASE_SERVICE_ROLE_KEY,{auth:{persistSession:false}});
const data=JSON.parse(await readFile(new URL('../content/first-money-practice-seed.json',import.meta.url),'utf8'));
for(const [table,rows] of [['cs_lessons',data.lessons],['cs_questions',data.questions]]){const {error}=await db.from(table).upsert(rows,{onConflict:'id',ignoreDuplicates:true});if(error)throw new Error(error.message);}
for(let position=1;position<=5;position++){const {error}=await db.from('cs_lessons').update({unit_index:Math.floor((position-1)/2)}).eq('journey_id','independent').eq('journey_position',position);if(error)throw new Error(error.message);}
const {error}=await db.from('cs_journeys').update({units:data.units}).eq('id','independent');if(error)throw new Error(error.message);
console.log('Added two first-time money lessons; existing progress preserved.');
