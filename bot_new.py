import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, InlineQueryHandler, ContextTypes
from telegram.constants import ParseMode
import random
from datetime import datetime, timedelta
import asyncio
import warnings
import json
import os

# Suppress warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Token
BOT_TOKEN = "8441476926:AAGWc1_v-BDSxx3yKUw0Dh6vbft5sVhLP9I"

# Required Channels (with actual IDs)
REQUIRED_CHANNELS = {
    "@DevJisanX": -1001473422979,
    "@treaderjisanx": -1002028492840,
    "@SingleBotMaker": -1002503354809
}

# Currency Pairs
OTC_PAIRS = [
    "NZD/CHF (OTC)", "USD/BRL (OTC)", "EUR/GBP (OTC)", "GBP/AUD (OTC)",
    "GBP/JPY (OTC)", "GBP/USD (OTC)", "USD/JPY (OTC)", "USD/ZAR (OTC)",
    "EUR/AUD (OTC)", "EUR/CAD (OTC)", "EUR/JPY (OTC)", "EUR/USD (OTC)",
    "GBP/CAD (OTC)", "GBP/CHF (OTC)", "USD/CAD (OTC)", "USD/CHF (OTC)",
    "AUD/NZD (OTC)", "CAD/CHF (OTC)", "CHF/JPY (OTC)", "EUR/SGD (OTC)",
    "USD/MXN (OTC)", "USD/COP (OTC)", "NZD/CAD (OTC)", "USD/ARS (OTC)",
    "EUR/CHF (OTC)", "USD/IDR (OTC)", "USD/NGN (OTC)", "AUD/CAD (OTC)",
    "AUD/JPY (OTC)", "AUD/USD (OTC)", "USD/BDT (OTC)", "USD/PHP (OTC)",
    "USD/PKR (OTC)", "USD/TRY (OTC)"
]

REAL_PAIRS = [
    "NZD/CHF", "USD/BRL", "EUR/GBP", "GBP/AUD",
    "GBP/JPY", "GBP/USD", "USD/JPY", "USD/ZAR",
    "EUR/AUD", "EUR/CAD", "EUR/JPY", "EUR/USD",
    "GBP/CAD", "GBP/CHF", "USD/CAD", "USD/CHF",
    "AUD/NZD", "CAD/CHF", "CHF/JPY", "EUR/SGD",
    "USD/MXN", "USD/COP", "NZD/CAD", "USD/ARS",
    "EUR/CHF", "USD/IDR", "USD/NGN", "AUD/CAD",
    "AUD/JPY", "AUD/USD", "USD/BDT", "USD/PHP",
    "USD/PKR", "USD/TRY"
]

TIMEFRAMES = ["01:00", "02:00", "05:00"]

# User data storage (temporary session data)
user_data = {}

# Database file for persistent user data
DB_FILE = "user_database.json"

# Load user database
def load_user_db():
    """Load user database from JSON file"""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_user_db(db):
    """Save user database to JSON file"""
    with open(DB_FILE, 'w') as f:
        json.dump(db, f, indent=2)

# User database structure:
# {
#   "user_id": {
#     "signal_limit": 10,
#     "signals_used": 0,
#     "referred_by": null or user_id,
#     "referrals": [list of user_ids],
#     "username": "username",
#     "first_name": "name"
#   }
# }

user_db = load_user_db()

def get_user_info(user_id):
    """Get user info from database"""
    user_id_str = str(user_id)
    if user_id_str not in user_db:
        user_db[user_id_str] = {
            "signal_limit": 10,  # Default 10 signals
            "signals_used": 0,
            "referred_by": None,
            "referrals": [],
            "username": "",
            "first_name": "",
            "channels_joined": [],  # Track which channels user joined
            "pending_referrer": None,  # Store referrer until channels joined
            "bot_unlocked": False  # Bot access granted after channel join
        }
        save_user_db(user_db)
    return user_db[user_id_str]

def update_user_info(user_id, **kwargs):
    """Update user info in database"""
    user_id_str = str(user_id)
    user_info = get_user_info(user_id)
    user_info.update(kwargs)
    user_db[user_id_str] = user_info
    save_user_db(user_db)

def add_referral(referrer_id, new_user_id):
    """Add referral and update limits"""
    referrer_id_str = str(referrer_id)
    new_user_id_str = str(new_user_id)
    
    # Get or create referrer info
    referrer_info = get_user_info(referrer_id)
    
    # Add to referrals list
    if new_user_id_str not in referrer_info["referrals"]:
        referrer_info["referrals"].append(new_user_id_str)
        referrer_info["signal_limit"] += 5  # Add 5 signals
        update_user_info(referrer_id, **referrer_info)
    
    # Set new user's referred_by and give 15 signals
    new_user_info = get_user_info(new_user_id)
    new_user_info["referred_by"] = referrer_id_str
    new_user_info["signal_limit"] = 15  # Referred users get 15
    update_user_info(new_user_id, **new_user_info)

async def check_channel_membership(user_id, context):
    """Check if user is member of all required channels"""
    joined_channels = []
    not_joined = []
    
    for channel_username, channel_id in REQUIRED_CHANNELS.items():
        try:
            # Try using channel username first
            member = await context.bot.get_chat_member(channel_username, user_id)
            if member.status in ['member', 'administrator', 'creator']:
                joined_channels.append(channel_username)
            else:
                not_joined.append(channel_username)
        except Exception as e:
            # If username doesn't work, channel might be private or user not joined
            not_joined.append(channel_username)
    
    return joined_channels, not_joined

async def unlock_bot_for_user(user_id, context):
    """Unlock bot access after channel join and process referral"""
    user_info = get_user_info(user_id)
    
    # Mark bot as unlocked
    user_info["bot_unlocked"] = True
    
    # Process pending referral
    if user_info.get("pending_referrer"):
        referrer_id = int(user_info["pending_referrer"])
        add_referral(referrer_id, user_id)
        
        # Send notification to referrer
        try:
            referrer_info = get_user_info(referrer_id)
            await context.bot.send_message(
                chat_id=referrer_id,
                text=f"""
ðŸŽ‰ <b>Great News!</b> ðŸŽ‰

<b>ðŸŽ New Referral Joined!</b>

ðŸ‘¤ <b>{user_info.get('first_name', 'A friend')}</b> just joined using your referral link!

âœ… <b>+5 Free Signals Added!</b>
ðŸ“Š Total Signals: <b>{referrer_info['signal_limit']}</b>
ðŸ”¥ Total Referrals: <b>{len(referrer_info['referrals'])}</b>

<i>Keep sharing to earn unlimited signals! ðŸš€</i>
""",
                parse_mode=ParseMode.HTML
            )
        except:
            pass
        
        user_info["pending_referrer"] = None
    
    update_user_info(user_id, **user_info)

def check_signal_limit(user_id):
    """Check if user has remaining signals"""
    user_info = get_user_info(user_id)
    return user_info["signals_used"] < user_info["signal_limit"]

def use_signal(user_id):
    """Increment signals used counter"""
    user_info = get_user_info(user_id)
    user_info["signals_used"] += 1
    update_user_info(user_id, **user_info)


