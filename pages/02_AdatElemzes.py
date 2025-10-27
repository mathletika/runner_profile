import math
import os
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# -------------------- Oldal beállítás --------------------
st.set_page_config(page_title="Adatelemzés", page_icon="📊", layout="wide")

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
# === Infóbox stílus + helper ===
def _inject_info_styles():
    import streamlit as st
    st.markdown("""
    <style>
      .info-box{
        background:#f5f7fa;           /* halvány szürke */
        border:1px solid #e5e7eb;     /* vékony szegély */
        border-radius:12px;
        padding:14px 16px;
        margin:8px 0 16px 0;
      }
      .info-title{
        font-weight:600;
        color:#111827;
        margin:0 0 6px 0;
        font-size:0.95rem;
      }
      .info-text{
        color:#374151;
        font-size:0.92rem;
        line-height:1.55;
        margin:0;
      }
    </style>
    """, unsafe_allow_html=True)

def info_box(title: str, html_body: str, icon: str = "ℹ️"):
    st.markdown(
        """
        <style>
        .rp-infobox{background:#f3f4f6;border:1px solid #e5e7eb;border-radius:12px;padding:14px 16px;margin:8px 0;}
        .rp-infobox h4{margin:0 0 6px 0;font-size:15px;font-weight:700;color:#111827;display:flex;gap:8px;align-items:center;}
        .rp-infobox p{margin:6px 0 0 0;font-size:13px;line-height:1.5;color:#374151;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="rp-infobox">
          <h4>{icon} {title}</h4>
          <p>{html_body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


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
    st.warning("Nincsenek megadva időeredmények.")
    st.stop()
idok = st.session_state.idok.copy()
gender = st.session_state.get("gender", "Man")

# -------------------- Tabok --------------------
tab1, tab2, tab3 = st.tabs(["🏁 Kritikus Sebesség", "📐 Riegel-exponens", "🏅 WA Score"])

# ===========================================================
#                 KRITIKUS SEBESSÉG (meghagyva)
# ===========================================================
with tab1:
    st.subheader("Kritikus sebesség (Critical Speed, CS)")
    info_box(
        "Mi az a Kritikus sebesség?",
        "A <b>Kritikus sebesség</b> (<i>k</i>) lényegében a teljesítmény alapú, valóban érzett küszöb a fenntartható és fenntarthatatlan tartományok között.<br>"
        "Kettő vagy több eredmény alapján számolható, és ebből aztán zónákat, edzésintenzitásokat is lehet képezni.<br>"
        "Forrás és ajánlott irodalom: Philip Skiba: Scientific Training for Endurance Athletes",
        icon="🔥"
    )
    st.info("**Ajánlás:** 3–20 perc közötti idők használata. **Max. 3** idő jelölhető ki.")

    sel = result_cards_selector(idok, "cs", max_select=3, ncols=8)
    use = idok.loc[sel].copy()
    if len(use) >= 2:
        use["m"] = use["Versenyszám"].map(EVENT_TO_METERS)
        use["s"] = use["Idő"].apply(time_to_seconds)
        x = use["s"].values; y = use["m"].values
        A = np.vstack([x, np.ones_like(x)]).T
        cs, dprime = np.linalg.lstsq(A, y, rcond=None)[0]
        pace = 1000.0 / cs

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


        import io

        # ... kritikus sebesség számítás után:
        xs = np.linspace(x.min() * 0.9, x.max() * 1.1, 100)
        ys = cs * xs + dprime
        fig, ax = plt.subplots(figsize=(3.6, 2.6), dpi=120)
        ax.scatter(x, y, s=12)
        ax.plot(xs, ys, linewidth=1.2)
        ax.set_xlabel("Idő (s)", fontsize=9)
        ax.set_ylabel("Táv (m)", fontsize=9)
        ax.tick_params(axis="both", labelsize=8)
        st.pyplot(fig, use_container_width=False)

        # --- ÚJ: mentés a session-be exporthoz ---
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
        buf.seek(0)
        st.session_state["cs_result"] = {
            "pace_str": seconds_to_mmss_per_km(pace),
            "cs": cs,
            "dprime": dprime,
            "plot_png": buf.getvalue(),
        }

        # --- Zóna kalkuláció és zóna-kártya renderelés ---

        cs_sec_per_km = pace  # mp/km float tempó a kritikus sebességhez

        def zone_interval(f_hi, f_lo):
            """
            f_hi, f_lo pl. 1.24 és 1.15
            Lassabb tempó (magasabb mp/km) = felső érték.
            Visszatér: ("3:45", "3:30") jellegű stringpár.
            """
            hi = cs_sec_per_km * f_hi
            lo = cs_sec_per_km * f_lo
            return seconds_to_mmss(hi), seconds_to_mmss(lo)

        zones = [
            {
                "zona": "Z1 Regeneráció",
                "range": ">124%",
                "pace_txt": f"{seconds_to_mmss(cs_sec_per_km * 1.24)}+",
            },
            {
                "zona": "Z2 Állóképesség",
                "range": "124–115%",
                "pace_txt": " - ".join(zone_interval(1.24, 1.15)),
            },
            {
                "zona": "Z3 Tempó",
                "range": "114–105%",
                "pace_txt": " - ".join(zone_interval(1.14, 1.05)),
            },
            {
                "zona": "Z4 Threshold",
                "range": "104–95%",
                "pace_txt": " - ".join(zone_interval(1.04, 0.95)),
            },
            {
                "zona": "Z5 VO₂max",
                "range": "94–84%",
                "pace_txt": " - ".join(zone_interval(0.94, 0.84)),
            },
            {
                "zona": "Z6 Anaerob",
                "range": "<84%",
                "pace_txt": f"{seconds_to_mmss(cs_sec_per_km * 0.84)}-",
            },
        ]

        # --- Stílus a kártyához (egyszer beszúrjuk itt) ---
        st.markdown("""
        <style>
        .cs-card {
            background:#ffffff;
            border:1px solid #e5e7eb;
            border-radius:12px;
            padding:16px 20px;
            margin-top:16px;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            box-shadow:0 8px 24px -6px rgba(0,0,0,0.08);
        }
        .cs-head {
            font-size:14px;
            font-weight:600;
            color:#111827;
            display:flex;
            align-items:center;
            margin-bottom:10px;
        }
        .cs-table {
            width:100%;
            border-collapse:collapse;
        }
        .cs-table th {
            text-align:left;
            font-size:12px;
            font-weight:600;
            color:#6b7280;
            padding:6px 8px;
            border-bottom:1px solid #e5e7eb;
            white-space:nowrap;
        }
        .cs-table td {
            font-size:13px;
            color:#111827;
            padding:8px 8px;
            border-bottom:1px solid #f3f4f6;
            vertical-align:top;
            white-space:nowrap;
        }
        .cs-zonename {
            font-weight:600;
            color:#111827;
        }
        .cs-range {
            color:#4b5563;
            font-size:12px;
        }
        .cs-pace {
            font-feature-settings:'tnum' 1,'ss01' 1;
            font-variant-numeric:tabular-nums;
            font-weight:600;
            color:#111827;
        }
        </style>
        """, unsafe_allow_html=True)

        # --- Táblázat sorainak HTML-je ---
        import streamlit.components.v1 as components

        # --- HTML sorok összeállítása ---
        rows_html_parts = []
        for z in zones:
            rows_html_parts.append(f"""
            <tr>
              <td style="padding:8px 8px; border-bottom:1px solid #f3f4f6; vertical-align:top; white-space:nowrap;">
                <div style="font-weight:600; color:#111827;">{z['zona']}</div>
                <div style="color:#4b5563; font-size:12px;">{z['range']}</div>
              </td>
              <td style="padding:8px 8px; border-bottom:1px solid #f3f4f6; vertical-align:top; white-space:nowrap;
                         font-feature-settings:'tnum' 1,'ss01' 1; font-variant-numeric:tabular-nums;
                         font-weight:600; color:#111827;">
                {z['pace_txt']}
              </td>
            </tr>
            """)
        rows_html = "\n".join(rows_html_parts)

        # --- az egész kártya komplett, inline stílussal (nem külső CSS-re támaszkodunk) ---
        card_html = f"""
        <div style="
            background:#ffffff;
            border:1px solid #e5e7eb;
            border-radius:12px;
            padding:16px 20px;
            margin-top:16px;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            box-shadow:0 8px 24px -6px rgba(0,0,0,0.08);
        ">
          <div style="
              font-size:14px;
              font-weight:600;
              color:#111827;
              margin-bottom:10px;
          ">
            Edzés zónák a Kritikus Sebesség alapján
          </div>

          <table style="width:100%; border-collapse:collapse;">
            <thead>
              <tr>
                <th style="
                    text-align:left;
                    font-size:12px;
                    font-weight:600;
                    color:#6b7280;
                    padding:6px 8px;
                    border-bottom:1px solid #e5e7eb;
                    white-space:nowrap;
                ">
                  Zóna
                </th>
                <th style="
                    text-align:left;
                    font-size:12px;
                    font-weight:600;
                    color:#6b7280;
                    padding:6px 8px;
                    border-bottom:1px solid #e5e7eb;
                    white-space:nowrap;
                ">
                  Tempóérték
                </th>
              </tr>
            </thead>
            <tbody>
              {rows_html}
            </tbody>
          </table>
        </div>
        """

        # itt NEM st.markdown, hanem egy valódi HTML iframe render
        components.html(card_html, height=440, scrolling=False)

# ===========================================================
#                 RIEGEL EXPONENS (meghagyva)
# ===========================================================
with tab2:
    st.subheader("Riegel-exponens")
    info_box(
        "Mi az a Riegel-exponens?",
        "A <b>Riegel-exponens</b> (<i>k</i>) egyszerűen szólva azt írja le, hogy mennyit lassulunk, ahogy növeljük a versenytávot.<br> "
        "Két ismert eredményből becsüljük <i>k</i>-t, majd ezzel előrejelzünk egy harmadik választott távra, rávetítve a várható lassulást/gyorsulást",
        icon="🧪"
    )

    st.info("**Ajánlás:** válassz két eredményt (a cél versenytávhoz minél közelebbi számok), majd add meg a cél versenyszámot.")

    sel = result_cards_selector(idok, "riegel", max_select=2, ncols=8)
    target = st.selectbox("Cél versenyszám", EVENT_OPTIONS, key="riegel_target_select")

    if len(sel) == 2:
        df = idok.loc[sel].copy()
        df["m"] = df["Versenyszám"].map(EVENT_TO_METERS)
        df["s"] = df["Idő"].apply(time_to_seconds)
        d1, t1 = float(df.iloc[0]["m"]), float(df.iloc[0]["s"])
        d2, t2 = float(df.iloc[1]["m"]), float(df.iloc[1]["s"])
        k = math.log(t2 / t1) / math.log(d2 / d1) if d1 != d2 else None
        if k:
            d_target = EVENT_TO_METERS[target]
            ref = (d1, t1) if abs(d_target - d1) < abs(d_target - d2) else (d2, t2)
            t_pred = ref[1] * (d_target / ref[0]) ** k
            if t_pred:
                pretty = seconds_to_hms(t_pred) if t_pred >= 3600 else seconds_to_mmss(t_pred)
                st.success(f"**Várható idő** {target}: **{pretty}**")

            st.markdown(
                f"""
                <div style="border-left:4px solid #3b82f6;background:#eef6ff;padding:10px 12px;border-radius:6px;">
                  <b>Riegel képletek és számítás:</b><br>
                  <code>k = ln(T₂/T₁) / ln(D₂/D₁)</code><br>
                  Behelyettesítve: <code>k = ln({t2:.2f}/{t1:.2f}) / ln({d2:.0f}/{d1:.0f}) = {k:.4f}</code><br><br>
                  <code>T_target = T_ref × (D_target / D_ref)^k</code><br>
                  Behelyettesítve: <code>T_target = {ref[1]:.2f} × ({d_target:.0f}/{ref[0]:.0f})^{k:.4f} = {t_pred:.2f} s</code>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ===========================================================
#                 WA SCORE (új kód hozzáadva)
# ===========================================================
with tab3:
    st.subheader("WA pontszám")
    info_box(
        "Mi az a WA pontszám",
        "A <b>WA pontszám</b> (<i>másik nevén Spiriev-táblázat</i>) atlétikai versenyszámok eredményeit pontozza aszerint, hogy az adott teljesítmény mennyire közelít a világszintű szinthez.<br>"
        "A pontszámok segítségével különböző távok és nemek eredményei is összehasonlíthatók, de mindegyik pontszám egy adott versenyszámhoz kötött.",
        icon="🏅"
    )

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

    # konverzió: score -> points, result -> result_sec
    wa_df = wa_df.rename(columns={"score": "points"})
    if "result_sec" not in wa_df.columns:
        wa_df["result_sec"] = wa_df["result"].apply(lambda x: time_to_seconds(str(x)))

    # Segédfüggvény: idő → WA pont
    def wa_points_lookup(g: str, event: str, t_sec: float) -> float | None:
        sub = wa_df[(wa_df["gender"] == g) & (wa_df["discipline"] == event)].copy()
        if sub.empty or not np.isfinite(t_sec):
            return None
        sub = sub.dropna(subset=["result_sec"])
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

    # HOgy be tudjuk tölteni majd az Exporthoz
    st.session_state["wa_results"] = work

    # KÁRTYÁK
    # ---- CSS definiálása egyszer ----
    st.markdown("""
    <style>
    .wa-box {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
        background-color: #ffffff;
    }
    .wa-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 10px;
    }
    .wa-card {
        background-color: #f9fafb;
        border-radius: 6px;
        padding: 8px 10px;
        text-align: center;
        font-size: 14px;
        font-weight: 600;
        white-space: nowrap;
    }
    </style>
    """, unsafe_allow_html=True)

    # ---- Dinamikus HTML tartalom ----
    cards_html = '<div class="wa-box"><div class="wa-grid">'

    for _, row in work.iterrows():
        cards_html += f'<div class="wa-card">{row["Versenyszám"]} ({row["Idő"]}): 🏅 {int(round(row["WA pont"]))} p</div>'

    cards_html += '</div></div>'

    st.markdown(cards_html, unsafe_allow_html=True)

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
    st.subheader("WA Kalkulátor")

    # ---- Kalkulátor ----
    st.markdown(
        "<div style='border-left:4px solid #3b82f6;background:#eef6ff;padding:10px 12px;border-radius:6px;'>"
        "Versenyszámok választása átlagos WA score számításhoz"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    sel_calc = result_cards_selector(work, "wa_calc", max_select=3, ncols=8)
    use_calc = work.loc[sel_calc].copy()

    avg_pts = None
    if len(use_calc) > 0:
        avg_pts = float(use_calc["WA pont"].mean())
        st.markdown(f"**Átlag WA pont:** {int(round(avg_pts))} p")
    else:
        st.caption("Nincs kijelölt eredmény, átlag WA pont nem számítható.")

    target2 = st.selectbox("Cél versenyszám", EVENT_OPTIONS, key="wa_calc_target")

    if avg_pts:
        sub = wa_df[(wa_df["gender"] == gender) & (wa_df["discipline"] == target2)].copy()
        if not sub.empty:
            sub = sub.dropna(subset=["result_sec"])
            sub = sub.sort_values("points", ascending=False)
            diffs = (sub["points"] - avg_pts).abs().values
            idx = int(diffs.argmin())
            t_pred = float(sub.iloc[idx]["result_sec"])
            pretty = seconds_to_hms(t_pred) if t_pred >= 3600 else seconds_to_mmss(t_pred)
            st.success(f"**Várható idő** {target2}: **{pretty}** (≈ {int(round(sub.iloc[idx]['points']))} p)")