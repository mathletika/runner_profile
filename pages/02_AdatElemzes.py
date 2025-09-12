import math
import pandas as pd
import streamlit as st

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

def format_seconds(sec: float):
    """Másodperc → hh:mm:ss vagy mm:ss.ss formátum."""
    if sec is None or not math.isfinite(sec) or sec <= 0:
        return ""
    if sec >= 3600:
        h = int(sec // 3600)
        m = int((sec - 3600*h) // 60)
        s = int(round(sec - 3600*h - 60*m))
        return f"{h}:{m:02d}:{s:02d}"
    m = int(sec // 60)
    s = sec - 60*m
    return f"{m}:{s:05.2f}"

def pace_from_speed(cs_mps: float):
    """m/s → min/km string."""
    if cs_mps is None or cs_mps <= 0:
        return ""
    sec_per_km = 1000.0 / cs_mps
    m = int(sec_per_km // 60)
    s = int(round(sec_per_km - 60*m))
    return f"{m}:{s:02d} min/km"

def calc_cs_cp(df: pd.DataFrame):
    """Kritikus sebesség (CS) és D′ számítása."""
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
        return (cs if cs > 0 else None), (dprime if dprime and dprime > 0 else None)
    # Több pont → OLS regresszió
    x, y = df["sec"].values, df["dist_m"].values
    n = len(x)
    sx, sy = x.sum(), y.sum()
    sxx, sxy = (x**2).sum(), (x*y).sum()
    denom = (n * sxx - sx**2)
    if abs(denom) < 1e-9:
        return None, None
    a = (n * sxy - sx * sy) / denom
    b = (sy - a * sx) / n
    return (a if a > 0 else None), (b if b > 0 else None)

def riegel_kitevő_from_two(d1_m, t1_s, d2_m, t2_s):
    """Riegel kitevő k = ln(t2/t1) / ln(d2/d1)."""
    if min(d1_m, d2_m, t1_s, t2_s) <= 0 or d1_m == d2_m:
        return None
    return math.log(t2_s / t1_s) / math.log(d2_m / d1_m)

def riegel_predict_time(t_ref_s, d_ref_m, d_target_m, k):
    if min(t_ref_s, d_ref_m, d_target_m) <= 0 or k is None:
        return None
    return t_ref_s * (d_target_m / d_ref_m) ** k

def pontkereso(wa_df: pd.DataFrame, gender: str, discipline: str, input_time: str):
    """WA tábla → legközelebbi, de lassabb/equal idő pontszáma."""
    if wa_df is None or wa_df.empty:
        return None
    input_sec = parse_time_to_seconds(input_time)
    if input_sec is None:
        return None
    sub = wa_df[(wa_df["gender"] == gender) & (wa_df["discipline"] == discipline)].copy()
    if sub.empty: return None
    sub["time_seconds"] = sub["result"].apply(parse_time_to_seconds)
    sub = sub[sub["time_seconds"] >= input_sec]
    if sub.empty: return None
    closest = sub.sort_values("time_seconds").iloc[0]
    return int(closest["score"])

def time_for_score(wa_df: pd.DataFrame, gender: str, discipline: str, target_score: float):
    """Cél WA score → idő (string)."""
    if wa_df is None or wa_df.empty or target_score is None:
        return None
    sub = wa_df[(wa_df["gender"] == gender) & (wa_df["discipline"] == discipline)].copy()
    if sub.empty: return None
    sub = sub.sort_values("score", ascending=False)
    match = sub[sub["score"] <= target_score]
    row = match.iloc[0] if not match.empty else sub.iloc[-1]
    return row["result"]

# ====== Distancia mapping ======
DIST_TO_METERS = {"800 Metres": 800, "1500 Metres": 1500, "5000 Metres": 5000,
                  "10000 Metres": 10000, "Half Marathon": 21097.5, "Marathon": 42195}
EVENT_OPTIONS = list(DIST_TO_METERS.keys())

# ====== Oldal beállítás ======
st.set_page_config(page_title="AdatElemzés", page_icon="📊", layout="wide")
st.title("📊 AdatElemzés")

# ====== WA tábla betöltés ======
if "wa_scores_df" not in st.session_state:
    try:
        st.session_state.wa_scores_df = pd.read_csv("wa_score_merged_standardized.csv")
    except Exception:
        st.session_state.wa_scores_df = None
wa_df = st.session_state.wa_scores_df

# ====== IDŐK ======
if "idok" not in st.session_state or st.session_state.idok.empty:
    st.warning("Nincs adat az `idok` táblában.")
    st.stop()
idok = st.session_state.idok.copy()
idok["sec"] = idok["Idő"].apply(parse_time_to_seconds)
idok["dist_m"] = idok["Versenyszám"].map(DIST_TO_METERS)

# ====== Tabs ======
tab1, tab2, tab3 = st.tabs(["⚡ Kritikus Sebesség", "📈 Riegel exponens", "🏅 WA Score"])

# --- Kritikus Sebesség ---
with tab1:
    st.subheader("Kritikus Sebesség (CS)")
    st.info("✅ Javasolt a 3–20 perc közti eredményeket kiválasztani.")

    valid = idok.dropna(subset=["sec","dist_m"])
    valid = valid[(valid["sec"] > 0) & (valid["dist_m"] > 0)]

    picks = st.multiselect("Válassz ki legalább 2 eredményt:", 
                           [f"{r['Versenyszám']} – {r['Idő']}" for _, r in valid.iterrows()])
    use_df = valid[valid.apply(lambda r: f"{r['Versenyszám']} – {r['Idő']}" in picks, axis=1)]

    if len(use_df) >= 2:
        cs, dprime = calc_cs_cp(use_df)
        if cs:
            st.success(f"🔥 Kritikus tempó: {pace_from_speed(cs)}")
            st.caption(f"Kritikus sebesség (CS): {cs:.3f} m/s")
            if dprime: st.caption(f"D′ ≈ {dprime:.0f} m")
        else:
            st.warning("Nem sikerült számolni.")

# --- Riegel exponens ---
with tab2:
    st.subheader("Riegel exponens")
    valid = idok.dropna(subset=["sec","dist_m"])
    picks = st.multiselect("Válassz pontosan 2 eredményt:", 
                           [f"{r['Versenyszám']} – {r['Idő']}" for _, r in valid.iterrows()])
    if len(picks) == 2:
        use_df = valid[valid.apply(lambda r: f"{r['Versenyszám']} – {r['Idő']}" in picks, axis=1)]
        r1, r2 = use_df.iloc[0], use_df.iloc[1]
        k = riegel_kitevő_from_two(r1["dist_m"], r1["sec"], r2["dist_m"], r2["sec"])
        if k:
            st.success(f"Becsült Riegel-kitevő: {k:.3f}")
            target = st.selectbox("Cél versenyszám", EVENT_OPTIONS)
            d_target = DIST_TO_METERS.get(target)
            t_pred = riegel_predict_time(r1["sec"], r1["dist_m"], d_target, k)
            if t_pred:
                st.success(f"⏱️ Várható idő {target}: {format_seconds(t_pred)}")
                st.info(f"A becslés a képletből jön: t₂ = t₁ × (d₂/d₁)^k "
                        f"\n\nAlap: {r1['Versenyszám']} {r1['Idő']} → {target}, k = {k:.3f}")
        else:
            st.warning("Nem sikerült kitevőt számolni.")

# --- WA Score ---
with tab3:
    st.subheader("WA Score elemzés")

    if wa_df is not None:
        idok["Score"] = [pontkereso(wa_df, r["Gender"], r["Versenyszám"], r["Idő"]) for _, r in idok.iterrows()]
    show = idok.dropna(subset=["Score"]).copy().sort_values("Score", ascending=False)

    if not show.empty:
        st.markdown("### Eredmények WA pontszám szerint:")
        for _, row in show.iterrows():
            st.markdown(f"🏁 **{row['Versenyszám']}** – {row['Idő']} → {int(row['Score'])} pont")

        best, worst = show.iloc[0], show.iloc[-1]
        avg = int(round(show["Score"].mean()))
        st.markdown(f"\n🥇 **Legjobb:** {best['Versenyszám']} {best['Idő']} → {int(best['Score'])}")
        st.markdown(f"📊 **Átlagos:** {avg}")
        st.markdown(f"🐢 **Legalacsonyabb:** {worst['Versenyszám']} {worst['Idő']} → {int(worst['Score'])}")

        st.divider()
        st.subheader("WA kalkulátor")
        picks = st.multiselect("Válassz ki legfeljebb 3 eredményt:", 
                               [f"{r['Versenyszám']} – {r['Idő']}" for _, r in show.iterrows()])
        use_df = show[show.apply(lambda r: f"{r['Versenyszám']} – {r['Idő']}" in picks, axis=1)]
        if not use_df.empty:
            avg_score = int(round(use_df["Score"].mean()))
            st.success(f"Átlag WA Score (kiválasztottak): {avg_score}")
            target = st.selectbox("Cél versenyszám", EVENT_OPTIONS)
            pred_time = time_for_score(wa_df, st.session_state.gender, target, avg_score)
            if pred_time:
                st.info(f"{avg_score} pont → kb. {pred_time} ({target})")
