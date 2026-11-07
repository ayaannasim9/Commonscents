export type Journey = { id: string; title: string; description: string; units: string[]; flexible: boolean };
export type Lesson = { id: string; position: number; title: string; description: string; reading: string; minutes: number; xp: number; journey_id?: string; journey_position?: number; reading_cards?: string[]; checklist?: string[]; sources?: {title:string;url:string}[]; reviewed_at?: string };
export type Question = { id: string; prompt: string; options: string[]; position: number };
export type Progress = { completed: string[]; xp: number; streak: number; todayXp: number };
export type LearningState = { lessons: Lesson[]; journeys: Journey[]; activeJourney: string; progress: Progress; error: string | null };
