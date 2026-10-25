# ═══════════════════════════════════════════════════════════════
# Dev: @NOORX771 (Telegram Control Version)
# ═══════════════════════════════════════════════════════════════
import os
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import login_engine
import bot_core
from bot_core import (
    TcPOnLine,
    TcPChaT,
    build_ob55_online_auth,
    create_auth_token_chat,
)

# ─── Config ───
TELEGRAM_BOT_TOKEN = os.environ.get("BOT_TOKEN", "8510543770:AAEHSpib5zdObv1F1MLKReQhVmrkERTlKFE")
ADMIN_USERNAME = "NOORX771"  # Sirf is username ko access milega
REGION_PREF = os.environ.get("REGION", "IND")

# Accounts List
ACCOUNTS = [
    {
        "UID": "8324238347",
        "PW": "B2A712A9E12A091F474CDE18C85F65148D9D2ED487C10666CFD54D22C6336DB5"
    }
]

# Global task trackers
running_tasks = {}
cs_match_tasks = {}

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# ─── Bot Core Logic ───
async def MaiiiinE(uid, pw):
    print(f"[*] Starting login for UID: {uid}...")
    result = await login_engine.do_login(uid, pw, REGION_PREF)
    if not result:
        print(f"[-] Login failed for UID {uid}, retry in 10s...")
        await asyncio.sleep(10)
        return
    
    bot_uid = result["bot_uid"]
    token   = result["token"]
    region  = result["region"]
    key       = result["key"]
    iv        = result["iv"]
    timestamp = result["timestamp"]
    online_ip = result["online_ip"]
    online_port = result["online_port"]
    chat_ip   = result["chat_ip"]
    chat_port = result["chat_port"]
    acc_name  = result["account_name"]
    
    print(f"[+] UID: {bot_uid} | Region: {region} | Name: {acc_name}")
    
    ChatAutH = create_auth_token_chat(int(bot_uid), token, int(timestamp), key, iv)
    OnlineAutH, _ = build_ob55_online_auth(int(bot_uid), token, int(timestamp), key, iv)
    
    ready_event = asyncio.Event()
    t1 = asyncio.create_task(TcPChaT(chat_ip, chat_port, ChatAutH, key, iv, ready_event, region))
    await ready_event.wait()
    await asyncio.sleep(1)
    t2 = asyncio.create_task(TcPOnLine(online_ip, online_port, key, iv, OnlineAutH))
    
    await asyncio.gather(t1, t2)

async def run_bot_account(uid, pw):
    while True:
        try:
            await asyncio.wait_for(MaiiiinE(uid, pw), timeout=7 * 60 * 60)
        except asyncio.TimeoutError:
            print(f"[!] Token expired for UID {uid}, restarting...")
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"[!] Error for UID {uid}: {e} -> Restarting in 5s...")
            await asyncio.sleep(5)

async def play_cs_match(uid):
    """Simulate bots creating a group and playing CS matches"""
    while True:
        try:
            print(f"[*] UID {uid} is in group building & playing CS match...")
            # Yahan CS match loop / custom packet logic execute hogi
            await asyncio.sleep(30)
        except asyncio.CancelledError:
            print(f"[-] CS match loop stopped for UID {uid}")
            break

# ─── Telegram Handlers ───
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.username != ADMIN_USERNAME:
        await update.message.reply_text("❌ Aapko is bot ko use karne ki permission nahi hai!")
        return
    
    await update.message.reply_text(
        "👋 Welcome Boss!\n\n"
        "Available Commands:\n"
        "👉 `/run all bot` - Saare bots ko online karke group banakar CS khelne ke liye\n"
        "👉 `stop` - Current match/activity rokne ke liye\n"
        "👉 `off` - Sabhi bots ko offline karne ke liye"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.username != ADMIN_USERNAME:
        return  # Unauthorized users ke messages ignore honge

    text = update.message.text.strip().lower()

    # 1. Run all bot command
    if text == "/run all bot":
        if running_tasks:
            await update.message.reply_text("⚠️ Bots pehle se hi running me hain!")
            return
        
        await update.message.reply_text("🚀 Free Fire bots login ho rahe hain aur CS match ke liye group ban raha hai...")
        
        for acc in ACCOUNTS:
            # Pehle account ko background me run karo
            task = asyncio.create_task(run_bot_account(acc["UID"], acc["PW"]))
            running_tasks[acc["UID"]] = task
            
            # Phir CS match task start karo
            cs_task = asyncio.create_task(play_cs_match(acc["UID"]))
            cs_match_tasks[acc["UID"]] = cs_task
            
        await update.message.reply_text("✅ Saare bots group banakar successfully CS match khelne lage hain!")

    # 2. Stop command
    elif text == "stop":
        if not cs_match_tasks:
            await update.message.reply_text("⚠️ Koi active match task nahi chal raha.")
            return
        
        for uid, task in cs_match_tasks.items():
            task.cancel()
        cs_match_tasks.clear()
        
        await update.message.reply_text("🛑 Match activity rok di gayi hai.")

    # 3. Off command
    elif text == "off":
        if not running_tasks and not cs_match_tasks:
            await update.message.reply_text("⚠️ Sabhi bots pehle se hi offline hain.")
            return
        
        for uid, task in cs_match_tasks.items():
            task.cancel()
        cs_match_tasks.clear()

        for uid, task in running_tasks.items():
            task.cancel()
        running_tasks.clear()
        
        await update.message.reply_text("🔌 Sabhi bots completely offline kar diye gaye hain.")

# ─── Main Execution ───
def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    # Text messages handle karne ke liye MessageHandler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("run", handle_message)) # Agar koi /run all bot command ki tarah dale
    
    print("[*] Telegram Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
