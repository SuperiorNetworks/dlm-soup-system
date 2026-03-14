#!/usr/bin/env python3
"""
Name: dlm_settings.py
Version: 1.0.0
Purpose: Build interactive DLM settings page with toggles and natural language
Author: Dwain Henderson Jr. | Superior Networks LLC
Contact: (937) 985-2480 | dhenderson@superiornetworks.biz
Copyright: 2026, Superior Networks LLC
Location: /root/.openclaw/SNDayton/scripts/dlm_settings.py

What This Script Does:
  - Display comprehensive settings dashboard
  - Show all config options with current state
  - Provide natural language toggling (enable/disable locations & soups)
  - Generate Discord embed with interactive instructions
  - Return JSON ready for Discord display

Input:
  - Command: show, toggle [item], adjust [setting]
  - Natural language queries: "show settings", "toggle mason", etc.

Output:
  - Discord embed with settings dashboard
  - Toggle instructions
  - Current state of all preferences

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

class DLMSettings:
    """Interactive DLM settings dashboard"""
    
    def __init__(self):
        self.scraper = DLMSoupScraper()
        self.config = self.scraper.config
        self.all_locations = ['Oakwood', 'Mason', 'Springboro', 'Washington Square', 'Culinary Center', 'Love Cakes']
        self.all_soups = {}
        # Scrape on init to get all soups
        self.scraper.scrape_soups()
        self.all_soups = dict(self.scraper.current_soups)
    
    def build_settings_dashboard(self):
        """Build comprehensive settings page with all soups"""
        enabled_locs = self.config['daily_digest_config']['enabled_locations']
        disabled_locs = [loc for loc in self.all_locations if loc not in enabled_locs]
        favorites = self.config['preferences']['favorite_soups']
        temp_threshold = self.config['daily_digest_config']['temperature_triggers']['high_threshold']
        
        # Scrape all soups
        if not hasattr(self, 'all_soups') or not self.all_soups:
            self.scraper.scrape_soups()
            self.all_soups = {}
            for loc, soups in self.scraper.current_soups.items():
                self.all_soups[loc] = soups
        
        # Build location toggles
        location_section = "**ENABLED LOCATIONS** ✅\n"
        for loc in enabled_locs:
            location_section += f"• {loc}\n"
        
        location_section += "\n**DISABLED LOCATIONS** ❌\n"
        for loc in disabled_locs:
            location_section += f"• {loc}\n"
        
        # Build ALL soups with favorite indicators
        soup_section = "**ALL SOUPS** (⭐ = Your Favorite)\n\n"
        
        for location in self.all_locations:
            if location not in self.all_soups:
                continue
            
            soups = self.all_soups[location]
            soup_section += f"**{location}:**\n"
            
            for soup in soups:
                icon = "⭐" if soup in favorites else "☆"
                soup_section += f"  {icon} {soup}\n"
            
            soup_section += "\n"
        
        # Build temperature section
        temp_section = f"**TEMPERATURE THRESHOLD**\n"
        temp_section += f"Current: {temp_threshold}°F or colder\n"
        temp_section += f"(Soups show in digest when high ≤ {temp_threshold}°F OR dropped 10°F in 24h)\n"
        
        # Build instructions
        instructions = "\n**HOW TO TOGGLE:**\n"
        instructions += "• \"toggle mason\" → Enable/disable location\n"
        instructions += "• \"toggle [soup name]\" → Star/unstar favorite\n"
        instructions += "• \"set temp to 65\" → Change threshold\n"
        instructions += "• \"add springboro\" → Enable location\n"
        instructions += "• \"remove classic chili\" → Remove favorite\n"
        
        content = location_section + "\n" + soup_section + temp_section + instructions
        
        return {
            "content": "🍲 **DLM SOUP OF THE DAY SETTINGS**",
            "embeds": [{
                "title": "Your Preferences Dashboard",
                "description": content,
                "color": 0xF39C12,
                "footer": {"text": "Natural language enabled - toggle any soup to favorite (⭐)"}
            }]
        }
    
    def toggle_location(self, location):
        """Toggle location on/off"""
        location = location.title()
        
        if location not in self.all_locations:
            return {
                "content": f"❌ **{location}** not found.\n\nAvailable locations: {', '.join(self.all_locations)}"
            }
        
        enabled_locs = self.config['daily_digest_config']['enabled_locations']
        
        if location in enabled_locs:
            # Disable
            enabled_locs.remove(location)
            action = "disabled"
            icon = "❌"
        else:
            # Enable
            enabled_locs.append(location)
            action = "enabled"
            icon = "✅"
        
        # Save
        with open('/root/.openclaw/SNDayton/config/dlm_config.json', 'w') as f:
            json.dump(self.config, f, indent=2)
        
        return {
            "content": f"{icon} **{location}** {action}.\n\nEnabled locations: {', '.join(enabled_locs)}"
        }
    
    def toggle_soup(self, soup_name):
        """Toggle soup favorite on/off"""
        favorites = self.config['preferences']['favorite_soups']
        
        # Try exact match first, then case-insensitive
        match = None
        for fav in favorites:
            if fav.lower() == soup_name.lower():
                match = fav
                break
        
        # If no match in favorites, try to find canonical name from all_soups
        canonical_name = soup_name
        if not match and self.all_soups:
            for location, soups in self.all_soups.items():
                for soup in soups:
                    if soup.lower() == soup_name.lower():
                        canonical_name = soup
                        break
        
        if match:
            # Remove
            favorites.remove(match)
            action = "removed"
            icon = "❌"
        else:
            # Add (use canonical name)
            favorites.append(canonical_name)
            action = "added"
            icon = "⭐"
        
        # Save
        with open('/root/.openclaw/SNDayton/config/dlm_config.json', 'w') as f:
            json.dump(self.config, f, indent=2)
        
        count = len(favorites)
        return {
            "content": f"{icon} **{canonical_name}** {action} to favorites.\n\nTotal favorites: {count}"
        }
    
    def adjust_temperature(self, temp_str):
        """Adjust temperature threshold"""
        try:
            temp = int(temp_str)
            if temp < 30 or temp > 90:
                return {
                    "content": f"⚠️ Temperature {temp}°F seems out of range. Use 30-90°F."
                }
            
            self.config['daily_digest_config']['temperature_triggers']['high_threshold'] = temp
            
            # Save
            with open('/root/.openclaw/SNDayton/config/dlm_config.json', 'w') as f:
                json.dump(self.config, f, indent=2)
            
            return {
                "content": f"✅ Temperature threshold set to **{temp}°F or colder**.\n\nDLM soups will show in digest when high ≤ {temp}°F (or dropped 10°F in 24h)."
            }
        except ValueError:
            return {
                "content": f"❌ Invalid temperature: '{temp_str}'. Use a number (30-90)."
            }
    
    def detect_intent(self, text):
        """Detect user intent from natural language"""
        text_lower = text.lower()
        
        # Normalize
        text_lower = text_lower.replace('super', 'soup').replace('dly', 'dlm')
        
        # Intent: Show settings
        if 'show settings' in text_lower or 'what are my settings' in text_lower or 'my config' in text_lower or 'current settings' in text_lower:
            return ('show', None)
        
        # Intent: Toggle location
        for loc in self.all_locations:
            if f'toggle {loc.lower()}' in text_lower or f'enable {loc.lower()}' in text_lower or f'disable {loc.lower()}' in text_lower:
                return ('toggle_location', loc)
        
        # Intent: Toggle soup
        if 'toggle ' in text_lower or 'add ' in text_lower or 'remove ' in text_lower:
            # Extract soup name
            for keyword in ['toggle', 'add', 'remove']:
                if keyword in text_lower:
                    parts = text_lower.split(keyword)
                    if len(parts) > 1:
                        soup_name = parts[1].strip()
                        return ('toggle_soup', soup_name)
        
        # Intent: Change temperature
        if 'temp' in text_lower or 'threshold' in text_lower or 'set temp' in text_lower:
            # Extract temperature
            import re
            temps = re.findall(r'\b(\d{1,2})\b', text_lower)
            if temps:
                return ('adjust_temp', temps[0])
        
        return ('show', None)
    
    def handle_command(self, command, arg=None):
        """Route command to handler"""
        if command == 'show':
            return self.build_settings_dashboard()
        elif command == 'toggle_location':
            return self.toggle_location(arg)
        elif command == 'toggle_soup':
            return self.toggle_soup(arg)
        elif command == 'adjust_temp':
            return self.adjust_temperature(arg)
        else:
            return self.build_settings_dashboard()
    
    def process_natural_language(self, text):
        """Process natural language input"""
        intent, arg = self.detect_intent(text)
        return self.handle_command(intent, arg)

def main():
    if len(sys.argv) < 2:
        # No args - show settings
        settings = DLMSettings()
        result = settings.build_settings_dashboard()
        print(json.dumps(result))
        return
    
    command = sys.argv[1].lower()
    
    settings = DLMSettings()
    
    # Try natural language first
    result = settings.process_natural_language(' '.join(sys.argv[1:]))
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
