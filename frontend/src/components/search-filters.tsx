import { useState, useEffect } from "react";
import { SearchIcon, ArrowUpIcon, ArrowDownIcon } from "lucide-react";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { YARN_WEIGHTS, SORT_OPTIONS } from "@/data/constants";
import type { YarnWeight } from "@/types";

export interface FilterState {
  search: string;
  weight: YarnWeight | "";
  fibre: string;
  hasProject: "all" | "with" | "without";
  sortBy: string;
  sortDir: "asc" | "desc";
}

interface SearchFiltersProps {
  filters: FilterState;
  onChange: (filters: FilterState) => void;
}

export function SearchFilters({ filters, onChange }: SearchFiltersProps) {
  const [searchInput, setSearchInput] = useState(filters.search);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchInput !== filters.search) {
        onChange({ ...filters, search: searchInput });
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [searchInput]); // eslint-disable-line react-hooks/exhaustive-deps

  // Keep local input in sync if parent resets it
  useEffect(() => {
    setSearchInput(filters.search);
  }, [filters.search]);

  return (
    <div className="flex flex-wrap gap-2 items-center mb-4">
      <div className="relative flex-1 min-w-48">
        <SearchIcon className="absolute left-2.5 top-1/2 -translate-y-1/2 size-4 text-stone-400 pointer-events-none" />
        <Input
          className="pl-8"
          type="text"
          placeholder="Search yarns..."
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
        />
      </div>

      <Select
        value={filters.weight || null}
        onValueChange={(value) =>
          onChange({ ...filters, weight: (value ?? "") as YarnWeight | "" })
        }
      >
        <SelectTrigger className="w-36">
          <SelectValue placeholder="All weights" />
        </SelectTrigger>
        <SelectContent>
          {YARN_WEIGHTS.map((w) => (
            <SelectItem key={w} value={w}>
              {w}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Input
        className="w-40"
        type="text"
        placeholder="Filter by fibre..."
        value={filters.fibre}
        onChange={(e) => onChange({ ...filters, fibre: e.target.value })}
      />

      <Select
        value={filters.hasProject}
        onValueChange={(value) =>
          onChange({ ...filters, hasProject: (value ?? "all") as "all" | "with" | "without" })
        }
      >
        <SelectTrigger className="w-36">
          <SelectValue placeholder="All" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All</SelectItem>
          <SelectItem value="with">With project</SelectItem>
          <SelectItem value="without">Without project</SelectItem>
        </SelectContent>
      </Select>

      <Select
        value={filters.sortBy}
        onValueChange={(value) =>
          onChange({ ...filters, sortBy: value ?? "name" })
        }
      >
        <SelectTrigger className="w-36">
          <SelectValue placeholder="Sort by..." />
        </SelectTrigger>
        <SelectContent>
          {SORT_OPTIONS.map((opt) => (
            <SelectItem key={opt.value} value={opt.value}>
              {opt.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Button
        variant="outline"
        size="icon"
        onClick={() =>
          onChange({ ...filters, sortDir: filters.sortDir === "asc" ? "desc" : "asc" })
        }
        title={filters.sortDir === "asc" ? "Sort ascending" : "Sort descending"}
      >
        {filters.sortDir === "asc" ? (
          <ArrowUpIcon className="size-4" />
        ) : (
          <ArrowDownIcon className="size-4" />
        )}
      </Button>
    </div>
  );
}
