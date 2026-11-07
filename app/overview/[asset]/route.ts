import { readFile } from 'node:fs/promises';
import path from 'node:path';

const assets: Record<string, string> = {
  'app.js': 'text/javascript; charset=utf-8',
  'styles.css': 'text/css; charset=utf-8',
  'ml-bridge.js': 'text/javascript; charset=utf-8',
};

export async function GET(_request: Request, context: { params: Promise<{ asset: string }> }) {
  const { asset } = await context.params;
  if (!Object.hasOwn(assets, asset)) return new Response('Not found', { status: 404 });
  const content = await readFile(path.join(process.cwd(), 'Overview', asset), 'utf8');
  return new Response(content, { headers: { 'Content-Type': assets[asset] } });
}
