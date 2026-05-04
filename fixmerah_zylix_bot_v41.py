#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════╗
║  🔴 𝗙𝗶𝘅𝗠𝗲𝗿𝗮𝗵 𝗕𝗼𝘁 × 𝗭𝘆𝗹𝗶𝘅 🚀  —  𝗠𝗘𝗠𝗕𝗘𝗥𝗦𝗛𝗜𝗣 𝗦𝗬𝗦𝗧𝗘𝗠 𝘃𝟰.𝟭  ║
║  Owner: 安扎君 · 𝕬𝖓𝖟𝖆𝖏𝖚𝖓 𝕬𝖕𝖔𝖈𝖆𝖑𝖞𝖕𝖘𝖊 أنزاجون 🕊️⚔️  |  @anzajun  ║
║  Community: https://t.me/FixMerahCommunity                    ║
║  Official:  https://t.me/FixMerahOfficial                     ║
╠═══════════════════════════════════════════════════════════════╣
║  TIERS:                                                       ║
║  🆓 FREE     — Batasan harian, add Gmail sendiri              ║
║  💎 PREMIUM  — 3 Paket (5K/10K/15K), Gmail owner + pribadi    ║
║  👑 OWNER    — Full access, manage all                        ║
║  🔗 REFERRAL — Sistem referral dengan bonus + komisi 10%      ║
║  💳 PAKASIR  — Pembayaran QRIS otomatis                       ║
╚═══════════════════════════════════════════════════════════════╝
"""

import os
import json
import time
import random
import threading
import subprocess
import smtplib
import imaplib
import email as emaillib
import socket
import socks
import requests
import io
import base64
import secrets
import string
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from telebot import TeleBot, types

try:
    import qrcode
    from PIL import Image
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False
    print("[WARN] qrcode/PIL tidak terinstall. Install: pip install qrcode[pil]")

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER = os.getenv("OWNER", "@anzajun")

# ═══════════════════ PAKASIR CONFIG ═══════════════════
PAKASIR_PROJECT = os.getenv("PAKASIR_PROJECT", "")
PAKASIR_API_KEY = os.getenv("PAKASIR_API_KEY", "")
PAKASIR_API_URL = "https://app.pakasir.com/api"
PAKASIR_PAY_URL = "https://app.pakasir.com/pay"

# QRIS Fee: 0.7% + Rp 310 (untuk <= Rp 105.000)
#           1% + Rp 0    (untuk > Rp 105.000)
def calculate_qris_fee(amount):
    if amount > 105000:
        fee = round(amount * 0.01)
    else:
        fee = round(amount * 0.007 + 310)
    return fee

SUPPORT_EMAILS = [
    os.getenv("SUPPORT_EMAIL1", "android@support.whatsapp.com"),
    os.getenv("SUPPORT_EMAIL2", "support@support.whatsapp.com"),
    os.getenv("SUPPORT_EMAIL3", "smb@support.whatsapp.com"),
]

# OWNER Gmail accounts (for PREMIUM users)
OWNER_EMAILS = []
OWNER_APPS = []
for i in range(1, 11):
    e = os.getenv(f"EMAIL{i}")
    p = os.getenv(f"APP_PASSWORD{i}")
    if e and p:
        OWNER_EMAILS.append(e)
        OWNER_APPS.append(p)

MIN_DELAY = int(os.getenv("MIN_DELAY", 30))
MAX_DELAY = int(os.getenv("MAX_DELAY", 120))

WARP_ENABLED = os.getenv("WARP_ENABLED", "true").lower() == "true"
WARP_PROXY_HOST = os.getenv("WARP_PROXY_HOST", "127.0.0.1")
WARP_PROXY_PORT = int(os.getenv("WARP_PROXY_PORT", 40000))

AUTO_REPLY_ENABLED = os.getenv("AUTO_REPLY_ENABLED", "true").lower() == "true"
AUTO_REPLY_INTERVAL = int(os.getenv("AUTO_REPLY_INTERVAL", 300))

if not BOT_TOKEN:
    raise SystemExit("❌ BOT_TOKEN tidak ditemukan di .env!")

if not PAKASIR_PROJECT or not PAKASIR_API_KEY:
    print("[WARN] PAKASIR_PROJECT atau PAKASIR_API_KEY belum diatur di .env. Payment system tidak akan berfungsi.")

bot = TeleBot(BOT_TOKEN, parse_mode="HTML")

# ═══════════════════ DATA FILES ═══════════════════
DATA_FILE = "data.json"
REPLIES_FILE = "replies.json"
USERS_FILE = "users.json"
TRANSACTIONS_FILE = "transactions.json"

user_state = {}
sending_threads = {}
auto_reply_threads = {}
payment_threads = {}

# ═══════════════════ MEMBERSHIP TIERS ═══════════════════
TIER_CONFIG = {
    "free": {
        "name": "🆓 FREE",
        "daily_limit": 3,
        "use_own_gmail": True,
        "can_add_gmail": True,
        "max_gmail": 2,
        "price": 0,
        "duration_days": 0,
        "warp": False,
        "auto_reply": False,
    },
    "premium_basic": {
        "name": "💎 PREMIUM BASIC",
        "daily_limit": 15,
        "use_own_gmail": False,
        "can_add_gmail": True,
        "max_gmail": 5,
        "price": 5000,
        "duration_days": 30,
        "warp": True,
        "auto_reply": True,
    },
    "premium_pro": {
        "name": "💎💎 PREMIUM PRO",
        "daily_limit": 35,
        "use_own_gmail": False,
        "can_add_gmail": True,
        "max_gmail": 8,
        "price": 10000,
        "duration_days": 30,
        "warp": True,
        "auto_reply": True,
    },
    "premium_permanent": {
        "name": "👑 PREMIUM PERMANENT",
        "daily_limit": 50,
        "use_own_gmail": False,
        "can_add_gmail": True,
        "max_gmail": 10,
        "price": 15000,
        "duration_days": 99999,
        "warp": True,
        "auto_reply": True,
    },
    "owner": {
        "name": "👑 OWNER",
        "daily_limit": 99999,
        "use_own_gmail": False,
        "can_add_gmail": True,
        "max_gmail": 10,
        "price": 0,
        "duration_days": 99999,
        "warp": True,
        "auto_reply": True,
    }
}

# ═══════════════════ DEFAULT DATA ═══════════════════
DEFAULT_DATA = {
    "approved_groups": [],
    "paused": False,
    "min_delay": MIN_DELAY,
    "max_delay": MAX_DELAY,
    "total_sent": 0,
    "total_success": 0,
    "total_failed": 0,
}

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return DEFAULT_DATA.copy()
    return DEFAULT_DATA.copy()

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def load_replies():
    if os.path.exists(REPLIES_FILE):
        try:
            with open(REPLIES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_replies(replies):
    with open(REPLIES_FILE, "w", encoding="utf-8") as f:
        json.dump(replies, f, ensure_ascii=False, indent=2)

def load_transactions():
    if os.path.exists(TRANSACTIONS_FILE):
        try:
            with open(TRANSACTIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_transactions(transactions):
    with open(TRANSACTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(transactions, f, ensure_ascii=False, indent=2)

data = load_data()
approved_groups = set(data.get("approved_groups", []))
paused = data.get("paused", False)
MIN_DELAY = int(data.get("min_delay", MIN_DELAY))
MAX_DELAY = int(data.get("max_delay", MAX_DELAY))
users_db = load_users()
transactions_db = load_transactions()

# ═══════════════════ OWNER CHECK ═══════════════════
OWNER_USERNAME = OWNER.lstrip("@").lower()
try:
    OWNER_ID = int(OWNER) if OWNER.isdigit() else None
except:
    OWNER_ID = None

def is_owner(user):
    if OWNER_ID and getattr(user, "id", None) == OWNER_ID:
        return True
    uname = getattr(user, "username", "").lower()
    if uname and uname == OWNER_USERNAME:
        return True
    return False

# ═══════════════════ REFERRAL SYSTEM ═══════════════════
def generate_referral_code():
    """Generate unique 6-char uppercase referral code"""
    chars = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(secrets.choice(chars) for _ in range(6))
        # check uniqueness
        exists = any(u.get("referral_code") == code for u in users_db.values())
        if not exists:
            return code

def get_referral_code(user_id):
    uid = str(user_id)
    user_data = get_user_data(user_id)
    if not user_data.get("referral_code"):
        user_data["referral_code"] = generate_referral_code()
        save_users(users_db)
    return user_data["referral_code"]

def apply_referral(new_user_id, ref_code):
    """Apply referral when new user starts with ref code. Returns referrer id if valid."""
    if not ref_code:
        return None
    ref_code = ref_code.upper().strip()
    if len(ref_code) != 6:
        return None
    
    # Find referrer
    referrer_id = None
    for uid, udata in users_db.items():
        if udata.get("referral_code") == ref_code:
            referrer_id = uid
            break
    
    if not referrer_id:
        return None
    if referrer_id == str(new_user_id):
        return None  # cannot refer self
    
    new_user = get_user_data(new_user_id)
    if new_user.get("referred_by"):
        return None  # already has referrer
    
    new_user["referred_by"] = referrer_id
    new_user["referred_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_users(users_db)
    
    # Notify referrer
    try:
        ref_count = users_db.get(referrer_id, {}).get("referral_count", 0) + 1
        users_db[referrer_id]["referral_count"] = ref_count
        save_users(users_db)
        
        bot.send_message(
            int(referrer_id),
            f"🎉 <b>Referral Baru!</b>\n\n"
            f"User <code>{new_user_id}</code> baru saja bergabung menggunakan kode referral Anda.\n"
            f"Total referral: <b>{ref_count}</b>\n\n"
            f"Anda akan mendapat bonus +5 limit/hari selama 30 hari ketika user ini berhasil upgrade Premium.",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"[REFERRAL NOTIFY] Error: {e}")
    
    return referrer_id

def reward_referrer_on_upgrade(referred_user_id, tier):
    """Give reward to referrer when referred user upgrades"""
    referred_user = get_user_data(referred_user_id)
    referrer_id = referred_user.get("referred_by")
    if not referrer_id:
        return
    
    # Check if already rewarded for this tier
    rewards = referred_user.get("referral_rewards", [])
    if tier in rewards:
        return  # already rewarded
    
    rewards.append(tier)
    referred_user["referral_rewards"] = rewards
    save_users(users_db)
    
    # Add bonus: +5 daily limit for 30 days (stored as referral_bonus_expiry)
    referrer_data = get_user_data(int(referrer_id))
    expiry = datetime.now() + timedelta(days=30)
    referrer_data["referral_bonus_expiry"] = expiry.strftime("%Y-%m-%d")
    referrer_data["referral_bonus_limit"] = referrer_data.get("referral_bonus_limit", 0) + 5
    
    # Also record total earnings
    price = TIER_CONFIG.get(tier, {}).get("price", 0)
    commission = round(price * 0.10)  # 10% commission
    referrer_data["referral_earnings"] = referrer_data.get("referral_earnings", 0) + commission
    referrer_data["total_referral_success"] = referrer_data.get("total_referral_success", 0) + 1
    save_users(users_db)
    
    try:
        bot.send_message(
            int(referrer_id),
            f"💰 <b>KOMISI REFERRAL!</b>\n\n"
            f"Referral Anda (<code>{referred_user_id}</code>) berhasil upgrade ke <b>{TIER_CONFIG[tier]['name']}</b>!\n"
            f"🎁 Bonus: <b>+5 limit/hari</b> selama 30 hari\n"
            f"💵 Komisi: <b>Rp {commission:,}</b> (10%)\n"
            f"📊 Total Penghasilan: <b>Rp {referrer_data['referral_earnings']:,}</b>",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"[REFERRAL REWARD] Error: {e}")

# ═══════════════════ USER MANAGEMENT ═══════════════════
def get_user_tier(user_id):
    uid = str(user_id)
    if uid not in users_db:
        return "free"
    return users_db[uid].get("tier", "free")

def get_user_data(user_id):
    uid = str(user_id)
    if uid not in users_db:
        users_db[uid] = {
            "tier": "free",
            "expiry": None,
            "daily_used": 0,
            "daily_reset": datetime.now().strftime("%Y-%m-%d"),
            "gmail_accounts": [],
            "gmail_apps": [],
            "total_sent": 0,
            "joined": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "referral_code": generate_referral_code(),
            "referred_by": None,
            "referred_at": None,
            "referral_count": 0,
            "referral_rewards": [],
            "referral_bonus_expiry": None,
            "referral_bonus_limit": 0,
            "referral_earnings": 0,
            "total_referral_success": 0,
        }
        save_users(users_db)
    return users_db[uid]

def check_and_reset_daily(user_id):
    user_data = get_user_data(user_id)
    today = datetime.now().strftime("%Y-%m-%d")
    if user_data.get("daily_reset") != today:
        user_data["daily_used"] = 0
        user_data["daily_reset"] = today
        save_users(users_db)
    return user_data

def get_daily_remaining(user_id):
    user_data = check_and_reset_daily(user_id)
    tier = get_user_tier(user_id)
    base_limit = TIER_CONFIG[tier]["daily_limit"]
    
    # Add referral bonus if active
    bonus = 0
    if user_data.get("referral_bonus_expiry"):
        try:
            expiry = datetime.strptime(user_data["referral_bonus_expiry"], "%Y-%m-%d")
            if datetime.now() <= expiry:
                bonus = user_data.get("referral_bonus_limit", 0)
        except:
            pass
    
    return (base_limit + bonus) - user_data.get("daily_used", 0)

def use_daily_quota(user_id, amount=1):
    user_data = check_and_reset_daily(user_id)
    user_data["daily_used"] = user_data.get("daily_used", 0) + amount
    save_users(users_db)

def is_premium_active(user_id):
    user_data = get_user_data(user_id)
    tier = user_data.get("tier", "free")
    if tier == "free" or tier == "owner":
        return tier == "owner"
    expiry_str = user_data.get("expiry")
    if not expiry_str:
        return False
    try:
        expiry = datetime.strptime(expiry_str, "%Y-%m-%d")
        return datetime.now() <= expiry
    except:
        return False

def set_user_tier(user_id, tier, duration_days=None):
    uid = str(user_id)
    user_data = get_user_data(user_id)
    user_data["tier"] = tier
    if duration_days and tier != "owner":
        expiry = datetime.now() + timedelta(days=duration_days)
        user_data["expiry"] = expiry.strftime("%Y-%m-%d")
    else:
        user_data["expiry"] = None
    save_users(users_db)

def get_user_gmails(user_id):
    user_data = get_user_data(user_id)
    tier = get_user_tier(user_id)
    config = TIER_CONFIG[tier]

    gmails = []
    apps = []

    if not config["use_own_gmail"] and OWNER_EMAILS:
        gmails.extend(OWNER_EMAILS)
        apps.extend(OWNER_APPS)

    personal_gmails = user_data.get("gmail_accounts", [])
    personal_apps = user_data.get("gmail_apps", [])
    gmails.extend(personal_gmails)
    apps.extend(personal_apps)

    return gmails, apps

def add_user_gmail(user_id, email, app_password):
    user_data = get_user_data(user_id)
    tier = get_user_tier(user_id)
    max_gmail = TIER_CONFIG[tier]["max_gmail"]

    current = len(user_data.get("gmail_accounts", []))
    if current >= max_gmail:
        return False, f"Maksimal {max_gmail} Gmail untuk tier {TIER_CONFIG[tier]['name']}"

    user_data["gmail_accounts"] = user_data.get("gmail_accounts", []) + [email]
    user_data["gmail_apps"] = user_data.get("gmail_apps", []) + [app_password]
    save_users(users_db)
    return True, None

def del_user_gmail(user_id, index):
    user_data = get_user_data(user_id)
    gmails = user_data.get("gmail_accounts", [])
    apps = user_data.get("gmail_apps", [])

    if 0 <= index < len(gmails):
        gmails.pop(index)
        apps.pop(index)
        user_data["gmail_accounts"] = gmails
        user_data["gmail_apps"] = apps
        save_users(users_db)
        return True
    return False

# ═══════════════════ PAKASIR PAYMENT FUNCTIONS ═══════════════════
def create_pakasir_transaction(order_id, amount):
    """Create QRIS transaction via Pakasir API"""
    if not PAKASIR_PROJECT or not PAKASIR_API_KEY:
        return None, "Pakasir config missing"
    
    url = f"{PAKASIR_API_URL}/transactioncreate/qris"
    payload = {
        "project": PAKASIR_PROJECT,
        "order_id": order_id,
        "amount": amount,
        "api_key": PAKASIR_API_KEY,
    }
    
    try:
        resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
        data = resp.json()
        if resp.status_code == 200 and "payment" in data:
            return data["payment"], None
        else:
            return None, data.get("message", "Unknown error")
    except Exception as e:
        return None, str(e)

def check_pakasir_transaction(order_id, amount):
    """Check transaction status via Pakasir API"""
    if not PAKASIR_PROJECT or not PAKASIR_API_KEY:
        return None, "Pakasir config missing"
    
    url = (
        f"{PAKASIR_API_URL}/transactiondetail"
        f"?project={PAKASIR_PROJECT}"
        f"&amount={amount}"
        f"&order_id={order_id}"
        f"&api_key={PAKASIR_API_KEY}"
    )
    
    try:
        resp = requests.get(url, timeout=30)
        data = resp.json()
        if resp.status_code == 200 and "transaction" in data:
            return data["transaction"], None
        else:
            return None, data.get("message", "Unknown error")
    except Exception as e:
        return None, str(e)

def generate_qr_image(qr_string):
    """Generate QR code image from QR string"""
    if not QR_AVAILABLE:
        return None, "qrcode library not installed"
    
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_string)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf, None
    except Exception as e:
        return None, str(e)

def get_payment_amount(tier):
    """Calculate total amount including Pakasir QRIS fee"""
    price = TIER_CONFIG[tier]["price"]
    fee = calculate_qris_fee(price)
    return price, fee, price + fee

def generate_order_id(user_id, tier):
    """Generate unique order_id for transaction"""
    ts = datetime.now().strftime("%y%m%d%H%M%S")
    rand = secrets.token_hex(3).upper()
    return f"ZLX{user_id}{ts}{rand}"

# ═══════════════════ WARP FUNCTIONS ═══════════════════
def check_warp_status():
    try:
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.settimeout(3)
        result = test_socket.connect_ex((WARP_PROXY_HOST, WARP_PROXY_PORT))
        test_socket.close()
        return result == 0
    except:
        return False

def setup_warp_proxy():
    if not WARP_ENABLED:
        return False
    try:
        socks.set_default_proxy(socks.SOCKS5, WARP_PROXY_HOST, WARP_PROXY_PORT)
        socket.socket = socks.socksocket
        return True
    except Exception as e:
        print(f"[WARP] Error: {e}")
        return False

def reset_proxy():
    try:
        socks.set_default_proxy()
        socket.socket = socket._socketobject if hasattr(socket, '_socketobject') else socket.socket
    except:
        pass

def get_public_ip():
    try:
        import urllib.request
        req = urllib.request.Request('https://api.ipify.org?format=json', headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())['ip']
    except:
        return "Unknown"

def rotate_warp_ip():
    if not WARP_ENABLED:
        return None, "WARP disabled"
    try:
        subprocess.run(["warp-cli", "disconnect"], capture_output=True, timeout=10)
        time.sleep(2)
        result = subprocess.run(["warp-cli", "connect"], capture_output=True, timeout=10)
        if result.returncode == 0:
            time.sleep(3)
            ip = get_public_ip()
            return ip, None
        else:
            return None, "WARP connect failed"
    except FileNotFoundError:
        return get_public_ip(), "WARP CLI not found"
    except Exception as e:
        return None, str(e)


# ═══════════════════ 50 REALISTIC NAMES ═══════════════════
NAMES = [
    "Budi Santoso", "Ahmad Fauzi", "Dewi Lestari", "Rini Wulandari", "Agus Pratama",
    "Siti Aminah", "Hendra Wijaya", "Maya Sari", "Eko Susanto", "Fitriani Rahma",
    "Bayu Aji", "Nurul Hidayah", "Fajar Ramadhan", "Lina Kusuma", "Dedi Kurniawan",
    "Yuni Astuti", "Rudi Hartono", "Ani Susanti", "Wawan Setiawan", "Rina Marlina",
    "Adi Nugroho", "Sri Wahyuni", "Teguh Wibowo", "Diana Putri", "Indra Lesmana",
    "Rina Oktaviani", "Yusuf Maulana", "Mira Andini", "Fahmi Abdullah", "Lestari Dewi",
    "Bambang Surya", "Citra Lestari", "Dodi Firmansyah", "Eva Susanti", "Guntur Wibowo",
    "Hani Pratiwi", "Irfan Hakim", "Joko Widodo", "Kartika Sari", "Lukman Hakim",
    "Mega Utami", "Nanda Pratama", "Oscar Wijaya", "Putri Ayu", "Qori Hidayat",
    "Raka Aditya", "Salsa Nabila", "Taufik Hidayat", "Umi Kulsum", "Vina Panduwinata"
]

# ═══════════════════ 50 APPEAL TEMPLATES ═══════════════════
APPEALS = [
    "Halo Tim WhatsApp, Perkenalkan, saya {name}. Saya ingin mengajukan banding terkait kendala saat mendaftarkan nomor telepon ke WhatsApp. Muncul pesan \"login tidak tersedia\" sehingga proses registrasi tidak bisa dilanjutkan. Mohon peninjauan ulang agar saya dapat menggunakan layanan WhatsApp kembali. Nomor: {number}. Terima kasih. Hormat saya, {name}.",
    "Yth. Tim Support WhatsApp, Saya {name} menghadapi masalah teknis pada aplikasi WhatsApp. Saat verifikasi nomor {number}, sistem menampilkan notifikasi bahwa login tidak tersedia untuk sementara waktu. Saya mohon bantuan teknis untuk mengatasi kendala ini. Atas perhatiannya, saya ucapkan terima kasih. {name}",
    "Kepada Yth. WhatsApp Support, Dengan hormat, saya {name} menyampaikan permohonan peninjauan akun. Nomor {number} tidak dapat melakukan proses aktivasi karena adanya pembatasan login. Saya tidak melakukan pelanggaran kebijakan. Mohon dikembalikan akses saya. Salam, {name}",
    "Halo WhatsApp Team, Nama saya {name}. HP saya tiba-tiba gak bisa login WhatsApp dengan nomor {number}. Muncul tulisan login gak tersedia. Padahal nomor saya aktif dan sering dipakai. Tolong bantu cek ya. Makasih banyak! -{name}",
    "Hi WhatsApp, Saya {name} punya masalah. Nomor {number} gabisa daftar WhatsApp. Ada tulisan merah login tidak tersedia. Saya butuh WhatsApp buat kerja. Tolong diperbaiki. Thanks! {name}",
    "Dear WhatsApp Support Team, My name is {name}. I am writing to appeal a restriction on my WhatsApp account. My phone number {number} is unable to complete registration due to a \"login unavailable\" error. I have not violated any terms. Please review and restore my access. Sincerely, {name}",
    "To the WhatsApp Security Team, I, {name}, am experiencing a login restriction on number {number}. The application states that login is unavailable for security reasons. I request a manual review of my account status. Thank you for your assistance. Regards, {name}",
    "Hey WhatsApp Support, It's {name} here. My number {number} can't log in. Getting some error about login not being available. My number is legit and active. Can you fix this ASAP? Thanks! {name}",
    "Hello, I'm {name}. Having trouble with WhatsApp on {number}. Says login unavailable. Need this for family communication. Please help restore. Best, {name}",
    "Kepada Pasukan WhatsApp, Nama saya {name}. Saya menghadapi masalah log masuk dengan nombor {number}. Aplikasi menunjukkan \"log masuk tidak tersedia\". Saya mohon semakan semula. Terima kasih. Yours sincerely, {name}",
    "Hi WhatsApp, Saya {name}. Nombor {number} tak boleh login. Ada tulisan login tak available. Boleh tolong fix? Thanks! -{name}",
    "Kanggo Tim WhatsApp, Wasta abdi {name}. Nomer {number} teu tiasa login ka WhatsApp. Aya pesen login teu sadia. Mangga dipariksa. Hatur nuhun. {name}",
    "Kagem Tim WhatsApp, Jenengku {name}. Nomer {number} ora iso mlebu WhatsApp. Muncul tulisan login ora kasedhiya. Monggo dipriksa. Matur nuwun. {name}",
    "Horas WhatsApp Team, Ahu {name}. Nomor {number} ndang boi login. Ada hata login ndang tersedia. Tulong pariksa. Mauliate. {name}",
    "Untuak Tim WhatsApp, Namo den {name}. Nomor {number} indak dapek login. Ada tulisan login indak tersedia. Tolong diperiksa. Tarimo kasih. {name}",
    "Halo WhatsApp, Saya {name}. Nomor {number} got login unavailable error. Saya butuh banget buat komunikasi kerja. Please help to fix this issue. Thank you. {name}",
    "Dear WhatsApp, Ini {name}. My number {number} tidak bisa login karena alasan keamanan. I need this for urgent business. Mohon bantuannya. Regards, {name}",
    "Halo, saya {name}. Kemarin saya ganti HP baru dan coba install WhatsApp. Pas masukin nomor {number}, muncul tulisan login tidak tersedia. Saya bingung karena nomor ini sudah saya pakai 5 tahun. Mohon bantuannya. Terima kasih. {name}",
    "Selamat pagi WhatsApp Team, Saya {name} wirausaha online. Nomor {number} adalah nomor utama saya untuk bisnis. Tiba-tiba tidak bisa login WhatsApp. Ada keterangan login tidak tersedia. Saya kehilangan banyak pelanggan. Mohon segera ditindaklanjuti. {name}",
    "Halo, nama saya {name}. Saya baru saja pulang dari luar negeri. Pas coba login WhatsApp dengan nomor {number}, muncul pesan login tidak tersedia. Mungkin karena saya pakai roaming? Mohon penjelasan dan solusi. Terima kasih. {name}",
    "Dear WhatsApp, Saya {name} ibu rumah tangga. Nomor {number} saya tidak bisa login WhatsApp sejak semalam. Saya butuh kontak dengan anak yang kuliah di luar kota. Mohon bantuannya. Terima kasih banyak. {name}",
    "Halo Tim WhatsApp, Perkenalkan {name}. Saya programmer freelance. Nomor {number} saya terkunci dari WhatsApp dengan pesan login unavailable. Ini sangat mengganggu pekerjaan saya. Mohon review manual. Thanks. {name}",
    "WhatsApp Support, Device: Android 14. Issue: Login unavailable for {number}. Steps taken: Clear cache, reinstall, restart phone. Result: Still blocked. Request: Manual account review. User: {name}",
    "Bug Report - WhatsApp v2.24. Number {number} cannot authenticate. Error: Login unavailable for security reasons. Device info available upon request. Urgency: High. Reporter: {name}",
    "WhatsApp please help! I'm {name} and my number {number} is blocked. I have sick parents I need to check on daily via WhatsApp. Please restore my access. I'm begging you. {name}",
    "Dear WhatsApp Team, This is urgent. My name is {name}. My number {number} shows login unavailable. I have a job interview via WhatsApp tomorrow. Please help me. God bless. {name}",
    "{name} - {number} - Login unavailable - Please fix",
    "Account appeal: {number}. User: {name}. Issue: Cannot login. Action requested: Review and restore.",
    "Formal Complaint - To WhatsApp Inc. Subject: Account restriction without cause. Account: {number}. Complainant: {name}. I demand explanation per user agreement section 4.2. Please respond within 48 hours.",
    "Business Account Recovery Request. Company contact: {name}. Registered number: {number}. Issue: Login unavailable affecting business operations. Revenue impact: Significant. Request immediate restoration.",
    "WhatsApp Business Support, Our registered business number {number} under manager {name} is experiencing login restrictions. This is affecting customer service. Please escalate to technical team.",
    "Hi WhatsApp, I'm {name}. My family group chat is on {number}. Now I can't login. Says unavailable. My elderly parents are waiting for my messages. Please help. {name}",
    "Hello, I'm {name}, university student. My number {number} can't access WhatsApp. I need it for class group discussions. Login shows unavailable. Please assist. Thank you. {name}",
    "WhatsApp Support, Student {name} here. Number {number} blocked from login. Need for school project coordination. Error: Login unavailable. Please review. {name}",
    "Dear WhatsApp, I am {name}, 65 years old. My children set up WhatsApp for me on {number}. Now it says cannot login. I don't understand technology. Please help this old man. {name}",
    "URGENT: {name} - {number} - Cannot login WhatsApp. Login unavailable error. Need immediate restoration for emergency communication. Time sensitive.",
    "PRIORITY REQUEST - User {name}, number {number}. Complete login blockage. Security reason cited. No prior warning. Request emergency review and immediate restoration.",
    "Hello WhatsApp, {name} here. Why is my number {number} showing login unavailable? I haven't done anything wrong. Can someone explain and fix this? Thanks. {name}",
    "WhatsApp team, what happened to my account? Number {number} cannot login. Says unavailable for security. I need answers. Please contact me. {name}",
    "Dear WhatsApp, If I did something wrong, I apologize. My name is {name}. Number {number} is blocked. Please give me another chance. I need WhatsApp for work. Sorry and thank you. {name}",
    "WhatsApp Technical Team, User: {name}, Number: {number}, Device: Samsung Galaxy S23, OS: Android 14, App Version: Latest from Play Store. Issue: Login unavailable (security). Frequency: Every attempt. Duration: 3 days. Request: Technical review and resolution.",
    "Please help me login to WhatsApp. Name: {name}. Number: {number}. Error: Login unavailable. Thank you.",
    "WhatsApp please fix my account. I'm {name}. My number is {number}. Can't login. Shows unavailable. Help please.",
    "Good day WhatsApp Support, I am {name}, a professional user. My registered number {number} is experiencing a login restriction citing security concerns. I assure you my usage complies with all terms. Kindly review and restore. Best regards.",
    "Hello, I'm {name}. I don't know why but my WhatsApp on {number} says login unavailable. I just use it to chat with family. Nothing bad. Please help me understand. {name}",
    "Hi WhatsApp, {name} here. I was traveling and now back home. My number {number} cannot login. Says unavailable. Maybe because I used different networks? Please check. {name}",
    "Hello WhatsApp, I got a new phone and trying to setup WhatsApp with {number}. But it says login unavailable. Old phone is broken. Please help me transfer. {name}",
    "WhatsApp Security, I lost my phone and got new SIM for {number}. Cannot login to WhatsApp. Says unavailable. Need to recover my account urgently. Please verify my identity. {name}",
    "WhatsApp Help, I enabled 2FA on {number} but now can't login. Says login unavailable. I remember my PIN but system won't let me enter it. Please help restore. {name}",
    "Hi, {name} here. After updating WhatsApp, my number {number} shows login unavailable. Tried reinstalling. Didn't help. Please fix this bug. {name}",
]

# ═══════════════════ UTILITIES ═══════════════════
def normalize_number(num):
    num = num.strip()
    if num.startswith("+"):
        return ''.join(c for c in num if c in "+0123456789")
    num = ''.join(c for c in num if c.isdigit())
    if not num:
        return ""
    if num.startswith("0"):
        return "+62" + num[1:]
    if num.startswith("62"):
        return "+" + num
    if num.startswith("8"):
        return "+62" + num
    return "+" + num

def parse_numbers(text):
    parts = text.replace(",", "\n").replace(";", "\n").split()
    seen = set()
    result = []
    for p in parts:
        n = normalize_number(p.strip())
        if n and n not in seen:
            seen.add(n)
            result.append(n)
    return result

def get_random_appeal(number):
    name = random.choice(NAMES)
    template = random.choice(APPEALS)
    return template.format(name=name, number=number)

def get_random_subject():
    subjects = [
        "Appeal: Login Unavailable - Account Review Requested",
        "Urgent: Cannot Access WhatsApp - Number Blocked",
        "Help Needed: WhatsApp Login Restriction",
        "Account Recovery Request - Login Unavailable Error",
        "Technical Support: Unable to Login WhatsApp",
        "Banding: Kendala Login WhatsApp",
        "Permohonan Bantuan: Akun WhatsApp Terkunci",
        "WhatsApp Access Issue - Immediate Attention Required",
        "Login Unavailable Error - Please Investigate",
        "Request for Account Restoration",
        "WhatsApp Security Review Needed",
        "Cannot Verify Number - Login Unavailable",
        "Account Appeal - Number Restriction",
        "WhatsApp Login Problem - Need Assistance",
        "Pengajuan Banding WhatsApp",
        "Mohon Bantuan Teknis WhatsApp",
        "WhatsApp Account Under Review",
        "Login Restriction Appeal",
        "WhatsApp Number Blocked - Help",
        "Request Manual Account Review",
    ]
    return random.choice(subjects)


# ═══════════════════ EMAIL SENDING WITH WARP ═══════════════════
email_lock = threading.Lock()
email_index = 0

def get_next_email(gmails):
    global email_index
    if not gmails:
        return None, None, None
    with email_lock:
        idx = email_index % len(gmails)
        email_index += 1
    return f"mailv{idx+1}", gmails[idx]

def send_appeal_email(number, email, app_password, support_email, use_warp=True, max_retries=2):
    body = get_random_appeal(number)
    subject = get_random_subject()

    if use_warp and WARP_ENABLED:
        setup_warp_proxy()
        ip, err = rotate_warp_ip()
        if ip:
            print(f"[WARP] IP: {ip}")

    for attempt in range(max_retries):
        try:
            msg = MIMEMultipart()
            msg["Subject"] = subject
            msg["From"] = email
            msg["To"] = support_email
            msg.attach(MIMEText(body, "plain", "utf-8"))

            server = smtplib.SMTP("smtp.gmail.com", 587, timeout=20)
            server.starttls()
            server.login(email, app_password)
            server.sendmail(email, support_email, msg.as_string())
            server.quit()

            if use_warp and WARP_ENABLED:
                reset_proxy()
            return True, None
        except Exception as e:
            if attempt == max_retries - 1:
                if use_warp and WARP_ENABLED:
                    reset_proxy()
                return False, str(e)
            time.sleep(2)

    if use_warp and WARP_ENABLED:
        reset_proxy()
    return False, "Max retries"

# ═══════════════════ AUTO-REPLY DETECTION ═══════════════════
def check_email_replies(email, app_password, label, chat_id_notify=None):
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", timeout=20)
        mail.login(email, app_password)
        mail.select("inbox")

        for support in SUPPORT_EMAILS:
            _, search_data = mail.search(None, f'FROM "{support}" UNSEEN')
            email_ids = search_data[0].split()

            for e_id in email_ids[-5:]:
                _, data = mail.fetch(e_id, "(RFC822)")
                raw_email = data[0][1]
                email_msg = emaillib.message_from_bytes(raw_email)

                from_addr = email_msg["From"]
                subject = email_msg["Subject"] or "No Subject"

                body = ""
                if email_msg.is_multipart():
                    for part in email_msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode("utf-8", errors="ignore")[:500]
                            break
                else:
                    body = email_msg.get_payload(decode=True).decode("utf-8", errors="ignore")[:500]

                replies = load_replies()
                reply_key = f"{label}_{e_id.decode()}"

                if reply_key not in replies:
                    replies[reply_key] = {
                        "from": from_addr,
                        "subject": subject,
                        "body": body,
                        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "notified": False
                    }
                    save_replies(replies)

                    if chat_id_notify and not replies[reply_key]["notified"]:
                        try:
                            bot.send_message(
                                chat_id_notify,
                                f"📩 <b>BALASAN WHATSAPP SUPPORT!</b>\n\n"
                                f"📧 Gmail: <code>{label}</code>\n"
                                f"📨 Dari: <code>{from_addr}</code>\n"
                                f"📝 Subject: <b>{subject}</b>\n"
                                f"\n"
                                f"<pre>{body[:300]}</pre>",
                                parse_mode="HTML"
                            )
                            replies[reply_key]["notified"] = True
                            save_replies(replies)
                        except:
                            pass

        mail.close()
        mail.logout()
        return True
    except Exception as e:
        print(f"[AUTO-REPLY] Error: {e}")
        return False

def auto_reply_worker(chat_id=None):
    while AUTO_REPLY_ENABLED:
        for i, (email, app) in enumerate(zip(OWNER_EMAILS, OWNER_APPS)):
            label = f"mailv{i+1}"
            check_email_replies(email, app, label, chat_id)
            time.sleep(5)
        time.sleep(AUTO_REPLY_INTERVAL)

def start_auto_reply(chat_id=None):
    if not AUTO_REPLY_ENABLED or not OWNER_EMAILS:
        return None
    t = threading.Thread(target=auto_reply_worker, args=(chat_id,), daemon=True)
    t.start()
    auto_reply_threads[chat_id] = t
    return t

# ═══════════════════ KEYBOARD BUILDERS ═══════════════════
def main_menu_keyboard(user):
    user_id = user.id
    tier = get_user_tier(user_id)
    config = TIER_CONFIG[tier]
    remaining = get_daily_remaining(user_id)

    kb = types.InlineKeyboardMarkup(row_width=2)

    if is_owner(user):
        kb.add(
            types.InlineKeyboardButton("🚀 KIRIM BANDING", callback_data="menu_banding"),
            types.InlineKeyboardButton(f"📊 STATISTIK", callback_data="menu_stats"),
            types.InlineKeyboardButton("⚙️ PENGATURAN", callback_data="menu_settings"),
            types.InlineKeyboardButton("👤 PROFIL", callback_data="menu_profile"),
            types.InlineKeyboardButton("📧 GMAIL", callback_data="menu_gmail"),
            types.InlineKeyboardButton("📩 BALASAN", callback_data="menu_replies"),
        )
        kb.add(
            types.InlineKeyboardButton("🔴 BREAK", callback_data="cmd_break"),
            types.InlineKeyboardButton("🟢 GAS", callback_data="cmd_gas"),
        )
        kb.add(
            types.InlineKeyboardButton("➕ ADD GROUP", callback_data="cmd_addgroup"),
            types.InlineKeyboardButton("👑 USERS", callback_data="cmd_users"),
        )
        kb.add(
            types.InlineKeyboardButton("🌐 WARP", callback_data="warp_status"),
            types.InlineKeyboardButton("💰 HARGA", callback_data="menu_pricing"),
        )
        kb.add(
            types.InlineKeyboardButton("🔗 REFERRAL", callback_data="menu_referral"),
        )
    else:
        kb.add(
            types.InlineKeyboardButton("🚀 KIRIM BANDING", callback_data="menu_banding"),
            types.InlineKeyboardButton(f"📊 STATISTIK", callback_data="menu_stats"),
        )
        kb.add(
            types.InlineKeyboardButton("👤 PROFIL", callback_data="menu_profile"),
            types.InlineKeyboardButton("📧 GMAIL", callback_data="menu_gmail"),
        )
        if config["auto_reply"]:
            kb.add(
                types.InlineKeyboardButton("📩 BALASAN", callback_data="menu_replies"),
                types.InlineKeyboardButton("🌐 WARP", callback_data="warp_status"),
            )
        else:
            kb.add(
                types.InlineKeyboardButton("💎 UPGRADE", callback_data="menu_pricing"),
                types.InlineKeyboardButton("🔗 REFERRAL", callback_data="menu_referral"),
            )

    kb.add(types.InlineKeyboardButton("❓ BANTUAN", callback_data="menu_help"))
    return kb

def banding_email_keyboard(user_id):
    gmails, apps = get_user_gmails(user_id)
    kb = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for i in range(len(gmails)):
        buttons.append(types.InlineKeyboardButton(f"📧 mailv{i+1}", callback_data=f"band_mailv{i+1}"))
    kb.add(*buttons)
    kb.add(types.InlineKeyboardButton("🔙 KEMBALI", callback_data="menu_main"))
    return kb

def banding_support_keyboard(email_label):
    kb = types.InlineKeyboardMarkup(row_width=1)
    for i, se in enumerate(SUPPORT_EMAILS):
        kb.add(types.InlineKeyboardButton(f"📨 Support {i+1}", callback_data=f"sup_{email_label}_{i}"))
    kb.add(types.InlineKeyboardButton("📨 SEMUA SUPPORT (3x)", callback_data=f"sup_{email_label}_all"))
    kb.add(types.InlineKeyboardButton("🔙 KEMBALI", callback_data="menu_banding"))
    return kb

def confirm_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("✅ YA, KIRIM", callback_data="confirm_yes"),
        types.InlineKeyboardButton("❌ BATAL", callback_data="confirm_no"),
    )
    return kb

def settings_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("⏱️ SET DELAY", callback_data="set_delay"),
        types.InlineKeyboardButton("📋 LIST GROUP", callback_data="list_group"),
        types.InlineKeyboardButton("📋 LIST USERS", callback_data="list_users"),
        types.InlineKeyboardButton("📢 BROADCAST", callback_data="broadcast"),
    )
    kb.add(types.InlineKeyboardButton("🔙 KEMBALI", callback_data="menu_main"))
    return kb

def gmail_menu_keyboard(user_id):
    kb = types.InlineKeyboardMarkup(row_width=2)
    user_data = get_user_data(user_id)
    tier = get_user_tier(user_id)
    config = TIER_CONFIG[tier]

    personal_count = len(user_data.get("gmail_accounts", []))
    max_gmail = config["max_gmail"]

    kb.add(
        types.InlineKeyboardButton(f"📧 Gmail Saya ({personal_count}/{max_gmail})", callback_data="gmail_list"),
    )

    if config["can_add_gmail"] and personal_count < max_gmail:
        kb.add(
            types.InlineKeyboardButton("➕ TAMBAH GMAIL", callback_data="gmail_add"),
        )

    if personal_count > 0:
        kb.add(
            types.InlineKeyboardButton("🗑️ HAPUS GMAIL", callback_data="gmail_del"),
        )

    kb.add(types.InlineKeyboardButton("🔙 KEMBALI", callback_data="menu_main"))
    return kb

def pricing_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=1)
    
    for tier_key in ["premium_basic", "premium_pro", "premium_permanent"]:
        price = TIER_CONFIG[tier_key]["price"]
        fee = calculate_qris_fee(price)
        total = price + fee
        name = TIER_CONFIG[tier_key]["name"]
        kb.add(
            types.InlineKeyboardButton(
                f"{name} - Rp {total:,} (inc. fee)",
                callback_data=f"pay_{tier_key}"
            )
        )
    
    kb.add(types.InlineKeyboardButton("🔙 KEMBALI", callback_data="menu_main"))
    return kb

def payment_status_keyboard(order_id, tier):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🔄 CEK STATUS", callback_data=f"cekpay_{order_id}_{tier}"),
        types.InlineKeyboardButton("❌ BATALKAN", callback_data=f"cancelpay_{order_id}_{tier}"),
    )
    return kb

def referral_keyboard(user_id):
    kb = types.InlineKeyboardMarkup(row_width=1)
    ref_code = get_referral_code(user_id)
    bot_info = bot.get_me()
    bot_username = bot_info.username if bot_info else "bot"
    ref_link = f"https://t.me/{bot_username}?start={ref_code}"
    
    kb.add(types.InlineKeyboardButton("📋 SALIN LINK", url=ref_link))
    kb.add(types.InlineKeyboardButton("🔙 KEMBALI", callback_data="menu_main"))
    return kb

# ═══════════════════ WORKER THREAD ═══════════════════
def worker_send(chat_id, numbers, email_label, support_indices, user, user_gmails, user_apps):
    global paused, data

    idx = int(email_label.replace("mailv", "")) - 1
    email = user_gmails[idx]
    app = user_apps[idx]

    total = len(numbers) * len(support_indices)
    sent = 0
    success = 0
    failed = 0

    tier = get_user_tier(user.id)
    use_warp = TIER_CONFIG[tier]["warp"]

    try:
        bot.edit_message_text(
            f"⏳ <b>MEMULAI PENGIRIMAN...</b>\n\n"
            f"📧 Email: <code>{email_label}</code>\n"
            f"📨 Target: {len(support_indices)} support\n"
            f"📱 Nomor: {len(numbers)}\n"
            f"📊 Total: {total} email\n"
            f"🌐 WARP: <b>{'AKTIF' if use_warp else 'NONAKTIF'}</b>",
            chat_id=chat_id,
            message_id=user_state.get(chat_id, {}).get("msg_id"),
            parse_mode="HTML"
        )
    except:
        pass

    for num in numbers:
        if paused:
            try:
                bot.send_message(chat_id, "⏸️ <b>BOT DIHENTIKAN OWNER</b>", parse_mode="HTML")
            except:
                pass
            return

        for sup_idx in support_indices:
            if paused:
                return

            support_email = SUPPORT_EMAILS[sup_idx]
            delay = random.randint(MIN_DELAY, MAX_DELAY)

            if use_warp:
                ip, warp_err = rotate_warp_ip()
                if ip:
                    print(f"[WARP] IP: {ip}")

            time.sleep(delay)

            ok, err = send_appeal_email(num, email, app, support_email, use_warp=use_warp)
            sent += 1

            if ok:
                success += 1
                data["total_success"] = data.get("total_success", 0) + 1
                use_daily_quota(user.id)
                try:
                    bot.send_message(
                        chat_id,
                        f"✅ <b>TERKIRIM</b>\n"
                        f"📱 <code>{num}</code>\n"
                        f"📨 Support {sup_idx+1}\n"
                        f"📧 {email_label}\n"
                        f"⏱️ Delay: {delay}s",
                        parse_mode="HTML"
                    )
                except:
                    pass
            else:
                failed += 1
                data["total_failed"] = data.get("total_failed", 0) + 1
                try:
                    bot.send_message(
                        chat_id,
                        f"❌ <b>GAGAL</b>\n"
                        f"📱 <code>{num}</code>\n"
                        f"📨 Support {sup_idx+1}\n"
                        f"⚠️ {str(err)[:100]}",
                        parse_mode="HTML"
                    )
                except:
                    pass

            data["total_sent"] = data.get("total_sent", 0) + 1
            save_data(data)

    try:
        bot.send_message(
            chat_id,
            f"🎉 <b>SELESAI!</b>\n\n"
            f"📊 Statistik:\n"
            f"✅ Berhasil: {success}\n"
            f"❌ Gagal: {failed}\n"
            f"📦 Total: {sent}",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(user)
        )
    except:
        pass

    if chat_id in user_state:
        del user_state[chat_id]

# ═══════════════════ PAYMENT POLLING WORKER ═══════════════════
def payment_polling_worker(chat_id, user_id, order_id, tier, amount, msg_id):
    """Poll Pakasir transaction status every 10s for up to 15 minutes"""
    max_checks = 90  # 15 minutes
    check_interval = 10
    
    for i in range(max_checks):
        time.sleep(check_interval)
        
        txn, err = check_pakasir_transaction(order_id, amount)
        if err:
            print(f"[PAY POLL] Error: {err}")
            continue
        
        status = txn.get("status", "")
        
        if status == "completed":
            # Activate premium
            duration = TIER_CONFIG[tier]["duration_days"]
            set_user_tier(user_id, tier, duration if duration < 99999 else None)
            
            # Save to transactions
            transactions_db[order_id]["status"] = "completed"
            transactions_db[order_id]["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_transactions(transactions_db)
            
            # Reward referrer if exists
            reward_referrer_on_upgrade(user_id, tier)
            
            try:
                bot.edit_message_text(
                    f"🔴 <b>𝗣𝗘𝗠𝗕𝗔𝗬𝗔𝗥𝗔𝗡 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 — 𝗙𝗶𝘅𝗠𝗲𝗿𝗮𝗵 × 𝗭𝘆𝗹𝗶𝘅</b>\n\n"
                    f"💎 Tier: <b>{TIER_CONFIG[tier]['name']}</b>\n"
                    f"💰 Amount: <b>Rp {amount:,}</b>\n"
                    f"⏰ Diaktifkan: <b>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</b>\n\n"
                    f"✅ Selamat! Akun Anda sudah upgrade!\n"
                    f"👥 Community: @FixMerahCommunity\n"
                    f"📢 Official: @FixMerahOfficial\n\n"
                    f"Klik /start untuk menu utama.",
                    chat_id=chat_id,
                    message_id=msg_id,
                    parse_mode="HTML"
                )
            except Exception as e:
                print(f"[PAY POLL] Edit msg error: {e}")
                try:
                    bot.send_message(
                        chat_id,
                        f"✅ <b>PEMBAYARAN BERHASIL!</b>\n\n"
                        f"💎 Tier: <b>{TIER_CONFIG[tier]['name']}</b>\n"
                        f"📊 Amount: <b>Rp {amount:,}</b>\n\n"
                        f"Selamat! Akun Anda sudah upgrade.\n"
                        f"Klik /start untuk menu utama.",
                        parse_mode="HTML"
                    )
                except:
                    pass
            return
        
        elif status in ["expired", "failed", "cancelled"]:
            transactions_db[order_id]["status"] = status
            save_transactions(transactions_db)
            try:
                bot.edit_message_text(
                    f"❌ <b>PEMBAYARAN GAGAL / EXPIRED</b>\n\n"
                    f"Order ID: <code>{order_id}</code>\n"
                    f"Status: <b>{status.upper()}</b>\n\n"
                    f"Silakan coba lagi dengan klik 💎 UPGRADE.",
                    chat_id=chat_id,
                    message_id=msg_id,
                    parse_mode="HTML"
                )
            except:
                pass
            return
    
    # Timeout after 15 minutes
    try:
        bot.edit_message_text(
            f"⏰ <b>PEMBAYARAN MENUNGGU</b>\n\n"
            f"Order ID: <code>{order_id}</code>\n"
            f"Status belum terkonfirmasi dalam 15 menit.\n\n"
            f"Jika sudah bayar, klik 🔄 CEK STATUS di menu.\n"
            f"Jika ingin batal, klik ❌ BATALKAN.",
            chat_id=chat_id,
            message_id=msg_id,
            parse_mode="HTML",
            reply_markup=payment_status_keyboard(order_id, tier)
        )
    except:
        pass

# ═══════════════════ HANDLERS ═══════════════════

@bot.message_handler(commands=["start"])
def handle_start(message):
    user = message.from_user
    chat_id = message.chat.id
    
    # Parse referral from deep link /start REFCODE
    ref_code = None
    if message.text and len(message.text.split()) > 1:
        parts = message.text.split(maxsplit=1)
        if len(parts) == 2:
            ref_code = parts[1].strip().upper()
    
    # Register user if new
    get_user_data(user.id)
    
    # Apply referral if valid
    if ref_code:
        referrer = apply_referral(user.id, ref_code)
        if referrer:
            try:
                bot.send_message(
                    chat_id,
                    f"🎉 <b>Kode Referral Berhasil Digunakan!</b>\n\n"
                    f"Anda bergabung menggunakan referral dari user <code>{referrer}</code>.\n"
                    f"Upgrade Premium sekarang dan referrer Anda akan mendapat bonus!",
                    parse_mode="HTML"
                )
            except:
                pass

    if message.chat.type == "private" and not is_owner(user):
        if not is_premium_active(user.id):
            tier = get_user_tier(user.id)
            if tier.startswith("premium"):
                set_user_tier(user.id, "free")

    if message.chat.type in ["group", "supergroup"] and chat_id not in approved_groups:
        bot.reply_to(message,
            "❌ <b>GRUP BELUM TERDAFTAR</b>\n"
            "Hubungi owner untuk aktivasi.",
            parse_mode="HTML")
        return

    if AUTO_REPLY_ENABLED and chat_id not in auto_reply_threads:
        start_auto_reply(chat_id)

    tier = get_user_tier(user.id)
    config = TIER_CONFIG[tier]
    remaining = get_daily_remaining(user.id)

    welcome_text = (
        f"👋 <b>Halo {user.first_name}!</b>\n\n"
        f"🔴 <b>𝗙𝗶𝘅𝗠𝗲𝗿𝗮𝗵 𝗕𝗼𝘁 × 𝗭𝘆𝗹𝗶𝘅 🚀</b>\n"
        f"📌 Versi: 4.1\n"
        f"👤 Status: <b>{config['name']}</b>\n"
        f"📊 Limit Harian: <b>{remaining}</b>/{config['daily_limit']}\n"
        f"📧 Gmail: <b>{len(get_user_gmails(user.id)[0])}</b> akun\n"
        f"📨 Support: <b>{len(SUPPORT_EMAILS)}</b> email\n"
        f"📝 Template: <b>{len(APPEALS)}</b> banding\n"
        f"🌐 WARP: <b>{'AKTIF ✓' if config['warp'] else 'NONAKTIF ✗'}</b>\n"
        f"📩 Auto-Reply: <b>{'AKTIF ✓' if config['auto_reply'] else 'NONAKTIF ✗'}</b>\n\n"
        f"Pilih menu di bawah:"
    )

    bot.send_message(
        message.chat.id,
        welcome_text,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(user)
    )


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user = call.from_user
    chat_id = call.message.chat.id
    data_cb = call.data
    global paused

    if call.message.chat.type == "private" and not is_owner(user):
        if not is_premium_active(user.id):
            bot.answer_callback_query(call.id, "🚫 Premium expired! Upgrade di /start")
            return

    if call.message.chat.type in ["group", "supergroup"] and chat_id not in approved_groups:
        bot.answer_callback_query(call.id, "❌ Grup belum terdaftar!")
        return

    # ═══ MAIN MENU ═══
    if data_cb == "menu_main":
        tier = get_user_tier(user.id)
        config = TIER_CONFIG[tier]
        remaining = get_daily_remaining(user.id)

        welcome_text = (
            f"🔴 <b>𝗛𝗮𝗹𝗼 {user.first_name}!</b>\n\n"
            f"<b>🔴 𝗙𝗶𝘅𝗠𝗲𝗿𝗮𝗵 𝗕𝗼𝘁 × 𝗭𝘆𝗹𝗶𝘅 🚀</b>\n"
            f"📌 Versi: <b>4.1</b> | 👤 Owner: <b>@anzajun</b>\n"
            f"👥 Community: <b>@FixMerahCommunity</b>\n"
            f"📢 Official: <b>@FixMerahOfficial</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Status: <b>{config['name']}</b>\n"
            f"📊 Limit Harian: <b>{remaining}</b>/{config['daily_limit']}\n"
            f"📧 Gmail: <b>{len(get_user_gmails(user.id)[0])}</b> akun\n"
            f"📨 Support: <b>{len(SUPPORT_EMAILS)}</b> email\n"
            f"📝 Template: <b>{len(APPEALS)}</b> banding\n"
            f"🌐 WARP: <b>{'AKTIF ✓' if config['warp'] else 'NONAKTIF ✗'}</b>\n"
            f"📩 Auto-Reply: <b>{'AKTIF ✓' if config['auto_reply'] else 'NONAKTIF ✗'}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Pilih menu di bawah:"
        )
        bot.edit_message_text(welcome_text, chat_id=chat_id, message_id=call.message.message_id,
                             parse_mode="HTML", reply_markup=main_menu_keyboard(user))
        bot.answer_callback_query(call.id, "🏠 Menu utama")
        return

    # ═══ BANDING MENU ═══
    if data_cb == "menu_banding":
        gmails, apps = get_user_gmails(user.id)
        if not gmails:
            bot.answer_callback_query(call.id, "❌ Belum ada Gmail! Tambah di menu Gmail")
            return

        remaining = get_daily_remaining(user.id)
        if remaining <= 0:
            bot.answer_callback_query(call.id, "❌ Limit harian habis! Tunggu besok atau upgrade")
            return

        text = (
            f"🚀 <b>KIRIM BANDING</b>\n"
            f"📊 Sisa limit hari ini: <b>{remaining}</b>\n\n"
            f"1️⃣ Pilih Gmail yang akan digunakan\n"
            f"2️⃣ Pilih Support WhatsApp target\n"
            f"3️⃣ Kirim nomor WhatsApp (bisa banyak)\n\n"
            f"📧 Gmail tersedia:"
        )
        bot.edit_message_text(text, chat_id=chat_id, message_id=call.message.message_id,
                             parse_mode="HTML", reply_markup=banding_email_keyboard(user.id))
        bot.answer_callback_query(call.id, "🚀 Kirim banding")
        return

    # ═══ SELECT EMAIL FOR BANDING ═══
    if data_cb.startswith("band_mailv"):
        email_label = data_cb.replace("band_", "")
        text = (
            f"📧 <b>{email_label}</b> dipilih!\n\n"
            f"Pilih target support WhatsApp:\n"
            f"• Support 1: <code>{SUPPORT_EMAILS[0]}</code>\n"
            f"• Support 2: <code>{SUPPORT_EMAILS[1]}</code>\n"
            f"• Support 3: <code>{SUPPORT_EMAILS[2]}</code>\n\n"
            f"<b>SEMUA SUPPORT</b> = kirim ke 3 support sekaligus"
        )
        bot.edit_message_text(text, chat_id=chat_id, message_id=call.message.message_id,
                             parse_mode="HTML", reply_markup=banding_support_keyboard(email_label))
        bot.answer_callback_query(call.id, f"📧 {email_label}")
        return

    # ═══ SELECT SUPPORT ═══
    if data_cb.startswith("sup_"):
        parts = data_cb.split("_")
        email_label = parts[1]
        sup_type = parts[2]

        if sup_type == "all":
            support_indices = list(range(len(SUPPORT_EMAILS)))
        else:
            support_indices = [int(sup_type)]

        user_state[chat_id] = {
            "state": "INPUT_NUMBERS",
            "email_label": email_label,
            "support_indices": support_indices,
            "msg_id": call.message.message_id
        }

        text = (
            f"✅ <b>Konfigurasi:</b>\n"
            f"📧 Gmail: <code>{email_label}</code>\n"
            f"📨 Target: {len(support_indices)} support\n\n"
            f"📱 <b>Kirim nomor WhatsApp sekarang!</b>\n"
            f"Bisa 1 nomor atau banyak (pisah dengan enter):\n\n"
            f"<i>Contoh:</i>\n"
            f"<code>08123456789</code>\n"
            f"<code>+628123456789</code>"
        )
        bot.edit_message_text(text, chat_id=chat_id, message_id=call.message.message_id,
                             parse_mode="HTML")
        bot.answer_callback_query(call.id, "📱 Input nomor")
        return

    # ═══ CONFIRM YES ═══
    if data_cb == "confirm_yes":
        state = user_state.get(chat_id)
        if not state or state.get("state") != "CONFIRM":
            bot.answer_callback_query(call.id, "⚠️ Session expired!")
            return

        numbers = state["numbers"]
        email_label = state["email_label"]
        support_indices = state["support_indices"]

        gmails, apps = get_user_gmails(user.id)

        bot.edit_message_text(
            f"🚀 <b>MEMULAI PENGIRIMAN {len(numbers)} BANDING...</b>",
            chat_id=chat_id, message_id=call.message.message_id, parse_mode="HTML"
        )

        t = threading.Thread(
            target=worker_send,
            args=(chat_id, numbers, email_label, support_indices, user, gmails, apps),
            daemon=True
        )
        t.start()
        sending_threads[chat_id] = t

        bot.answer_callback_query(call.id, "🚀 Mengirim banding...")
        return

    # ═══ CONFIRM NO ═══
    if data_cb == "confirm_no":
        if chat_id in user_state:
            del user_state[chat_id]
        bot.edit_message_text(
            "❌ <b>DIBATALKAN</b>\n\nPilih menu:",
            chat_id=chat_id, message_id=call.message.message_id,
            parse_mode="HTML", reply_markup=main_menu_keyboard(user)
        )
        bot.answer_callback_query(call.id, "❌ Dibatalkan")
        return

    # ═══ STATS ═══
    if data_cb == "menu_stats":
        tier = get_user_tier(user.id)
        config = TIER_CONFIG[tier]
        remaining = get_daily_remaining(user.id)
        user_data = get_user_data(user.id)

        text = (
            f"🔴 <b>𝗦𝗧𝗔𝗧𝗜𝗦𝗧𝗜𝗞 — 𝗙𝗶𝘅𝗠𝗲𝗿𝗮𝗵 × 𝗭𝘆𝗹𝗶𝘅</b>\n\n"
            f"👤 Tier: <b>{config['name']}</b>\n"
            f"📊 Limit Harian: <b>{remaining}</b>/{config['daily_limit']}\n"
            f"📨 Total Terkirim: <b>{user_data.get('total_sent', 0)}</b>\n"
            f"📧 Gmail: <b>{len(get_user_gmails(user.id)[0])}</b> akun\n"
            f"⏱️ Delay: <b>{MIN_DELAY}-{MAX_DELAY}</b> detik\n"
            f"🌐 WARP: <b>{'AKTIF' if config['warp'] else 'NONAKTIF'}</b>\n"
            f"📩 Auto-Reply: <b>{'AKTIF' if config['auto_reply'] else 'NONAKTIF'}</b>\n"
        )

        if user_data.get("expiry"):
            text += f"⏰ Expiry: <b>{user_data['expiry']}</b>\n"
        
        # Referral bonus info
        if user_data.get("referral_bonus_expiry"):
            try:
                expiry = datetime.strptime(user_data["referral_bonus_expiry"], "%Y-%m-%d")
                if datetime.now() <= expiry:
                    text += f"🔗 Bonus Referral: <b>+{user_data.get('referral_bonus_limit', 0)}/hari</b> s/d <b>{user_data['referral_bonus_expiry']}</b>\n"
            except:
                pass
        
        if user_data.get("referral_earnings", 0) > 0:
            text += f"💵 Total Komisi: <b>Rp {user_data['referral_earnings']:,}</b>\n"

        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔙 KEMBALI", callback_data="menu_main"))
        bot.edit_message_text(text, chat_id=chat_id, message_id=call.message.message_id,
                             parse_mode="HTML", reply_markup=kb)
        bot.answer_callback_query(call.id, "📊 Statistik")
        return

    # ═══ PROFILE ═══
    if data_cb == "menu_profile":
        tier = get_user_tier(user.id)
        config = TIER_CONFIG[tier]
        user_data = get_user_data(user.id)
        remaining = get_daily_remaining(user.id)

        text = (
            f"🔴 <b>𝗣𝗥𝗢𝗙𝗜𝗟 — 𝗙𝗶𝘅𝗠𝗲𝗿𝗮𝗵 × 𝗭𝘆𝗹𝗶𝘅</b>\n\n"
            f"🆔 ID: <code>{user.id}</code>\n"
            f"👤 Nama: {user.first_name}\n"
            f"📛 Username: @{user.username or 'N/A'}\n"
            f"👑 Status: <b>{config['name']}</b>\n"
            f"📊 Limit: <b>{remaining}</b>/{config['daily_limit']} per hari\n"
            f"📧 Gmail: <b>{len(get_user_gmails(user.id)[0])}</b> akun\n"
            f"📨 Total Kirim: <b>{user_data.get('total_sent', 0)}</b>\n"
            f"📅 Bergabung: <b>{user_data.get('joined', 'N/A')}</b>\n\n"
            f"👥 Community: @FixMerahCommunity\n"
            f"📢 Official: @FixMerahOfficial"
        )

        if user_data.get("expiry"):
            text += f"\n⏰ Expiry: <b>{user_data['expiry']}</b>"
        
        if user_data.get("referral_code"):
            text += f"\n\n🔗 Kode Referral: <code>{user_data['referral_code']}</code>"
        
        if user_data.get("referred_by"):
            text += f"\n👥 Referred by: <code>{user_data['referred_by']}</code>"

        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔙 KEMBALI", callback_data="menu_main"))
        bot.edit_message_text(text, chat_id=chat_id, message_id=call.message.message_id,
                             parse_mode="HTML", reply_markup=kb)
        bot.answer_callback_query(call.id, "👤 Profil")
        return


    # ═══ GMAIL MENU ═══
    if data_cb == "menu_gmail":
        gmails, apps = get_user_gmails(user.id)
        tier = get_user_tier(user.id)
        config = TIER_CONFIG[tier]
        user_data = get_user_data(user.id)
        personal = user_data.get("gmail_accounts", [])

        text = (
            f"📧 <b>MANAJEMEN GMAIL</b>\n\n"
            f"👤 Tier: <b>{config['name']}</b>\n"
            f"📧 Total Gmail: <b>{len(gmails)}</b> akun\n"
            f"📧 Gmail Pribadi: <b>{len(personal)}</b> akun\n"
            f"📧 Gmail Owner: <b>{len(gmails) - len(personal)}</b> akun\n"
            f"➕ Max Tambah: <b>{config['max_gmail']}</b> akun\n\n"
        )

        if not config["use_own_gmail"] and OWNER_EMAILS:
            text += "✅ <b>Gmail owner tersedia otomatis</b>\n"

        if personal:
            text += "\n<b>Gmail Pribadi:</b>\n"
            for i, e in enumerate(personal, 1):
                masked = e[:3] + "***" + e[e.find("@"):]
                text += f"  {i}. <code>{masked}</code>\n"

        bot.edit_message_text(text, chat_id=chat_id, message_id=call.message.message_id,
                             parse_mode="HTML", reply_markup=gmail_menu_keyboard(user.id))
        bot.answer_callback_query(call.id, "📧 Gmail")
        return

    # ═══ GMAIL LIST ═══
    if data_cb == "gmail_list":
        gmails, apps = get_user_gmails(user.id)
        text = "📧 <b>DAFTAR GMAIL AKTIF:</b>\n\n"
        for i, e in enumerate(gmails, 1):
            masked = e[:3] + "***" + e[e.find("@"):]
            text += f"<b>mailv{i}</b>: <code>{masked}</code>\n"

        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔙 KEMBALI", callback_data="menu_gmail"))
        bot.edit_message_text(text, chat_id=chat_id, message_id=call.message.message_id,
                             parse_mode="HTML", reply_markup=kb)
        bot.answer_callback_query(call.id, "📧 List Gmail")
        return

    # ═══ GMAIL ADD ═══
    if data_cb == "gmail_add":
        tier = get_user_tier(user.id)
        config = TIER_CONFIG[tier]
        user_data = get_user_data(user.id)
        personal_count = len(user_data.get("gmail_accounts", []))

        if personal_count >= config["max_gmail"]:
            bot.answer_callback_query(call.id, f"❌ Maksimal {config['max_gmail']} Gmail!")
            return

        user_state[chat_id] = {"state": "ADD_GMAIL"}
        text = (
            "➕ <b>TAMBAH GMAIL</b>\n\n"
            "Kirim format:\n"
            "<code>email@gmail.com|app_password</code>\n\n"
            "<b>Cara dapat App Password:</b>\n"
            "1. Buka myaccount.google.com/apppasswords\n"
            "2. Login & pilih 'Mail'\n"
            "3. Copy 16 digit password\n\n"
            f"Sisa slot: <b>{config['max_gmail'] - personal_count}</b>"
        )
        bot.edit_message_text(text, chat_id=chat_id, message_id=call.message.message_id, parse_mode="HTML")
        bot.answer_callback_query(call.id, "➕ Tambah Gmail")
        return

    # ═══ GMAIL DELETE ═══
    if data_cb == "gmail_del":
        user_data = get_user_data(user.id)
        personal = user_data.get("gmail_accounts", [])

        if not personal:
            bot.answer_callback_query(call.id, "❌ Tidak ada Gmail pribadi!")
            return

        kb = types.InlineKeyboardMarkup(row_width=1)
        for i, e in enumerate(personal):
            masked = e[:3] + "***" + e[e.find("@"):]
            kb.add(types.InlineKeyboardButton(f"🗑️ {masked}", callback_data=f"del_gmail_{i}"))
        kb.add(types.InlineKeyboardButton("🔙 KEMBALI", callback_data="menu_gmail"))

        text = "🗑️ <b>PILIH GMAIL YANG AKAN DIHAPUS:</b>"
        bot.edit_message_text(text, chat_id=chat_id, message_id=call.message.message_id,
                             parse_mode="HTML", reply_markup=kb)
        bot.answer_callback_query(call.id, "🗑️ Hapus Gmail")
        return

    if data_cb.startswith("del_gmail_"):
        idx = int(data_cb.replace("del_gmail_", ""))
        if del_user_gmail(user.id, idx):
            bot.answer_callback_query(call.id, "✅ Gmail dihapus!")
        else:
            bot.answer_callback_query(call.id, "❌ Gagal hapus!")

        gmails, apps = get_user_gmails(user.id)
        tier = get_user_tier(user.id)
        config = TIER_CONFIG[tier]
        user_data = get_user_data(user.id)
        personal = user_data.get("gmail_accounts", [])

        text = (
            f"📧 <b>MANAJEMEN GMAIL</b>\n\n"
            f"👤 Tier: <b>{config['name']}</b>\n"
            f"📧 Total Gmail: <b>{len(gmails)}</b> akun\n"
            f"📧 Gmail Pribadi: <b>{len(personal)}</b> akun\n"
        )
        bot.edit_message_text(text, chat_id=chat_id, message_id=call.message.message_id,
                             parse_mode="HTML", reply_markup=gmail_menu_keyboard(user.id))
        return

    # ═══ PRICING MENU ═══
    if data_cb == "menu_pricing":
        text = (
            "🔴 <b>𝗗𝗔𝗙𝗧𝗔𝗥 𝗛𝗔𝗥𝗚𝗔 𝗣𝗥𝗘𝗠𝗜𝗨𝗠 — 𝗙𝗶𝘅𝗠𝗲𝗿𝗮𝗵 × 𝗭𝘆𝗹𝗶𝘅</b>\n\n"
            "👥 Community: @FixMerahCommunity | 📢 Official: @FixMerahOfficial\n"
            "Harga sudah termasuk fee QRIS Pakasir:\n\n"
            "<b>🆓 FREE</b>\n"
            "  • Limit: 3/hari\n"
            "  • Gmail: Add sendiri (max 2)\n"
            "  • WARP: ❌\n"
            "  • Auto-Reply: ❌\n"
            "  • Harga: <b>GRATIS</b>\n\n"
        )
        
        for tier_key in ["premium_basic", "premium_pro", "premium_permanent"]:
            price = TIER_CONFIG[tier_key]["price"]
            fee = calculate_qris_fee(price)
            total = price + fee
            name = TIER_CONFIG[tier_key]["name"]
            duration = TIER_CONFIG[tier_key]["duration_days"]
            duration_text = "Lifetime" if duration >= 99999 else f"{duration} hari"
            
            text += (
                f"<b>{name}</b>\n"
                f"  • Harga: <b>Rp {price:,}</b> + Fee QRIS: <b>Rp {fee:,}</b>\n"
                f"  • <b>Total Bayar: Rp {total:,}</b>\n"
                f"  • Durasi: <b>{duration_text}</b>\n\n"
            )
        
        text += (
            "✅ Pembayaran via <b>QRIS Pakasir</b>\n"
            "✅ Langsung aktif setelah pembayaran\n\n"
            "Pilih paket di bawah:"
        )
        
        bot.edit_message_text(text, chat_id=chat_id, message_id=call.message.message_id,
                             parse_mode="HTML", reply_markup=pricing_keyboard())
        bot.answer_callback_query(call.id, "💰 Harga")
        return

    # ═══ PAYMENT - CREATE QRIS ═══
    if data_cb.startswith("pay_"):
        if not PAKASIR_PROJECT or not PAKASIR_API_KEY:
            bot.answer_callback_query(call.id, "❌ Payment config belum diatur!")
            return
        
        tier = data_cb.replace("pay_", "")
        if tier not in TIER_CONFIG:
            bot.answer_callback_query(call.id, "❌ Tier invalid!")
            return
        
        base_price, fee, total = get_payment_amount(tier)
        order_id = generate_order_id(user.id, tier)
        
        # Create transaction
        payment_data, err = create_pakasir_transaction(order_id, total)
        if err:
            bot.answer_callback_query(call.id, f"❌ Gagal: {err[:100]}")
            return
        
        if not payment_data:
            bot.answer_callback_query(call.id, "❌ Gagal membuat transaksi!")
            return
        
        # Save transaction
        transactions_db[order_id] = {
            "user_id": str(user.id),
            "tier": tier,
            "base_price": base_price,
            "fee": fee,
            "total": total,
            "status": "pending",
            "order_id": order_id,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "expired_at": payment_data.get("expired_at", ""),
        }
        save_transactions(transactions_db)
        
        # Generate QR image
        qr_string = payment_data.get("payment_number", "")
        if not qr_string:
            bot.answer_callback_query(call.id, "❌ QR string tidak ditemukan!")
            return
        
        qr_buf, qr_err = generate_qr_image(qr_string)
        if qr_err or not qr_buf:
            # Fallback: send as string with Pakasir link
            pay_url = f"{PAKASIR_PAY_URL}/{PAKASIR_PROJECT}/{total}?order_id={order_id}&qris_only=1"
            text = (
                f"🔴 <b>𝗣𝗘𝗠𝗕𝗔𝗬𝗔𝗥𝗔𝗡 𝗤𝗥𝗜𝗦 — 𝗙𝗶𝘅𝗠𝗲𝗿𝗮𝗵 × 𝗭𝘆𝗹𝗶𝘅</b>\n\n"
                f"💎 Tier: <b>{TIER_CONFIG[tier]['name']}</b>\n"
                f"💰 Harga: <b>Rp {base_price:,}</b>\n"
                f"📋 Fee QRIS: <b>Rp {fee:,}</b>\n"
                f"💵 <b>Total Bayar: Rp {total:,}</b>\n"
                f"⏰ Expired: <b>{payment_data.get('expired_at', '15 menit')}</b>\n\n"
                f"⚠️ QR Image gagal generate.\n"
                f"👉 <a href='{pay_url}'>𝗞𝗟𝗜𝗞 𝗗𝗜𝗦𝗜𝗡𝗜 𝗨𝗡𝗧𝗨𝗞 𝗕𝗔𝗬𝗔𝗥</a>\n\n"
                f"🆔 Order ID: <code>{order_id}</code>\n"
                f"👥 Community: @FixMerahCommunity | 📢 Official: @FixMerahOfficial"
            )
            bot.edit_message_text(text, chat_id=chat_id, message_id=call.message.message_id,
                                 parse_mode="HTML", reply_markup=payment_status_keyboard(order_id, tier))
            bot.answer_callback_query(call.id, "💳 Link pembayaran dibuat")
        else:
            # Send QR image
            pay_url = f"{PAKASIR_PAY_URL}/{PAKASIR_PROJECT}/{total}?order_id={order_id}&qris_only=1"
            text = (
                f"🔴 <b>𝗦𝗖𝗔𝗡 𝗤𝗥𝗜𝗦 𝗨𝗡𝗧𝗨𝗞 𝗕𝗔𝗬𝗔𝗥 — 𝗙𝗶𝘅𝗠𝗲𝗿𝗮𝗵 × 𝗭𝘆𝗹𝗶𝘅</b>\n\n"
                f"💎 Tier: <b>{TIER_CONFIG[tier]['name']}</b>\n"
                f"💰 Harga: <b>Rp {base_price:,}</b>\n"
                f"📋 Fee QRIS: <b>Rp {fee:,}</b>\n"
                f"💵 <b>Total Bayar: Rp {total:,}</b>\n"
                f"⏰ Expired: <b>{payment_data.get('expired_at', '15 menit')}</b>\n\n"
                f"📱 Scan QR di atas pakai e-wallet (OVO, GoPay, DANA, ShopeePay, dll).\n\n"
                f"🆔 Order ID: <code>{order_id}</code>\n"
                f"👥 Community: @FixMerahCommunity\n"
                f"📢 Official: @FixMerahOfficial\n\n"
                f"<i>✅ Setelah bayar, sistem otomatis cek & aktifkan tier.</i>"
            )
            
            try:
                # Delete old message, send new with photo
                bot.delete_message(chat_id, call.message.message_id)
                sent_msg = bot.send_photo(
                    chat_id,
                    qr_buf,
                    caption=text,
                    parse_mode="HTML",
                    reply_markup=payment_status_keyboard(order_id, tier)
                )
                msg_id = sent_msg.message_id
            except Exception as e:
                print(f"[PAYMENT] Send photo error: {e}")
                # Fallback to edit
                bot.edit_message_text(text, chat_id=chat_id, message_id=call.message.message_id,
                                     parse_mode="HTML", reply_markup=payment_status_keyboard(order_id, tier))
                msg_id = call.message.message_id
            
            bot.answer_callback_query(call.id, "💳 QRIS dibuat! Scan untuk bayar.")
            
            # Start polling thread
            poll_t = threading.Thread(
                target=payment_polling_worker,
                args=(chat_id, user.id, order_id, tier, total, msg_id),
                daemon=True
            )
            poll_t.start()
            payment_threads[order_id] = poll_t
        
        return

    # ═══ CHECK PAYMENT STATUS ═══
    if data_cb.startswith("cekpay_"):
        parts = data_cb.split("_")
        if len(parts) >= 3:
            order_id = parts[1]
            tier = "_".join(parts[2:])
        else:
            bot.answer_callback_query(call.id, "❌ Format invalid")
            return
        
        txn_data = transactions_db.get(order_id)
        if not txn_data:
            bot.answer_callback_query(call.id, "❌ Transaksi tidak ditemukan!")
            return
        
        amount = txn_data.get("total", 0)
        txn, err = check_pakasir_transaction(order_id, amount)
        if err:
            bot.answer_callback_query(call.id, f"⚠️ {err[:100]}")
            return
        
        status = txn.get("status", "unknown")
        
        if status == "completed":
            # Activate if not yet
            if get_user_tier(user.id) != tier or not is_premium_active(user.id):
                duration = TIER_CONFIG[tier]["duration_days"]
                set_user_tier(user.id, tier, duration if duration < 99999 else None)
                reward_referrer_on_upgrade(user.id, tier)
            
            transactions_db[order_id]["status"] = "completed"
            save_transactions(transactions_db)
            
            bot.answer_callback_query(call.id, "✅ Pembayaran berhasil!")
            try:
                bot.edit_message_text(
                    f"🔴 <b>𝗣𝗘𝗠𝗕𝗔𝗬𝗔𝗥𝗔𝗡 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 — 𝗙𝗶𝘅𝗠𝗲𝗿𝗮𝗵 × 𝗭𝘆𝗹𝗶𝘅</b>\n\n"
                    f"💎 Tier: <b>{TIER_CONFIG[tier]['name']}</b>\n"
                    f"💰 Amount: <b>Rp {amount:,}</b>\n\n"
                    f"✅ Selamat! Akun Anda sudah upgrade!\n"
                    f"👥 Community: @FixMerahCommunity\n"
                    f"📢 Official: @FixMerahOfficial\n\n"
                    f"Klik /start untuk menu utama.",
                    chat_id=chat_id,
                    message_id=call.message.message_id,
                    parse_mode="HTML"
                )
            except:
                pass
        elif status in ["expired", "failed", "cancelled"]:
            bot.answer_callback_query(call.id, f"❌ Status: {status}")
            try:
                bot.edit_message_text(
                    f"❌ <b>PEMBAYARAN {status.upper()}</b>\n\n"
                    f"Order ID: <code>{order_id}</code>\n"
                    f"Silakan coba lagi dengan klik 💎 UPGRADE.",
                    chat_id=chat_id,
                    message_id=call.message.message_id,
                    parse_mode="HTML"
                )
            except:
                pass
        else:
            bot.answer_callback_query(call.id, f"⏳ Status: {status} - Masih menunggu pembayaran")
        return

    # ═══ CANCEL PAYMENT ═══
    if data_cb.startswith("cancelpay_"):
        parts = data_cb.split("_")
        if len(parts) >= 3:
            order_id = parts[1]
            tier = "_".join(parts[2:])
        else:
            bot.answer_callback_query(call.id, "❌ Format invalid")
            return
        
        # Cancel via API (optional, Pakasir supports cancel)
        if PAKASIR_PROJECT and PAKASIR_API_KEY:
            try:
                url = f"{PAKASIR_API_URL}/transactioncancel"
                payload = {
                    "project": PAKASIR_PROJECT,
                    "order_id": order_id,
                    "amount": transactions_db.get(order_id, {}).get("total", 0),
                    "api_key": PAKASIR_API_KEY,
                }
                requests.post(url, json=payload, timeout=10)
            except:
                pass
        
        if order_id in transactions_db:
            transactions_db[order_id]["status"] = "cancelled"
            save_transactions(transactions_db)
        
        bot.answer_callback_query(call.id, "❌ Transaksi dibatalkan")
        try:
            bot.edit_message_text(
                "❌ <b>TRANSAKSI DIBATALKAN</b>\n\n"
                "Silakan pilih menu lain.",
                chat_id=chat_id,
                message_id=call.message.message_id,
                parse_mode="HTML",
                reply_markup=main_menu_keyboard(user)
            )
        except:
            pass
        return

    # ═══ REFERRAL MENU ═══
    if data_cb == "menu_referral":
        user_data = get_user_data(user.id)
        ref_code = get_referral_code(user.id)
        bot_info = bot.get_me()
        bot_username = bot_info.username if bot_info else "bot"
        ref_link = f"https://t.me/{bot_username}?start={ref_code}"
        
        ref_count = user_data.get("referral_count", 0)
        total_success = user_data.get("total_referral_success", 0)
        earnings = user_data.get("referral_earnings", 0)
        
        text = (
            f"🔗 <b>𝗦𝗜𝗦𝗧𝗘𝗠 𝗥𝗘𝗙𝗘𝗥𝗥𝗔𝗟 — 𝗙𝗶𝘅𝗠𝗲𝗿𝗮𝗵 × 𝗭𝘆𝗹𝗶𝘅</b>\n\n"
            f"👤 Kode Referral Anda:\n"
            f"<code>{ref_code}</code>\n\n"
            f"🔗 Link Referral:\n"
            f"<code>{ref_link}</code>\n\n"
            f"📊 Statistik:\n"
            f"  • Total Referral: <b>{ref_count}</b>\n"
            f"  • Berhasil Upgrade: <b>{total_success}</b>\n"
            f"  • Total Komisi: <b>Rp {earnings:,}</b>\n\n"
            f"🎁 <b>Reward:</b>\n"
            f"  • Kamu dapat <b>+5 limit/hari selama 30 hari</b> setiap referral berhasil upgrade!\n"
            f"  • Komisi <b>10%</b> dari setiap pembayaran referral!\n\n"
            f"👥 Community: @FixMerahCommunity\n"
            f"📢 Official: @FixMerahOfficial\n\n"
            f"Bagikan link referral ke temanmu!"
        )
        
        bot.edit_message_text(text, chat_id=chat_id, message_id=call.message.message_id,
                             parse_mode="HTML", reply_markup=referral_keyboard(user.id))
        bot.answer_callback_query(call.id, "🔗 Referral")
        return

    # ═══ BUY (old redirect - now handled by pay_*) ═══
    if data_cb in ["buy_basic", "buy_pro", "buy_permanent"]:
        # Redirect to new payment flow
        tier_map = {
            "buy_basic": "premium_basic",
            "buy_pro": "premium_pro",
            "buy_permanent": "premium_permanent"
        }
        tier = tier_map.get(data_cb)
        if tier:
            # Simulate pay_ callback
            call.data = f"pay_{tier}"
            handle_callback(call)
        return

    # ═══ CEK BALASAN ═══
    if data_cb == "menu_replies":
        replies = load_replies()
        if not replies:
            text = (
                "📭 <b>BELUM ADA BALASAN</b>\n\n"
                "Bot akan otomatis cek inbox setiap 5 menit.\n"
                "Jika WhatsApp Support balas, kamu akan dapat notifikasi."
            )
        else:
            text = f"📩 <b>BALASAN TERBARU ({len(replies)})</b>\n\n"
            for i, (key, reply) in enumerate(list(replies.items())[-5:], 1):
                text += (
                    f"<b>{i}. {reply['subject'][:40]}</b>\n"
                    f"📧 Gmail: <code>{key.split('_')[0]}</code>\n"
                    f"📨 Dari: <code>{reply['from'][:30]}</code>\n"
                    f"🕐 {reply['time']}\n"
                    f"<pre>{reply['body'][:150]}</pre>\n\n"
                )

        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔄 REFRESH", callback_data="menu_replies"))
        kb.add(types.InlineKeyboardButton("🔙 KEMBALI", callback_data="menu_main"))
        bot.edit_message_text(text, chat_id=chat_id, message_id=call.message.message_id,
                             parse_mode="HTML", reply_markup=kb)
        bot.answer_callback_query(call.id, "📩 Cek balasan")
        return

    # ═══ WARP STATUS ═══
    if data_cb == "warp_status":
        tier = get_user_tier(user.id)
        config = TIER_CONFIG[tier]

        if not config["warp"]:
            text = (
                "❌ <b>WARP TIDAK TERSEDIA</b>\n\n"
                "Upgrade ke Premium untuk akses WARP!\n"
                "Klik 💎 UPGRADE di menu utama."
            )
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("💎 UPGRADE", callback_data="menu_pricing"))
            kb.add(types.InlineKeyboardButton("🔙 KEMBALI", callback_data="menu_main"))
            bot.edit_message_text(text, chat_id=chat_id, message_id=call.message.message_id,
                                 parse_mode="HTML", reply_markup=kb)
            bot.answer_callback_query(call.id, "❌ WARP locked")
            return

        warp_ok = check_warp_status()
        current_ip = get_public_ip()

        text = (
            f"🌐 <b>WARP STATUS</b>\n\n"
            f"🌐 WARP Enabled: <b>{'YA' if WARP_ENABLED else 'TIDAK'}</b>\n"
            f"📡 Proxy: <code>{WARP_PROXY_HOST}:{WARP_PROXY_PORT}</code>\n"
            f"🔌 Proxy Connection: <b>{'CONNECTED ✓' if warp_ok else 'DISCONNECTED ✗'}</b>\n"
            f"🌍 Current IP: <code>{current_ip}</code>"
        )

        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton("🔄 ROTATE IP", callback_data="warp_rotate"),
            types.InlineKeyboardButton("🔙 KEMBALI", callback_data="menu_main")
        )
        bot.edit_message_text(text, chat_id=chat_id, message_id=call.message.message_id,
                             parse_mode="HTML", reply_markup=kb)
        bot.answer_callback_query(call.id, "🌐 WARP Status")
        return

    # ═══ WARP ROTATE IP ═══
    if data_cb == "warp_rotate":
        tier = get_user_tier(user.id)
        if not TIER_CONFIG[tier]["warp"]:
            bot.answer_callback_query(call.id, "❌ WARP tidak tersedia!")
            return

        if not WARP_ENABLED:
            bot.answer_callback_query(call.id, "🌐 WARP tidak aktif!")
            return

        bot.answer_callback_query(call.id, "🔄 Rotating IP...")

        old_ip = get_public_ip()
        new_ip, err = rotate_warp_ip()

        if new_ip:
            text = (
                f"✅ <b>IP BERHASIL DIROTATE!</b>\n\n"
                f"🌍 IP Lama: <code>{old_ip}</code>\n"
                f"🌍 IP Baru: <code>{new_ip}</code>"
            )
        else:
            text = (
                f"❌ <b>GAGAL ROTATE IP</b>\n\n"
                f"⚠️ Error: {err or 'Unknown'}\n"
                f"🌍 IP Saat Ini: <code>{old_ip}</code>"
            )

        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton("🔄 ROTATE LAGI", callback_data="warp_rotate"),
            types.InlineKeyboardButton("🔙 KEMBALI", callback_data="menu_main")
        )
        bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=kb)
        return

    # ═══ HELP ═══
    if data_cb == "menu_help":
        tier = get_user_tier(user.id)
        config = TIER_CONFIG[tier]

        text = (
            "🔴 <b>𝗙𝗶𝘅𝗠𝗲𝗿𝗮𝗵 𝗕𝗼𝘁 × 𝗭𝘆𝗹𝗶𝘅 — 𝗕𝗔𝗡𝗧𝗨𝗔𝗡</b>\n\n"
            "👥 Community: @FixMerahCommunity\n"
            "📢 Official: @FixMerahOfficial\n"
            "👤 Owner: @anzajun\n\n"
            "<b>1. Kirim Banding:</b>\n"
            "   • Klik 🚀 KIRIM BANDING\n"
            "   • Pilih Gmail (mailv1, mailv2, dst)\n"
            "   • Pilih Support target\n"
            "   • Kirim nomor WhatsApp\n"
            "   • Konfirmasi pengiriman\n\n"
            "<b>2. Format Nomor:</b>\n"
            "   • 08123456789\n"
            "   • +628123456789\n"
            "   • Bisa banyak (pisah enter)\n\n"
        )

        if config["auto_reply"]:
            text += (
                "<b>3. Auto-Reply:</b>\n"
                "   • Bot cek inbox otomatis setiap 5 menit\n"
                "   • Notifikasi jika WhatsApp Support balas\n\n"
            )

        if config["warp"]:
            text += (
                "<b>4. WARP Proxy:</b>\n"
                "   • IP berubah setiap kirim email\n"
                "   • Menghindari rate limit & deteksi\n\n"
            )

        text += (
            "<b>5. Limit Harian:</b>\n"
            f"   • Tier Anda: {config['name']}\n"
            f"   • Limit: {config['daily_limit']}/hari\n"
            "   • Reset setiap jam 00:00 WIB\n\n"
            "<b>6. Gmail:</b>\n"
        )

        if config["use_own_gmail"]:
            text += "   • Anda harus add Gmail sendiri\n"
        else:
            text += "   • Gmail owner tersedia otomatis\n"
            text += "   • Bisa tambah Gmail pribadi\n"

        text += (
            "\n<b>7. Upgrade & Referral:</b>\n"
            "   • Klik 💎 UPGRADE untuk beli Premium\n"
            "   • Bayar via QRIS Pakasir (otomatis)\n"
            "   • Klik 🔗 REFERRAL untuk link referral\n"
            "   • Dapat bonus +5 limit/hari per referral upgrade!\n"
        )

        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔙 KEMBALI", callback_data="menu_main"))
        bot.edit_message_text(text, chat_id=chat_id, message_id=call.message.message_id,
                             parse_mode="HTML", reply_markup=kb)
        bot.answer_callback_query(call.id, "❓ Bantuan")
        return

    # ═══ OWNER: SETTINGS ═══
    if data_cb == "menu_settings":
        if not is_owner(user):
            bot.answer_callback_query(call.id, "❌ Hanya owner!")
            return
        text = (
            f"⚙️ <b>PENGATURAN OWNER</b>\n\n"
            f"⏱️ Delay: <b>{MIN_DELAY}-{MAX_DELAY}</b> detik\n"
            f"⏸️ Status: <b>{'ISTIRAHAT' if paused else 'AKTIF'}</b>\n"
            f"📧 Gmail Owner: <b>{len(OWNER_EMAILS)}</b>\n"
            f"👥 Total Users: <b>{len(users_db)}</b>\n"
            f"🏢 Grup: <b>{len(approved_groups)}</b>\n"
            f"🌐 WARP: <b>{'AKTIF' if WARP_ENABLED else 'NONAKTIF'}</b>\n"
            f"📩 Auto-Reply: <b>{'AKTIF' if AUTO_REPLY_ENABLED else 'NONAKTIF'}</b>"
        )
        bot.edit_message_text(text, chat_id=chat_id, message_id=call.message.message_id,
                             parse_mode="HTML", reply_markup=settings_keyboard())
        bot.answer_callback_query(call.id, "⚙️ Pengaturan")
        return

    # ═══ OWNER: BREAK ═══
    if data_cb == "cmd_break":
        if not is_owner(user):
            bot.answer_callback_query(call.id, "❌ Hanya owner!")
            return
        paused = True
        save_data(data)
        bot.answer_callback_query(call.id, "⏸️ Bot dihentikan!")
        bot.send_message(chat_id, "⏸️ <b>BOT MASUK MODE ISTIRAHAT</b>", parse_mode="HTML")
        return

    # ═══ OWNER: GAS ═══
    if data_cb == "cmd_gas":
        if not is_owner(user):
            bot.answer_callback_query(call.id, "❌ Hanya owner!")
            return
        paused = False
        save_data(data)
        bot.answer_callback_query(call.id, "🟢 Bot aktif!")
        bot.send_message(chat_id, "🟢 <b>BOT KEMBALI AKTIF</b>", parse_mode="HTML")
        return

    # ═══ OWNER: ADD GROUP ═══
    if data_cb == "cmd_addgroup":
        if not is_owner(user):
            bot.answer_callback_query(call.id, "❌ Hanya owner!")
            return
        if call.message.chat.type in ["group", "supergroup"]:
            approved_groups.add(chat_id)
            save_data(data)
            bot.answer_callback_query(call.id, "✅ Grup ditambahkan!")
            bot.send_message(chat_id, f"✅ <b>Grup terdaftar!</b>\nID: <code>{chat_id}</code>", parse_mode="HTML")
        else:
            bot.answer_callback_query(call.id, "⚠️ Jalankan di grup!")
        return

    # ═══ OWNER: USERS MENU ═══
    if data_cb == "cmd_users":
        if not is_owner(user):
            bot.answer_callback_query(call.id, "❌ Hanya owner!")
            return
        text = (
            "👑 <b>MANAJEMEN USER</b>\n\n"
            "Perintah owner:\n"
            "<code>/settier @username tier</code>\n"
            "<code>/settier 123456 premium_basic</code>\n\n"
            "Tiers: free, premium_basic, premium_pro, premium_permanent, owner"
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("📋 LIST USERS", callback_data="list_users"))
        kb.add(types.InlineKeyboardButton("🔙 KEMBALI", callback_data="menu_main"))
        bot.edit_message_text(text, chat_id=chat_id, message_id=call.message.message_id,
                             parse_mode="HTML", reply_markup=kb)
        bot.answer_callback_query(call.id, "👑 Users")
        return

    # ═══ OWNER: LIST USERS ═══
    if data_cb == "list_users":
        if not is_owner(user):
            bot.answer_callback_query(call.id, "❌ Hanya owner!")
            return
        if not users_db:
            text = "📭 <b>Belum ada user terdaftar</b>"
        else:
            text = "👥 <b>DAFTAR USER:</b>\n\n"
            for uid, udata in list(users_db.items())[:20]:
                tier = udata.get("tier", "free")
                name = TIER_CONFIG.get(tier, {}).get("name", tier)
                ref_count = udata.get("referral_count", 0)
                text += f"• <code>{uid}</code> - {name} (Ref: {ref_count})\n"
            if len(users_db) > 20:
                text += f"\n... dan {len(users_db)-20} lainnya"

        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔙 KEMBALI", callback_data="menu_settings"))
        bot.edit_message_text(text, chat_id=chat_id, message_id=call.message.message_id,
                             parse_mode="HTML", reply_markup=kb)
        bot.answer_callback_query(call.id, "👥 List users")
        return

    # ═══ OWNER: SET DELAY ═══
    if data_cb == "set_delay":
        if not is_owner(user):
            bot.answer_callback_query(call.id, "❌ Hanya owner!")
            return
        user_state[chat_id] = {"state": "SET_DELAY"}
        text = (
            "⏱️ <b>SET DELAY</b>\n\n"
            "Kirim format:\n"
            "<code>min max</code>\n"
            "Contoh: <code>30 120</code>"
        )
        bot.edit_message_text(text, chat_id=chat_id, message_id=call.message.message_id, parse_mode="HTML")
        bot.answer_callback_query(call.id, "⏱️ Set delay")
        return

    # ═══ OWNER: LIST GROUP ═══
    if data_cb == "list_group":
        if not is_owner(user):
            bot.answer_callback_query(call.id, "❌ Hanya owner!")
            return
        if not approved_groups:
            text = "📭 <b>Belum ada grup terdaftar</b>"
        else:
            text = "🏢 <b>GRUP TERDAFTAR:</b>\n\n"
            for gid in approved_groups:
                text += f"• <code>{gid}</code>\n"
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔙 KEMBALI", callback_data="menu_settings"))
        bot.edit_message_text(text, chat_id=chat_id, message_id=call.message.message_id,
                             parse_mode="HTML", reply_markup=kb)
        bot.answer_callback_query(call.id, "🏢 List grup")
        return

    # ═══ OWNER: BROADCAST ═══
    if data_cb == "broadcast":
        if not is_owner(user):
            bot.answer_callback_query(call.id, "❌ Hanya owner!")
            return
        user_state[chat_id] = {"state": "BROADCAST"}
        text = (
            "📢 <b>BROADCAST</b>\n\n"
            "Kirim pesan yang akan dibroadcast\n"
            "ke semua grup."
        )
        bot.edit_message_text(text, chat_id=chat_id, message_id=call.message.message_id, parse_mode="HTML")
        bot.answer_callback_query(call.id, "📢 Broadcast")
        return


# ═══════════════════ MESSAGE HANDLER ═══════════════════
@bot.message_handler(func=lambda msg: True, content_types=["text"])
def handle_message(message):
    user = message.from_user
    chat_id = message.chat.id
    text = message.text.strip()
    global MIN_DELAY, MAX_DELAY

    # Auto-register new users
    get_user_data(user.id)

    # Permission check
    if message.chat.type == "private" and not is_owner(user):
        if not is_premium_active(user.id):
            tier = get_user_tier(user.id)
            if tier.startswith("premium"):
                set_user_tier(user.id, "free")
                kb = types.InlineKeyboardMarkup()
                kb.add(types.InlineKeyboardButton("💎 UPGRADE PREMIUM", callback_data="menu_pricing"))
                bot.reply_to(message,
                    "⏰ <b>PREMIUM ANDA HABIS!</b>\n\n"
                    "Tier downgrade ke FREE.\n"
                    "Silakan upgrade untuk fitur lengkap.",
                    parse_mode="HTML", reply_markup=kb)
                return

    if message.chat.type in ["group", "supergroup"] and chat_id not in approved_groups:
        return

    state = user_state.get(chat_id)

    # ═══ INPUT NUMBERS ═══
    if state and state.get("state") == "INPUT_NUMBERS":
        numbers = parse_numbers(text)
        if not numbers:
            bot.reply_to(message,
                "❌ <b>Tidak ditemukan nomor valid!</b>",
                parse_mode="HTML")
            return

        remaining = get_daily_remaining(user.id)
        total_needed = len(numbers) * len(state["support_indices"])
        if total_needed > remaining:
            bot.reply_to(message,
                f"❌ <b>LIMIT TIDAK CUKUP!</b>\n\n"
                f"Butuh: <b>{total_needed}</b>\n"
                f"Sisa: <b>{remaining}</b>\n"
                f"Kurangi nomor atau upgrade tier.",
                parse_mode="HTML")
            return

        state["numbers"] = numbers
        state["state"] = "CONFIRM"

        preview = "\n".join([f"• <code>{n}</code>" for n in numbers[:5]])
        if len(numbers) > 5:
            preview += f"\n... dan {len(numbers)-5} lainnya"

        confirm_text = (
            f"📋 <b>KONFIRMASI PENGIRIMAN</b>\n\n"
            f"📧 Gmail: <code>{state['email_label']}</code>\n"
            f"📨 Target: <b>{len(state['support_indices'])}</b> support\n"
            f"📱 Nomor: <b>{len(numbers)}</b>\n"
            f"📊 Total: <b>{total_needed}</b> email\n"
            f"📊 Limit tersisa: <b>{remaining - total_needed}</b>\n"
            f"⏱️ Estimasi: <b>{(total_needed * MIN_DELAY)//60}-{(total_needed * MAX_DELAY)//60}</b> menit\n\n"
            f"📱 Nomor:\n{preview}\n\n"
            f"<b>Kirim sekarang?</b>"
        )

        msg = bot.send_message(chat_id, confirm_text, parse_mode="HTML", reply_markup=confirm_keyboard())
        state["msg_id"] = msg.message_id
        return

    # ═══ ADD GMAIL ═══
    if state and state.get("state") == "ADD_GMAIL":
        try:
            parts = text.split("|")
            if len(parts) != 2:
                raise ValueError()
            email = parts[0].strip()
            app_pass = parts[1].strip()

            ok, err = add_user_gmail(user.id, email, app_pass)
            if ok:
                bot.reply_to(message,
                    f"✅ <b>GMAIL DITAMBAHKAN!</b>\n"
                    f"📧 <code>{email[:3]}***{email[email.find('@'):]}</code>",
                    parse_mode="HTML")
            else:
                bot.reply_to(message, f"❌ <b>GAGAL:</b> {err}", parse_mode="HTML")
        except:
            bot.reply_to(message,
                "❌ <b>Format salah!</b>\n"
                "Gunakan: <code>email@gmail.com|app_password</code>",
                parse_mode="HTML")
        finally:
            if chat_id in user_state:
                del user_state[chat_id]
        return

    # ═══ SET DELAY (OWNER) ═══
    if state and state.get("state") == "SET_DELAY":
        if not is_owner(user):
            return
        try:
            parts = text.split()
            mn = int(parts[0])
            mx = int(parts[1])
            if mn <= 0 or mx <= 0 or mn > mx:
                raise ValueError()
            MIN_DELAY = mn
            MAX_DELAY = mx
            save_data(data)
            bot.reply_to(message,
                f"✅ <b>DELAY DIUBAH</b>\n"
                f"Min: <b>{mn}</b> detik\n"
                f"Max: <b>{mx}</b> detik",
                parse_mode="HTML")
        except:
            bot.reply_to(message,
                "❌ <b>Format salah!</b>\n"
                "Gunakan: <code>min max</code>",
                parse_mode="HTML")
        finally:
            if chat_id in user_state:
                del user_state[chat_id]
        return

    # ═══ BROADCAST (OWNER) ═══
    if state and state.get("state") == "BROADCAST":
        if not is_owner(user):
            return
        targets = list(approved_groups)
        sent = 0
        for t in targets:
            try:
                bot.send_message(t, f"🔴 <b>𝗙𝗶𝘅𝗠𝗲𝗿𝗮𝗵 𝗕𝗼𝘁 × 𝗭𝘆𝗹𝗶𝘅 — 𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧</b>\n\n{text}", parse_mode="HTML")
                sent += 1
            except:
                pass
        bot.reply_to(message,
            f"📢 <b>BROADCAST SELESAI</b>\n"
            f"Terkirim ke <b>{sent}</b> grup",
            parse_mode="HTML")
        if chat_id in user_state:
            del user_state[chat_id]
        return

    # ═══ OWNER COMMANDS via TEXT ═══
    if is_owner(user) and text.startswith("/"):
        # /settier @username tier
        if text.startswith("/settier"):
            parts = text.split(maxsplit=2)
            if len(parts) < 3:
                bot.reply_to(message, "⚠️ Format: /settier @username tier")
                return
            who = parts[1].strip()
            tier = parts[2].strip()

            target_id = None
            for uid, udata in users_db.items():
                if udata.get("username", "").lower() == who.lstrip("@").lower():
                    target_id = uid
                    break

            if not target_id and who.isdigit():
                target_id = who

            if not target_id:
                bot.reply_to(message, "⚠️ User tidak ditemukan!")
                return

            if tier not in TIER_CONFIG:
                bot.reply_to(message, f"⚠️ Tier invalid! Pilih: {', '.join(TIER_CONFIG.keys())}")
                return

            duration = TIER_CONFIG[tier]["duration_days"]
            set_user_tier(target_id, tier, duration if duration < 99999 else None)

            bot.reply_to(message,
                f"✅ <b>TIER DIUBAH!</b>\n"
                f"User: <code>{target_id}</code>\n"
                f"Tier: <b>{TIER_CONFIG[tier]['name']}</b>",
                parse_mode="HTML")
            return

        # /deluser @username
        if text.startswith("/deluser"):
            parts = text.split(maxsplit=1)
            if len(parts) < 2:
                bot.reply_to(message, "⚠️ Format: /deluser @username")
                return
            who = parts[1].strip()

            for uid in list(users_db.keys()):
                if users_db[uid].get("username", "").lower() == who.lstrip("@").lower():
                    del users_db[uid]
                    save_users(users_db)
                    bot.reply_to(message, f"✅ <b>User {who} dihapus!</b>", parse_mode="HTML")
                    return

            bot.reply_to(message, "⚠️ User tidak ditemukan!")
            return

# ═══════════════════ NEW CHAT MEMBER ═══════════════════
@bot.message_handler(content_types=["new_chat_members"])
def handle_new_member(message):
    for member in message.new_chat_members:
        try:
            me = bot.get_me()
            if me and member.id == me.id:
                approved_groups.add(message.chat.id)
                save_data(data)
                bot.send_message(
                    message.chat.id,
                    f"🔴 <b>𝗙𝗶𝘅𝗠𝗲𝗿𝗮𝗵 𝗕𝗼𝘁 × 𝗭𝘆𝗹𝗶𝘅 𝗔𝗞𝗧𝗜𝗙!</b>\n"
                    f"Grup ID: <code>{message.chat.id}</code>\n"
                    f"Klik /start untuk menu.",
                    parse_mode="HTML"
                )
        except:
            pass

# ═══════════════════ RUN ═══════════════════
if __name__ == "__main__":
    print("╚═══════════════════════════════════════╝")
    print("║  🔴 𝗙𝗶𝘅𝗠𝗲𝗿𝗮𝗵 𝗕𝗼𝘁 × 𝗭𝘆𝗹𝗶𝘅 🚀  𝘃𝟰.𝟭  ║")
    print("  Developer: 安扎君 · 𝕬𝖓𝖟𝖆𝖏𝖚𝖓 𝕬𝖕𝖔𝖈𝖆𝖑𝖞𝖕𝖘𝖊 أنزاجون 🕊️⚔️")
    print("╚═══════════════════════════════════════╝")
    print(f"  Owner: {OWNER}")
    print(f"  Gmail Owner: {len(OWNER_EMAILS)} accounts")
    print(f"  Support: {len(SUPPORT_EMAILS)} emails")
    print(f"  Templates: {len(APPEALS)} appeals")
    print(f"  Names: {len(NAMES)} scenarios")
    print(f"  WARP: {'ENABLED' if WARP_ENABLED else 'DISABLED'}")
    print(f"  Auto-Reply: {'ENABLED' if AUTO_REPLY_ENABLED else 'DISABLED'}")
    print(f"  Pakasir Project: {PAKASIR_PROJECT or 'NOT SET'}")
    print(f"  QRIS Fee Ready: {'YES' if QR_AVAILABLE else 'NO (install qrcode[pil])'}")
    print("╚═══════════════════════════════════════╝")

    if AUTO_REPLY_ENABLED and OWNER_EMAILS:
        print("[AUTO-REPLY] Starting detection thread...")
        t = threading.Thread(target=auto_reply_worker, daemon=True)
        t.start()

    try:
        bot.polling(non_stop=True, interval=0, timeout=20)
    except KeyboardInterrupt:
        print("\n🛑 Bot dihentikan.")
        save_data(data)
        save_users(users_db)
        save_transactions(transactions_db)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        save_data(data)
        save_users(users_db)
        save_transactions(transactions_db)
