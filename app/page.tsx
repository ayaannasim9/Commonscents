import { overviewMarkup } from './overview-html';
import { loadLearning } from '@/lib/learning';
import OverviewApp from './components/overview-app';
import '../Overview/styles.css';
import './learning-integrated.css';
import './dashboard-integrated.css';
export const dynamic = 'force-dynamic';
export default async function Home() {
  const [markup, initial] = await Promise.all([overviewMarkup(), loadLearning()]);
  return <OverviewApp markup={markup} initial={initial}/>;
}
