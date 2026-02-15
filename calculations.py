import math
from dataclasses import dataclass
from typing import Dict, List, Tuple

@dataclass
class WallInputs:
    # Dimensions
    H: float
    B: float
    toe: float
    heel: float
    t_base: float
    t_stem_top: float
    t_stem_bottom: float
    s_cf: float
    t_cf: float
    d_key: float
    w_key: float
    L_wall: float

    # Loads and Factors
    surcharge: float
    crane_load: float
    crane_dist: float
    
    # Material Properties
    gamma_w: float = 9.81
    gamma_c: float = 24.0
    phi_soil: float = 30.0
    gamma_soil: float = 18.0
    gamma_sat: float = 20.0
    c_soil: float = 0.0
    mu_rock: float = 0.50
    
    # Anchors
    anchor_cap: float = 0.0 # kN/m
    anchor_inclination: float = 0.0 # degrees

    # Design
    fy: float = 460.0
    fcu: float = 30.0
    cover: float = 50.0
    
    # Toggles
    uplift_full_base: bool = True
    stem_continuous: bool = False # False = wL^2/8, True = wL^2/10

@dataclass
class StabilityResult:
    case_name: str
    sum_H: float
    sum_V: float
    uplift: float
    res_mom: float
    ot_mom: float
    m_res_net: float
    fs_slide: float
    fs_ot: float
    eccentricity: float
    q_max: float
    q_min: float
    status: str
    debug_info: str

def calculate_ka(phi: float) -> float:
    # Rankine
    # tan^2(45 - phi/2)
    return math.tan(math.radians(45 - phi/2.0))**2

def calculate_kp(phi: float) -> float:
    # Rankine Passive
    return math.tan(math.radians(45 + phi/2.0))**2

def calculate_stability(inp: WallInputs, case_name: str) -> StabilityResult:
    # --- 1. Load Case Definition ---
    # LC-A: Canal Full (H), Backfill Empty (0).
    # LC-B: Canal Full (H), Backfill Full (H).
    # LC-C: Canal Empty (0), Backfill Full (H).
    
    h_w_canal = 0.0
    h_w_backfill = 0.0
    
    if case_name == "LC-A":
        h_w_canal = inp.H
        h_w_backfill = 0.0
    elif case_name == "LC-B":
        h_w_canal = inp.H
        h_w_backfill = inp.H
    elif case_name == "LC-C":
        h_w_canal = 0.0
        h_w_backfill = inp.H
    else:
        h_w_canal = 0
        h_w_backfill = 0

    # Constants
    ka = calculate_ka(inp.phi_soil)
    kp = calculate_kp(inp.phi_soil)
    
    # --- 2. Vertical Forces (V) & Moments about TOE ---
    
    # A. Concrete Weights
    # Stem (Vertical Back Face assumption)
    stem_back_x = inp.toe + inp.t_stem_bottom
    h_stem = inp.H - inp.t_base
    
    # Visual Logic: Stem Top Thickness `t_t`, Bottom `t_b`.
    w_stem_rect = inp.t_stem_top * h_stem * inp.gamma_c
    x_stem_rect = stem_back_x - inp.t_stem_top / 2.0
    
    w_stem_tri = 0.5 * (inp.t_stem_bottom - inp.t_stem_top) * h_stem * inp.gamma_c
    x_stem_tri = stem_back_x - inp.t_stem_top - (inp.t_stem_bottom - inp.t_stem_top)/3.0
    
    # Base
    w_base = inp.B * inp.t_base * inp.gamma_c
    x_base = inp.B / 2.0
    
    # Key
    x_key = inp.toe + inp.t_stem_bottom / 2.0
    w_key = inp.d_key * inp.w_key * inp.gamma_c
    
    # Counterforts
    # Triangular (Stem Back to Heel End).
    area_cf = 0.5 * inp.heel * h_stem
    vol_cf_m = (area_cf * inp.t_cf) / inp.s_cf
    w_cf = vol_cf_m * inp.gamma_c
    x_cf = stem_back_x + inp.heel / 3.0
    
    # Sum Concrete
    W_conc = w_stem_rect + w_stem_tri + w_base + w_key + w_cf
    M_conc = (w_stem_rect * x_stem_rect) + (w_stem_tri * x_stem_tri) + \
             (w_base * x_base) + (w_key * x_key) + (w_cf * x_cf)
             
    # B. Soil Weight (Heel)
    h_w_local_bf = h_w_backfill - inp.t_base
    if h_w_local_bf < 0: h_w_local_bf = 0
    if h_w_local_bf > h_stem: h_w_local_bf = h_stem
    
    h_dry = h_stem - h_w_local_bf
    
    # Gross Soil (Assume No CF)
    w_soil_dry_gross = inp.heel * h_dry * inp.gamma_soil
    w_soil_sat_gross = inp.heel * h_w_local_bf * inp.gamma_sat
    
    # Displacement Correction
    h_total_soil = h_stem
    if h_total_soil > 0:
        avg_gamma_soil = (w_soil_dry_gross + w_soil_sat_gross) / (inp.heel * h_total_soil)
    else:
        avg_gamma_soil = inp.gamma_soil
        
    w_soil_displaced = vol_cf_m * avg_gamma_soil
    
    W_soil = w_soil_dry_gross + w_soil_sat_gross - w_soil_displaced
    x_soil = stem_back_x + inp.heel / 2.0
    M_soil = W_soil * x_soil
    
    # C. Surcharge (Vertical)
    w_sur = inp.surcharge * inp.heel
    M_sur = w_sur * x_soil
    
    # D. Crane Load
    W_crane = inp.crane_load
    x_crane = stem_back_x + inp.crane_dist
    M_crane = W_crane * x_crane if W_crane > 0 else 0
    
    # E. Anchors (Vertical Component)
    ang_rad = math.radians(inp.anchor_inclination)
    F_anchor_v = inp.anchor_cap * math.sin(ang_rad)
    F_anchor_h = inp.anchor_cap * math.cos(ang_rad)
    
    # --- 3. Uplift ---
    head_max = max(h_w_canal, h_w_backfill)
    
    if inp.uplift_full_base:
        # Rectangular distribution
        U = (inp.gamma_w * head_max) * inp.B
        x_U = inp.B / 2.0
    else:
        # Standard Triangular/Trap
        u1 = inp.gamma_w * h_w_canal
        u2 = inp.gamma_w * h_w_backfill
        U = 0.5 * (u1 + u2) * inp.B
        if (u1+u2) > 0:
            x_U = (inp.B/3.0) * (u1 + 2*u2)/(u1 + u2)
        else:
            x_U = 0.0
            
    M_uplift = U * x_U
    
    # Total Vertical
    sum_V = W_conc + W_soil + w_sur + W_crane + F_anchor_v
    sum_V_eff = sum_V - U
    
    # Resisting Moment about Toe
    M_resist_weights = M_conc + M_soil + M_sur + M_crane
    M_anchor = F_anchor_v * stem_back_x # Approximated at Stem Back
    M_resist_total = M_resist_weights + M_anchor
    
    # --- 4. Horizontal Forces (Driving & Resisting) ---
    
    # Driving:
    # 1. Earth Pressure (Backfill)
    h_dry_soil = inp.H - h_w_backfill
    if h_dry_soil < 0: h_dry_soil = 0
    if h_dry_soil > inp.H: h_dry_soil = inp.H
    h_wet_soil = h_w_backfill
    
    # Forces
    Pa_1 = 0.5 * ka * inp.gamma_soil * h_dry_soil**2
    y_1  = h_wet_soil + h_dry_soil/3.0
    
    q_transfer = ka * inp.gamma_soil * h_dry_soil
    Pa_2 = q_transfer * h_wet_soil
    y_2 = h_wet_soil / 2.0
    
    gamma_sub = inp.gamma_sat - inp.gamma_w
    Pa_3 = 0.5 * ka * gamma_sub * h_wet_soil**2
    y_3 = h_wet_soil / 3.0
    
    Pw_back = 0.5 * inp.gamma_w * h_wet_soil**2
    y_wb = h_wet_soil / 3.0
    
    Pa_sur = ka * inp.surcharge * inp.H
    y_sur = inp.H / 2.0
    
    sum_H_drive = Pa_1 + Pa_2 + Pa_3 + Pw_back + Pa_sur
    M_OT = (Pa_1 * y_1) + (Pa_2 * y_2) + (Pa_3 * y_3) + (Pw_back * y_wb) + (Pa_sur * y_sur)
    
    # Resisting:
    # 1. Water Pressure (Canal - Front)
    Pw_front = 0.5 * inp.gamma_w * h_w_canal**2
    y_wf = h_w_canal / 3.0
    M_water_resist = Pw_front * y_wf
    
    # 2. Friction
    if sum_V_eff < 0: sum_V_eff = 0
    F_friction = inp.mu_rock * sum_V_eff
    
    # 3. Shear Key Passive
    F_key = 0.0
    if inp.d_key > 0:
        sigma_v_top = (h_w_canal * inp.gamma_w) 
        F_key = (kp * sigma_v_top * inp.d_key) + (0.5 * kp * (inp.gamma_sat - inp.gamma_w) * inp.d_key**2)
        
    sum_H_resist_force = F_friction + F_key + F_anchor_h + Pw_front
    
    # Factors of Safety
    fs_slide = sum_H_resist_force / sum_H_drive if sum_H_drive > 0 else 99.0
    
    # Overturning
    fs_ot = (M_resist_total + M_water_resist) / (M_OT + M_uplift) if (M_OT + M_uplift) > 0 else 99.0
    
    # Bearing
    M_net = (M_resist_total + M_water_resist) - (M_OT + M_uplift)
    x_resultant = M_net / sum_V_eff if sum_V_eff > 0 else 0
    e = (inp.B / 2.0) - x_resultant
    
    q_avg = sum_V_eff / inp.B
    if abs(e) <= inp.B / 6.0:
        q_max = q_avg * (1 + 6*e/inp.B)
        q_min = q_avg * (1 - 6*e/inp.B)
    else:
        dist_a = x_resultant
        if dist_a > 0:
            q_max = (2 * sum_V_eff) / (3 * dist_a)
            q_min = 0.0
        else:
            q_max = 9999
            q_min = 0.0
            
    status = "PASS"
    if fs_slide < 1.5: status = "FAIL (Sliding)"
    if fs_ot < 2.0: status = "FAIL (Overturning)"
    if abs(e) > inp.B/6.0: status += " (Eccentricity > B/6)"
    
    debug = f"Pa1={Pa_1:.1f}, Pa2={Pa_2:.1f}, Pa3={Pa_3:.1f}, Pw_b={Pw_back:.1f}, Pw_f={Pw_front:.1f}\n"
    debug += f"Frique={F_friction:.1f}, Key={F_key:.1f}, AncH={F_anchor_h:.1f}\n"
    debug += f"Uplift={U:.1f}, M_U={M_uplift:.1f}, HeadMax={head_max:.1f}"

    return StabilityResult(
        case_name=case_name,
        sum_H=sum_H_drive,
        sum_V=sum_V_eff,
        uplift=U,
        res_mom=M_resist_total + M_water_resist,
        ot_mom=M_OT + M_uplift,
        m_res_net=M_net,
        fs_slide=fs_slide,
        fs_ot=fs_ot,
        eccentricity=e,
        q_max=q_max,
        q_min=q_min,
        status=status,
        debug_info=debug
    )

def calculate_reinforcement(inp: WallInputs) -> Dict:
    # BS 8110 Logic
    
    # 1. Stem
    ka = calculate_ka(inp.phi_soil)
    h_s = inp.H - inp.t_base
    
    # Pressure
    p_lat = (ka * (inp.gamma_sat - 9.81) * h_s) + (9.81 * h_s) + (ka * inp.surcharge)
    
    coeff = 0.10 if inp.stem_continuous else 0.125
    
    M_stem_sls = coeff * p_lat * (inp.s_cf**2)
    M_stem_uls = M_stem_sls * 1.4
    
    d = inp.t_stem_bottom * 1000 - inp.cover - 8
    if d <= 0: d = 100
    z = 0.95 * d
    As_req = (M_stem_uls * 1e6) / (0.95 * inp.fy * z)
    
    As_min = 0.0013 * 1000 * (inp.t_stem_bottom * 1000)
    As_final = max(As_req, As_min)
    
    bar_diam = suggest_bar(As_final)
    
    # 2. Heel
    w_heel = (inp.gamma_soil * h_s) + inp.surcharge + (inp.gamma_c * inp.t_base)
    M_heel_uls = 1.4 * (w_heel * (inp.heel**2) / 2.0)
    
    d_base = inp.t_base * 1000 - inp.cover - 10
    As_heel = (M_heel_uls * 1e6) / (0.95 * inp.fy * 0.95*d_base)
    As_heel_min = 0.0013 * 1000 * (inp.t_base * 1000)
    As_heel_final = max(As_heel, As_heel_min)
    
    # 3. Toe
    res_B = calculate_stability(inp, "LC-B")
    q_des = res_B.q_max 
    M_toe_uls = 1.4 * (q_des * (inp.toe**2) / 2.0)
    
    As_toe = (M_toe_uls * 1e6) / (0.95 * inp.fy * 0.95*d_base)
    As_toe_final = max(As_toe, As_heel_min)
    
    return {
        "Stem": {
            "M_uls": M_stem_uls,
            "As_req": As_final,
            "Bar": f"H{bar_diam} @ 150 (As={area_of(bar_diam, 150):.0f}) > {As_final:.0f}"
        },
        "Heel": {
            "M_uls": M_heel_uls,
            "As_req": As_heel_final,
            "Bar": f"H{suggest_bar(As_heel_final)} @ 150"
        },
        "Toe": {
            "M_uls": M_toe_uls,
            "As_req": As_toe_final,
            "Bar": f"H{suggest_bar(As_toe_final)} @ 150"
        }
    }

def suggest_bar(As):
    for d in [10, 12, 16, 20, 25, 32]:
        if area_of(d, 150) >= As:
            return d
    return 32

def area_of(d, s):
    return (math.pi * d**2 / 4.0) * (1000.0 / s)
