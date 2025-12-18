import streamlit as st
import sqlite3
import qrcode
from PIL import Image
import os
import io

# Databas
conn = sqlite3.connect('ordna_reda.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS boxes (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY AUTOINCREMENT, box_id INTEGER, description TEXT, image_path TEXT)''')
conn.commit()

def get_boxes():
    c.execute("SELECT * FROM boxes")
    return c.fetchall()

def get_items(box_id):
    c.execute("SELECT * FROM items WHERE box_id=?", (box_id,))
    return c.fetchall()

# CSS med vit bakgrund och ljus design
css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Lora:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Lora', serif !important;
    color: #333333;
}
.stApp {
    background-color: #FFFFFF;
}
.main > div {
    background-color: #F8F9FA;
    border-radius: 18px;
    padding: 30px;
    margin: 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}
h1, h2, h3, h4 {
    color: #2C3E50;
}
.stButton > button {
    background-color: #4B0082;
    color: white;
    border: none;
    border-radius: 12px;
    padding: 14px 28px;
}
.stButton > button:hover {
    background-color: #6B23B2;
}
.stTextInput > div > div > input, .stFileUploader > div > div {
    background-color: #FFFFFF;
    color: #333333;
    border: 1px solid #DDDDDD;
}
.stExpander {
    background-color: #FFFFFF;
    border: 1px solid #4B0082;
    border-radius: 14px;
}
.stSidebar {
    background-color: #F0F2F6;
}
@media print {
    .no-print { display: none; }
    body { background: white; color: black; }
    h1, h2 { color: black; }
    img { max-width: 100%; page-break-inside: avoid; }
}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# Ny titel
st.markdown("<h1 style='text-align: center; color: #2C3E50;'>Välkommen in i ditt förråd</h1>", unsafe_allow_html=True)
st.markdown("---")

# Sidebar – ren
st.sidebar.markdown("---")

# QR-direktvisning med utskriftssida
query_params = st.query_params
if "box" in query_params:
    try:
        box_id = int(query_params["box"])
        c.execute("SELECT name FROM boxes WHERE id=?", (box_id,))
        box = c.fetchone()
        if box:
            st.markdown(f"<h1 style='text-align: center; color: #2C3E50;'>{box[0]}</h1>", unsafe_allow_html=True)
            st.markdown("<div style='text-align: center; margin-bottom: 30px;'>", unsafe_allow_html=True)
            if st.button("🖨️ Skriv ut denna sida"):
                st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            items = get_items(box_id)
            if items:
                for item in items:
                    st.markdown(f"<h2>{item[2]}</h2>", unsafe_allow_html=True)
                    if item[3]:
                        st.image(item[3], use_column_width=True)
                    st.markdown("---")
            else:
                st.info("Denna låda är tom.")
        else:
            st.error("Lådan finns inte.")
    except:
        st.error("Ogiltig länk.")
else:
    option = st.sidebar.selectbox("Välj funktion", ["Skapa låda", "Visa och redigera lådor", "Sök i innehåll"])

    if option == "Skapa låda":
        st.header("Skapa ny låda")
        name = st.text_input("Lådans namn (t.ex. Sommarminnen)")
        if st.button("Skapa låda") and name:
            c.execute("INSERT INTO boxes (name) VALUES (?)", (name,))
            conn.commit()
            st.success(f"Låda '{name}' skapad!")

    elif option == "Visa och redigera lådor":
        st.header("Dina lådor")
        boxes = get_boxes()
        if not boxes:
            st.info("Inga lådor ännu – skapa en i menyn till vänster!")
        else:
            for box in boxes:
                box_id, box_name = box
                item_count = len(get_items(box_id))
                with st.expander(f"{box_name} – {item_count} saker", expanded=False):
                    new_name = st
