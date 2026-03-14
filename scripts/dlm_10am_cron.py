#!/usr/bin/env python3
"""
Name: dlm_10am_cron.py
Version: 1.0.0
Purpose: Run at 10 AM EDT - Check temp, if ≤65°F post DLM favorites to Discord
Author: Dwain Henderson Jr. | Superior Networks LLC
Contact: (937) 985-2480 | dhenderson@superiornetworks.biz
Copyright: 2026, Superior Networks LLC
Location: /root/.openclaw/SNDayton/scripts/dlm_10am_cron.py

What This Script Does:
  - Runs daily at 10 AM EDT (when DLM menu is fresh)
  - Checks current temperature via wttr.in
  - If temp ≤ 65°F, runs DLM favorites command
  - Posts result to #general Discord channel via webhook
  - Sends JSON output formatted for Discord embeds

Input:
  - None (cron-triggered)

Output:
  - Discord message in #general with DLM favorites
  - Returns nothing if temp is above threshold

Dependencies:
  - requests
  - dlm_commands (DLMCommandHandler)
  - json (built-in)

Change Log:
  2026-03-14 v1.0.0 - Initial release (Dwain Henderson Jr)
"""

import json
import requests
import sys

sys.path.insert(0, '/root/.openclaw/SNDayton/scripts')
from dlm_commands import DLMCommandHandler

def get_current_temp():
    """Get current temperature from wttr.in"""
    try:
        response = requests.get('https://wttr.in/Dayton,Ohio?format=j1', timeout=5)
        if response.status_code == 200:
            data = response.json()
            current_temp = int(data['current_condition'][0]['temp_F'])
            return current_temp
    except Exception as e:
        print(f"❌ Error getting weather: {e}")
    return None

def post_to_discord(message):
    """Post message to Discord #general"""
    webhook_url = None
    try:
        with open('/root/.openclaw/SNDayton/config/discord_webhook.txt') as f:
            webhook_url = f.read().strip()
    except:
        print("❌ No webhook URL found")
        return False
    
    if not webhook_url:
        print("❌ Webhook URL is empty")
        return False
    
    try:
        # Parse message as JSON if it is JSON
        if isinstance(message, str) and message.startswith('{'):
            msg_data = json.loads(message)
        else:
            msg_data = message
        
        response = requests.post(webhook_url, json=msg_data, timeout=10)
        
        if response.status_code == 204:
            return True
        else:
            print(f"❌ Discord post failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error posting to Discord: {e}")
        return False

def main():
    print("[10 AM DLM Check]")
    
    # Get current temperature
    current_temp = get_current_temp()
    
    if not current_temp:
        print("❌ Could not get temperature")
        return
    
    print(f"Current temp: {current_temp}°F")
    
    # Check if temp triggers DLM
    threshold = 65
    if current_temp > threshold:
        print(f"⏭️  Skipping (temp {current_temp}°F > {threshold}°F threshold)")
        return
    
    print(f"✅ Temp {current_temp}°F ≤ {threshold}°F - Running DLM soup command")
    
    # Get DLM favorites
    handler = DLMCommandHandler()
    result = handler.handle_command('favorites')
    
    # Add header
    result['content'] = f"☀️ **10 AM SOUP CHECK** (Dayton: {current_temp}°F)\n\n{result.get('content', '')}"
    
    # Post to Discord
    if post_to_discord(result):
        print("✅ Posted to Discord #general")
    else:
        print("❌ Failed to post to Discord")

if __name__ == "__main__":
    main()
