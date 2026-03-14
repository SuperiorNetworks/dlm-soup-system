# DLM Soup System

**Dorothy Lane Market Soup of the Day Automation**

A Python-based automation system that scrapes Dorothy Lane Market's daily soup menu, tracks your favorites, and delivers alerts based on weather conditions.

---

## Features

✅ **Daily Soup Scraping** — Fresh data from all DLM locations every day
✅ **Favorite Soup Tracking** — Mark your preferred soups, get alerts when they're available
✅ **Weather-Triggered Alerts** — Posts soups to Discord when temperature ≤ 65°F
✅ **Multiple Command Formats** — Text commands (`!dlm-check`), slash commands (`/dlm check`), natural language
✅ **Interactive Settings** — Edit preferences from Discord or Google Drive
✅ **Location Management** — Enable/disable locations, track soups across all DLM sites
✅ **Daily Cron Jobs** — Automated scraping and alert delivery

---

## System Architecture

### Daily Schedule

| Time | Task | Details |
|------|------|---------|
| **4:30 AM EDT** | Temperature Check | If ≤ 65°F, posts favorite soups to Discord #general |
| **5:00 AM EDT** | Daily Digest | Sends briefing with tasks, weather, inbox snapshot |
| **9:30 AM** | DLM Menu Updates | New soups appear (external, not automated) |

### Scripts

- **`dlm_soup_scraper.py`** — Scrapes all locations, tracks new soups, manages state
- **`dlm_commands.py`** — Discord command handlers (check, mason, favorites, new, config)
- **`dlm_settings.py`** — Interactive settings dashboard with toggles
- **`dlm_10am_cron.py`** — Temperature-triggered alerts (runs at 4:30 AM EDT)
- **`daily_digest.py`** — Daily briefing with tasks, calendar, weather, inbox stats

### Configuration

**Editable Files:**
- `config/dlm_config.json` — User preferences (locations, soups, temperature threshold)
- `DLM_SETTINGS.md` — Human-readable settings file (sync to Google Drive)

**State Tracking:**
- `state/dlm_all_soups_ever.json` — All soups ever seen (for new soup detection)
- `state/dlm_last_run.json` — Last scrape timestamp

---

## Installation

### Requirements
- Python 3.7+
- `requests` library
- Discord webhook URL (for alerts)
- wttr.in API (free, no key needed)

### Setup

1. **Clone the repo:**
   ```bash
   git clone https://github.com/SuperiorNetworks/dlm-soup-system.git
   cd dlm-soup-system
   ```

2. **Install dependencies:**
   ```bash
   pip install requests
   ```

3. **Configure:**
   - Copy `config/dlm_config.json.example` to `config/dlm_config.json`
   - Edit your favorite locations and soups
   - Add Discord webhook URL to `config/discord_webhook.txt`

4. **Test:**
   ```bash
   python3 scripts/dlm_soup_scraper.py --check
   ```

---

## Usage

### Command Line

**Show current settings:**
```bash
python3 scripts/dlm_settings.py
```

**Check all soups:**
```bash
python3 scripts/dlm_commands.py check
```

**Show your favorites:**
```bash
python3 scripts/dlm_commands.py favorites
```

**Toggle a favorite soup:**
```bash
python3 scripts/dlm_commands.py "toggle classic chili"
```

**Set temperature threshold:**
```bash
python3 scripts/dlm_commands.py config --set-temp-threshold 70
```

### Discord Commands

**Text commands:**
- `!dlm-check` — All soups from all locations
- `!dlm-mason` — Mason location only
- `!dlm-favorites` — Your favorite soups
- `!dlm-new` — New soups never seen before
- `!dlm-settings` — Settings dashboard
- `!dlm-config` — Edit preferences

**Slash commands:**
- `/dlm check` — Same as above, slash format

**Natural language:**
- "What is the DLM soup of the day?" → Shows favorites
- "Toggle mason" → Enable/disable location
- "Set temp to 70" → Change threshold

### Google Drive Settings

Edit `DLM_SETTINGS.md` in Google Drive:
1. Download the file
2. Edit locations, soups, temperature
3. Share updated file with system
4. Changes sync back automatically

---

## Configuration

### `dlm_config.json`

```json
{
  "daily_digest_config": {
    "enabled_locations": ["Oakwood", "Springboro"],
    "temperature_triggers": {
      "high_threshold": 65
    }
  },
  "preferences": {
    "favorite_soups": ["Fisherman's Stew", "New England Clam Chowder"]
  }
}
```

**Options:**
- `enabled_locations` — Which DLM locations to monitor (default: Oakwood, Springboro, Washington Square)
- `high_threshold` — Temperature at or below which soups appear (default: 65°F)
- `favorite_soups` — Your favorite soups (add/remove as needed)

---

## How It Works

### Daily Flow

1. **4:30 AM EDT:** `dlm_10am_cron.py` runs
   - Gets current temperature from wttr.in
   - If ≤ 65°F, runs DLM favorites command
   - Posts result to Discord #general

2. **5:00 AM EDT:** `daily_digest.py` runs
   - Pulls email stats, calendar, weather, tasks
   - Generates briefing
   - Posts to Discord

3. **Anytime:** User runs commands
   - `!dlm-check` triggers `dlm_commands.py`
   - Returns formatted Discord embed with soups

### Soup Scraping

- Scrapes Dorothy Lane Market website daily
- Compares against previous soups (detects new items)
- Stores in JSON state files
- No caching — always fresh data

### Temperature Triggers

Soups show in alerts when:
- Current high ≤ 65°F (editable), OR
- Temperature dropped 10°F in last 24h

---

## Development

### Adding a New Feature

1. Create a script in `scripts/` following naming convention
2. Add header with Name, Version, Purpose, Author, Contact, Copyright
3. Use pure Python (no platform SDK imports)
4. Make it CLI-testable: `python3 script.py --check`
5. Return JSON output for Discord formatting
6. Commit and push:
   ```bash
   git add scripts/new_feature.py
   git commit -m "Add feature description"
   git push origin main
   ```

### Running Tests

```bash
# Test scraper
python3 scripts/dlm_soup_scraper.py --check

# Test commands
python3 scripts/dlm_commands.py favorites
python3 scripts/dlm_commands.py "toggle beef vegetable"

# Test settings
python3 scripts/dlm_settings.py
```

### Logging

Cron job output is logged to:
- `digests/dlm_10am.log` — Temperature checks and alerts
- `digests/digest.log` — Daily digest execution

---

## Locations

Dorothy Lane Market operates at:
- **Oakwood** — Scraper active ✅
- **Mason** — Scraper active ✅
- **Springboro** — Scraper active ✅
- **Washington Square** — Scraper active ✅
- **Culinary Center** — Scraper monitoring
- **Love Cakes** — Scraper monitoring

---

## Troubleshooting

**Webhook not posting?**
- Verify webhook URL is valid and not expired
- Check Discord channel permissions
- Run test: `python3 scripts/dlm_10am_cron.py`

**Soups not showing?**
- Check temperature threshold: `python3 scripts/dlm_settings.py`
- Verify location is enabled
- Check if soups are actually available at enabled locations

**State files corrupted?**
- Delete `state/dlm_all_soups_ever.json` and `state/dlm_last_run.json`
- Next scrape will rebuild them

---

## Contributing

This is a Superior Networks project. For questions or improvements:
- Open an issue on GitHub
- Create a pull request with changes
- Update documentation for new features

---

## License

Internal use by Superior Networks LLC. Not for public redistribution.

---

## Contact

**Superior Networks LLC**
- 📍 703 Jefferson St, Dayton, OH 45342
- 📞 (937) 985-2480
- 🌐 https://github.com/SuperiorNetworks

---

**Last Updated:** March 14, 2026
