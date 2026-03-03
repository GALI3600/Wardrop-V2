import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import QueryProvider from "@/providers/QueryProvider";
import ThemeProvider from "@/providers/ThemeProvider";
import Header from "@/components/Header";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Wardrop - Comparador de Preços",
  description: "Compare preços entre marketplaces brasileiros",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem("wardrop-theme");if(t==="dark")document.documentElement.classList.add("dark")}catch(e){}})()`,
          }}
        />
      </head>
      <body className={`${inter.className} bg-[var(--bg-body)] text-[var(--text-primary)] min-h-screen`}>
        <QueryProvider>
          <ThemeProvider>
            <Header />
            <main className="max-w-7xl mx-auto px-4 py-6">{children}</main>
          </ThemeProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
