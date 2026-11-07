import 'server-only';
import { database, DEMO_LEARNER } from './supabase';
import { summarize } from './progress';
import type { LearningState } from './types';
export async function loadLearning(): Promise<LearningState> {
  try {
    const db = database();
    const [lessons, completions, journeys, learner] = await Promise.all([
      db.from('cs_lessons').select('*').order('journey_position'),
      db.from('cs_completions').select('lesson_id,xp,completed_at').eq('learner_id', DEMO_LEARNER),
      db.from('cs_journeys').select('id,title,description,units,flexible').eq('visible',true).order('position'),
      db.from('cs_learners').select('active_journey').eq('id',DEMO_LEARNER).single()
    ]);
    if (lessons.error || completions.error || journeys.error || learner.error) throw new Error('The UK journeys database update is not ready. Apply the repository migrations to your Supabase project.');
    if (!lessons.data?.length || !journeys.data?.length) throw new Error('Run the supplied migrations to load your learning journeys.');
    return { lessons: lessons.data, journeys: journeys.data, activeJourney: learner.data.active_journey, progress: summarize(completions.data ?? []), error: null };
  } catch (e) {
    return { lessons: [], journeys: [], activeJourney: 'independent', progress: {completed: [], xp: 0, streak: 0, todayXp: 0}, error: e instanceof Error ? e.message : 'Could not connect to Supabase.' };
  }
}
