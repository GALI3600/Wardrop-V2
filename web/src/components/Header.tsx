import Link from "next/link";

export default function Header() {
  return (
    <header className="border-b border-slate-700 bg-slate-900/80 backdrop-blur sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
        <Link href="/" className="text-2xl font-bold text-indigo-500 hover:text-indigo-400 transition">
          Wardrop
        </Link>
        <nav className="flex items-center gap-4">
          <Link href="/" className="text-sm text-slate-400 hover:text-slate-200 transition">
            Produtos
          </Link>
        </nav>
      </div>
    </header>
  );
}
