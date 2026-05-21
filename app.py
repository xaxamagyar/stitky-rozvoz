import streamlit as st
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import os

# --- REGISTRACE ČESKÉHO FONTU (ARIAL) ---
FONT_REGISTRATION_SUCCESS = False
try:
    if os.path.exists("ARIAL.TTF") and os.path.exists("ARIALBD.TTF"):
        pdfmetrics.registerFont(TTFont('ArialCustom', 'ARIAL.TTF'))
        pdfmetrics.registerFont(TTFont('ArialCustom-Bold', 'ARIALBD.TTF'))
        FONT_REGISTRATION_SUCCESS = True
except Exception as e:
    st.error(f"Nepodařilo se načíst nahrané fonty Arial: {e}")

FONT_REGULAR = 'ArialCustom' if FONT_REGISTRATION_SUCCESS else 'Helvetica'
FONT_BOLD = 'ArialCustom-Bold' if FONT_REGISTRATION_SUCCESS else 'Helvetica-Bold'

# Přesné rozměry A4 v bodech
A4_SIZE = (595.27, 841.89)

st.set_page_config(page_title="Generátor štítků", layout="wide")

st.title("📦 Generátor balíkových štítků (A4 - 2x7)")
st.write("Zadejte údaje, přidejte balíky do seznamu a následně vygenerujte PDF pro tisk.")

if "labels" not in st.session_state:
    st.session_state.labels = []

# --- FORMULÁŘ PRO ZADÁNÍ ---
st.subheader("📝 Nový štítek")
with st.form("label_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Jméno / Firma")
        order_num = st.text_input("Číslo objednávky")
    with col2:
        note = st.text_area("Poznámka", max_chars=100)
        count = st.number_input("Počet balíků (štítků)", min_value=1, value=1, step=1)
    
    submit = st.form_submit_button("➕ Přidat do seznamu")

if submit:
    if name or order_num:
        for i in range(1, count + 1):
            st.session_state.labels.append({
                "name": name,
                "order_num": order_num,
                "note": note,
                "package_info": f"BALÍK: {i}/{count}" if count > 1 else "BALÍK: 1/1"
            })
        st.success(f"Přidáno {count} štítků.")
    else:
        st.error("Vyplňte prosím aspoň jméno nebo číslo objednávky.")

# --- PŘEHLED ZADANÝCH ŠTÍTKŮ ---
if st.session_state.labels:
    st.subheader(f"📋 Seznam štítků k tisku ({len(st.session_state.labels)} ks)")
    st.dataframe(st.session_state.labels)
    
    if st.button("🗑️ Vymazat celý seznam"):
        st.session_state.labels = []
        st.rerun()

    # --- GENEROVÁNÍ PDF ---
    st.subheader("🖨️ Tisk")
    
    pdf_buffer = io.BytesIO()
    
    # Zmenšíme okraj stránky na 10 bodů (cca 3.5 mm), abychom dali tabulce více místa pro 7 řádků
    margin = 10
    doc = SimpleDocTemplate(
        pdf_buffer, 
        pagesize=A4_SIZE,
        leftMargin=margin, 
        rightMargin=margin, 
        topMargin=margin, 
        bottomMargin=margin
    )
    
    styles = getSampleStyleSheet()
    
    # --- ÚPRAVA VELIKOSTÍ PÍSMA ---
    # Jméno a objednávka jsou menší, aby nepřetékaly z okénka
    style_name = ParagraphStyle('Name', parent=styles['Normal'], fontSize=11, leading=13, fontName=FONT_BOLD)
    style_order = ParagraphStyle('Order', parent=styles['Normal'], fontSize=10, leading=12, fontName=FONT_REGULAR)
    style_note = ParagraphStyle('Note', parent=styles['Normal'], fontSize=9, leading=11, fontName=FONT_REGULAR, textColor=colors.HexColor('#555555'))
    
    # Informace o balíku je obrovská a výrazná (velikost 20)
    style_pkg = ParagraphStyle('Pkg', parent=styles['Normal'], fontSize=20, leading=22, fontName=FONT_BOLD, alignment=2)
    
    story = []
    grid_data = []
    current_row = []
    
    for label in st.session_state.labels:
        label_content = [
            Paragraph(f"<b>Příjemce:</b> {label['name']}", style_name),
            Spacer(1, 3),
            Paragraph(f"<b>Objednávka:</b> {label['order_num']}", style_order),
            Spacer(1, 3),
            Paragraph(f"<b>Poznámka:</b> {label['note']}" if label['note'] else "", style_note),
            Spacer(1, 10), # Mezera před velkým číslem balíku
            Paragraph(label['package_info'], style_pkg)
        ]
        
        current_row.append(label_content)
        
        if len(current_row) == 2:
            grid_data.append(current_row)
            current_row = []
            
    if current_row:
        current_row.append("")
        grid_data.append(current_row)
        
    if grid_data:
        # Výpočet rozměrů buněk tak, aby se jich na výšku vešlo přesně 7
        col_width = (595.27 - (2 * margin)) / 2
        row_height = (841.89 - (2 * margin)) / 7
        
        row_heights = [row_height] * len(grid_data)
        
        t = Table(grid_data, colWidths=[col_width, col_width], rowHeights=row_heights)
        
        # Snížili jsme TOP a BOTTOM padding na 8, aby text netlačil řádek na další stránku
        t.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#999999')),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ]))
        
        story.append(t)
        doc.build(story)
        
        pdf_data = pdf_buffer.getvalue()
        st.download_button(
            label="📥 Stáhnout PDF se štítky",
            data=pdf_data,
            file_name="stitky_opraveno.pdf",
            mime="application/pdf"
        )
else:
    st.info("Seznam je prázdný. Zadejte data výše.")