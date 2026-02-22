"use client";

import { useCallback, useEffect, useMemo, useRef, useState, DragEvent } from "react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
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
import { SelectedPlansPanel } from "@/components/plans/selected-plans-panel";
import { plansApi } from "@/lib/api";
import { ChevronLeft, ChevronRight, GripVertical, LayoutGrid, List, Plus, X } from "lucide-react";
import type { Plan } from "@/types/plans";

const CARRIERS = ["IHA", "Highmark", "Univera", "Excellus"];
const YEARS = [2024, 2025, 2026, 2027];
const QUARTERS = ["Q1", "Q2", "Q3", "Q4"];
const PAGE_SIZE = 20;

const CARRIER_COLORS: Record<string, string> = {
  IHA: "bg-red-600 text-white",
  "Independent Health": "bg-red-600 text-white",
  Highmark: "bg-blue-500 text-white",
  Univera: "bg-lime-500 text-black",
  Excellus: "bg-blue-600 text-white",
};

function getCarrierClass(carrier: string): string {
  for (const [key, cls] of Object.entries(CARRIER_COLORS)) {
    if (carrier.toUpperCase().includes(key.toUpperCase())) return cls;
  }
  return "bg-gray-500 text-white";
}

function formatCurrency(val: number | null): string {
  if (val == null) return "N/A";
  return `$${val.toFixed(2)}`;
}

export function ComparisonTab() {
  // ── All plans fetched independently ───────────────────────────────
  const [allPlans, setAllPlans] = useState<Plan[]>([]);
  const [loadingPlans, setLoadingPlans] = useState(false);

  // ── Period selectors ──────────────────────────────────────────────
  const [currentYear, setCurrentYear]       = useState<number | undefined>();
  const [currentQuarter, setCurrentQuarter] = useState<string | undefined>();
  const [renewalYear, setRenewalYear]       = useState<number | undefined>();
  const [renewalQuarter, setRenewalQuarter] = useState<string | undefined>();

  // ── Browse filter (carrier only — period is handled by selectors) ─
  const [carrierFilters, setCarrierFilters] = useState<Set<string>>(new Set());
  const [viewMode, setViewMode] = useState<"list" | "grid">("list");

  // ── Pagination ────────────────────────────────────────────────────
  const [page, setPage] = useState(1);

  // ── Selections ────────────────────────────────────────────────────
  const [selectedCurrentIds, setSelectedCurrentIds] = useState<Set<string>>(new Set());
  const [selectedRenewalIds, setSelectedRenewalIds] = useState<Set<string>>(new Set());
  const [selectedOptionIds,  setSelectedOptionIds]  = useState<Set<string>>(new Set());

  // Track current → renewal pairing so we can remove both together
  const [currentToRenewal, setCurrentToRenewal] = useState<Map<string, string>>(new Map());

  const [isGenerating, setIsGenerating] = useState(false);
  const [dropTarget, setDropTarget] = useState<"current" | "option" | null>(null);

  // Refs so the re-pair effect can read latest state without circular deps
  const latestCurrentIds     = useRef(selectedCurrentIds);
  const latestCurrentToRenewal = useRef(currentToRenewal);
  useEffect(() => { latestCurrentIds.current = selectedCurrentIds; }, [selectedCurrentIds]);
  useEffect(() => { latestCurrentToRenewal.current = currentToRenewal; }, [currentToRenewal]);

  // ── Fetch all plans once ──────────────────────────────────────────
  const fetchPlans = useCallback(async () => {
    setLoadingPlans(true);
    try {
      const { data } = await plansApi.browse({});
      setAllPlans(data);
    } catch {
      toast.error("Failed to load plans");
    } finally {
      setLoadingPlans(false);
    }
  }, []);

  useEffect(() => { fetchPlans(); }, [fetchPlans]);

  // ── Plans visible in the table (current period + optional carriers) ─
  const tablePlans = useMemo(() => {
    return allPlans.filter((p) => {
      if (currentYear    && p.year    !== currentYear)    return false;
      if (currentQuarter && p.quarter !== currentQuarter) return false;
      if (carrierFilters.size > 0 && !Array.from(carrierFilters).some((cf) =>
        p.carrier.toUpperCase().includes(cf.toUpperCase())
      )) return false;
      return true;
    });
  }, [allPlans, currentYear, currentQuarter, carrierFilters]);

  // Reset page when filters change
  useEffect(() => { setPage(1); }, [currentYear, currentQuarter, carrierFilters]);

  const totalPages = Math.max(1, Math.ceil(tablePlans.length / PAGE_SIZE));
  const paginatedPlans = useMemo(
    () => tablePlans.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE),
    [tablePlans, page]
  );

  // ── Auto-find the renewal counterpart for a given plan ────────────
  const findRenewal = useCallback(
    (plan: Plan): Plan | undefined => {
      if (!renewalYear && !renewalQuarter) return undefined;

      const norm = (s: string) => s.trim().toLowerCase();
      const planName    = norm(plan.plan_name);
      const planCarrier = norm(plan.carrier);

      console.log("[findRenewal] searching for:", {
        carrier: planCarrier,
        plan_name: planName,
        renewalYear,
        renewalQuarter,
        totalPlans: allPlans.length,
      });

      const match = allPlans.find(
        (p) =>
          norm(p.carrier)   === planCarrier &&
          norm(p.plan_name) === planName &&
          (!renewalYear    || p.year    === renewalYear) &&
          (!renewalQuarter || p.quarter === renewalQuarter)
      );

      console.log("[findRenewal] result:", match
        ? `${match.plan_name} (${match.quarter} ${match.year})`
        : "NOT FOUND — available plans for this name:",
        !match
          ? allPlans
              .filter((p) => norm(p.plan_name) === planName)
              .map((p) => `${p.carrier} / ${p.quarter} ${p.year}`)
          : ""
      );

      return match;
    },
    [allPlans, renewalYear, renewalQuarter]
  );

  // ── Re-pair when renewal period changes or allPlans reloads ──────
  // Handles the case where user sets the renewal period AFTER selecting
  // current plans (the most common workflow).
  useEffect(() => {
    if (!renewalYear && !renewalQuarter) return;

    const currentIds = latestCurrentIds.current;
    const pairings   = latestCurrentToRenewal.current;

    // Only re-pair current plans that don't have a renewal yet
    const unpaired = Array.from(currentIds).filter((id) => !pairings.has(id));
    if (unpaired.length === 0) return;

    const newPairings = new Map(pairings);
    const toAdd: string[] = [];

    for (const planId of unpaired) {
      const plan = allPlans.find((p) => p.plan_id === planId);
      if (!plan) continue;
      const renewal = findRenewal(plan);
      if (renewal) {
        toAdd.push(renewal.plan_id);
        newPairings.set(planId, renewal.plan_id);
      }
    }

    if (toAdd.length > 0) {
      setSelectedRenewalIds((prev) => {
        const n = new Set(prev);
        toAdd.forEach((id) => n.add(id));
        return n;
      });
      setCurrentToRenewal(newPairings);
      toast.success(
        `Auto-paired ${toAdd.length} renewal plan${toAdd.length > 1 ? "s" : ""}`
      );
    } else if (unpaired.length > 0) {
      toast.warning(
        `No renewal match found for ${unpaired.length} plan${unpaired.length > 1 ? "s" : ""} in ${renewalQuarter ?? ""} ${renewalYear ?? ""}. Check console for details.`.trim()
      );
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [renewalYear, renewalQuarter, findRenewal, allPlans]);

  // ── Add as Current + auto-pair Renewal ───────────────────────────
  const handleAddAsCurrent = useCallback(
    (plan: Plan) => {
      // Toggle off
      if (selectedCurrentIds.has(plan.plan_id)) {
        handleRemoveCurrent(plan.plan_id);
        return;
      }

      // Remove from option bucket if it was there
      setSelectedOptionIds((p) => { const n = new Set(p); n.delete(plan.plan_id); return n; });
      setSelectedCurrentIds((p) => new Set(p).add(plan.plan_id));

      if (!renewalYear && !renewalQuarter) {
        // No renewal period set — try to auto-detect one from available plans.
        // Find other versions of this same plan (same carrier + name, different period).
        const norm = (s: string) => s.trim().toLowerCase();
        const candidates = allPlans.filter(
          (p) =>
            norm(p.carrier)   === norm(plan.carrier) &&
            norm(p.plan_name) === norm(plan.plan_name) &&
            p.plan_id !== plan.plan_id
        );

        if (candidates.length > 0) {
          // Pick the most recent period (highest year, then latest quarter)
          candidates.sort((a, b) =>
            a.year !== b.year ? b.year - a.year : b.quarter.localeCompare(a.quarter)
          );
          const best = candidates[0];
          // Setting these triggers the re-pair useEffect which will do the pairing
          setRenewalYear(best.year);
          setRenewalQuarter(best.quarter);
          toast.success(
            `Auto-detected Renewal Period: ${best.quarter} ${best.year} — pairing renewal plans…`
          );
        } else {
          toast.warning(
            `No other period found for "${plan.plan_name}". Set the Renewal Period manually.`
          );
        }
        return;
      }

      const renewal = findRenewal(plan);
      if (renewal) {
        setSelectedRenewalIds((p) => new Set(p).add(renewal.plan_id));
        setCurrentToRenewal((m) => new Map(m).set(plan.plan_id, renewal.plan_id));
        toast.success(
          `Auto-paired: ${renewal.plan_name} (${renewal.quarter} ${renewal.year})`
        );
      } else {
        toast.warning(
          `No renewal match found for "${plan.plan_name}" in ${renewalQuarter ?? ""} ${renewalYear ?? ""}. Check browser console for details.`.trim()
        );
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [selectedCurrentIds, renewalYear, renewalQuarter, findRenewal, allPlans]
  );

  // ── Add as Option ─────────────────────────────────────────────────
  const handleAddAsOption = (plan: Plan) => {
    if (selectedOptionIds.has(plan.plan_id)) {
      setSelectedOptionIds((p) => { const n = new Set(p); n.delete(plan.plan_id); return n; });
      return;
    }
    // Remove from current/renewal if it was there
    setSelectedCurrentIds((p) => { const n = new Set(p); n.delete(plan.plan_id); return n; });
    setSelectedRenewalIds((p) => { const n = new Set(p); n.delete(plan.plan_id); return n; });
    setSelectedOptionIds((p)  => new Set(p).add(plan.plan_id));
  };

  // ── Remove handlers ───────────────────────────────────────────────
  const handleRemoveCurrent = (planId: string) => {
    setSelectedCurrentIds((p) => { const n = new Set(p); n.delete(planId); return n; });
    // Remove paired renewal
    const renewalId = currentToRenewal.get(planId);
    if (renewalId) {
      setSelectedRenewalIds((p) => { const n = new Set(p); n.delete(renewalId); return n; });
      setCurrentToRenewal((m) => { const n = new Map(m); n.delete(planId); return n; });
    }
  };
  const handleRemoveRenewal = (planId: string) => {
    setSelectedRenewalIds((p) => { const n = new Set(p); n.delete(planId); return n; });
    // Break pairing
    setCurrentToRenewal((m) => {
      const n = new Map(m);
      for (const [k, v] of n.entries()) { if (v === planId) { n.delete(k); break; } }
      return n;
    });
  };
  const handleRemoveOption = (planId: string) =>
    setSelectedOptionIds((p) => { const n = new Set(p); n.delete(planId); return n; });

  // ── Generate ──────────────────────────────────────────────────────
  const handleGenerateComparison = async () => {
    const currentIds = Array.from(selectedCurrentIds);
    const renewalIds = Array.from(selectedRenewalIds);
    const optionIds  = Array.from(selectedOptionIds);
    if (!currentIds.length && !renewalIds.length && !optionIds.length) {
      toast.error("Select at least one plan");
      return;
    }
    setIsGenerating(true);
    try {
      const { data } = await plansApi.generateComparison({
        current_plan_ids: currentIds,
        renewal_plan_ids: renewalIds,
        option_plan_ids:  optionIds,
      });
      const url = window.URL.createObjectURL(new Blob([data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = "Marketing-Renewal-Comparison.xlsx";
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success("Comparison Excel downloaded");
    } catch {
      toast.error("Failed to generate comparison");
    } finally {
      setIsGenerating(false);
    }
  };

  // ── Selection state for row highlighting ──────────────────────────
  const getState = (planId: string) => {
    if (selectedCurrentIds.has(planId)) return "current";
    if (selectedRenewalIds.has(planId)) return "renewal";
    if (selectedOptionIds.has(planId))  return "option";
    return null;
  };

  // ── Drag & drop ───────────────────────────────────────────────────
  const handleDragStart = (e: DragEvent, planId: string) => {
    e.dataTransfer.setData("text/plain", planId);
    e.dataTransfer.effectAllowed = "copy";
  };
  const handleDragOver = (e: DragEvent, target: "current" | "option") => {
    e.preventDefault();
    setDropTarget(target);
  };
  const handleDragLeave = () => setDropTarget(null);
  const handleDrop = (e: DragEvent, target: "current" | "option") => {
    e.preventDefault();
    setDropTarget(null);
    const planId = e.dataTransfer.getData("text/plain");
    const plan = allPlans.find((p) => p.plan_id === planId);
    if (!plan) return;
    if (target === "current") handleAddAsCurrent(plan);
    else handleAddAsOption(plan);
  };

  const periodLabel = currentYear || currentQuarter
    ? `${currentQuarter ?? ""} ${currentYear ?? ""}`.trim()
    : "all periods";

  return (
    <div className="space-y-4">

      {/* ── Period selectors ───────────────────────────────────────── */}
      <div className="grid grid-cols-2 gap-4">
        {/* Current Period */}
        <div className="border rounded-lg p-3 space-y-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Current Period (enrolled)
          </p>
          <div className="flex gap-2">
            <Select
              value={currentYear?.toString() ?? ""}
              onValueChange={(v) => setCurrentYear(v ? Number(v) : undefined)}
            >
              <SelectTrigger className="flex-1">
                <SelectValue placeholder="Year" />
              </SelectTrigger>
              <SelectContent>
                {YEARS.map((y) => (
                  <SelectItem key={y} value={y.toString()}>{y}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select
              value={currentQuarter ?? ""}
              onValueChange={(v) => setCurrentQuarter(v || undefined)}
            >
              <SelectTrigger className="flex-1">
                <SelectValue placeholder="Quarter" />
              </SelectTrigger>
              <SelectContent>
                {QUARTERS.map((q) => (
                  <SelectItem key={q} value={q}>{q}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            {(currentYear || currentQuarter) && (
              <Button variant="ghost" size="icon" onClick={() => { setCurrentYear(undefined); setCurrentQuarter(undefined); }}>
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>

        {/* Renewal Period */}
        <div className="border rounded-lg p-3 space-y-2 bg-yellow-50/50">
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Renewal Period (auto-paired)
          </p>
          <div className="flex gap-2">
            <Select
              value={renewalYear?.toString() ?? ""}
              onValueChange={(v) => setRenewalYear(v ? Number(v) : undefined)}
            >
              <SelectTrigger className="flex-1">
                <SelectValue placeholder="Year" />
              </SelectTrigger>
              <SelectContent>
                {YEARS.map((y) => (
                  <SelectItem key={y} value={y.toString()}>{y}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select
              value={renewalQuarter ?? ""}
              onValueChange={(v) => setRenewalQuarter(v || undefined)}
            >
              <SelectTrigger className="flex-1">
                <SelectValue placeholder="Quarter" />
              </SelectTrigger>
              <SelectContent>
                {QUARTERS.map((q) => (
                  <SelectItem key={q} value={q}>{q}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            {(renewalYear || renewalQuarter) && (
              <Button variant="ghost" size="icon" onClick={() => { setRenewalYear(undefined); setRenewalQuarter(undefined); }}>
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* ── Browse filters ─────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-muted-foreground font-medium">Carriers:</span>
          {CARRIERS.map((c) => {
            const active = carrierFilters.has(c);
            return (
              <button
                key={c}
                onClick={() => {
                  setCarrierFilters((prev) => {
                    const next = new Set(prev);
                    if (next.has(c)) next.delete(c);
                    else next.add(c);
                    return next;
                  });
                }}
                className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                  active
                    ? "bg-primary text-primary-foreground border-primary"
                    : "bg-white text-gray-600 border-gray-300 hover:border-gray-500"
                }`}
              >
                {c}
              </button>
            );
          })}
          {carrierFilters.size > 0 && (
            <button
              onClick={() => setCarrierFilters(new Set())}
              className="text-xs text-muted-foreground underline hover:text-gray-900"
            >
              Clear
            </button>
          )}
        </div>

        <div className="ml-auto flex border rounded-md">
          <Button
            variant={viewMode === "list" ? "default" : "ghost"}
            size="icon" className="h-8 w-8 rounded-r-none"
            onClick={() => setViewMode("list")}
          >
            <List className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === "grid" ? "default" : "ghost"}
            size="icon" className="h-8 w-8 rounded-l-none"
            onClick={() => setViewMode("grid")}
          >
            <LayoutGrid className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <p className="text-xs text-muted-foreground">
        Showing plans for <strong>{periodLabel}</strong>. Click <strong>Select</strong> to add a plan as Current and auto-pair its Renewal. Click <strong>Option</strong> for alternative plans (toggle carriers above to browse).
      </p>

      <div className="flex gap-6">
        {/* ── Plan picker ──────────────────────────────────────────── */}
        <div className="flex-1 min-w-0">
          {loadingPlans ? (
            <div className="text-center py-12 text-muted-foreground">Loading plans…</div>
          ) : tablePlans.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              No plans found. Select a period or upload PDFs first.
            </div>
          ) : viewMode === "list" ? (
            <div className="border rounded-lg overflow-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[30px]" />
                    <TableHead>Carrier</TableHead>
                    <TableHead className="min-w-[180px]">Plan Name</TableHead>
                    <TableHead>Quarter</TableHead>
                    <TableHead>Year</TableHead>
                    <TableHead className="text-right">EE Only</TableHead>
                    <TableHead className="w-[180px]" />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {paginatedPlans.map((plan) => {
                    const state = getState(plan.plan_id);
                    return (
                      <TableRow
                        key={plan.plan_id}
                        draggable
                        onDragStart={(e) => handleDragStart(e, plan.plan_id)}
                        className={`${state !== "renewal" ? "cursor-grab active:cursor-grabbing" : "cursor-default"} ${
                          state === "current" ? "bg-blue-50" :
                          state === "renewal" ? "bg-amber-50 opacity-60" :
                          state === "option"  ? "bg-green-50" : ""
                        }`}
                      >
                        <TableCell className="px-2">
                          <GripVertical className="h-4 w-4 text-muted-foreground" />
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className="text-xs">{plan.carrier}</Badge>
                        </TableCell>
                        <TableCell className="font-medium text-sm">{plan.plan_name}</TableCell>
                        <TableCell className="text-sm">{plan.quarter}</TableCell>
                        <TableCell className="text-sm">{plan.year}</TableCell>
                        <TableCell className="text-right text-sm">
                          {plan.ee_only != null
                            ? `$${plan.ee_only.toLocaleString("en-US", { minimumFractionDigits: 2 })}`
                            : "-"}
                        </TableCell>
                        <TableCell>
                          {state === "renewal" ? (
                            <span className="inline-flex items-center gap-1 text-xs text-amber-700 bg-amber-100 border border-amber-300 rounded px-2 py-1 font-medium select-none">
                              🔒 Auto-paired Renewal
                            </span>
                          ) : (
                            <div className="flex gap-1.5">
                              <Button
                                size="sm"
                                variant={state === "current" ? "default" : "outline"}
                                className="h-7 text-xs"
                                onClick={() => handleAddAsCurrent(plan)}
                              >
                                {state === "current" ? "Current ✓" : "Select"}
                              </Button>
                              <Button
                                size="sm"
                                variant={state === "option" ? "default" : "outline"}
                                className="h-7 text-xs"
                                onClick={() => handleAddAsOption(plan)}
                              >
                                {state === "option" ? "Option ✓" : "Option"}
                              </Button>
                            </div>
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {paginatedPlans.map((plan) => {
                const state = getState(plan.plan_id);
                return (
                  <Card
                    key={plan.plan_id}
                    draggable={state !== "renewal"}
                    onDragStart={(e) => state !== "renewal" && handleDragStart(e, plan.plan_id)}
                    className={`transition-all hover:shadow-md ${
                      state === "renewal" ? "opacity-60 cursor-default" : "cursor-grab active:cursor-grabbing"
                    } ${
                      state === "current" ? "ring-2 ring-blue-500" :
                      state === "option"  ? "ring-2 ring-green-500" :
                      state === "renewal" ? "ring-2 ring-amber-400" : ""
                    }`}
                  >
                    <CardHeader className="pb-2">
                      <div className="flex items-start justify-between gap-2">
                        <div className="space-y-1 min-w-0">
                          <Badge className={getCarrierClass(plan.carrier)}>{plan.carrier}</Badge>
                          <h3 className="text-sm font-medium leading-tight truncate">{plan.plan_name}</h3>
                        </div>
                        <GripVertical className="h-4 w-4 text-muted-foreground shrink-0 mt-1" />
                      </div>
                      <div className="flex gap-2 text-xs text-muted-foreground">
                        <span>{plan.quarter} {plan.year}</span>
                        <span>{plan.plan_type}</span>
                      </div>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs mb-3">
                        {[
                          ["EE Only", plan.ee_only],
                          ["EE+Spouse", plan.ee_spouse],
                          ["EE+Child", plan.ee_children],
                          ["Family", plan.family],
                        ].map(([label, val]) => (
                          <div key={label as string} className="flex justify-between">
                            <span className="text-muted-foreground">{label}</span>
                            <span className="font-medium">{formatCurrency(val as number | null)}</span>
                          </div>
                        ))}
                      </div>
                      {state === "renewal" ? (
                        <div className="flex items-center justify-center gap-1 text-xs text-amber-700 bg-amber-100 border border-amber-300 rounded px-2 py-1.5 font-medium select-none">
                          🔒 Auto-paired Renewal
                        </div>
                      ) : (
                        <div className="flex gap-1">
                          <Button
                            variant={state === "current" ? "default" : "outline"}
                            size="sm" className="flex-1 h-7 text-xs"
                            onClick={() => handleAddAsCurrent(plan)}
                          >
                            <Plus className="h-3 w-3 mr-1" />
                            {state === "current" ? "Current ✓" : "Select"}
                          </Button>
                          <Button
                            variant={state === "option" ? "default" : "outline"}
                            size="sm" className="flex-1 h-7 text-xs"
                            onClick={() => handleAddAsOption(plan)}
                          >
                            <Plus className="h-3 w-3 mr-1" />
                            {state === "option" ? "Option ✓" : "Option"}
                          </Button>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}

          {tablePlans.length > 0 && (
            <div className="flex items-center justify-between mt-3">
              <p className="text-xs text-muted-foreground">
                Showing {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, tablePlans.length)} of {tablePlans.length} plan{tablePlans.length !== 1 ? "s" : ""}
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

        {/* ── Right panel ───────────────────────────────────────────── */}
        <div className="w-72 shrink-0 space-y-3">
          {/* Drop zones */}
          <div className="grid grid-cols-2 gap-2">
            <div
              onDragOver={(e) => handleDragOver(e, "current")}
              onDragLeave={handleDragLeave}
              onDrop={(e) => handleDrop(e, "current")}
              className={`border-2 border-dashed rounded-lg p-3 text-center text-xs transition-colors ${
                dropTarget === "current"
                  ? "border-blue-500 bg-blue-50 text-blue-700"
                  : "border-slate-300 text-muted-foreground"
              }`}
            >
              Drop to<br /><span className="font-semibold">Select</span>
            </div>
            <div
              onDragOver={(e) => handleDragOver(e, "option")}
              onDragLeave={handleDragLeave}
              onDrop={(e) => handleDrop(e, "option")}
              className={`border-2 border-dashed rounded-lg p-3 text-center text-xs transition-colors ${
                dropTarget === "option"
                  ? "border-green-500 bg-green-50 text-green-700"
                  : "border-slate-300 text-muted-foreground"
              }`}
            >
              Drop as<br /><span className="font-semibold">Option</span>
            </div>
          </div>

          <SelectedPlansPanel
            plans={allPlans}
            selectedCurrentIds={selectedCurrentIds}
            selectedRenewalIds={selectedRenewalIds}
            selectedOptionIds={selectedOptionIds}
            onRemoveCurrent={handleRemoveCurrent}
            onRemoveRenewal={handleRemoveRenewal}
            onRemoveOption={handleRemoveOption}
            onGenerateComparison={handleGenerateComparison}
            isGenerating={isGenerating}
          />
        </div>
      </div>
    </div>
  );
}