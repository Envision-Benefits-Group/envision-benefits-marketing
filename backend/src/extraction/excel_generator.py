import pandas as pd
import io
from xlsxwriter.utility import xl_col_to_name


class ExcelReportGenerator:
    """
    Handles the transformation of raw insurance plan data into
    a formatted, dynamic Excel model with formulas.
    """

    # 1. Defined Row Map (Order Matters!)
    ROW_MAP = {
        # --- SECTION: RATES ---
        'SECTION_RATES': 'Monthly Rates',
        'ee_only': 'Employee Only',
        'ee_spouse': 'Employee + Spouse',
        'ee_children': 'Employee + Child(ren)',
        'family': 'Family',

        # --- SECTION: CALCULATIONS ---
        'calc_total_premium': 'Monthly Premium Total',
        'input_premium_diff': 'Monthly Premium Difference',
        'calc_pct_diff': '% Difference',

        # --- SECTION: WELLNESS ---
        'SECTION_WELLNESS': 'Wellness Benefits',
        'wellness_benefit': 'Health & Wellness Benefit',

        # --- SECTION: IN-NETWORK ---
        'SECTION_IN_NETWORK': 'In-Network Benefits',
        'deductible_display': 'Deductible (Individual/Family)',
        'coinsurance_in': 'Coinsurance',
        'oop_display': 'Out of Pocket Maximum',
        'pcp_copay': 'PCP Copay',
        'specialist_copay': 'Specialist Copay',
        'inpatient_hospital': 'Inpatient Hospitalization',
        'outpatient_facility': 'Outpatient Facility',
        'emergency_room': 'Emergency Room',
        'urgent_care': 'Urgent Care',

        # --- SECTION: OON ---
        'SECTION_OON': 'Out-of-Network Coverage',
        'deductible_oon_display': 'Deductible (OON)',
        'coinsurance_oon': 'Coinsurance (OON)',
        'oop_oon_display': 'Out of Pocket Maximum (OON)',

        # --- SECTION: RX ---
        'SECTION_RX': 'Prescription Coverage',
        'rx_display': 'Generic / Preferred / Non-Preferred',

        # --- SECTION: OTHER ---
        'SECTION_OTHER': 'Other',
        'hsa_qualified': 'HSA Qualified',
        'creditable_coverage': 'Creditable Coverage',
        'dependent_coverage': 'Dependent Coverage',

        # --- SECTION: MEMBER COUNTS (INPUTS) --- moved to bottom
        'SECTION_COUNTS': 'Member Counts (Enter values below)',
        'count_ee': 'Count: Employee Only',
        'count_sp': 'Count: Employee + Spouse',
        'count_ch': 'Count: Employee + Child(ren)',
        'count_fam': 'Count: Family',
    }

    # Rows that get Currency Format ($)
    CURRENCY_ROWS = [
        'Employee Only', 'Employee + Spouse', 'Employee + Child(ren)', 'Family',
        'Monthly Premium Total', 'Monthly Premium Difference'
    ]

    # Rows with no special coloring (plain style)
    NO_COLOR_ROWS = [
        'Monthly Premium Total', 'Monthly Premium Difference', '% Difference',
        'Count: Employee Only', 'Count: Employee + Spouse',
        'Count: Employee + Child(ren)', 'Count: Family'
    ]

    # Rows that get Percent Format (%)
    PERCENT_ROWS = ['% Difference']

    def generate(self, df: pd.DataFrame) -> io.BytesIO:
        output = io.BytesIO()
        processed_df = self._preprocess_data(df)

        carriers = processed_df['carrier'].unique()
        network_types = sorted(processed_df['network_type'].unique())

        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            self.workbook = writer.book
            self._init_styles()

            # Handle HealthyNY separately - consolidate all carriers into one tab
            if 'HealthyNY' in network_types:
                self._create_combined_healthyny_sheet(processed_df)

            # Create per-carrier sheets for other network types
            for carrier in carriers:
                for network in network_types:
                    if network == 'HealthyNY':
                        continue  # Already handled above
                    self._create_sheet_for_network(processed_df, carrier, network)

        output.seek(0)
        return output

    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['network_type'] = df.apply(self._classify_network, axis=1)

        # Apply Hardcoded Wellness Logic
        df['wellness_benefit'] = df.apply(self._apply_wellness_logic, axis=1)

        # Pre-fill empty columns for our new inputs/calculations
        new_cols = [
            'count_ee', 'count_sp', 'count_ch', 'count_fam',
            'calc_total_premium', 'input_premium_diff', 'calc_pct_diff'
        ]
        for col in new_cols:
            df[col] = None

        # Helper to safely format embedded string
        def fmt_deduct(x):
            ind = x.get('deductible_in_ee', '')
            fam = x.get('deductible_in_fam', '')
            ind_str = str(ind).replace('$', '').replace(',', '').strip()
            fam_str = str(fam).replace('$', '').replace(',', '').strip()
            if ind_str in ('0', '0.00', '') and fam_str in ('0', '0.00', ''):
                return 'None'
            d_type = 'True Family' if x.get('in_network_deductible_type') == 'T' else 'Embedded'
            return f"{ind} / {fam} ({d_type})"

        df['deductible_display'] = df.apply(fmt_deduct, axis=1)

        # Helper to normalize coinsurance values (0%/NaN/None/0$/0 -> "None")
        def normalize_coinsurance(val):
            if pd.isna(val) or val is None:
                return 'None'
            val_str = str(val).strip().lower()
            # Check for various zero/empty representations
            if val_str in ('', 'none', 'nan', 'n/a', 'na', '0', '0%', '0.0%', '0.00%', '$0', '$0.00'):
                return 'None'
            return val

        df['coinsurance_in'] = df['coinsurance_in'].apply(normalize_coinsurance)
        df['coinsurance_oon'] = df['coinsurance_oon'].apply(normalize_coinsurance)

        # In-Network OOP with type
        def fmt_oop_in(x):
            ee = x.get('oop_max_in_ee', '')
            fam = x.get('oop_max_in_fam', '')
            oop_type = 'True Family' if x.get('in_network_oop_type') == 'T' else 'Embedded'
            return f"{ee} / {fam} ({oop_type})"

        df['oop_display'] = df.apply(fmt_oop_in, axis=1)

        # OON Deductible with type
        def fmt_deduct_oon(x):
            ee = x.get('deductible_oon_ee', '')
            fam = x.get('deductible_oon_fam', '')
            d_type = 'True Family' if x.get('out_network_deductible_type') == 'T' else 'Embedded'
            return f"{ee} / {fam} ({d_type})"

        df['deductible_oon_display'] = df.apply(fmt_deduct_oon, axis=1)

        # Out-of-Network OOP with type
        def fmt_oop_oon(x):
            ee = x.get('oop_max_oon_ee', '')
            fam = x.get('oop_max_oon_fam', '')
            oop_type = 'True Family' if x.get('out_network_oop_type') == 'T' else 'Embedded'
            return f"{ee} / {fam} ({oop_type})"

        df['oop_oon_display'] = df.apply(fmt_oop_oon, axis=1)
        df['rx_display'] = df['rx_generic'].astype(str) + " / " + df['rx_preferred_brand'].astype(str) + " / " + df[
            'rx_non_preferred_brand'].astype(str)

        return df

    def _apply_wellness_logic(self, row):
        """Overrides wellness benefit based on carrier rules."""
        carrier = str(row.get('carrier', '')).upper()
        network = row.get('network_type', '')

        # 1. Independent Health
        if 'INDEPENDENT' in carrier or 'IHA' in carrier:
            if network == 'PPO':
                return "None"
            else:  # POS and HealthyNY
                return "Health Extras $250 Or Nutrition Reimbursement up to $500 / $1,000"

        # 2. Highmark
        if 'HIGHMARK' in carrier:
            return "$250 Gym/Fitness Center Card"

        # 3. Univera
        if 'UNIVERA' in carrier:
            return ("Vitalize, a digital home base dedicated to engaging in health and wellbeing. "
                    "This digital hub includes rewards of up to $200 per subscriber and $200 per spouse, "
                    "or domestic partner, for a total rewards payout of $400 per plan year.")

        # 4. Excellus
        if 'EXCELLUS' in carrier:
            return ("ThriveWell, a digital home base dedicated to engaging in health and wellbeing. "
                    "This digital hub will include rewards of up to $200 per subscriber and $200 per spouse, "
                    "or domestic partner, for a total rewards payout of $400 per plan year.")

        # Fallback to whatever AI extracted if no match
        return row.get('wellness_benefit', '')

    def _classify_network(self, row):
        carrier = str(row.get("carrier", "")).upper()
        plan = str(row.get("plan_name", "")).upper()

        # Healthy NY — check first as it can appear across carriers
        if any(k in plan for k in ("HEALTHY NY", "HNY")) or "HEALTHY NY" in carrier:
            return "HealthyNY"

        # Univera
        if "UNIVERA" in carrier:
            return "PPO" if "ACCESS PLUS" in plan else "POS"

        # Highmark
        if "HIGHMARK" in carrier:
            return "PPO" if "PPO" in plan else "POS"

        # Independent Health / IHA
        if "INDEPENDENT" in carrier or "IHA" in carrier:
            if "PPO" in plan or "PASSPORT PLAN NATIONAL" in plan:
                return "PPO"
            return "POS"

        # Excellus / other carriers
        return "PPO" if "PPO" in plan else "POS"

    def _init_styles(self):
        # Header Style (Grey) - Left aligned for Column A
        self.header_fmt_left = self.workbook.add_format({
            'bold': True, 'text_wrap': True, 'valign': 'top',
            'fg_color': '#D9D9D9', 'border': 1, 'align': 'left'
        })
        # Header Style (Grey) - Center aligned for plan columns
        self.header_fmt_center = self.workbook.add_format({
            'bold': True, 'text_wrap': True, 'valign': 'top',
            'fg_color': '#D9D9D9', 'border': 1, 'align': 'center'
        })
        # Section Divider Style (Dark Grey with White Font) - Left aligned
        self.section_fmt_left = self.workbook.add_format({
            'bold': True, 'bg_color': '#595959', 'font_color': '#FFFFFF',
            'border': 1, 'align': 'left'
        })
        # Section Divider Style (Dark Grey with White Font) - Center aligned
        self.section_fmt_center = self.workbook.add_format({
            'bold': True, 'bg_color': '#595959', 'font_color': '#FFFFFF',
            'border': 1, 'align': 'center'
        })
        # Standard Cell Style - Left aligned
        self.cell_fmt_left = self.workbook.add_format({
            'text_wrap': True, 'valign': 'top', 'border': 1, 'align': 'left'
        })
        # Standard Cell Style - Center aligned
        self.cell_fmt_center = self.workbook.add_format({
            'text_wrap': True, 'valign': 'top', 'border': 1, 'align': 'center'
        })
        # Currency Style ($) - Left aligned
        self.currency_fmt_left = self.workbook.add_format({
            'text_wrap': True, 'valign': 'top', 'border': 1,
            'num_format': '$#,##0.00', 'align': 'left'
        })
        # Currency Style ($) - Center aligned
        self.currency_fmt_center = self.workbook.add_format({
            'text_wrap': True, 'valign': 'top', 'border': 1,
            'num_format': '$#,##0.00', 'align': 'center'
        })
        # Percentage Style (%) - Left aligned
        self.percent_fmt_left = self.workbook.add_format({
            'text_wrap': True, 'valign': 'top', 'border': 1,
            'num_format': '0.00%', 'align': 'left'
        })
        # Percentage Style (%) - Center aligned
        self.percent_fmt_center = self.workbook.add_format({
            'text_wrap': True, 'valign': 'top', 'border': 1,
            'num_format': '0.00%', 'align': 'center'
        })
        # Footer: Red bold disclaimer
        self.footer_red_fmt = self.workbook.add_format({
            'bold': True, 'font_color': '#FF0000', 'text_wrap': True
        })
        # Footer: Dark grey background note
        self.footer_note_fmt = self.workbook.add_format({
            'bold': True, 'text_wrap': True,
            'bg_color': '#808080', 'font_color': '#FFFFFF'
        })

    # Number of Excel columns each plan spans
    COLS_PER_PLAN = 2

    def _create_combined_healthyny_sheet(self, df):
        """Create a single HealthyNY tab combining all carriers."""
        subset = df[df['network_type'] == 'HealthyNY']
        if subset.empty:
            return

        # Build plan headers with carrier name: "Carrier - Plan Name"
        plan_headers = []
        for _, row in subset.iterrows():
            carrier = row['carrier']
            plan_name = row['plan_name']
            plan_headers.append(f"{carrier}\n{plan_name}")

        matrix_data = []

        # Build Matrix
        for key, label in self.ROW_MAP.items():
            if key.startswith('SECTION_'):
                matrix_data.append([label] + [''] * len(subset))
            else:
                row_data = [label]
                for i in range(len(subset)):
                    val = subset.iloc[i].get(key, '')
                    if pd.isna(val):
                        val = ''
                    row_data.append(val)
                matrix_data.append(row_data)

        worksheet = self.workbook.add_worksheet('HealthyNY')
        self._apply_sheet_formatting(worksheet, matrix_data, plan_headers)

    def _create_sheet_for_network(self, df, carrier, network):
        subset = df[(df['carrier'] == carrier) & (df['network_type'] == network)]
        if subset.empty: return

        plans = subset['plan_name'].tolist()
        matrix_data = []

        # Build Matrix
        for key, label in self.ROW_MAP.items():
            if key.startswith('SECTION_'):
                matrix_data.append([label] + [''] * len(plans))
            else:
                row_data = [label]
                for i in range(len(plans)):
                    val = subset.iloc[i].get(key, '')
                    if pd.isna(val): val = ''
                    row_data.append(val)
                matrix_data.append(row_data)

        sheet_name = f"{carrier[:15]} - {network}"[:30].replace("/", "")
        worksheet = self.workbook.add_worksheet(sheet_name)
        self._apply_sheet_formatting(worksheet, matrix_data, plans)

    def _apply_sheet_formatting(self, worksheet, matrix_data, plans):
        num_plans = len(plans)
        last_col = num_plans * self.COLS_PER_PLAN  # total plan columns

        worksheet.set_column(0, 0, 35)
        for i in range(num_plans):
            start_col = 1 + i * self.COLS_PER_PLAN
            worksheet.set_column(start_col, start_col + self.COLS_PER_PLAN - 1, 18)
        worksheet.freeze_panes(1, 1)

        # First pass: build idx_map (Excel row numbers, 1-indexed)
        idx_map = {}
        for r_idx, row in enumerate(matrix_data):
            idx_map[row[0]] = r_idx + 2  # +1 for header row, +1 for 1-indexing

        # Write header row: "Plan Details" + merged plan name headers
        worksheet.write(0, 0, 'Plan Details', self.header_fmt_left)
        for i, plan_name in enumerate(plans):
            col_start = 1 + i * self.COLS_PER_PLAN
            col_end = col_start + self.COLS_PER_PLAN - 1
            worksheet.merge_range(0, col_start, 0, col_end, plan_name, self.header_fmt_center)

        # Write data rows
        for r_idx, row in enumerate(matrix_data):
            row_label = row[0]
            excel_row = r_idx + 1  # row 0 is header

            is_section = all(x == '' for x in row[1:])

            # --- DETERMINE FORMAT ---
            # Check if this row should have no special coloring
            is_no_color = row_label in self.NO_COLOR_ROWS

            if is_section and not is_no_color:
                # Section headers get dark grey with white font
                fmt_left = self.section_fmt_left
                fmt_center = self.section_fmt_center
            elif row_label in self.PERCENT_ROWS:
                fmt_left = self.percent_fmt_left
                fmt_center = self.percent_fmt_center
            elif row_label in self.CURRENCY_ROWS:
                fmt_left = self.currency_fmt_left
                fmt_center = self.currency_fmt_center
            else:
                # Standard cell format (no special color)
                fmt_left = self.cell_fmt_left
                fmt_center = self.cell_fmt_center

            # Write label column (left aligned)
            worksheet.write(excel_row, 0, row_label, fmt_left)

            # Write plan columns (each plan spans COLS_PER_PLAN columns, merged, center aligned)
            for plan_i in range(num_plans):
                col_start = 1 + plan_i * self.COLS_PER_PLAN
                col_end = col_start + self.COLS_PER_PLAN - 1
                # The first column of each plan pair is the one used in formulas
                col_letter = xl_col_to_name(col_start)
                val = row[plan_i + 1] if plan_i + 1 < len(row) else ''

                # Formula: Monthly Premium Total
                if row_label == 'Monthly Premium Total':
                    try:
                        r_ee = idx_map['Employee Only']
                        r_sp = idx_map['Employee + Spouse']
                        r_ch = idx_map['Employee + Child(ren)']
                        r_fam = idx_map['Family']

                        c_ee = idx_map['Count: Employee Only']
                        c_sp = idx_map['Count: Employee + Spouse']
                        c_ch = idx_map['Count: Employee + Child(ren)']
                        c_fam = idx_map['Count: Family']

                        formula = (
                            f"=({col_letter}{r_ee}*{col_letter}{c_ee}) + "
                            f"({col_letter}{r_sp}*{col_letter}{c_sp}) + "
                            f"({col_letter}{r_ch}*{col_letter}{c_ch}) + "
                            f"({col_letter}{r_fam}*{col_letter}{c_fam})"
                        )
                        worksheet.merge_range(excel_row, col_start, excel_row, col_end, '', self.currency_fmt_center)
                        worksheet.write_formula(excel_row, col_start, formula, self.currency_fmt_center)
                        continue
                    except KeyError:
                        pass

                # Formula: % Difference
                elif row_label == '% Difference':
                    try:
                        r_total = idx_map['Monthly Premium Total']
                        r_diff = idx_map['Monthly Premium Difference']
                        formula = f"=IFERROR(({col_letter}{r_total} - {col_letter}{r_diff}) / {col_letter}{r_diff}, 0)"
                        worksheet.merge_range(excel_row, col_start, excel_row, col_end, '', self.percent_fmt_center)
                        worksheet.write_formula(excel_row, col_start, formula, self.percent_fmt_center)
                        continue
                    except KeyError:
                        pass

                # Section rows: merge across all plan columns
                if is_section:
                    worksheet.merge_range(excel_row, col_start, excel_row, col_end, '', fmt_center)
                else:
                    worksheet.merge_range(excel_row, col_start, excel_row, col_end, val, fmt_center)

        # --- FOOTER ROWS ---
        last_data_row = len(matrix_data)  # 0-indexed header + data rows
        last_col = num_plans * self.COLS_PER_PLAN

        footer_row_1 = last_data_row + 1
        footer_row_2 = last_data_row + 2
        footer_row_3 = last_data_row + 4  # blank row gap before note

        worksheet.merge_range(footer_row_1, 0, footer_row_1, last_col,
                              'Payroll Deductions should be verified by the Employer for Accuracy.',
                              self.footer_red_fmt)
        worksheet.merge_range(footer_row_2, 0, footer_row_2, last_col,
                              '** If there is no enrollment in the plan; monthly premium differences are based off Employee only cost',
                              self.footer_note_fmt)
        worksheet.merge_range(footer_row_3, 0, footer_row_3, last_col,
                              'Note: To unmerge cells for renewal comparison, unmerge the right column of each plan pair '
                              '(C, E, G, etc.). The left columns (B, D, F, etc.) hold all values and formulas.',
                              self.footer_note_fmt)
