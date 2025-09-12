import pandas as pd
import streamlit as st

# Oldal beállítás
st.set_page_config(page_title="Eredmények betöltése", page_icon="📝", layout="wide")

# ====== Állapot inicializálás ======
if "gender" not in st.session_state:
    st.session_state.gender = "Man"

if "manual_cards" not in st.session_state:
    # Alapból 4 üres kártya
    st.session_state.manual_cards = [{"Táv":"", "Idő":""} for _ in range(4)]

if "idok" not in st.session_state:
    st.session_state.idok = pd.DataFrame(columns=["Versenyszám","Idő","Gender","Forrás"])

# ====== Események + formátumok ======
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

# ====== Fejléc ======
st.markdown(
    """
    <div style="background:linear-gradient(90deg,#3d5361,#5d7687);padding:15px;border-radius:8px;margin-bottom:20px;">
        <h1 style="color:white;margin:0;font-size:1.6rem;">📝 Eredmények betöltése</h1>
        <p style="color:#f0f0f0;margin:0.2rem 0 0;">Add meg kézzel a versenyeredményeidet, majd nézd meg az elemzést a második oldalon.</p>
    </div>
    """,
    unsafe_allow_html=True
)

with st.sidebar:
    st.header("Beállítások")
    st.radio("Nem:", ["Man","Woman"], horizontal=True, key="gender")
    st.caption("A WA pontszámokhoz a nem szükséges (külön férfi/női táblák).")

# ====== Manuális kártyák ======
st.subheader("Manuális eredmények")
st.caption("Válaszd ki a versenyszámot, add meg az időt (pl. 16:45.2 vagy 1:15:30), majd add a táblázathoz.")

for i in range(0, len(st.session_state.manual_cards), 4):
    cols = st.columns(4)
    for j in range(4):
        idx = i + j
        if idx >= len(st.session_state.manual_cards): break
        k = st.session_state.manual_cards[idx]
        cap = k["Táv"] if k["Táv"] else f"Kártya #{idx+1}"
        with cols[j].expander(cap, expanded=True):
            k["Táv"] = st.selectbox("Versenyszám", [""] + EVENT_OPTIONS,
                                    index=([""] + EVENT_OPTIONS).index(k["Táv"]) if k["Táv"] in EVENT_OPTIONS else 0,
                                    key=f"manual_tav_{idx}")
            k["Idő"] = st.text_input("Időeredmény", value=k.get("Idő",""), key=f"manual_ido_{idx}")
            if st.button("Eltávolítás", key=f"manual_rm_{idx}"):
                st.session_state.manual_cards.pop(idx)
                st.rerun()

c1, c2 = st.columns([1,1])
with c1:
    if st.button("Új kártya hozzáadása"):
        st.session_state.manual_cards.append({"Táv":"", "Idő":""})
        st.rerun()
with c2:
    if st.button("Megadott eredmények hozzáadása az IDŐK táblához", type="primary"):
        rows = []
        for k in st.session_state.manual_cards:
            if k.get("Táv") and k.get("Idő"):
                rows.append({
                    "Versenyszám": k["Táv"], "Idő": k["Idő"],
                    "Gender": st.session_state.gender, "Forrás":"Manuális"
                })
        if rows:
            add_df = pd.DataFrame(rows)
            st.session_state.idok = pd.concat([st.session_state.idok, add_df], ignore_index=True)
            st.session_state.idok.drop_duplicates(subset=["Versenyszám","Idő","Gender"], inplace=True, keep="first")
            st.success(f"Hozzáadva {len(add_df)} sor.")

st.divider()

# ====== IDŐK tábla megjelenítése ======
st.subheader("Összesített IDŐK táblázat")

if st.session_state.idok.empty:
    st.info("Még nincs adat a táblában.")
else:
    st.dataframe(st.session_state.idok, use_container_width=True, hide_index=True)

# ====== Gomb a második oldalra ======
st.divider()
if st.button("➡️ Tovább az AdatElemzés oldalra"):
    st.switch_page("pages/02_AdatElemzes.py")
