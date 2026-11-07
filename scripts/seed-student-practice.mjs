// Apply the data-only migration through HTTPS when direct PostgreSQL is unavailable.
// Run: node --env-file=.env.local scripts/seed-student-practice.mjs
import {createClient} from '@supabase/supabase-js';
import {readFile} from 'node:fs/promises';
const db=createClient(process.env.SUPABASE_URL,process.env.SUPABASE_SECRET_KEY||process.env.SUPABASE_SERVICE_ROLE_KEY,{auth:{persistSession:false}});
const journey=JSON.parse(await readFile(new URL('../content/journeys.json',import.meta.url),'utf8')).find(j=>j.id==='university');
const ids=['uni-food','uni-split','uni-surprise'];
const lessons=ids.map((id,i)=>{const l=journey.lessons.find(l=>l.id===id);return {id,position:300+i,title:l.title,description:l.description,reading:l.reading_cards.join(' '),minutes:3,xp:30,journey_id:'university',journey_position:5+i,reading_cards:l.reading_cards,checklist:l.checklist,sources:[],reviewed_at:null};});
const questions=ids.flatMap(id=>journey.lessons.find(l=>l.id===id).questions.map((q,i)=>({id:`${id}-${i+1}`,lesson_id:id,position:i+1,...q})));
for(const [table,rows] of [['cs_lessons',lessons],['cs_questions',questions]]){const {error}=await db.from(table).upsert(rows,{onConflict:'id',ignoreDuplicates:true});if(error)throw new Error(`${table}: ${error.message}`);}
const {error}=await db.from('cs_journeys').update({units:journey.units}).eq('id','university');if(error)throw new Error(error.message);
const result=await db.from('cs_lessons').select('id').eq('journey_id','university');if(result.error)throw new Error(result.error.message);
console.log(`University journey now contains ${result.data.length} lessons.`);
