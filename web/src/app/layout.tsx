import type { Metadata } from 'next';
import { AuthProvider } from '@/context/AuthContext';
import { Header } from '@/components/Header';
import './globals.css';

export const metadata: Metadata = {
  title: 'Shree Hari Beauty',
  description: 'Natural beauty products — oils, facewash, creams',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <Header />
          <main className="container" style={{ paddingBottom: '3rem' }}>
            {children}
          </main>
        </AuthProvider>
      </body>
    </html>
  );
}
