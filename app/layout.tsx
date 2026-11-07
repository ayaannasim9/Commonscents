import type { Metadata } from 'next';
export const metadata: Metadata = { title: 'NatWise — Your financial future', description: 'Explore your financial future and build practical money skills.' };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en-GB"><body>{children}</body></html>;
}
