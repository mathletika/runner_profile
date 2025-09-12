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

# -------------------- Kártyás választó --------------------
def result_cards_selector(df, key_prefix, max_select=None, ncols=8):
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

# -------------------- Adatok --------------------
if "idok" not in st.session_state or st.session_state.idok.empty:
    st.warning("Nincs adat az `idok` táblában.")
    st.stop()
idok = st.session_state.idok.copy()
gender = st.session_state.get("gender", "Man")

# -------------------- Tabok --------------------
tab1, tab2, tab3 = st.tabs(["🏁 Kritikus Sebesség", "📐 Riegel exponens", "🏅 WA Score"])

# ===========================================================
#                           WA SCORE
# ===========================================================
with tab3:
    st.subheader("WA Score")

    # WA tábla betöltése (.csv)
    candidates = [
        Path("wa_score_merged_standardized.csv"),
        Path(__file__).resolve().parent.parent / "wa_score_merged_standardized.csv",
        Path(__file__).resolve().parent / "wa_score_merged_standardized.csv",
        Path(os.getcwd()) / "wa_score_merged_standardized.csv",
    ]
    wa_path = next((p for p in candidates if p.is_file()), None)

    if wa_path is None:
        st.error("❌ A WA ponttáblát nem sikerült betölteni (**wa_score_merged_standardized.csv**).")
        st.stop()

    wa_df = pd.read_csv(wa_path)

    # Segédfüggvény: idő → WA pont
    def wa_points_lookup(g: str, event: str, t_sec: float) -> float | None:
        sub = wa_df[(wa_df["gender"] == g) & (wa_df["discipline"] == event)]
        if sub.empty or not np.isfinite(t_sec):
            return None
        sub = sub.sort_values("result_sec")
        idx = np.searchsorted(sub["result_sec"].values, t_sec, side="left")
        if idx >= len(sub):
            idx = len(sub) - 1
        return float(sub.iloc[idx]["points"])

    # Pontszámok hozzárendelése
    work = idok.copy()
    work["s"] = work["Idő"].apply(time_to_seconds)
    work["WA pont"] = work.apply(
        lambda r: wa_points_lookup(gender, r["Versenyszám"], r["s"]), axis=1
    )
    work = work.dropna(subset=["WA pont"])
    work = work.sort_values("WA pont", ascending=False)

    # ---- Kártyák boxban ----
    st.markdown('<div style="padding:8px;border:1px solid #ddd;border-radius:8px;margin-bottom:12px;">', unsafe_allow_html=True)
    for i in range(0, len(work), 8):
        cols = st.columns(8, gap="small")
        for j in range(8):
            if i + j >= len(work):
                break
            row = work.iloc[i + j]
            with cols[j].container(border=True):
                st.caption(f"**{row['Versenyszám']}**")
                st.caption(f"{row['Idő']}")
                st.markdown(f"<div style='font-weight:700;'>🏅 {int(round(row['WA pont']))} p</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ---- Összegzés emojikkal ----
    if not work.empty:
        best = work.iloc[0]
        worst = work.iloc[-1]
        avg = work["WA pont"].mean()
        st.markdown(
            f"""
            🥇 Legjobb WA Score: {best['Versenyszám']} — {best['Idő']} — {int(round(best['WA pont']))} p  
            📊 Átlagos WA Score: {int(round(avg))} p  
            🐢 Legalacsonyabb WA Score: {worst['Versenyszám']} — {worst['Idő']} — {int(round(worst['WA pont']))} p
            """
        )

    st.divider()

    # ---- Kalkulátor ----
    st.markdown(
        "<div style='border-left:4px solid #3b82f6;background:#eef6ff;padding:10px 12px;border-radius:6px;'>"
        "Versenyszámok választása átlagos WA score számításhoz"
        "</div>",
        unsafe_allow_html=True,
    )

    sel_calc = result_cards_selector(work, "wa_calc", max_select=3, ncols=8)
    use_calc = work.loc[sel_calc].copy()

    if len(use_calc) > 0:
        avg_pts = float(use_calc["WA pont"].mean())
        st.markdown(f"**Átlag WA pont:** {int(round(avg_pts))} p")

        target2 = st.selectbox("Cél versenyszám", EVENT_OPTIONS, key="wa_calc_target")
        sub = wa_df[(wa_df["gender"] == gender) & (wa_df["discipline"] == target2)]
        if not sub.empty:
            sub = sub.sort_values("points", ascending=False)
            diffs = (sub["points"] - avg_pts).abs().values
            idx = int(diffs.argmin())
            t_pred = float(sub.iloc[idx]["result_sec"])
            pretty = seconds_to_hms(t_pred) if t_pred >= 3600 else seconds_to_mmss(t_pred)
            st.success(f"**Várható idő** {target2}: **{pretty}** (≈ {int(round(sub.iloc[idx]['points']))} p)")
