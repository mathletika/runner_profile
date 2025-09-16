import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from io import BytesIO
import numpy as np

st.set_page_config(page_title="Export", page_icon="📄", layout="centered")
st.title("📄 Export futóprofil")

# --- Inputok ---
name = st.text_input("Név")
age = st.number_input("Életkor", min_value=5, max_value=100, step=1)
gender = st.session_state.get("gender", "Man")

idok = st.session_state.get("idok")
cs_result = st.session_state.get("cs_result")

if st.button("📥 PDF exportálása"):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 2*cm

    # ---------------- Profil box ----------------
    c.setFillColorRGB(0.95, 0.97, 1)  # halvány kék háttér
    c.roundRect(2*cm, y-3*cm, width-4*cm, 2.5*cm, 12, stroke=0, fill=1)
    c.setFillColorRGB(0,0,0)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2.5*cm, y-1.0*cm, "Profil")
    c.setFont("Helvetica", 11)
    c.drawString(2.5*cm, y-1.8*cm, f"Név: {name}")
    c.drawString(2.5*cm, y-2.5*cm, f"Életkor: {age} év   Nem: {gender}")

    y -= 4*cm

    # ---------------- WA pont box ----------------
    if idok is not None and not idok.empty:
        work = idok.copy()
        work = work.sort_values("Versenyszám")  # táv szerinti sorrend
        best = work.iloc[0]
        worst = work.iloc[-1]
        avg = work["WA pont"].mean()

        box_height = 6*cm
        c.setFillColorRGB(0.96,0.96,0.96)
        c.roundRect(2*cm, y-box_height, width-4*cm, box_height, 12, stroke=0, fill=1)
        c.setFillColorRGB(0,0,0)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(2.5*cm, y-1*cm, "Eredmények és WA pontszámok")

        # kártyák grid
        row_height = 1.5*cm
        col_width = (width-4*cm)/3
        cur_y = y-2*cm
        for i, (_, row) in enumerate(work.iterrows()):
            col = i % 3
            if col == 0 and i>0:
                cur_y -= row_height
            x0 = 2*cm + col*col_width

            # szín: arany, ha ez a legjobb
            if row["WA pont"] == work["WA pont"].max():
                c.setFillColorRGB(1,0.95,0.75)  # halvány arany
            else:
                c.setFillColorRGB(1,1,1)
            c.roundRect(x0+0.2*cm, cur_y-1.2*cm, col_width-0.4*cm, 1.2*cm, 6, stroke=1, fill=1)
            c.setFillColorRGB(0,0,0)
            c.setFont("Helvetica", 8)
            c.drawCentredString(x0+col_width/2, cur_y-0.5*cm,
                f"{row['Versenyszám']} ({row['Idő']}) — 🏅 {int(row['WA pont'])} p")

        # szöveges összegzés
        c.setFont("Helvetica", 10)
        c.drawString(2*cm, y-box_height-0.8*cm, f"🥇 Legjobb: {best['Versenyszám']} {best['Idő']} ({int(best['WA pont'])} p)")
        c.drawString(2*cm, y-box_height-1.5*cm, f"📊 Átlagos: {int(avg)} p")
        c.drawString(2*cm, y-box_height-2.2*cm, f"🐢 Legalacsonyabb: {worst['Versenyszám']} {worst['Idő']} ({int(worst['WA pont'])} p)")

        y -= (box_height+3*cm)

    # ---------------- Kritikus Sebesség ----------------
    if cs_result:
        c.setFillColorRGB(0.9,1,0.9)
        c.roundRect(2*cm, y-2.5*cm, width-4*cm, 2*cm, 12, stroke=0, fill=1)
        c.setFillColorRGB(0,0,0)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(2.5*cm, y-1.0*cm, f"Kritikus tempó: {cs_result['pace_str']}")
        c.setFont("Helvetica", 10)
        c.drawString(2.5*cm, y-1.8*cm, f"CS: {cs_result['cs']:.2f} m/s, D′: {cs_result['dprime']:.0f} m")

        # grafikon a zöld boxon kívül
        if "plot_png" in cs_result:
            img = ImageReader(BytesIO(cs_result["plot_png"]))
            c.drawImage(img, 2*cm, y-9*cm, width-4*cm, 6*cm, preserveAspectRatio=True)

    # ---------------- Mentés és letöltés ----------------
    c.save()
    buffer.seek(0)

    st.download_button(
        "📥 PDF letöltése",
        data=buffer,
        file_name="runner_profile.pdf",
        mime="application/pdf"
    )
