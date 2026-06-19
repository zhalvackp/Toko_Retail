import csv
import os
from datetime import datetime
from collections import defaultdict
import hashlib

import streamlit as st
import pandas as pd

PRODUK_FILE    = "data_produk.csv"
TRANSAKSI_FILE = "data_transaksi.csv"

def hash_password(pw):
    return hashlib.md5(pw.encode()).hexdigest()

AKUN_DEFAULT = {
    "admin": hash_password("admin123"),
    "kasir": hash_password("kasir123"),
}

class Produk:
    def __init__(self, kode, nama, harga, stok):
        self.kode  = kode
        self.nama  = nama
        self.harga = float(harga)
        self.stok  = int(stok)

    def to_dict(self):
        return {"kode": self.kode, "nama": self.nama,
                "harga": self.harga, "stok": self.stok}


class Transaksi:
    def __init__(self, id_transaksi, kode_produk, nama_produk,
                 jumlah, harga_satuan, total_harga, tanggal=None, kasir="", metode_bayar=""):
        self.id_transaksi = id_transaksi
        self.kode_produk  = kode_produk
        self.nama_produk  = nama_produk
        self.jumlah       = int(jumlah)
        self.harga_satuan = float(harga_satuan)
        self.total_harga  = float(total_harga)
        self.tanggal      = tanggal or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.kasir        = kasir
        self.metode_bayar = metode_bayar

    def to_dict(self):
        return {
            "id_transaksi": self.id_transaksi,
            "kode_produk" : self.kode_produk,
            "nama_produk" : self.nama_produk,
            "jumlah"      : self.jumlah,
            "harga_satuan": self.harga_satuan,
            "total_harga" : self.total_harga,
            "tanggal"     : self.tanggal,
            "kasir"       : self.kasir,
            "metode_bayar": self.metode_bayar,
        }

def muat_produk():
    produk_list = []
    if not os.path.exists(PRODUK_FILE):
        return produk_list
    with open(PRODUK_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            produk_list.append(Produk(row["kode"], row["nama"],
                                      row["harga"], row["stok"]))
    return produk_list


def simpan_produk(produk_list):
    with open(PRODUK_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["kode", "nama", "harga", "stok"])
        w.writeheader()
        for p in produk_list:
            w.writerow(p.to_dict())


def muat_transaksi():
    trx_list = []
    if not os.path.exists(TRANSAKSI_FILE):
        return trx_list
    with open(TRANSAKSI_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            trx_list.append(Transaksi(
                row["id_transaksi"], row["kode_produk"], row["nama_produk"],
                row["jumlah"], row["harga_satuan"], row["total_harga"],
                row.get("tanggal"), row.get("kasir", ""), row.get("metode_bayar", "")
            ))
    return trx_list


def simpan_transaksi(trx_list):
    fieldnames = ["id_transaksi", "kode_produk", "nama_produk",
                  "jumlah", "harga_satuan", "total_harga", "tanggal", "kasir", "metode_bayar"]
    with open(TRANSAKSI_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for t in trx_list:
            w.writerow(t.to_dict())


def cari_produk(produk_list, kode):
    for p in produk_list:
        if p.kode.lower() == kode.lower():
            return p
    return None


def buat_id_transaksi(trx_list):
    if not trx_list:
        return "TRX001"
    nomor_terbesar = 0
    for t in trx_list:
        try:
            n = int(t.id_transaksi.replace("TRX", ""))
            nomor_terbesar = max(nomor_terbesar, n)
        except ValueError:
            pass
    return f"TRX{nomor_terbesar + 1:03d}"


def rupiah(angka):
    return f"Rp{angka:,.0f}"

AKUN_FILE = "data_akun.csv"

def muat_akun():
    akun = dict(AKUN_DEFAULT)
    if os.path.exists(AKUN_FILE):
        with open(AKUN_FILE, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                akun[row["username"]] = row["password_hash"]
    else:
        simpan_akun(akun)
    return akun


def simpan_akun(akun_dict):
    with open(AKUN_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["username", "password_hash"])
        w.writeheader()
        for u, h in akun_dict.items():
            w.writerow({"username": u, "password_hash": h})

def init_state():
    if "produk_list" not in st.session_state:
        st.session_state.produk_list = muat_produk()
    if "trx_list" not in st.session_state:
        st.session_state.trx_list = muat_transaksi()
    if "akun" not in st.session_state:
        st.session_state.akun = muat_akun()
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "login_error" not in st.session_state:
        st.session_state.login_error = ""
    if "reg_message" not in st.session_state:
        st.session_state.reg_message = ("", "")
    if "keranjang" not in st.session_state:
        st.session_state.keranjang = []
    if "struk_terakhir" not in st.session_state:
        st.session_state.struk_terakhir = None
    # MODIF: state untuk uang bayar agar bisa di-reset
    if "uang_bayar_input" not in st.session_state:
        st.session_state.uang_bayar_input = 0

def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f2027, #203a43, #2c5364);
    }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.2); }
    [data-testid="stSidebar"] .stRadio label {
        background: rgba(255,255,255,0.08);
        border-radius: 8px;
        padding: 8px 14px;
        margin: 3px 0;
        display: block;
        transition: background 0.2s;
        cursor: pointer;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(255,255,255,0.18);
    }

    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #ffffff, #f0f4ff);
        border: none;
        border-radius: 16px;
        padding: 1.2rem 1.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        transition: transform 0.2s;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.12);
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea, #764ba2);
        border: none;
        border-radius: 10px;
        color: white;
        font-weight: 600;
        padding: 0.6rem 1.5rem;
        transition: all 0.2s;
        box-shadow: 0 4px 15px rgba(102,126,234,0.4);
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102,126,234,0.5);
    }
    .stButton > button:not([kind="primary"]) {
        border-radius: 10px;
        border: 2px solid #667eea;
        color: #667eea;
        font-weight: 600;
        transition: all 0.2s;
    }

    /* MODIF: Tab - semua teks tab warna hitam, override orange/merah default */
    .stTabs [data-baseweb="tab-list"] {
        background: #f0f4ff;
        border-radius: 12px;
        padding: 4px;
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.88rem;
    }
    .stTabs [data-baseweb="tab"] p,
    .stTabs [data-baseweb="tab"] span,
    .stTabs [data-baseweb="tab"] div {
        color: #1a1a2e !important;
    }
    .stTabs [aria-selected="true"] {
        background: white !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .stTabs [aria-selected="true"] p,
    .stTabs [aria-selected="true"] span,
    .stTabs [aria-selected="true"] div {
        color: #1a1a2e !important;
        font-weight: 700;
    }
    .stTabs [aria-selected="false"] p,
    .stTabs [aria-selected="false"] span,
    .stTabs [aria-selected="false"] div {
        color: #1a1a2e !important;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #667eea !important;
    }
    .stTabs [data-baseweb="tab-border"] {
        background-color: transparent !important;
    }
    /* Override warna orange bawaan Streamlit pada tab */
    button[data-baseweb="tab"] {
        color: #1a1a2e !important;
    }
    button[data-baseweb="tab"] * {
        color: #1a1a2e !important;
    }

    .clock-box {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border-radius: 16px;
        padding: 1rem 1.5rem;
        text-align: center;
        margin-bottom: 1rem;
    }
    .clock-time {
        font-size: 2rem;
        font-weight: 700;
        color: #00d2ff;
        letter-spacing: 3px;
        font-family: 'Courier New', monospace;
    }
    .clock-date { font-size: 0.8rem; color: #a0aec0; margin-top: 4px; }

    .logo-box { text-align: center; padding: 1.5rem 1rem 0.5rem; }
    .logo-icon { font-size: 3rem; display: block; }
    .logo-name { font-size: 1.1rem; font-weight: 700; color: white; letter-spacing: 0.05em; }
    .logo-sub  { font-size: 0.7rem; color: #a0c4ff; letter-spacing: 0.1em; text-transform: uppercase; }

    .section-header {
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin-bottom: 1.5rem;
        color: white;
    }
    .section-header h2 { color: white !important; margin: 0; font-size: 1.4rem; }
    .section-header p  { color: rgba(255,255,255,0.8); margin: 0; font-size: 0.85rem; }

    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    }

    .stTextInput input, .stNumberInput input {
        border-radius: 8px !important;
        border: 2px solid #e8eaed !important;
        font-family: 'Poppins', sans-serif !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102,126,234,0.1) !important;
    }

    /* Struk styling */
    .struk-box {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        font-family: 'Courier New', monospace;
        border: 2px dashed #e0e0e0;
        color: #1a1a2e;
    }

    hr { border: none; border-top: 2px solid #f0f4ff; margin: 1.5rem 0; }
    .main .block-container { padding-top: 2rem; }
    </style>
    """, unsafe_allow_html=True)

def halaman_login():
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        min-height: 100vh;
    }
    [data-testid="stSidebar"] { display: none; }
    header[data-testid="stHeader"] { background: transparent; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:5vh'></div>", unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 1.2, 1])
    with col_c:

        st.markdown("""
        <div style='text-align:center; margin-bottom:0.5rem'>
            <span style='font-size:5.5rem;filter:drop-shadow(0 8px 20px rgba(0,0,0,0.3));
                         display:inline-block'>🛒</span>
            <div style='
                font-size:1.9rem;font-weight:800;color:white;
                text-shadow:0 2px 10px rgba(0,0,0,0.2);
                margin:.4rem 0 .1rem;letter-spacing:0.02em'>
                TOKO KOKO REUBEN
            </div>
            <div style='
                font-size:0.78rem;color:rgba(255,255,255,0.8);
                text-transform:uppercase;letter-spacing:0.2em;margin-bottom:2rem'>
                ✦ Point of Sales System ✦
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.container():
            st.markdown("""
            <div style='
                background:white;border-radius:24px;
                padding:2rem 2rem 1.5rem;
                box-shadow:0 25px 60px rgba(0,0,0,0.25);
            '>
                <div style='text-align:center;margin-bottom:0.5rem'>
                    <div style='font-size:1.1rem;font-weight:700;color:#1a1a2e'>
                         Login Kasir
                    </div>
                    <div style='font-size:0.78rem;color:#999'>
                        Masuk atau daftarkan akun staf baru
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            tab_login, tab_daftar = st.tabs(["Masuk", "Registrasi Akun"])

            with tab_login:
                username = st.text_input("👤 Username", placeholder="Masukkan username", key="login_user")
                password = st.text_input("🔑 Password", type="password",
                                         placeholder="Masukkan password", key="login_pass")

                if st.session_state.login_error:
                    st.markdown(f"""
                    <div style='
                        background:#fff3f3;border-left:4px solid #e53e3e;
                        border-radius:8px;padding:.7rem 1rem;
                        color:#c53030;font-size:0.85rem;margin:.5rem 0
                    '>
                        ❌ {st.session_state.login_error}
                    </div>
                    """, unsafe_allow_html=True)

                if st.button("Login", use_container_width=True, type="primary", key="btn_login"):
                    u = username.strip()
                    p = password.strip()
                    akun = st.session_state.akun
                    if not u or not p:
                        st.session_state.login_error = "Username dan password tidak boleh kosong!"
                        st.rerun()
                    elif u in akun and akun[u] == hash_password(p):
                        st.session_state.logged_in   = True
                        st.session_state.username    = u
                        st.session_state.login_error = ""
                        st.rerun()
                    else:
                        st.session_state.login_error = "Username atau password salah!"
                        st.rerun()

                st.markdown("""
                <div style='
                    background:#f0f4ff;border-radius:10px;
                    padding:.8rem 1rem;font-size:0.76rem;
                    color:#667eea;margin-top:1rem;
                    border-left:3px solid #667eea;line-height:1.8
                '>
                    
                </div>
                """, unsafe_allow_html=True)

            with tab_daftar:
                st.markdown("""
                <div style='font-size:0.8rem;color:#888;margin-bottom:0.8rem'>
                    💡 Daftarkan akun staf kasir baru di sini.
                </div>
                """, unsafe_allow_html=True)

                reg_user = st.text_input("👤 Username Baru", placeholder="Contoh: kasir_budi", key="reg_user")
                reg_pass = st.text_input("🔑 Password Baru", type="password",
                                         placeholder="Minimal 4 karakter", key="reg_pass")
                reg_konf = st.text_input("🔑 Ulangi Password", type="password",
                                         placeholder="Pastikan sama", key="reg_konf")

                tipe_msg, teks_msg = st.session_state.reg_message
                if teks_msg:
                    warna_bg  = "#fff3f3" if tipe_msg == "error" else "#f0fff4"
                    warna_brd = "#e53e3e" if tipe_msg == "error" else "#38a169"
                    warna_txt = "#c53030" if tipe_msg == "error" else "#276749"
                    ikon = "❌" if tipe_msg == "error" else "✅"
                    st.markdown(f"""
                    <div style='
                        background:{warna_bg};border-left:4px solid {warna_brd};
                        border-radius:8px;padding:.7rem 1rem;
                        color:{warna_txt};font-size:0.85rem;margin:.5rem 0
                    '>
                        {ikon} {teks_msg}
                    </div>
                    """, unsafe_allow_html=True)

                if st.button("💾 Daftarkan Akun", use_container_width=True, type="primary", key="btn_daftar"):
                    ru = reg_user.strip()
                    rp = reg_pass.strip()
                    rk = reg_konf.strip()
                    akun = st.session_state.akun
                    if not ru or not rp:
                        st.session_state.reg_message = ("error", "Username dan password tidak boleh kosong!")
                    elif len(rp) < 4:
                        st.session_state.reg_message = ("error", "Password minimal 4 karakter!")
                    elif ru in akun:
                        st.session_state.reg_message = ("error", f"Username '{ru}' sudah terdaftar!")
                    elif rp != rk:
                        st.session_state.reg_message = ("error", "Konfirmasi password tidak cocok!")
                    else:
                        akun[ru] = hash_password(rp)
                        simpan_akun(akun)
                        st.session_state.akun = akun
                        st.session_state.reg_message = ("success", f"Akun '{ru}' berhasil dibuat! Silakan login.")
                    st.rerun()

        st.markdown("""
        <div style='text-align:center;color:rgba(255,255,255,0.7);
                    font-size:0.72rem;margin-top:1.5rem'>
            © 2026 Toko KOKO REUBEN · All rights reserved
        </div>
        """, unsafe_allow_html=True)

def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div class="logo-box">
            <span class="logo-icon">🛒</span>
            <div class="logo-name">TOKO KOKO REUBEN</div>
            <div class="logo-sub">Point of Sales System</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        now = datetime.now()
        hari_indo  = ["Senin","Selasa","Rabu","Kamis","Jumat","Sabtu","Minggu"]
        bulan_indo = ["","Januari","Februari","Maret","April","Mei","Juni",
                      "Juli","Agustus","September","Oktober","November","Desember"]
        hari = hari_indo[now.weekday()]
        tgl  = f"{now.day} {bulan_indo[now.month]} {now.year}"
        jam  = now.strftime("%H:%M:%S")

        st.markdown(f"""
        <div class="clock-box">
            <div class="clock-time" id="jam">{jam}</div>
            <div class="clock-date">📅 {hari}, {tgl}</div>
        </div>
        <script>
        function updateClock() {{
            const now = new Date();
            const h = String(now.getHours()).padStart(2,'0');
            const m = String(now.getMinutes()).padStart(2,'0');
            const s = String(now.getSeconds()).padStart(2,'0');
            const el = document.getElementById('jam');
            if (el) el.textContent = h + ':' + m + ':' + s;
        }}
        setInterval(updateClock, 1000);
        </script>
        """, unsafe_allow_html=True)

        st.markdown("---")

        role = "Administrator" if st.session_state.username == "admin" else "Kasir"
        st.markdown(f"""
        <div style='
            background:rgba(255,255,255,0.1);
            border-radius:10px;padding:.8rem 1rem;margin-bottom:.5rem;
            font-size:0.82rem;line-height:1.8
        '>
            👤 <b>{st.session_state.username}</b><br>
            🎫 Role: {role}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        menu = st.radio(
            "Menu",
            ["Beranda", "Beli Produk", "Kelola Produk", "Laporan"],
            label_visibility="collapsed",
        )

        st.markdown("---")

        jml_produk = len(st.session_state.produk_list)
        jml_trx    = len(st.session_state.trx_list)
        stok_habis = sum(1 for p in st.session_state.produk_list if p.stok == 0)
        jml_keranjang = len(st.session_state.keranjang)

        st.markdown(f"""
        <div style='font-size:0.82rem;line-height:2'>
            📦 &nbsp;<b>Produk</b> &nbsp;: {jml_produk} item<br>
            🧾 &nbsp;<b>Transaksi</b> : {jml_trx} data<br>
            🛒 &nbsp;<b>Keranjang</b> : {jml_keranjang} item<br>
            🔴 &nbsp;<b>Stok Habis</b> : {stok_habis} produk
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        if st.button("LOGOUT", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username  = ""
            st.session_state.keranjang = []
            st.rerun()

        st.markdown("<div style='font-size:0.7rem;color:#a0c4ff;text-align:center'>v3.0 · 2025</div>",
                    unsafe_allow_html=True)

    return menu

def halaman_beranda():
    produk_list = st.session_state.produk_list
    trx_list    = st.session_state.trx_list

    st.markdown(f"""
    <div style='
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        border-radius: 20px; padding: 2.5rem 2rem; margin-bottom: 2rem;
        text-align: center; box-shadow: 0 10px 40px rgba(102,126,234,0.3);
    '>
        <div style='font-size:3.5rem'>🛒</div>
        <h1 style='color:white;font-size:2rem;margin:.5rem 0 .3rem;font-weight:700'>
            Toko KOKO REUBEN
        </h1>
        <p style='color:rgba(255,255,255,0.85);font-size:1rem;margin:0'>
            Selamat datang, <b>{st.session_state.username}</b>!
        </p>
    </div>
    """, unsafe_allow_html=True)

    total_produk    = len(produk_list)
    total_trx       = len(set(t.id_transaksi for t in trx_list))
    total_pemasukan = sum(t.total_harga for t in trx_list)
    stok_habis      = sum(1 for p in produk_list if p.stok == 0)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("<div style='text-align:center;font-size:1.8rem'>📦</div>", unsafe_allow_html=True)
        st.metric("Total Produk", total_produk)
    with c2:
        st.markdown("<div style='text-align:center;font-size:1.8rem'>🧾</div>", unsafe_allow_html=True)
        st.metric("Total Transaksi", total_trx)
    with c3:
        st.markdown("<div style='text-align:center;font-size:1.8rem'>💰</div>", unsafe_allow_html=True)
        st.metric("Total Pemasukan", rupiah(total_pemasukan))
    with c4:
        st.markdown("<div style='text-align:center;font-size:1.8rem'>⚠️</div>", unsafe_allow_html=True)
        st.metric("Stok Habis", stok_habis)

    st.markdown("<br>", unsafe_allow_html=True)

    if produk_list:
        st.markdown("""
        <div class="section-header">
            <h2>Daftar Produk</h2>
            <p>Semua produk yang tersedia di toko</p>
        </div>
        """, unsafe_allow_html=True)
        rows = [{"Kode": p.kode, "Nama Produk": p.nama, "Harga": rupiah(p.harga),
                 "Stok": p.stok,
                 "Status": "🔴 Habis" if p.stok == 0 else ("🟡 Menipis" if p.stok <= 5 else "🟢 Tersedia")}
                for p in produk_list]
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.markdown("""
        <div style='text-align:center;padding:3rem;background:#f8f9ff;
                    border-radius:16px;border:2px dashed #c8d4ff'>
            <div style='font-size:3rem'>🏪</div>
            <h3 style='color:#667eea'>Toko Masih Kosong</h3>
            <p style='color:#888'>Tambahkan produk melalui menu <b>Kelola Produk</b></p>
        </div>
        """, unsafe_allow_html=True)

    if trx_list:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="section-header">
            <h2>5 Transaksi Terbaru</h2>
            <p>Riwayat penjualan paling baru</p>
        </div>
        """, unsafe_allow_html=True)
        recent = trx_list[-5:][::-1]
        rows2  = [{"ID": t.id_transaksi, "Tanggal": t.tanggal, "Produk": t.nama_produk,
                   "Jumlah": t.jumlah, "Total": rupiah(t.total_harga)} for t in recent]
        st.dataframe(rows2, use_container_width=True, hide_index=True)

def cetak_struk(id_transaksi, keranjang, total_tagihan, uang_bayar, kembalian, metode, kasir, waktu):
    """Render struk format kasir fisik - putih, monospace, harga satuan x qty"""
    import streamlit.components.v1 as components

    total_qty = sum(it["jumlah"] for it in keranjang)

    def fmt(angka):
        return f"{int(angka):,}".replace(",", ".")

    # Baris produk: nama bold, lalu qty x harga_satuan rata kanan subtotal
    baris_list = []
    for i, it in enumerate(keranjang):
        subtotal  = it["harga"] * it["jumlah"]
        nama_aman = str(it["nama"]).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        baris_list.append(
            f"<div style='margin-bottom:10px'>"
            f"<div class='prod-nama'>{i+1}. {nama_aman}</div>"
            f"<div class='prod-detail'>"
            f"<span>{it['jumlah']} x {fmt(it['harga'])}</span>"
            f"<span>Rp {fmt(subtotal)}</span>"
            f"</div>"
            f"</div>"
        )
    semua_baris = "\n".join(baris_list)

    html_struk = f"""<!DOCTYPE html><html><head><meta charset='utf-8'>
<style>
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{
    background: transparent;
    display: flex;
    justify-content: center;
    padding: 4px;
    font-family: 'Segoe UI', Arial, sans-serif;
  }}
  .struk {{
    background: #3a3a4a;
    border-radius: 20px;
    padding: 24px 28px 28px;
    width: 100%;
    max-width: 380px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    color: #fff;
  }}
  .header {{ text-align:center; margin-bottom:14px; line-height:1.6; }}
  .header .toko {{ font-size:16px; font-weight:800; color:#fff; letter-spacing:1px; }}
  .header .sub  {{ font-size:12px; color:#bbb; }}
  .sep {{ border:none; border-top:1px solid rgba(255,255,255,0.15); margin:12px 0; }}
  .meta {{ font-size:12px; color:#ccc; line-height:1.8; }}
  .meta b {{ color:#fff; }}
  .produk-list {{ margin: 6px 0; }}
  .prod-nama {{ font-weight:700; color:#fff; font-size:13.5px; }}
  .prod-detail {{
    display:flex; justify-content:space-between;
    font-size:13px; color:#ccc; padding-left:16px; margin-top:2px;
  }}
  .prod-detail span:last-child {{ color:#fff; font-weight:600; }}
  .row {{
    display:flex; justify-content:space-between;
    font-size:13.5px; padding:4px 0; color:#ccc;
  }}
  .row span:last-child {{ color:#fff; font-weight:600; }}
  .row.big {{ font-size:15px; }}
  .row.big span:last-child {{ font-size:16px; }}
  .row.kembalian span:last-child {{ color:#6ee7b7; font-size:17px; }}
  .footer {{ text-align:center; font-size:12px; color:#aaa; margin-top:10px; line-height:1.8; }}
  .footer b {{ color:#a78bfa; }}
</style>
</head><body>
<div class='struk'>
  <div class='header'>
    <div style='font-size:28px'></div>
    <div class='toko'>TOKO KOKO REUBEN</div>
    <div class='sub'>Point of Sales System</div>
    <div class='meta' style='margin-top:8px'>
      ID: <b>{id_transaksi}</b> · Kasir: <b>{kasir}</b><br>
      Waktu: {waktu}
    </div>
  </div>

  <hr class='sep'>

  <div class='produk-list'>
    {semua_baris}
  </div>

  <hr class='sep'>

  <div class='row'>
    <span>Total QTY</span>
    <span>{total_qty} item</span>
  </div>

  <hr class='sep'>

  <div class='row'>
    <span>Sub Total</span>
    <span>Rp {fmt(total_tagihan)}</span>
  </div>
  <div class='row big' style='margin-top:4px'>
    <span>Total</span>
    <span>Rp {fmt(total_tagihan)}</span>
  </div>
  <div class='row big' style='margin-top:4px'>
    <span>Bayar ({metode})</span>
    <span>Rp {fmt(uang_bayar)}</span>
  </div>
  <div class='row big kembalian' style='margin-top:4px'>
    <span>Kembali</span>
    <span>Rp {fmt(kembalian)}</span>
  </div>

  <hr class='sep'>

  <div class='footer'>
    Terimakasih Telah Berbelanja<br>
    <b>✦ TOKO KOKO REUBEN ✦</b>
  </div>
</div>
</body></html>"""

    tinggi_iframe = 480 + (len(keranjang) * 52)
    components.html(html_struk, height=tinggi_iframe, scrolling=False)

def halaman_beli():
    st.markdown("""
    <div class="section-header">
        <h2>Transaksi Penjualan (Kasir)</h2>
        <p>Pilih beberapa produk, masukkan ke keranjang, lalu bayar</p>
    </div>
    """, unsafe_allow_html=True)

    produk_list = st.session_state.produk_list
    trx_list    = st.session_state.trx_list
    tersedia    = [p for p in produk_list if p.stok > 0]

    if not tersedia:
        st.markdown("""
        <div style='text-align:center;padding:3rem;background:#fff3f3;
                    border-radius:16px;border:2px dashed #fc8181'>
            <div style='font-size:3rem'>📭</div>
            <h3 style='color:#e53e3e'>Semua Stok Habis!</h3>
            <p>Tambah stok produk melalui menu Kelola Produk</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # KONDISI A: Jika struk di-load dari halaman reload (Session State)
    if st.session_state.struk_terakhir:
        st.markdown("### Struk Pembayaran")
        d = st.session_state.struk_terakhir
        cetak_struk(
            d["id"], d["keranjang"], d["total"], d["bayar"],
            d["kembalian"], d["metode"], d["kasir"], d["waktu"]
        )
        # PAS KLIK TRANSAKSI BARU DISINI, SEBELUM RERUN WAJIB KOSONGKAN KERANJANG TOTAL!
        if st.button("✖️ Transaksi Baru", use_container_width=True):
            st.session_state.struk_terakhir = None
            st.session_state.keranjang = []  # <--- INI BIAR KERANJANG BALIK KOSONG LAGI
            st.session_state.uang_bayar_input = 0
            st.rerun()
        return

    placeholder_halaman = st.empty()

    with placeholder_halaman.container():
        col_left, col_right = st.columns([1.1, 1.3])

        with col_left:
            st.markdown("#### Pilih Produk")
            opsi    = {f"[{p.kode}] {p.nama}": p for p in tersedia}
            pilihan = st.selectbox("Produk", list(opsi.keys()))
            p       = opsi[pilihan]

            st.markdown(f"""
            <div style='background:#f0f4ff;border-radius:10px;padding:.8rem 1rem;
                        font-size:0.85rem;margin:.5rem 0;color:#1a1a2e'>
                💰 Harga: <b>{rupiah(p.harga)}</b> &nbsp;|&nbsp; 📦 Stok: <b>{p.stok}</b>
            </div>
            """, unsafe_allow_html=True)

            jumlah = st.number_input(f"Jumlah (maks {p.stok})", min_value=1,
                                      max_value=p.stok, step=1, key="jml_beli")

            if st.button("➕ Masukkan ke Keranjang", use_container_width=True, type="primary"):
                keranjang = st.session_state.keranjang
                item_ada = next((it for it in keranjang if it["kode"] == p.kode), None)
                if item_ada:
                    if item_ada["jumlah"] + jumlah <= p.stok:
                        item_ada["jumlah"] += jumlah
                        st.success(f"✅ Jumlah **{p.nama}** di keranjang diperbarui.")
                    else:
                        st.error(f"❌ Total melebihi stok! Sisa stok hanya {p.stok}.")
                else:
                    keranjang.append({"kode": p.kode, "nama": p.nama,
                                      "harga": p.harga, "jumlah": jumlah})
                    st.success(f"✅ **{p.nama}** ditambahkan ke keranjang!")
                st.rerun()

            st.markdown("<br>#### Status Stok Toko", unsafe_allow_html=True)
            rows = [{"Kode": pr.kode, "Nama": pr.nama, "Stok": pr.stok,
                     "Status": "🔴 Habis" if pr.stok == 0 else ("🟡 Menipis" if pr.stok <= 5 else "🟢 Aman")}
                    for pr in produk_list]
            st.dataframe(rows, use_container_width=True, hide_index=True, height=200)

        with col_right:
            st.markdown("#### 🧾 Keranjang Belanja")
            keranjang = st.session_state.keranjang

            if not keranjang:
                st.markdown("""
                <div style='text-align:center;padding:2rem;background:#f8f9ff;
                            border-radius:14px;border:2px dashed #c8d4ff'>
                    <div style='font-size:2.2rem'>🛒</div>
                    <p style='color:#888;margin:0'>Keranjang masih kosong</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                rows = []
                total_tagihan = 0
                for it in keranjang:
                    subtotal = it["harga"] * it["jumlah"]
                    total_tagihan += subtotal
                    rows.append({"Produk": it["nama"], "Harga": rupiah(it["harga"]),
                                 "Jumlah": it["jumlah"], "Subtotal": rupiah(subtotal)})
                st.dataframe(rows, use_container_width=True, hide_index=True)

                st.markdown(f"""
                <div style='
                    background:linear-gradient(135deg,#667eea,#764ba2);
                    border-radius:14px;padding:1.2rem 1.5rem;color:white;margin:1rem 0;
                    display:flex;justify-content:space-between;align-items:center'>
                    <span style='font-size:0.95rem'>💵 TOTAL BELANJA</span>
                    <span style='font-size:1.5rem;font-weight:700'>{rupiah(total_tagihan)}</span>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("##### 💳 Metode Pembayaran")
                metode_bayar = st.radio(
                    "Pilih metode:",
                    ["Cash", "QRIS"],
                    horizontal=True,
                    key="metode_bayar_radio",
                    label_visibility="collapsed"
                )

                st.markdown("##### 💴 Uang Diterima (Rp)")
                uang_str = st.text_input(
                    "Uang Diterima",
                    value=str(st.session_state.uang_bayar_input) if st.session_state.uang_bayar_input != 0 else "",
                    placeholder="Contoh: 50000",
                    key="uang_bayar_str",
                    label_visibility="collapsed"
                )

                try:
                    uang_bayar = int(uang_str.replace(".", "").replace(",", "").strip()) if uang_str.strip() else 0
                except ValueError:
                    uang_bayar = 0

                if uang_bayar > 0:
                    st.markdown(f"""
                    <div style='background:#f0fff4;border-left:4px solid #38a169;
                                border-radius:8px;padding:.5rem 1rem;color:#276749;font-size:0.9rem'>
                        💵 {rupiah(uang_bayar)}
                    </div>
                    """, unsafe_allow_html=True)

                if uang_bayar >= total_tagihan and uang_bayar > 0:
                    kembalian_preview = uang_bayar - total_tagihan
                    st.markdown(f"""
                    <div style='background:#ebf8ff;border-left:4px solid #3182ce;
                                border-radius:8px;padding:.5rem 1rem;color:#2b6cb0;font-size:0.9rem;margin-top:4px'>
                        🔄 Kembalian: <b>{rupiah(kembalian_preview)}</b>
                    </div>
                    """, unsafe_allow_html=True)
                elif uang_bayar > 0 and uang_bayar < total_tagihan:
                    kurang = total_tagihan - uang_bayar
                    st.markdown(f"""
                    <div style='background:#fff3f3;border-left:4px solid #e53e3e;
                                border-radius:8px;padding:.5rem 1rem;color:#c53030;font-size:0.9rem;margin-top:4px'>
                        ❌ Kurang: <b>{rupiah(kurang)}</b>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Kosongkan", use_container_width=True):
                        st.session_state.keranjang = []
                        st.session_state.uang_bayar_input = 0
                        st.rerun()
                with c2:
                    if st.button("Bayar", use_container_width=True, type="primary"):
                        if uang_bayar <= 0:
                            st.error("❌ Masukkan jumlah uang yang diterima!")
                        elif uang_bayar < total_tagihan:
                            st.error(f"❌ Uang kurang! Minimal {rupiah(total_tagihan)}")
                        else:
                            kembalian = uang_bayar - total_tagihan
                            id_baru   = buat_id_transaksi(trx_list)
                            waktu     = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                            keranjang_untuk_struk = list(keranjang)

                            for it in keranjang:
                                prod = cari_produk(produk_list, it["kode"])
                                if prod:
                                    prod.stok -= it["jumlah"]
                                trx_list.append(Transaksi(
                                    id_baru, it["kode"], it["nama"], it["jumlah"],
                                    it["harga"], it["harga"] * it["jumlah"],
                                    waktu, st.session_state.username, metode_bayar
                                ))

                            simpan_produk(produk_list)
                            simpan_transaksi(trx_list)

                            st.session_state.struk_terakhir = {
                                "id": id_baru,
                                "keranjang": keranjang_untuk_struk,
                                "total": total_tagihan,
                                "bayar": uang_bayar,
                                "kembalian": kembalian,
                                "metode": metode_bayar,
                                "kasir": st.session_state.username,
                                "waktu": waktu,
                            }
                            
                            # KONDISI B: Eksekusi Instan saat klik bayar di layar kasir aktif
                            with placeholder_halaman.container():
                                st.balloons()
                                st.markdown("### Struk Pembayaran")
                                cetak_struk(id_baru, keranjang_untuk_struk, total_tagihan, uang_bayar, kembalian, metode_bayar, st.session_state.username, waktu)
                                
                                # PAS TRANSAKSI BARU DISINI DIKLIK, WAJIB BERSIHKAN KERANJANG AGAR KASIR BALIK KOSONG
                                if st.button("✖️ Transaksi Baru", use_container_width=True):
                                    st.session_state.struk_terakhir = None
                                    st.session_state.keranjang = []  # <--- BERSIHKAN TOTAL DI SINI JUGA
                                    st.session_state.uang_bayar_input = 0
                                    st.rerun()

def halaman_produk():
    st.markdown("""
    <div class="section-header">
        <h2> Kelola Produk</h2>
        <p>Tambah, ubah, atau hapus produk toko</p>
    </div>
    """, unsafe_allow_html=True)

    produk_list = st.session_state.produk_list
    tab1, tab2, tab3 = st.tabs(["Tambah Produk", "Ubah Harga & Stok", "Hapus Produk"])

    with tab1:
        col_form, col_info = st.columns([1, 1])
        with col_form:
            st.markdown("#### Tambah Produk Baru")
            with st.form("form_tambah", clear_on_submit=True):
                kode  = st.text_input("Kode Produk", placeholder="Contoh: P001")
                nama  = st.text_input("Nama Produk", placeholder="Contoh: Indomie Goreng")
                harga_str = st.text_input("Harga Satuan (Rp)", value="", placeholder="Contoh: 15000")
                stok  = st.number_input("Jumlah Stok", min_value=0, step=1)
                submit = st.form_submit_button("💾 Tambah Produk", use_container_width=True, type="primary")
            if submit:
                kode = kode.strip(); nama = nama.strip()
                try:
                    harga = float(harga_str.strip()) if harga_str.strip() else 0.0
                except ValueError:
                    st.error("❌ Masukkan harga satuan dengan format angka yang valid!")
                    return
                
                if not kode:
                    st.error("❌ Kode produk tidak boleh kosong.")
                elif not nama:
                    st.error("❌ Nama produk tidak boleh kosong.")
                elif cari_produk(produk_list, kode):
                    st.error(f"❌ Kode **{kode}** sudah digunakan.")
                else:
                    produk_list.append(Produk(kode, nama, harga, stok))
                    simpan_produk(produk_list)
                    st.success(f"✅ Produk **{nama}** berhasil ditambahkan!")
                    st.rerun()
        with col_info:
            st.markdown("#### 💡 Tips Pengisian")
            st.markdown("""
            <div style='background:#f0f4ff;border-radius:12px;padding:1.2rem'>
            <ul style='margin:0;padding-left:1.2rem;line-height:2;color:#444'>
                <li>Kode produk harus <b>unik</b> (contoh: P001)</li>
                <li>Nama produk jelas dan mudah dicari</li>
                <li>Harga dalam satuan <b>Rupiah</b></li>
                <li>Stok adalah jumlah <b>awal persediaan</b></li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # --- TAMBAHAN DAFTAR PRODUK DI TAB 1 ---
        st.markdown("<br>Daftar Produk Saat Ini", unsafe_allow_html=True)
        if not produk_list:
            st.info("📭 Belum ada produk yang terdaftar.")
        else:
            rows_tab1 = [{"Kode": pr.kode, "Nama": pr.nama, "Harga": rupiah(pr.harga), "Stok": pr.stok} for pr in produk_list]
            st.dataframe(rows_tab1, use_container_width=True, hide_index=True)

    with tab2:
        st.markdown("#### Ubah Harga & Stok Produk")
        if not produk_list:
            st.info("📭 Belum ada produk.")
        else:
            opsi = {f"[{p.kode}] {p.nama}": p for p in produk_list}
            pilihan = st.selectbox("Pilih Produk", list(opsi.keys()), key="select_ubah")
            p = opsi[pilihan]
            st.markdown(f"""
            <div style='background:#fff8e1;border-left:4px solid #ffc107;
                        border-radius:8px;padding:1rem;margin:1rem 0;color:#1a1a2e'>
                <b>Data saat ini:</b> {p.nama} | Harga: {rupiah(p.harga)} | Stok: {p.stok}
            </div>
            """, unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                harga_baru_str = st.text_input(
                    "💰 Harga Baru (Rp)", 
                    value=str(int(p.harga)) if p.harga != 0 else "", 
                    placeholder="Contoh: 20000",
                    key="harga_baru_input"
                )
            with col2:
                stok_baru = st.number_input("📦 Stok Baru", min_value=0,
                                             value=int(p.stok), step=1, key="stok_baru")
            if st.button("💾 Simpan Perubahan", use_container_width=True, type="primary", key="btn_ubah"):

                try:
                    harga_baru = float(harga_baru_str.strip()) if harga_baru_str.strip() else 0.0
                except ValueError:
                    st.error("❌ Masukkan harga baru dengan format angka yang valid!")
                    return

                if harga_baru <= 0:
                    st.error("❌ Harga baru harus lebih besar dari 0.")
                    return
                
                p.harga = harga_baru
                p.stok  = stok_baru
                simpan_produk(produk_list)
                st.success(f"✅ Produk **{p.nama}** berhasil diperbarui!")
                st.rerun()
            
            # --- TAMBAHAN DAFTAR PRODUK DI TAB 2 ---
            st.markdown("<br>Daftar Produk Saat Ini", unsafe_allow_html=True)
            rows_tab2 = [{"Kode": pr.kode, "Nama": pr.nama, "Harga": rupiah(pr.harga), "Stok": pr.stok} for pr in produk_list]
            st.dataframe(rows_tab2, use_container_width=True, hide_index=True)

    with tab3:
        st.markdown("#### Hapus Produk")
        if not produk_list:
            st.info("📭 Belum ada produk.")
        else:
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**Opsi A — Hapus Satu Produk**")
                opsi_h = {f"[{p.kode}] {p.nama}": p for p in produk_list}
                pilihan_h = st.selectbox("Pilih Produk", list(opsi_h.keys()), key="select_hapus")
                ph = opsi_h[pilihan_h]
                st.markdown(f"""
                <div style='background:#fff3f3;border-left:4px solid #e53e3e;
                            border-radius:8px;padding:.8rem;margin:.5rem 0;color:#1a1a2e'>
                    ⚠️ Akan menghapus: <b>{ph.nama}</b>
                </div>
                """, unsafe_allow_html=True)
                konfirm = st.checkbox("Ya, saya yakin", key="konfirm_hapus")
                if st.button("Hapus Produk", use_container_width=True, key="btn_hapus"):
                    if not konfirm:
                        st.error("❌ Centang konfirmasi terlebih dahulu!")
                    else:
                        produk_list[:] = [p for p in produk_list if p.kode != ph.kode]
                        simpan_produk(produk_list)
                        st.success(f"✅ Produk **{ph.nama}** berhasil dihapus!")
                        st.rerun()

            with col_b:
                st.markdown("**Opsi B — Bersihkan Massal Stok Habis**")
                stok_habis_list = [p for p in produk_list if p.stok == 0]
                if stok_habis_list:
                    st.markdown(f"""
                    <div style='background:#fff8e1;border-left:4px solid #ffc107;
                                border-radius:8px;padding:.8rem;margin:.5rem 0;color:#1a1a2e'>
                        📋 Ditemukan <b>{len(stok_habis_list)}</b> produk dengan stok 0
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style='background:#f0fff4;border-left:4px solid #38a169;
                                border-radius:8px;padding:.8rem;margin:.5rem 0;color:#276749'>
                        ✅ Tidak ada produk stok habis
                    </div>
                    """, unsafe_allow_html=True)
                if st.button("Hapus Semua Stok Habis", use_container_width=True, key="btn_hapus_massal",
                             disabled=len(stok_habis_list) == 0):
                    produk_list[:] = [p for p in produk_list if p.stok != 0]
                    simpan_produk(produk_list)
                    st.success(f"✅ {len(stok_habis_list)} produk stok habis berhasil dihapus!")
                    st.rerun()


def halaman_laporan():
    st.markdown("""
    <div class="section-header">
        <h2>Laporan Penjualan</h2>
        <p>Ringkasan data transaksi toko</p>
    </div>
    """, unsafe_allow_html=True)

    trx_list = st.session_state.trx_list

    if not trx_list:
        st.markdown("""
        <div style='text-align:center;padding:3rem;background:#f8f9ff;
                    border-radius:16px;border:2px dashed #c8d4ff'>
            <div style='font-size:3rem'>📭</div>
            <h3 style='color:#667eea'>Belum Ada Transaksi</h3>
            <p style='color:#888'>Data laporan akan muncul setelah ada transaksi</p>
        </div>
        """, unsafe_allow_html=True)
        return

    total_pemasukan = sum(t.total_harga for t in trx_list)
    total_item_terjual = sum(t.jumlah for t in trx_list)
    total_trx_unik = len(set(t.id_transaksi for t in trx_list))

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("💰 Total Pemasukan", rupiah(total_pemasukan))
    with c2:
        st.metric("🧾 Total Transaksi", total_trx_unik)
    with c3:
        st.metric("📦 Item Terjual", total_item_terjual)

    # ── GRAFIK: Pendapatan per Hari ──────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="section-header">
        <h2>📈 Grafik Pendapatan Harian</h2>
        <p>Tren penjualan dari waktu ke waktu</p>
    </div>
    """, unsafe_allow_html=True)

    pendapatan_harian = defaultdict(float)
    for t in trx_list:
        tgl_only = t.tanggal[:10]  # ambil YYYY-MM-DD saja
        pendapatan_harian[tgl_only] += t.total_harga

    tgl_terurut = sorted(pendapatan_harian.keys())
    df_harian = {"Tanggal": tgl_terurut,
                 "Pendapatan": [pendapatan_harian[tg] for tg in tgl_terurut]}

    df_chart = pd.DataFrame(df_harian).set_index("Tanggal")
    st.line_chart(df_chart, use_container_width=True, color="#667eea")

    # ── GRAFIK: Produk Terlaris (Bar Chart) ──────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="section-header">
        <h2>📊 Grafik Produk Terlaris</h2>
        <p>Perbandingan jumlah unit terjual per produk</p>
    </div>
    """, unsafe_allow_html=True)

    penjualan_chart = defaultdict(lambda: {"nama": "", "qty": 0, "total": 0})
    for t in trx_list:
        penjualan_chart[t.kode_produk]["nama"] = t.nama_produk
        penjualan_chart[t.kode_produk]["qty"] += t.jumlah
        penjualan_chart[t.kode_produk]["total"] += t.total_harga

    ranking_chart = sorted(penjualan_chart.items(), key=lambda x: x[1]["qty"], reverse=True)
    nama_produk_chart = [v["nama"] for k, v in ranking_chart]
    qty_chart         = [v["qty"] for k, v in ranking_chart]

    df_produk = pd.DataFrame({"Produk": nama_produk_chart, "Qty Terjual": qty_chart}).set_index("Produk")
    st.bar_chart(df_produk, use_container_width=True, color="#764ba2")

    # ── GRAFIK: Metode Pembayaran (Pie-style via bar) ────────────────────────
    metode_count = defaultdict(float)
    for t in trx_list:
        m = t.metode_bayar or "Tidak Diketahui"
        metode_count[m] += t.total_harga

    if len(metode_count) > 1 or (len(metode_count) == 1 and "Tidak Diketahui" not in metode_count):
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="section-header">
            <h2>💳 Grafik Metode Pembayaran</h2>
            <p>Perbandingan pendapatan berdasarkan metode bayar</p>
        </div>
        """, unsafe_allow_html=True)
        df_metode = pd.DataFrame({
            "Metode": list(metode_count.keys()),
            "Pendapatan": list(metode_count.values())
        }).set_index("Metode")
        st.bar_chart(df_metode, use_container_width=True, color="#38a169")

    # ── Detail Transaksi ──────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="section-header">
        <h2>Detail Transaksi</h2>
        <p>Semua riwayat penjualan</p>
    </div>
    """, unsafe_allow_html=True)

    rows = [{"ID": t.id_transaksi, "Tanggal": t.tanggal, "Produk": t.nama_produk,
             "Qty": t.jumlah, "Harga Satuan": rupiah(t.harga_satuan),
             "Total": rupiah(t.total_harga), "Kasir": t.kasir,
             "Metode": t.metode_bayar or "-"}
            for t in reversed(trx_list)]
    st.dataframe(rows, use_container_width=True, hide_index=True)

    # Produk terlaris (tabel)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="section-header">
        <h2>🏆 Produk Terlaris</h2>
        <p>Ranking produk berdasarkan jumlah terjual</p>
    </div>
    """, unsafe_allow_html=True)

    penjualan = defaultdict(lambda: {"nama": "", "qty": 0, "total": 0})
    for t in trx_list:
        penjualan[t.kode_produk]["nama"] = t.nama_produk
        penjualan[t.kode_produk]["qty"] += t.jumlah
        penjualan[t.kode_produk]["total"] += t.total_harga

    ranking = sorted(penjualan.items(), key=lambda x: x[1]["qty"], reverse=True)
    rows_rank = [{"#": i+1, "Kode": k, "Produk": v["nama"],
                  "Total Terjual": v["qty"], "Pendapatan": rupiah(v["total"])}
                 for i, (k, v) in enumerate(ranking)]
    st.dataframe(rows_rank, use_container_width=True, hide_index=True)


# ── MAIN ─────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Toko KOKO REUBEN – POS",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_state()
inject_css()

if not st.session_state.logged_in:
    halaman_login()
else:
    menu = render_sidebar()
    if menu == "Beranda":
        halaman_beranda()
    elif menu == "Beli Produk":
        halaman_beli()
    elif menu == "Kelola Produk":
        halaman_produk()
    elif menu == "Laporan":
        halaman_laporan()