"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { UploadTab } from "@/components/extraction/upload-tab";
import { PlansTableTab } from "@/components/extraction/plans-table-tab";
import { ComparisonTab } from "@/components/extraction/comparison-tab";
import { PlanEditDialog } from "@/components/plans/plan-edit-dialog";
import { plansApi } from "@/lib/api";
import type { BrowseFilters, Plan } from "@/types/plans";

export default function ExtractionPage() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [filters, setFilters] = useState<BrowseFilters>({});
  const [loading, setLoading] = useState(false);
  const [editingPlan, setEditingPlan] = useState<Plan | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);

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
    <div className="min-h-screen bg-background">
      <div className="max-w-[1400px] mx-auto p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold">Extraction</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Upload PDFs, browse plans, and generate comparisons
          </p>
        </div>

        <Tabs defaultValue="upload" className="space-y-6">
          <TabsList>
            <TabsTrigger value="upload">Upload</TabsTrigger>
            <TabsTrigger value="plans">Plans</TabsTrigger>
            <TabsTrigger value="comparison">Comparison</TabsTrigger>
          </TabsList>

          <TabsContent value="upload">
            <UploadTab onIngestionComplete={fetchPlans} />
          </TabsContent>

          <TabsContent value="plans">
            <PlansTableTab
              plans={plans}
              loading={loading}
              filters={filters}
              onFiltersChange={setFilters}
              onEdit={setEditingPlan}
              onDownloadMasterTemplate={handleDownloadMasterTemplate}
              isDownloading={isDownloading}
            />
          </TabsContent>

          <TabsContent value="comparison">
            <ComparisonTab />
          </TabsContent>
        </Tabs>
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
