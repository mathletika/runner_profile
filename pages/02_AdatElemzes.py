import math
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# ====== Segédfüggvények ======
def parse_time_to_seconds(time_str: str):
    """Idő string → másodperc (float)."""
    if not time_str or str(time_str).strip() == "":
        return None
    t = str(time_str).replace(",", ".").strip()
    parts = t.split(":")
    if len(parts) == 3:
        h, m, s = parts
    elif len(parts) == 2:
        h, m, s = 0, *parts
    else:
        h, m, s = 0, 0, parts[0]
    try:
        return int(h) * 3600 + int(m) * 60 + float(s)
    except Exception:
        return None


def pontkereso(wa_df: pd.DataFrame, gender: str, discipline: str, input_time: str):
    """
    Megkeresi a WA táblában a megadott nem + versenyszám kombinációhoz tartozó
    legközelebbi, de lassabb vagy egyenlő időt, és visszaadja annak pontszámát.
    """
    if wa_df is None or wa_df.empty:
        return None

    input_sec = parse_time_to_seconds(input_time)
    if input_sec is None:
        return None

    sub = wa_df[(wa_df["gender"] == gender) & (wa_df["discipline"] == discipline)].copy()
    if sub.empty:
        return None

    sub["time_seconds"] = sub["result"].apply(parse_time_to_seconds)
    sub = sub[sub["time_seconds"] >= input_sec]  # csak lassabb vagy egyenlő idők

    if sub.empty:
        return None

    # legközelebbi lassabb vagy egyenlő
    closest = sub.sort_values("time_seconds").iloc[0]
    return int(closest["score"])


def calc_cs_cp(df: pd.DataFrame):
    """
    Kritikus sebesség (CS) és D′ számítása.
    d = CS * t + D′
    """
    df = df.dropna(subset=["dist_m","sec"])
    if len(df) < 2:
        return None, None

    if len(df) == 2:
        d1, t1 = df.iloc[0]["dist_m"], df.iloc[0]["sec"]
        d2, t2 = df.iloc[1]["dist_m"], df.iloc[1]["sec"]
        if abs(t2 - t1) < 1e-6:
            return None, None
        cs = (d2 - d1) / (t2 - t1)
        dprime = (d1 * t2 - d2 * t1) / (t2 - t1)
        return (cs if cs > 0 else None), (dprime if dprime > 0 else None)

    # Több pont → OLS regresszió
    x = df["sec"].values
    y = df["dist_m"].values
    n = len(x)
    sx, sy = x.sum(), y.sum()
    sxx, sxy = (x**2).sum(), (x*y).sum()
    denom = (n * sxx - sx**2)
    if abs(denom) < 1e-9:
        return None, None
    a = (n * sxy - sx * sy) / denom
    b = (sy - a * sx) / n
    cs = a
    dprime = b
    if cs is None or cs <= 0:
        return None, None
    if dprime is not None and dprime <= 0:
        dprime = None
    return cs, dprime


def pace_from_speed(cs_mps: float):
    """m/s → min/km string."""
    if cs_mps is None or cs_mps <= 0:
        return ""
    sec_per_km = 1000.0 / cs_mps
    m = int(sec_per_km // 60)
    s = int(round(sec_per_km - 60*m))
    return f"{m}:{s:02d} min/km"


# ====== Oldal beállítás ======
st.set_page_config(page_title="Runner Profile – AdatElemzés", page_icon="📊", layout="wide")
st.title("📊 Runner Profile – AdatElemzés")

# ====== WA score tábla betöltése ======
if "wa_scores_df" not in st.session_state:
    try:
        st.session_state.wa_scores_df = pd.read_csv("wa_score_merged_standardized.csv")
    except Exception:
        st.session_state.wa_scores_df = None

wa_df = st.session_state.wa_scores_df

# ====== IDŐK tábla ellenőrzés ======
if "idok" not in st.session_state or st.session_state.idok.empty:
    st.warning("Nincs adat az `idok` táblában. Először tölts fel eredményeket az Adatbetöltés oldalon.")
    st.stop()

idok = st.session_state.idok.copy()

# Származtatott oszlopok
DIST_TO_METERS = {
    "50 Metres": 50, "55 Metres": 55, "60 Metres": 60, "100 Metres": 100,
    "200 Metres": 200, "200 Metres Short Track": 200, "300 Metres": 300,
    "300 Metres Short Track": 300, "400 Metres": 400, "400 Metres Short Track": 400,
    "500 Metres": 500, "500 Metres Short Track": 500, "600 Metres": 600,
    "600 Metres Short Track": 600, "800 Metres": 800, "800 Metres Short Track": 800,
    "1000 Metres": 1000, "1000 Metres Short Track": 1000, "1500 Metres": 1500,
    "1500 Metres Short Track": 1500, "Mile": 1609.34, "Mile Short Track": 1609.34,
    "2000 Metres": 2000, "2000 Metres Short Track": 2000, "3000 Metres": 3000,
    "3000 Metres Short Track": 3000, "2 Miles": 3218.68, "2 Miles Short Track": 3218.68,
    "5000 Metres": 5000, "5000 Metres Short Track": 5000, "10000 Metres": 10000,
    "5 Kilometres Road": 5000, "10 Kilometres Road": 10000, "10 Miles Road": 16093.4,
    "15 Kilometres Road": 15000, "Half Marathon": 21097.5, "Marathon": 42195
}
idok["sec"] = idok["Idő"].apply(parse_time_to_seconds)
idok["dist_m"] = idok["Versenyszám"].map(DIST_TO_METERS)

# ====== Tabs ======
tab1, tab2, tab3 = st.tabs(["⚡ Kritikus Sebesség", "📈 Riegel exponens", "🏅 WA Score"])

# --- Tab1: Kritikus Sebesség ---
with tab1:
    st.subheader("Kritikus Sebesség (CS) elemzés")
    valid = idok.dropna(subset=["sec","dist_m"])
    valid = valid[(valid["sec"] > 0) & (valid["dist_m"] > 0)]

    if len(valid) < 2:
        st.info("Adj meg legalább két eredményt a CP számításhoz.")
    else:
        cs, dprime = calc_cs_cp(valid)
        if cs is None:
            st.warning("Nem sikerült kritikus sebességet számolni.")
        else:
            st.success(f"Kritikus sebesség (CS): **{cs:.3f} m/s** | Kritikus tempó: {pace_from_speed(cs)}")
            if dprime:
                st.caption(f"D′ (anaerob kapacitás): ~{dprime:.0f} m")

            # Ábra
            fig, ax = plt.subplots()
            ax.scatter(valid["sec"], valid["dist_m"], label="Eredmények", color="blue")
            if dprime is not None:
                x_line = valid["sec"].values
                y_line = cs * x_line + dprime
                ax.plot(x_line, y_line, color="red", label="Illesztett modell")
            ax.set_xlabel("Idő (s)")
            ax.set_ylabel("Távolság (m)")
            ax.legend()
            st.pyplot(fig)

# --- Tab2: Riegel exponens ---
with tab2:
    st.subheader("Riegel exponens elemzés")
    st.info("Itt lesz majd a Riegel exponens számítása és vizualizációja.")

# --- Tab3: WA Score ---
with tab3:
    st.subheader("WA pontszámítás")
    if wa_df is not None:
        scores = []
        for _, row in idok.iterrows():
            score = pontkereso(
                wa_df=wa_df,
                gender=row.get("Gender", "Man"),
                discipline=row.get("Versenyszám", ""),
                input_time=row.get("Idő", "")
            )
            scores.append(score)
        idok["Score"] = scores
    else:
        idok["Score"] = None

    st.dataframe(idok, use_container_width=True, hide_index=True)

    if idok["Score"].notna().any():
        best = idok.dropna(subset=["Score"]).sort_values("Score", ascending=False).iloc[0]
        st.success(f"Legjobb WA pontszám: **{int(best['Score'])}** "
                   f"({best['Versenyszám']} – {best['Idő']})")
