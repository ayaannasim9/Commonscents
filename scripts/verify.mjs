import assert from 'node:assert/strict';
import { readFile, readdir } from 'node:fs/promises';
import { PGlite } from '@electric-sql/pglite';
import { summarize, dateInLondon } from '../lib/progress.ts';
const db = new PGlite();
try {
  await db.exec('create role anon; create role authenticated; create role service_role;');
  const migrations = new URL('../supabase/migrations/', import.meta.url);
  for (const file of (await readdir(migrations)).filter(f => f.endsWith('.sql')).sort()) {
    await db.exec(await readFile(new URL(file, migrations), 'utf8'));
  }
  const learner='00000000-0000-4000-8000-000000000001';
  const id = () => crypto.randomUUID();
  const submit = async (lesson,answers,attempt=id()) => (await db.query('select cs_complete_lesson($1,$2,$3::jsonb,$4) as result',[learner,lesson,JSON.stringify(answers),attempt])).rows[0].result;
  assert.equal((await db.query('select count(*)::int as n from cs_questions')).rows[0].n,69);
  assert.equal((await db.query('select count(*)::int as n from cs_journeys where visible')).rows[0].n,4);
  await assert.rejects(submit('budget-balance',[1,0,2]),/locked/);
  const fail=await submit('money-map',[1,0,0]);
  assert.equal(fail.passed,false); assert.equal(fail.awarded,0);
  assert.equal((await db.query('select count(*)::int as n from cs_attempts')).rows[0].n,1);
  await assert.rejects(submit('money-map',[0,1]),/Invalid answers/);
  await assert.rejects(submit('money-map',[0,null,2]),/Invalid answer/);
  await assert.rejects(submit('money-map',[0,1,8]),/Invalid answer/);
  const attempt=id();
  const pass=await submit('money-map',[0,1,2],attempt);
  assert.deepEqual(pass,{score:3,total:3,passed:true,awarded:30});
  const replay=await submit('money-map',[0,1,2],attempt);
  assert.equal(replay.awarded,0);
  await assert.rejects(submit('money-map',[1,1,2],attempt),/mismatch/);
  assert.equal((await submit('money-map',[0,1,2])).awarded,0);
  assert.equal((await submit('budget-balance',[1,0,0])).passed,true);
  assert.equal((await db.query('select sum(xp)::int as xp from cs_completions')).rows[0].xp,60);
  assert.equal((await db.query('select active_journey from cs_learners where id=$1',[learner])).rows[0].active_journey,'independent');
  await db.query('insert into cs_learners(id,name) values ($1,$2)',[id(),'New learner']);
  assert.equal((await db.query("select active_journey from cs_learners where name='New learner'")).rows[0].active_journey,'independent');
  // New journeys start independently; old completions do not unlock them.
  await assert.rejects(submit('uni-home',[0,1,2]),/locked/);
  const content = JSON.parse(await readFile(new URL('../content/journeys.json',import.meta.url),'utf8'));
  for (const journey of content) {
    assert.equal(journey.lessons.length,journey.id==='independent'?5:4);
    // Flexible journeys allow starting with the last lesson; guided ones do not.
    if (journey.flexible) {
      const last = journey.lessons.at(-1);
      const response = await submit(last.id,last.questions.map(q=>q.correct_index));
      assert.equal(response.passed,true);
    } else {
      await assert.rejects(submit(journey.lessons.at(-1).id,[0,1,2]),/locked/);
    }
    for (const lesson of journey.lessons) {
      assert.equal(lesson.questions.length,3);
      assert.ok(lesson.reading_cards.length && lesson.checklist.length && lesson.sources.length);
      for (const q of lesson.questions) assert.ok(q.correct_index>=0 && q.correct_index<q.options.length);
      const result = await submit(lesson.id,lesson.questions.map(q=>q.correct_index));
      assert.equal(result.score,3);
      assert.equal(result.passed,true);
      assert.equal((await submit(lesson.id,lesson.questions.map(q=>q.correct_index))).awarded,0);
    }
  }
  assert.equal((await db.query('select sum(xp)::int as xp from cs_completions')).rows[0].xp,570);
  await db.exec('set role anon');
  await assert.rejects(db.query('select * from cs_questions'),/permission denied/);
  await db.exec('reset role');
  assert.equal(dateInLondon(new Date('2026-07-01T23:30:00Z')),'2026-07-02');
  const rows=[{lesson_id:'a',xp:30,completed_at:'2026-11-06T12:00:00Z'},{lesson_id:'b',xp:30,completed_at:'2026-11-05T12:00:00Z'}];
  assert.equal(summarize(rows,new Date('2026-11-07T12:00:00Z')).streak,2);
  assert.equal(summarize(rows,new Date('2026-11-08T12:00:00Z')).streak,0);
  assert.equal(summarize(rows,new Date('2026-11-06T12:00:00Z')).todayXp,30);
  console.log('Passed: migration and seed, grading, failed attempts, unlock enforcement, invalid answers, idempotency, XP uniqueness, anonymous access denial, timezone and streaks; all 17 UK lessons, default journey and shared scam lesson, independent journey unlocking and flexible support journeys.');
} finally { await db.close(); }
