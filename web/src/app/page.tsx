import Link from "next/link";
import {
  TrendingDown,
  ShoppingBag,
  Layers,
  Chrome,
  Download,
  ArrowRight,
  MousePointerClick,
  PiggyBank,
} from "lucide-react";
import DashboardShowcase from "@/components/DashboardShowcase";
import ExtensionPreview from "@/components/ExtensionPreview";

const MARKETPLACES = [
  { name: "Amazon", domain: "amazon.com.br" },
  { name: "Mercado Livre", domain: "mercadolivre.com.br" },
  { name: "Magalu", domain: "magazineluiza.com.br" },
  { name: "Shopee", domain: "shopee.com.br" },
  { name: "Casas Bahia", domain: "casasbahia.com.br" },
  { name: "Americanas", domain: "americanas.com.br" },
  { name: "Kabum", domain: "kabum.com.br" },
  { name: "AliExpress", domain: "aliexpress.com" },
];

const FEATURES = [
  {
    icon: TrendingDown,
    title: "Histórico de Preços",
    description:
      "Acompanhe a evolução do preço de qualquer produto com gráficos detalhados e saiba o melhor momento para comprar.",
  },
  {
    icon: ShoppingBag,
    title: "Multi-marketplace",
    description:
      "Compare preços entre 8 marketplaces brasileiros em um único painel, sem precisar abrir várias abas.",
  },
  {
    icon: Layers,
    title: "Agrupamento Inteligente",
    description:
      "Produtos iguais de diferentes lojas são agrupados automaticamente para facilitar a comparação.",
  },
  {
    icon: Chrome,
    title: "Extensão para Chrome",
    description:
      "Adicione produtos ao Wardrop diretamente da página da loja com um único clique no botão de rastreamento.",
  },
];

const STEPS = [
  {
    number: "1",
    icon: Download,
    title: "Instale a extensão",
    description:
      "Baixe a extensão para Chrome e ela ficará disponível em todos os marketplaces suportados.",
  },
  {
    number: "2",
    icon: MousePointerClick,
    title: "Rastreie produtos",
    description:
      "Navegue normalmente pelas lojas e clique em \"Rastrear\" nos produtos que deseja monitorar.",
  },
  {
    number: "3",
    icon: PiggyBank,
    title: "Economize",
    description:
      "Acompanhe o histórico de preços no painel web e compre no momento certo, pelo menor preço.",
  },
];

export default function LandingPage() {
  return (
    <div className="-mx-4 -mt-6">
      {/* Hero */}
      <section className="px-4 pt-16 pb-24 text-center">
        <div className="max-w-3xl mx-auto">
          <div className="flex justify-center mb-6">
            <div className="w-20 h-20 rounded-2xl bg-[var(--accent)] flex items-center justify-center text-white text-4xl font-bold shadow-lg">
              W
            </div>
          </div>
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight mb-4">
            Pare de pagar caro.{" "}
            <span className="text-[var(--accent)]">Rastreie preços</span> nos
            maiores marketplaces.
          </h1>
          <p className="text-lg text-[var(--text-secondary)] mb-8 max-w-2xl mx-auto">
            O Wardrop monitora preços em 8 marketplaces brasileiros, agrupa
            produtos iguais e mostra o histórico completo para você comprar no
            momento certo.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <a
              href="#"
              className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-[var(--accent)] text-white font-semibold hover:bg-[var(--accent-hover)] transition shadow-lg"
            >
              <Download className="w-5 h-5" />
              Instalar Extensão
            </a>
            <Link
              href="/produtos"
              className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl border border-[var(--border-color)] text-[var(--text-primary)] font-semibold hover:bg-[var(--bg-hover)] transition"
            >
              Ver Produtos
              <ArrowRight className="w-5 h-5" />
            </Link>
          </div>
        </div>
      </section>

      {/* Screenshot showcase — live data */}
      <section className="px-4 pb-20">
        <div className="max-w-6xl mx-auto">
          <DashboardShowcase />
        </div>
      </section>

      {/* Features grid */}
      <section className="px-4 py-16">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-bold text-center mb-12">
            Tudo que você precisa para{" "}
            <span className="text-[var(--accent)]">economizar</span>
          </h2>
          <div className="grid sm:grid-cols-2 gap-6">
            {FEATURES.map((feature) => (
              <div
                key={feature.title}
                className="p-6 rounded-2xl border border-[var(--border-color)] bg-[var(--bg-card)] hover:shadow-lg transition"
              >
                <div className="w-12 h-12 rounded-xl bg-[var(--accent-muted)] flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-[var(--accent)]" />
                </div>
                <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                <p className="text-[var(--text-secondary)] text-sm leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Supported marketplaces */}
      <section className="px-4 py-16">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-2xl sm:text-3xl font-bold mb-4">
            8 marketplaces em um só lugar
          </h2>
          <p className="text-[var(--text-secondary)] mb-10">
            Monitoramos os principais marketplaces do Brasil para você.
          </p>
          <div className="flex flex-wrap justify-center gap-6">
            {MARKETPLACES.map((mp) => (
              <div
                key={mp.name}
                className="flex flex-col items-center gap-2"
              >
                <div className="w-14 h-14 rounded-2xl bg-[var(--bg-card)] border border-[var(--border-color)] flex items-center justify-center shadow-sm">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={`https://www.google.com/s2/favicons?domain=${mp.domain}&sz=32`}
                    alt={mp.name}
                    width={32}
                    height={32}
                  />
                </div>
                <span className="text-xs text-[var(--text-muted)]">
                  {mp.name}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="px-4 py-16">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-bold text-center mb-4">
            Como funciona
          </h2>
          <p className="text-[var(--text-secondary)] text-center mb-12 max-w-xl mx-auto">
            Três passos simples para nunca mais pagar caro.
          </p>

          <div className="relative">
            {/* Connector line — hidden on mobile */}
            <div className="hidden sm:block absolute top-10 left-[calc(16.67%+28px)] right-[calc(16.67%+28px)] h-0.5 bg-[var(--border-color)]" />

            <div className="grid sm:grid-cols-3 gap-10 sm:gap-6">
              {STEPS.map((step) => (
                <div key={step.number} className="relative flex flex-col items-center text-center">
                  {/* Number badge + icon */}
                  <div className="relative mb-5">
                    <div className="w-20 h-20 rounded-2xl bg-[var(--accent-muted)] flex items-center justify-center">
                      <step.icon className="w-9 h-9 text-[var(--accent)]" />
                    </div>
                    <span className="absolute -top-2 -right-2 w-7 h-7 rounded-full bg-[var(--accent)] text-white text-sm font-bold flex items-center justify-center shadow-md ring-2 ring-[var(--bg-body)]">
                      {step.number}
                    </span>
                  </div>

                  <h3 className="text-lg font-semibold mb-2">{step.title}</h3>
                  <p className="text-[var(--text-secondary)] text-sm leading-relaxed max-w-[240px]">
                    {step.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Extension preview */}
      <section className="px-4 py-16">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-bold text-center mb-4">
            A extensão que faz o trabalho por você
          </h2>
          <p className="text-[var(--text-secondary)] text-center mb-10 max-w-2xl mx-auto">
            Basta navegar normalmente. Quando encontrar um produto, clique em
            &quot;Rastrear&quot; e o Wardrop cuida do resto.
          </p>
          <ExtensionPreview />
        </div>
      </section>

      {/* CTA footer */}
      <section className="relative pt-16 pb-20 overflow-hidden">
        {/* Animated arrows scattered across the section */}
        {[
          { top: "18%", left: "6%", delay: "0s", size: "w-5 h-5" },
          { top: "50%", left: "12%", delay: "0.8s", size: "w-4 h-4" },
          { top: "78%", left: "4%", delay: "1.4s", size: "w-5 h-5" },
          { top: "35%", left: "18%", delay: "0.4s", size: "w-3 h-3" },
          { top: "22%", right: "8%", delay: "0.5s", size: "w-5 h-5" },
          { top: "55%", right: "14%", delay: "1.1s", size: "w-4 h-4" },
          { top: "80%", right: "5%", delay: "0.2s", size: "w-5 h-5" },
          { top: "40%", right: "20%", delay: "1.6s", size: "w-3 h-3" },
        ].map((arrow, i) => (
          <svg
            key={i}
            className={`absolute ${arrow.size} text-[var(--accent)] pointer-events-none`}
            style={{
              top: arrow.top,
              left: arrow.left,
              right: arrow.right,
              opacity: 0.15,
              animation: `float-down 2s ease-in-out ${arrow.delay} infinite`,
            }}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M12 5v14M19 12l-7 7-7-7" />
          </svg>
        ))}

        <div className="relative max-w-2xl mx-auto flex flex-col items-center text-center px-4">
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight mb-4">
            Comece a{" "}
            <span className="text-[var(--accent)]">economizar</span> agora
          </h2>
          <p className="text-[var(--text-secondary)] mb-10 max-w-md text-lg leading-relaxed">
            Instale a extensão gratuitamente e tenha o controle total sobre os
            preços dos produtos que você acompanha.
          </p>

          <a
            href="#"
            className="inline-flex items-center justify-center gap-2.5 px-10 py-4 rounded-2xl bg-[var(--accent)] text-white font-bold text-lg hover:bg-[var(--accent-hover)] hover:scale-105 transition-all shadow-lg"
          >
            <Chrome className="w-5 h-5" />
            Instalar Extensão Grátis
          </a>
          <span className="mt-4 text-[var(--text-muted)] text-sm">
            Disponível para Google Chrome — 100% gratuito
          </span>
        </div>
      </section>
    </div>
  );
}
