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

        # --- SECTION: MEMBER COUNTS (INPUTS) ---
        'SECTION_COUNTS': 'Member Counts (Enter values below)',
        'count_ee': 'Count: Employee Only',
        'count_sp': 'Count: Employee + Spouse',
        'count_ch': 'Count: Employee + Child(ren)',
        'count_fam': 'Count: Family',

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

        # --- SECTION: RX ---
        'SECTION_RX': 'Prescription Coverage',
        'rx_display': 'Generic / Preferred / Non-Preferred',

        # --- SECTION: OTHER ---
        'SECTION_OTHER': 'Other',
        'hsa_qualified': 'HSA Qualified',
        'creditable_coverage': 'Creditable Coverage',
        'dependent_coverage': 'Dependent Coverage'
    }

    # Rows that get Currency Format ($)
    CURRENCY_ROWS = [
        'Employee Only', 'Employee + Spouse', 'Employee + Child(ren)', 'Family',
        'Monthly Premium Total', 'Monthly Premium Difference'
    ]

    # Rows that are User Inputs (Yellow Background)
    INPUT_ROWS = [
        'Count: Employee Only', 'Count: Employee + Spouse',
        'Count: Employee + Child(ren)', 'Count: Family',
        'Monthly Premium Difference'
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

            for carrier in carriers:
                for network in network_types:
                    self._create_sheet_for_network(writer, processed_df, carrier, network)

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
            d_type = 'True Family' if x.get('in_network_deductible_type') == 'T' else 'Embedded'
            return f"{ind} / {fam} ({d_type})"

        df['deductible_display'] = df.apply(fmt_deduct, axis=1)
        df['oop_display'] = df['oop_max_in_ee'].astype(str) + " / " + df['oop_max_in_fam'].astype(str)
        df['deductible_oon_display'] = df.apply(
            lambda x: f"{x.get('deductible_oon_ee', '')} / {x.get('deductible_oon_fam', '')}", axis=1)
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

        HEALTHY_NY = ("HEALTHY NY", "HNY")
        PPO_WORD = "PPO"

        if any(k in plan for k in HEALTHY_NY) or "HEALTHY NY" in carrier:
            return "HealthyNY"

        if "PASSPORT PLAN NATIONAL" in carrier:
            return "PPO"

        if "UNIVERA" in carrier:
            return "PPO" if "ACCESS PLUS" in plan else "POS"

        if any(k in carrier for k in ("HIGHMARK", "IHA", "INDEPENDENT")):
            return "PPO" if PPO_WORD in plan else "POS"

        return "PPO" if PPO_WORD in plan else "POS"

    def _init_styles(self):
        # Header Style (Grey)
        self.header_fmt = self.workbook.add_format({
            'bold': True, 'text_wrap': True, 'valign': 'top',
            'fg_color': '#D9D9D9', 'border': 1
        })
        # Section Divider Style (Blue)
        self.section_fmt = self.workbook.add_format({
            'bold': True, 'bg_color': '#BDD7EE', 'border': 1
        })
        # Standard Cell Style
        self.cell_fmt = self.workbook.add_format({
            'text_wrap': True, 'valign': 'top', 'border': 1
        })
        # Currency Style ($)
        self.currency_fmt = self.workbook.add_format({
            'text_wrap': True, 'valign': 'top', 'border': 1,
            'num_format': '$#,##0.00'
        })
        # Input Style (Yellow)
        self.input_fmt = self.workbook.add_format({
            'text_wrap': True, 'valign': 'top', 'border': 1,
            'bg_color': '#FFFFCC'
        })
        # Input Currency Style (Yellow + $)
        self.input_currency_fmt = self.workbook.add_format({
            'text_wrap': True, 'valign': 'top', 'border': 1,
            'bg_color': '#FFFFCC', 'num_format': '$#,##0.00'
        })
        # Percentage Style (%)
        self.percent_fmt = self.workbook.add_format({
            'text_wrap': True, 'valign': 'top', 'border': 1,
            'num_format': '0.00%'  # Displays 0.15 as 15.00%
        })

    def _create_sheet_for_network(self, writer, df, carrier, network):
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

        # Create DataFrame
        matrix_df = pd.DataFrame(matrix_data, columns=['Plan Details'] + plans)
        sheet_name = f"{carrier[:15]} - {network}"[:30].replace("/", "")
        matrix_df.to_excel(writer, sheet_name=sheet_name, index=False)

        self._apply_sheet_formatting(writer.sheets[sheet_name], matrix_data, len(plans), matrix_df.columns)

    def _apply_sheet_formatting(self, worksheet, matrix_data, num_plans, columns):
        worksheet.set_column(0, 0, 35)
        worksheet.set_column(1, num_plans, 25)
        worksheet.freeze_panes(1, 1)

        idx_map = {}

        for r_idx, row in enumerate(matrix_data):
            row_label = row[0]
            idx_map[row_label] = r_idx + 2

            is_section = all(x == '' for x in row[1:])

            # --- DETERMINE FORMAT ---
            if r_idx == 0:
                base_fmt = self.header_fmt
            elif is_section:
                base_fmt = self.section_fmt
            elif row_label in self.INPUT_ROWS:
                if 'Difference' in row_label:
                    base_fmt = self.input_currency_fmt
                else:
                    base_fmt = self.input_fmt
            elif row_label in self.PERCENT_ROWS:
                base_fmt = self.percent_fmt
            elif row_label in self.CURRENCY_ROWS:
                base_fmt = self.currency_fmt
            else:
                base_fmt = self.cell_fmt

            # --- WRITE CELLS ---
            for c_idx, val in enumerate(row):
                if r_idx == 0:
                    worksheet.write(0, c_idx, columns[c_idx], self.header_fmt)
                    continue

                if c_idx > 0:
                    col_letter = xl_col_to_name(c_idx)

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
                            worksheet.write_formula(r_idx + 1, c_idx, formula, base_fmt)
                            continue
                        except KeyError:
                            pass

                    # Formula: % Difference
                    elif row_label == '% Difference':
                        try:
                            r_total = idx_map['Monthly Premium Total']
                            r_diff = idx_map['Monthly Premium Difference']
                            # Note: No need to multiply by 100 in formula.
                            # Excel stores percentage as 0.15. The 'num_format': '0.00%' handles the display.
                            formula = f"=IFERROR(({col_letter}{r_total} - {col_letter}{r_diff}) / {col_letter}{r_diff}, 0)"
                            worksheet.write_formula(r_idx + 1, c_idx, formula, base_fmt)
                            continue
                        except KeyError:
                            pass

                worksheet.write(r_idx + 1, c_idx, val, base_fmt)
