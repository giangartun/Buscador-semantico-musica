import type { Metadata } from 'next';
import { Geist, Geist_Mono } from 'next/font/google';
import LanguageProvider from './language/LanguageProvider';
import './globals.css';

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
});

export const metadata: Metadata = {
  title: 'Buscador Semántico Musical',
  description: 'Ontología de Instrumentos Musicales',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="es"
      translate="no"
      suppressHydrationWarning
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col" translate="no">
        <LanguageProvider>
          {children}
        </LanguageProvider>
      </body>
    </html>
  );
}