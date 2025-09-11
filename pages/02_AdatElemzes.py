import streamlit as st
import pandas as pd
import numpy as np
from typing import Optional, Tuple

st.set_page_config(
    page_title="Futó teljesítmény – Elemzés",
    page_icon="📊",
    layout="wide"
)

# ====== STÍLUS ======
st.markdown("""
<style>
.section-title{
  font-weight:700; font-size:1.2rem; margin: 12px 0 8px 0; color: #3d5361;
  border-left: 6px solid #3d5361; padding-left: 10px;
}
.card {
  background: #f6f7f9; border: 1px solid #dfe3e8; border-radius: 14px;
  padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
hr.soft{border: none; border-top: 1px solid #eceff1; margin: 1rem 0;}
</style>
""", unsafe_allow_html=True)

st.title("📊 Elemzés")

if "idok" not in st.session_state or st.session_state["idok"].empty:
    st.warning("Nincs adat a munkamenetben. Menj vissza az Adatbetöltés oldalra!")
    st.page_link("../streamlit_app.py", label="Vissza az Adatbetöltéshez →", icon="⬅️")
    st.stop()

df = st.session_state["idok"].copy()

# ====== SEGÉD: táv (m) és idő (s) becslés az 'Idő' és 'Versenyszám' alapján ======
EVENT_TO_METERS = {
    "50 Metres": 50, "55 Metres": 55, "60 Metres": 60, "100 Metres": 100,
    "200 Metres": 200, "300 Metres": 300, "400 Metres": 400,
    "500 Metres": 500, "600 Metres": 600, "800 Metres": 800,
    "1000 Metres": 1000, "1500 Metres": 1500, "Mile": 1609,
    "2000 Metres": 2000, "3000 Metres": 3000, "5000 Metres": 5000,
    "10000 Metres": 10000,
    "5 Kilometres Road": 5000, "10 Kilometres Road": 10000, "15 Kilometres Road": 15000,
    "20 Kilometres Road": 20000, "25 Kilometres Road": 25000, "30 Kilometres Road": 30000,
    "10 Miles": 16093, "Half Marathon": 21097, "Marathon": 42195,
    "100 Kilometres Road": 100000
}

def time_to_seconds(txt: str) -> Optional[float]:
    """
    Elfogad: ss.ss | mm:ss.ss | mm:ss | hh:mm:ss
    (A WA-projekthez illesztve.)
    """
    if not isinstance(txt, str) or not txt.strip():
        return None
    t = txt.strip()
    # hh:mm:ss
    if t.count(":") == 2:
        hh, mm, ss = t.split(":")
        try:
            return int(hh) * 3600 + int(mm) * 60 + float(ss)
        except:
            return None
    # mm:ss(.ss)
    if t.count(":") == 1:
        mm, ss = t.split(":")
        try:
            return int(mm) * 60 + float(ss)
        except:
            return None
    # ss(.ss)
    try:
        return float(t)
    except:
        return None

def add_distance_time_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["Táv_m"] = out["Versenyszám"].map(EVENT_TO_METERS)
    out["Idő_sec"] = out["Idő"].apply(time_to_seconds)
    return out

df_calc = add_distance_time_columns(df)

# ====== TABOK: Critical Speed | Átlagos lassulás | (Később) WA pontok ======
tab1, tab2, tab3 = st.tabs(["Critical Speed (CS)", "Átlagos lassulás", "WA pontszámok (később)"])

with tab1:
    st.markdown("#### Critical Speed (Monod–Scherrer)")
    st.caption("A CS-t a d = CS·t + D' lineáris modellből becsüljük (t idő [s], d távolság [m]).")

    # Alap: csak ésszerű tartomány (>=1500m) – csúszka a felhasználónak
    min_d, max_d = st.slider(
        "Felhasznált távok (méter) tartománya",
        min_value=400, max_value=42195, value=(1500, 10000), step=100
    )
    use = df_calc.dropna(subset=["Táv_m", "Idő_sec"])
    use = use[(use["Táv_m"] >= min_d) & (use["Táv_m"] <= max_d)]
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Adatok a regresszióhoz")
    st.dataframe(use[["Versenyszám", "Idő", "Táv_m", "Idő_sec"]], use_container_width=True, hide_index=True)

    if len(use) >= 2:
        # d = CS * t + D'  => slope = CS
        t = use["Idő_sec"].to_numpy()
        d = use["Táv_m"].to_numpy()
        A = np.vstack([t, np.ones_like(t)]).T
        # legkisebb négyzetek
        slope, intercept = np.linalg.lstsq(A, d, rcond=None)[0]
        CS = slope  # m/s
        Dprime = intercept  # m

        st.markdown("#### Eredmények")
        csa, csb, csc = st.columns(3)
        with csa:
            st.metric("Critical Speed (CS)", f"{CS:.2f} m/s", help="m/s")
        with csb:
            st.metric("CS (perc/km)", f"{(1000/CS)/60:.2f} p/km")
        with csc:
            st.metric("D′ (méter)", f"{Dprime:.0f} m")

        # Illesztés-vonal és pontok
        import altair as alt
        df_plot = use.copy()
        df_plot["Modell_d"] = CS * df_plot["Idő_sec"] + Dprime

        pts = alt.Chart(df_plot).mark_circle(size=80).encode(
            x=alt.X("Idő_sec:Q", title="Idő [s]"),
            y=alt.Y("Táv_m:Q", title="Távolság [m]"),
            tooltip=["Versenyszám","Idő","Táv_m","Idő_sec"]
        )
        line = alt.Chart(pd.DataFrame({
            "Idő_sec": np.linspace(df_plot["Idő_sec"].min()*0.9, df_plot["Idő_sec"].max()*1.1, 100)
        })).transform_calculate(
            Táv_m=f"{CS}*datum.Idő_sec+{Dprime}"
        ).mark_line().encode(
            x="Idő_sec:Q",
            y=alt.Y("Táv_m:Q", title="Távolság [m]")
        )
        st.altair_chart((pts + line).properties(height=360), use_container_width=True)
    else:
        st.info("Legalább 2 adatpont szükséges a CS becsléséhez.")

    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown("#### Átlagos lassulás (példa metrika)")
    st.caption("Egyszerű példa: a hosszabb távok fajlagos tempója (p/mp) hogyan romlik a rövidebbekhez képest.")
    st.markdown('<div class="card">', unsafe_allow_html=True)

    use = df_calc.dropna(subset=["Táv_m", "Idő_sec"]).copy()
    use["mp_per_km"] = (use["Idő_sec"] / (use["Táv_m"]/1000.0))
    use = use.sort_values("Táv_m")

    if len(use) >= 2:
        # baseline: a legrövidebb táv mp/km tempója
        base = use.iloc[0]["mp_per_km"]
        use["lassulás_mp_per_km"] = use["mp_per_km"] - base

        st.dataframe(
            use[["Versenyszám","Idő","Táv_m","mp_per_km","lassulás_mp_per_km"]],
            use_container_width=True, hide_index=True
        )

        import altair as alt
        chart = alt.Chart(use).mark_bar().encode(
            x=alt.X("Versenyszám:N", sort=None, title="Versenyszám"),
            y=alt.Y("lassulás_mp_per_km:Q", title="Lassulás [mp/km] a legrövidebb távhoz képest"),
            tooltip=["Versenyszám","Idő","Táv_m","mp_per_km","lassulás_mp_per_km"]
        ).properties(height=360)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("Legalább 2 adatpont szükséges a lassulás becsléséhez.")

    st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.markdown("#### WA pontszámok")
    st.info("Itt fogjuk később bekötni a „pontkereső” logikát és megjeleníteni a WA pontokat / eloszlásokat. "
            "Előbb véglegesítjük az adatbetöltés és számítások keretét.")
