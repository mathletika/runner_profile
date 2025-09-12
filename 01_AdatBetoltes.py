import pandas as pd
import streamlit as st

# Oldal beállítás
st.set_page_config(page_title="Eredmények betöltése", page_icon="📝", layout="wide")

# ====== Állapot inicializálás ======
if "gender" not in st.session_state:
    st.session_state.gender = "Man"

if "manual_cards" not in st.session_state:
    st.session_state.manual_cards = [{"Táv":"", "Idő":""} for _ in range(4)]

if "idok" not in st.session_state:
    st.session_state.idok = pd.DataFrame(columns=["Versenyszám","Idő","Gender"])

# ====== Események + formátumok ======
event_time_formats = {...}  # változatlanul hagyhatjuk, lásd korábbi kód
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

# ====== Nem választó ======
nem_val = st.radio("Válaszd ki a nemet:", ["Férfi", "Nő"], horizontal=True)
st.session_state.gender = "Man" if nem_val == "Férfi" else "Woman"

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
                    "Gender": st.session_state.gender
                })
        if rows:
            add_df = pd.DataFrame(rows)
            # Egy versenyszámhoz csak egy idő maradjon
            st.session_state.idok = pd.concat([st.session_state.idok, add_df], ignore_index=True)
            st.session_state.idok.drop_duplicates(subset=["Versenyszám","Gender"], keep="last", inplace=True)
            st.success(f"Hozzáadva {len(add_df)} sor (felülírás, ha volt már ilyen versenyszám).")

st.divider()

# ====== IDŐK tábla + törlés ======
st.subheader("Összesített IDŐK táblázat")

if st.session_state.idok.empty:
    st.info("Még nincs adat a táblában.")
else:
    to_show = st.session_state.idok.copy().reset_index().rename(columns={"index": "Sorszám"})
    to_show["Törlés"] = False

    edited = st.data_editor(
        to_show,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Törlés": st.column_config.CheckboxColumn("Törlés", help="Jelöld be és nyomd meg a Törlés gombot"),
        },
        disabled=["Sorszám"],
        num_rows="fixed"
    )

    if st.button("🗑️ Kijelöltek törlése"):
        to_delete_idx = edited.loc[edited["Törlés"] == True, "Sorszám"].tolist()
        if to_delete_idx:
            st.session_state.idok.drop(index=to_delete_idx, inplace=True, errors="ignore")
            st.session_state.idok.reset_index(drop=True, inplace=True)
            st.success(f"Törölve: {len(to_delete_idx)} sor.")
            st.rerun()

# ====== Gomb a második oldalra ======
st.divider()
if st.button("➡️ Tovább az AdatElemzés oldalra"):
    st.switch_page("pages/02_AdatElemzes.py")
