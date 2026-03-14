#!/usr/bin/env python3
"""
Name: dlm_commands.py
Version: 1.0.0
Purpose: OpenClaw command handler for DLM soup queries via Discord
Author: Dwain Henderson Jr. | Superior Networks LLC
Contact: (937) 985-2480 | dhenderson@superiornetworks.biz
Copyright: 2026, Superior Networks LLC
Location: /root/.openclaw/SNDayton/scripts/dlm_commands.py

What This Script Does:
  - Handles Discord commands: !dlm-check, !dlm-mason, !dlm-favorites
  - Calls dlm_soup_scraper and formats output for Discord
  - Returns Discord-friendly JSON with embeds and emoji
  - Pure Python, platform-agnostic (works with any chat platform via OpenClaw)

Input:
  - Command name and arguments from Discord
  - dlm_config.json (preferences)
  - dlm_all_soups_ever.json (history)

Output:
  - JSON with Discord embed formatting
  - Content + embeds for clean display

Dependencies:
  - dlm_soup_scraper
  - json (built-in)
  - sys (built-in)

Change Log:
  2026-03-14 v1.0.0 - Initial release (Dwain Henderson Jr)
"""

import json
import sys
import os

sys.path.insert(0, '/root/.openclaw/SNDayton/scripts')
from dlm_soup_scraper import DLMSoupScraper

class DLMCommandHandler:
    """Handle Discord commands for DLM soups"""
    
    def __init__(self):
        self.scraper = DLMSoupScraper()
    
    def format_discord_message(self, title, content_dict, color=0xFF6B35):
        """Format output for Discord embed"""
        return {
            "embeds": [{
                "title": title,
                "description": self._build_description(content_dict),
                "color": color,
                "fields": self._build_fields(content_dict)
            }]
        }
    
    def _build_description(self, data):
        """Build embed description"""
        if isinstance(data, dict) and 'description' in data:
            return data['description']
        return ""
    
    def _build_fields(self, data):
        """Build embed fields"""
        fields = []
        if isinstance(data, dict):
            for key, value in data.items():
                if key != 'description' and not isinstance(value, (dict, list)):
                    fields.append({
                        "name": key,
                        "value": str(value),
                        "inline": False
                    })
        return fields
    
    def handle_check(self):
        """!dlm-check - Show all current soups"""
        if not self.scraper.scrape_soups():
            return {
                "content": "❌ Failed to scrape DLM website. Try again later."
            }
        
        result = {
            "content": "🍲 **DOROTHY LANE MARKET - ALL SOUPS** (All Locations)\n\n",
            "embeds": []
        }
        
        locations = ['Oakwood', 'Mason', 'Springboro', 'Washington Square', 'Culinary Center', 'Love Cakes']
        
        for location in locations:
            if location not in self.scraper.current_soups:
                continue
            
            soups = self.scraper.current_soups[location]
            soup_list = "\n".join([f"• {soup}" for soup in soups])
            
            result["embeds"].append({
                "title": f"📍 {location}",
                "description": soup_list,
                "color": 0xFF6B35
            })
        
        return result
    
    def handle_mason(self):
        """!dlm-mason - Show Mason soups only"""
        if not self.scraper.scrape_soups():
            return {
                "content": "❌ Failed to scrape DLM website. Try again later."
            }
        
        if 'Mason' not in self.scraper.current_soups:
            return {
                "content": "⚠️ Mason location not found."
            }
        
        soups = self.scraper.current_soups['Mason']
        favorites = self.scraper.config['preferences']['favorite_soups']
        
        soup_lines = []
        for soup in soups:
            marker = "⭐" if soup in favorites else "•"
            soup_lines.append(f"{marker} {soup}")
        
        soup_list = "\n".join(soup_lines)
        
        return {
            "content": "🍲 **MASON LOCATION** (⭐ = Your Favorite)",
            "embeds": [{
                "title": "📍 Mason",
                "description": soup_list,
                "color": 0xFF6B35,
                "footer": {"text": "⭐ = Your favorites"}
            }]
        }
    
    def handle_favorites(self):
        """!dlm-favorites - Show your favorite soups across all locations"""
        if not self.scraper.scrape_soups():
            return {
                "content": "❌ Failed to scrape DLM website. Try again later."
            }
        
        favorites = self.scraper.config['preferences']['favorite_soups']
        
        matches = []
        for location, soups in self.scraper.current_soups.items():
            for soup in soups:
                if soup in favorites:
                    matches.append(f"• {soup} → **{location}**")
        
        if not matches:
            return {
                "content": "❌ None of your favorite soups are available today."
            }
        
        return {
            "content": "⭐ **YOUR FAVORITE SOUPS** (All Locations)",
            "embeds": [{
                "title": "Your Favorites Available",
                "description": "\n".join(matches),
                "color": 0x2ECC71
            }]
        }
    
    def handle_new(self):
        """!dlm-new - Show new soups never seen before"""
        if not self.scraper.scrape_soups():
            return {
                "content": "❌ Failed to scrape DLM website. Try again later."
            }
        
        new_soups = self.scraper.detect_new_soups()
        
        if not new_soups:
            return {
                "content": "✅ No new soups today. Same old menu."
            }
        
        new_lines = []
        for soup in new_soups:
            new_lines.append(f"🆕 {soup['soup']} → **{soup['location']}**")
        
        return {
            "content": f"🚨 **{len(new_soups)} NEW SOUPS DETECTED**",
            "embeds": [{
                "title": "Fresh Soup Discoveries",
                "description": "\n".join(new_lines),
                "color": 0xE74C3C
            }]
        }
    
    def handle_config_show(self):
        """Show config menu for editing preferences"""
        config = self.scraper.config
        
        locations = config['daily_digest_config']['enabled_locations']
        soups = config['preferences']['favorite_soups']
        temp_threshold = config['daily_digest_config']['temperature_triggers']['high_threshold']
        
        content = "⚙️ **DLM PREFERENCES CONFIG**\n\n"
        content += f"**Enabled Locations:** {', '.join(locations)}\n\n"
        content += f"**Favorite Soups:** {', '.join(soups[:3])}...\n\n"
        content += f"**Temp Threshold:** {temp_threshold}°F or colder\n\n"
        content += "**Edit with:**\n"
        content += "• `!dlm-config --add-location [name]`\n"
        content += "• `!dlm-config --remove-location [name]`\n"
        content += "• `!dlm-config --add-soup [name]`\n"
        content += "• `!dlm-config --remove-soup [name]`\n"
        content += "• `!dlm-config --set-temp-threshold [temp]`\n"
        
        return {"content": content}
    
    def handle_config_edit(self, args):
        """Edit config preferences"""
        if not args or len(args) < 2:
            return self.handle_config_show()
        
        action = args[0]
        value = ' '.join(args[1:])
        
        config = self.scraper.config
        
        if action == '--add-location':
            if value not in config['daily_digest_config']['enabled_locations']:
                config['daily_digest_config']['enabled_locations'].append(value)
                self.scraper._save_state()
                return {
                    "content": f"✅ Added **{value}** to enabled locations.\n\n**New locations:** {', '.join(config['daily_digest_config']['enabled_locations'])}"
                }
            else:
                return {"content": f"⚠️ **{value}** already in enabled locations."}
        
        elif action == '--remove-location':
            if value in config['daily_digest_config']['enabled_locations']:
                config['daily_digest_config']['enabled_locations'].remove(value)
                with open('/root/.openclaw/SNDayton/config/dlm_config.json', 'w') as f:
                    json.dump(config, f, indent=2)
                return {
                    "content": f"✅ Removed **{value}** from enabled locations.\n\n**Remaining locations:** {', '.join(config['daily_digest_config']['enabled_locations'])}"
                }
            else:
                return {"content": f"⚠️ **{value}** not found in enabled locations."}
        
        elif action == '--add-soup':
            if value not in config['preferences']['favorite_soups']:
                config['preferences']['favorite_soups'].append(value)
                with open('/root/.openclaw/SNDayton/config/dlm_config.json', 'w') as f:
                    json.dump(config, f, indent=2)
                return {
                    "content": f"✅ Added **{value}** to favorites.\n\nTotal favorites: {len(config['preferences']['favorite_soups'])}"
                }
            else:
                return {"content": f"⚠️ **{value}** already in favorites."}
        
        elif action == '--remove-soup':
            if value in config['preferences']['favorite_soups']:
                config['preferences']['favorite_soups'].remove(value)
                with open('/root/.openclaw/SNDayton/config/dlm_config.json', 'w') as f:
                    json.dump(config, f, indent=2)
                return {
                    "content": f"✅ Removed **{value}** from favorites.\n\nRemaining: {len(config['preferences']['favorite_soups'])} soups"
                }
            else:
                return {"content": f"⚠️ **{value}** not found in favorites."}
        
        elif action == '--set-temp-threshold':
            try:
                temp = int(value)
                config['daily_digest_config']['temperature_triggers']['high_threshold'] = temp
                with open('/root/.openclaw/SNDayton/config/dlm_config.json', 'w') as f:
                    json.dump(config, f, indent=2)
                return {
                    "content": f"✅ Temperature threshold set to **{temp}°F or colder**.\n\nDLM soups will show in digest when high ≤ {temp}°F."
                }
            except ValueError:
                return {"content": f"❌ Invalid temperature. Use a number (e.g., 65)"}
        
        return {"content": "❌ Unknown config action."}
    
    def handle_command(self, command, args=None):
        """Route command to handler"""
        if command == 'check' or command == 'all':
            return self.handle_check()
        elif command == 'mason':
            return self.handle_mason()
        elif command == 'favorites':
            return self.handle_favorites()
        elif command == 'new':
            return self.handle_new()
        elif command == 'config':
            if args:
                return self.handle_config_edit(args)
            else:
                return self.handle_config_show()
        else:
            return {
                "content": "❌ Unknown command.\n\n**Available commands:**\n• `!dlm-check` - All soups (all locations)\n• `!dlm-mason` - Mason only (⭐ = favorites)\n• `!dlm-favorites` - Your favorites across all locations (natural language: \"what is the DLM soup of the day?\")\n• `!dlm-new` - New soups never seen before\n• `!dlm-config` - Edit preferences (locations, soups, temp threshold)"
            }

def detect_natural_language(text):
    """Detect natural language triggers and map to commands"""
    text_lower = text.lower()
    
    # Check for natural language phrases
    if 'what is the dlm soup of the day' in text_lower or 'what are your favorite soups' in text_lower:
        return 'favorites'
    elif 'mason soup' in text_lower or 'mason location' in text_lower:
        return 'mason'
    elif 'new soup' in text_lower:
        return 'new'
    elif 'dlm soup' in text_lower or 'dorothy lane' in text_lower:
        return 'check'
    
    return None

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"content": "No command provided"}))
        sys.exit(1)
    
    full_input = ' '.join(sys.argv[1:]).lower()
    
    # Try natural language detection first
    nl_command = detect_natural_language(full_input)
    if nl_command:
        handler = DLMCommandHandler()
        result = handler.handle_command(nl_command)
        print(json.dumps(result))
        return
    
    # Parse text/slash commands
    command = sys.argv[1].lower().replace('!dlm-', '').replace('--', '').replace('/dlm ', '')
    
    # Handle config editing (may have additional args)
    if command == 'config' and len(sys.argv) > 2:
        config_args = sys.argv[2:]
        handler = DLMCommandHandler()
        result = handler.handle_command('config', config_args)
        print(json.dumps(result))
        return
    
    handler = DLMCommandHandler()
    result = handler.handle_command(command)
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
