import asyncio
from telegram import Bot

# Bot token
TOKEN = "8441476926:AAGWc1_v-BDSxx3yKUw0Dh6vbft5sVhLP9I"

# Channel usernames
channels = ["@DevJisanX", "@treaderjisanx", "@SingleBotMaker"]

async def get_channel_ids():
    bot = Bot(token=TOKEN)
    
    print("Fetching channel IDs...\n")
    
    for channel in channels:
        try:
            chat = await bot.get_chat(channel)
            print(f"Channel: {channel}")
            print(f"ID: {chat.id}")
            print(f"Title: {chat.title}")
            print(f"Type: {chat.type}")
            print("-" * 50)
        except Exception as e:
            print(f"Error fetching {channel}: {e}")
            print("-" * 50)

if __name__ == "__main__":
    asyncio.run(get_channel_ids())
