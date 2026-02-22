"use client";

import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import type { Plan } from "@/types/plans";

interface PlanEditDialogProps {
  plan: Plan | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSave: (planId: string, data: Record<string, unknown>) => Promise<void>;
  isSaving: boolean;
}

interface FormValues {
  carrier: string;
  plan_name: string;
  ee_only: string;
  ee_spouse: string;
  ee_children: string;
  family: string;
  deductible_in_ee: string;
  deductible_in_fam: string;
  in_network_deductible_type: string;
  coinsurance_in: string;
  oop_max_in_ee: string;
  oop_max_in_fam: string;
  in_network_oop_type: string;
  pcp_copay: string;
  specialist_copay: string;
  inpatient_hospital: string;
  outpatient_facility: string;
  emergency_room: string;
  urgent_care: string;
  deductible_oon_ee: string;
  deductible_oon_fam: string;
  out_network_deductible_type: string;
  coinsurance_oon: string;
  oop_max_oon_ee: string;
  oop_max_oon_fam: string;
  out_network_oop_type: string;
  rx_generic: string;
  rx_preferred_brand: string;
  rx_non_preferred_brand: string;
  hsa_qualified: string;
  creditable_coverage: string;
  dependent_coverage: string;
  wellness_benefit: string;
}

export function PlanEditDialog({
  plan,
  open,
  onOpenChange,
  onSave,
  isSaving,
}: PlanEditDialogProps) {
  const { register, handleSubmit, reset } = useForm<FormValues>();
  const [pendingData, setPendingData] = useState<Record<string, unknown> | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);

  useEffect(() => {
    if (plan) {
      const d = plan.medical_details;
      reset({
        carrier: plan.carrier,
        plan_name: plan.plan_name,
        ee_only: plan.ee_only?.toString() ?? "",
        ee_spouse: plan.ee_spouse?.toString() ?? "",
        ee_children: plan.ee_children?.toString() ?? "",
        family: plan.family?.toString() ?? "",
        deductible_in_ee: d?.deductible_in_ee ?? "",
        deductible_in_fam: d?.deductible_in_fam ?? "",
        in_network_deductible_type: d?.in_network_deductible_type ?? "",
        coinsurance_in: d?.coinsurance_in ?? "",
        oop_max_in_ee: d?.oop_max_in_ee ?? "",
        oop_max_in_fam: d?.oop_max_in_fam ?? "",
        in_network_oop_type: d?.in_network_oop_type ?? "",
        pcp_copay: d?.pcp_copay ?? "",
        specialist_copay: d?.specialist_copay ?? "",
        inpatient_hospital: d?.inpatient_hospital ?? "",
        outpatient_facility: d?.outpatient_facility ?? "",
        emergency_room: d?.emergency_room ?? "",
        urgent_care: d?.urgent_care ?? "",
        deductible_oon_ee: d?.deductible_oon_ee ?? "",
        deductible_oon_fam: d?.deductible_oon_fam ?? "",
        out_network_deductible_type: d?.out_network_deductible_type ?? "",
        coinsurance_oon: d?.coinsurance_oon ?? "",
        oop_max_oon_ee: d?.oop_max_oon_ee ?? "",
        oop_max_oon_fam: d?.oop_max_oon_fam ?? "",
        out_network_oop_type: d?.out_network_oop_type ?? "",
        rx_generic: d?.rx_generic ?? "",
        rx_preferred_brand: d?.rx_preferred_brand ?? "",
        rx_non_preferred_brand: d?.rx_non_preferred_brand ?? "",
        hsa_qualified: d?.hsa_qualified ?? "",
        creditable_coverage: d?.creditable_coverage ?? "",
        dependent_coverage: d?.dependent_coverage ?? "",
        wellness_benefit: d?.wellness_benefit ?? "",
      });
    }
  }, [plan, reset]);

  const buildUpdates = (data: FormValues): Record<string, unknown> => ({
    carrier: data.carrier,
    plan_name: data.plan_name,
    ee_only: data.ee_only ? parseFloat(data.ee_only) : null,
    ee_spouse: data.ee_spouse ? parseFloat(data.ee_spouse) : null,
    ee_children: data.ee_children ? parseFloat(data.ee_children) : null,
    family: data.family ? parseFloat(data.family) : null,
    deductible_in_ee: data.deductible_in_ee || null,
    deductible_in_fam: data.deductible_in_fam || null,
    in_network_deductible_type: data.in_network_deductible_type || null,
    coinsurance_in: data.coinsurance_in || null,
    oop_max_in_ee: data.oop_max_in_ee || null,
    oop_max_in_fam: data.oop_max_in_fam || null,
    in_network_oop_type: data.in_network_oop_type || null,
    pcp_copay: data.pcp_copay || null,
    specialist_copay: data.specialist_copay || null,
    inpatient_hospital: data.inpatient_hospital || null,
    outpatient_facility: data.outpatient_facility || null,
    emergency_room: data.emergency_room || null,
    urgent_care: data.urgent_care || null,
    deductible_oon_ee: data.deductible_oon_ee || null,
    deductible_oon_fam: data.deductible_oon_fam || null,
    out_network_deductible_type: data.out_network_deductible_type || null,
    coinsurance_oon: data.coinsurance_oon || null,
    oop_max_oon_ee: data.oop_max_oon_ee || null,
    oop_max_oon_fam: data.oop_max_oon_fam || null,
    out_network_oop_type: data.out_network_oop_type || null,
    rx_generic: data.rx_generic || null,
    rx_preferred_brand: data.rx_preferred_brand || null,
    rx_non_preferred_brand: data.rx_non_preferred_brand || null,
    hsa_qualified: data.hsa_qualified || null,
    creditable_coverage: data.creditable_coverage || null,
    dependent_coverage: data.dependent_coverage || null,
    wellness_benefit: data.wellness_benefit || null,
  });

  const onSubmit = (data: FormValues) => {
    if (!plan) return;
    setPendingData(buildUpdates(data));
    setConfirmOpen(true);
  };

  const handleConfirm = async () => {
    if (!plan || !pendingData) return;
    setConfirmOpen(false);
    await onSave(plan.plan_id, pendingData);
    setPendingData(null);
  };

  return (
    <>
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh]">
        <DialogHeader>
          <DialogTitle>Edit Plan</DialogTitle>
          <DialogDescription>
            {plan?.carrier} - {plan?.plan_name}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)}>
          <ScrollArea className="h-[60vh] pr-4">
            <div className="space-y-6">
              {/* Basic Info */}
              <section>
                <h4 className="text-sm font-semibold mb-3">Basic Info</h4>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label htmlFor="carrier">Carrier</Label>
                    <Input id="carrier" {...register("carrier")} />
                  </div>
                  <div>
                    <Label htmlFor="plan_name">Plan Name</Label>
                    <Input id="plan_name" {...register("plan_name")} />
                  </div>
                </div>
              </section>

              <Separator />

              {/* Rates */}
              <section>
                <h4 className="text-sm font-semibold mb-3">Monthly Rates</h4>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label htmlFor="ee_only">Employee Only</Label>
                    <Input id="ee_only" type="number" step="0.01" {...register("ee_only")} />
                  </div>
                  <div>
                    <Label htmlFor="ee_spouse">Employee + Spouse</Label>
                    <Input id="ee_spouse" type="number" step="0.01" {...register("ee_spouse")} />
                  </div>
                  <div>
                    <Label htmlFor="ee_children">Employee + Child(ren)</Label>
                    <Input id="ee_children" type="number" step="0.01" {...register("ee_children")} />
                  </div>
                  <div>
                    <Label htmlFor="family">Family</Label>
                    <Input id="family" type="number" step="0.01" {...register("family")} />
                  </div>
                </div>
              </section>

              <Separator />

              {/* In-Network */}
              <section>
                <h4 className="text-sm font-semibold mb-3">In-Network Benefits</h4>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label htmlFor="deductible_in_ee">Deductible (Individual)</Label>
                    <Input id="deductible_in_ee" {...register("deductible_in_ee")} />
                  </div>
                  <div>
                    <Label htmlFor="deductible_in_fam">Deductible (Family)</Label>
                    <Input id="deductible_in_fam" {...register("deductible_in_fam")} />
                  </div>
                  <div>
                    <Label htmlFor="in_network_deductible_type">Deductible Type (T/E)</Label>
                    <Input id="in_network_deductible_type" {...register("in_network_deductible_type")} />
                  </div>
                  <div>
                    <Label htmlFor="coinsurance_in">Coinsurance</Label>
                    <Input id="coinsurance_in" {...register("coinsurance_in")} />
                  </div>
                  <div>
                    <Label htmlFor="oop_max_in_ee">OOP Max (Individual)</Label>
                    <Input id="oop_max_in_ee" {...register("oop_max_in_ee")} />
                  </div>
                  <div>
                    <Label htmlFor="oop_max_in_fam">OOP Max (Family)</Label>
                    <Input id="oop_max_in_fam" {...register("oop_max_in_fam")} />
                  </div>
                  <div>
                    <Label htmlFor="in_network_oop_type">OOP Type (T/E)</Label>
                    <Input id="in_network_oop_type" {...register("in_network_oop_type")} />
                  </div>
                  <div>
                    <Label htmlFor="pcp_copay">PCP Copay</Label>
                    <Input id="pcp_copay" {...register("pcp_copay")} />
                  </div>
                  <div>
                    <Label htmlFor="specialist_copay">Specialist Copay</Label>
                    <Input id="specialist_copay" {...register("specialist_copay")} />
                  </div>
                  <div>
                    <Label htmlFor="inpatient_hospital">Inpatient Hospital</Label>
                    <Input id="inpatient_hospital" {...register("inpatient_hospital")} />
                  </div>
                  <div>
                    <Label htmlFor="outpatient_facility">Outpatient Facility</Label>
                    <Input id="outpatient_facility" {...register("outpatient_facility")} />
                  </div>
                  <div>
                    <Label htmlFor="emergency_room">Emergency Room</Label>
                    <Input id="emergency_room" {...register("emergency_room")} />
                  </div>
                  <div>
                    <Label htmlFor="urgent_care">Urgent Care</Label>
                    <Input id="urgent_care" {...register("urgent_care")} />
                  </div>
                </div>
              </section>

              <Separator />

              {/* Out-of-Network */}
              <section>
                <h4 className="text-sm font-semibold mb-3">Out-of-Network</h4>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label htmlFor="deductible_oon_ee">Deductible OON (Individual)</Label>
                    <Input id="deductible_oon_ee" {...register("deductible_oon_ee")} />
                  </div>
                  <div>
                    <Label htmlFor="deductible_oon_fam">Deductible OON (Family)</Label>
                    <Input id="deductible_oon_fam" {...register("deductible_oon_fam")} />
                  </div>
                  <div>
                    <Label htmlFor="out_network_deductible_type">OON Deductible Type (T/E)</Label>
                    <Input id="out_network_deductible_type" {...register("out_network_deductible_type")} />
                  </div>
                  <div>
                    <Label htmlFor="coinsurance_oon">Coinsurance OON</Label>
                    <Input id="coinsurance_oon" {...register("coinsurance_oon")} />
                  </div>
                  <div>
                    <Label htmlFor="oop_max_oon_ee">OOP Max OON (Individual)</Label>
                    <Input id="oop_max_oon_ee" {...register("oop_max_oon_ee")} />
                  </div>
                  <div>
                    <Label htmlFor="oop_max_oon_fam">OOP Max OON (Family)</Label>
                    <Input id="oop_max_oon_fam" {...register("oop_max_oon_fam")} />
                  </div>
                  <div>
                    <Label htmlFor="out_network_oop_type">OON OOP Type (T/E)</Label>
                    <Input id="out_network_oop_type" {...register("out_network_oop_type")} />
                  </div>
                </div>
              </section>

              <Separator />

              {/* Rx */}
              <section>
                <h4 className="text-sm font-semibold mb-3">Prescription Coverage</h4>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label htmlFor="rx_generic">Generic</Label>
                    <Input id="rx_generic" {...register("rx_generic")} />
                  </div>
                  <div>
                    <Label htmlFor="rx_preferred_brand">Preferred Brand</Label>
                    <Input id="rx_preferred_brand" {...register("rx_preferred_brand")} />
                  </div>
                  <div>
                    <Label htmlFor="rx_non_preferred_brand">Non-Preferred Brand</Label>
                    <Input id="rx_non_preferred_brand" {...register("rx_non_preferred_brand")} />
                  </div>
                </div>
              </section>

              <Separator />

              {/* Other */}
              <section>
                <h4 className="text-sm font-semibold mb-3">Other</h4>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label htmlFor="hsa_qualified">HSA Qualified</Label>
                    <Input id="hsa_qualified" {...register("hsa_qualified")} />
                  </div>
                  <div>
                    <Label htmlFor="creditable_coverage">Creditable Coverage</Label>
                    <Input id="creditable_coverage" {...register("creditable_coverage")} />
                  </div>
                  <div>
                    <Label htmlFor="dependent_coverage">Dependent Coverage</Label>
                    <Input id="dependent_coverage" {...register("dependent_coverage")} />
                  </div>
                  <div>
                    <Label htmlFor="wellness_benefit">Wellness Benefit</Label>
                    <Input id="wellness_benefit" {...register("wellness_benefit")} />
                  </div>
                </div>
              </section>
            </div>
          </ScrollArea>
          <DialogFooter className="mt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSaving}>
              {isSaving ? "Saving..." : "Save Changes"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>

    <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Save changes?</AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to update this plan? This will overwrite the
            existing data.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={() => setPendingData(null)}>
            Cancel
          </AlertDialogCancel>
          <AlertDialogAction onClick={handleConfirm}>
            Confirm
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
    </>
  );
}
