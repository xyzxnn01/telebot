# 🎯 Quotex Trading Signal Telegram Bot

একটি প্রফেশনাল এবং ইউনিক Telegram Bot যা Quotex Trading এর জন্য Real-time Signal প্রদান করে।

## ✨ Features

- 🌙 **OTC Market Support** - 34টি OTC Currency Pairs
- 🌞 **Real Market Support** - 34টি Real Currency Pairs  
- ⏱️ **Multiple Timeframes** - 5, 10, 15, 30 মিনিট এবং 1, 2, 5 ঘন্টা
- 📊 **Technical Analysis** - RSI, MACD, Stochastic indicators
- 🎯 **High Accuracy Signals** - 75-98% confidence level
- 💱 **Beautiful UI** - HTML formatted messages with emojis
- 🔄 **Loading Animation** - Professional loading experience
- 📈 **Martingale Strategy** - Smart risk management

## 📦 Installation

### 1. Python Install করুন
আপনার কম্পিউটারে Python 3.8+ install করা থাকতে হবে।

### 2. Dependencies Install করুন

```powershell
cd "d:\Telegram Bot"
pip install -r requirements.txt
```

### 3. Bot Run করুন

```powershell
python bot.py
```

## 🚀 Usage

1. Telegram এ আপনার bot খুঁজে বের করুন
2. `/start` command দিয়ে bot শুরু করুন
3. Market Type সিলেক্ট করুন (OTC বা Real)
4. Currency Pair সিলেক্ট করুন
5. Timeframe সিলেক্ট করুন
6. Signal receive করুন!

## 🎮 Bot Commands

- `/start` - Bot শুরু করুন এবং login করুন

## 📊 Supported Currency Pairs

### OTC Market (34 pairs)
NZD/CHF, USD/BRL, EUR/GBP, GBP/AUD, GBP/JPY, GBP/USD, USD/JPY, USD/ZAR, EUR/AUD, EUR/CAD, EUR/JPY, EUR/USD, GBP/CAD, GBP/CHF, USD/CAD, USD/CHF, AUD/NZD, CAD/CHF, CHF/JPY, EUR/SGD, USD/MXN, USD/COP, NZD/CAD, USD/ARS, EUR/CHF, USD/IDR, USD/NGN, AUD/CAD, AUD/JPY, AUD/USD, USD/BDT, USD/PHP, USD/PKR, USD/TRY

### Real Market (34 pairs)
একই pairs কিন্তু Real Market এর জন্য

## ⏱️ Timeframes

- 00:05 - 5 Minutes (Default)
- 00:10 - 10 Minutes
- 00:15 - 15 Minutes
- 00:30 - 30 Minutes
- 01:00 - 1 Hour
- 02:00 - 2 Hours
- 05:00 - 5 Hours

## 🔧 Configuration

Bot Token `bot.py` file এ configure করা আছে:
```python
BOT_TOKEN = "8441476926:AAGWc1_v-BDSxx3yKUw0Dh6vbft5sVhLP9I"
```

## 📝 Signal Format

প্রতিটি signal এ থাকে:
- 🎯 Direction (CALL/PUT)
- 💱 Currency Pair
- ⏱️ Timeframe
- 💰 Entry Price
- ⏰ Expiry Time
- 🎲 Martingale Levels
- 📊 Technical Indicators (RSI, MACD, Stochastic)
- ✅ Confidence Level

## ⚠️ Disclaimer

এই bot educational purposes এর জন্য। Trading এ সবসময় risk থাকে। নিজ দায়িত্বে trade করুন এবং proper risk management ব্যবহার করুন।

## 🌐 Hosting

### Local Server (আপনার PC তে)
```powershell
python bot.py
```

### Cloud Hosting (পরবর্তীতে)
- Heroku
- PythonAnywhere
- AWS/Google Cloud
- VPS Server

## 📞 Support

কোন সমস্যা হলে bot developer এর সাথে যোগাযোগ করুন।

---

<div align="center">
  <b>Made with ❤️ for Quotex Traders</b>
</div>
