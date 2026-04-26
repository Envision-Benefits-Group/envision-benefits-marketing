"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { plansApi } from "@/lib/api";
import type { Plan } from "@/types/plans";
import {
  CalendarDays,
  ChevronRight,
  CheckCircle2,
  Circle,
  Download,
  Loader2,
  Search,
  X,
  Check,
  Building2,
  FileSpreadsheet,
  Users,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const CARRIERS = ["IHA", "Highmark", "Univera", "Excellus"];

const CARRIER_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  IHA:      { bg: "#fee2e2", text: "#991b1b", border: "#fca5a5" },
  Highmark: { bg: "#dbeafe", text: "#1e40af", border: "#93c5fd" },
  Univera:  { bg: "#dcfce7", text: "#166534", border: "#86efac" },
  Excellus: { bg: "#ede9fe", text: "#5b21b6", border: "#c4b5fd" },
};

function getCarrierStyle(carrier: string) {
  for (const [key, style] of Object.entries(CARRIER_COLORS)) {
    if (carrier.toUpperCase().includes(key.toUpperCase())) return style;
  }
  return { bg: "#f1f5f9", text: "#334155", border: "#cbd5e1" };
}

function fmt(val: number | null) {
  if (val == null) return "—";
  return "$" + val.toLocaleString("en-US", { minimumFractionDigits: 2 });
}

function quarterFromDate(dateStr: string): { quarter: string; year: number } | null {
  if (!dateStr) return null;
  const d = new Date(dateStr + "T00:00:00");
  const q = "Q" + Math.ceil((d.getMonth() + 1) / 3);
  return { quarter: q, year: d.getFullYear() };
}

function StepIndicator({ steps, current }: { steps: string[]; current: number }) {
  return (
    <div className="flex items-center gap-0 mb-8">
      {steps.map((label, i) => {
        const done = i < current;
        const active = i === current;
        return (
          <div key={i} className="flex items-center">
            <div className="flex flex-col items-center">
              <div
                className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-all"
                style={{
                  background: done ? "#0d2240" : active ? "#c9a84c" : "#e2e8f0",
                  color: (done || active) ? "white" : "#94a3b8",
                }}
              >
                {done ? <Check className="w-4 h-4" /> : i + 1}
              </div>
              <span
                className="text-xs mt-1 font-medium whitespace-nowrap"
                style={{ color: active ? "#c9a84c" : done ? "#0d2240" : "#94a3b8" }}
              >
                {label}
              </span>
            </div>
            {i < steps.length - 1 && (
              <div
                className="h-0.5 w-16 mx-1 mb-4 transition-all"
                style={{ background: i < current ? "#0d2240" : "#e2e8f0" }}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

function PlanCard({ plan, selected, onToggle, role }: {
  plan: Plan; selected: boolean; onToggle: () => void; role: "enrolled" | "option";
}) {
  const style = getCarrierStyle(plan.carrier);
  const ded = plan.medical_details?.deductible_in_ee;
  return (
    <button
      onClick={onToggle}
      className="w-full text-left rounded-xl border-2 p-4 transition-all hover:shadow-md"
      style={{
        borderColor: selected ? (role === "enrolled" ? "#0d2240" : "#c9a84c") : "#e2e8f0",
        background: selected ? (role === "enrolled" ? "rgba(13,34,64,0.04)" : "rgba(201,168,76,0.06)") : "white",
      }}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full" style={{ background: style.bg, color: style.text, border: "1px solid " + style.border }}>
              {plan.carrier}
            </span>
            <span className="text-xs text-gray-400">{plan.quarter} {plan.year}</span>
          </div>
          <p className="text-sm font-semibold text-gray-800 leading-tight">{plan.plan_name}</p>
          {ded && (
            <p className="text-xs text-gray-500 mt-1 leading-tight">
              Deductible: {ded.length > 55 ? ded.substring(0, 55) + "…" : ded}
            </p>
          )}
        </div>
        <div
          className="w-5 h-5 rounded-full border-2 flex-shrink-0 flex items-center justify-center mt-0.5"
          style={{
            borderColor: selected ? (role === "enrolled" ? "#0d2240" : "#c9a84c") : "#cbd5e1",
            background: selected ? (role === "enrolled" ? "#0d2240" : "#c9a84c") : "white",
          }}
        >
          {selected && <Check className="w-3 h-3 text-white" />}
        </div>
      </div>
      <div className="mt-3 grid grid-cols-4 gap-1">
        {[["EE Only", plan.ee_only], ["+ Spouse", plan.ee_spouse], ["+ Child(ren)", plan.ee_children], ["Family", plan.family]].map(([label, val]) => (
          <div key={label as string} className="text-center">
            <p className="text-xs text-gray-400 leading-tight">{label}</p>
            <p className="text-xs font-semibold text-gray-700">{fmt(val as number | null)}</p>
          </div>
        ))}
      </div>
    </button>
  );
}

function PlanChip({ plan, role, onRemove }: { plan: Plan; role: "enrolled" | "option"; onRemove: () => void }) {
  return (
    <div
      className="flex items-center gap-2 px-3 py-2 rounded-lg border text-xs font-medium"
      style={{
        background: role === "enrolled" ? "rgba(13,34,64,0.06)" : "rgba(201,168,76,0.08)",
        borderColor: role === "enrolled" ? "rgba(13,34,64,0.2)" : "rgba(201,168,76,0.3)",
        color: role === "enrolled" ? "#0d2240" : "#92711e",
      }}
    >
      <span className="truncate max-w-[160px]">{plan.plan_name}</span>
      <span className="text-gray-400 shrink-0">{plan.quarter} {plan.year}</span>
      <button onClick={onRemove} className="ml-1 hover:opacity-70 shrink-0">
        <X className="w-3 h-3" />
      </button>
    </div>
  );
}

export function ComparisonTab() {
  const [step, setStep] = useState(0);
  const [allPlans, setAllPlans] = useState<Plan[]>([]);
  const [loadingPlans, setLoadingPlans] = useState(false);
  const [renewalDate, setRenewalDate] = useState("");
  const [selectedCarriers, setSelectedCarriers] = useState<Set<string>>(new Set());
  const [enrolledIds, setEnrolledIds] = useState<Set<string>>(new Set());
  const [optionIds, setOptionIds] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);

  const renewalPeriod = useMemo(() => quarterFromDate(renewalDate), [renewalDate]);
  const currentPeriod = useMemo(() => {
    if (!renewalPeriod) return null;
    return { quarter: renewalPeriod.quarter, year: renewalPeriod.year - 1 };
  }, [renewalPeriod]);

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

  const enrolledCandidates = useMemo(() => {
    return allPlans.filter((p) => {
      if (selectedCarriers.size > 0 && !Array.from(selectedCarriers).some(c => p.carrier.toUpperCase().includes(c.toUpperCase()))) return false;
      // Filter by quarter only — not year — so future renewal dates still show available plans
      if (currentPeriod && p.quarter !== currentPeriod.quarter) return false;
      if (search && !p.plan_name.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    });
  }, [allPlans, selectedCarriers, currentPeriod, search]);

  const optionCandidates = useMemo(() => {
    return allPlans.filter((p) => {
      // Options show ALL carriers — not filtered by selected renewal carriers
      // Filter by quarter only so future renewal dates work
      if (renewalPeriod && p.quarter !== renewalPeriod.quarter) return false;
      if (search && !p.plan_name.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    });
  }, [allPlans, renewalPeriod, search]);

  const enrolledPlans = useMemo(() => allPlans.filter(p => enrolledIds.has(p.plan_id)), [allPlans, enrolledIds]);
  const optionPlans = useMemo(() => allPlans.filter(p => optionIds.has(p.plan_id)), [allPlans, optionIds]);

  const renewalIds = useMemo(() => {
    if (!renewalPeriod) return new Set<string>();
    const ids = new Set<string>();
    for (const enrolled of enrolledPlans) {
      const match = allPlans.find(p =>
        p.carrier.toLowerCase() === enrolled.carrier.toLowerCase() &&
        p.plan_name.toLowerCase() === enrolled.plan_name.toLowerCase() &&
        p.year === renewalPeriod.year &&
        p.quarter === renewalPeriod.quarter
      );
      if (match) ids.add(match.plan_id);
    }
    return ids;
  }, [enrolledPlans, allPlans, renewalPeriod]);

  const toggleCarrier = (c: string) => {
    setSelectedCarriers(prev => {
      const n = new Set(prev);
      if (n.has(c)) n.delete(c); else n.add(c);
      return n;
    });
  };

  const toggleEnrolled = (plan: Plan) => {
    setEnrolledIds(prev => {
      const n = new Set(prev);
      if (n.has(plan.plan_id)) n.delete(plan.plan_id); else n.add(plan.plan_id);
      return n;
    });
  };

  const toggleOption = (plan: Plan) => {
    setOptionIds(prev => {
      const n = new Set(prev);
      if (n.has(plan.plan_id)) n.delete(plan.plan_id); else n.add(plan.plan_id);
      return n;
    });
  };

  const handleGenerate = async () => {
    if (enrolledIds.size === 0 && optionIds.size === 0) {
      toast.error("Select at least one plan");
      return;
    }
    setIsGenerating(true);
    try {
      const { data } = await plansApi.generateComparison({
        current_plan_ids: enrolledPlans.map(p => p.plan_id),
        renewal_plan_ids: Array.from(renewalIds),
        option_plan_ids: Array.from(optionIds),
      });
      const url = window.URL.createObjectURL(new Blob([data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = "Marketing-Renewal-Comparison" + (renewalDate ? "-" + renewalDate : "") + ".xlsx";
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success("Comparison grid downloaded!");
    } catch {
      toast.error("Failed to generate comparison");
    } finally {
      setIsGenerating(false);
    }
  };

  const canProceedStep1 = renewalDate && selectedCarriers.size > 0;
  const canProceedStep2 = enrolledIds.size > 0;
  const STEPS = ["Renewal Setup", "Enrolled Plans", "Options", "Generate"];

  return (
    <div className="max-w-4xl mx-auto">
      <StepIndicator steps={STEPS} current={step} />

      {step === 0 && (
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: "#0d2240" }}>
              <CalendarDays className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold" style={{ color: "#0d2240" }}>Renewal Setup</h2>
              <p className="text-sm text-gray-500">Enter the renewal effective date and select which carriers are renewing</p>
            </div>
          </div>
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Renewal Effective Date <span className="text-red-500">*</span>
              </label>
              <Input type="date" value={renewalDate} onChange={(e) => setRenewalDate(e.target.value)} className="w-56" />
              {renewalPeriod && (
                <div className="mt-2 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-500" />
                  <span className="text-sm text-gray-600">
                    Compares <strong>{currentPeriod?.quarter} {currentPeriod?.year}</strong> (current) vs <strong>{renewalPeriod.quarter} {renewalPeriod.year}</strong> (renewal)
                  </span>
                </div>
              )}
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Which carriers are renewing? <span className="text-red-500">*</span>
              </label>
              <p className="text-xs text-gray-500 mb-3">Select all carriers included in this renewal. You can select multiple.</p>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {CARRIERS.map((c) => {
                  const active = selectedCarriers.has(c);
                  const style = getCarrierStyle(c);
                  return (
                    <button
                      key={c}
                      onClick={() => toggleCarrier(c)}
                      className="flex items-center gap-3 p-4 rounded-xl border-2 transition-all text-left"
                      style={{ borderColor: active ? "#0d2240" : "#e2e8f0", background: active ? "rgba(13,34,64,0.05)" : "white" }}
                    >
                      <div className="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold shrink-0" style={{ background: style.bg, color: style.text }}>
                        {c[0]}
                      </div>
                      <p className="text-sm font-semibold text-gray-800">{c}</p>
                      {active && <Check className="w-4 h-4 ml-auto shrink-0" style={{ color: "#0d2240" }} />}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
          <div className="mt-8 flex justify-end">
            <Button onClick={() => setStep(1)} disabled={!canProceedStep1} className="gap-2 px-6" style={{ background: canProceedStep1 ? "#0d2240" : undefined }}>
              Continue to Enrolled Plans <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}

      {step === 1 && (
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: "#0d2240" }}>
              <Users className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold" style={{ color: "#0d2240" }}>Select Enrolled Plans</h2>
              <p className="text-sm text-gray-500">
                Plans the client is <strong>currently enrolled in</strong>. Showing all {currentPeriod?.quarter} plans — select the ones renewing.
              </p>
            </div>
          </div>
          {enrolledPlans.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-4 p-3 rounded-lg bg-gray-50 border border-gray-200">
              <span className="text-xs font-medium text-gray-500 self-center">Selected:</span>
              {enrolledPlans.map(p => <PlanChip key={p.plan_id} plan={p} role="enrolled" onRemove={() => toggleEnrolled(p)} />)}
            </div>
          )}
          <div className="relative mb-4">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search by plan name..." className="pl-9" />
          </div>
          {loadingPlans ? (
            <div className="flex items-center justify-center py-16 text-gray-400"><Loader2 className="w-5 h-5 animate-spin mr-2" />Loading plans...</div>
          ) : enrolledCandidates.length === 0 ? (
            <div className="text-center py-16 text-gray-400">
              <Circle className="w-10 h-10 mx-auto mb-3 opacity-30" />
              <p className="font-medium">No plans found for {currentPeriod?.quarter}</p>
              <p className="text-sm mt-1">Upload rate PDFs in the Data Input tab first, then come back here.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-[460px] overflow-y-auto pr-1">
              {enrolledCandidates.map(plan => (
                <PlanCard key={plan.plan_id} plan={plan} selected={enrolledIds.has(plan.plan_id)} onToggle={() => toggleEnrolled(plan)} role="enrolled" />
              ))}
            </div>
          )}
          {enrolledPlans.length > 0 && renewalPeriod && (
            <div className="mt-4 p-3 rounded-lg border" style={{ background: renewalIds.size === enrolledIds.size ? "#f0fdf4" : "#fffbeb", borderColor: renewalIds.size === enrolledIds.size ? "#86efac" : "#fcd34d" }}>
              <div className="flex items-center gap-2">
                {renewalIds.size === enrolledIds.size ? <CheckCircle2 className="w-4 h-4 text-green-600" /> : <Circle className="w-4 h-4 text-amber-500" />}
                <span className="text-sm font-medium" style={{ color: renewalIds.size === enrolledIds.size ? "#166534" : "#92400e" }}>
                  {renewalIds.size} of {enrolledIds.size} plans auto-matched to {renewalPeriod.quarter} {renewalPeriod.year} renewal rates
                </span>
              </div>
              {renewalIds.size < enrolledIds.size && (
                <p className="text-xs text-amber-700 mt-1 ml-6">{enrolledIds.size - renewalIds.size} plan(s) not found in renewal period — upload renewal rate PDFs in Data Input.</p>
              )}
            </div>
          )}
          <div className="mt-6 flex justify-between">
            <Button variant="outline" onClick={() => setStep(0)}>Back</Button>
            <Button onClick={() => { setSearch(""); setStep(2); }} disabled={!canProceedStep2} className="gap-2 px-6" style={{ background: canProceedStep2 ? "#0d2240" : undefined }}>
              Continue to Options <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: "#c9a84c" }}>
              <Building2 className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold" style={{ color: "#0d2240" }}>Select Option Plans</h2>
              <p className="text-sm text-gray-500">
                <strong>Alternative plans</strong> to show as options for {renewalPeriod?.quarter} {renewalPeriod?.year}. These appear in the Opts columns of the grid.
              </p>
            </div>
          </div>
          {optionPlans.length > 0 ? (
            <div className="flex flex-wrap gap-2 mb-4 p-3 rounded-lg bg-gray-50 border border-gray-200">
              <span className="text-xs font-medium text-gray-500 self-center">Selected:</span>
              {optionPlans.map(p => <PlanChip key={p.plan_id} plan={p} role="option" onRemove={() => toggleOption(p)} />)}
            </div>
          ) : (
            <div className="mb-4 p-3 rounded-lg bg-amber-50 border border-amber-200">
              <p className="text-xs text-amber-700"><strong>Optional:</strong> Skip this step if you don't want alternative plan options in the grid.</p>
            </div>
          )}
          <div className="relative mb-4">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search by plan name..." className="pl-9" />
          </div>
          {loadingPlans ? (
            <div className="flex items-center justify-center py-16 text-gray-400"><Loader2 className="w-5 h-5 animate-spin mr-2" />Loading plans...</div>
          ) : optionCandidates.length === 0 ? (
            <div className="text-center py-16 text-gray-400">
              <Circle className="w-10 h-10 mx-auto mb-3 opacity-30" />
              <p className="font-medium">No plans found for {renewalPeriod?.quarter} {renewalPeriod?.year}</p>
              <p className="text-sm mt-1">Upload renewal rate PDFs in the Data Input tab first.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-[460px] overflow-y-auto pr-1">
              {optionCandidates.map(plan => (
                <PlanCard key={plan.plan_id} plan={plan} selected={optionIds.has(plan.plan_id)} onToggle={() => toggleOption(plan)} role="option" />
              ))}
            </div>
          )}
          <div className="mt-6 flex justify-between">
            <Button variant="outline" onClick={() => { setSearch(""); setStep(1); }}>Back</Button>
            <Button onClick={() => setStep(3)} className="gap-2 px-6" style={{ background: "#0d2240" }}>
              Continue to Generate <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: "#0d2240" }}>
              <FileSpreadsheet className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold" style={{ color: "#0d2240" }}>Review & Generate</h2>
              <p className="text-sm text-gray-500">Review your selections and generate the Marketing Renewal Comparison grid</p>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
            <div className="rounded-xl border border-gray-200 p-4">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Renewal Period</p>
              <p className="text-2xl font-bold" style={{ color: "#0d2240" }}>{renewalPeriod?.quarter} {renewalPeriod?.year}</p>
              <p className="text-sm text-gray-500 mt-1">vs {currentPeriod?.quarter} {currentPeriod?.year} (current)</p>
              <div className="mt-2 flex flex-wrap gap-1">
                {Array.from(selectedCarriers).map(c => {
                  const style = getCarrierStyle(c);
                  return <span key={c} className="text-xs px-2 py-0.5 rounded-full font-medium" style={{ background: style.bg, color: style.text }}>{c}</span>;
                })}
              </div>
            </div>
            <div className="rounded-xl border border-gray-200 p-4">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Enrolled Plans</p>
              <p className="text-2xl font-bold" style={{ color: "#0d2240" }}>{enrolledPlans.length}</p>
              <p className="text-sm text-gray-500 mt-1">{renewalIds.size} renewal matches found</p>
              <div className="mt-2 space-y-1">
                {enrolledPlans.slice(0, 3).map(p => <p key={p.plan_id} className="text-xs text-gray-600 truncate">• {p.plan_name}</p>)}
                {enrolledPlans.length > 3 && <p className="text-xs text-gray-400">+{enrolledPlans.length - 3} more</p>}
              </div>
            </div>
            <div className="rounded-xl border border-gray-200 p-4">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Option Plans</p>
              <p className="text-2xl font-bold" style={{ color: "#c9a84c" }}>{optionPlans.length}</p>
              <p className="text-sm text-gray-500 mt-1">{optionPlans.length === 0 ? "None selected" : "alternative plans"}</p>
              <div className="mt-2 space-y-1">
                {optionPlans.slice(0, 3).map(p => <p key={p.plan_id} className="text-xs text-gray-600 truncate">• {p.plan_name}</p>)}
                {optionPlans.length > 3 && <p className="text-xs text-gray-400">+{optionPlans.length - 3} more</p>}
              </div>
            </div>
          </div>
          {renewalIds.size < enrolledIds.size && (
            <div className="mb-4 p-3 rounded-lg bg-amber-50 border border-amber-200">
              <p className="text-sm text-amber-700">⚠️ {enrolledIds.size - renewalIds.size} enrolled plan(s) don't have renewal rate matches. The grid will be generated with available data.</p>
            </div>
          )}
          <div className="flex flex-col items-center gap-3 py-4">
            <Button
              onClick={handleGenerate}
              disabled={isGenerating || (enrolledIds.size === 0 && optionIds.size === 0)}
              className="gap-3 px-10 py-4 text-base h-auto"
              style={{ background: "#0d2240" }}
            >
              {isGenerating ? <><Loader2 className="w-5 h-5 animate-spin" />Generating...</> : <><Download className="w-5 h-5" />Generate Marketing Grid</>}
            </Button>
            <p className="text-xs text-gray-400">Downloads as .xlsx — ready for client presentation</p>
          </div>
          <div className="mt-4 flex justify-start">
            <Button variant="outline" onClick={() => setStep(2)}>Back</Button>
          </div>
        </div>
      )}

      {step > 0 && (
        <div className="mt-4 flex items-center gap-4 text-xs text-gray-500 px-2">
          <span><strong style={{ color: "#0d2240" }}>{renewalPeriod?.quarter} {renewalPeriod?.year}</strong> renewal</span>
          <ChevronRight className="w-3 h-3" />
          <span>{Array.from(selectedCarriers).join(", ")}</span>
          {enrolledIds.size > 0 && <><ChevronRight className="w-3 h-3" /><span><strong>{enrolledIds.size}</strong> enrolled plan{enrolledIds.size !== 1 ? "s" : ""}</span></>}
          {optionIds.size > 0 && <><ChevronRight className="w-3 h-3" /><span><strong>{optionIds.size}</strong> option{optionIds.size !== 1 ? "s" : ""}</span></>}
          <button
            onClick={() => { setStep(0); setEnrolledIds(new Set()); setOptionIds(new Set()); setSelectedCarriers(new Set()); setRenewalDate(""); }}
            className="ml-auto text-gray-400 hover:text-gray-600 underline"
          >
            Start over
          </button>
        </div>
      )}
    </div>
  );
}
