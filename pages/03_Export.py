import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO

# Emojihoz font
pdfmetrics.registerFont(TTFont("DejaVuSans", "DejaVuSans.ttf"))

st.set_page_config(page_title="Export", page_icon="📄", layout="centered")
st.title("📄 Export futóprofil")

# --- Inputok ---
name = st.text_input("Név")
age = st.number_input("Életkor", min_value=18, max_value=100, step=1, value=18)
gender = st.session_state.get("gender", "Man")

gender_hu = "Férfi" if gender == "Man" else "Nő"

work = st.session_state.get("wa_results")
cs_result = st.session_state.get("cs_result")

if st.button("📥 PDF exportálása") and work is not None and not work.empty:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 2*cm

    # ---------------- Profil ----------------
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2*cm, y, "Profil")
    y -= 1*cm

    c.setFillColorRGB(0.95, 0.97, 1)  # halvány kék
    c.roundRect(2*cm, y-2.5*cm, width-4*cm, 2*cm, 12, stroke=0, fill=1)
    c.setFillColorRGB(0,0,0)
    c.setFont("Helvetica", 11)
    c.drawString(2.5*cm, y-1.2*cm,
        f"Név: {name}    Életkor: {age} év    Nem: {gender_hu}")
    y -= 3.5*cm

    # ---------------- WA pontok ----------------
    best = work.loc[work["WA pont"].idxmax()]
    worst = work.loc[work["WA pont"].idxmin()]
    avg = work["WA pont"].mean()

    c.setFont("Helvetica-Bold", 14)
    c.drawString(2*cm, y, "Eredmények és WA pontszámok")
    y -= 1*cm

    box_height = 6*cm
    c.setFillColorRGB(0.96,0.96,0.96)
    c.roundRect(2*cm, y-box_height, width-4*cm, box_height, 12, stroke=0, fill=1)

    row_height = 1.5*cm
    col_width = (width-4*cm)/3
    cur_y = y-1*cm
    for i, (_, row) in enumerate(work.iterrows()):
        col = i % 3
        if col == 0 and i>0:
            cur_y -= row_height
        x0 = 2*cm + col*col_width

        if row["WA pont"] == work["WA pont"].max():
            c.setFillColorRGB(1,0.95,0.75)  # arany
        else:
            c.setFillColorRGB(1,1,1)
        c.roundRect(x0+0.2*cm, cur_y-1.0*cm, col_width-0.4*cm, 1.0*cm, 6, stroke=1, fill=1)

        c.setFillColorRGB(0,0,0)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(x0+col_width/2, cur_y-0.4*cm, f"{row['Versenyszám']} ({row['Idő']})")
        c.setFont("DejaVuSans", 8)
        c.drawCentredString(x0+col_width/2, cur_y-0.7*cm, f"🏅 {int(row['WA pont'])} p")

    # szöveges összegzés emojikkal
    c.setFont("DejaVuSans", 10)
    c.drawString(2*cm, y-box_height-0.8*cm, f"🥇 Legjobb: {best['Versenyszám']} {best['Idő']} ({int(best['WA pont'])} p)")
    c.drawString(2*cm, y-box_height-1.5*cm, f"📊 Átlagos: {int(avg)} p")
    c.drawString(2*cm, y-box_height-2.2*cm, f"🐢 Legalacsonyabb: {worst['Versenyszám']} {worst['Idő']} ({int(worst['WA pont'])} p)")

    y -= (box_height+3*cm)

    # ---------------- Kritikus Sebesség ----------------
    if cs_result:
        c.setFont("Helvetica-Bold", 14)
        c.drawString(2*cm, y, "Critical Speed")
        y -= 1*cm

        c.setFillColorRGB(0.9,1,0.9)
        c.roundRect(2*cm, y-2*cm, width-4*cm, 1.5*cm, 12, stroke=0, fill=1)
        c.setFillColorRGB(0,0,0)
        c.setFont("Helvetica", 11)
        c.drawString(2.5*cm, y-1.0*cm, f"Kritikus tempó: {cs_result['pace_str']}   CS: {cs_result['cs']:.2f} m/s   D′: {cs_result['dprime']:.0f} m")

        # grafikon keretben
        if "plot_png" in cs_result:
            y -= 7*cm
            c.setFillColorRGB(1,1,1)
            c.roundRect(2*cm, y, width-4*cm, 6*cm, 12, stroke=1, fill=1)
            img = ImageReader(BytesIO(cs_result["plot_png"]))
            c.drawImage(img, 2*cm, y, width-4*cm, 6*cm, preserveAspectRatio=True, mask='auto')

    # ---------------- Mentés ----------------
    c.save()
    buffer.seek(0)

    st.download_button(
        "📥 PDF letöltése",
        data=buffer,
        file_name="runner_profile.pdf",
        mime="application/pdf"
    )
