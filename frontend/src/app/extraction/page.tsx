"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { Upload, TableProperties, ArrowLeftRight } from "lucide-react";
import Image from "next/image";
import { UploadTab } from "@/components/extraction/upload-tab";
import { PlansTableTab } from "@/components/extraction/plans-table-tab";
import { ComparisonTab } from "@/components/extraction/comparison-tab";
import { PlanEditDialog } from "@/components/plans/plan-edit-dialog";
import { plansApi } from "@/lib/api";
import type { BrowseFilters, Plan } from "@/types/plans";

type TabId = "upload" | "plans" | "comparison";

const TAB_META: Record<TabId, { title: string; description: string }> = {
  upload: {
    title: "Upload Files",
    description: "Upload PDFs to extract and ingest plan data automatically",
  },
  plans: {
    title: "Edit Data",
    description:
      "Browse, filter, and edit plans. Download as Master Template.",
  },
  comparison: {
    title: "Comparison",
    description:
      "Select current plans, auto-pair renewals, and generate comparison.",
  },
};

const TABS = [
  { id: "upload" as const, label: "Upload Files", icon: Upload },
  { id: "plans" as const, label: "Edit Data", icon: TableProperties },
  { id: "comparison" as const, label: "Comparison", icon: ArrowLeftRight },
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

  useEffect(() => {
    fetchPlans();
  }, [fetchPlans]);

  // Auto-select the latest year on first load
  useEffect(() => {
    if (!didAutoYear.current && plans.length > 0) {
      didAutoYear.current = true;
      const maxYear = Math.max(...plans.map((p) => p.year));
      setFilters((f) => ({ ...f, year: maxYear }));
    }
  }, [plans]);

  const handleEditSave = async (
    planId: string,
    data: Record<string, unknown>
  ) => {
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
      const { data } = await plansApi.downloadMasterTemplate(
        filters.year,
        filters.quarter
      );
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

  return (
    <div className="min-h-screen bg-gray-50">
        <header className="bg-white border-b border-gray-200 sticky top-0 z-40 shadow-sm h-16 flex items-center px-4">
          <Image
            src="/logo.png"
            alt="Envision HR Platform"
            width={50}
            height={50}
            className="h-12 w-auto rounded-lg"
          />
        </header>

        <div className="flex" style={{ minHeight: "calc(100vh - 64px)" }}>
          {/* Left Sidebar */}
          <aside className="w-56 flex-shrink-0 bg-white border-r border-gray-200">
            <nav className="p-3 space-y-1 sticky top-16">
              {TABS.map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  onClick={() => setActiveTab(id)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors text-left ${
                    activeTab === id
                      ? "bg-primary/10 text-primary border-l-2 border-primary pl-[10px]"
                      : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                  }`}
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  {label}
                </button>
              ))}
            </nav>
          </aside>

          {/* Main Content */}
          <main className="flex-1 p-6 overflow-auto">
            <div className="max-w-[1400px] mx-auto">
              <div className="mb-6">
                <h1 className="text-2xl font-bold text-gray-900">
                  {TAB_META[activeTab].title}
                </h1>
                <p className="text-sm text-gray-500 mt-1">
                  {TAB_META[activeTab].description}
                </p>
              </div>

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
        </div>

      <PlanEditDialog
        plan={editingPlan}
        open={!!editingPlan}
        onOpenChange={(open) => {
          if (!open) setEditingPlan(null);
        }}
        onSave={handleEditSave}
        isSaving={isSaving}
      />
    </div>
  );
}
