import { loadLearning } from '@/lib/learning';
import LearningApp from './components/learning-app';
export const dynamic = 'force-dynamic';
export default async function Home() { return <LearningApp initial={await loadLearning()} />; }
