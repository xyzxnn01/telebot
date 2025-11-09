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
🎉 <b>Great News!</b> 🎉

<b>🎁 New Referral Joined!</b>

👤 <b>{user_info.get('first_name', 'A friend')}</b> just joined using your referral link!

✅ <b>+5 Free Signals Added!</b>
📊 Total Signals: <b>{referrer_info['signal_limit']}</b>
🔥 Total Referrals: <b>{len(referrer_info['referrals'])}</b>

<i>Keep sharing to earn unlimited signals! 🚀</i>
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command with channel verification"""
    user_id = update.effective_user.id
    user = update.effective_user
    
    # Initialize session data
    user_data[user_id] = {
        'market_type': None,
        'currency_pair': None,
        'timeframe': '01:00'
    }
    
    # Get or create user in database
    user_info = get_user_info(user_id)
    user_info["username"] = user.username or ""
    user_info["first_name"] = user.first_name or ""
    
    # Handle referral if present - store as pending until channel verification
    pending_referrer = None
    if context.args and len(context.args) > 0:
        try:
            referrer_id = int(context.args[0])
            if referrer_id != user_id:
                pending_referrer = referrer_id
                user_info["pending_referrer"] = referrer_id
        except ValueError:
            pass
    
    # Save user info
    update_user_info(user_id, **user_info)
    
    # Check if user already unlocked bot
    if user_info.get("bot_unlocked", False):
        # User already verified, show main menu directly
        user_info = get_user_info(user_id)
        remaining_signals = user_info["signal_limit"] - user_info["signals_used"]
    
    welcome_message = f"""
╔═══════════════════════════════════╗
║  <b>⚡ 𝐐𝐗 𝐒𝐈𝐆𝐍𝐀𝐋 𝐌𝐀𝐊𝐄𝐑 ⚡</b>  ║
╚═══════════════════════════════════╝

<b>� 𝐏𝐫��� 𝐓𝐫𝐚𝐝𝐢𝐧𝐠 𝐒𝐢𝐠𝐧𝐚𝐥𝐬 𝐁𝐨𝐭</b>

✅ <i>𝙻𝚘𝚐𝚒𝚗 𝚂𝚞𝚌𝚌𝚎𝚜𝚜𝚏𝚞𝚕!</i>
🎁 <b>Free Signals: {remaining_signals}/{user_info["signal_limit"]}</b>

<b>━━━━━━━ 🔹 𝐅𝐞𝐚𝐭𝐮𝐫𝐞𝐬 🔹 ━━━━━━━</b>
⚡ 𝑅𝑒𝑎𝑙-𝑡𝑖𝑚𝑒 𝑇𝑟𝑎𝑑𝑖𝑛𝑔 𝑆𝑖𝑔𝑛𝑎𝑙𝑠
🌐 𝑂𝑇𝐶 & 𝑅𝑒𝑎𝑙 𝑀𝑎𝑟𝑘𝑒𝑡 𝑆𝑢𝑝𝑝𝑜𝑟𝑡
⏰ 𝑀𝑢𝑙𝑡𝑖𝑝𝑙𝑒 𝑇𝑖𝑚𝑒𝑓𝑟𝑎𝑚𝑒𝑠
🎯 𝐻𝑖𝑔ℎ 𝐴𝑐𝑐𝑢𝑟𝑎𝑐𝑦 𝑃𝑟𝑒𝑑𝑖𝑐𝑡𝑖𝑜𝑛𝑠

<b>📊 𝐒𝐞𝐥𝐞𝐜𝐭 𝐌𝐚𝐫𝐤𝐞𝐭 𝐓𝐲𝐩𝐞:</b>
"""
    
    keyboard = [
        [
            InlineKeyboardButton("🌙 𝐎𝐓𝐂 𝐌𝐚𝐫𝐤𝐞𝐭", callback_data="market_otc"),
            InlineKeyboardButton("🌞 𝐑𝐞𝐚𝐥 𝐌𝐚𝐫𝐤𝐞𝐭", callback_data="market_real")
        ],
        [
            InlineKeyboardButton("👤 𝐌𝐲 𝐌𝐞𝐧𝐮", callback_data="my_menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_message,
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup
    )


async def market_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle market type selection"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    market_type = query.data.split('_')[1]
    user_data[user_id]['market_type'] = market_type
    
    pairs = OTC_PAIRS if market_type == 'otc' else REAL_PAIRS
    market_name = "𝐎𝐓𝐂 𝐌𝐚𝐫𝐤𝐞𝐭" if market_type == 'otc' else "𝐑𝐞𝐚𝐥 𝐌𝐚𝐫𝐤𝐞𝐭"
    
    message = f"""
╔══════════════════════════════════╗
║    <b>✅ {market_name} 𝐒𝐞𝐥𝐞𝐜𝐭𝐞𝐝</b>    ║
╚══════════════════════════════════╝

<b>💱 𝐒𝐞𝐥𝐞𝐜𝐭 𝐂𝐮𝐫𝐫𝐞𝐧𝐜𝐲 𝐏𝐚𝐢𝐫:</b>
"""
    
    # Create currency pair buttons (2 per row)
    keyboard = []
    row = []
    for i, pair in enumerate(pairs):
        # Add (OTC) suffix for OTC market
        if market_type == 'otc':
            pair_display = f"{pair} (OTC)" if " (OTC)" not in pair else pair
        else:
            pair_display = pair
        row.append(InlineKeyboardButton(pair_display, callback_data=f"pair_{i}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    # Add back button
    keyboard.append([InlineKeyboardButton("🔙 𝐁𝐚𝐜𝐤 𝐭𝐨 𝐌𝐚𝐫𝐤𝐞𝐭", callback_data="back_market")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Check if message has photo (can't edit photo to text)
    if query.message.photo:
        await query.message.delete()
        await query.message.reply_text(
            message,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    else:
        await query.edit_message_text(
            message,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )


async def pair_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle currency pair selection"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Initialize user data if not exists
    if user_id not in user_data:
        user_data[user_id] = {
            'market_type': None,
            'currency_pair': None,
            'timeframe': '00:05'
        }
    
    pair_index = int(query.data.split('_')[1])
    
    market_type = user_data[user_id]['market_type']
    pairs = OTC_PAIRS if market_type == 'otc' else REAL_PAIRS
    selected_pair = pairs[pair_index]
    
    user_data[user_id]['currency_pair'] = selected_pair
    
    message = f"""
╔══════════════════════════════════╗
║  <b>✅ 𝐏𝐚𝐢𝐫 𝐒𝐞𝐥𝐞𝐜𝐭𝐞𝐝 𝐒𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲</b>  ║
╚══════════════════════════════════╝

<b>💱 𝐒𝐞𝐥𝐞𝐜𝐭𝐞𝐝:</b> <code>{selected_pair}</code>

<b>⏱ 𝐒𝐞𝐥𝐞𝐜𝐭 𝐓𝐢𝐦𝐞𝐟𝐫𝐚𝐦𝐞:</b>
<i>(𝘿𝙚𝙛𝙖𝙪𝙡𝙩: 5 𝙈𝙞𝙣𝙪𝙩𝙚𝙨)</i>
"""
    
    # Create timeframe buttons (4 per row)
    keyboard = []
    row = []
    for i, tf in enumerate(TIMEFRAMES):
        tf_label = f"⏰ {tf}" if tf == "00:05" else tf
        row.append(InlineKeyboardButton(tf_label, callback_data=f"time_{i}"))
        if len(row) == 4:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    # Add back button
    keyboard.append([InlineKeyboardButton("🔙 𝐁𝐚𝐜𝐤 𝐭𝐨 𝐏𝐚𝐢𝐫𝐬", callback_data=f"market_{market_type}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Check if message has photo (can't edit photo to text)
    if query.message.photo:
        await query.message.delete()
        await query.message.reply_text(
            message,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    else:
        await query.edit_message_text(
            message,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )


async def generate_signal(user_id: int) -> dict:
    """Generate unique trading signal with technical analysis"""
    user_info = user_data.get(user_id, {})
    
    # Use stored values or defaults
    currency_pair = user_info.get('currency_pair', 'USD/JPY')
    timeframe = user_info.get('timeframe', '00:05')
    
    # Simulate technical analysis
    await asyncio.sleep(1.5)  # Realistic delay
    
    # Generate signal direction (Call/Put)
    direction = random.choice(["CALL", "PUT"])
    
    # Generate confidence level
    confidence = random.randint(75, 98)
    
    # Generate entry price (simulated)
    base_price = random.uniform(1.0000, 1.9999)
    entry_price = round(base_price, 4)
    
    # Generate martingale levels
    martingale = random.randint(1, 3)
    
    # Calculate expiry time
    timeframe_minutes = int(timeframe.split(':')[1])
    expiry_time = datetime.now() + timedelta(minutes=timeframe_minutes)
    
    # Generate indicator values
    rsi = random.randint(30, 70)
    macd = "Bullish" if direction == "CALL" else "Bearish"
    stochastic = random.randint(20, 80)
    
    return {
        'direction': direction,
        'confidence': confidence,
        'entry_price': entry_price,
        'martingale': martingale,
        'expiry_time': expiry_time.strftime("%H:%M:%S"),
        'rsi': rsi,
        'macd': macd,
        'stochastic': stochastic,
        'pair': currency_pair,
        'timeframe': timeframe
    }


async def show_loading_animation(query, user_id):
    """Show unique animated loading with real-time percentage updates"""
    
    loading_stages = [
        {
            'percent': 0,
            'text': '🔄 𝐒𝐢𝐠𝐧𝐚𝐥 𝐆𝐞𝐧𝐞𝐫𝐚𝐭𝐢𝐨𝐧 𝐒𝐭𝐚𝐫𝐭𝐢𝐧𝐠...',
            'bar': '⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜',
            'status': '⚡ 𝙸𝚗𝚒𝚝𝚒𝚊𝚕𝚒𝚣𝚒𝚗𝚐 𝚂𝚢𝚜𝚝𝚎𝚖...'
        },
        {
            'percent': 15,
            'text': '📊 𝐀𝐧𝐚𝐥𝐲𝐳𝐢𝐧𝐠 𝐌𝐚𝐫𝐤𝐞𝐭 𝐃𝐚𝐭𝐚...',
            'bar': '🟩🟩⬜⬜⬜⬜⬜⬜⬜⬜',
            'status': '📈 𝙼𝚊𝚛𝚔𝚎𝚝 𝙳𝚊𝚝𝚊 𝙿𝚛𝚘𝚌𝚎𝚜𝚜𝚒𝚗𝚐...'
        },
        {
            'percent': 30,
            'text': '🔍 𝐏𝐫𝐨𝐜𝐞𝐬𝐬𝐢𝐧𝐠 𝐈𝐧𝐝𝐢𝐜𝐚𝐭𝐨𝐫𝐬...',
            'bar': '🟩🟩🟩🟩⬜⬜⬜⬜⬜⬜',
            'status': '🎯 𝚁𝚂𝙸, 𝙼𝙰𝙲𝙳, 𝚂𝚝𝚘𝚌𝚑𝚊𝚜𝚝𝚒𝚌...'
        },
        {
            'percent': 45,
            'text': '📉 𝐂𝐡𝐞𝐜𝐤𝐢𝐧𝐠 𝐏𝐫𝐢𝐜𝐞 𝐀𝐜𝐭𝐢𝐨𝐧...',
            'bar': '🟩🟩🟩🟩🟩⬜⬜⬜⬜⬜',
            'status': '💹 𝙿𝚛𝚒𝚌𝚎 𝙰𝚌𝚝𝚒𝚘𝚗 𝙰𝚗𝚊𝚕𝚢𝚜𝚒𝚜...'
        },
        {
            'percent': 60,
            'text': '🎲 𝐅𝐢𝐧𝐝𝐢𝐧𝐠 𝐒𝐮𝐩𝐩𝐨𝐫𝐭 & 𝐑𝐞𝐬𝐢𝐬𝐭𝐚𝐧𝐜𝐞...',
            'bar': '🟩🟩🟩🟩🟩🟩🟨🟨⬜⬜',
            'status': '📊 𝙸𝚍𝚎𝚗𝚝𝚒𝚏𝚢𝚒𝚗𝚐 𝚂/𝚁 𝙻𝚎𝚟𝚎𝚕𝚜...'
        },
        {
            'percent': 75,
            'text': '🎯 𝐂𝐚𝐥𝐜𝐮𝐥𝐚𝐭𝐢𝐧𝐠 𝐄𝐧𝐭𝐫𝐲 𝐏𝐨𝐢𝐧𝐭...',
            'bar': '🟩🟩🟩🟩🟩🟩🟩🟨🟨⬜',
            'status': '💰 𝙱𝚎𝚜𝚝 𝙴𝚗𝚝𝚛𝚢 𝙲𝚊𝚕𝚌𝚞𝚕𝚊𝚝𝚒𝚘𝚗...'
        },
        {
            'percent': 90,
            'text': '✅ 𝐕𝐞𝐫𝐢𝐟𝐲𝐢𝐧𝐠 𝐂𝐨𝐧𝐟𝐢𝐝𝐞𝐧𝐜𝐞 𝐋𝐞𝐯𝐞𝐥...',
            'bar': '🟩🟩🟩🟩🟩🟩🟩🟩🟩⬜',
            'status': '🎖️ 𝙰𝚌𝚌𝚞𝚛𝚊𝚌𝚢 𝚅𝚎𝚛𝚒𝚏𝚒𝚌𝚊𝚝𝚒𝚘𝚗...'
        },
        {
            'percent': 100,
            'text': '🎉 𝐒𝐢𝐠𝐧𝐚𝐥 𝐑𝐞𝐚𝐝𝐲!',
            'bar': '🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩',
            'status': '✨ 𝙲𝚘𝚖𝚙𝚕𝚎𝚝𝚎𝚍 𝚂𝚞𝚌𝚌𝚎𝚜𝚜𝚏𝚞𝚕𝚕𝚢!'
        }
    ]
    
    for stage in loading_stages:
        loading_message = f"""
╔═══════════════════════════════════╗
║   <b>🎯 𝐐𝐔𝐎𝐓𝐄𝐗 𝐒𝐈𝐆𝐍𝐀𝐋 𝐆𝐄𝐍𝐄𝐑𝐀𝐓𝐎𝐑</b>   ║
╚═══════════════════════════════════╝

<b>{stage['text']}</b>

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  <b>𝐏𝐫𝐨𝐠𝐫𝐞𝐬𝐬:</b> <code>{stage['percent']}%</code>
┃  
┃  {stage['bar']}
┃  
┃  <i>{stage['status']}</i>
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

<b>⏳ 𝙿𝚕𝚎𝚊𝚜𝚎 𝚆𝚊𝚒𝚝...</b>

<i>🔐 𝚂𝚎𝚌𝚞𝚛𝚎 𝙰𝚗𝚊𝚕𝚢𝚜𝚒𝚜 𝚒𝚗 𝙿𝚛𝚘𝚐𝚛𝚎𝚜𝚜</i>
"""
        
        try:
            await query.edit_message_text(
                loading_message,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.warning(f"Loading animation edit failed: {e}")
        
        # Wait between stages
        await asyncio.sleep(0.4)


async def show_loading_animation_new(message, user_id):
    """Show unique loading animation for new signal requests"""
    loading_stages = [
        {
            'percent': 0,
            'text': '⏳ 𝐈𝐧𝐢𝐭𝐢𝐚𝐥𝐢𝐳𝐢𝐧𝐠...',
            'bar': '⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜',
            'status': '🔄 𝚂𝚝𝚊𝚛𝚝𝚒𝚗𝚐 𝙰𝚗𝚊𝚕𝚢𝚜𝚒𝚜...'
        },
        {
            'percent': 15,
            'text': '🔍 𝐒𝐜𝐚𝐧𝐧𝐢𝐧𝐠...',
            'bar': '🟦⬜⬜⬜⬜⬜⬜⬜⬜⬜',
            'status': '📊 𝙲𝚘𝚕𝚕𝚎𝚌𝚝𝚒𝚗𝚐 𝙼𝚊𝚛𝚔𝚎𝚝 𝙳𝚊𝚝𝚊...'
        },
        {
            'percent': 30,
            'text': '📈 𝐀𝐧𝐚𝐥𝐲𝐳𝐢𝐧𝐠...',
            'bar': '🟦🟦🟦⬜⬜⬜⬜⬜⬜⬜',
            'status': '🎯 𝙿𝚛𝚘𝚌𝚎𝚜𝚜𝚒𝚗𝚐 𝙸𝚗𝚍𝚒𝚌𝚊𝚝𝚘𝚛𝚜...'
        },
        {
            'percent': 45,
            'text': '🧮 𝐂𝐚𝐥𝐜𝐮𝐥𝐚𝐭𝐢𝐧𝐠...',
            'bar': '🟦🟦🟦🟦⬜⬜⬜⬜⬜⬜',
            'status': '💹 𝙲𝚘𝚖𝚙𝚞𝚝𝚒𝚗𝚐 𝚂𝚒𝚐𝚗𝚊𝚕 𝚂𝚝𝚛𝚎𝚗𝚐𝚝𝚑...'
        },
        {
            'percent': 60,
            'text': '🎯 𝐏𝐫𝐨𝐜𝐞𝐬𝐬𝐢𝐧𝐠...',
            'bar': '🟦🟦🟦🟦🟦🟦⬜⬜⬜⬜',
            'status': '🔮 𝙴𝚟𝚊𝚕𝚞𝚊𝚝𝚒𝚗𝚐 𝙿𝚊𝚝𝚝𝚎𝚛𝚗𝚜...'
        },
        {
            'percent': 75,
            'text': '✨ 𝐎𝐩𝐭𝐢𝐦𝐢𝐳𝐢𝐧𝐠...',
            'bar': '🟩🟩🟩🟩🟩🟩🟩⬜⬜⬜',
            'status': '💡 𝙵𝚒𝚗𝚎-𝚝𝚞𝚗𝚒𝚗𝚐 𝚂𝚝𝚛𝚊𝚝𝚎𝚐𝚢...'
        },
        {
            'percent': 90,
            'text': '🚀 𝐅𝐢𝐧𝐚𝐥𝐢𝐳𝐢𝐧𝐠...',
            'bar': '🟩🟩🟩🟩🟩🟩🟩🟩🟩⬜',
            'status': '🎖️ 𝙰𝚌𝚌𝚞𝚛𝚊𝚌𝚢 𝚅𝚎𝚛𝚒𝚏𝚒𝚌𝚊𝚝𝚒𝚘𝚗...'
        },
        {
            'percent': 100,
            'text': '🎉 𝐒𝐢𝐠𝐧𝐚𝐥 𝐑𝐞𝐚𝐝𝐲!',
            'bar': '🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩',
            'status': '✨ 𝙲𝚘𝚖𝚙𝚕𝚎𝚝𝚎𝚍 𝚂𝚞𝚌𝚌𝚎𝚜𝚜𝚏𝚞𝚕𝚕𝚢!'
        }
    ]
    
    for stage in loading_stages:
        loading_message = f"""
╔═══════════════════════════════════╗
║   <b>🎯 𝐐𝐔𝐎𝐓𝐄𝐗 𝐒𝐈𝐆𝐍𝐀𝐋 𝐆𝐄𝐍𝐄𝐑𝐀𝐓𝐎𝐑</b>   ║
╚═══════════════════════════════════╝

<b>{stage['text']}</b>

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  <b>𝐏𝐫𝐨𝐠𝐫𝐞𝐬𝐬:</b> <code>{stage['percent']}%</code>
┃  
┃  {stage['bar']}
┃  
┃  <i>{stage['status']}</i>
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

<b>⏳ 𝙿𝚕𝚎𝚊𝚜𝚎 𝚆𝚊𝚒𝚝...</b>

<i>🔐 𝚂𝚎𝚌𝚞𝚛𝚎 𝙰𝚗𝚊𝚕𝚢𝚜𝚒𝚜 𝚒𝚗 𝙿𝚛𝚘𝚐𝚛𝚎𝚜𝚜</i>
"""
        
        try:
            await message.edit_text(
                loading_message,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.warning(f"Loading animation edit failed: {e}")
        
        # Wait between stages
        await asyncio.sleep(0.4)


async def timeframe_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle timeframe selection and generate signal"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Check signal limit
    if not check_signal_limit(user_id):
        # User has reached limit - show referral message
        user_info = get_user_info(user_id)
        bot_username = context.bot.username
        referral_link = f"https://t.me/{bot_username}?start={user_id}"
        
        limit_message = f"""
╔══════════════════════════════════╗
║   <b>⚠️ 𝐋𝐈𝐌𝐈𝐓 𝐑𝐄𝐀𝐂𝐇𝐄𝐃</b>   ║
╚══════════════════════════════════╝

<b>🚫 You've used all your free signals!</b>

<b>📊 Your Stats:</b>
• Signals Used: {user_info["signals_used"]}/{user_info["signal_limit"]}
• Total Referrals: {len(user_info["referrals"])}

<b>🎁 Get More Free Signals:</b>
Share your referral link with friends!
<b>+5 signals per referral</b> 🎉

<b>🔗 Your Referral Link:</b>
<code>{referral_link}</code>

<b>💡 Benefits:</b>
✅ You get <b>+5 free signals</b> per friend
✅ Your friends get <b>15 signals</b> (instead of 10)
✅ Unlimited referrals = Unlimited signals!

<i>📤 Forward this link to your friends now!</i>
"""
        
        keyboard = [
            [InlineKeyboardButton("👤 𝐌𝐲 𝐌𝐞𝐧𝐮", callback_data="my_menu")],
            [InlineKeyboardButton("🔙 𝐁𝐚𝐜𝐤 𝐭𝐨 𝐌𝐚𝐢𝐧", callback_data="back_market")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if query.message.photo:
            await query.message.delete()
            await query.message.reply_text(
                limit_message,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_text(
                limit_message,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
        return
    
    time_index = int(query.data.split('_')[1])
    selected_timeframe = TIMEFRAMES[time_index]
    
    # Initialize user data if not exists (for new signal button)
    if user_id not in user_data:
        user_data[user_id] = {}
    
    user_data[user_id]['timeframe'] = selected_timeframe
    
    # Increment signals used counter
    use_signal(user_id)
    
    # Send new loading message (don't edit the previous one)
    loading_msg = await query.message.reply_text(
        "🔄 Generating signal...",
        parse_mode=ParseMode.HTML
    )
    
    # Show unique animated loading
    await show_loading_animation_new(loading_msg, user_id)
    
    # Generate signal
    signal = await generate_signal(user_id)
    
    # Create short signal message
    timeframe_str = signal['timeframe']
    hours = int(timeframe_str.split(':')[0])
    minutes = int(timeframe_str.split(':')[1])
    total_seconds = hours * 3600 + minutes * 60
    
    # Dynamic trade time calculation based on timeframe
    # For 1M, 2M, 5M: 1-3 minutes delay with exact minute (no seconds)
    if total_seconds in [60, 120, 300]:  # 1M, 2M, 5M
        # Get next exact minute (1-3 minutes from now)
        minutes_delay = random.randint(1, 3)  # 1-3 minutes
        current_time = datetime.now()
        # Round up to next minute and add delay
        next_minute = (current_time + timedelta(minutes=1)).replace(second=0, microsecond=0)
        trade_time = next_minute + timedelta(minutes=minutes_delay - 1)
        trade_time_str = trade_time.strftime("%H:%M:00")  # Exact minute format
    else:
        # Default for longer timeframes: 1-3 minutes with exact minute
        minutes_delay = random.randint(1, 3)
        current_time = datetime.now()
        next_minute = (current_time + timedelta(minutes=1)).replace(second=0, microsecond=0)
        trade_time = next_minute + timedelta(minutes=minutes_delay - 1)
        trade_time_str = trade_time.strftime("%H:%M:00")
    
    signal_message = f"""
🎲 <b>UTC +6:00</b>
<b>{signal['pair']} Quotex</b>
⏰ <code>{timeframe_str}</code>
🎯 <b>{signal['direction']}</b>
⏱ <b>Trade Time: {trade_time_str}</b>

✔️ <b>Backtested: High accuracy!</b>
💹 <b>Market is within safe range</b>
⚡ <b>If You Lose Use 1 Step MTG .</b>
"""
    
    # Select image based on direction
    image_path = "up.png" if signal['direction'] == "CALL" else "down.png"
    
    # Create action buttons
    keyboard = [
        [
            InlineKeyboardButton("🔄 𝐍𝐞𝐰 𝐒𝐢𝐠𝐧𝐚𝐥", callback_data=f"time_{time_index}"),
            InlineKeyboardButton("⏱ 𝐂𝐡𝐚𝐧𝐠𝐞 𝐓𝐢𝐦𝐞", callback_data=f"pair_{TIMEFRAMES.index(selected_timeframe)}")
        ],
        [
            InlineKeyboardButton("💱 𝐂𝐡𝐚𝐧𝐠𝐞 𝐏𝐚𝐢𝐫", callback_data=f"market_{user_data[user_id]['market_type']}"),
            InlineKeyboardButton("🏠 𝐌𝐚𝐢𝐧 𝐌𝐞𝐧𝐮", callback_data="back_market")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send photo with signal message
    try:
        # Delete the loading message
        await loading_msg.delete()
        
        # Send new message with photo
        with open(image_path, 'rb') as photo:
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=photo,
                caption=signal_message,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
    except FileNotFoundError:
        # If images not found, send without image
        await loading_msg.delete()
        await query.message.reply_text(
            signal_message,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )


async def back_to_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Go back to market selection"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    welcome_message = """
╔═══════════════════════════════════╗
║  <b>⚡ 𝐐 𝐒𝐈𝐆𝐍𝐀𝐋 𝐌�𝐊�� ⚡</b>  ║
╚═══════════════════════════════════╝

<b>📊 𝐒𝐞𝐥𝐞𝐜𝐭 𝐌𝐚𝐫𝐤𝐞𝐭 𝐓𝐲𝐩𝐞:</b>
"""
    
    keyboard = [
        [
            InlineKeyboardButton("🌙 𝐎𝐓𝐂 𝐌𝐚𝐫𝐤𝐞𝐭", callback_data="market_otc"),
            InlineKeyboardButton("🌞 𝐑𝐞𝐚𝐥 𝐌𝐚𝐫𝐤𝐞𝐭", callback_data="market_real")
        ],
        [
            InlineKeyboardButton("👤 𝐌𝐲 𝐌𝐞𝐧𝐮", callback_data="my_menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Check if message has photo (can't edit photo to text)
    if query.message.photo:
        await query.message.delete()
        await query.message.reply_text(
            welcome_message,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    else:
        await query.edit_message_text(
            welcome_message,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )


async def my_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's personal menu with stats and referral link"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_info = get_user_info(user_id)
    
    # Calculate stats
    remaining_signals = user_info["signal_limit"] - user_info["signals_used"]
    total_referrals = len(user_info["referrals"])
    
    # Generate referral link
    bot_username = context.bot.username
    referral_link = f"https://t.me/{bot_username}?start={user_id}"
    
    # Get referral usernames
    referral_list = ""
    if total_referrals > 0:
        referral_names = []
        for ref_id in user_info["referrals"][:10]:  # Show max 10
            ref_info = get_user_info(int(ref_id))
            ref_name = ref_info.get("first_name", "Unknown")
            referral_names.append(f"  • {ref_name}")
        referral_list = "\n".join(referral_names)
        if total_referrals > 10:
            referral_list += f"\n  <i>... and {total_referrals - 10} more</i>"
    else:
        referral_list = "  <i>No referrals yet</i>"
    
    menu_message = f"""
╔══════════════════════════════════╗
║     <b>👤 𝐌𝐘 𝐏𝐑𝐎𝐅𝐈𝐋𝐄 𝐌𝐄𝐍𝐔</b>     ║
╚══════════════════════════════════╝

<b>📊 Your Statistics:</b>
━━━━━━━━━━━━━━━━━━━━━━━
🎁 <b>Free Signals Remaining:</b> {remaining_signals}/{user_info["signal_limit"]}
📈 <b>Signals Used:</b> {user_info["signals_used"]}
👥 <b>Total Referrals:</b> {total_referrals}

<b>🔗 Your Referral Link:</b>
<code>{referral_link}</code>

<b>💡 How It Works:</b>
• Share your link with friends
• Each referral gives you <b>+5 signals</b>
• Your friends get <b>15 signals</b> (vs 10)

<b>👥 Your Referrals:</b>
{referral_list}

<b>━━━━━━━━━━━━━━━━━━━━━━━</b>
<i>💬 Forward this link to your friends and earn unlimited free signals!</i>
"""
    
    keyboard = [
        [InlineKeyboardButton("� 𝐒𝐡𝐚𝐫𝐞 𝐰𝐢𝐭𝐡 𝐅𝐫𝐢𝐞𝐧𝐝𝐬", callback_data="share_friends")],
        [InlineKeyboardButton("�🔙 𝐁𝐚𝐜𝐤 𝐭𝐨 𝐌𝐚𝐢𝐧", callback_data="back_market")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Check if message has photo
    if query.message.photo:
        await query.message.delete()
        await query.message.reply_text(
            menu_message,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    else:
        await query.edit_message_text(
            menu_message,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )


async def share_with_friends(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate shareable promotional message"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Generate referral link
    bot_username = context.bot.username
    referral_link = f"https://t.me/{bot_username}?start={user_id}"
    
    # Create promotional message
    promo_message = f"""
╔═══════════════════════════════════╗
║  <b>⚡ 𝐐 𝐒𝐈𝐆𝐍𝐀𝐋 ���𝐄𝐑 ⚡</b>  ║
╚═══════════════════════════════════╝

<b>� Premium Trading Signals - 100% FREE!</b>

<b>✨ 100% FREE - LIFETIME ACCESS ✨</b>

<b>🎁 Special Offer:</b>
━━━━━━━━━━━━━━━━━━━━━━━━
✅ Get <b>15 FREE Signals</b> instantly!
📈 High accuracy predictions
🌐 OTC & Real market support
⏰ Multiple timeframes available
💯 Backtested strategies
🔄 Unlimited signals via referrals

<b>💎 Features:</b>
• Real-time signal generation
• Professional technical analysis
• User-friendly interface
• 24/7 availability
• Free forever!

<b>🔗 Join Now:</b>
{referral_link}

<b>━━━━━━━━━━━━━━━━━━━━━━━━</b>
<i>⚡ Click the link above and start trading with confidence!</i>
<i>💰 Share with friends and earn MORE free signals!</i>
"""
    
    # Create share URL with encoded message
    import urllib.parse
    share_text_encoded = urllib.parse.quote(promo_message.replace('<b>', '').replace('</b>', '').replace('<i>', '').replace('</i>', ''))
    share_url = f"https://t.me/share/url?text={share_text_encoded}"
    
    # Create inline keyboard with share button
    keyboard = [
        [InlineKeyboardButton("📤 𝐅𝐨𝐫𝐰𝐚𝐫𝐝 𝐭𝐨 𝐅𝐫𝐢𝐞𝐧𝐝𝐬", url=share_url)],
        [InlineKeyboardButton("🔗 𝐂𝐨𝐩𝐲 𝐋𝐢𝐧𝐤", callback_data="copy_link")],
        [InlineKeyboardButton("🔙 𝐁𝐚𝐜𝐤 𝐭𝐨 𝐌𝐞𝐧𝐮", callback_data="my_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Check if message has photo
    if query.message.photo:
        await query.message.delete()
        await query.message.reply_text(
            promo_message,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    else:
        await query.edit_message_text(
            promo_message,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all button callbacks"""
    query = update.callback_query
    callback_data = query.data
    
    if callback_data.startswith("market_"):
        await market_selection(update, context)
    elif callback_data.startswith("pair_"):
        await pair_selection(update, context)
    elif callback_data.startswith("time_"):
        await timeframe_selection(update, context)
    elif callback_data == "back_market":
        await back_to_market(update, context)
    elif callback_data == "my_menu":
        await my_menu(update, context)
    elif callback_data == "share_friends":
        await share_with_friends(update, context)
    elif callback_data == "copy_link":
        await query.answer("✅ Link is displayed above - tap and hold to copy!", show_alert=True)


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline queries for sharing"""
    query = update.inline_query.query
    user_id = update.inline_query.from_user.id
    
    # Generate referral link
    bot_username = context.bot.username
    referral_link = f"https://t.me/{bot_username}?start={user_id}"
    
    # Create full promotional message for sharing
    share_text = f"""
╔═══════════════════════════════════╗
║  *⚡ QX SIGNAL MAKER ⚡*  ║
╚═══════════════════════════════════╝

*� Premium Trading Signals - 100% FREE!*

*✨ 100% FREE - LIFETIME ACCESS ✨*

*🎁 Special Offer:*
━━━━━━━━━━━━━━━━━━━━━━━━
✅ Get *15 FREE Signals* instantly!
📈 High accuracy predictions
🌐 OTC & Real market support
⏰ Multiple timeframes available
💯 Backtested strategies
🔄 Unlimited signals via referrals

*� Features:*
• Real-time signal generation
• Professional technical analysis
• User-friendly interface
• 24/7 availability
• Free forever!

*�🔗 Join Now:*
{referral_link}

*━━━━━━━━━━━━━━━━━━━━━━━━*
_⚡ Click the link above and start trading with confidence!_
_💰 Share with friends and earn MORE free signals!_
"""
    
    results = [
        InlineQueryResultArticle(
            id="1",
            title="⚡ Share QX Signal Maker",
            description="Share this premium FREE signal bot with your friends!",
            input_message_content=InputTextMessageContent(
                message_text=share_text,
                parse_mode="Markdown"
            ),
            thumb_url="https://i.imgur.com/QqBBQqE.png"  # Optional thumbnail
        )
    ]
    
    await update.inline_query.answer(results, cache_time=300)


def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(InlineQueryHandler(inline_query))
    
    # Start the bot
    logger.info("Bot started successfully!")
    print("Bot is running... Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
