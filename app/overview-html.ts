import { readFile } from 'node:fs/promises';
import path from 'node:path';
export async function overviewMarkup() {
  const html = await readFile(path.join(process.cwd(), 'Overview/index.html'), 'utf8');
  return html.split('<body>')[1].split('</body>')[0].replace(/<script[\s\S]*?<\/script>/g, '');
}
