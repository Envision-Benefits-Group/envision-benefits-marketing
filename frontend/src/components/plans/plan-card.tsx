"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
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

interface PlanCardProps {
  plan: Plan;
  isSelectedCurrent: boolean;
  isSelectedNew: boolean;
  onAddAsCurrent: (plan: Plan) => void;
  onAddAsNew: (plan: Plan) => void;
  onEdit: (plan: Plan) => void;
}

export function PlanCard({
  plan,
  isSelectedCurrent,
  isSelectedNew,
  onAddAsCurrent,
  onAddAsNew,
  onEdit,
}: PlanCardProps) {
  const isSelected = isSelectedCurrent || isSelectedNew;

  return (
    <Card
      className={`transition-all hover:shadow-md ${
        isSelected ? "ring-2 ring-primary" : ""
      }`}
    >
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <div className="space-y-1 min-w-0">
            <Badge className={getCarrierClass(plan.carrier)}>
              {plan.carrier}
            </Badge>
            <h3 className="text-sm font-medium leading-tight truncate">
              {plan.plan_name}
            </h3>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7 shrink-0"
            onClick={() => onEdit(plan)}
          >
            <Pencil className="h-3.5 w-3.5" />
          </Button>
        </div>
        <div className="flex gap-2 text-xs text-muted-foreground">
          <span>{plan.quarter} {plan.year}</span>
          <span>{plan.plan_type}</span>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs mb-3">
          <div className="flex justify-between">
            <span className="text-muted-foreground">EE Only</span>
            <span className="font-medium">{formatCurrency(plan.ee_only)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">EE+Spouse</span>
            <span className="font-medium">{formatCurrency(plan.ee_spouse)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">EE+Child</span>
            <span className="font-medium">{formatCurrency(plan.ee_children)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Family</span>
            <span className="font-medium">{formatCurrency(plan.family)}</span>
          </div>
        </div>
        <div className="flex gap-1">
          <Button
            variant={isSelectedCurrent ? "default" : "outline"}
            size="sm"
            className="flex-1 h-7 text-xs"
            onClick={() => onAddAsCurrent(plan)}
          >
            <Plus className="h-3 w-3 mr-1" />
            {isSelectedCurrent ? "Current" : "Add Current"}
          </Button>
          <Button
            variant={isSelectedNew ? "default" : "outline"}
            size="sm"
            className="flex-1 h-7 text-xs"
            onClick={() => onAddAsNew(plan)}
          >
            <Plus className="h-3 w-3 mr-1" />
            {isSelectedNew ? "New Option" : "Add New"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
