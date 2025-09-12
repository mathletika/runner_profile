import math
import pandas as pd
import numpy as np
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
    "100 Kilometres Road": "hh:mm:ss"
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
    "100 Kilometres Road": 100000
}

# -------------------- Helper függvények --------------------
def time_to_seconds(txt: str) -> float:
    if not isinstance(txt, str) or not txt.strip():
        return np.nan
    parts = txt.split(":")
    try:
        if len(parts) == 1: return float(parts[0])
        elif len(parts) == 2: return int(parts[0])*60 + float(parts[1])
        elif len(parts) == 3: return int(parts[0])*3600 + int(parts[1])*60 + float(parts[2])
    except: return np.nan
    return np.nan

def seconds_to_mmss_per_km(sec_per_km: float) -> str:
    if np.isnan(sec_per_km) or sec_per_km<=0: return "-"
    m = int(sec_per_km//60); s = int(round(sec_per_km - m*60))
    return f"{m}:{s:02d}/km"

def riegel_k(d1,t1,d2,t2):
    if min(d1,d2,t1,t2)<=0 or d1==d2: return None
    return math.log(t2/t1)/math.log(d2/d1)

def riegel_predict(tref,dref,dtarget,k):
    if not k or min(tref,dref,dtarget)<=0: return None
    return tref*(dtarget/dref)**k

# -------------------- Kártyás választó --------------------
def result_cards_selector(df, key_prefix, max_select=None):
    selected=[]
    df=df.reset_index()
    for i in range(0,len(df),6):
        cols=st.columns(6)
        for j in range(6):
            if i+j>=len(df): break
            row=df.iloc[i+j]
            with cols[j].container(border=True):
                st.caption(f"**{row['Versenyszám']}**")
                st.text(row["Idő"])
                if st.checkbox(" ",key=f"{key_prefix}_{row['index']}"):
                    selected.append(row["index"])
    if max_select and len(selected)>max_select:
        st.warning(f"Max {max_select} választható.")
    return selected

# -------------------- Adatok --------------------
if "idok" not in st.session_state or st.session_state.idok.empty:
    st.warning("Nincs adat az `idok` táblában.")
    st.stop()
idok = st.session_state.idok.copy()
gender = st.session_state.get("gender","Man")

# -------------------- Tabok --------------------
tab1, tab2, tab3 = st.tabs(["🏁 Kritikus Sebesség","📐 Riegel exponens","🏅 WA Score"])

# -------------------- Kritikus Sebesség --------------------
with tab1:
    st.subheader("Kritikus Sebesség (CS)")
    sel=result_cards_selector(idok,"cs")
    use=idok.loc[sel].copy()
    if len(use)>=2:
        use["m"]=use["Versenyszám"].map(EVENT_TO_METERS)
        use["s"]=use["Idő"].apply(time_to_seconds)
        x=use["s"].values; y=use["m"].values
        A=np.vstack([x,np.ones_like(x)]).T
        cs,dprime=np.linalg.lstsq(A,y,rcond=None)[0]
        pace=1000/cs
        st.markdown(
            f"<div style='background:#d1fae5;padding:12px;border-radius:6px;'>"
            f"<h3>🔥 Kritikus tempó: {seconds_to_mmss_per_km(pace)}</h3>"
            f"<p>CS: {cs:.2f} m/s &nbsp; | &nbsp; D′: {dprime:.0f} m</p>"
            f"</div>",unsafe_allow_html=True)
        xs=np.linspace(x.min()*0.9,x.max()*1.1,100); ys=cs*xs+dprime
        fig,ax=plt.subplots(figsize=(4,3))
        ax.scatter(x,y); ax.plot(xs,ys)
        ax.set_xlabel("Idő (s)"); ax.set_ylabel("Táv (m)")
        st.pyplot(fig,use_container_width=True)

# -------------------- Riegel exponens --------------------
with tab2:
    st.subheader("Riegel exponens")
    sel=result_cards_selector(idok,"riegel",max_select=2)
    if len(sel)==2:
        df=idok.loc[sel].copy()
        df["m"]=df["Versenyszám"].map(EVENT_TO_METERS)
        df["s"]=df["Idő"].apply(time_to_seconds)
        if len(df)==2:
            d1,t1=df.iloc[0]["m"],df.iloc[0]["s"]
            d2,t2=df.iloc[1]["m"],df.iloc[1]["s"]
            k=riegel_k(d1,t1,d2,t2)
            if k:
                st.metric("k",f"{k:.3f}")
                target=st.selectbox("Cél versenyszám",EVENT_OPTIONS)
                dt=EVENT_TO_METERS[target]
                ref=(d1,t1) if abs(dt-d1)<abs(dt-d2) else (d2,t2)
                test=riegel_predict(ref[1],ref[0],dt,k)
                if test:
                    st.success(f"Várható idő {target}: {int(test//60)}:{int(test%60):02d}")
                    st.markdown(
                        f"<div style='border-left:4px solid #3b82f6;background:#eef6ff;padding:10px;'>"
                        f"Képlet: T₂ = T₁ × (D₂/D₁)^k<br>"
                        f"Behelyettesítve: T₂ = {ref[1]:.1f}s × ({dt}/{ref[0]})^{k:.3f} = {test:.1f}s"
                        f"</div>",unsafe_allow_html=True)

# -------------------- WA Score --------------------
with tab3:
    st.subheader("WA Score")
    try:
        wa_df=pd.read_excel("wa_score_merged_standardized.xlsx")
    except Exception:
        st.error("❌ A WA ponttáblát nem sikerült betölteni (`wa_score_merged_standardized.xlsx`).")
        st.stop()
    # dummy példa: itt számítás logika jönne
    st.info("Itt jönnének a WA kártyák és kalkulátor (a fájl betöltés után).")
