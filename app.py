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

A4_SIZE = (595.27, 841.89)

st.set_page_config(page_title="Generátor štítků", layout="wide")

st.title("📦 Generátor balíkových štítků (A4 - 2x7)")
st.write("Zadejte údaje, spravujte objednávky ve frontě a vygenerujte PDF pro tisk.")

# Inicializace paměti pro objednávky a režim editace
if "orders" not in st.session_state:
    st.session_state.orders = []
if "edit_index" not in st.session_state:
    st.session_state.edit_index = None

# --- FORMULÁŘ PRO ZADÁNÍ / EDITACI ---
is_editing = st.session_state.edit_index is not None

if is_editing:
    st.subheader("✏️ Upravit skupinu balíků / objednávku")
    edit_idx = st.session_state.edit_index
    current_order = st.session_state.orders[edit_idx]
    default_name = current_order["name"]
    default_order = current_order["order_num"]
    default_note = current_order["note"]
    default_count = current_order["count"]
else:
    st.subheader("📝 Nový štítek / skupina balíků")
    default_name = ""
    default_order = ""
    default_note = ""
    default_count = 1

with st.form("label_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Jméno / Firma", value=default_name)
        order_num = st.text_input("Číslo objednávky", value=default_order)
    with col2:
        note = st.text_area("Poznámka", value=default_note, max_chars=100)
        count = st.number_input("Počet balíků (štítků) pro tuto objednávku", min_value=1, value=default_count, step=1)
    
    btn_label = "💾 Uložit změny objednávky" if is_editing else "➕ Přidat do fronty"
    submit = st.form_submit_button(btn_label)

if submit:
    if name or order_num:
        if is_editing:
            # Přepis celé objednávky včetně možnosti změnit počet balíků
            st.session_state.orders[st.session_state.edit_index] = {
                "name": name,
                "order_num": order_num,
                "note": note,
                "count": count
            }
            st.session_state.edit_index = None
            st.success("Objednávka byla úspěšně upravena.")
            st.rerun()
        else:
            # Uložení jako jedna ucelená objednávka
            st.session_state.orders.append({
                "name": name,
                "order_num": order_num,
                "note": note,
                "count": count
            })
            st.success(f"Objednávka s {count} balíky byla přidána.")
            st.rerun()
    else:
        st.error("Vyplňte prosím aspoň jméno nebo číslo objednávky.")

if is_editing:
    if st.button("❌ Zrušit editaci"):
        st.session_state.edit_index = None
        st.rerun()

# --- PŘEHLED ZADANÝCH OBJEDNÁVEK ---
if st.session_state.orders:
    # Spočítáme celkový počet štítků napříč objednávkami
    total_labels = sum(order["count"] for order in st.session_state.orders)
    
    st.subheader(f"📋 Seznam objednávek ve frontě (Celkem {total_labels} štítků k tisku)")
    
    # Zobrazení přehledné tabulky
    st.dataframe(st.session_state.orders, use_container_width=True)
    
    # Ovládací prvky pro jednotlivé objednávky
    st.write("**Správa objednávek:**")
    for idx, order in enumerate(st.session_state.orders):
        col_text, col_edit, col_del = st.columns([6, 1, 1])
        with col_text:
            st.text(f"{idx + 1}. {order['name']} | Obj: {order['order_num']} | Počet balíků: {order['count']} ks")
        with col_edit:
            if st.button("✏️ Upravit vše", key=f"edit_{idx}"):
                st.session_state.edit_index = idx
                st.rerun()
        with col_del:
            if st.button("🗑️ Smazat", key=f"del_{idx}"):
                st.session_state.orders.pop(idx)
                if st.session_state.edit_index == idx:
                    st.session_state.edit_index = None
                st.rerun()

    st.write("---")
    if st.button("🗑️ Vymazat úplně celou frontu"):
        st.session_state.orders = []
        st.session_state.edit_index = None
        st.rerun()

    # --- GENEROVÁNÍ PDF ---
    st.subheader("🖨️ Tisk")
    
    pdf_buffer = io.BytesIO()
    
    PAGE_MARGIN = 0  
    COL_WIDTH = 595.27 / 2  
    ROW_HEIGHT = 117.5  
    
    doc = SimpleDocTemplate(
        pdf_buffer, 
        pagesize=A4_SIZE,
        leftMargin=PAGE_MARGIN, 
        rightMargin=PAGE_MARGIN, 
        topMargin=PAGE_MARGIN, 
        bottomMargin=PAGE_MARGIN
    )
    
    styles = getSampleStyleSheet()
    
    style_name = ParagraphStyle('Name', parent=styles['Normal'], fontSize=16, leading=19, fontName=FONT_BOLD)
    style_order = ParagraphStyle('Order', parent=styles['Normal'], fontSize=11, leading=13, fontName=FONT_REGULAR)
    style_note = ParagraphStyle('Note', parent=styles['Normal'], fontSize=10, leading=12, fontName=FONT_REGULAR, textColor=colors.HexColor('#444444'))
    style_pkg = ParagraphStyle('Pkg', parent=styles['Normal'], fontSize=22, leading=24, fontName=FONT_BOLD, alignment=2)
    
    story = []
    grid_data = []
    current_row = []
    
    # Rozbalení skupin na jednotlivé štítky až těsně před generováním PDF
    for order in st.session_state.orders:
        for i in range(1, order["count"] + 1):
            pkg_info = f"BALÍK: {i}/{order['count']}" if order["count"] > 1 else "BALÍK: 1/1"
            
            label_content = [
                Paragraph(f"<b>Příjemce:</b> {order['name']}", style_name),
                Spacer(1, 2),
                Paragraph(f"<b>Objednávka:</b> {order['order_num']}", style_order),
                Spacer(1, 2),
                Paragraph(f"<b>Poznámka:</b> {order['note']}" if order['note'] else "", style_note),
                Spacer(1, 4), 
                Paragraph(pkg_info, style_pkg)
            ]
            
            current_row.append(label_content)
            
            if len(current_row) == 2:
                grid_data.append(current_row)
                current_row = []
                
    if current_row:
        current_row.append("")
        grid_data.append(current_row)
        
    if grid_data:
        row_heights = [ROW_HEIGHT] * len(grid_data)
        
        t = Table(grid_data, colWidths=[COL_WIDTH, COL_WIDTH], rowHeights=row_heights)
        
        t.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')), 
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            
            ('LEFTPADDING', (0,0), (0,-1), 18),
            ('RIGHTPADDING', (0,0), (0,-1), 10),
            
            ('LEFTPADDING', (1,0), (1,-1), 10),
            ('RIGHTPADDING', (1,0), (1,-1), 18),
        ]))
        
        story.append(t)
        doc.build(story)
        
        pdf_data = pdf_buffer.getvalue()
        st.download_button(
            label="📥 Stáhnout PDF se štítky",
            data=pdf_data,
            file_name="stitky_kompletni.pdf",
            mime="application/pdf"
        )
else:
    st.info("Fronta je prázdná. Zadejte novou objednávku výše.")