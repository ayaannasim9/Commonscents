import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = { title: 'Commonscents — A little wiser, every day', description: 'Build money confidence, one small lesson at a time.' };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
