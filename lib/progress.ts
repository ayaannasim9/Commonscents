import type { Progress } from './types';
export function dateInLondon(date: Date): string {
  return new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/London', year: 'numeric', month: '2-digit', day: '2-digit' }).format(date);
}
export function summarize(rows: { lesson_id: string; xp: number; completed_at: string }[], now = new Date()): Progress {
  const today = dateInLondon(now);
  const days = new Set(rows.map(r => dateInLondon(new Date(r.completed_at))));
  const cursor = new Date(today + 'T12:00:00Z');
  if (!days.has(today)) cursor.setUTCDate(cursor.getUTCDate() - 1);
  let streak = 0;
  while (days.has(cursor.toISOString().slice(0,10))) { streak++; cursor.setUTCDate(cursor.getUTCDate() - 1); }
  return { completed: rows.map(r => r.lesson_id), xp: rows.reduce((n,r) => n+r.xp,0), streak, todayXp: rows.filter(r => dateInLondon(new Date(r.completed_at)) === today).reduce((n,r) => n+r.xp,0) };
}
