export interface MedicalDetails {
  in_network_deductible_type: string | null;
  out_network_deductible_type: string | null;
  in_network_oop_type: string | null;
  out_network_oop_type: string | null;
  wellness_benefit: string | null;
  deductible_in_ee: string | null;
  deductible_in_fam: string | null;
  coinsurance_in: string | null;
  oop_max_in_ee: string | null;
  oop_max_in_fam: string | null;
  pcp_copay: string | null;
  specialist_copay: string | null;
  inpatient_hospital: string | null;
  outpatient_facility: string | null;
  emergency_room: string | null;
  urgent_care: string | null;
  deductible_oon_ee: string | null;
  deductible_oon_fam: string | null;
  coinsurance_oon: string | null;
  oop_max_oon_ee: string | null;
  oop_max_oon_fam: string | null;
  rx_generic: string | null;
  rx_preferred_brand: string | null;
  rx_non_preferred_brand: string | null;
  hsa_qualified: string | null;
  creditable_coverage: string | null;
  dependent_coverage: string | null;
}

export interface Plan {
  plan_id: string;
  plan_type: string;
  carrier: string;
  plan_name: string;
  year: number;
  quarter: string;
  ee_only: number | null;
  ee_spouse: number | null;
  ee_children: number | null;
  family: number | null;
  created_at: string;
  updated_at: string;
  medical_details: MedicalDetails | null;
}

export interface BrowseFilters {
  carrier?: string;
  year?: number;
  quarter?: string;
  network_type?: string;
}

export interface ComparisonRequest {
  current_plan_ids: string[];   // enrolled plans — old pricing
  renewal_plan_ids: string[];   // renewal pricing for same plans (matched by position)
  option_plan_ids: string[];    // alternative plans for Opts tabs
  member_counts?: MemberCounts[];
}

export interface MemberCounts {
  ee: number;
  spouse: number;
  children: number;
  family: number;
}

export interface AutoRenewalRequest {
  renewal_effective_date: string;  // YYYY-MM-DD
  enrolled_plan_ids: string[];     // plan IDs from the RENEWAL period
  option_plan_ids: string[];
  member_counts?: MemberCounts[];
}

export interface IngestQuarterResult {
  status: "success" | "error" | "no_plans_found";
  plans?: number;
  inserted?: number;
  updated_exact?: number;
  updated_fuzzy?: number;
  detail?: string;
}

export interface IngestFileResult {
  file: string;
  status: "success" | "error" | "no_plans_found";
  detail?: string;
  detected_quarters?: string[];
  quarters: Record<string, IngestQuarterResult>;
  total_plans: number;
  inserted: number;
  updated_exact: number;
  updated_fuzzy: number;
}

export interface IngestResponse {
  total_files: number;
  total_plans_ingested: number;
  files: IngestFileResult[];
}
