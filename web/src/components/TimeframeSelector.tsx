"use client";

interface TimeframeSelectorProps {
  value: string;
  onChange: (value: string) => void;
}

export default function TimeframeSelector({ value, onChange }: TimeframeSelectorProps) {
  const options = [
    { value: "dia", label: "Dia" },
    { value: "semana", label: "Semana" },
    { value: "mes", label: "Mês" },
    { value: "sempre", label: "Sempre" },
  ];

  return (
    <div className="inline-flex rounded-lg bg-[var(--bg-input)] p-1 gap-1">
      {options.map((opt) => (
        <button
          key={opt.value}
          onClick={() => onChange(opt.value)}
          className={`
            px-3 py-1.5 text-xs font-medium rounded-md transition-all
            ${value === opt.value
              ? "bg-[var(--accent)] text-white shadow-sm"
              : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            }
          `}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
