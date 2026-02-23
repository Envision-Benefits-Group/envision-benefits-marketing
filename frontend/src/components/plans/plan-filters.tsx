"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { LayoutGrid, List, X } from "lucide-react";
import type { BrowseFilters } from "@/types/plans";

const CARRIERS = [
  "IHA",
  "Highmark",
  "Univera",
  "Excellus",
];

const YEARS = [2024, 2025, 2026, 2027];
const QUARTERS = ["Q1", "Q2", "Q3", "Q4"];
const NETWORKS = ["POS", "PPO", "HealthyNY"];

interface PlanFiltersProps {
  filters: BrowseFilters;
  onFiltersChange: (filters: BrowseFilters) => void;
  viewMode: "grid" | "list";
  onViewModeChange: (mode: "grid" | "list") => void;
  onDownloadMasterTemplate: () => void;
  isDownloading: boolean;
}

export function PlanFilters({
  filters,
  onFiltersChange,
  viewMode,
  onViewModeChange,
  onDownloadMasterTemplate,
  isDownloading,
}: PlanFiltersProps) {
  const hasFilters =
    filters.carrier || filters.year || filters.quarter || filters.network_type;

  return (
    <div className="flex flex-wrap items-center gap-3">
      <Select
        value={filters.carrier || ""}
        onValueChange={(v) =>
          onFiltersChange({ ...filters, carrier: v || undefined })
        }
      >
        <SelectTrigger className="w-[160px]">
          <SelectValue placeholder="All Carriers" />
        </SelectTrigger>
        <SelectContent>
          {CARRIERS.map((c) => (
            <SelectItem key={c} value={c}>
              {c}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={filters.year?.toString() || ""}
        onValueChange={(v) =>
          onFiltersChange({ ...filters, year: v ? Number(v) : undefined })
        }
      >
        <SelectTrigger className="w-[120px]">
          <SelectValue placeholder="All Years" />
        </SelectTrigger>
        <SelectContent>
          {YEARS.map((y) => (
            <SelectItem key={y} value={y.toString()}>
              {y}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={filters.quarter || ""}
        onValueChange={(v) =>
          onFiltersChange({ ...filters, quarter: v || undefined })
        }
      >
        <SelectTrigger className="w-[120px]">
          <SelectValue placeholder="All Quarters" />
        </SelectTrigger>
        <SelectContent>
          {QUARTERS.map((q) => (
            <SelectItem key={q} value={q}>
              {q}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={filters.network_type || ""}
        onValueChange={(v) =>
          onFiltersChange({ ...filters, network_type: v || undefined })
        }
      >
        <SelectTrigger className="w-[140px]">
          <SelectValue placeholder="All Networks" />
        </SelectTrigger>
        <SelectContent>
          {NETWORKS.map((n) => (
            <SelectItem key={n} value={n}>
              {n}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {hasFilters && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onFiltersChange({})}
        >
          <X className="h-4 w-4 mr-1" />
          Clear
        </Button>
      )}

      <div className="ml-auto flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={onDownloadMasterTemplate}
          disabled={isDownloading || !filters.year || !filters.quarter}
          title={
            !filters.year || !filters.quarter
              ? "Select year and quarter to download"
              : "Download Master Template"
          }
        >
          {isDownloading ? "Downloading..." : "Download Master Template"}
        </Button>

        <div className="flex border rounded-md">
          <Button
            variant={viewMode === "grid" ? "default" : "ghost"}
            size="icon"
            className="h-8 w-8 rounded-r-none"
            onClick={() => onViewModeChange("grid")}
          >
            <LayoutGrid className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === "list" ? "default" : "ghost"}
            size="icon"
            className="h-8 w-8 rounded-l-none"
            onClick={() => onViewModeChange("list")}
          >
            <List className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
