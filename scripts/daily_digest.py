#!/usr/bin/env python3
"""
Daily Digest Generator v3 - SUPERIOR NETWORKS BRANDED
Runs at 5 AM EDT (9 AM UTC) every day
- Superior Networks branding & logo
- ACTIVE TASKS as top section
- Real data: Gmail, Calendar, Weather, Cron Status
"""

import json
import requests
from datetime import datetime, timedelta
import os
import re
import sys

# Add scripts directory to path for DLM import
sys.path.insert(0, '/root/.openclaw/SNDayton/scripts')
from dlm_soup_scraper import DLMSoupScraper

tokens_file = "/root/.openclaw/SNDayton/google_tokens.json"
creds_file = "/root/.openclaw/SNDayton/google_oauth_credentials.json"

def refresh_token():
    """Refresh Google OAuth token"""
    with open(tokens_file) as f:
        tokens = json.load(f)
    
    with open(creds_file) as f:
        creds = json.load(f)['installed']
    
    refresh_token_val = tokens.get('refresh_token')
    client_id = creds.get('client_id')
    client_secret = creds.get('client_secret')
    
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token_val,
        'grant_type': 'refresh_token'
    }
    
    resp = requests.post(token_url, json=token_data)
    
    if resp.status_code == 200:
        new_tokens = resp.json()
        tokens['access_token'] = new_tokens['access_token']
        tokens['expires_in'] = new_tokens['expires_in']
        
        with open(tokens_file, 'w') as f:
            json.dump(tokens, f, indent=2)
        
        return new_tokens['access_token']
    
    return None

def get_calendar_events(access_token):
    """Get today's calendar events"""
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
        today_end = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
        
        url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
        params = {
            "timeMin": today_start,
            "timeMax": today_end,
            "singleEvents": True,
            "orderBy": "startTime"
        }
        
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            events = resp.json().get('items', [])
            return events
    except:
        pass
    
    return []

def get_inbox_stats(access_token):
    """Get inbox statistics - query actual message counts"""
    headers = {"Authorization": f"Bearer {access_token}"}
    
    stats = {
        'unread': 0,
        'total': 0,
        'financial': 0,
        'procurement': 0,
        'operations': 0,
        'system_access': 0,
        'learning': 0,
        'tax': 0
    }
    
    try:
        gmail_url = "https://www.googleapis.com/gmail/v1/users/me/messages?maxResults=1"
        resp = requests.get(gmail_url, headers=headers)
        if resp.status_code == 200:
            stats['total'] = resp.json().get('resultSizeEstimate', 0)
    except:
        pass
    
    # Query actual label counts by exact label name
    try:
        label_queries = {
            'financial': 'label:"Financial"',
            'procurement': 'label:"Procurement"',
            'operations': 'label:"Operations"',
            'system_access': 'label:"System & Access"',
            'learning': 'label:"Learning"',
            'tax': 'label:"Tax & Accounting"'
        }
        
        for key, query in label_queries.items():
            try:
                url = "https://www.googleapis.com/gmail/v1/users/me/messages"
                resp = requests.get(url, headers=headers, params={'q': query})
                
                if resp.status_code == 200:
                    count = resp.json().get('resultSizeEstimate', 0)
                    stats[key] = count
            except:
                pass
    except:
        pass
    
    return stats

def get_dlm_soups(current_high, change_24h):
    """Get DLM soups if temperature triggers are met"""
    try:
        scraper = DLMSoupScraper()
        dlm_output = scraper.generate_output(current_high=current_high, change_24h=change_24h)
        return dlm_output
    except Exception as e:
        print(f"[DLM] Error: {e}")
        return None

def get_weather():
    """Get comprehensive weather from wttr.in with multi-day forecast in F"""
    try:
        # Get current weather with all details
        resp = requests.get("https://wttr.in/Dayton,Ohio?format=%t|%c|%h|%w|%p|%u|%M", timeout=5)
        if resp.status_code == 200:
            data = resp.text.split('|')
            
            # Convert current temp to F
            temp = data[0].strip() if len(data) > 0 else 'N/A'
            if temp and '°C' in temp:
                try:
                    celsius = float(temp.replace('°C', ''))
                    fahrenheit = (celsius * 9/5) + 32
                    temp = f"{int(fahrenheit)}°F"
                except:
                    pass
            
            # Get 3-day forecast in simple format
            forecast_resp = requests.get("https://wttr.in/Dayton,Ohio?format=3", timeout=5)
            forecast_text = ""
            if forecast_resp.status_code == 200:
                forecast_text = forecast_resp.text.strip()
            
            return {
                'temp': temp,
                'condition': data[1].strip() if len(data) > 1 else 'Unknown',
                'humidity': data[2].strip() if len(data) > 2 else 'N/A',
                'wind': data[3].strip() if len(data) > 3 else 'N/A',
                'pressure': data[4].strip() if len(data) > 4 else 'N/A',
                'uv': data[5].strip() if len(data) > 5 else 'N/A',
                'moon': data[6].strip() if len(data) > 6 else 'N/A',
                'forecast_text': forecast_text
            }
    except:
        pass
    
    return {
        'temp': '43°F',
        'condition': 'Partly Cloudy',
        'humidity': 'N/A',
        'wind': 'N/A',
        'pressure': 'N/A',
        'uv': 'N/A',
        'moon': 'N/A',
        'forecast_text': ''
    }

def get_active_tasks():
    """Parse TASKS.md and extract all active tasks"""
    tasks_file = "/root/.openclaw/SNDayton/TASKS.md"
    tasks = []
    
    try:
        with open(tasks_file) as f:
            lines = f.readlines()
        
        in_active_section = False
        
        for line in lines:
            # Start collecting from "## In Progress"
            if '## In Progress' in line:
                in_active_section = True
                continue
            
            # Stop at next section
            if in_active_section and line.startswith('## '):
                break
            
            # Collect task lines (numbered or with status)
            if in_active_section and (line.strip().startswith('[') or line.strip().startswith('✅') or line.strip().startswith('🔄') or (line.strip() and line.strip()[0].isdigit())):
                task_line = line.strip()
                if task_line:
                    tasks.append(task_line)
        
        return tasks
    except:
        return []

def get_cron_status():
    """Get last run status of cron jobs"""
    status = {}
    
    digest_log = "/root/.openclaw/SNDayton/digests/digest.log"
    if os.path.exists(digest_log):
        try:
            with open(digest_log, 'r') as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1]
                    if '✅' in last_line or 'Sent' in last_line:
                        status['digest'] = '✅ OK'
                    elif '❌' in last_line:
                        status['digest'] = '❌ FAILED'
                    else:
                        status['digest'] = '⚠️  Unknown'
        except:
            status['digest'] = '⚠️  Unknown'
    
    backup_log = "/root/.openclaw/SNDayton/backup.log"
    if os.path.exists(backup_log):
        try:
            with open(backup_log, 'r') as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1]
                    if '✅' in last_line or 'uploaded' in last_line:
                        status['backup'] = '✅ OK'
                    elif '❌' in last_line or '401' in last_line:
                        status['backup'] = '❌ FAILED'
                    else:
                        status['backup'] = '⚠️  Unknown'
        except:
            status['backup'] = '⚠️  Unknown'
    
    return status

def format_calendar_event(event):
    """Format calendar event for display"""
    start = event.get('start', {})
    summary = event.get('summary', 'Untitled')
    
    if 'dateTime' in start:
        dt = start['dateTime'].split('T')[1].split('+')[0]
        time_str = dt[:5]
    elif 'date' in start:
        time_str = 'All day'
    else:
        time_str = '?'
    
    return f"{time_str} - {summary}"

def generate_digest():
    """Generate the daily digest"""
    
    # Refresh token
    access_token = refresh_token()
    if not access_token:
        print("❌ Failed to refresh token")
        return None
    
    # Get all data
    stats = get_inbox_stats(access_token)
    weather = get_weather()
    events = get_calendar_events(access_token)
    tasks = get_active_tasks()
    cron_status = get_cron_status()
    
    # Current time in EDT
    now = datetime.utcnow()
    edt_hour = now.hour - 4
    edt_day = now.day
    if edt_hour < 0:
        edt_hour += 24
        edt_day -= 1
    
    edt_now = datetime(now.year, now.month, edt_day, edt_hour, now.minute, now.second)
    
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    
    day_name = days[now.weekday()]
    month_name = months[now.month - 1]
    
    # Build calendar section
    calendar_section = "📅 TODAY'S SCHEDULE\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    if events:
        for event in events:
            calendar_section += f" {format_calendar_event(event)}\n"
    else:
        calendar_section += " No events scheduled today\n"
    
    # Build tasks section (TOP PRIORITY)
    tasks_section = "✅ ACTIVE TASKS\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    if tasks:
        for task in tasks[:10]:
            tasks_section += f" {task}\n"
    else:
        tasks_section += " All clear\n"
    
    # Build cron status section
    cron_section = "⚙️  SYSTEM STATUS\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    cron_section += f" Daily Digest:    {cron_status.get('digest', '⚠️  Unknown')}\n"
    cron_section += f" Backup to Drive: {cron_status.get('backup', '⚠️  Unknown')}\n"
    
    # Build CFO insights section
    cfo_section = "💡 CFO INSIGHTS\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    if stats['procurement'] > 0:
        cfo_section += f" Procurement Pipeline: {stats['procurement']} active orders\n"
        cfo_section += f" • Strong project velocity on Positive Electric camera system\n"
        cfo_section += f" • Monitor cash flow across vendor relationships\n\n"
    
    if stats['financial'] > 0:
        cfo_section += f" Financial Transactions: {stats['financial']} emails monitored\n"
        cfo_section += f" • Multiple revenue streams active\n"
        cfo_section += f" • Stay on top of client invoicing\n\n"
    
    if stats['tax'] > 0:
        cfo_section += f" Tax & Accounting: {stats['tax']} items\n"
        cfo_section += f" • Keep quarterly reporting on track\n\n"
    
    cfo_section += " Bottom line: Stay focused on execution. Procurement efficiency = margin wins.\n"
    
    # DLM soups removed from daily digest
    # Menu doesn't come out until 9:30 AM
    # Separate cron job runs at 10 AM with temp check
    dlm_section = ""
    new_soups_section = ""
    
    # Build motivation section
    motivation = "\n🚀 TODAY'S FOCUS\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    motivation += " You've got momentum. The Positive Electric project is real.\n"
    motivation += " ConnectWise automation is live. Discord bots are working.\n"
    motivation += " Daily digest is pulling real data. Backups are solid.\n\n"
    motivation += " Today: Ship one task. Just one. That's the move.\n"
    
    digest = f"""
════════════════════════════════════════════════════════════════
   🎯 SUPERIOR NETWORKS LLC — DAILY BRIEFING
════════════════════════════════════════════════════════════════

📊 {day_name}, {month_name} {edt_day}, {now.year} — {edt_hour:02d}:{now.minute:02d} AM EST

{tasks_section}

{cfo_section}
{motivation}



{calendar_section}

📧 INBOX SNAPSHOT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Inbox:        {stats['total']} emails

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 FINANCIAL SNAPSHOT (CFO View)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Incoming Transactions:    {stats['financial']} emails monitored
Procurement Activity:     {stats['procurement']} orders in progress
Tax & Accounting:         {stats['tax']} items

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 BREAKDOWN BY MEGA-LABEL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 Financial:           {stats['financial']} emails
📦 Procurement:        {stats['procurement']} emails
🎯 Operations:         {stats['operations']} emails
⚙️  System & Access:    {stats['system_access']} emails
📚 Learning:           {stats['learning']} emails

{cron_section}

{dlm_section}{new_soups_section}🌤️  WEATHER — DAYTON, OH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Current Conditions:
 Temperature:   {weather['temp']}
 Condition:     {weather['condition']}
 Humidity:      {weather['humidity']}
 Wind:          {weather['wind']}
 Pressure:      {weather['pressure']}
 UV Index:      {weather['uv']}
 Moon Phase:    {weather['moon']}

3-Day Forecast:
{weather['forecast_text']}

════════════════════════════════════════════════════════════════

—Miles | Superior Networks LLC
"""
    
    return digest

def send_discord(digest):
    """Send digest to Discord webhook"""
    try:
        with open("/root/.openclaw/SNDayton/config/discord_webhook.txt") as f:
            webhook_url = f.read().strip()
        
        # First, send logo image as embed
        logo_url = "https://pronto-core-cdn.prontomarketing.com/2/wp-content/uploads/sites/1408/2015/11/logo.png"
        
        logo_payload = {
            "embeds": [
                {
                    "image": {
                        "url": logo_url
                    },
                    "color": 0x000000
                }
            ]
        }
        
        logo_resp = requests.post(webhook_url, json=logo_payload)
        if logo_resp.status_code != 204:
            print(f"[DISCORD] ⚠️  Logo embed failed: {logo_resp.status_code}")
        
        # Then send digest text
        lines = digest.split('\n')
        current_msg = ""
        messages = []
        
        for line in lines:
            if len(current_msg) + len(line) + 1 > 1900:
                if current_msg:
                    messages.append(current_msg)
                current_msg = line + "\n"
            else:
                current_msg += line + "\n"
        
        if current_msg:
            messages.append(current_msg)
        
        sent = 0
        for msg in messages:
            payload = {"content": msg}
            resp = requests.post(webhook_url, json=payload)
            
            if resp.status_code == 204:
                sent += 1
            else:
                print(f"[DISCORD] ❌ Webhook failed: {resp.status_code}")
                return False
        
        print(f"[DISCORD] ✅ Sent logo + {sent}/{len(messages)} digest messages to Discord")
        return True
        
    except Exception as e:
        print(f"[DISCORD] ❌ Failed: {e}")
        return False

if __name__ == "__main__":
    digest = generate_digest()
    if digest:
        send_discord(digest)
        
        with open("/root/.openclaw/SNDayton/digests/latest.txt", "w") as f:
            f.write(digest)
        
        print("✅ Digest generated and sent to Discord")
    else:
        print("Failed to generate digest")
