import "./globals.css";

export const metadata = {
  title: "Phishing URL Detector",
  description: "ML-powered phishing URL risk checker",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
