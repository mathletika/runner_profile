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

def format_seconds(sec: float):
    """Másodperc → hh:mm:ss vagy mm:ss.ss formázás (okos kerekítés)."""
    if sec is None or not math.isfinite(sec) or sec <= 0:
        return ""
    # ha 1 óránál több, hh:mm:ss
    if sec >= 3600:
        h = int(sec // 3600)
        m = int((sec - 3600*h) // 60)
        s = int(round(sec - 3600*h - 60*m))
        return f"{h}:{m:02d}:{s:02d}"
    # különben mm:ss.ss
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
    """
    Kritikus sebesség (CS) és D′ számítása.
    d = CS * t + D′  (OLS illesztés több pontnál, 2 pontnál egyszerű kétpontos megoldás)
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
        return (cs if cs > 0 else None), (dprime if dprime and dprime > 0 else None)

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

def riegel_kitevő_from_two(d1_m, t1_s, d2_m, t2_s):
    """Riegel-kitevő k becslése két eredményből: t2 = t1 * (d2/d1)^k → k = ln(t2/t1)/ln(d2/d1)."""
    if min(d1_m, d2_m, t1_s, t2_s) <= 0 or d1_m == d2_m:
        return None
    return math.log(t2_s / t1_s) / math.log(d2_m / d1_m)

def riegel_predict_time(t_ref_s, d_ref_m, d_target_m, k):
    """Riegel-időbecslés: t_target = t_ref * (d_target/d_ref)^k"""
    if min(t_ref_s, d_ref_m, d_target_m) <= 0 or k is None:
        return None
    return t_ref_s * (d_target_m / d_ref_m) ** k

def pontkereso(wa_df: pd.DataFrame, gender: str, discipline: str, input_time: str):
    """
    WA tábla: megadott nem + versenyszám + idő → legközelebbi, de lassabb vagy egyenlő idő pontszáma.
    """
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
    """
    WA tábla: cél pontszám → ennek megfelelő (vagy ahhoz legközelebb eső, alacsonyabb) idő string.
    """
    if wa_df is None or wa_df.empty or target_score is None:
        return None
    sub = wa_df[(wa_df["gender"] == gender) & (wa_df["discipline"] == discipline)].copy()
    if sub.empty: return None
    sub = sub.sort_values("score", ascending=False)
    # Keressük az elsőt, amelynek score <= target_score (pont vagy alacsonyabb)
    match = sub[sub["score"] <= target_score]
    if match.empty:
        # ha mindenki nagyobb, vegyük a legkisebb pontot (leglassabb időt)
        row = sub.iloc[-1]
    else:
        row = match.iloc[0]
    return row["result"]

# ====== Distancia mapping ======
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
EVENT_OPTIONS = list(DIST_TO_METERS.keys())

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
idok["sec"] = idok["Idő"].apply(parse_time_to_seconds)
idok["dist_m"] = idok["Versenyszám"].map(DIST_TO_METERS)

# ====== Kis kártyák a kiválasztáshoz ======
def render_result_selector(df: pd.DataFrame, key_prefix: str, max_select: int = None):
    """
    Visszaadja: kiválasztott indexek listája.
    Kis kártyás, checkboxos választó (4 oszlopban).
    """
    selected = []
    df = df.reset_index().rename(columns={"index": "ix"})
    for i in range(0, len(df), 4):
        cols = st.columns(4)
        for j in range(4):
            ridx = i + j
            if ridx >= len(df): break
            row = df.iloc[ridx]
            label = f"{row['Versenyszám']}\n{row['Idő']}"
            with cols[j].container(border=True):
                st.caption(label)
                checked = st.checkbox("Választ", key=f"{key_prefix}_{row['ix']}")
                if checked:
                    selected.append(int(row["ix"]))
    if max_select is not None and len(selected) > max_select:
        st.warning(f"Legfeljebb {max_select} eredményt jelölhetsz.")
        selected = selected[:max_select]
    return selected

# ====== Tabs ======
tab1, tab2, tab3 = st.tabs(["⚡ Kritikus Sebesség", "📈 Riegel exponens", "🏅 WA Score"])

# --- Tab1: Kritikus Sebesség ---
with tab1:
    st.subheader("Kritikus Sebesség (CS) elemzés")
    st.info("Javasolt a 3–20 perc közti eredményeket kiválasztani a megbízható illesztéshez.")

    valid = idok.dropna(subset=["sec","dist_m"])
    valid = valid[(valid["sec"] > 0) & (valid["dist_m"] > 0)]

    if valid.empty:
        st.info("Nincs elég érvényes adat.")
    else:
        st.markdown("**Válaszd ki a használni kívánt eredményeket:**")
        picked_idx = render_result_selector(valid[["Versenyszám","Idő","sec","dist_m"]], key_prefix="cs_pick", max_select=None)

        if len(picked_idx) < 2:
            st.info("Legalább két eredményt jelölj ki a számításhoz.")
        else:
            use_df = valid.loc[picked_idx, ["Versenyszám","Idő","sec","dist_m"]].copy()
            cs, dprime = calc_cs_cp(use_df)
            if cs is None:
                st.warning("Nem sikerült kritikus sebességet számolni.")
            else:
                st.success(f"Kritikus sebesség (CS): **{cs:.3f} m/s** | Kritikus tempó: {pace_from_speed(cs)}")
                if dprime:
                    st.caption(f"D′ (anaerob kapacitás): ~{dprime:.0f} m")

                # Ábra
                fig, ax = plt.subplots()
                ax.scatter(use_df["sec"], use_df["dist_m"], label="Eredmények")
                if dprime is not None:
                    x_line = use_df["sec"].values
                    y_line = cs * x_line + (dprime if dprime is not None else 0.0)
                    ax.plot(x_line, y_line, label="Illesztett modell")
                ax.set_xlabel("Idő (s)")
                ax.set_ylabel("Távolság (m)")
                ax.legend()
                st.pyplot(fig)

# --- Tab2: Riegel exponens ---
with tab2:
    st.subheader("Riegel exponens és időbecslés")

    valid = idok.dropna(subset=["sec","dist_m"])
    valid = valid[(valid["sec"] > 0) & (valid["dist_m"] > 0)]

    if len(valid) < 2:
        st.info("Adj meg legalább két eredményt a Riegel-becsléshez.")
    else:
        st.markdown("**Válassz ki pontosan két eredményt:**")
        picked_idx = render_result_selector(valid[["Versenyszám","Idő","sec","dist_m"]], key_prefix="riegel_pick", max_select=2)

        if len(picked_idx) != 2:
            st.info("Pontosan két eredményt jelölj be.")
        else:
            r1, r2 = valid.loc[picked_idx].iloc[0], valid.loc[picked_idx].iloc[1]
            k = riegel_kitevő_from_two(r1["dist_m"], r1["sec"], r2["dist_m"], r2["sec"])
            if k is None or not math.isfinite(k):
                st.warning("Nem sikerült kitevőt becsülni (ellenőrizd az adatokat).")
            else:
                st.success(f"Becsült Riegel-kitevő: **{k:.3f}**")

                # Cél versenyszám kiválasztása + becslés
                target = st.selectbox("Cél versenyszám", EVENT_OPTIONS, index=EVENT_OPTIONS.index("10 Kilometres Road") if "10 Kilometres Road" in EVENT_OPTIONS else 0)
                d_target = DIST_TO_METERS.get(target, None)

                # Használjuk referenciának az időben "közelebbi" távot (opcionális döntés),
                # de itt legyen az első jelölt alapértelmezésként:
                ref_label = st.radio("Melyik eredmény legyen a referencia?", [
                    f"{r1['Versenyszám']} – {r1['Idő']}",
                    f"{r2['Versenyszám']} – {r2['Idő']}"
                ], horizontal=False)
                ref = r1 if ref_label.startswith(str(r1["Versenyszám"])) else r2

                if d_target and ref["sec"] and ref["dist_m"]:
                    t_pred = riegel_predict_time(ref["sec"], ref["dist_m"], d_target, k)
                    if t_pred and math.isfinite(t_pred):
                        st.success(f"Várható idő {target} távon: **{format_seconds(t_pred)}** (Riegel)")
                    else:
                        st.warning("Nem sikerült időt becsülni.")

# --- Tab3: WA Score ---
with tab3:
    st.subheader("WA pontszámok és kalkulátor")

    # WA pontok kiszámítása a meglévő eredményekre
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

    show = idok.dropna(subset=["Score"]).copy()
    if show.empty:
        st.info("Nincs kiszámítható WA pontszám. Adj meg több adatot.")
    else:
        # Grafikon: score szerinti csökkenő sorrend
        show = show.sort_values("Score", ascending=False)
        labels = [f"{r['Versenyszám']} · {r['Idő']}" for _, r in show.iterrows()]
        vals = show["Score"].astype(int).tolist()

        fig, ax = plt.subplots()
        ax.barh(range(len(vals)), vals)
        ax.set_yticks(range(len(vals)))
        ax.set_yticklabels(labels)
        ax.invert_yaxis()
        ax.set_xlabel("WA Score")
        ax.set_title("Eredmények WA pontszám szerint")
        st.pyplot(fig)

        # Összegzés emojikkal
        best = show.iloc[0]
        worst = show.iloc[-1]
        avg = int(round(show["Score"].mean()))
        st.markdown(
            f"🥇 **Legjobb WA pontszám:** {int(best['Score'])} — {best['Versenyszám']} ({best['Idő']})"
            f"\n\n📊 **Átlagos WA pontszám:** {avg}"
            f"\n\n🐢 **Legalacsonyabb WA pontszám:** {int(worst['Score'])} — {worst['Versenyszám']} ({worst['Idő']})"
        )

        st.divider()
        st.subheader("WA kalkulátor")

        st.markdown("**Válassz ki legfeljebb 3 eredményt az átlagos WA score-hoz:**")
        picked_idx = render_result_selector(show[["Versenyszám","Idő","Score"]], key_prefix="wa_calc_pick", max_select=3)

        if len(picked_idx) == 0:
            st.info("Jelölj ki legalább egy eredményt a kalkulációhoz.")
        else:
            sel = show.loc[picked_idx]
            avg_score = int(round(sel["Score"].mean()))
            st.success(f"Átlagos WA score (kiválasztottakból): **{avg_score}**")

            # Cél versenyszám + nem kiválasztása → idő becslése a táblából
            colA, colB = st.columns(2)
            with colA:
                target_disc = st.selectbox("Cél versenyszám", EVENT_OPTIONS, index=EVENT_OPTIONS.index("Half Marathon") if "Half Marathon" in EVENT_OPTIONS else 0, key="wa_calc_disc")
            with colB:
                target_gender = st.selectbox("Nem (cél versenyszám WA táblához)", ["Man","Woman"], index=["Man","Woman"].index(st.session_state.get("gender","Man")), key="wa_calc_gender")

            pred_time = time_for_score(wa_df, target_gender, target_disc, avg_score) if wa_df is not None else None
            if pred_time:
                st.success(f"**{avg_score}** átlagos WA score kb. **{pred_time}** időnek felel meg ({target_disc}, {target_gender}).")
            else:
                st.warning("A megadott score-hoz nem találtam időt a WA táblában (ellenőrizd az adatfájlt).")
