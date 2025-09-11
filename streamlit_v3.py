#!/usr/bin/env python
# coding: utf-8

import streamlit as st
import pandas as pd
from datetime import date
from get_pb import scrape_world_athletics_pbs  # <<< közvetlen import

# ====== Oldal beállítás ======
st.set_page_config(page_title="Futó teljesítmény – Adatbetöltés", page_icon="🏃‍♂️", layout="wide")

# ====== Stílus ======
st.markdown("""
<style>
hr.soft { border: none; border-top: 1px solid black; margin: 1rem 0; }
h3 { color: #3d5361; margin-bottom: .35rem; }
.hint { color:#5f6c76; font-size:.9rem; margin:-2px 0 10px 0; }
.headerbox{
  background: linear-gradient(180deg, #ffffff, #f9fafb);
  border: 1px solid black; border-radius: 0; padding: 12px 16px; margin-bottom: 10px;
}
.headerbox h1{font-size:1.25rem; margin:0; color: #3d5361;}
.smallmuted{color:#6c7a86; font-size:.92rem;}
div[data-testid="stContainer"] > div:has(> div[data-testid="stVerticalBlock"]) { background: #f6f7f9; }
div[data-testid="stContainer"] { border: 1px solid black !important; border-radius: 0 !important; padding: 14px 14px 10px 14px; }
</style>
""", unsafe_allow_html=True)

# ====== Esemény-formátumok (MEGADOTT LISTA) ======
event_time_formats = {
    '50 Metres': 'ss.ss', '55 Metres': 'ss.ss', '60 Metres': 'ss.ss',
    '100 Metres': 'ss.ss', '200 Metres': 'ss.ss', '200 Metres Short Track': 'ss.ss',
    '300 Metres': 'ss.ss', '300 Metres Short Track': 'ss.ss', '400 Metres': 'ss.ss', '400 Metres Short Track': 'ss.ss',
    '500 Metres': 'mm:ss.ss', '500 Metres Short Track': 'mm:ss.ss', '600 Metres': 'mm:ss.ss', '600 Metres Short Track': 'mm:ss.ss',
    '800 Metres': 'mm:ss.ss', '800 Metres Short Track': 'mm:ss.ss', '1000 Metres': 'mm:ss.ss', '1000 Metres Short Track': 'mm:ss.ss',
    '1500 Metres': 'mm:ss.ss', '1500 Metres Short Track': 'mm:ss.ss', 'Mile': 'mm:ss.ss', 'Mile Short Track': 'mm:ss.ss',
    'Mile Road': 'mm:ss.ss', '2000 Metres': 'mm:ss.ss', '2000 Metres Short Track': 'mm:ss.ss', '3000 Metres': 'mm:ss.ss',
    '3000 Metres Short Track': 'mm:ss.ss', '2 Miles': 'mm:ss.ss', '2 Miles Short Track': 'mm:ss.ss',
    '5000 Metres': 'mm:ss.ss', '5000 Metres Short Track': 'mm:ss.ss', '5 Kilometres Road': 'mm:ss.ss',
    '10,000 Metres': 'mm:ss.ss', '10 Kilometres Road': 'mm:ss.ss', '10 Miles Road': 'hh:mm:ss',
    '15 Kilometres Road': 'hh:mm:ss', 'Half Marathon': 'hh:mm:ss', 'Marathon': 'hh:mm:ss'
}
EVENT_OPTIONS = list(event_time_formats.keys())

# ====== Állapot ======
if "gender" not in st.session_state: st.session_state.gender = "Man"
if "wa_kartyak" not in st.session_state: st.session_state.wa_kartyak = []
if "manual_kartyak" not in st.session_state:
    st.session_state.manual_kartyak = [{"Táv":"", "Eredmény":"", "Használat":True} for _ in range(2)]
if "idok" not in st.session_state:
    st.session_state.idok = pd.DataFrame(columns=["Versenyszám","Idő","Dátum","Score","Gender","Forrás"])
if "wa_scores_df" not in st.session_state:
    try:
        st.session_state.wa_scores_df = pd.read_csv("wa_score_merged_standardized.csv")
    except Exception:
        pass

# ====== Pontkereső segédfv. ======
def parse_time_to_seconds(time_str):
    try:
        if time_str is None:
            return None
        t = str(time_str).replace(",", ".").strip()
        parts = t.split(":")
        if len(parts) == 3: h, m, s = parts
        elif len(parts) == 2: h, m, s = 0, *parts
        else: h, m, s = 0, 0, parts[0]
        return int(h) * 3600 + int(m) * 60 + float(s)
    except:
        return None

def pontkereso(gender, discipline, input_time):
    if "wa_scores_df" not in st.session_state:
        return None
    wa = st.session_state.wa_scores_df.copy()
    wa = wa[(wa["gender"] == gender) & (wa["discipline"] == discipline)]
    if wa.empty: return None
    wa["time_seconds"] = wa["result"].apply(parse_time_to_seconds)
    input_sec = parse_time_to_seconds(input_time)
    if input_sec is None: return None
    wa = wa[wa["time_seconds"] >= input_sec]
    if wa.empty: return None
    closest = wa.sort_values("time_seconds").iloc[0]
    try: return int(closest["score"])
    except: return None

# ====== WA scraping közvetlenül Seleniummal ======
def get_personal_bests_direct(url: str, timeout=60):
    try:
        rows = scrape_world_athletics_pbs(url.strip(), wait_sec=timeout)
        if not isinstance(rows, list) or len(rows) == 0:
            return None
        df = pd.DataFrame(rows)
        for c in ["Discipline","Performance","Date","Score"]:
            if c not in df.columns: df[c] = None
        df = df[~df["Discipline"].isna() & ~df["Performance"].isna()].copy()
        df["Performance"] = df["Performance"].astype(str).str.replace(",", ".", regex=False)
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date.astype("string")
        return df
    except Exception as e:
        st.error(f"Hiba a scraping közben: {e}")
        return None

# ====== Fejléc ======
st.markdown(
    '<div class="headerbox"><h1>🏃‍♂️ Futó teljesítmény – Adatbetöltés</h1>'
    '<div class="smallmuted">A PB-ket a World Athletics profilod <b>Personal bests</b> füléről töltjük be. '
    'Csak a megadott versenyszám-listából szereplő eseményeket vesszük át.</div></div>',
    unsafe_allow_html=True
)

# ====== Nem ======
with st.container(border=True):
    st.markdown("<h3>Nem kiválasztása</h3>", unsafe_allow_html=True)
    st.radio("Nem:", ["Man","Woman"], horizontal=True, key="gender")

st.markdown('<hr class="soft" />', unsafe_allow_html=True)

# ====== Két oszlop ======
col1, col2 = st.columns([1,1], gap="large")

# --- WA PB kártya (Personal bests) ---
with col1:
    with st.container(border=True):
        st.markdown("<h3>World Athletics PB-k (Personal bests)</h3>"
                    "<div class='hint'>Illeszd be a WA profil linket, a betöltés csak a listában szereplő versenyszámokra történik.</div>",
                    unsafe_allow_html=True)

        wa_url = st.text_input("World Athletics profil link", key="wa_url")

        if st.button("PB-k betöltése", type="primary"):
            if not wa_url.strip():
                st.error("Adj meg egy érvényes WA linket.")
            else:
                with st.spinner("PB-k letöltése Seleniummal…"):
                    wa_df = get_personal_bests_direct(wa_url, timeout=60)

                if wa_df is not None and "Discipline" in wa_df.columns:
                    wa_tbl = wa_df[wa_df["Discipline"].isin(EVENT_OPTIONS)].copy()
                    if wa_tbl.empty:
                        st.warning("A PB-k között nincs a megadott listának megfelelő esemény.")
                    else:
                        for _, row in wa_tbl.iterrows():
                            st.session_state.wa_kartyak.append({
                                "Táv": row.get("Discipline",""),
                                "Eredmény": row.get("Performance",""),
                                "Dátum": pd.to_datetime(row.get("Date", date.today()), errors="coerce").date() if row.get("Date", None) else date.today(),
                                "Használat": True,
                                "Score": row.get("Score", None),
                                "Forrás": "World Athletics"
                            })
                        st.success(f"Betöltve {len(wa_tbl)} PB az engedélyezett versenyszámokból.")
                else:
                    st.warning("Nem kaptam megfelelő szerkezetű adatot a scrapingből.")

        if st.session_state.wa_kartyak:
            st.markdown("#### Betöltött WA kártyák")
            for i in range(0, len(st.session_state.wa_kartyak), 2):
                cols = st.columns(2)
                for j in range(2):
                    idx = i + j
                    if idx >= len(st.session_state.wa_kartyak): break
                    k = st.session_state.wa_kartyak[idx]
                    cap = k.get("Táv", f"WA kártya {idx+1}")
                    with cols[j].expander(cap, expanded=True):
                        k["Táv"] = st.selectbox("Versenyszám", EVENT_OPTIONS,
                                                index=EVENT_OPTIONS.index(k["Táv"]) if k["Táv"] in EVENT_OPTIONS else 0,
                                                key=f"wa_tav_{idx}")
                        k["Eredmény"] = st.text_input("Időeredmény", value=k.get("Eredmény",""), key=f"wa_ered_{idx}")
                        k["Dátum"] = st.date_input("Dátum", value=k.get("Dátum", date.today()), key=f"wa_datum_{idx}")
                        k["Score"] = st.text_input("WA pontszám (opcionális)", value=str(k.get("Score","") or ""), key=f"wa_score_{idx}")
                        k["Használat"] = st.checkbox("Használat", value=k.get("Használat", True), key=f"wa_haszn_{idx}")
                        if st.button("Eltávolítás", key=f"wa_rm_{idx}"):
                            st.session_state.wa_kartyak.pop(idx); st.experimental_rerun()

            if st.button("Kiválasztott WA PB-k hozzáadása az IDŐK táblához", type="primary"):
                rows = []
                for k in st.session_state.wa_kartyak:
                    if not k.get("Használat", False): continue
                    rows.append({
                        "Versenyszám": k["Táv"], "Idő": k["Eredmény"],
                        "Dátum": str(k.get("Dátum","")) if k.get("Dátum","") else "",
                        "Score": k.get("Score", None), "Gender": st.session_state.gender,
                        "Forrás": "World Athletics"
                    })
                if rows:
                    add_df = pd.DataFrame(rows)
                    st.session_state.idok = pd.concat([st.session_state.idok, add_df], ignore_index=True)
                    st.session_state.idok.drop_duplicates(subset=["Versenyszám","Idő","Dátum","Gender"], inplace=True, keep="first")
                    st.success(f"Hozzáadva {len(add_df)} sor.")

# --- Manuális bevitel ---
with col2:
    with st.container(border=True):
        st.markdown("<h3>Manuális bevitel</h3>"
                    "<div class='hint'>Válaszd ki a versenyszámot a listából, add meg az időt, majd add hozzá az IDŐK táblához.</div>",
                    unsafe_allow_html=True)

        for i in range(0, len(st.session_state.manual_kartyak), 2):
            cols = st.columns(2)
            for j in range(2):
                idx = i + j
                if idx >= len(st.session_state.manual_kartyak): break
                k = st.session_state.manual_kartyak[idx]
                cap = k["Táv"] if k["Táv"] else f"Kártya #{idx+1}"
                with cols[j].expander(cap, expanded=True):
                    k["Táv"] = st.selectbox("Versenyszám", [""] + EVENT_OPTIONS,
                                            index=([""] + EVENT_OPTIONS).index(k["Táv"]) if k["Táv"] in EVENT_OPTIONS else 0,
                                            key=f"manual_tav_{idx}")
                    k["Eredmény"] = st.text_input("Időeredmény", value=k.get("Eredmény",""), key=f"manual_ered_{idx}")
                    k["Használat"] = st.checkbox("Használat", value=k.get("Használat", True), key=f"manual_haszn_{idx}")
                    if st.button("Eltávolítás", key=f"manual_rm_{idx}"):
                        st.session_state.manual_kartyak.pop(idx); st.experimental_rerun()

        c1, c2 = st.columns([1,1])
        with c1:
            if st.button("További kártya hozzáadása"):
                st.session_state.manual_kartyak.append({"Táv":"", "Eredmény":"", "Használat":True}); st.experimental_rerun()
        with c2:
            if st.button("Megadott eredmények hozzáadása az IDŐK táblához", type="primary"):
                rows = []
                for k in st.session_state.manual_kartyak:
                    if k.get("Használat", False) and k.get("Táv") and k.get("Eredmény"):
                        rows.append({
                            "Versenyszám": k["Táv"], "Idő": k["Eredmény"], "Dátum":"", "Score": None,
                            "Gender": st.session_state.gender, "Forrás":"Manuális"
                        })
                if rows:
                    add_df = pd.DataFrame(rows)
                    st.session_state.idok = pd.concat([st.session_state.idok, add_df], ignore_index=True)
                    st.session_state.idok.drop_duplicates(subset=["Versenyszám","Idő","Dátum","Gender"], inplace=True, keep="first")
                    st.success(f"Hozzáadva {len(add_df)} sor.")

st.markdown('<hr class="soft" />', unsafe_allow_html=True)

# ====== Összesített tábla ======
with st.container(border=True):
    st.markdown("<h3>Összesített IDŐK táblázat</h3>", unsafe_allow_html=True)
    if not st.session_state.idok.empty:
        st.dataframe(st.session_state.idok, use_container_width=True, hide_index=True)
    else:
        st.info("Még nincs adat a táblában.")
