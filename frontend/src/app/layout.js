import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";
import { FilterProvider } from "@/context/FilterContext";
import { Toaster } from "react-hot-toast";

export const metadata = {
  title: "Liopleurodon — Global Job Aggregation Platform",
  description: "Discover jobs from 10+ sources. Big tech, VC-backed startups, stealth companies, and remote-first opportunities worldwide.",
  keywords: "jobs, tech jobs, startup jobs, remote jobs, VC-backed, YC, a16z, job search",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet" />
      </head>
      <body suppressHydrationWarning>
        <AuthProvider>
          <FilterProvider>
            {children}
            <Toaster
              position="bottom-right"
              toastOptions={{
                style: {
                  background: '#12121a',
                  color: '#e2e8f0',
                  border: '1px solid #1e1e2e',
                  borderRadius: '12px',
                  fontSize: '14px',
                },
                success: { iconTheme: { primary: '#10b981', secondary: '#12121a' } },
                error: { iconTheme: { primary: '#ef4444', secondary: '#12121a' } },
              }}
            />
          </FilterProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
