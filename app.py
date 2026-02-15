import streamlit as st
import pandas as pd
import calculations as calc
import visualization as viz
import reporting
import os

st.set_page_config(layout="wide", page_title="Counterfort Retaining Wall (BS 8110)")

st.title("Counterfort Retaining Wall Design")
st.markdown("BS 8110 Standards | Sri Lanka Defaults")

# --- Tabs ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Inputs", 
    "Loads & Stability", 
    "Batch Results", 
    "Reinforcement", 
    "3D Sketch", 
    "Report"
])

# --- Tab 1: Inputs ---
with tab1:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Geometry")
        H = st.number_input("Total Height H (m)", value=6.0, step=0.1)
        B = st.number_input("Base Width B (m)", value=4.0, step=0.1)
        toe = st.number_input("Toe Width (m)", value=1.0, step=0.1)
        heel = st.number_input("Heel Width (m)", value=2.5, step=0.1)
        t_base = st.number_input("Base Thickness (m)", value=0.5, step=0.05)
        
    with col2:
        st.subheader("Structure")
        t_stem_top = st.number_input("Stem Top (m)", value=0.3, step=0.05)
        t_stem_bottom = st.number_input("Stem Bottom (m)", value=0.5, step=0.05)
        s_cf = st.number_input("Counterfort Spacing (m)", value=2.5, step=0.1)
        t_cf = st.number_input("Counterfort Thickness (m)", value=0.4, step=0.05)
        d_key = st.number_input("Shear Key Depth (m)", value=0.5, step=0.1)
        w_key = st.number_input("Shear Key Width (m)", value=0.5, step=0.1)

    with col3:
        st.subheader("Materials & Anchors")
        phi_soil = st.number_input("Soil Phi (deg)", value=30.0)
        surcharge = st.number_input("Surcharge (kPa)", value=10.0)
        
        st.markdown("**Anchors**")
        anchor_cap = st.number_input("Capacity (kN/m)", value=0.0)
        anchor_inc = st.number_input("Inclination (deg)", value=15.0)
        
        st.markdown("**Load Settings**")
        crane_load = st.number_input("Crane Load (kN)", value=0.0)
        crane_dist = st.number_input("Crane Dist (m)", value=2.0)
        
    st.divider()
    with st.expander("Advanced / Defaults (Sri Lanka)"):
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            gamma_w = st.number_input("Water Unit Wt", value=9.81)
            gamma_c = st.number_input("Conc Unit Wt", value=24.0)
            gamma_soil = st.number_input("Soil Gamma (Dry)", value=18.0)
            gamma_sat = st.number_input("Soil Gamma (Sat)", value=20.0)
            mu_rock = st.number_input("Friction mu", value=0.5)
        with col_d2:
            fy = st.number_input("Steel fy (MPa)", value=460.0)
            fcu = st.number_input("Conc fcu (MPa)", value=30.0)
            cover = st.number_input("Cover (mm)", value=50.0)

# --- Tab 2: Single Analysis ---
with tab2:
    st.subheader("Analysis Configuration")
    
    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        uplift_full = st.checkbox("Near-full Uplift (Conservative)", value=True, help="Assumes full hydrostatic uplift under entire base using max head.")
    with col_opt2:
        stem_cont = st.checkbox("Stem Continuous (wL^2/10)", value=False, help="Default is Simply Supported (wL^2/8). Check if continuous.")

    # Create Input Object 
    inputs = calc.WallInputs(
        H=H, B=B, toe=toe, heel=heel, t_base=t_base,
        t_stem_top=t_stem_top, t_stem_bottom=t_stem_bottom,
        s_cf=s_cf, t_cf=t_cf, d_key=d_key, w_key=w_key, L_wall=20.0, 
        surcharge=surcharge, crane_load=crane_load, crane_dist=crane_dist,
        gamma_w=gamma_w, gamma_c=gamma_c, phi_soil=phi_soil,
        gamma_soil=gamma_soil, gamma_sat=gamma_sat, mu_rock=mu_rock,
        anchor_cap=anchor_cap, anchor_inclination=anchor_inc,
        fy=fy, fcu=fcu, cover=cover,
        uplift_full_base=uplift_full, stem_continuous=stem_cont
    )

    st.markdown("### Select Load Case")
    lc_sel = st.radio("Load Case", [
        "LC-A: Canal Full / Backfill Empty (Water Level 0)", 
        "LC-B: Both Full (Canal H / Backfill H)", 
        "LC-C: Canal Empty / Backfill Full (Canal 0 / Backfill H)"
    ])
    
    case_map = {
        "LC-A: Canal Full / Backfill Empty (Water Level 0)": "LC-A",
        "LC-B: Both Full (Canal H / Backfill H)": "LC-B",
        "LC-C: Canal Empty / Backfill Full (Canal 0 / Backfill H)": "LC-C"
    }
    
    run_case = case_map[lc_sel]
    res = calc.calculate_stability(inputs, run_case)
    
    # Display Results
    st.markdown(f"**Status: {res.status}**")
    
    col_r1, col_r2, col_r3, col_r4 = st.columns(4)
    col_r1.metric("FS Sliding", f"{res.fs_slide:.2f}", delta="> 1.5")
    col_r2.metric("FS Ot", f"{res.fs_ot:.2f}", delta="> 2.0")
    col_r3.metric("Max Bearing", f"{res.q_max:.1f} kPa")
    col_r4.metric("Eccentricity", f"{res.eccentricity:.3f} m")
    
    with st.expander("Detailed Forces"):
        st.write(f"Driving H: {res.sum_H:.2f} kN")
        st.write(f"Resisting H (Fric+Key+Anch): {res.fs_slide * res.sum_H:.2f} kN") # approximate back-calc approx logic
        st.write(f"Effective V: {res.sum_V:.2f} kN")
        st.write(f"Uplift: {res.uplift:.2f} kN")
        st.text(res.debug_info)

# --- Tab 3: Batch Results ---
with tab3:
    st.subheader("All Load Cases Summary")
    results_map = {}
    for c in ["LC-A", "LC-B", "LC-C"]:
        results_map[c] = calc.calculate_stability(inputs, c)
        
    # Table
    data = []
    for c, r in results_map.items():
        data.append({
            "Case": c,
            "FS Slide": f"{r.fs_slide:.2f}",
            "FS OT": f"{r.fs_ot:.2f}",
            "Qmax (kPa)": f"{r.q_max:.1f}",
            "Ecc (m)": f"{r.eccentricity:.3f}",
            "Status": r.status
        })
    st.table(pd.DataFrame(data))

# --- Tab 4: Reinforcement ---
with tab4:
    reinf = calc.calculate_reinforcement(inputs)
    st.subheader("Reinforcement Recommendations (BS 8110)")
    
    col_re1, col_re2 = st.columns(2)
    with col_re1:
        st.info("Stem Design (One-Way Slab)")
        st.write(f"Model: {'Continuous' if stem_cont else 'Simply Supported'}")
        st.write(f"Ult. Moment: {reinf['Stem']['M_uls']:.1f} kNm/m")
        st.write(f"Area Req: {reinf['Stem']['As_req']:.0f} mm2/m")
        st.success(f"Use: {reinf['Stem']['Bar']}")
        
    with col_re2:
        st.info("Base Design (Cantilevers)")
        st.write(f"Heel Moment: {reinf['Heel']['M_uls']:.1f} kNm/m")
        st.text(f"Heel Prov: {reinf['Heel']['Bar']}")
        st.write(f"Toe Moment: {reinf['Toe']['M_uls']:.1f} kNm/m")
        st.text(f"Toe Prov: {reinf['Toe']['Bar']}")

# --- Tab 5: 3D ---
with tab5:
    repeats = st.slider("Number of Bays to Show", 1, 10, 2)
    st.plotly_chart(viz.draw_wall_3d(inputs, repeats), use_container_width=True)

# --- Tab 6: Report ---
with tab6:
    if st.button("Download PDF Report"):
        batch_res = {c: calc.calculate_stability(inputs, c) for c in ["LC-A", "LC-B", "LC-C"]}
        pdf_file = reporting.generate_pdf_report(inputs, batch_res, reinf)
        with open(pdf_file, "rb") as f:
            st.download_button("Click to Save PDF", f, file_name="Design_Report.pdf")
