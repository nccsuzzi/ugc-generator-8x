import type { Metadata } from 'next';
import { Syne, Plus_Jakarta_Sans } from 'next/font/google';
import './globals.css';
import Header from '../components/Header';

const syne = Syne({
  subsets: ['latin'],
  weight: ['600', '700', '800'],
  variable: '--font-syne',
  display: 'swap',
});

const plusJakarta = Plus_Jakarta_Sans({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-sans',
  display: 'swap',
});

export const metadata: Metadata = {
  title: '8x UGC Studio — AI UGC Video Generator',
  description: 'Assemble high-converting 9:16 UGC video ads from any product URL using licensed media.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${syne.variable} ${plusJakarta.variable} h-full overflow-hidden bg-[#ffffff]`}
    >
      <body
        suppressHydrationWarning
        className="h-full flex flex-col overflow-hidden bg-[#ffffff] text-[#0e121b] font-sans antialiased selection:bg-[#0021cc]/15"
      >
        <Header />
        <main className="flex-1 flex flex-col min-h-0 overflow-hidden">{children}</main>
      </body>
    </html>
  );
}
