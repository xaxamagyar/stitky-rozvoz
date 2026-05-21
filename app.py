import streamlit as st
from reportlab.lib.pagesizes import a4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io

st.set_page_config(page_title="Generátor štítků", layout="wide")

st.title("📦 Generátor balíkových štítků (A4 - 2x7)")
st.write("Zadejte údaje, přidejte balíky do seznamu a následně vygenerujte PDF pro tisk.")

# Inicializace stavu aplikace (paměť pro uložené štítky)
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
    if name or order_num:  # Aspoň něco musíme vědět
        # Pokud zadáš více balíků, vytvoříme pro každý samostatný štítek s označením X/Y
        for i in range(1, count + 1):
            st.session_state.labels.append({
                "name": name,
                "order_num": order_num,
                "note": note,
                "package_info": f"Balík: {i}/{count}" if count > 1 else "Balík: 1/1"
            })
        st.success(f"Přidáno {count} štítků.")
    else:
        st.error("Vyplňte prosím aspoň jméno nebo číslo objednávky.")

# --- PŘEHLED ZADANÝCH ŠTÍTKŮ ---
if st.session_state.labels:
    st.subheader(f"📋 Seznam štítků k tisku ({len(st.session_state.labels)} ks)")
    
    # Zobrazení tabulky pro kontrolu
    st.dataframe(st.session_state.labels)
    
    if st.button("🗑️ Vymazat celý seznam"):
        st.session_state.labels = []
        st.rerun()

    # --- GENEROVÁNÍ PDF ---
    st.subheader("🖨️ Tisk")
    
    # Tlačítko pro generování spustíme až v paměti
    pdf_buffer = io.BytesIO()
    
    # Nastavení dokumentu: A4 má rozměry 595 x 842 bodů (points)
    # Okraje dáme minimální (např. 15 bodů / cca 5mm), abychom maximálně využili plochu
    margin = 15
    doc = SimpleDocTemplate(
        pdf_buffer, 
        pagesize=a4,
        leftMargin=margin, 
        rightMargin=margin, 
        topMargin=margin, 
        bottomMargin=margin
    )
    
    styles = getSampleStyleSheet()
    # Definice vlastních stylů pro text uvnitř štítku
    style_name = ParagraphStyle('Name', parent=styles['Normal'], fontSize=12, leading=14, fontName="Helvetica-Bold")
    style_order = ParagraphStyle('Order', parent=styles['Normal'], fontSize=10, leading=12, fontName="Helvetica")
    style_note = ParagraphStyle('Note', parent=styles['Normal'], fontSize=8, leading=10, fontName="Helvetica-Oblique", textColor=colors.gray)
    style_pkg = ParagraphStyle('Pkg', parent=styles['Normal'], fontSize=9, leading=11, fontName="Helvetica", alignment=2) # alignment 2 = vpravo
    
    story = []
    
    # Příprava mřížky pro 2 sloupce a 7 řádků (celkem 14 štítků na stránku)
    grid_data = []
    current_row = []
    
    for label in st.session_state.labels:
        # Vytvoření obsahu jednoho štítku
        label_content = [
            Paragraph(f"<b>Příjemce:</b> {label['name']}", style_name),
            Spacer(1, 4),
            Paragraph(f"<b>Objednávka:</b> {label['order_num']}", style_order),
            Spacer(1, 4),
            Paragraph(f"<b>Poznámka:</b> {label['note']}", style_note),
            Spacer(1, 8),
            Paragraph(label['package_info'], style_pkg)
        ]
        
        current_row.append(label_content)
        
        # Jakmile máme 2 štítky, uzavřeme řádek
        if len(current_row) == 2:
            grid_data.append(current_row)
            current_row = []
            
    # Pokud na konci zbyl jeden osamocený štítek, doplníme prázdnou buňku
    if current_row:
        current_row.append("")
        grid_data.append(current_row)
        
    # Pokud máme data, spočítáme přesné rozměry pro tisk na A4
    if grid_data:
        # Šířka stránky po odečtení okrajů / 2 sloupce
        col_width = (595 - (2 * margin)) / 2
        # Výška stránky po odečtení okrajů / 7 řádků (cca 116 bodů na štítek)
        row_height = (842 - (2 * margin)) / 7
        
        # Vytvoření tabulky
        # Abychom simulovali mřížku 2x7 na každé stránce, musíme reportlabu říct výšky řádků
        row_heights = [row_height] * len(grid_data)
        
        t = Table(grid_data, colWidths=[col_width, col_width], rowHeights=row_heights)
        
        # Styl tabulky - ohraničení pro snadné stříhání/trhání (šedá tenká čára)
        t.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ]))
        
        story.append(t)
        doc.build(story)
        
        # Nabídnutí souboru ke stažení
        pdf_data = pdf_buffer.getvalue()
        st.download_button(
            label="📥 Stáhnout PDF se štítky",
            data=pdf_data,
            file_name="stitky.pdf",
            mime="application/pdf"
        )
else:
    st.info("Seznam je prázdný. Zadejte data výše.")