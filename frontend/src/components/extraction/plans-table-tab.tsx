"use client";

import { Fragment, useMemo } from "react";
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
import { Download, Pencil, X } from "lucide-react";
import type { BrowseFilters, Plan } from "@/types/plans";

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
  const grouped = useMemo(() => {
    const map = new Map<string, Plan[]>();
    for (const plan of plans) {
      const existing = map.get(plan.carrier) || [];
      existing.push(plan);
      map.set(plan.carrier, existing);
    }
    // Sort carriers alphabetically
    return Array.from(map.entries()).sort(([a], [b]) => a.localeCompare(b));
  }, [plans]);

  const hasFilters =
    filters.carrier || filters.year || filters.quarter || filters.network_type;

  const columnCount = 11; // Plan Name + 4 rates + PCP + Deductible + OOP Max + Quarter + Year + Actions

  return (
    <div className="space-y-4">
      {/* Inline filter bar */}
      <div className="flex flex-wrap items-center gap-3">
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
            onClick={() => onFiltersChange({})}
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
      ) : plans.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          No plans found. Try adjusting your filters or upload some PDFs.
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

      {!loading && plans.length > 0 && (
        <p className="text-xs text-muted-foreground">
          {plans.length} plan{plans.length !== 1 ? "s" : ""} found
        </p>
      )}
    </div>
  );
}
