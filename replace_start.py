# New start function with full channel verification
NEW_START_FUNCTION = '''async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    # Detect language (Bangladesh = Bangla, others = English)
    language_code = user.language_code or "en"
    is_bangla = language_code == "bn" or language_code == "bn-BD"
    
    # Handle referral if present - store as pending until channel verification
    if context.args and len(context.args) > 0:
        try:
            referrer_id = int(context.args[0])
            if referrer_id != user_id and user_info["referred_by"] is None and user_info.get("pending_referrer") is None:
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

<b>🚀 𝐏𝐫𝐨 𝐓𝐫𝐚𝐝𝐢𝐧𝐠 𝐒𝐢𝐠𝐧𝐚𝐥𝐬 𝐁𝐨𝐭</b>

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
        return
    
    # User needs to join channels - show welcome message with channel join buttons
    user_name = user.first_name or user.username or "Trader"
    
    # Check which channels user already joined
    joined_channels, not_joined = await check_channel_membership(user_id, context)
    
    # Create attractive welcome message based on language and referral status
    has_referrer = user_info.get("pending_referrer") is not None
    
    if is_bangla:
        # Bangla welcome message
        welcome_msg = f"""
╔═══════════════════════════════════╗
║  <b>⚡ 𝐐𝐗 𝐒𝐈𝐆𝐍𝐀𝐋 𝐌𝐀𝐊𝐄𝐑 ⚡</b>  ║
╚═══════════════════════════════════╝

<b>🎉 স্বাগতম {user_name}! 🎉</b>

<b>💎 বিশ্বের সেরা ট্রেডিং সিগন্যাল বট! 💎</b>

━━━━━━━ <b>🌟 বিশেষ সুবিধা</b> 🌟 ━━━━━━━
✨ <b>100% একদম ফ্রি</b> - কোন খরচ নেই!
💰 প্রতিদিন <b>$100-$150</b> আয় করুন
🎯 <b>95%+ নিখুঁত</b> সিগন্যাল
⚡ রিয়েল-টাইম ট্রেডিং সিগন্যাল
🌐 OTC ও Real মার্কেট সাপোর্ট
⏰ একাধিক টাইমফ্রেম
━━━━━━━━━━━━━━━━━━━━━━━━

<b>🎁 আপনার ফ্রি সিগন্যাল:</b>
{'🌟 <b>15টি সিগন্যাল</b> - রেফারেল বোনাস!' if has_referrer else '🎁 <b>10টি সিগন্যাল</b> একদম ফ্রি!'}

<b>🚀 আরও সিগন্যাল পেতে:</b>
👥 প্রতি রেফারে = <b>+5 সিগন্যাল</b>
🔗 বন্ধুদের শেয়ার করুন
💎 আনলিমিটেড সিগন্যাল পান!

━━━━━━━━━━━━━━━━━━━━━━━━

<b>⚠️ বট ব্যবহারের জন্য:</b>
নিচের <b>তিনটি চ্যানেলে জয়েন</b> করুন
তারপর <b>"চেক করুন ✅"</b> বাটনে ক্লিক করুন

<b>👇 এখনই চ্যানেলে জয়েন করুন 👇</b>
"""
    else:
        # English welcome message
        welcome_msg = f"""
╔═══════════════════════════════════╗
║  <b>⚡ 𝐐𝐗 𝐒𝐈𝐆𝐍𝐀𝐋 𝐌𝐀𝐊𝐄𝐑 ⚡</b>  ║
╚═══════════════════════════════════╝

<b>🎉 Welcome {user_name}! 🎉</b>

<b>💎 World's Best Trading Signals Bot! 💎</b>

━━━━━━━ <b>🌟 Amazing Features</b> 🌟 ━━━━━━━
✨ <b>100% FREE</b> - No Hidden Costs!
💰 Earn <b>$100-$150 Daily</b>
🎯 <b>95%+ Accuracy</b> Rate
⚡ Real-Time Trading Signals
🌐 OTC & Real Market Support
⏰ Multiple Timeframes Available
━━━━━━━━━━━━━━━━━━━━━━━━

<b>🎁 Your Free Signals:</b>
{'🌟 <b>15 Signals</b> - Referral Bonus!' if has_referrer else '🎁 <b>10 Signals</b> Absolutely Free!'}

<b>🚀 Get More Signals:</b>
👥 Each Referral = <b>+5 Signals</b>
🔗 Share with Friends
💎 Unlock Unlimited Signals!

━━━━━━━━━━━━━━━━━━━━━━━━

<b>⚠️ To Start Using Bot:</b>
Join <b>3 Channels</b> below
Then click <b>"Check Membership ✅"</b>

<b>👇 Join Our Channels Now 👇</b>
"""
    
    # Create keyboard with channel join buttons (only show not joined channels)
    keyboard = []
    for channel_username in REQUIRED_CHANNELS.keys():
        if channel_username in not_joined:
            keyboard.append([InlineKeyboardButton(
                f"📢 Join {channel_username}",
                url=f"https://t.me/{channel_username[1:]}"  # Remove @ from username
            )])
    
    # Add check membership button
    if is_bangla:
        keyboard.append([InlineKeyboardButton("✅ চেক করুন", callback_data="check_channels")])
    else:
        keyboard.append([InlineKeyboardButton("✅ Check Membership", callback_data="check_channels")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_msg,
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup
    )
'''

# Read the file
with open("bot.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find and replace the start function
import re

# Find the start function and the next function definition
pattern = r'async def start\(update: Update, context: ContextTypes\.DEFAULT_TYPE\):.*?(?=\nasync def )'
replacement = NEW_START_FUNCTION + '\n\n'

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write back
with open("bot.py", "w", encoding="utf-8") as f:
    f.write(new_content)

print("✅ Start function replaced successfully!")
