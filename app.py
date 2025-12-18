import streamlit as st
import sqlite3
import qrcode
from PIL import Image
import os
import io

# Databas (delad för alla användare online)
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

# CSS med Lora-typsnitt och snyggt mörkt tema
css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Lora:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Lora', serif !important;
    color: #E0E0E0;
}
.stApp {
    background-color: #121212;
}
.main > div {
    background-color: rgba(30, 30, 30, 0.6);
    border-radius: 18px;
    padding: 30px;
    margin: 20px;
}
h1, h2, h3, h4 {
    color: #FFFFFF;
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
    background-color: rgba(50, 50, 50, 0.8);
    color: #E0E0E0;
}
.stExpander {
    background-color: rgba(40, 40, 40, 0.6);
    border: 1px solid #4B0082;
    border-radius: 14px;
}
.stSidebar {
    background-color: rgba(20, 20, 20, 0.95);
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

# Titel
st.markdown("<h1 style='text-align: center;'>📦 Ordna Reda</h1>", unsafe_allow_html=True)
st.markdown("---")

# Sidebar – bara meny, inga länkar
st.sidebar.markdown("---")

# QR-direktvisning med utskriftssida
query_params = st.query_params
if "box" in query_params:
    try:
        box_id = int(query_params["box"])
        c.execute("SELECT name FROM boxes WHERE id=?", (box_id,))
        box = c.fetchone()
        if box:
            st.markdown(f"<h1 style='text-align: center;'>📦 {box[0]}</h1>", unsafe_allow_html=True)
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
    # Normal meny
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
                with st.expander(f"📦 {box_name} – {item_count} saker", expanded=False):
                    new_name = st.text_input("Nytt namn", value=box_name, key=f"name_{box_id}")
                    if st.button("Uppdatera namn", key=f"upd_{box_id}"):
                        c.execute("UPDATE boxes SET name=? WHERE id=?", (new_name, box_id))
                        conn.commit()
                        st.success("Namn uppdaterat!")

                    items = get_items(box_id)
                    if items:
                        for item in items:
                            item_id, _, desc, img_path = item
                            col1, col2 = st.columns([4, 1])
                            with col1:
                                st.write(f"• {desc}")
                            with col2:
                                if st.button("🗑️", key=f"del_{item_id}"):
                                    c.execute("DELETE FROM items WHERE id=?", (item_id,))
                                    conn.commit()
                                    st.success("Borttaget!")
                                    st.rerun()
                            if img_path:
                                st.image(img_path, width=700)
                    else:
                        st.info("Inga saker i lådan ännu.")

                    st.subheader("Lägg till innehåll")
                    new_desc = st.text_input("Beskrivning", key=f"desc_{box_id}")
                    uploaded = st.file_uploader("Bild (valfritt)", type=["jpg","png","jpeg","gif"], key=f"file_{box_id}")
                    if st.button("Lägg till", key=f"add_{box_id}"):
                        if not new_desc.strip():
                            st.warning("Skriv en beskrivning först!")
                        else:
                            img_path = None
                            if uploaded:
                                os.makedirs("images", exist_ok=True)
                                img_path = f"images/{uploaded.name}"
                                with open(img_path, "wb") as f:
                                    f.write(uploaded.getbuffer())
                            c.execute("INSERT INTO items (box_id, description, image_path) VALUES (?, ?, ?)",
                                      (box_id, new_desc, img_path))
                            conn.commit()
                            st.success(f"Tillagt: {new_desc}")
                            st.rerun()

                    st.subheader("Generera QR-kod")
                    base_url = st.text_input("Appens URL (kopiera från webbläsarens adressfält)", value="", key=f"url_{box_id}")
                    if not base_url:
                        base_url = "https://din-app.streamlit.app"  # fallback
                    if st.button("Skapa QR-kod", key=f"qr_{box_id}"):
                        url = f"{base_url.rstrip('/')}/?box={box_id}"
                        qr = qrcode.QRCode(version=1, box_size=10, border=4)
                        qr.add_data(url)
                        qr.make(fit=True)
                        pil_img = qr.make_image(fill_color="white", back_color="#4B0082")
                        buf = io.BytesIO()
                        pil_img.save(buf, format="PNG")
                        buf.seek(0)
                        st.image(buf, caption="Skriv ut och klistra på lådan!")
                        buf.seek(0)
                        st.download_button("Ladda ner QR-kod", buf, f"QR_{box_name.replace(' ', '_')}.png", "image/png")

                    if st.button(f"🗑️ Ta bort hela lådan '{box_name}'", key=f"delbox_{box_id}"):
                        c.execute("DELETE FROM items WHERE box_id=?", (box_id,))
                        c.execute("DELETE FROM boxes WHERE id=?", (box_id,))
                        conn.commit()
                        st.success("Lådan borttagen!")
                        st.rerun()

    elif option == "Sök i innehåll":
        st.header("🔍 Sök i allt innehåll")
        term = st.text_input("Sök efter något (t.ex. julpynt, foton)")
        if term:
            c.execute("""SELECT b.name, i.description FROM items i
                         JOIN boxes b ON i.box_id = b.id
                         WHERE i.description LIKE ?""", (f"%{term}%",))
            results = c.fetchall()
            if results:
                st.success(f"Hittade {len(results)} träffar:")
                for r in results:
                    st.write(f"• **{r[1]}** finns i låda **{r[0]}**")
            else:
                st.info("Inget hittades.")

conn.close()
