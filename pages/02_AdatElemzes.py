import math
import pandas as pd
import numpy as np
import streamlit as st

# -------------------- Oldal beállítás --------------------
st.set_page_config(page_title="AdatElemzés", page_icon="📊", layout="wide")

# -------------------- Közös segédfüggvények --------------------
# Esemény-formátumok és -távok (szinkronban az AdatBetöltés oldallal)
EVENT_TIME_FORMATS = {
    "50 Metres": "ss.ss",
    "55 Metres": "ss.ss",
    "60 Metres": "ss.ss",
    "100 Metres": "ss.ss",
    "200 Metres": "ss.ss",
    "200 Metres Short Track": "ss.ss",
    "300 Metres": "ss.ss",
    "300 Metres Short Track": "ss.ss",
    "400 Metres": "ss.ss",
    "400 Metres Short Track": "ss.ss",
    "500 Metres": "mm:ss.ss",
    "500 Metres Short Track": "mm:ss.ss",
    "600 Metres": "mm:ss.ss",
    "600 Metres Short Track": "mm:ss.ss",
    "800 Metres": "mm:ss.ss",
    "800 Metres Short Track": "mm:ss.ss",
    "1000 Metres": "mm:ss.ss",
    "1000 Metres Short Track": "mm:ss.ss",
    "1500 Metres": "mm:ss.ss",
    "1500 Metres Short Track": "mm:ss.ss",
    "Mile": "mm:ss.ss",
    "Mile Short Track": "mm:ss.ss",
    "2000 Metres": "mm:ss.ss",
    "2000 Metres Short Track": "mm:ss.ss",
    "3000 Metres": "mm:ss.ss",
    "3000 Metres Short Track": "mm:ss.ss",
    "2 Miles": "mm:ss.ss",
    "2 Miles Short Track": "mm:ss.ss",
    "5000 Metres": "mm:ss.ss",
    "5000 Metres Short Track": "mm:ss.ss",
    "10000 Metres": "mm:ss.ss",
    "5 Kilometres Road": "mm:ss",
    "10 Kilometres Road": "mm:ss",
    "15 Kilometres Road": "mm:ss",
    "20 Kilometres Road": "mm:ss",
    "25 Kilometres Road": "mm:ss",
    "30 Kilometres Road": "mm:ss",
    "10 Miles Road": "mm:ss",
    "Half Marathon": "hh:mm:ss",
    "Marathon": "hh:mm:ss",
    "100 Kilometres Road": "hh:mm:ss"
}
EVENT_OPTIONS = list(EVENT_TIME_FORMATS.keys())

# Hozzárendelt táv (méter) becslés a futószámokhoz
EVENT_TO_METERS = {
    "50 Metres": 50, "55 Metres": 55, "60 Metres": 60,
    "100 Metres": 100, "200 Metres": 200, "200 Metres Short Track": 200,
    "300 Metres": 300, "300 Metres Short Track": 300,
    "400 Metres": 400, "400 Metres Short Track": 400,
    "500 Metres": 500, "500 Metres Short Track": 500,
    "600 Metres": 600, "600 Metres Short Track": 600,
    "800 Metres": 800, "800 Metres Short Track": 800,
    "1000 Metres": 1000, "1000 Metres Short Track": 1000,
    "1500 Metres": 1500, "1500 Metres Short Track": 1500,
    "Mile": 1609.344, "Mile Short Track": 1609.344,
    "2000 Metres": 2000, "2000 Metres Short Track": 2000,
    "3000 Metres": 3000, "3000 Metres Short Track": 3000,
    "2 Miles": 3218.688, "2 Miles Short Track": 3218.688,
    "5000 Metres": 5000, "5000 Metres Short Track": 5000,
    "10000 Metres": 10000,
    "5 Kilometres Road": 5000, "10 Kilometres Road": 10000,
    "15 Kilometres Road": 15000, "20 Kilometres Road": 20000,
    "25 Kilometres Road": 25000, "30 Kilometres Road": 30000,
    "10 Miles Road": 16093.44,
    "Half Marathon": 21097.5,
    "Marathon": 42195,
    "100 Kilometres Road": 100000
}

def time_to_seconds(txt: str) -> float:
    """'mm:ss.ss' vagy 'hh:mm:ss' → másodperc (float)"""
    if not isinstance(txt, str) or not txt.strip():
        return np.nan
    t = txt.strip()
    parts = t.split(":")
    try:
        if len(parts) == 1:
            return float(parts[0])
        elif len(parts) == 2:
            m = int(parts[0])
            s = float(parts[1])
            return m * 60 + s
        elif len(parts) == 3:
            h = int(parts[0]); m = int(parts[1]); s = float(parts[2])
            return h * 3600 + m * 60 + s
    except:
        return np.nan
    return np.nan

def seconds_to_formatted(sec: float, event: str) -> str:
    """Másodperc → megjelenítés az esemény formátuma alapján."""
    if np.isnan(sec):
        return "-"
    fmt = EVENT_TIME_FORMATS.get(event, "mm:ss.ss")
    sec = float(sec)
    if fmt == "ss.ss":
        return f"{sec:.2f}"
    elif fmt == "mm:ss":
        m = int(sec // 60); s = int(round(sec - m*60))
        return f"{m}:{s:02d}"
    elif fmt == "mm:ss.ss":
        m = int(sec // 60); s = sec - m*60
        return f"{m}:{s:05.2f}"
    elif fmt == "hh:mm:ss":
        h = int(sec // 3600); rem = sec - h*3600
        m = int(rem // 60); s = int(round(rem - m*60))
        return f"{h}:{m:02d}:{s:02d}"
    else:
        # fallback
        m = int(sec // 60); s = sec - m*60
        return f"{m}:{s:05.2f}"

def ensure_idok_df():
    if "idok" not in st.session_state:
        st.session_state.idok = pd.DataFrame(columns=["Versenyszám","Idő","Gender"])
    return st.session_state.idok

def get_gender():
    # AdatBetöltés oldalon állítjuk: "Man" vagy "Woman"
    return st.session_state.get("gender", "Man")

# -------------------- Fejléc --------------------
st.markdown(
    """
    <div style="background:linear-gradient(90deg,#3d5361,#5d7687);padding:15px;border-radius:8px;margin-bottom:16px;">
        <h1 style="color:white;margin:0;font-size:1.6rem;">📊 AdatElemzés</h1>
        <p style="color:#f0f0f0;margin:0.2rem 0 0;">Válaszd ki a felhasznált eredményeket kis kártyákon pipával, majd nézd meg a számításokat fülönként.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# -------------------- Eredmény-kártyák (általános komponens) --------------------
def result_cards_selector(df: pd.DataFrame, key_prefix: str, max_select: int | None = None, help_text: str | None = None):
    """
    Kis kártyás választó. Visszaadja a kiválasztott indexek listáját (df indexeiből).
    """
    if df.empty:
        st.info("Nincs elérhető eredmény. Térj vissza az AdatBetöltés oldalra.")
        return []

    if help_text:
        st.caption(help_text)

    selected = []
    # rendezzük távolság szerint (ha van), különben az eredeti sorrend
    df_local = df.copy()
    df_local["meters"] = df_local["Versenyszám"].map(EVENT_TO_METERS)
    df_local = df_local.sort_values(["meters","Versenyszám"], na_position="last").reset_index()

    # 4 oszlopos megjelenítés
    for i in range(0, len(df_local), 4):
        cols = st.columns(4)
        for j in range(4):
            if i + j >= len(df_local): break
            row = df_local.iloc[i+j]
            idx_orig = row["index"]
            ev = row["Versenyszám"]
            ttxt = row["Idő"]
            with cols[j].container(border=True):
                st.markdown(f"**{ev}**")
                st.markdown(f"{ttxt}")
                # Egyedi kulcs a duplikációk elkerülésére
                ch = st.checkbox("Kiválaszt", key=f"{key_prefix}_sel_{idx_orig}", value=False)
                if ch:
                    selected.append(idx_orig)

    if (max_select is not None) and (len(selected) > max_select):
        st.warning(f"Legfeljebb {max_select} eredményt pipálhatsz be. A feleslegeseket vedd ki.")
    return selected

# -------------------- Adatok --------------------
idok = ensure_idok_df()
gender = get_gender()

# -------------------- Tabok --------------------
tab_cs, tab_riegel, tab_wa = st.tabs(["🏁 Kritikus Sebesség", "📐 Riegel exponens", "🏅 WA Score"])

# ==================== KRITIKUS SEBESSÉG ====================
with tab_cs:
    st.subheader("Kritikus Sebesség (CS)")

    sel = result_cards_selector(
        idok,
        key_prefix="cs",
        max_select=None,
        help_text="Javasolt **3 és 20 perc** közötti eredményeket kiválasztani a stabil CS becsléshez."
    )

    # Szűrés és modell
    use_df = idok.loc[sel].copy()
    if use_df.empty:
        st.info("Válassz ki legalább **2** eredményt a becsléshez.")
    else:
        # csak azok az események, melyekhez van táv és értelmes idő
        use_df["meters"] = use_df["Versenyszám"].map(EVENT_TO_METERS)
        use_df["sec"] = use_df["Idő"].apply(time_to_seconds)
        use_df = use_df.dropna(subset=["meters","sec"])
        if len(use_df) < 2:
            st.info("Legalább **2** érvényes eredmény szükséges.")
        else:
            # lineáris illesztés: distance = CS * time + D'
            x = use_df["sec"].values
            y = use_df["meters"].values
            # illesztés
            A = np.vstack([x, np.ones_like(x)]).T
            cs, dprime = np.linalg.lstsq(A, y, rcond=None)[0]  # cs = slope (m/s), d' = intercept (m)
            # Eredmények
            cs_kmh = cs * 3.6
            pace_sec_per_km = 1000.0 / cs
            pace_txt = seconds_to_formatted(pace_sec_per_km, "5000 Metres")  # mm:ss.ss jellegű
            col1, col2, col3 = st.columns([1.2,1,1])
            with col1:
                st.metric("🔥 Kritikus tempó (CS)", f"{pace_txt}/km")
            with col2:
                st.metric("CS (m/s)", f"{cs:.2f}")
            with col3:
                st.metric("D′ (m)", f"{dprime:.0f}")

            # Grafikon: pontok + illesztett egyenes
            import matplotlib.pyplot as plt

            xs = np.linspace(x.min()*0.9, x.max()*1.1, 100)
            ys = cs*xs + dprime

            fig = plt.figure(figsize=(6,4))
            plt.scatter(x, y, label="Eredmények")
            plt.plot(xs, ys, label="Illesztett: d = CS·t + D′")
            plt.xlabel("Idő (s)")
            plt.ylabel("Táv (m)")
            plt.title("CS illesztés (kijelölt eredmények)")
            plt.legend()
            st.pyplot(fig, use_container_width=True)

# ==================== RIEGEL EXPONENS ====================
with tab_riegel:
    st.subheader("Riegel exponens")

    st.caption("Válassz **pontosan két** eredményt a kártyákon pipával. Ezekből számoljuk az exponens értékét, majd egy választott célversenyszámra becslünk időt.")
    sel = result_cards_selector(idok, key_prefix="riegel", max_select=2)

    if len(sel) != 2:
        st.info("Válassz ki **pontosan 2** eredményt a számításhoz.")
    else:
        df2 = idok.loc[sel].copy()
        df2["meters"] = df2["Versenyszám"].map(EVENT_TO_METERS)
        df2["sec"] = df2["Idő"].apply(time_to_seconds)
        df2 = df2.dropna(subset=["meters","sec"])
        if len(df2) != 2:
            st.info("A kiválasztott két eredményből nem mind konvertálható (hiányzó táv/idő).")
        else:
            # jelöljük ki
            d1, t1 = df2.iloc[0]["meters"], df2.iloc[0]["sec"]
            d2, t2 = df2.iloc[1]["meters"], df2.iloc[1]["sec"]
            # Riegel k kiszámítása: t ~ a * d^k → k = ln(t2/t1)/ln(d2/d1)
            if d1<=0 or d2<=0 or t1<=0 or t2<=0 or (d1==d2):
                st.warning("Nem számolható k az adott párosból.")
            else:
                k = math.log(t2/t1) / math.log(d2/d1)
                st.metric("Riegel exponens (k)", f"{k:.3f}")

                # Célversenyszám választás (az ÖSSZES elérhetőből)
                st.markdown("**Cél versenyszám kiválasztása**")
                # Kártyás cél-esemény választó (hogy konzisztens legyen a többi UI-val)
                # De itt 1 db-ot kell választani → egyetlen checkbox is elég.
                # Mivel sok az esemény, megcsináljuk 4 oszlopos gridben.
                target_event = st.session_state.get("riegel_target_event", None)
                chosen = None
                evs = EVENT_OPTIONS
                for i in range(0, len(evs), 4):
                    cols = st.columns(4)
                    for j in range(4):
                        if i+j >= len(evs): break
                        ev = evs[i+j]
                        with cols[j].container(border=True):
                            checked = st.checkbox(ev, key=f"riegel_target_{ev}", value=(ev==target_event))
                            if checked:
                                chosen = ev
                if chosen is None:
                    st.info("Válassz ki **1** célversenyszámot a fenti listából.")
                else:
                    st.session_state["riegel_target_event"] = chosen
                    d_target = EVENT_TO_METERS.get(chosen, np.nan)
                    if np.isnan(d_target) or d_target<=0:
                        st.warning("A választott célversenyszámhoz nem ismert a táv.")
                    else:
                        # Időbecslés: t_target = t_ref * (d_target/d_ref)^k
                        # Vegyük referenciaidőnek a rövidebb távhoz tartozó gyorsabb időt (stabilabb)
                        if d1 <= d2:
                            tref, dref = t1, d1
                            ref_txt = df2.iloc[0]["Versenyszám"] + " – " + df2.iloc[0]["Idő"]
                        else:
                            tref, dref = t2, d2
                            ref_txt = df2.iloc[1]["Versenyszám"] + " – " + df2.iloc[1]["Idő"]

                        t_est = tref * (d_target / dref) ** k
                        t_est_txt = seconds_to_formatted(t_est, chosen)

                        st.success(f"✅ **Várható idő a választott távon:** {chosen} → **{t_est_txt}**")

                        # Magyarázó doboz képlettel és behelyettesítéssel
                        st.markdown(
                            f"""
                            <div style="border-left: 4px solid #3b82f6; background:#eef6ff; padding:12px; border-radius:6px; margin-top:8px;">
                            <b>Hogyan számoltuk?</b><br>
                            Alapképlet: <code>T₂ = T₁ × (D₂ / D₁)^k</code><br>
                            Ahol <code>k = ln(T₂/T₁) / ln(D₂/D₁)</code> a két kiválasztott eredményből.<br><br>
                            <b>Behelyettesítve:</b><br>
                            Referencia: <code>T₁ = {seconds_to_formatted(tref, df2.iloc[0]['Versenyszám']) if dref==d1 else seconds_to_formatted(tref, df2.iloc[1]['Versenyszám'])}</code>,
                            <code>D₁ = {int(dref)} m</code> (≈ {ref_txt})<br>
                            Cél: <code>D₂ = {int(d_target)} m</code> ({chosen}), <code>k = {k:.3f}</code><br>
                            Így: <code>T₂ = {tref:.2f} × ({d_target:.0f}/{dref:.0f})^{k:.3f} = {t_est:.2f} s</code> → <b>{t_est_txt}</b>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

# ==================== WA SCORE ====================
with tab_wa:
    st.subheader("WA Score")

    # WA tábla betöltés
    @st.cache_data(show_spinner=False)
    def load_wa_table():
        try:
            df = pd.read_excel("wa_score_merged_standardized.xlsx")
            # elvárás: oszlopokban legyen legalább: Event, Gender, Time(s) vagy Time, Score
            # próbáljuk egységesíteni
            cols = [c.lower() for c in df.columns]
            df.columns = cols
            # próbáljuk kitalálni a kulcsneveket
            # event -> 'event'
            # gender -> 'gender'
            # time (sec) -> lehet 'time(s)' vagy 'time_sec' vagy 'time'
            tcol = "time(s)" if "time(s)" in cols else ("time_sec" if "time_sec" in cols else "time")
            scol = "score" if "score" in cols else None
            if "event" not in cols or "gender" not in cols or (tcol not in cols) or (scol not in cols):
                return None
            df = df.rename(columns={tcol: "time_sec", "event": "event", "gender": "gender", scol: "score"})
            # normalizálás
            df["event"] = df["event"].astype(str)
            df["gender"] = df["gender"].astype(str)
            return df[["event","gender","time_sec","score"]].copy()
        except Exception:
            return None

    wa_df = load_wa_table()
    if wa_df is None:
        st.warning("A WA ponttáblát nem sikerült betölteni (`wa_score_merged_standardized.xlsx`). Ellenőrizd a fájlt a repó gyökerében.")
    else:
        # Pontszámok a felhasználói eredményekhez
        def wa_score_for_time(event: str, gender: str, time_txt: str) -> float | None:
            """Idő → score. Szabály: a megadott időhöz a legközelebbi, de nem gyorsabb (azaz nem kisebb idő) sor pontszáma."""
            tsec = time_to_seconds(time_txt)
            if np.isnan(tsec):
                return None
            sub = wa_df[(wa_df["event"]==event) & (wa_df["gender"]==gender)].copy()
            if sub.empty:
                return None
            # idő növekvő (lassuló) → score csökken
            sub = sub.sort_values("time_sec", ascending=True).reset_index(drop=True)
            # keressük az indexet, ahol time_sec >= tsec (tehát a tábla idő lassabb vagy egyenlő)
            # de a feladat szerint a legközelebbi, de NEM gyorsabb: azaz sub.time_sec >= tsec legkisebb idő
            idx = np.searchsorted(sub["time_sec"].values, tsec, side="left")
            if idx < len(sub):
                # a sub[idx] idő >= tsec (lassabb vagy egyező) → annak a scoreja kell
                return float(sub.iloc[idx]["score"])
            else:
                # minden tábla-idő gyorsabb volt → nincs lassabb vagy egyenlő → vegyük a legutolsót (leglassabb)
                return float(sub.iloc[-1]["score"])

        # Pontlista kiszámítás
        if idok.empty:
            st.info("Nincs időeredmény. Töltsd fel az AdatBetöltés oldalon.")
        else:
            work = idok.copy()
            work["score"] = work.apply(lambda r: wa_score_for_time(r["Versenyszám"], gender, r["Idő"]), axis=1)
            work = work.dropna(subset=["score"]).copy()
            if work.empty:
                st.info("A megadott eredményekhez nem találtam WA pontot a táblában.")
            else:
                # Kártyák dobozban, score szerinti sorrend
                work = work.sort_values("score", ascending=False).reset_index(drop=True)
                st.markdown('<div style="padding:8px;border:1px solid #e5e7eb;border-radius:8px;margin-bottom:8px;">', unsafe_allow_html=True)
                for i in range(0, len(work), 4):
                    cols = st.columns(4)
                    for j in range(4):
                        if i+j >= len(work): break
                        row = work.iloc[i+j]
                        with cols[j].container(border=True):
                            st.markdown(f"**{row['Versenyszám']}**")
                            st.markdown(f"⏱️ {row['Idő']}")
                            st.markdown(f"🏅 **{int(row['score'])}** pont")
                st.markdown('</div>', unsafe_allow_html=True)

                # Emojis összegzés
                best = work.iloc[0]
                avg_score = work["score"].mean()
                worst = work.iloc[-1]
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.success(f"🥇 Legjobb: **{best['Versenyszám']} – {best['Idő']}** ({int(best['score'])} p)")
                with c2:
                    st.info(f"📊 Átlagos: **{avg_score:.1f} p**")
                with c3:
                    st.warning(f"🏁 Legalacsonyabb: **{worst['Versenyszám']} – {worst['Idő']}** ({int(worst['score'])} p)")

                st.divider()
                st.subheader("WA kalkulátor (átlag pont → idő becslés egy cél távra)")

                st.caption("Pipálj be legfeljebb **3** eredményt; ezek átlag pontja alapján kiszámoljuk, hogy egy választott távon milyen idő felelne meg ennek a pontszámnak.")

                sel_calc = result_cards_selector(work[["Versenyszám","Idő","Gender"]].assign(Gender=gender), key_prefix="wa_calc", max_select=3)

                if len(sel_calc) == 0:
                    st.info("Válassz ki legalább 1 (max 3) eredményt.")
                else:
                    sub_calc = work.loc[sel_calc].copy()
                    avg_s = sub_calc["score"].mean()
                    st.write(f"Átlagolt WA pontszám: **{avg_s:.1f}**")

                    # Célversenyszám választása kártyásan (1 kiválasztható)
                    st.markdown("**Cél versenyszám kiválasztása**")
                    target_event = st.session_state.get("wa_calc_target_event", None)
                    chosen = None
                    for i in range(0, len(EVENT_OPTIONS), 4):
                        cols = st.columns(4)
                        for j in range(4):
                            if i+j >= len(EVENT_OPTIONS): break
                            ev = EVENT_OPTIONS[i+j]
                            with cols[j].container(border=True):
                                chk = st.checkbox(ev, key=f"wa_calc_target_{ev}", value=(ev==target_event))
                                if chk:
                                    chosen = ev
                    if chosen is None:
                        st.info("Válassz ki **1** célversenyszámot a fenti listából.")
                    else:
                        st.session_state["wa_calc_target_event"] = chosen
                        # score -> idő (monotonitás alapján)
                        dd = wa_df[(wa_df["event"]==chosen) & (wa_df["gender"]==gender)].copy()
                        if dd.empty:
                            st.warning("Ehhez a célversenyszámhoz/​nemhez nem található WA táblázat.")
                        else:
                            dd = dd.sort_values("score", ascending=True).reset_index(drop=True)
                            # keressük az első sort, ahol score >= avg_s
                            idx = np.searchsorted(dd["score"].values, avg_s, side="left")
                            if idx >= len(dd):
                                idx = len(dd)-1
                            tsec = float(dd.iloc[idx]["time_sec"])
                            ttxt = seconds_to_formatted(tsec, chosen)
                            st.success(f"✅ Becsült idő a választott távon ({chosen}) az átlagolt {avg_s:.1f} pont alapján: **{ttxt}**")

# -------------------- Alul: az IDŐK táblázat (megtekintés) --------------------
st.divider()
st.subheader("Megadott IDŐK (összefoglaló)")
view_df = idok.copy()
if view_df.empty:
    st.info("Még nincs adat.")
else:
    st.dataframe(view_df, use_container_width=True)
