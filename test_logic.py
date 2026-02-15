import calculations as calc
import visualization as viz
import reporting
import os

def test_logic():
    print("Testing Wall Calculation Logic...")
    
    inputs = calc.WallInputs(
        H=6.0, B=4.0, toe=1.0, heel=2.5, t_base=0.5,
        t_stem_top=0.3, t_stem_bottom=0.5,
        s_cf=2.5, t_cf=0.4, d_key=0.5, w_key=0.5, L_wall=20.0,
        surcharge=10.0, crane_load=0.0, crane_dist=2.0,
        gamma_w=9.81, gamma_c=24.0, phi_soil=30.0,
        gamma_soil=18.0, gamma_sat=20.0, mu_rock=0.5,
        anchor_cap=0.0, anchor_inclination=15.0,
        fy=460.0, fcu=30.0, cover=50.0,
        uplift_full_base=True, stem_continuous=False
    )
    
    cases = ["LC-A", "LC-B", "LC-C"]
    results = {}
    for c in cases:
        print(f"Running {c}...")
        res = calc.calculate_stability(inputs, c)
        results[c] = res
        print(f"  FS Slide: {res.fs_slide:.2f}")
        print(f"  FS OT: {res.fs_ot:.2f}")
        print(f"  Status: {res.status}")
        
    print("Running Reinforcement...")
    reinf = calc.calculate_reinforcement(inputs)
    print(f"  Stem Bar: {reinf['Stem']['Bar']}")
    
    print("Generating 3D Figure...")
    fig = viz.draw_wall_3d(inputs)
    print("  Figure generated.")

    print("Generating PDF...")
    pdf_path = reporting.generate_pdf_report(inputs, results, reinf)
    print(f"  PDF generated at {pdf_path}")
    
    print("All tests passed.")

if __name__ == "__main__":
    test_logic()
