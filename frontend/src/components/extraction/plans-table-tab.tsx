"use client";

import { Fragment, useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ChevronLeft, ChevronRight, Download, Pencil, Search, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import type { BrowseFilters, Plan } from "@/types/plans";

const PAGE_SIZE = 20;
const CARRIERS = ["IHA", "Highmark", "Univera", "Excellus"];
const YEARS = [2024, 2025, 2026, 2027];
const QUARTERS = ["Q1", "Q2", "Q3", "Q4"];
const NETWORKS = ["POS", "PPO", "HealthyNY"];

const CARRIER_COLORS: Record<string, string> = {
  IHA: "bg-blue-100 text-blue-800 border-blue-200",
  Highmark: "bg-purple-100 text-purple-800 border-purple-200",
  Univera: "bg-emerald-100 text-emerald-800 border-emerald-200",
  Excellus: "bg-orange-100 text-orange-800 border-orange-200",
};

interface PlansTableTabProps {
  plans: Plan[];
  loading: boolean;
  filters: BrowseFilters;
  onFiltersChange: (filters: BrowseFilters) => void;
  onEdit: (plan: Plan) => void;
  onDownloadMasterTemplate: () => void;
  isDownloading: boolean;
}

function formatRate(value: number | null): string {
  if (value == null) return "-";
  return `$${value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export function PlansTableTab({
  plans,
  loading,
  filters,
  onFiltersChange,
  onEdit,
  onDownloadMasterTemplate,
  isDownloading,
}: PlansTableTabProps) {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");

  // Reset to page 1 whenever the plan list or search changes
  useEffect(() => { setPage(1); }, [plans, search]);

  const filtered = useMemo(() => {
    if (!search.trim()) return plans;
    const q = search.toLowerCase();
    return plans.filter((p) => p.plan_name.toLowerCase().includes(q));
  }, [plans, search]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const grouped = useMemo(() => {
    const map = new Map<string, Plan[]>();
    for (const plan of paginated) {
      const existing = map.get(plan.carrier) || [];
      existing.push(plan);
      map.set(plan.carrier, existing);
    }
    return Array.from(map.entries()).sort(([a], [b]) => a.localeCompare(b));
  }, [paginated]);

  const hasFilters =
    filters.carrier || filters.year || filters.quarter || filters.network_type || search;

  const columnCount = 11; // Plan Name + 4 rates + PCP + Deductible + OOP Max + Quarter + Year + Actions

  return (
    <div className="space-y-4">
      {/* Inline filter bar */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground pointer-events-none" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search plans..."
            className="pl-8 w-[200px] h-9"
          />
        </div>

        <Select
          value={filters.carrier || ""}
          onValueChange={(v) =>
            onFiltersChange({ ...filters, carrier: v || undefined })
          }
        >
          <SelectTrigger className="w-[150px]">
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
          <SelectTrigger className="w-[110px]">
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
          <SelectTrigger className="w-[110px]">
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
          <SelectTrigger className="w-[130px]">
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
            onClick={() => { onFiltersChange({}); setSearch(""); }}
          >
            <X className="h-4 w-4 mr-1" />
            Clear
          </Button>
        )}

        <div className="ml-auto">
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
            <Download className="h-4 w-4 mr-2" />
            {isDownloading ? "Downloading..." : "Master Template"}
          </Button>
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full rounded" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          {plans.length === 0
            ? "No plans found. Try adjusting your filters or upload some PDFs."
            : `No plans match "${search}".`}
        </div>
      ) : (
        <div className="border rounded-lg overflow-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="min-w-[200px]">Plan Name</TableHead>
                <TableHead className="text-right">EE Only</TableHead>
                <TableHead className="text-right">EE+Spouse</TableHead>
                <TableHead className="text-right">EE+Child</TableHead>
                <TableHead className="text-right">Family</TableHead>
                <TableHead>PCP Copay</TableHead>
                <TableHead>Deductible</TableHead>
                <TableHead>OOP Max</TableHead>
                <TableHead>Quarter</TableHead>
                <TableHead>Year</TableHead>
                <TableHead className="w-[60px]" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {grouped.map(([carrier, carrierPlans]) => (
                <Fragment key={carrier}>
                  {/* Carrier group header */}
                  <TableRow className="hover:bg-transparent">
                    <TableCell colSpan={columnCount} className="py-2 px-3">
                      <Badge
                        className={`text-xs font-semibold ${CARRIER_COLORS[carrier] || "bg-gray-100 text-gray-800"}`}
                      >
                        {carrier}
                      </Badge>
                      <span className="text-xs text-muted-foreground ml-2">
                        {carrierPlans.length} plan
                        {carrierPlans.length !== 1 ? "s" : ""}
                      </span>
                    </TableCell>
                  </TableRow>
                  {/* Plans */}
                  {carrierPlans.map((plan) => (
                    <TableRow key={plan.plan_id}>
                      <TableCell className="font-medium text-sm">
                        {plan.plan_name}
                      </TableCell>
                      <TableCell className="text-right text-sm">
                        {formatRate(plan.ee_only)}
                      </TableCell>
                      <TableCell className="text-right text-sm">
                        {formatRate(plan.ee_spouse)}
                      </TableCell>
                      <TableCell className="text-right text-sm">
                        {formatRate(plan.ee_children)}
                      </TableCell>
                      <TableCell className="text-right text-sm">
                        {formatRate(plan.family)}
                      </TableCell>
                      <TableCell className="text-sm">
                        {plan.medical_details?.pcp_copay || "-"}
                      </TableCell>
                      <TableCell className="text-sm">
                        {plan.medical_details?.deductible_in_ee || "-"}
                      </TableCell>
                      <TableCell className="text-sm">
                        {plan.medical_details?.oop_max_in_ee || "-"}
                      </TableCell>
                      <TableCell className="text-sm">{plan.quarter}</TableCell>
                      <TableCell className="text-sm">{plan.year}</TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() => onEdit(plan)}
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </Fragment>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      {!loading && filtered.length > 0 && (
        <div className="flex items-center justify-between pt-1">
          <p className="text-xs text-muted-foreground">
            Showing {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, filtered.length)} of {filtered.length} plan{filtered.length !== 1 ? "s" : ""}
          </p>
          {totalPages > 1 && (
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                className="h-7 px-2"
                onClick={() => setPage((p) => p - 1)}
                disabled={page === 1}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="text-xs text-muted-foreground">
                Page {page} of {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                className="h-7 px-2"
                onClick={() => setPage((p) => p + 1)}
                disabled={page === totalPages}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
