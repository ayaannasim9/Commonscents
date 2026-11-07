import { NextRequest, NextResponse } from 'next/server';
import { database, DEMO_LEARNER } from '@/lib/supabase';
import { loadLearning } from '@/lib/learning';
export async function GET(request: NextRequest) {
  const lessonId = request.nextUrl.searchParams.get('lesson');
  if (!lessonId) return NextResponse.json(await loadLearning());
  try {
    const state = await loadLearning();
    if (state.error) return NextResponse.json({error: state.error}, {status: 503});
    const lesson = state.lessons.find(l => l.id === lessonId);
    const journey = state.journeys.find(j => j.id === lesson?.journey_id);
    const locked = lesson && !journey?.flexible && state.lessons.some(l => l.journey_id === lesson.journey_id && (l.journey_position ?? l.position) < (lesson.journey_position ?? lesson.position) && !state.progress.completed.includes(l.id));
    if (!lesson || !journey || locked) return NextResponse.json({error:'Complete the previous lesson first.'}, {status:403});
    const {data, error} = await database().from('cs_questions').select('id,prompt,options,position,interaction').eq('lesson_id',lessonId).order('position');
    if (error || !data?.length) throw new Error();
    return NextResponse.json({questions:data});
  } catch { return NextResponse.json({error:'Could not load this lesson. Check your database connection.'}, {status:503}); }
}
export async function POST(request: NextRequest) {
  // The no-auth demo is intended only for the loopback development server.
  // Next.js can normalize nextUrl to localhost even when the browser uses 127.0.0.1.
  // Match the actual Host header and allow only this prototype's loopback hosts.
  const host = request.headers.get('host');
  if (!host || !/^(127\.0\.0\.1|localhost)(:\d+)?$/.test(host) || request.headers.get('origin') !== `http://${host}`) return NextResponse.json({error:'Invalid request origin.'},{status:403});
  let body;
  try { body = await request.json(); } catch { return NextResponse.json({error:'Invalid request.'},{status:400}); }
  try {
    const db = database();
    if (body.action === 'journey') {
      if (typeof body.journeyId !== 'string') return NextResponse.json({error:'Choose a journey.'},{status:400});
      const {data:journey} = await db.from('cs_journeys').select('id').eq('id',body.journeyId).eq('visible',true).single();
      if (!journey) return NextResponse.json({error:'Journey unavailable.'},{status:400});
      const {error} = await db.from('cs_learners').update({active_journey:journey.id}).eq('id',DEMO_LEARNER);
      if (error) throw error;
      return NextResponse.json({state:await loadLearning()});
    }
    if (body.action === 'check') {
      if (typeof body.questionId !== 'string' || !Number.isInteger(body.answer)) return NextResponse.json({error:'Choose an answer.'},{status:400});
      const {data:q,error} = await db.from('cs_questions').select('correct_index,explanation,options').eq('id',body.questionId).single();
      if (error || !q || body.answer < 0 || body.answer >= q.options.length) return NextResponse.json({error:'Invalid question or answer.'},{status:400});
      return NextResponse.json({correct:body.answer === q.correct_index, correctIndex:q.correct_index, explanation:q.explanation});
    }
    if (body.action !== 'complete' || typeof body.lessonId !== 'string' || !Array.isArray(body.answers) || typeof body.attemptId !== 'string' || !/^[0-9a-f-]{36}$/i.test(body.attemptId)) return NextResponse.json({error:'Invalid lesson attempt.'},{status:400});
    const {data,error} = await db.rpc('cs_complete_lesson', {p_learner:DEMO_LEARNER,p_lesson:body.lessonId,p_answers:body.answers,p_attempt:body.attemptId});
    if (error) return NextResponse.json({error:'Could not save this attempt. Check the lesson is unlocked and try again.'},{status:400});
    return NextResponse.json({...data,state:await loadLearning()});
  } catch { return NextResponse.json({error:'Could not reach Supabase. Your attempt is still open; please retry.'},{status:503}); }
}
