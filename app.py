import streamlit as st
import sqlite3
import qrcode
from PIL import Image
import os
import io
import base64

# Skapa mappar
for folder in ['images', 'logo', 'background']:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Base64-funktion för bakgrund
def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Uppladdning av bakgrund och logga
background_path = "background/mybackground.jpg"
logo_path = "logo/mylogo.png"

uploaded_bg = st.file_uploader("Ladda upp din bearbetade bakgrundsbild", type=["jpg", "jpeg", "png"], key="bg_upload")
if uploaded_bg:
    with open(background_path, "wb") as f:
        f.write(uploaded_bg.getbuffer())
    st.success("✅ Bakgrundsbild uppdaterad!")
    st.rerun()

uploaded_logo = st.file_uploader("Ladda upp din logga", type=["png", "jpg", "jpeg"], key="logo_upload")
if uploaded_logo:
    with open(logo_path, "wb") as f:
        f.write(uploaded_logo.getbuffer())
    st.success("✅ Logga uppdaterad!")
    st.rerun()

# CSS – samma tema som innan, men med extra stil för utskriftssidan
css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Lora:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Lora', serif;
    color: #E0E0E0;
}
.stApp {
    background-color: #000000;
}
"""

if os.path.exists(background_path):
    bin_str = get_base64(background_path)
    css += f"""
    .stApp {{
        background-image: url("data:image/jpeg;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    .main > div {{
        background-color: transparent;
        border-radius: 18px;
        padding: 30px;
        margin: 20px;
    }}
    """

css += """
    h1, h2, h3, h4 {
        color: #FFFFFF;
        text-shadow: 2px 2px 8px rgba(0,0,0,0.8);
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
        background-color: rgba(50, 50, 50, 0.7);
        color: #E0E0E0;
    }
    .stExpander {
        background-color: rgba(30, 30, 30, 0.5);
        border: 1px solid #4B0082;
        border-radius: 14px;
    }
    .stSidebar {
        background-color: rgba(10, 10, 10, 0.9);
    }
    /* Utskriftsvänlig stil */
    @media print {
        body { background: white; color: black; }
        .no-print { display: none !important; }
        img { max-width: 100%; height: auto; page-break-inside: avoid; }
        h1, h2 { color: black; text-shadow: none; }
    }
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# Logga
if os.path.exists(logo_path):
    st.image(Image.open(logo_path), use_column_width=True)
else:
    st.markdown("<h1 style='text-align: center;'>📦 Ordna Reda</h1>", unsafe_allow_html=True)

st.markdown("---")

# Sidebar
st.sidebar.markdown("### 📲 Följ mig")
instagram_url = st.sidebar.text_input("Instagram-länk", value="https://www.instagram.com/dittnamn/", key="ig")
website_url = st.sidebar.text_input("Hemsida-länk", value="https://dinhemsida.se", key="web")
st.sidebar.markdown(f"[📷 Instagram]({instagram_url})", unsafe_allow_html=True)
st.sidebar.markdown(f"[🌐 Hemsida]({website_url})", unsafe_allow_html=True)
st.sidebar.markdown("---")

# Databas
conn = sqlite3.connect('ordna_reda.db')
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

# Kolla om vi kom