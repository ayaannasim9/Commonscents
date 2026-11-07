import 'server-only';
import { createClient } from '@supabase/supabase-js';
export function database() {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_SECRET_KEY || process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !key) throw new Error('Add your Supabase URL and server secret key to .env.local, then restart the app.');
  return createClient(url, key, { auth: { persistSession: false, autoRefreshToken: false } });
}
export const DEMO_LEARNER = '00000000-0000-4000-8000-000000000001';
