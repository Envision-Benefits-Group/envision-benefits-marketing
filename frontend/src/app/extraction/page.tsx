"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import Image from "next/image";
import { UploadTab } from "@/components/extraction/upload-tab";
import { PlansTableTab } from "@/components/extraction/plans-table-tab";
import { ComparisonTab } from "@/components/extraction/comparison-tab";
import { PlanEditDialog } from "@/components/plans/plan-edit-dialog";
import { plansApi } from "@/lib/api";
import type { BrowseFilters, Plan } from "@/types/plans";
import {
  UploadCloud,
  Database,
  BarChart3,
  ChevronRight,
  Activity,
} from "lucide-react";

type TabId = "upload" | "plans" | "comparison";

const TABS: { id: TabId; label: string; description: string; icon: React.ElementType }[] = [
  {
    id: "upload",
    label: "Data Input",
    description: "Upload rate PDFs & benefit summaries",
    icon: UploadCloud,
  },
  {
    id: "plans",
    label: "Plan Data",
    description: "Browse, filter & edit extracted plans",
    icon: Database,
  },
  {
    id: "comparison",
    label: "Generate Output",
    description: "Build & download comparison grids",
    icon: BarChart3,
  },
];

export default function ExtractionPage() {
  const [activeTab, setActiveTab] = useState<TabId>("upload");
  const [plans, setPlans] = useState<Plan[]>([]);
  const [filters, setFilters] = useState<BrowseFilters>({});
  const [loading, setLoading] = useState(false);
  const [editingPlan, setEditingPlan] = useState<Plan | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const didAutoYear = useRef(false);

  const fetchPlans = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await plansApi.browse(filters);
      setPlans(data);
    } catch (err) {
      toast.error("Failed to fetch plans");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => { fetchPlans(); }, [fetchPlans]);

  useEffect(() => {
    if (!didAutoYear.current && plans.length > 0) {
      didAutoYear.current = true;
      const maxYear = Math.max(...plans.map((p) => p.year));
      setFilters((f) => ({ ...f, year: maxYear }));
    }
  }, [plans]);

  const handleEditSave = async (planId: string, data: Record<string, unknown>) => {
    setIsSaving(true);
    try {
      await plansApi.update(planId, data as Partial<Plan>);
      toast.success("Plan updated successfully");
      setEditingPlan(null);
      fetchPlans();
    } catch (err) {
      toast.error("Failed to update plan");
      console.error(err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDownloadMasterTemplate = async () => {
    if (!filters.year || !filters.quarter) {
      toast.error("Select year and quarter to download the master template");
      return;
    }
    setIsDownloading(true);
    try {
      const { data } = await plansApi.downloadMasterTemplate(filters.year, filters.quarter);
      const url = window.URL.createObjectURL(new Blob([data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = `Master-Template-${filters.quarter}-${filters.year}.xlsx`;
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success("Master template downloaded");
    } catch (err) {
      toast.error("Failed to download master template");
      console.error(err);
    } finally {
      setIsDownloading(false);
    }
  };

  const activeTabMeta = TABS.find((t) => t.id === activeTab)!;
  const ActiveIcon = activeTabMeta.icon;

  return (
    <div className="min-h-screen" style={{ background: "#f0f2f5" }}>

      {/* ── Header ──────────────────────────────────────────────────── */}
      <header
        className="sticky top-0 z-50"
        style={{
          background: "linear-gradient(135deg, #0d2240 0%, #1a3a6b 100%)",
          boxShadow: "0 2px 20px rgba(0,0,0,0.25)",
        }}
      >
        <div className="flex items-center justify-between px-6 h-16">

          {/* Left: SOLA logo */}
          <div className="flex items-center gap-3">
            <div className="bg-white rounded-lg px-2 py-1">
              <Image
                src="/sola-logo.png"
                alt="EnvisionSOLA System"
                width={110}
                height={44}
                className="h-9 w-auto object-contain"
              />
            </div>
            <div className="h-6 w-px" style={{ background: "rgba(255,255,255,0.2)" }} />
            <span
              className="text-xs font-semibold tracking-widest uppercase hidden sm:block"
              style={{ color: "#c9a84c", letterSpacing: "0.15em" }}
            >
              Benefits Marketing Platform
            </span>
          </div>

          {/* Center: Tab navigation */}
          <nav className="flex items-center gap-1">
            {TABS.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className="relative flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200"
                  style={{
                    background: isActive ? "rgba(201,168,76,0.15)" : "transparent",
                    color: isActive ? "#c9a84c" : "rgba(255,255,255,0.65)",
                    border: isActive ? "1px solid rgba(201,168,76,0.3)" : "1px solid transparent",
                  }}
                >
                  <Icon className="w-4 h-4" />
                  <span className="hidden sm:inline">{tab.label}</span>
                  {isActive && (
                    <span
                      className="absolute bottom-0 left-0 right-0 h-0.5 rounded-full"
                      style={{ background: "#c9a84c" }}
                    />
                  )}
                </button>
              );
            })}
          </nav>

          {/* Right: EB logo */}
          <div className="flex items-center">
            <Image
              src="/eb-logo.svg"
              alt="Envision Benefits Group"
              width={160}
              height={40}
              className="h-8 w-auto object-contain"
              style={{ filter: "brightness(0) invert(1)" }}
            />
          </div>
        </div>
      </header>

      {/* ── Page Title Bar ───────────────────────────────────────────── */}
      <div
        className="px-8 py-4"
        style={{ background: "white", borderBottom: "1px solid #e2e6ea" }}
      >
        <div className="max-w-[1400px] mx-auto flex items-center gap-3">
          <div
            className="flex items-center justify-center w-9 h-9 rounded-lg flex-shrink-0"
            style={{ background: "#0d2240" }}
          >
            <ActiveIcon className="w-5 h-5" style={{ color: "#c9a84c" }} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium" style={{ color: "#8a95a0" }}>
                Marketing Grid
              </span>
              <ChevronRight className="w-3 h-3" style={{ color: "#c0c8d0" }} />
              <span className="text-xs font-semibold" style={{ color: "#0d2240" }}>
                {activeTabMeta.label}
              </span>
            </div>
            <h1 className="text-xl font-bold mt-0.5" style={{ color: "#0d2240" }}>
              {activeTabMeta.label}
            </h1>
            <p className="text-xs mt-0.5" style={{ color: "#8a95a0" }}>
              {activeTabMeta.description}
            </p>
          </div>
          <div className="ml-auto flex items-center gap-2 px-3 py-1.5 rounded-lg" style={{ background: "#f0f2f5" }}>
            <Activity className="w-3.5 h-3.5" style={{ color: "#4caf50" }} />
            <span className="text-xs font-medium" style={{ color: "#6b7a8a" }}>
              {plans.length} plan{plans.length !== 1 ? "s" : ""} in database
            </span>
          </div>
        </div>
      </div>

      {/* ── Main Content ─────────────────────────────────────────────── */}
      <main className="px-8 py-6">
        <div className="max-w-[1400px] mx-auto">
          {activeTab === "upload" && (
            <UploadTab onIngestionComplete={fetchPlans} />
          )}
          {activeTab === "plans" && (
            <PlansTableTab
              plans={plans}
              loading={loading}
              filters={filters}
              onFiltersChange={setFilters}
              onEdit={setEditingPlan}
              onDownloadMasterTemplate={handleDownloadMasterTemplate}
              isDownloading={isDownloading}
            />
          )}
          {activeTab === "comparison" && <ComparisonTab />}
        </div>
      </main>

      {/* ── Footer ───────────────────────────────────────────────────── */}
      <footer
        className="mt-8 px-8 py-4 text-center text-xs"
        style={{ color: "#9aa3ad", borderTop: "1px solid #e2e6ea", background: "white" }}
      >
        © {new Date().getFullYear()} Envision Benefits Group · EnvisionSOLA Benefits Marketing Platform
      </footer>

      <PlanEditDialog
        plan={editingPlan}
        open={!!editingPlan}
        onOpenChange={(open) => { if (!open) setEditingPlan(null); }}
        onSave={handleEditSave}
        isSaving={isSaving}
      />
    </div>
  );
}
