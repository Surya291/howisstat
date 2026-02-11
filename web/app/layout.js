import './globals.css';
import GlobalSound from './components/GlobalSound';

export const metadata = {
  title: 'HOW.IS.STAT',
  description: 'Trump Cards Reimagined',
};

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        {children}
        <GlobalSound />
      </body>
    </html>
  );
}
