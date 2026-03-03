"use client";

interface SortDropdownProps {
  sortBy: string;
  sortOrder: string;
  onChange: (sortBy: string, sortOrder: string) => void;
}

const OPTIONS = [
  { label: "Mais recentes", sortBy: "created_at", sortOrder: "desc" },
  { label: "Mais antigos", sortBy: "created_at", sortOrder: "asc" },
  { label: "Menor preço", sortBy: "current_price", sortOrder: "asc" },
  { label: "Maior preço", sortBy: "current_price", sortOrder: "desc" },
  { label: "Nome A-Z", sortBy: "name", sortOrder: "asc" },
  { label: "Nome Z-A", sortBy: "name", sortOrder: "desc" },
];

export default function SortDropdown({ sortBy, sortOrder, onChange }: SortDropdownProps) {
  const currentValue = `${sortBy}:${sortOrder}`;

  return (
    <select
      value={currentValue}
      onChange={(e) => {
        const [sb, so] = e.target.value.split(":");
        onChange(sb, so);
      }}
      className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
    >
      {OPTIONS.map((opt) => (
        <option key={`${opt.sortBy}:${opt.sortOrder}`} value={`${opt.sortBy}:${opt.sortOrder}`}>
          {opt.label}
        </option>
      ))}
    </select>
  );
}
