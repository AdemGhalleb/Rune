import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { documents } from "@/lib/data/demoData";
import { Icon } from "@/components/ui/Icon";

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const actions = [
  { id: "chat", label: "Start a new chat", meta: "Action", path: "/chat" },
  { id: "practice", label: "Generate practice questions", meta: "Learning", path: "/learning" },
  { id: "settings", label: "Open appearance settings", meta: "Settings", path: "/settings" },
];

export function CommandPalette({ onOpenChange, open }: CommandPaletteProps) {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);

  const results = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    const documentResults = documents.map((document) => ({
      id: document.id,
      label: document.title,
      meta: document.course,
      path: "/documents",
    }));
    const allResults = [...actions, ...documentResults];
    if (!normalizedQuery) {
      return allResults;
    }
    return allResults.filter((result) => `${result.label} ${result.meta}`.toLowerCase().includes(normalizedQuery));
  }, [query]);

  useEffect(() => {
    if (!open) {
      return undefined;
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onOpenChange(false);
      }
      if (event.key === "ArrowDown") {
        event.preventDefault();
        setActiveIndex((currentIndex) => Math.min(currentIndex + 1, results.length - 1));
      }
      if (event.key === "ArrowUp") {
        event.preventDefault();
        setActiveIndex((currentIndex) => Math.max(currentIndex - 1, 0));
      }
      if (event.key === "Enter" && results[activeIndex]) {
        navigate(results[activeIndex].path);
        onOpenChange(false);
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [activeIndex, navigate, onOpenChange, open, results]);

  useEffect(() => {
    setActiveIndex(0);
  }, [query, open]);

  if (!open) {
    return null;
  }

  return (
    <div className="palette-backdrop" onMouseDown={() => onOpenChange(false)} role="presentation">
      <section
        aria-label="Command palette"
        className="command-palette"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <label className="search-field command-search">
          <Icon name="search" size={18} />
          <input
            autoFocus
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search Rune or run a command"
            value={query}
          />
          <kbd>Enter</kbd>
        </label>
        <div className="command-results">
          <p className="eyebrow">Actions / Documents</p>
          {results.map((result, index) => (
            <button
              className={`command-result ${activeIndex === index ? "active" : ""}`}
              key={result.id}
              onClick={() => {
                navigate(result.path);
                onOpenChange(false);
              }}
              onMouseEnter={() => setActiveIndex(index)}
              type="button"
            >
              <span>{result.label}</span>
              <span>{result.meta}</span>
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}
