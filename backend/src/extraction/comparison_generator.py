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
        ('family',                'Family',                                           'rate_last'),
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
        ('rx_generic',            'Generic',                                          'benefit'),
        ('rx_preferred_brand',    'Preferred Brand',                                  'benefit'),
        ('rx_non_preferred_brand','Non-Preferred Brand',                              'benefit'),
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
        member_counts: list[dict] | None = None,
    ) -> io.BytesIO:
        """
        Generate the Marketing Renewal Comparison Excel.

        Parameters
        ----------
        current_df    : enrolled plans with OLD (current year) pricing
        renewal_df    : renewal pricing for the SAME enrolled plans, matched by position
        options_df    : alternative plans for Opts tabs, grouped by carrier in output
        member_counts : list of dicts with keys count_ee, count_sp, count_ch, count_fam
                        matched by position to current/renewal pairs
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

        counts = member_counts or []

        # Pair current and renewal by position, group by carrier
        # Also track the original position index for member counts
        n_pairs = min(len(current_processed), len(renewal_processed))
        pairs_by_carrier: dict[str, list] = defaultdict(list)
        counts_by_carrier: dict[str, list] = defaultdict(list)
        for i in range(n_pairs):
            curr_row = current_processed.iloc[i]
            ren_row = renewal_processed.iloc[i]
            carrier = curr_row['carrier']
            pairs_by_carrier[carrier].append((curr_row, ren_row))
            counts_by_carrier[carrier].append(
                counts[i] if i < len(counts) else {"count_ee": 0, "count_sp": 0, "count_ch": 0, "count_fam": 0}
            )

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
                carrier_counts = counts_by_carrier.get(carrier, [])
                self._build_current_renewal_sheet(ws, pairs, carrier, carrier_counts)

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
                # Pass the enrolled counts from the matching carrier's Current_Renewal tab
                carrier_counts = counts_by_carrier.get(carrier, [])
                self._build_opts_sheet(ws, opt_plans, carrier, ref_sheet, carrier_counts)

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
        # Bold left-aligned for total/diff/pct row labels
        self.bold_label_fmt = self.workbook.add_format({
            'bold': True, 'text_wrap': True, 'valign': 'top',
            'border': 1, 'align': 'left',
        })
        self.bold_currency_left_fmt = self.workbook.add_format({
            'bold': True, 'text_wrap': True, 'valign': 'top',
            'border': 1, 'align': 'left', 'num_format': '$#,##0.00',
        })
        self.bold_percent_left_fmt = self.workbook.add_format({
            'bold': True, 'text_wrap': True, 'valign': 'top',
            'border': 1, 'align': 'left', 'num_format': '0.00%',
        })
        # Bottom-border format for the Family (last rate) row
        self.rate_last_fmt_center = self.workbook.add_format({
            'text_wrap': True, 'valign': 'top',
            'border': 1, 'align': 'center', 'num_format': '$#,##0.00',
            'bottom': 2,  # thick bottom border
        })
        self.rate_last_fmt_left = self.workbook.add_format({
            'text_wrap': True, 'valign': 'top',
            'border': 1, 'align': 'left', 'num_format': '$#,##0.00',
            'bottom': 2,
        })

    # ------------------------------------------------------------------
    # Value formatting helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _fmt_copay(val):
        """Format copay values: '$10' → '$10 Copay', preserve 'Deductible then...' etc."""
        if not val or val == '':
            return ''
        s = str(val).strip()
        s_lower = s.lower()
        # Skip formatting for non-copay values
        if any(kw in s_lower for kw in ['deductible', 'coinsurance', 'covered', 'none', 'n/a', '%']):
            return s
        # If it's a bare dollar amount like "$10" or "$40", add " Copay"
        if s.startswith('$') and 'copay' not in s_lower:
            return f"{s} Copay"
        return s

    @staticmethod
    def _fmt_rx_value(val):
        """Format Rx values: '$5' → '$5 Copay', '50%' → '50% Coinsurance'."""
        if not val or val == '':
            return ''
        s = str(val).strip()
        s_lower = s.lower()
        # Already has suffix
        if 'copay' in s_lower or 'coinsurance' in s_lower or 'covered' in s_lower:
            return s
        # Handle 'Deductible then $X' → 'Deductible then $X Copay'
        if s_lower.startswith('deductible then'):
            remainder = s[len('Deductible then '):].strip()
            if remainder.startswith('$') and '%' not in remainder:
                return f"Deductible then {remainder} Copay"
            elif '%' in remainder:
                return f"Deductible then {remainder} Coinsurance"
            return s
        # Bare dollar → Copay
        if s.startswith('$') and '%' not in s:
            return f"{s} Copay"
        # Bare percentage → Coinsurance
        if '%' in s:
            return f"{s} Coinsurance"
        return s

    @staticmethod
    def _fmt_deductible(val):
        """'None' → 'No Deductible'. Also catches 'None / None (...)' from preprocessor."""
        if not val or val == '':
            return ''
        s = str(val).strip()
        s_lower = s.lower()
        if s_lower in ('none', 'n/a', 'na', '$0', '$0/$0', 'no deductible'):
            return 'No Deductible'
        # Catch preprocessor output like "None / None (Embedded)"
        if s_lower.startswith('none / none'):
            return 'No Deductible'
        return s

    @staticmethod
    def _fmt_coinsurance(val):
        """'None' → 'No Coinsurance'."""
        if not val or val == '':
            return ''
        s = str(val).strip()
        if s.lower() in ('none', 'n/a', 'na', '0%', '0'):
            return 'No Coinsurance'
        return s

    # ------------------------------------------------------------------
    # Current_Renewal tab
    # ------------------------------------------------------------------

    def _build_current_renewal_sheet(self, ws, plan_pairs, carrier, member_counts=None):
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
        # Fields that need copay formatting
        COPAY_FIELDS = {'pcp_copay', 'specialist_copay', 'inpatient_hospital',
                        'outpatient_facility', 'emergency_room', 'urgent_care'}
        RX_FIELDS = {'rx_generic', 'rx_preferred_brand', 'rx_non_preferred_brand'}

        for key, label, row_type in self.COMPARISON_ROWS:
            xls_row = self._EXCEL_ROWS[key] - 1  # xlsxwriter 0-indexed

            if row_type == 'section_rates':
                ws.write(xls_row, 0, label, self.section_fmt_left)
                for i in range(n_plans):
                    col_s = 1 + i * 2
                    ws.write(xls_row, col_s,     'CURRENT', self.subheader_fmt)
                    ws.write(xls_row, col_s + 1, 'RENEWAL', self.subheader_fmt)

            elif row_type in ('rate', 'rate_last'):
                # Rates are NOT bolded — plain currency format
                # rate_last (Family) gets a thick bottom border
                if row_type == 'rate_last':
                    left_fmt = self.rate_last_fmt_left
                    center_fmt = self.rate_last_fmt_center
                else:
                    left_fmt = self.currency_fmt_left
                    center_fmt = self.currency_fmt_center

                ws.write(xls_row, 0, label, left_fmt)
                for i, (curr_row, ren_row) in enumerate(plan_pairs):
                    col_s = 1 + i * 2
                    curr_val = self._val(curr_row, key)
                    ren_val  = self._val(ren_row, key)

                    if isinstance(curr_val, (int, float)) and curr_val != '':
                        ws.write_number(xls_row, col_s, curr_val, center_fmt)
                    else:
                        ws.write(xls_row, col_s, curr_val, center_fmt)

                    if isinstance(ren_val, (int, float)) and ren_val != '':
                        ws.write_number(xls_row, col_s + 1, ren_val, center_fmt)
                    else:
                        ws.write(xls_row, col_s + 1, ren_val, center_fmt)

            elif row_type == 'total':
                # Monthly Premium Total — BOLD
                ws.write(xls_row, 0, label, self.bold_currency_left_fmt)
                for i in range(n_plans):
                    col_s   = 1 + i * 2
                    curr_let = xl_col_to_name(col_s)
                    ren_let  = xl_col_to_name(col_s + 1)
                    curr_formula = (
                        f"=SUMPRODUCT({curr_let}{ee_row}:{curr_let}{fam_row},"
                        f"{curr_let}{c_ee_row}:{curr_let}{c_fam_row})"
                    )
                    ren_formula = (
                        f"=SUMPRODUCT({ren_let}{ee_row}:{ren_let}{fam_row},"
                        f"{curr_let}{c_ee_row}:{curr_let}{c_fam_row})"
                    )
                    ws.write_formula(xls_row, col_s,     curr_formula, self.bold_currency_fmt)
                    ws.write_formula(xls_row, col_s + 1, ren_formula,  self.bold_currency_fmt)

            elif row_type == 'diff':
                # Monthly Premium Difference — BOLD
                ws.write(xls_row, 0, label, self.bold_currency_left_fmt)
                for i in range(n_plans):
                    col_s    = 1 + i * 2
                    curr_let = xl_col_to_name(col_s)
                    ren_let  = xl_col_to_name(col_s + 1)
                    formula  = f"={ren_let}{total_row}-{curr_let}{total_row}"
                    ws.merge_range(xls_row, col_s, xls_row, col_s + 1, '', self.bold_currency_fmt)
                    ws.write_formula(xls_row, col_s, formula, self.bold_currency_fmt)

            elif row_type == 'pct':
                # % Difference — BOLD
                ws.write(xls_row, 0, label, self.bold_percent_left_fmt)
                for i in range(n_plans):
                    col_s    = 1 + i * 2
                    curr_let = xl_col_to_name(col_s)
                    ren_let  = xl_col_to_name(col_s + 1)
                    formula  = f"=({ren_let}{total_row}-{curr_let}{total_row})/{curr_let}{total_row}"
                    ws.merge_range(xls_row, col_s, xls_row, col_s + 1, '', self.bold_percent_fmt)
                    ws.write_formula(xls_row, col_s, formula, self.bold_percent_fmt)

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

                    # Apply value formatting based on field type
                    if key == 'deductible_display' or key == 'deductible_oon_display':
                        curr_val = self._fmt_deductible(curr_val)
                        ren_val = self._fmt_deductible(ren_val)
                    elif key == 'coinsurance_in' or key == 'coinsurance_oon':
                        curr_val = self._fmt_coinsurance(curr_val)
                        ren_val = self._fmt_coinsurance(ren_val)
                    elif key in COPAY_FIELDS:
                        curr_val = self._fmt_copay(curr_val)
                        ren_val = self._fmt_copay(ren_val)
                    elif key in RX_FIELDS:
                        curr_val = self._fmt_rx_value(curr_val)
                        ren_val = self._fmt_rx_value(ren_val)

                    if curr_val == ren_val or not ren_val:
                        ws.merge_range(xls_row, col_s, xls_row, col_s + 1, curr_val, self.cell_fmt_center)
                    else:
                        ws.write(xls_row, col_s,     curr_val, self.cell_fmt_center)
                        ws.write(xls_row, col_s + 1, ren_val,  self.bold_cell_fmt)

            elif row_type == 'count':
                ws.write(xls_row, 0, label, self.cell_fmt_left)
                count_key_map = {
                    'count_ee': 'count_ee', 'count_sp': 'count_sp',
                    'count_ch': 'count_ch', 'count_fam': 'count_fam',
                }
                mc_key = count_key_map.get(key)
                for i in range(n_plans):
                    col_s = 1 + i * 2
                    val = ''
                    if member_counts and i < len(member_counts) and mc_key:
                        val = member_counts[i].get(mc_key, '')
                        if val == 0:
                            val = ''
                    # Write to CURRENT column; RENEWAL total formula uses CURRENT counts
                    ws.merge_range(xls_row, col_s, xls_row, col_s + 1, '', self.cell_fmt_center)
                    if val != '':
                        ws.write_number(xls_row, col_s, val, self.cell_fmt_center)

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

    def _build_opts_sheet(self, ws, opt_plans, carrier, ref_sheet_name, member_counts=None):
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
        COPAY_FIELDS = {'pcp_copay', 'specialist_copay', 'inpatient_hospital',
                        'outpatient_facility', 'emergency_room', 'urgent_care'}
        RX_FIELDS = {'rx_generic', 'rx_preferred_brand', 'rx_non_preferred_brand'}

        for key, label, row_type in self.COMPARISON_ROWS:
            xls_row = self._EXCEL_ROWS[key] - 1  # xlsxwriter 0-indexed

            if row_type == 'section_rates':
                ws.write(xls_row, 0, label, self.section_fmt_left)
                last_col = n_plans * 2
                ws.merge_range(xls_row, 1, xls_row, last_col, '', self.section_fmt_center)

            elif row_type in ('rate', 'rate_last'):
                # Rates NOT bolded; rate_last gets thick bottom border
                if row_type == 'rate_last':
                    left_fmt = self.rate_last_fmt_left
                    center_fmt = self.rate_last_fmt_center
                else:
                    left_fmt = self.currency_fmt_left
                    center_fmt = self.currency_fmt_center

                ws.write(xls_row, 0, label, left_fmt)
                for i, plan_row in enumerate(opt_plans):
                    col_s = 1 + i * 2
                    val   = self._val(plan_row, key)
                    ws.merge_range(xls_row, col_s, xls_row, col_s + 1, '', center_fmt)
                    if isinstance(val, (int, float)) and val != '':
                        ws.write_number(xls_row, col_s, val, center_fmt)
                    else:
                        ws.write(xls_row, col_s, val, center_fmt)

            elif row_type == 'total':
                # BOLD
                ws.write(xls_row, 0, label, self.bold_currency_left_fmt)
                for i in range(n_plans):
                    col_s   = 1 + i * 2
                    col_let = xl_col_to_name(col_s)
                    formula = (
                        f"=SUMPRODUCT({col_let}{ee_row}:{col_let}{fam_row},"
                        f"{col_let}{c_ee_row}:{col_let}{c_fam_row})"
                    )
                    ws.merge_range(xls_row, col_s, xls_row, col_s + 1, '', self.bold_currency_fmt)
                    ws.write_formula(xls_row, col_s, formula, self.bold_currency_fmt)

            elif row_type == 'diff':
                # BOLD
                ws.write(xls_row, 0, label, self.bold_currency_left_fmt)
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
                    ws.merge_range(xls_row, col_s, xls_row, col_s + 1, '', self.bold_currency_fmt)
                    ws.write_formula(xls_row, col_s, formula, self.bold_currency_fmt)

            elif row_type == 'pct':
                # BOLD
                ws.write(xls_row, 0, label, self.bold_percent_left_fmt)
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
                    ws.merge_range(xls_row, col_s, xls_row, col_s + 1, '', self.bold_percent_fmt)
                    ws.write_formula(xls_row, col_s, formula, self.bold_percent_fmt)

            elif row_type == 'section':
                ws.write(xls_row, 0, label, self.section_fmt_left)
                last_col = n_plans * 2
                ws.merge_range(xls_row, 1, xls_row, last_col, '', self.section_fmt_center)

            elif row_type == 'benefit':
                ws.write(xls_row, 0, label, self.cell_fmt_left)
                for i, plan_row in enumerate(opt_plans):
                    col_s = 1 + i * 2
                    val   = str(self._val(plan_row, key))

                    # Apply value formatting
                    if key == 'deductible_display' or key == 'deductible_oon_display':
                        val = self._fmt_deductible(val)
                    elif key == 'coinsurance_in' or key == 'coinsurance_oon':
                        val = self._fmt_coinsurance(val)
                    elif key in COPAY_FIELDS:
                        val = self._fmt_copay(val)
                    elif key in RX_FIELDS:
                        val = self._fmt_rx_value(val)

                    ws.merge_range(xls_row, col_s, xls_row, col_s + 1, val, self.cell_fmt_center)

            elif row_type == 'count':
                ws.write(xls_row, 0, label, self.cell_fmt_left)
                count_key_map = {
                    'count_ee': 'count_ee', 'count_sp': 'count_sp',
                    'count_ch': 'count_ch', 'count_fam': 'count_fam',
                }
                mc_key = count_key_map.get(key)
                for i in range(n_plans):
                    col_s = 1 + i * 2
                    val = ''
                    # Opts tabs use the same member counts as Current_Renewal
                    # matched by position (plan 0 = same counts as enrolled plan 0)
                    if member_counts and i < len(member_counts) and mc_key:
                        val = member_counts[i].get(mc_key, '')
                        if val == 0:
                            val = ''
                    ws.merge_range(xls_row, col_s, xls_row, col_s + 1, '', self.cell_fmt_center)
                    if val != '':
                        ws.write_number(xls_row, col_s, val, self.cell_fmt_center)

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
