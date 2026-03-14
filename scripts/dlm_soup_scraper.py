#!/usr/bin/env python3
"""
Name: dlm_soup_scraper.py
Version: 1.0.0
Purpose: Scrape Dorothy Lane Market soup of the day, filter by preferences, track new soups
Author: Dwain Henderson Jr. | Superior Networks LLC
Contact: (937) 985-2480 | dhenderson@superiornetworks.biz
Copyright: 2026, Superior Networks LLC
Location: /root/.openclaw/SNDayton/scripts/dlm_soup_scraper.py

What This Script Does:
  - Scrapes current soups from Dorothy Lane Market website (all locations)
  - Tracks all soups ever seen in dlm_all_soups_ever.json
  - Identifies NEW soups (never seen before)
  - Filters favorite soups by enabled locations
  - Applies temperature thresholds:
    * High is 70°F or colder (<=)
    * OR High dropped 10°F in last 24h
  - Returns JSON for digest integration
  - Supports CLI commands for manual testing

Input:
  - dlm_config.json (location preferences, favorite soups, temp thresholds)
  - Current weather data (high temp, 24h change)
  - dlm_all_soups_ever.json (historical tracking)

Output:
  - JSON with: new_soups, daily_digest_section, background_alerts
  - State file updates: dlm_all_soups_ever.json, dlm_last_run.json

Dependencies:
  - requests (HTTP scraping)
  - json (built-in)
  - os (built-in)
  - sys (built-in)
  - datetime (built-in)

Change Log:
  2026-03-14 v1.0.0 - Initial release (Dwain Henderson Jr)
"""

import json
import requests
import re
import os
import sys
from datetime import datetime, timedelta

# Configuration
CONFIG_FILE = "/root/.openclaw/SNDayton/config/dlm_config.json"
STATE_FILE = "/root/.openclaw/SNDayton/state/dlm_all_soups_ever.json"
LAST_RUN_FILE = "/root/.openclaw/SNDayton/state/dlm_last_run.json"
DLM_URL = "https://www.dorothylane.com/soup-of-the-day/"

class DLMSoupScraper:
    """Dorothy Lane Market soup scraper with preferences and state tracking"""
    
    def __init__(self):
        self.config = self._load_config()
        self.state = self._load_state()
        self.last_run = self._load_last_run()
        self.current_soups = {}
        
    def _load_config(self):
        """Load user configuration"""
        try:
            if not os.path.exists(CONFIG_FILE):
                self._create_default_config()
            
            with open(CONFIG_FILE) as f:
                return json.load(f)
        except Exception as e:
            print(f"ERROR: Failed to load config: {e}")
            sys.exit(1)
    
    def _create_default_config(self):
        """Create default configuration file"""
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        
        default_config = {
            "daily_digest_config": {
                "dlm_soups_enabled": True,
                "temperature_triggers": {
                    "high_threshold": 70,
                    "high_comparison": "<=",
                    "change_24h_threshold": 10,
                    "change_24h_description": "If high dropped 10°F in last 24h"
                },
                "enabled_locations": ["Oakwood", "Springboro", "Washington Square"],
                "include_mason_daily": False,
                "description": "Show DLM soups if EITHER threshold is met"
            },
            "preferences": {
                "favorite_soups": [
                    "Seafood Chowder",
                    "Fisherman's Stew",
                    "New England Clam Chowder",
                    "Oyster Stew",
                    "Broccoli Chicken Bacon Soup"
                ],
                "background_alerts": {
                    "new_soups_all_locations": True,
                    "new_soups_at_mason_special": True,
                    "batch_at_5am_digest": True,
                    "note_on_9_30am_update": "DLM updates soups at 9:30 AM. Check back then."
                }
            }
        }
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default_config, f, indent=2)
    
    def _load_state(self):
        """Load historical soup tracking"""
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE) as f:
                    return json.load(f)
            except Exception as e:
                print(f"WARNING: Failed to load state: {e}")
        
        return {"all_seen_soups": {}}
    
    def _load_last_run(self):
        """Load last run details"""
        if os.path.exists(LAST_RUN_FILE):
            try:
                with open(LAST_RUN_FILE) as f:
                    return json.load(f)
            except:
                pass
        
        return {"last_run": None, "soups": {}}
    
    def _save_state(self):
        """Save historical soup tracking"""
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def _save_last_run(self):
        """Save last run state"""
        os.makedirs(os.path.dirname(LAST_RUN_FILE), exist_ok=True)
        self.last_run["last_run"] = datetime.now().isoformat()
        self.last_run["soups"] = self.current_soups
        
        with open(LAST_RUN_FILE, 'w') as f:
            json.dump(self.last_run, f, indent=2)
    
    def scrape_soups(self):
        """Scrape current soups from DLM website"""
        try:
            resp = requests.get(DLM_URL, timeout=10)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"ERROR: Failed to fetch DLM website: {e}")
            return False
        
        html = resp.text
        
        # Find all h1 location headers
        h1_pattern = r'<h1[^>]*?>\s*([^<]+?)\s*</h1>'
        h1_matches = list(re.finditer(h1_pattern, html))
        
        locations = ['Oakwood', 'Mason', 'Springboro', 'Washington Square', 'Culinary Center', 'Love Cakes']
        
        for i, location in enumerate(locations):
            # Find h1 for this location
            h1_search = rf'<h1[^>]*>\s*{location}\s*</h1>'
            h1_match = re.search(h1_search, html)
            
            if not h1_match:
                continue
            
            # Get content until next h1
            start_pos = h1_match.end()
            next_h1_match = re.search(r'<h1[^>]*>', html[start_pos:])
            end_pos = start_pos + next_h1_match.start() if next_h1_match else len(html)
            section = html[start_pos:end_pos]
            
            # Extract all li items
            soup_matches = re.findall(r'<li[^>]*>\s*([^<]+?)\s*(?:<strong|</li>)', section)
            
            # Clean soup names
            soups = []
            seen = set()
            for soup in soup_matches:
                soup = soup.strip()
                soup = re.sub(r'\s+(GF|VG|V)\s*$', '', soup)
                if soup and len(soup) > 2 and soup not in seen:
                    soups.append(soup)
                    seen.add(soup)
            
            if soups:
                self.current_soups[location] = soups
        
        return True
    
    def detect_new_soups(self):
        """Detect soups never seen before"""
        new_soups = []
        
        for location, soups in self.current_soups.items():
            for soup in soups:
                if soup not in self.state['all_seen_soups']:
                    new_soups.append({
                        "soup": soup,
                        "location": location,
                        "first_seen": datetime.now().isoformat()
                    })
                    
                    # Add to state
                    self.state['all_seen_soups'][soup] = datetime.now().isoformat()
        
        return new_soups
    
    def check_temperature_thresholds(self, current_high, change_24h):
        """Check if temperature triggers DLM soups in digest"""
        config = self.config['daily_digest_config']['temperature_triggers']
        
        high_threshold = config['high_threshold']
        change_threshold = config['change_24h_threshold']
        
        # Check high threshold
        if current_high <= high_threshold:
            return True, f"high <= {high_threshold}°F"
        
        # Check change threshold
        if change_24h <= -change_threshold:
            return True, f"temp dropped {abs(change_24h)}°F (>= {change_threshold}°F)"
        
        return False, None
    
    def get_favorites_for_digest(self, temp_triggered):
        """Get favorite soups at enabled locations (if temp triggers)"""
        if not temp_triggered:
            return []
        
        config = self.config['daily_digest_config']
        favorites = self.config['preferences']['favorite_soups']
        enabled_locs = config['enabled_locations']
        
        matches = []
        
        for location in enabled_locs:
            if location not in self.current_soups:
                continue
            
            for soup in self.current_soups[location]:
                if soup in favorites:
                    matches.append({
                        "soup": soup,
                        "location": location
                    })
        
        return matches
    
    def generate_output(self, current_high=None, change_24h=None):
        """Generate JSON output for digest integration"""
        
        # Check temperature triggers
        temp_triggered = False
        trigger_reason = None
        
        if current_high is not None and change_24h is not None:
            temp_triggered, trigger_reason = self.check_temperature_thresholds(current_high, change_24h)
        
        # Get new soups
        new_soups = self.detect_new_soups()
        
        # Get favorites if temp triggers
        favorites = self.get_favorites_for_digest(temp_triggered)
        
        output = {
            "timestamp": datetime.now().isoformat(),
            "temperature_check": {
                "current_high": current_high,
                "change_24h": change_24h,
                "triggered": temp_triggered,
                "reason": trigger_reason
            },
            "daily_digest_soups": {
                "should_include": temp_triggered,
                "note_if_triggered": "DLM updates soups at 9:30 AM. Check back then for full menu.",
                "your_favorites": favorites,
                "locations_included": self.config['daily_digest_config']['enabled_locations'] if temp_triggered else []
            },
            "new_soups_alert": {
                "new_soups_found": new_soups,
                "includes_all_locations": True,
                "all_current_soups": self.current_soups
            }
        }
        
        return output
    
    def run(self, args=None):
        """Main execution"""
        
        # Parse arguments
        if args and '--check' in args:
            # Manual check - just show current state
            pass
        elif args and '--config' in args:
            # Show config
            print(json.dumps(self.config, indent=2))
            return
        elif args and '--set-temp-threshold' in args:
            # Update temp threshold
            idx = args.index('--set-temp-threshold')
            if idx + 1 < len(args):
                new_threshold = int(args[idx + 1])
                self.config['daily_digest_config']['temperature_triggers']['high_threshold'] = new_threshold
                with open(CONFIG_FILE, 'w') as f:
                    json.dump(self.config, f, indent=2)
                print(f"Temperature threshold updated to {new_threshold}°F")
            return
        
        # Scrape
        if not self.scrape_soups():
            return False
        
        # Generate output (without temp data for CLI testing)
        output = self.generate_output()
        
        # Save state
        self._save_state()
        self._save_last_run()
        
        # Print output
        print(json.dumps(output, indent=2))
        
        return True

def main():
    scraper = DLMSoupScraper()
    scraper.run(sys.argv[1:])

if __name__ == "__main__":
    main()
