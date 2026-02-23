import io
from collections import defaultdict

import pandas as pd
from xlsxwriter.utility import xl_col_to_name

from src.extraction.excel_generator import BaseExcelGenerator


class ComparisonExcelGenerator(BaseExcelGenerator):
    """
    Generates the Marketing Renewal Comparison Excel.

    Output structure:
      - <Carrier> Current_Renewal  tab: enrolled plans with CURRENT | RENEWAL columns per plan
      - <Carrier> Opts              tab: alternative plans with cross-sheet Monthly Premium Difference
    """

    # Row definitions: (db_key, display_label, row_type)
    # row_type: 'section_rates' | 'rate' | 'total' | 'diff' | 'pct'
    #           | 'section' | 'benefit' | 'count'
    COMPARISON_ROWS = [
        ('SECTION_RATES',         'Monthly Rates',                                    'section_rates'),
        ('ee_only',               'Employee Only',                                    'rate'),
        ('ee_spouse',             'Employee + Spouse',                                'rate'),
        ('ee_children',           'Employee + Child(ren)',                            'rate'),
        ('family',                'Family',                                           'rate'),
        ('calc_total_premium',    'Monthly Premium Total',                            'total'),
        ('calc_premium_diff',     'Monthly Premium Difference',                       'diff'),
        ('calc_pct_diff',         '% Difference',                                     'pct'),
        ('SECTION_WELLNESS',      'Wellness Benefits',                                'section'),
        ('wellness_benefit',      'Health & Wellness Benefit',                        'benefit'),
        ('SECTION_IN_NETWORK',    'In-Network Benefits',                              'section'),
        ('deductible_display',    'Deductible (Employee/Family)',                     'benefit'),
        ('coinsurance_in',        'Coinsurance',                                      'benefit'),
        ('oop_display',           'Out of Pocket Maximum (Employee / Family)',        'benefit'),
        ('pcp_copay',             'PCP Copay',                                        'benefit'),
        ('specialist_copay',      'Specialist Copay',                                 'benefit'),
        ('inpatient_hospital',    'Inpatient Hospitalization',                        'benefit'),
        ('outpatient_facility',   'Outpatient Surgical',                              'benefit'),
        ('emergency_room',        'Emergency Room',                                   'benefit'),
        ('urgent_care',           'Urgent Care',                                      'benefit'),
        ('SECTION_OON',           'Out-of-Network Coverage',                         'section'),
        ('deductible_oon_display','Deductible (Employee/Family)',                     'benefit'),
        ('coinsurance_oon',       'Coinsurance',                                      'benefit'),
        ('oop_oon_display',       'Out of Pocket Maximum (Employee / Family)',        'benefit'),
        ('SECTION_RX',            'Prescription Coverage',                            'section'),
        ('rx_display',            'Generic / Preferred Brand / Non-Preferred Brand', 'benefit'),
        ('SECTION_OTHER',         'Other',                                            'section'),
        ('hsa_qualified',         'HSA Qualified',                                    'benefit'),
        ('creditable_coverage',   'Creditable Coverage',                              'benefit'),
        ('dependent_coverage',    'Dependent Coverage',                               'benefit'),
        ('SECTION_COUNTS',        'Member Counts',                                    'section'),
        ('count_ee',              'Employee Only',                                    'count'),
        ('count_sp',              'Employee + Spouse',                                'count'),
        ('count_ch',              'Employee + Child(ren)',                            'count'),
        ('count_fam',             'Family',                                           'count'),
    ]

    # Pre-computed Excel row indices (1-indexed) for formula use.
    # Row 0 (xlsxwriter) = Excel row 1 = plan name header.
    # Data rows start at xlsxwriter row 1 = Excel row 2.
    _EXCEL_ROWS = {}  # populated by _build_excel_row_map()

    @classmethod
    def _build_excel_row_map(cls):
        if cls._EXCEL_ROWS:
            return
        xls_row = 1  # xlsxwriter 0-indexed; Excel row = xls_row + 1
        for key, _label, _rtype in cls.COMPARISON_ROWS:
            cls._EXCEL_ROWS[key] = xls_row + 1  # store as Excel 1-indexed
            xls_row += 1

    def _val(self, row, key):
        """Safely get a value from a pandas row, normalising NaN → ''."""
        val = row.get(key)
        if val is None:
            return ''
        if isinstance(val, float) and pd.isna(val):
            return ''
        return val

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        current_df: pd.DataFrame,
        renewal_df: pd.DataFrame,
        options_df: pd.DataFrame,
    ) -> io.BytesIO:
        """
        Generate the Marketing Renewal Comparison Excel.

        Parameters
        ----------
        current_df  : enrolled plans with OLD (current year) pricing
        renewal_df  : renewal pricing for the SAME enrolled plans, matched by position
        options_df  : alternative plans for Opts tabs, grouped by carrier in output
        """
        self._build_excel_row_map()
        output = io.BytesIO()

        current_processed = (
            self._preprocess_data(current_df)
            if not current_df.empty
            else pd.DataFrame()
        )
        renewal_processed = (
            self._preprocess_data(renewal_df)
            if not renewal_df.empty
            else pd.DataFrame()
        )
        options_processed = (
            self._preprocess_data(options_df)
            if not options_df.empty
            else pd.DataFrame()
        )

        # Pair current and renewal by position, group by carrier
        n_pairs = min(len(current_processed), len(renewal_processed))
        pairs_by_carrier: dict[str, list] = defaultdict(list)
        for i in range(n_pairs):
            curr_row = current_processed.iloc[i]
            ren_row = renewal_processed.iloc[i]
            pairs_by_carrier[curr_row['carrier']].append((curr_row, ren_row))

        # Group option plans by carrier
        opts_by_carrier: dict[str, list] = defaultdict(list)
        if not options_processed.empty:
            for _, row in options_processed.iterrows():
                opts_by_carrier[row['carrier']].append(row)

        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            self.workbook = writer.book
            self._init_styles()
            self._init_comparison_styles()

            # 1. Current_Renewal tabs (one per enrolled carrier)
            current_renewal_sheet_names: dict[str, str] = {}
            for carrier, pairs in pairs_by_carrier.items():
                sheet_name = f"{carrier} Current_Renewal"[:31]
                current_renewal_sheet_names[carrier] = sheet_name
                ws = self.workbook.add_worksheet(sheet_name)
                self._build_current_renewal_sheet(ws, pairs, carrier)

            # Reference sheet for cross-sheet formulas in Opts tabs
            # (use the first enrolled carrier's sheet)
            ref_sheet = (
                next(iter(current_renewal_sheet_names.values()))
                if current_renewal_sheet_names
                else None
            )

            # 2. Opts tabs (one per carrier in options_df)
            for carrier, opt_plans in opts_by_carrier.items():
                sheet_name = f"{carrier} Opts"[:31]
                ws = self.workbook.add_worksheet(sheet_name)
                self._build_opts_sheet(ws, opt_plans, carrier, ref_sheet)

        output.seek(0)
        return output

    # ------------------------------------------------------------------
    # Style helpers
    # ------------------------------------------------------------------

    def _init_comparison_styles(self):
        """Additional formats needed for the comparison template."""
        # Sub-header for CURRENT / RENEWAL labels (light gray)
        self.subheader_fmt = self.workbook.add_format({
            'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter',
            'fg_color': '#D9D9D9',
        })
        # Bold variants for changed renewal cells
        self.bold_cell_fmt = self.workbook.add_format({
            'bold': True, 'text_wrap': True, 'valign': 'top',
            'border': 1, 'align': 'center',
        })
        self.bold_currency_fmt = self.workbook.add_format({
            'bold': True, 'text_wrap': True, 'valign': 'top',
            'border': 1, 'align': 'center', 'num_format': '$#,##0.00',
        })
        self.bold_percent_fmt = self.workbook.add_format({
            'bold': True, 'text_wrap': True, 'valign': 'top',
            'border': 1, 'align': 'center', 'num_format': '0.00%',
        })

    # ------------------------------------------------------------------
    # Current_Renewal tab
    # ------------------------------------------------------------------

    def _build_current_renewal_sheet(self, ws, plan_pairs, carrier):
        """
        Write the <Carrier> Current_Renewal tab.

        Each enrolled plan occupies two adjacent columns:
          left  = CURRENT (old pricing / current benefits)
          right = RENEWAL (new pricing / updated benefits)

        Benefit cells are merged when CURRENT == RENEWAL; otherwise both
        are shown, with the RENEWAL value in bold.
        """
        n_plans = len(plan_pairs)
        if n_plans == 0:
            return

        # Column widths
        ws.set_column(0, 0, 35)
        for i in range(n_plans):
            ws.set_column(1 + i * 2, 2 + i * 2, 18)
        ws.freeze_panes(1, 1)

        # ── Row 0: plan name headers (merged per pair) ────────────────
        ws.write(0, 0, '', self.header_fmt_left)
        for i, (curr_row, _) in enumerate(plan_pairs):
            col_s = 1 + i * 2
            hdr_fmt = self._create_carrier_header_format(carrier)
            ws.merge_range(0, col_s, 0, col_s + 1, curr_row['plan_name'], hdr_fmt)

        # Pre-compute Excel (1-indexed) row numbers we need for formulas
        ee_row    = self._EXCEL_ROWS['ee_only']
        fam_row   = self._EXCEL_ROWS['family']
        total_row = self._EXCEL_ROWS['calc_total_premium']
        c_ee_row  = self._EXCEL_ROWS['count_ee']
        c_fam_row = self._EXCEL_ROWS['count_fam']

        # ── Data rows ─────────────────────────────────────────────────
        for key, label, row_type in self.COMPARISON_ROWS:
            xls_row = self._EXCEL_ROWS[key] - 1  # xlsxwriter 0-indexed

            if row_type == 'section_rates':
                ws.write(xls_row, 0, label, self.section_fmt_left)
                for i in range(n_plans):
                    col_s = 1 + i * 2
                    ws.write(xls_row, col_s,     'CURRENT', self.subheader_fmt)
                    ws.write(xls_row, col_s + 1, 'RENEWAL', self.subheader_fmt)

            elif row_type == 'rate':
                ws.write(xls_row, 0, label, self.currency_fmt_left)
                for i, (curr_row, ren_row) in enumerate(plan_pairs):
                    col_s = 1 + i * 2
                    curr_val = self._val(curr_row, key)
                    ren_val  = self._val(ren_row, key)
                    same = (str(curr_val) == str(ren_val))
                    ren_fmt = self.currency_fmt_center if same else self.bold_currency_fmt

                    if isinstance(curr_val, (int, float)) and curr_val != '':
                        ws.write_number(xls_row, col_s, curr_val, self.currency_fmt_center)
                    else:
                        ws.write(xls_row, col_s, curr_val, self.currency_fmt_center)

                    if isinstance(ren_val, (int, float)) and ren_val != '':
                        ws.write_number(xls_row, col_s + 1, ren_val, ren_fmt)
                    else:
                        ws.write(xls_row, col_s + 1, ren_val, ren_fmt)

            elif row_type == 'total':
                ws.write(xls_row, 0, label, self.currency_fmt_left)
                for i in range(n_plans):
                    col_s   = 1 + i * 2
                    curr_let = xl_col_to_name(col_s)
                    ren_let  = xl_col_to_name(col_s + 1)
                    # CURRENT total uses current rates × current-column counts
                    curr_formula = (
                        f"=SUMPRODUCT({curr_let}{ee_row}:{curr_let}{fam_row},"
                        f"{curr_let}{c_ee_row}:{curr_let}{c_fam_row})"
                    )
                    # RENEWAL total uses renewal rates × SAME current-column counts
                    ren_formula = (
                        f"=SUMPRODUCT({ren_let}{ee_row}:{ren_let}{fam_row},"
                        f"{curr_let}{c_ee_row}:{curr_let}{c_fam_row})"
                    )
                    ws.write_formula(xls_row, col_s,     curr_formula, self.currency_fmt_center)
                    ws.write_formula(xls_row, col_s + 1, ren_formula,  self.currency_fmt_center)

            elif row_type == 'diff':
                ws.write(xls_row, 0, label, self.currency_fmt_left)
                for i in range(n_plans):
                    col_s    = 1 + i * 2
                    curr_let = xl_col_to_name(col_s)
                    ren_let  = xl_col_to_name(col_s + 1)
                    formula  = f"={ren_let}{total_row}-{curr_let}{total_row}"
                    ws.merge_range(xls_row, col_s, xls_row, col_s + 1, '', self.currency_fmt_center)
                    ws.write_formula(xls_row, col_s, formula, self.currency_fmt_center)

            elif row_type == 'pct':
                ws.write(xls_row, 0, label, self.percent_fmt_left)
                for i in range(n_plans):
                    col_s    = 1 + i * 2
                    curr_let = xl_col_to_name(col_s)
                    ren_let  = xl_col_to_name(col_s + 1)
                    formula  = f"=({ren_let}{total_row}-{curr_let}{total_row})/{curr_let}{total_row}"
                    ws.merge_range(xls_row, col_s, xls_row, col_s + 1, '', self.percent_fmt_center)
                    ws.write_formula(xls_row, col_s, formula, self.percent_fmt_center)

            elif row_type == 'section':
                ws.write(xls_row, 0, label, self.section_fmt_left)
                last_col = n_plans * 2
                ws.merge_range(xls_row, 1, xls_row, last_col, '', self.section_fmt_center)

            elif row_type == 'benefit':
                ws.write(xls_row, 0, label, self.cell_fmt_left)
                for i, (curr_row, ren_row) in enumerate(plan_pairs):
                    col_s    = 1 + i * 2
                    curr_val = str(self._val(curr_row, key))
                    ren_val  = str(self._val(ren_row, key))
                    if curr_val == ren_val or not ren_val:
                        # Same value → merge and display once
                        ws.merge_range(xls_row, col_s, xls_row, col_s + 1, curr_val, self.cell_fmt_center)
                    else:
                        # Changed → CURRENT plain, RENEWAL bold
                        ws.write(xls_row, col_s,     curr_val, self.cell_fmt_center)
                        ws.write(xls_row, col_s + 1, ren_val,  self.bold_cell_fmt)

            elif row_type == 'count':
                ws.write(xls_row, 0, label, self.cell_fmt_left)
                for i in range(n_plans):
                    col_s = 1 + i * 2
                    ws.merge_range(xls_row, col_s, xls_row, col_s + 1, '', self.cell_fmt_center)

        # ── Footer ────────────────────────────────────────────────────
        last_data_xls = self._EXCEL_ROWS['count_fam'] - 1  # xlsxwriter 0-indexed
        last_col = n_plans * 2
        ws.merge_range(
            last_data_xls + 2, 0, last_data_xls + 2, last_col,
            'Payroll Deductions should be verified by the Employer for Accuracy.',
            self.footer_red_fmt,
        )
        ws.merge_range(
            last_data_xls + 3, 0, last_data_xls + 3, last_col,
            '** If there is no enrollment in the plan; monthly premium differences are based off Employee only cost',
            self.footer_note_fmt,
        )

    # ------------------------------------------------------------------
    # Opts tab
    # ------------------------------------------------------------------

    def _build_opts_sheet(self, ws, opt_plans, carrier, ref_sheet_name):
        """
        Write a <Carrier> Opts tab.

        Each option plan occupies two merged columns (single value per plan).
        Monthly Premium Difference references the Current_Renewal tab via:
            =<col><total_row> - '<ref_sheet>'!<col><total_row>
        % Difference:
            =<col><total_row> / '<ref_sheet>'!<col><total_row> - 1
        """
        n_plans = len(opt_plans)
        if n_plans == 0:
            return

        ws.set_column(0, 0, 35)
        for i in range(n_plans):
            ws.set_column(1 + i * 2, 2 + i * 2, 18)
        ws.freeze_panes(1, 1)

        # ── Row 0: plan name headers ───────────────────────────────────
        ws.write(0, 0, '', self.header_fmt_left)
        for i, plan_row in enumerate(opt_plans):
            col_s   = 1 + i * 2
            hdr_fmt = self._create_carrier_header_format(carrier)
            ws.merge_range(0, col_s, 0, col_s + 1, plan_row['plan_name'], hdr_fmt)

        # Pre-compute formula row numbers
        ee_row    = self._EXCEL_ROWS['ee_only']
        fam_row   = self._EXCEL_ROWS['family']
        total_row = self._EXCEL_ROWS['calc_total_premium']
        c_ee_row  = self._EXCEL_ROWS['count_ee']
        c_fam_row = self._EXCEL_ROWS['count_fam']

        # ── Data rows ─────────────────────────────────────────────────
        for key, label, row_type in self.COMPARISON_ROWS:
            xls_row = self._EXCEL_ROWS[key] - 1  # xlsxwriter 0-indexed

            if row_type == 'section_rates':
                ws.write(xls_row, 0, label, self.section_fmt_left)
                last_col = n_plans * 2
                ws.merge_range(xls_row, 1, xls_row, last_col, '', self.section_fmt_center)

            elif row_type == 'rate':
                ws.write(xls_row, 0, label, self.currency_fmt_left)
                for i, plan_row in enumerate(opt_plans):
                    col_s = 1 + i * 2
                    val   = self._val(plan_row, key)
                    ws.merge_range(xls_row, col_s, xls_row, col_s + 1, '', self.currency_fmt_center)
                    if isinstance(val, (int, float)) and val != '':
                        ws.write_number(xls_row, col_s, val, self.currency_fmt_center)
                    else:
                        ws.write(xls_row, col_s, val, self.currency_fmt_center)

            elif row_type == 'total':
                ws.write(xls_row, 0, label, self.currency_fmt_left)
                for i in range(n_plans):
                    col_s   = 1 + i * 2
                    col_let = xl_col_to_name(col_s)
                    formula = (
                        f"=SUMPRODUCT({col_let}{ee_row}:{col_let}{fam_row},"
                        f"{col_let}{c_ee_row}:{col_let}{c_fam_row})"
                    )
                    ws.merge_range(xls_row, col_s, xls_row, col_s + 1, '', self.currency_fmt_center)
                    ws.write_formula(xls_row, col_s, formula, self.currency_fmt_center)

            elif row_type == 'diff':
                ws.write(xls_row, 0, label, self.currency_fmt_left)
                for i in range(n_plans):
                    col_s   = 1 + i * 2
                    col_let = xl_col_to_name(col_s)
                    if ref_sheet_name:
                        formula = (
                            f"={col_let}{total_row}"
                            f"-'{ref_sheet_name}'!{col_let}{total_row}"
                        )
                    else:
                        formula = f"={col_let}{total_row}"
                    ws.merge_range(xls_row, col_s, xls_row, col_s + 1, '', self.currency_fmt_center)
                    ws.write_formula(xls_row, col_s, formula, self.currency_fmt_center)

            elif row_type == 'pct':
                ws.write(xls_row, 0, label, self.percent_fmt_left)
                for i in range(n_plans):
                    col_s   = 1 + i * 2
                    col_let = xl_col_to_name(col_s)
                    if ref_sheet_name:
                        formula = (
                            f"={col_let}{total_row}"
                            f"/'{ref_sheet_name}'!{col_let}{total_row}-1"
                        )
                    else:
                        formula = "=0"
                    ws.merge_range(xls_row, col_s, xls_row, col_s + 1, '', self.percent_fmt_center)
                    ws.write_formula(xls_row, col_s, formula, self.percent_fmt_center)

            elif row_type == 'section':
                ws.write(xls_row, 0, label, self.section_fmt_left)
                last_col = n_plans * 2
                ws.merge_range(xls_row, 1, xls_row, last_col, '', self.section_fmt_center)

            elif row_type == 'benefit':
                ws.write(xls_row, 0, label, self.cell_fmt_left)
                for i, plan_row in enumerate(opt_plans):
                    col_s = 1 + i * 2
                    val   = str(self._val(plan_row, key))
                    ws.merge_range(xls_row, col_s, xls_row, col_s + 1, val, self.cell_fmt_center)

            elif row_type == 'count':
                ws.write(xls_row, 0, label, self.cell_fmt_left)
                for i in range(n_plans):
                    col_s = 1 + i * 2
                    ws.merge_range(xls_row, col_s, xls_row, col_s + 1, '', self.cell_fmt_center)

        # ── Footer ────────────────────────────────────────────────────
        last_data_xls = self._EXCEL_ROWS['count_fam'] - 1
        last_col = n_plans * 2
        ws.merge_range(
            last_data_xls + 2, 0, last_data_xls + 2, last_col,
            'Payroll Deductions should be verified by the Employer for Accuracy.',
            self.footer_red_fmt,
        )
        ws.merge_range(
            last_data_xls + 3, 0, last_data_xls + 3, last_col,
            '** If there is no enrollment in the plan; monthly premium differences are based off Employee only cost',
            self.footer_note_fmt,
        )