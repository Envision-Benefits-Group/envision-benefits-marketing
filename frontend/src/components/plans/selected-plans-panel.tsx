"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Download, X } from "lucide-react";
import type { Plan } from "@/types/plans";

interface SelectedPlansPanelProps {
  plans: Plan[];
  selectedCurrentIds: Set<string>;
  selectedRenewalIds: Set<string>;
  selectedOptionIds: Set<string>;
  onRemoveCurrent: (planId: string) => void;
  onRemoveRenewal: (planId: string) => void;
  onRemoveOption: (planId: string) => void;
  onGenerateComparison: () => void;
  isGenerating: boolean;
}

function PlanChip({
  plan,
  onRemove,
}: {
  plan: Plan;
  onRemove: (id: string) => void;
}) {
  return (
    <div className="flex items-center justify-between gap-2 p-2 bg-muted/50 rounded text-xs">
      <div className="min-w-0">
        <Badge variant="outline" className="text-[10px] mb-0.5">
          {plan.carrier}
        </Badge>
        <p className="truncate">{plan.plan_name}</p>
        <p className="text-muted-foreground">
          {plan.quarter} {plan.year}
        </p>
      </div>
      <Button
        variant="ghost"
        size="icon"
        className="h-6 w-6 shrink-0"
        onClick={() => onRemove(plan.plan_id)}
      >
        <X className="h-3 w-3" />
      </Button>
    </div>
  );
}

export function SelectedPlansPanel({
  plans,
  selectedCurrentIds,
  selectedRenewalIds,
  selectedOptionIds,
  onRemoveCurrent,
  onRemoveRenewal,
  onRemoveOption,
  onGenerateComparison,
  isGenerating,
}: SelectedPlansPanelProps) {
  const currentPlans = plans.filter((p) => selectedCurrentIds.has(p.plan_id));
  const renewalPlans = plans.filter((p) => selectedRenewalIds.has(p.plan_id));
  const optionPlans  = plans.filter((p) => selectedOptionIds.has(p.plan_id));

  const hasSelections =
    currentPlans.length > 0 || renewalPlans.length > 0 || optionPlans.length > 0;

  return (
    <div className="border rounded-lg p-4 h-fit sticky top-4">
      <h3 className="font-semibold text-sm mb-3">Selected Plans</h3>

      <ScrollArea className="max-h-[60vh]">
        <div className="space-y-4">

          {/* Current Plans */}
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wide">
              Current Plans (Old Pricing)
            </p>
            {currentPlans.length === 0 ? (
              <p className="text-xs text-muted-foreground italic">None selected</p>
            ) : (
              <div className="space-y-1.5">
                {currentPlans.map((plan) => (
                  <PlanChip key={plan.plan_id} plan={plan} onRemove={onRemoveCurrent} />
                ))}
              </div>
            )}
          </div>

          <Separator />

          {/* Renewal Plans */}
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wide">
              Renewal Plans (New Pricing)
            </p>
            {renewalPlans.length === 0 ? (
              <p className="text-xs text-muted-foreground italic">None selected</p>
            ) : (
              <div className="space-y-1.5">
                {renewalPlans.map((plan) => (
                  <PlanChip key={plan.plan_id} plan={plan} onRemove={onRemoveRenewal} />
                ))}
              </div>
            )}
          </div>

          <Separator />

          {/* Option Plans */}
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wide">
              Option Plans (Alternatives)
            </p>
            {optionPlans.length === 0 ? (
              <p className="text-xs text-muted-foreground italic">None selected</p>
            ) : (
              <div className="space-y-1.5">
                {optionPlans.map((plan) => (
                  <PlanChip key={plan.plan_id} plan={plan} onRemove={onRemoveOption} />
                ))}
              </div>
            )}
          </div>

        </div>
      </ScrollArea>

      <div className="mt-4">
        <Button
          className="w-full"
          onClick={onGenerateComparison}
          disabled={!hasSelections || isGenerating}
        >
          <Download className="h-4 w-4 mr-2" />
          {isGenerating ? "Generating..." : "Generate Comparison"}
        </Button>
      </div>
    </div>
  );
}