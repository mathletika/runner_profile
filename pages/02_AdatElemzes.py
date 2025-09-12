import math
import os
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# -------------------- Oldal beállítás --------------------
st.set_page_config(page_title="AdatElemzés", page_icon="📊", layout="wide")

# -------------------- Események és távok --------------------
EVENT_TIME_FORMATS = {
    "50 Metres": "ss.ss", "55 Metres": "ss.ss", "60 Metres": "ss.ss",
    "100 Metres": "ss.ss", "200 Metres": "ss.ss", "200 Metres Short Track": "ss.ss",
    "300 Metres": "ss.ss", "300 Metres Short Track": "ss.ss",
    "400 Metres": "ss.ss", "400 Metres Short Track": "ss.ss",
    "500 Metres": "mm:ss.ss", "500 Metres Short Track": "mm:ss.ss",
    "600 Metres": "mm:ss.ss", "600 Metres Short Track": "mm:ss.ss",
    "800 Metres": "mm:ss.ss", "800 Metres Short Track": "mm:ss.ss",
    "1000 Metres": "mm:ss.ss", "1000 Metres Short Track": "mm:ss.ss",
    "1500 Metres": "mm:ss.ss", "1500 Metres Short Track": "mm:ss.ss",
    "Mile": "mm:ss.ss", "Mile Short Track": "mm:ss.ss",
    "2000 Metres": "mm:ss.ss", "2000 Metres Short Track": "mm:ss.ss",
    "3000 Metres": "mm:ss.ss", "3000 Metres Short Track": "mm:ss.ss",
    "2 Miles": "mm:ss.ss", "2 Miles Short Track": "mm:ss.ss",
    "5000 Metres": "mm:ss.ss", "5000 Metres Short Track": "mm:ss.ss",
    "10000 Metres": "mm:ss.ss",
    "5 Kilometres Road": "mm:ss", "10 Kilometres Road": "mm:ss",
    "15 Kilometres Road": "mm:ss", "20 Kilometres Road": "mm:ss",
    "25 Kilometres Road": "mm:ss", "30 Kilometres Road": "mm:ss",
    "10 Miles Road": "mm:ss",
    "Half Marathon": "hh:mm:ss", "Marathon": "hh:mm:ss",
    "100 Kilometres Road": "hh:mm:ss",
}
EVENT_OPTIONS = list(EVENT_TIME_FORMATS.keys())

EVENT_TO_METERS = {
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
    "5 Kilometres Road": 5000, "10 Kilometres Road": 10000, "15 Kilometres Road": 15000,
    "20 Kilometres Road": 20000, "25 Kilometres Road": 25000, "30 Kilometres Road": 30000,
    "10 Miles Road": 16093.4, "Half Marathon": 21097.5, "Marathon": 42195,
    "100 Kilometres Road": 100000,
}

# -------------------- Helper függvények --------------------
def time_to_seconds(txt: str) -> float:
    if not isinstance(txt, str) or not txt.strip():
        return np.nan
    parts = txt.strip().split(":")
    try:
        if len(parts) == 1:
            return float(parts[0])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    except Exception:
        return np.nan
    return np.nan

def seconds_to_mmss(sec: float) -> str:
    if not np.isfinite(sec) or sec <= 0:
        return "-"
    m = int(sec // 60)
    s = int(round(sec - m * 60))
    return f"{m}:{s:02d}"

def seconds_to_hms(sec: float) -> str:
    if not np.isfinite(sec) or sec <= 0:
        return "-"
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(round(sec % 60))
    return f"{h}:{m:02d}:{s:02d}"

def seconds_to_mmss_per_km(sec_per_km: float) -> str:
    if not np.isfinite(sec_per_km) or sec_per_km <= 0:
        return "-"
    m = int(sec_per_km // 60)
    s = int(round(sec_per_km - m * 60))
    return f"{m}:{s:02d}/km"

def riegel_k(d1, t1, d2, t2):
    if min(d1, d2, t1, t2) <= 0 or d1 == d2:
        return None
    return math.log(t2 / t1) / math.log(d2 / d1)

def riegel_predict(t_ref, d_ref, d_target, k):
    if not k or min(t_ref, d_ref, d_target) <= 0:
        return None
    return t_ref * (d_target / d_ref) ** k

# -------------------- Kártyás választó (kisebb kártyák) --------------------
def result_cards_selector(df, key_prefix, max_select=None, ncols=8):
    """
    Visszaadja a kiválasztott indexeket (a df eredeti indexe alapján).
    Kisebb, tömörebb kártyák, jelölőnégyzet címke nélkül.
    """
    selected = []
    df = df.reset_index()
    for i in range(0, len(df), ncols):
        cols = st.columns(ncols, gap="small")
        for j in range(ncols):
            if i + j >= len(df):
                break
            row = df.iloc[i + j]
            with cols[j].container(border=True):
                st.caption(f"**{row['Versenyszám']}**")
                st.caption(row["Idő"])
                checked = st.checkbox(" ", key=f"{key_prefix}_{row['index']}")
                if checked:
                    selected.append(row["index"])
    if max_select and len(selected) > max_select:
        st.warning(f"Max {max_select} jelölhető.")
    return selected

# -------------------- Adatok a sessionből --------------------
if "idok" not in st.session_state or st.session_state.idok.empty:
    st.warning("Nincs adat az `idok` táblában.")
    st.stop()
idok = st.session_state.idok.copy()
gender = st.session_state.get("gender", "Man")  # "Man" / "Woman"

# -------------------- Tabok --------------------
tab1, tab2, tab3 = st.tabs(["🏁 Kritikus Sebesség", "📐 Riegel exponens", "🏅 WA Score"])

# ===========================================================
#                       KRITIKUS SEBESSÉG
# ===========================================================
with tab1:
    st.subheader("Kritikus Sebesség (CS)")
    # Ajánlás VISSZATÉR:
    st.info("**Ajánlás:** 3–20 perc közötti idők használata. **Max. 3** idő jelölhető ki.")

    sel = result_cards_selector(idok, "cs", max_select=3, ncols=8)
    use = idok.loc[sel].copy()

    if len(use) < 2:
        st.caption("Jelölj ki legalább **két** eredményt a számításhoz.")
    else:
        use["m"] = use["Versenyszám"].map(EVENT_TO_METERS)
        use["s"] = use["Idő"].apply(time_to_seconds)

        # Lineáris illesztés: distance = CS * time + D'
        x = use["s"].values
        y = use["m"].values
        A = np.vstack([x, np.ones_like(x)]).T
        cs, dprime = np.linalg.lstsq(A, y, rcond=None)[0]  # cs = m/s

        pace = 1000.0 / cs  # sec/km

        # Zöld hangsúlyos kártya – mm:ss/km
        st.markdown(
            f"""
            <div style="background:#d1fae5;padding:10px 12px;border-radius:8px;display:flex;align-items:center;gap:14px;">
              <div style="font-size:18px;font-weight:700;">🔥 Kritikus tempó:</div>
              <div style="font-size:20px;font-weight:800;">{seconds_to_mmss_per_km(pace)}</div>
              <div style="margin-left:auto;font-size:12px;opacity:0.85;">
                CS: {cs:.2f} m/s &nbsp; • &nbsp; D′: {dprime:.0f} m
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # KISEBB GRAFIKON és betűk
        xs = np.linspace(x.min() * 0.9, x.max() * 1.1, 100)
        ys = cs * xs + dprime
        fig, ax = plt.subplots(figsize=(3.6, 2.6), dpi=120)
        ax.scatter(x, y, s=12)
        ax.plot(xs, ys, linewidth=1.2)
        ax.set_xlabel("Idő (s)", fontsize=9)
        ax.set_ylabel("Táv (m)", fontsize=9)
        ax.tick_params(axis="both", labelsize=8)
        st.pyplot(fig, use_container_width=False)

# ===========================================================
#                       RIEGEL EXPONENS
# ===========================================================
with tab2:
    st.subheader("Riegel exponens")
    # Ajánlások VISSZA:
    st.info("**Ajánlás:** válassz **két** eredményt (minél különbözőbb távok), majd add meg a **cél versenyszámot**.")

    sel = result_cards_selector(idok, "riegel", max_select=2, ncols=8)

    # A cél versenyszám dropdown – ALAPBÓL is látszódjon
    target = st.selectbox("Cél versenyszám", EVENT_OPTIONS, key="riegel_target_select")

    # Ha megvan a két kijelölt eredmény, számolunk
    if len(sel) < 2:
        st.caption("Jelölj ki **pontosan két** eredményt a Riegel-k számításhoz.")
    else:
        df = idok.loc[sel].copy()
        df["m"] = df["Versenyszám"].map(EVENT_TO_METERS)
        df["s"] = df["Idő"].apply(time_to_seconds)

        # Két pont
        d1, t1 = float(df.iloc[0]["m"]), float(df.iloc[0]["s"])
        d2, t2 = float(df.iloc[1]["m"]), float(df.iloc[1]["s"])

        k = riegel_k(d1, t1, d2, t2)
        if k is None:
            st.error("A Riegel-k nem számolható ezekből a pontokból.")
        else:
            # Referencia VISSZA: a célhoz közelebbi legyen a referencia
            d_target = EVENT_TO_METERS[target]
            ref = (d1, t1) if abs(d_target - d1) < abs(d_target - d2) else (d2, t2)
            t_pred = riegel_predict(ref[1], ref[0], d_target, k)

            # Eredmény doboz
            if t_pred and np.isfinite(t_pred):
                pretty = seconds_to_hms(t_pred) if t_pred >= 3600 else seconds_to_mmss(t_pred)
                st.success(f"**Várható idő** {target}: **{pretty}**")

            # Részletes magyarázat – képlet + behelyettesítés (RÉSZLETES, mint korábban)
            # k képlete és behelyettesítése
            st.markdown(
                f"""
                <div style="border-left:4px solid #3b82f6;background:#eef6ff;padding:10px 12px;border-radius:6px;">
                  <div style="font-weight:700;margin-bottom:6px;">Riegel képletek és számítás:</div>
                  <div style="margin-bottom:6px;">
                    <code>k = ln(T₂/T₁) / ln(D₂/D₁)</code>
                  </div>
                  <div style="font-size:13px;margin-bottom:10px;">
                    Behelyettesítve: <code>k = ln({t2:.2f}/{t1:.2f}) / ln({d2:.0f}/{d1:.0f}) = {k:.4f}</code>
                  </div>
                  <div style="margin-bottom:6px;">
                    <code>T_target = T_ref × (D_target / D_ref) ^ k</code>
                  </div>
                  <div style="font-size:13px;">
                    Behelyettesítve: <code>T_target = {ref[1]:.2f} × ({d_target:.0f}/{ref[0]:.0f})^{k:.4f}
                    = {t_pred:.2f} s</code>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ===========================================================
#                           WA SCORE
# ===========================================================
with tab3:
    st.subheader("WA Score")

    # ---- WA tábla megbízható betöltése (ez volt a hiba oka) ----
    # A 'pages' alól futó modulnál nem mindig a repo gyökere a CWD.
    # Keressük több lehetséges helyen:
    candidates = [
        Path("wa_score_merged_standardized.xlsx"),
        Path(__file__).resolve().parent.parent / "wa_score_merged_standardized.xlsx",
        Path(__file__).resolve().parent / "wa_score_merged_standardized.xlsx",
        Path(os.getcwd()) / "wa_score_merged_standardized.xlsx",
    ]
    wa_path = next((p for p in candidates if p.is_file()), None)

    if wa_path is None:
        st.error("❌ A WA ponttáblát nem sikerült betölteni (**wa_score_merged_standardized.xlsx**). "
                 "Ellenőrizd, hogy a fájl a **repo gyökerében** van commitolva.")
        st.stop()

    @st.cache_data(show_spinner=False)
    def load_wa_table(path: Path) -> pd.DataFrame:
        df = pd.read_excel(path)
        # oszlop normalizálás rugalmasan (különböző forrásokhoz)
        cols = {c.lower().strip(): c for c in df.columns}
        # jelöltek
        event_col = next((cols[k] for k in cols if k in ("event", "discipline", "versenyszám")), None)
        gender_col = next((cols[k] for k in cols if k in ("gender", "sex", "nem")), None)
        points_col = next((cols[k] for k in cols if k in ("points", "score", "wa_points")), None)

        # idő/eredmény más néven is érkezhet
        seconds_col = None
        for key in ("perf_sec", "time_sec", "time_seconds", "seconds", "mark_sec", "mark_s", "performance_seconds"):
            if key in cols:
                seconds_col = cols[key]
                break

        # ha nincs seconds oszlop, próbáljuk stringből konvertálni
        if seconds_col is None:
            # keresünk valami idő/mark oszlopot
            time_text_col = next((cols[k] for k in cols if k in ("time", "mark", "eredmény", "perf")), None)
            if time_text_col is not None:
                df["_wa_seconds"] = df[time_text_col].apply(lambda x: time_to_seconds(str(x)) if pd.notna(x) else np.nan)
                seconds_col = "_wa_seconds"

        need = [event_col, gender_col, points_col, seconds_col]
        if any(v is None for v in need):
            raise ValueError("A WA tábla elvárt oszlopai nem találhatók (event/gender/points/seconds).")

        out = df.rename(columns={
            event_col: "event",
            gender_col: "gender",
            points_col: "points",
            seconds_col: "seconds",
        })[["event", "gender", "seconds", "points"]].copy()

        # tisztítás
        out = out.dropna(subset=["event", "gender", "seconds", "points"])
        # egységesítés
        out["event"] = out["event"].astype(str)
        out["gender"] = out["gender"].astype(str).map(lambda s: "Man" if s.lower().startswith(("m", "man", "férfi")) else ("Woman" if s.lower().startswith(("w", "wo", "women", "nő")) else s))
        out = out.sort_values(["event", "gender", "seconds"]).reset_index(drop=True)
        return out

    try:
        wa_df = load_wa_table(wa_path)
    except Exception as e:
        st.error(f"❌ A WA ponttábla betöltése sikertelen: {e}")
        st.stop()

    # ---- Segédfüggvény: idő -> pont a szabályod szerint (legközelebbi lassabb vagy egyenlő) ----
    def wa_points_lookup(g: str, event: str, t_sec: float) -> float | None:
        sub = wa_df[(wa_df["gender"] == g) & (wa_df["event"] == event)]
        if sub.empty or not np.isfinite(t_sec):
            return None
        # legközelebbi lassabb (nagyobb vagy egyenlő idő)
        sub = sub.sort_values("seconds")
        idx = np.searchsorted(sub["seconds"].values, t_sec, side="left")
        if idx >= len(sub):
            idx = len(sub) - 1
        return float(sub.iloc[idx]["points"])

    # ---- Eredmények pontozása és kártyák (kicsi, takarékos) ----
    work = idok.copy()
    work["s"] = work["Idő"].apply(time_to_seconds)
    work["WA pont"] = work.apply(
        lambda r: wa_points_lookup(gender, r["Versenyszám"], r["s"]), axis=1
    )
    work = work.dropna(subset=["WA pont"])
    work = work.sort_values("WA pont", ascending=False)

    # Kártyalista – kompakt
    st.caption("Eredmények WA pont szerint (csökkenő):")
    for i in range(0, len(work), 6):
        cols = st.columns(6, gap="small")
        for j in range(6):
            if i + j >= len(work):
                break
            row = work.iloc[i + j]
            with cols[j].container(border=True):
                st.caption(f"**{row['Versenyszám']}**")
                st.caption(f"{row['Idő']}")
                st.markdown(f"<div style='font-weight:700;'>🏅 {int(round(row['WA pont']))} p</div>", unsafe_allow_html=True)

    # Összefoglaló emojikkal
    if not work.empty:
        best = work.iloc[0]
        worst = work.iloc[-1]
        avg = work["WA pont"].mean()
        st.markdown(
            f"""
            <div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:6px;">
              <div style="background:#fef3c7;padding:10px;border-radius:8px;">🥇 <b>Legjobb</b>: {best['Versenyszám']} — {best['Idő']} — <b>{int(round(best['WA pont']))} p</b></div>
              <div style="background:#e0f2fe;padding:10px;border-radius:8px;">📊 <b>Átlag</b>: <b>{int(round(avg))} p</b></div>
              <div style="background:#fee2e2;padding:10px;border-radius:8px;">🐢 <b>Legalacsonyabb</b>: {worst['Versenyszám']} — {worst['Idő']} — <b>{int(round(worst['WA pont']))} p</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    # ---- Kalkulátor: max 3 pipa → átlag WA pont → cél versenyszám idő becslés ----
    st.markdown("**Kalkulátor** — jelölj ki legfeljebb 3 eredményt, számolunk átlag WA pontot, majd válassz célszámot.")

    sel_calc = result_cards_selector(idok, "wa_calc", max_select=3, ncols=8)
    use_calc = idok.loc[sel_calc].copy()

    if len(use_calc) == 0:
        st.caption("Jelölj ki legalább egy eredményt.")
    else:
        use_calc["s"] = use_calc["Idő"].apply(time_to_seconds)
        use_calc["WA pont"] = use_calc.apply(
            lambda r: wa_points_lookup(gender, r["Versenyszám"], r["s"]), axis=1
        )
        use_calc = use_calc.dropna(subset=["WA pont"])
        if use_calc.empty:
            st.warning("Nem számolható WA pont a kijelöltekre.")
        else:
            avg_pts = float(use_calc["WA pont"].mean())
            st.markdown(f"**Átlag WA pont:** {int(round(avg_pts))} p")

            target2 = st.selectbox("Cél versenyszám (WA kalkulátor)", EVENT_OPTIONS, key="wa_calc_target")
            # Invertálás: pont -> idő. Keresünk olyan sort, amelynek pontja legközelebb az átlaghoz.
            sub = wa_df[(wa_df["gender"] == gender) & (wa_df["event"] == target2)]
            if sub.empty:
                st.warning("A cél versenyszámhoz nincs WA tábla.")
            else:
                # legközelebbi pont
                sub = sub.sort_values("points", ascending=False)  # nagy pont → gyors
                diffs = (sub["points"] - avg_pts).abs().values
                idx = int(diffs.argmin())
                t_pred = float(sub.iloc[idx]["seconds"])
                pretty = seconds_to_hms(t_pred) if t_pred >= 3600 else seconds_to_mmss(t_pred)
                st.success(f"**Várható idő** {target2}: **{pretty}** (≈ {int(round(sub.iloc[idx]['points']))} p)")
