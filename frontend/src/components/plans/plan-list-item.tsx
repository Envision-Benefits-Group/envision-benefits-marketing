"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Pencil, Plus } from "lucide-react";
import type { Plan } from "@/types/plans";

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

interface PlanListItemProps {
  plan: Plan;
  isSelectedCurrent: boolean;
  isSelectedNew: boolean;
  onAddAsCurrent: (plan: Plan) => void;
  onAddAsNew: (plan: Plan) => void;
  onEdit: (plan: Plan) => void;
}

export function PlanListItem({
  plan,
  isSelectedCurrent,
  isSelectedNew,
  onAddAsCurrent,
  onAddAsNew,
  onEdit,
}: PlanListItemProps) {
  const isSelected = isSelectedCurrent || isSelectedNew;

  return (
    <div
      className={`flex items-center gap-4 p-3 border rounded-lg transition-all hover:shadow-sm ${
        isSelected ? "ring-2 ring-primary bg-primary/5" : ""
      }`}
    >
      <Badge className={`shrink-0 ${getCarrierClass(plan.carrier)}`}>
        {plan.carrier}
      </Badge>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium truncate">{plan.plan_name}</p>
        <p className="text-xs text-muted-foreground">
          {plan.quarter} {plan.year} &middot; {plan.plan_type}
        </p>
      </div>
      <div className="hidden sm:flex gap-4 text-xs shrink-0">
        <div className="text-center">
          <p className="text-muted-foreground">EE Only</p>
          <p className="font-medium">{formatCurrency(plan.ee_only)}</p>
        </div>
        <div className="text-center">
          <p className="text-muted-foreground">EE+Spouse</p>
          <p className="font-medium">{formatCurrency(plan.ee_spouse)}</p>
        </div>
        <div className="text-center">
          <p className="text-muted-foreground">EE+Child</p>
          <p className="font-medium">{formatCurrency(plan.ee_children)}</p>
        </div>
        <div className="text-center">
          <p className="text-muted-foreground">Family</p>
          <p className="font-medium">{formatCurrency(plan.family)}</p>
        </div>
      </div>
      <div className="flex items-center gap-1 shrink-0">
        <Button
          variant={isSelectedCurrent ? "default" : "outline"}
          size="sm"
          className="h-7 text-xs"
          onClick={() => onAddAsCurrent(plan)}
        >
          {isSelectedCurrent ? "Current" : "Current"}
        </Button>
        <Button
          variant={isSelectedNew ? "default" : "outline"}
          size="sm"
          className="h-7 text-xs"
          onClick={() => onAddAsNew(plan)}
        >
          {isSelectedNew ? "New" : "New"}
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          onClick={() => onEdit(plan)}
        >
          <Pencil className="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  );
}
