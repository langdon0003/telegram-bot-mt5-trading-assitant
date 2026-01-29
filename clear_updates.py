#!/usr/bin/env python3
"""
Clear all pending Telegram updates

This script drops all pending updates in the Telegram queue
to prevent rate limiting issues on bot restart.
"""

import os
import sys
from dotenv import load_dotenv
import requests
import time

# Load environment variables
load_dotenv()

# Get bot token
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not BOT_TOKEN:
    print("❌ Error: TELEGRAM_BOT_TOKEN not found in .env file")
    sys.exit(1)

print(f"🤖 Bot Token: {BOT_TOKEN[:10]}...{BOT_TOKEN[-5:]}")
print("\n🔄 Clearing pending updates...\n")

try:
    # Get pending updates
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    response = requests.get(url, timeout=10)

    if response.status_code == 429:
        retry_after = response.json().get('parameters', {}).get('retry_after', 10)
        print(f"⚠️  Bot is rate limited. Need to wait {retry_after} seconds...")
        print(f"   Please wait and run this script again after {retry_after}s")
        sys.exit(1)

    response.raise_for_status()
    data = response.json()

    if not data.get('ok'):
        print(f"❌ Error: {data.get('description', 'Unknown error')}")
        sys.exit(1)

    updates = data.get('result', [])

    if not updates:
        print("✅ No pending updates to clear")
        sys.exit(0)

    # Get the highest update_id
    last_update_id = updates[-1]['update_id']

    print(f"📊 Found {len(updates)} pending updates")
    print(f"   Last update ID: {last_update_id}")

    # Confirm before clearing
    print("\n⚠️  This will DISCARD all pending messages!")
    response_input = input("   Continue? (yes/no): ").strip().lower()

    if response_input != 'yes':
        print("❌ Cancelled")
        sys.exit(0)

    # Drop all updates by acknowledging with offset
    offset = last_update_id + 1
    clear_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}"
    clear_response = requests.get(clear_url, timeout=10)
    clear_response.raise_for_status()

    print(f"\n✅ Cleared {len(updates)} pending updates")
    print("   Bot is ready to start fresh!")
    print("\n💡 Wait 10 seconds before starting the bot")

except requests.exceptions.RequestException as e:
    print(f"❌ Network error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
