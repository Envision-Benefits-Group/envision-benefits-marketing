import pandas as pd
import io
from difflib import SequenceMatcher
from xlsxwriter.utility import xl_col_to_name


class BaseExcelGenerator:
    """
    Shared logic for Excel report generation: row mapping, styles,
    carrier colors, network classification, preprocessing.
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

    # Color Mapping — matched by keyword in carrier/plan name
    CARRIER_COLORS = {
        'IHA': {'bg_color': '#FF0000', 'font_color': '#FFFFFF'},
        'INDEPENDENT': {'bg_color': '#FF0000', 'font_color': '#FFFFFF'},
        'HIGHMARK': {'bg_color': '#008DD1', 'font_color': '#FFFFFF'},
        'UNIVERA': {'bg_color': '#82BB00', 'font_color': '#000000'},
        'EXCELLUS': {'bg_color': '#4472C4', 'font_color': '#FFFFFF'},
        'SHORT-TERM DISABILITY': {'bg_color': '#B39DDB', 'font_color': '#000000'},
        'STD': {'bg_color': '#B39DDB', 'font_color': '#000000'},
        'STD CURRENT': {'bg_color': '#D1C4E9', 'font_color': '#000000'},
        'STD RENEWAL': {'bg_color': '#D1C4E9', 'font_color': '#000000'},
        'LONG-TERM DISABILITY': {'bg_color': '#4DB6AC', 'font_color': '#000000'},
        'LTD': {'bg_color': '#4DB6AC', 'font_color': '#000000'},
        'LTD CURRENT': {'bg_color': '#A8DADC', 'font_color': '#000000'},
        'LTD RENEWAL': {'bg_color': '#A8DADC', 'font_color': '#000000'},
        'DENTAL': {'bg_color': '#FF8624', 'font_color': '#000000'},
        'DENTAL CURRENT': {'bg_color': '#FFA862', 'font_color': '#000000'},
        'DENTAL RENEWAL': {'bg_color': '#FFA862', 'font_color': '#000000'},
        'VISION CURRENT': {'bg_color': '#FFC5D3', 'font_color': '#000000'},
        'VISION RENEWAL': {'bg_color': '#FFC5D3', 'font_color': '#000000'},
        'VISION': {'bg_color': '#E75480', 'font_color': '#FFFFFF'},
        'LEGAL': {'bg_color': '#6E238E', 'font_color': '#FFFFFF'},
        'BASIC LIFE': {'bg_color': '#06402B', 'font_color': '#FFFFFF'},
        'AD&D': {'bg_color': '#06402B', 'font_color': '#FFFFFF'},
        'LIFE CURRENT': {'bg_color': '#80EF80', 'font_color': '#000000'},
        'LIFE RENEWAL': {'bg_color': '#80EF80', 'font_color': '#000000'},
        'VOLUNTARY LIFE': {'bg_color': '#9CAF88', 'font_color': '#000000'},
        'VOL LIFE': {'bg_color': '#9CAF88', 'font_color': '#000000'},
        'VOL CURRENT': {'bg_color': '#737D5C', 'font_color': '#FFFFFF'},
        'VOL RENEWAL': {'bg_color': '#737D5C', 'font_color': '#FFFFFF'},
    }

    DEFAULT_HEADER_COLOR = {'bg_color': '#708090', 'font_color': '#FFFFFF'}

    # Number of Excel columns each plan spans
    COLS_PER_PLAN = 2

    def _classify_network(self, row):
        carrier = str(row.get("carrier", "")).upper()
        plan = str(row.get("plan_name", "")).upper()

        # Healthy NY — fuzzy match against known variations
        hny_refs = ["HEALTHY NY", "HEALTHY NEW YORK", "HNY", "HEALTHYNY"]
        combined = f"{carrier} {plan}"
        for ref in hny_refs:
            if ref in combined:
                return "HealthyNY"
        for ref in ["HEALTHY NEW YORK", "HEALTHY NY"]:
            if SequenceMatcher(None, ref, plan).ratio() >= 0.6:
                return "HealthyNY"
            words = plan.split()
            for i in range(len(words)):
                for j in range(i + 2, min(i + 5, len(words) + 1)):
                    chunk = " ".join(words[i:j])
                    if SequenceMatcher(None, ref, chunk).ratio() >= 0.7:
                        return "HealthyNY"

        if "UNIVERA" in carrier:
            return "PPO" if "ACCESS PLUS" in plan else "POS"
        if "HIGHMARK" in carrier:
            return "PPO" if "PPO" in plan else "POS"
        if "INDEPENDENT" in carrier or "IHA" in carrier:
            if "PPO" in plan or "PASSPORT PLAN NATIONAL" in plan:
                return "PPO"
            return "POS"
        return "PPO" if "PPO" in plan else "POS"

    def _apply_wellness_logic(self, row):
        carrier = str(row.get('carrier', '')).upper()
        network = row.get('network_type', '')

        if 'INDEPENDENT' in carrier or 'IHA' in carrier:
            if network == 'PPO':
                return "None"
            else:
                return "Health Extras $250 Or Nutrition Reimbursement up to $500 / $1,000"
        if 'HIGHMARK' in carrier:
            return "$250 Gym/Fitness Center Card"
        if 'UNIVERA' in carrier:
            return ("Vitalize, a digital home base dedicated to engaging in health and wellbeing. "
                    "This digital hub includes rewards of up to $200 per subscriber and $200 per spouse, "
                    "or domestic partner, for a total rewards payout of $400 per plan year.")
        if 'EXCELLUS' in carrier:
            return ("ThriveWell, a digital home base dedicated to engaging in health and wellbeing. "
                    "This digital hub will include rewards of up to $200 per subscriber and $200 per spouse, "
                    "or domestic partner, for a total rewards payout of $400 per plan year.")
        return row.get('wellness_benefit', '')

    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['network_type'] = df.apply(self._classify_network, axis=1)
        df['wellness_benefit'] = df.apply(self._apply_wellness_logic, axis=1)

        new_cols = [
            'count_ee', 'count_sp', 'count_ch', 'count_fam',
            'calc_total_premium', 'input_premium_diff', 'calc_pct_diff'
        ]
        for col in new_cols:
            df[col] = None

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

        def normalize_coinsurance(val):
            if pd.isna(val) or val is None:
                return 'None'
            val_str = str(val).strip().lower()
            if val_str in ('', 'none', 'nan', 'n/a', 'na', '0', '0%', '0.0%', '0.00%', '$0', '$0.00'):
                return 'None'
            return val

        df['coinsurance_in'] = df['coinsurance_in'].apply(normalize_coinsurance)
        df['coinsurance_oon'] = df['coinsurance_oon'].apply(normalize_coinsurance)

        def fmt_oop_in(x):
            ee = x.get('oop_max_in_ee', '')
            fam = x.get('oop_max_in_fam', '')
            oop_type = 'True Family' if x.get('in_network_oop_type') == 'T' else 'Embedded'
            return f"{ee} / {fam} ({oop_type})"

        df['oop_display'] = df.apply(fmt_oop_in, axis=1)

        def fmt_deduct_oon(x):
            ee = x.get('deductible_oon_ee', '')
            fam = x.get('deductible_oon_fam', '')
            d_type = 'True Family' if x.get('out_network_deductible_type') == 'T' else 'Embedded'
            return f"{ee} / {fam} ({d_type})"

        df['deductible_oon_display'] = df.apply(fmt_deduct_oon, axis=1)

        def fmt_oop_oon(x):
            ee = x.get('oop_max_oon_ee', '')
            fam = x.get('oop_max_oon_fam', '')
            oop_type = 'True Family' if x.get('out_network_oop_type') == 'T' else 'Embedded'
            return f"{ee} / {fam} ({oop_type})"

        df['oop_oon_display'] = df.apply(fmt_oop_oon, axis=1)

        def fmt_rx(row):
            parts = [
                str(row.get('rx_generic', '')),
                str(row.get('rx_preferred_brand', '')),
                str(row.get('rx_non_preferred_brand', '')),
            ]
            prefix = "Deductible then "
            has_deductible = any(p.startswith(prefix) for p in parts)
            cleaned = [p[len(prefix):].strip() if p.startswith(prefix) else p.strip() for p in parts]
            combined = " / ".join(cleaned)
            return f"Deductible then {combined}" if has_deductible else combined

        df['rx_display'] = df.apply(fmt_rx, axis=1)

        return df

    def _init_styles(self):
        self.header_fmt_left = self.workbook.add_format({
            'bold': True, 'text_wrap': True, 'valign': 'vcenter',
            'fg_color': '#D9D9D9', 'border': 1, 'align': 'left'
        })
        self.header_fmt_center = self.workbook.add_format({
            'bold': True, 'text_wrap': True, 'valign': 'vcenter',
            'fg_color': '#D9D9D9', 'border': 1, 'align': 'center'
        })
        self.section_fmt_left = self.workbook.add_format({
            'bold': True, 'bg_color': '#595959', 'font_color': '#FFFFFF',
            'border': 1, 'align': 'left'
        })
        self.section_fmt_center = self.workbook.add_format({
            'bold': True, 'bg_color': '#595959', 'font_color': '#FFFFFF',
            'border': 1, 'align': 'center'
        })
        self.cell_fmt_left = self.workbook.add_format({
            'text_wrap': True, 'valign': 'top', 'border': 1, 'align': 'left'
        })
        self.cell_fmt_center = self.workbook.add_format({
            'text_wrap': True, 'valign': 'top', 'border': 1, 'align': 'center'
        })
        self.currency_fmt_left = self.workbook.add_format({
            'text_wrap': True, 'valign': 'top', 'border': 1,
            'num_format': '$#,##0.00', 'align': 'left'
        })
        self.currency_fmt_center = self.workbook.add_format({
            'text_wrap': True, 'valign': 'top', 'border': 1,
            'num_format': '$#,##0.00', 'align': 'center'
        })
        self.percent_fmt_left = self.workbook.add_format({
            'text_wrap': True, 'valign': 'top', 'border': 1,
            'num_format': '0.00%', 'align': 'left'
        })
        self.percent_fmt_center = self.workbook.add_format({
            'text_wrap': True, 'valign': 'top', 'border': 1,
            'num_format': '0.00%', 'align': 'center'
        })
        self.footer_red_fmt = self.workbook.add_format({
            'bold': True, 'font_color': '#FF0000', 'text_wrap': True
        })
        self.footer_note_fmt = self.workbook.add_format({
            'bold': True, 'text_wrap': True,
            'bg_color': '#808080', 'font_color': '#FFFFFF'
        })

    def _get_carrier_color(self, carrier_name: str) -> dict:
        carrier_upper = str(carrier_name).upper()
        for keyword, colors in self.CARRIER_COLORS.items():
            if keyword in carrier_upper:
                return colors
        return self.DEFAULT_HEADER_COLOR

    def _create_carrier_header_format(self, carrier_name: str):
        colors = self._get_carrier_color(carrier_name)
        return self.workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'vcenter',
            'fg_color': colors['bg_color'],
            'font_color': colors['font_color'],
            'border': 1,
            'align': 'center'
        })

    def _apply_sheet_formatting(self, worksheet, matrix_data, plans, carriers=None):
        num_plans = len(plans)
        last_col = num_plans * self.COLS_PER_PLAN

        if carriers is None:
            carriers = [''] * num_plans

        worksheet.set_column(0, 0, 35)
        for i in range(num_plans):
            start_col = 1 + i * self.COLS_PER_PLAN
            worksheet.set_column(start_col, start_col + self.COLS_PER_PLAN - 1, 18)
        worksheet.freeze_panes(1, 1)

        idx_map = {}
        for r_idx, row in enumerate(matrix_data):
            idx_map[row[0]] = r_idx + 2

        worksheet.write(0, 0, 'Plan Details', self.header_fmt_left)
        for i, plan_name in enumerate(plans):
            col_start = 1 + i * self.COLS_PER_PLAN
            col_end = col_start + self.COLS_PER_PLAN - 1
            header_fmt = self._create_carrier_header_format(carriers[i])
            worksheet.merge_range(0, col_start, 0, col_end, plan_name, header_fmt)

        for r_idx, row in enumerate(matrix_data):
            row_label = row[0]
            excel_row = r_idx + 1

            is_section = all(x == '' for x in row[1:])
            is_no_color = row_label in self.NO_COLOR_ROWS

            if is_section and not is_no_color:
                fmt_left = self.section_fmt_left
                fmt_center = self.section_fmt_center
            elif row_label in self.PERCENT_ROWS:
                fmt_left = self.percent_fmt_left
                fmt_center = self.percent_fmt_center
            elif row_label in self.CURRENCY_ROWS:
                fmt_left = self.currency_fmt_left
                fmt_center = self.currency_fmt_center
            else:
                fmt_left = self.cell_fmt_left
                fmt_center = self.cell_fmt_center

            worksheet.write(excel_row, 0, row_label, fmt_left)

            for plan_i in range(num_plans):
                col_start = 1 + plan_i * self.COLS_PER_PLAN
                col_end = col_start + self.COLS_PER_PLAN - 1
                col_letter = xl_col_to_name(col_start)
                val = row[plan_i + 1] if plan_i + 1 < len(row) else ''

                if row_label == 'Monthly Premium Total':
                    try:
                        r_ee = idx_map['Employee Only']
                        r_fam = idx_map['Family']
                        c_ee = idx_map['Count: Employee Only']
                        c_fam = idx_map['Count: Family']
                        formula = f"=SUMPRODUCT({col_letter}{r_ee}:{col_letter}{r_fam},{col_letter}{c_ee}:{col_letter}{c_fam})"
                        worksheet.merge_range(excel_row, col_start, excel_row, col_end, '', self.currency_fmt_center)
                        worksheet.write_formula(excel_row, col_start, formula, self.currency_fmt_center)
                        continue
                    except KeyError:
                        pass

                elif row_label == 'Monthly Premium Difference':
                    try:
                        r_total = idx_map['Monthly Premium Total']
                        next_col_letter = xl_col_to_name(col_start + 1)
                        formula = f"={next_col_letter}{r_total}-{col_letter}{r_total}"
                        worksheet.merge_range(excel_row, col_start, excel_row, col_end, '', self.currency_fmt_center)
                        worksheet.write_formula(excel_row, col_start, formula, self.currency_fmt_center)
                        continue
                    except KeyError:
                        pass

                elif row_label == '% Difference':
                    try:
                        r_total = idx_map['Monthly Premium Total']
                        next_col_letter = xl_col_to_name(col_start + 1)
                        formula = f"=({next_col_letter}{r_total}-{col_letter}{r_total})/{col_letter}{r_total}"
                        worksheet.merge_range(excel_row, col_start, excel_row, col_end, '', self.percent_fmt_center)
                        worksheet.write_formula(excel_row, col_start, formula, self.percent_fmt_center)
                        continue
                    except KeyError:
                        pass

                if is_section:
                    worksheet.merge_range(excel_row, col_start, excel_row, col_end, '', fmt_center)
                else:
                    worksheet.merge_range(excel_row, col_start, excel_row, col_end, val, fmt_center)

        merged_char_width = 18 * self.COLS_PER_PLAN
        for r_idx, row in enumerate(matrix_data):
            excel_row = r_idx + 1
            max_lines = 1
            for val in row:
                text = str(val) if val else ''
                if text:
                    lines = max(1, -(-len(text) // merged_char_width))
                    max_lines = max(max_lines, lines)
            if max_lines > 1:
                worksheet.set_row(excel_row, max_lines * 15)

        last_data_row = len(matrix_data)
        last_col = num_plans * self.COLS_PER_PLAN

        footer_row_1 = last_data_row + 1
        footer_row_2 = last_data_row + 2
        footer_row_3 = last_data_row + 4

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


class ExcelReportGenerator(BaseExcelGenerator):
    """
    Generates the Master Template Excel with per-carrier/network tabs.
    """

    def generate(self, df: pd.DataFrame) -> io.BytesIO:
        output = io.BytesIO()
        processed_df = self._preprocess_data(df)

        carriers = processed_df['carrier'].unique()
        network_types = sorted(processed_df['network_type'].unique())

        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            self.workbook = writer.book
            self._init_styles()

            if 'HealthyNY' in network_types:
                self._create_combined_healthyny_sheet(processed_df)

            for carrier in carriers:
                for network in network_types:
                    if network == 'HealthyNY':
                        continue
                    self._create_sheet_for_network(processed_df, carrier, network)

        output.seek(0)
        return output

    def _create_combined_healthyny_sheet(self, df):
        subset = df[df['network_type'] == 'HealthyNY']
        if subset.empty:
            return

        plan_headers = []
        carriers = []
        for _, row in subset.iterrows():
            carrier = row['carrier']
            plan_name = row['plan_name']
            plan_headers.append(f"{carrier}\n{plan_name}")
            carriers.append(carrier)

        matrix_data = []
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
        self._apply_sheet_formatting(worksheet, matrix_data, plan_headers, carriers)

    def _create_sheet_for_network(self, df, carrier, network):
        subset = df[(df['carrier'] == carrier) & (df['network_type'] == network)]
        if subset.empty: return

        plans = subset['plan_name'].tolist()
        carriers = [carrier] * len(plans)
        matrix_data = []

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
        self._apply_sheet_formatting(worksheet, matrix_data, plans, carriers)
