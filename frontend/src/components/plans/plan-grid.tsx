"use client";

import { PlanCard } from "./plan-card";
import type { Plan } from "@/types/plans";

interface PlanGridProps {
  plans: Plan[];
  selectedCurrentIds: Set<string>;
  selectedNewIds: Set<string>;
  onAddAsCurrent: (plan: Plan) => void;
  onAddAsNew: (plan: Plan) => void;
  onEdit: (plan: Plan) => void;
}

export function PlanGrid({
  plans,
  selectedCurrentIds,
  selectedNewIds,
  onAddAsCurrent,
  onAddAsNew,
  onEdit,
}: PlanGridProps) {
  if (plans.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-muted-foreground">
        No plans found for these filters.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {plans.map((plan) => (
        <PlanCard
          key={plan.plan_id}
          plan={plan}
          isSelectedCurrent={selectedCurrentIds.has(plan.plan_id)}
          isSelectedNew={selectedNewIds.has(plan.plan_id)}
          onAddAsCurrent={onAddAsCurrent}
          onAddAsNew={onAddAsNew}
          onEdit={onEdit}
        />
      ))}
    </div>
  );
}
