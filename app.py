import streamlit as st
import sqlite3
import qrcode
from PIL import Image
import os
import io
import hashlib

# Funktion för att hasha lösenord (enkelt och säkert nog för detta)
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Databas med användare
conn = sqlite3.connect('ordna_reda_private.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    password_hash TEXT UNIQUE
)''')
c.execute('''CREATE TABLE IF NOT EXISTS boxes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
)''')
c.execute('''CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    box_id INTEGER,
    description TEXT,
    image_path TEXT,
    FOREIGN KEY(box_id) REFERENCES boxes(id)
)''')
conn.commit()

# Session state för inloggning
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'open_box' not in st.session_state:
    st.session_state.open_box = None

# Inloggning / välj lösenord
st.markdown("<h1 style='text-align: center; color: #2C3E50;'>Välkommen in i ditt förråd</h1>", unsafe_allow_html=True)

if st.session_state.user_id is None:
    st.markdown("### Ange ditt privata lösenord för att komma åt dina lådor")
    st.info("Välj ett lösenord som bara du känner till. Det sparas säkert och används bara för att skilja dina lådor från andras.")
    password = st.text_input("Ditt lösenord", type="password", help="Du kan använda samma lösenord varje gång du kommer hit.")
    if st.button("Fortsätt"):
        if password.strip() == "":
            st.error("Skriv in ett lösenord först!")
        else:
            hash_pw = hash_password(password)
            c.execute("SELECT id FROM users WHERE password_hash = ?", (hash_pw,))
            user = c.fetchone()
            if user:
                st.session_state.user_id = user[0]
                st.success("Välkommen tillbaka!")
                st.rerun()
            else:
                c.execute("INSERT INTO users (password_hash) VALUES (?)", (hash_pw,))
                conn.commit()
                c.execute("SELECT id FROM users WHERE password_hash = ?", (hash_pw,))
                new_user = c.fetchone()
                st.session_state.user_id = new_user[0]
                st.success("Nytt förråd skapat! Välkommen!")
                st.rerun()
else:
    # Utloggning
    if st.sidebar.button("Byt användare / logga ut"):
        st.session_state.user_id = None
        st.session_state.open_box = None
        st.rerun()

    # CSS
    css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Lora:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Lora', serif !important; color: #333333; }
    .stApp { background-color: #FFFFFF; }
    .main > div { background-color: #F8F9FA; border-radius: 18px; padding: 30px; margin: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    h1, h2, h3, h4 { color: #2C3E50; }
    .stButton > button { background-color: #4B0082; color: white; border: none; border-radius: 12px; padding: 14px 28px; }
    .stButton > button:hover { background-color: #6B23B2; }
    .stTextInput > div > div > input, .stFileUploader > div > div { background-color: #FFFFFF; color: #333333; border: 1px solid #DDDDDD; }
    .stExpander { background-color: #FFFFFF; border: 1px solid #4B0082; border-radius: 14px; }
    .stSidebar { background-color: #F0F2F6; }
    @media print { .no-print { display: none; } body { background: white; color: black; } h1, h2 { color: black; } img { max-width: 100%; page-break-inside: avoid; } }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

    st.markdown("---")

    def get_user_boxes():
        c.execute("SELECT id, name FROM boxes WHERE user_id = ?", (st.session_state.user_id,))
        return c.fetchall()

    def get_user_items(box_id):
        c.execute("SELECT id, description, image_path FROM items WHERE box_id = ?", (box_id,))
        return c.fetchall()

    # QR-direktvisning (privat länk med user_id och box_id)
    query_params = st.query_params
    if "box" in query_params:
        try:
            box_id = int(query_params["box"])
            c.execute("SELECT name, user_id FROM boxes WHERE id = ?", (box_id,))
            box = c.fetchone()
            if box and box[1] == st.session_state.user_id:
                st.markdown(f"<h1 style='text-align: center; color: #2C3E50;'>{box[0]}</h1>", unsafe_allow_html=True)
                st.markdown("<div style='text-align: center; margin-bottom: 30px;'>", unsafe_allow_html=True)
                if st.button("🖨️ Skriv ut denna sida"):
                    st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
                items = get_user_items(box_id)
                if items:
                    for item in items:
                        st.markdown(f"<h2>{item[1]}</h2>", unsafe_allow_html=True)
                        if item[2]:
                            st.image(item[2], use_column_width=True)
                        st.markdown("---")
                else:
                    st.info("Denna låda är tom.")
            else:
                st.error("Lådan finns inte eller tillhör inte dig.")
        except:
            st.error("Ogiltig länk.")
    else:
        option = st.sidebar.selectbox("Välj funktion", ["Skapa låda", "Visa och redigera lådor", "Sök i innehåll"])

        if option == "Skapa låda":
            st.header("Skapa ny låda")
            name = st.text_input("Lådans namn (t.ex. Sommarminnen)")
            if st.button("Skapa låda") and name:
                c.execute("INSERT INTO boxes (user_id, name) VALUES (?, ?)", (st.session_state.user_id, name))
                conn.commit()
                st.success(f"Låda '{name}' skapad!")
                st.rerun()

        elif option == "Visa och redigera lådor":
            st.header("Dina lådor")
            boxes = get_user_boxes()
            if not boxes:
                st.info("Inga lådor ännu – skapa en i menyn till vänster!")
            else:
                for box in boxes:
                    box_id, box_name = box
                    item_count = len(get_user_items(box_id))
                    expanded = (st.session_state.open_box == box_id)
                    with st.expander(f"{box_name} – {item_count} saker", expanded=expanded):
                        st.session_state.open_box = box_id

                        new_name = st.text_input("Nytt namn", value=box_name, key=f"name_{box_id}")
                        if st.button("Uppdatera namn", key=f"upd_{box_id}"):
                            c.execute("UPDATE boxes SET name=? WHERE id=?", (new_name, box_id))
                            conn.commit()
                            st.success("Namn uppdaterat!")
                            st.rerun()

                        items = get_user_items(box_id)
                        if items:
                            for item in items:
                                item_id, desc, img_path = item
                                col1, col2 = st.columns([4, 1])
                                with col1:
                                    st.write(f"• {desc}")
                                with col2:
                                    if st.button("🗑️", key=f"del_item_{item_id}"):
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
                        uploaded = st.file_uploader("Bild (valfritt)", type=["jpg","png","jpeg","gif"], key=f"upload_{box_id}")
                        if st.button("Lägg till", key=f"add_{box_id}"):
                            if not new_desc.strip():
                                st.warning("Skriv en beskrivning!")
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
                        base_url = st.text_input("Appens URL", value="https://ordnareda-app-mnre2qovwqste4auga7bny.streamlit.app", key=f"url_{box_id}")
                        if st.button("Skapa QR-kod", key=f"qr_{box_id}"):
                            url = f"{base_url.rstrip('/')}/?box={box_id}"
                            qr = qrcode.QRCode(version=1, box_size=10, border=4)
                            qr.add_data(url)
                            qr.make(fit=True)
                            pil_img = qr.make_image(fill_color="black", back_color="white")
                            buf = io.BytesIO()
                            pil_img.save(buf, format="PNG")
                            buf.seek(0)
                            st.image(buf, caption="Skriv ut och klistra på lådan!")
                            buf.seek(0)
                            st.download_button("Ladda ner QR-kod", buf, f"QR_{box_name.replace(' ', '_')}.png", "image/png", key=f"dl_{box_id}")

                        if st.button(f"🗑️ Ta bort hela lådan '{box_name}'", key=f"delbox_{box_id}"):
                            c.execute("DELETE FROM items WHERE box_id=?", (box_id,))
                            c.execute("DELETE FROM boxes WHERE id=?", (box_id,))
                            conn.commit()
                            st.success("Lådan borttagen!")
                            st.session_state.open_box = None
                            st.rerun()

        elif option == "Sök i innehåll":
            st.header("🔍 Sök i ditt innehåll")
            term = st.text_input("Sök efter något (t.ex. julpynt, foton)")
            if term:
                c.execute("""SELECT b.name, i.description FROM items i
                             JOIN boxes b ON i.box_id = b.id
                             WHERE b.user_id = ? AND i.description LIKE ?""", 
                             (st.session_state.user_id, f"%{term}%"))
                results = c.fetchall()
                if results:
                    st.success(f"Hittade {len(results)} träffar:")
                    for r in results:
                        st.write(f"• **{r[1]}** finns i låda **{r[0]}**")
                else:
                    st.info("Inget hittades.")

conn.close()
