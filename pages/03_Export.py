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

    # --- Fejléc ---
    c.setFont("Helvetica-Bold", 18)
    c.drawString(2*cm, height - 2*cm, "Runner Profile")
    c.setFont("Helvetica", 12)
    c.drawString(2*cm, height - 3*cm, f"Név: {name}")
    c.drawString(2*cm, height - 4*cm, f"Életkor: {age}")
    c.drawString(2*cm, height - 5*cm, f"Nem: {gender}")

    y = height - 7*cm

    # --- Kritikus Sebesség kártya ---
    if cs_result:
        c.setFillColorRGB(0.9, 1, 0.9)  # világoszöld háttér
        c.roundRect(2*cm, y, width-4*cm, 3*cm, 10, stroke=1, fill=1)
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(2.5*cm, y + 2*cm, f"Kritikus tempó: {cs_result['pace_str']}")
        c.setFont("Helvetica", 10)
        c.drawString(2.5*cm, y + 1.3*cm, f"CS: {cs_result['cs']:.2f} m/s, D′: {cs_result['dprime']:.0f} m")

        # grafikon
        if "plot_png" in cs_result:
            img = ImageReader(BytesIO(cs_result["plot_png"]))
            c.drawImage(img, width/2, y - 1*cm, width=7*cm, height=4*cm, preserveAspectRatio=True)

        y -= 6*cm

    # --- WA eredmények box ---
    if idok is not None and not idok.empty:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2*cm, y, "Eredmények és WA pontszámok:")
        y -= 0.8*cm

        row_height = 2*cm
        col_width = (width - 4*cm) / 3
        padding = 0.2*cm

        n_rows = int(np.ceil(len(idok) / 3))
        box_height = n_rows * row_height + padding
        c.setFillColorRGB(0.96, 0.96, 0.96)  # halványszürke háttér
        c.roundRect(2*cm, y - box_height, width-4*cm, box_height, 10, stroke=0, fill=1)
        c.setFillColorRGB(0, 0, 0)

        cur_y = y - padding
        for i, (_, row) in enumerate(idok.iterrows()):
            col = i % 3
            if col == 0 and i > 0:
                cur_y -= row_height
            x0 = 2*cm + col*col_width
            c.setFillColorRGB(1, 1, 1)
            c.roundRect(x0 + padding, cur_y - row_height + padding,
                        col_width - 2*padding, row_height - 2*padding,
                        6, stroke=1, fill=1)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", 9)
            c.drawCentredString(x0 + col_width/2, cur_y - 0.7*cm,
                                f"{row['Versenyszám']}")
            c.setFont("Helvetica", 8)
            c.drawCentredString(x0 + col_width/2, cur_y - 1.2*cm,
                                f"{row['Idő']} — {int(row.get('WA pont',0))} p")

        y = cur_y - row_height - 1*cm

    c.save()
    buffer.seek(0)

    st.download_button(
        "📥 PDF letöltése",
        data=buffer,
        file_name="runner_profile.pdf",
        mime="application/pdf"
    )
