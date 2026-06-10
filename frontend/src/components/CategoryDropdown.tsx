// Custom dropdown for the category step. Replaces the native <select> so the
// styling stays on-brand (no macOS / Windows native styling popping in).
//
// Behaviour:
//   - click the trigger → list opens below
//   - click an item → selects + closes
//   - click outside, Escape, or blur → closes
//   - arrow keys + Enter for keyboard navigation
//   - opens floating above the SunRays (z-index high)

import { useEffect, useRef, useState } from "react";
import type { CannesCategory } from "../types";

interface Props {
  categories: CannesCategory[];
  value: string;
  onChange: (key: string) => void;
  onConfirm?: () => void; // called when user presses Enter on a selected item
}

export function CategoryDropdown({ categories, value, onChange, onConfirm }: Props) {
  const [open, setOpen] = useState(false);
  const [highlight, setHighlight] = useState<number>(() =>
    Math.max(0, categories.findIndex((c) => c.key === value)),
  );
  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  const selected = categories.find((c) => c.key === value);

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    const onDocClick = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, [open]);

  // Reset highlight to selected when opening
  useEffect(() => {
    if (open) {
      const idx = categories.findIndex((c) => c.key === value);
      setHighlight(idx >= 0 ? idx : 0);
    }
  }, [open, categories, value]);

  function handleKeyDown(e: React.KeyboardEvent) {
    if (!open) {
      if (e.key === "Enter" || e.key === " " || e.key === "ArrowDown") {
        e.preventDefault();
        setOpen(true);
      } else if (e.key === "Enter" && onConfirm) {
        e.preventDefault();
        onConfirm();
      }
      return;
    }
    // Open: navigate the list
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlight((h) => Math.min(categories.length - 1, h + 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlight((h) => Math.max(0, h - 1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      const pick = categories[highlight];
      if (pick) {
        onChange(pick.key);
        setOpen(false);
        triggerRef.current?.focus();
      }
    } else if (e.key === "Escape") {
      e.preventDefault();
      setOpen(false);
      triggerRef.current?.focus();
    }
  }

  return (
    <div ref={rootRef} className="relative" onKeyDown={handleKeyDown}>
      <button
        ref={triggerRef}
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="listbox"
        aria-expanded={open}
        className="w-full bg-transparent border-b border-ink text-center editorial text-xl py-1.5 focus:outline-none cursor-pointer flex items-center justify-center gap-2"
      >
        <span className={selected ? "" : "text-ink-faint italic"}>
          {selected?.label ?? "Loading…"}
        </span>
        <svg
          width="12"
          height="12"
          viewBox="0 0 12 12"
          aria-hidden
          className={`transition-transform ${open ? "rotate-180" : ""}`}
        >
          <path d="M2 4 L6 8 L10 4" stroke="currentColor" strokeWidth="1.4" fill="none" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>

      {open && (
        <ul
          role="listbox"
          className="absolute left-1/2 -translate-x-1/2 top-[110%] z-50 mt-1 w-full min-w-[20rem] max-h-72 overflow-y-auto bg-cream border border-ink shadow-[0_6px_20px_rgba(15,14,12,0.08)]"
        >
          {categories.map((cat, i) => {
            const isSelected = cat.key === value;
            const isHighlighted = i === highlight;
            return (
              <li
                key={cat.key}
                role="option"
                aria-selected={isSelected}
                onMouseEnter={() => setHighlight(i)}
                onClick={() => {
                  onChange(cat.key);
                  setOpen(false);
                  triggerRef.current?.focus();
                }}
                className={`px-4 py-2 cursor-pointer flex items-center gap-2 text-base ${
                  isHighlighted ? "bg-cream-soft" : ""
                } ${isSelected ? "font-medium" : ""}`}
              >
                <span
                  className={`block w-1.5 h-1.5 rounded-full flex-none ${
                    isSelected ? "bg-ink" : "bg-transparent"
                  }`}
                  aria-hidden
                />
                <span className="flex-1 text-left">{cat.label}</span>
                <span className="label-caps text-[0.65rem]">{cat.family}</span>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
