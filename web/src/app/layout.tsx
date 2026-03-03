import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import QueryProvider from "@/providers/QueryProvider";
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
    <html lang="pt-BR" className="dark">
      <body className={`${inter.className} bg-slate-900 text-slate-200 min-h-screen`}>
        <QueryProvider>
          <Header />
          <main className="max-w-7xl mx-auto px-4 py-6">{children}</main>
        </QueryProvider>
      </body>
    </html>
  );
}
