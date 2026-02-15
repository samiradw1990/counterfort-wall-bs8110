from fpdf import FPDF
import tempfile
import calculations as calc

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Counterfort Retaining Wall Design (BS 8110)', 0, 1, 'C')
        self.ln(5)

    def chapter_title(self, label):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 6, f'{label}', 0, 1, 'L', 1)
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 5, body)
        self.ln()

def generate_pdf_report(inputs, stability_results_map: dict, reinf_res):
    pdf = PDFReport()
    pdf.add_page()
    
    pdf.chapter_title("1. Design Inputs & Assumptions")
    input_text = (
        f"Dimensions:\n"
        f"  H: {inputs.H} m, B: {inputs.B} m\n"
        f"  Toe: {inputs.toe} m, Heel: {inputs.heel} m, t_base: {inputs.t_base} m\n"
        f"  Stem: {inputs.t_stem_top}m (top) - {inputs.t_stem_bottom}m (bot)\n"
        f"  Counterforts: Spacing {inputs.s_cf}m, Thick {inputs.t_cf}m\n"
        f"  Shear Key: Depth {inputs.d_key}m, Width {inputs.w_key}m\n\n"
        f"Properties:\n"
        f"  Concrete: {inputs.gamma_c} kN/m3, Soil: {inputs.gamma_soil} kN/m3, Water: {inputs.gamma_w} kN/m3\n"
        f"  Phi: {inputs.phi_soil} deg (Rankine Ka used)\n"
        f"  Surcharge: {inputs.surcharge} kPa\n"
        f"  Uplift Method: {'Full Hydrostatic (Conservative)' if inputs.uplift_full_base else 'Triangular'}\n"
    )
    pdf.chapter_body(input_text)
    
    pdf.chapter_title("2. Stability Analysis Summary")
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(30, 7, "Load Case", 1)
    pdf.cell(25, 7, "FS Slide", 1)
    pdf.cell(25, 7, "FS OT", 1)
    pdf.cell(30, 7, "Bear(kPa)", 1)
    pdf.cell(25, 7, "Ecc(m)", 1)
    pdf.cell(40, 7, "Status", 1)
    pdf.ln()
    
    pdf.set_font('Arial', '', 10)
    for name, res in stability_results_map.items():
        pdf.cell(30, 7, name, 1)
        pdf.cell(25, 7, f"{res.fs_slide:.2f}", 1)
        pdf.cell(25, 7, f"{res.fs_ot:.2f}", 1)
        pdf.cell(30, 7, f"{res.q_max:.1f} / {res.q_min:.1f}", 1)
        pdf.cell(25, 7, f"{res.eccentricity:.3f}", 1)
        status_short = "PASS" if "PASS" in res.status else "FAIL"
        pdf.cell(40, 7, status_short, 1)
        pdf.ln()
    
    pdf.ln(5)
    pdf.chapter_body("Note: Sliding FOS Target >= 1.5, OT FOS Target >= 2.0. Eccentricity Check B/6.")
    
    res = stability_results_map.get("LC-B", list(stability_results_map.values())[0])
    pdf.chapter_title(f"3. Detailed Breakdown ({res.case_name})")
    
    detail_text = (
        f"Forces per meter run:\n"
        f"  Sum V (Effective): {res.sum_V:.2f} kN\n"
        f"  Sum H (Driving): {res.sum_H:.2f} kN\n"
        f"  Uplift Force: {res.uplift:.2f} kN\n"
        f"  Resisting Moment: {res.res_mom:.2f} kNm\n"
        f"  Overturning Moment: {res.ot_mom:.2f} kNm (Inc Uplift if applicable)\n"
    )
    pdf.chapter_body(detail_text)
    
    pdf.chapter_title("4. Reinforcement Design (BS 8110)")
    
    stem = reinf_res['Stem']
    heel = reinf_res['Heel']
    toe = reinf_res['Toe']
    
    reinf_text = (
        f"Stem Panel (Span {inputs.s_cf}m {'Continuous' if inputs.stem_continuous else 'Simple'}):\n"
        f"  M_uls: {stem['M_uls']:.1f} kNm/m\n"
        f"  As_req: {stem['As_req']:.1f} mm2\n"
        f"  Prov: {stem['Bar']}\n\n"
        f"Heel (Cantilever):\n"
        f"  M_uls: {heel['M_uls']:.1f} kNm/m\n"
        f"  As_req: {heel['As_req']:.1f} mm2\n"
        f"  Prov: {heel['Bar']}\n\n"
        f"Toe (Cantilever):\n"
        f"  M_uls: {toe['M_uls']:.1f} kNm/m\n"
        f"  As_req: {toe['As_req']:.1f} mm2\n"
        f"  Prov: {toe['Bar']}\n"
    )
    pdf.chapter_body(reinf_text)

    outfile = tempfile.mktemp(suffix=".pdf")
    pdf.output(outfile, 'F')
    return outfile
