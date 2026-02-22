"use client";

import { PlanListItem } from "./plan-list-item";
import type { Plan } from "@/types/plans";

interface PlanListProps {
  plans: Plan[];
  selectedCurrentIds: Set<string>;
  selectedNewIds: Set<string>;
  onAddAsCurrent: (plan: Plan) => void;
  onAddAsNew: (plan: Plan) => void;
  onEdit: (plan: Plan) => void;
}

export function PlanList({
  plans,
  selectedCurrentIds,
  selectedNewIds,
  onAddAsCurrent,
  onAddAsNew,
  onEdit,
}: PlanListProps) {
  if (plans.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-muted-foreground">
        No plans found for these filters.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {plans.map((plan) => (
        <PlanListItem
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
