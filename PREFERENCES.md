# PREFERENCES.md — Dwain's Build Preferences

## Automation Architecture (CRITICAL)

**DEFAULT APPROACH: Python Scripts + OpenClaw Routing**

All automations are built as **platform-agnostic Python scripts**. OpenClaw handles platform routing (Discord, Teams, Slack, etc.).

**Never build platform-locked bots.** Always write pure Python.

### Script Requirements
- ✅ Accepts inputs via CLI args or function parameters
- ✅ Returns clean data (JSON, dicts, strings)
- ✅ No chat-platform imports (no discord.py, teams SDK, etc.)
- ✅ Testable from command line standalone
- ✅ Can be called from cron, API, or any frontend

### When Building Something New
1. Write pure Python script first
2. Test from CLI: `python3 script.py arg1 arg2`
3. Add OpenClaw routing AFTER script works
4. Platform changes = swap routing config, keep script unchanged

### Current State
- Daily digest: Pure Python ✅
- Backup to Drive: Pure Python ✅
- CW API wrapper: Pure Python ✅
- CW Link generator: Pure Python ✅
- CW Bot (cw_bot.py): Discord-specific ⚠️ (should refactor or retire)

**Decision Made:** 2026-03-14 14:48 UTC — Dwain explicitly chose portable architecture over platform-locked bots.

---

## Python Script Standards (MANDATORY)

### Header Block (REQUIRED)
```python
#!/usr/bin/env python3
"""
Name: script_name.py
Version: 1.0.0
Purpose: [What it does]
Author: Dwain Henderson Jr. | Superior Networks LLC
Contact: (937) 985-2480 | dhenderson@superiornetworks.biz
Copyright: 2026, Superior Networks LLC
Location: /root/.openclaw/SNDayton/scripts/script_name.py

What This Script Does:
  - [Bullets]

Input:
  - [Config/data sources]

Output:
  - [What it produces]

Dependencies:
  - [All imports]

Change Log:
  2026-03-14 v1.0.0 - Initial release (Dwain Henderson Jr)
"""
```

### Naming
- ✅ snake_case for files/functions/vars
- ❌ NOT camelCase
- ✅ Descriptive names

### Structure
- Class-based (not functional)
- Private methods prefixed with `_`
- `run(args=None)` as main entry point
- CLI testable with `--flag` support

### Configuration
- Location: `/root/.openclaw/SNDayton/config/[script]_config.json`
- User-editable, JSON format
- Auto-create with defaults on first run

### State Tracking
- Location: `/root/.openclaw/SNDayton/state/[script]_state.json`
- Auto-maintained
- Tracks historical data

### Output
- ✅ Clean JSON (no platform formatting)
- ✅ Print to stdout
- ✅ Let OpenClaw/frontend format for chat

### Version & Git
- Semantic versioning (v1.0.0)
- ALL scripts committed to git
- Author: Dwain Henderson Jr (dhenderson@superiornetworks.biz)
- Commit format: `Add [script] v1.0.0 - [description]`

### Must-Have Features
- [ ] No platform dependencies (no discord.py, teams SDK)
- [ ] Error handling (try/except)
- [ ] CLI testable (`python3 script.py --check`)
- [ ] JSON output
- [ ] Fresh data (no caching for daily tasks)
- [ ] ISO timestamp format - How I Should Work

## Units & Display

- **Temperature:** Fahrenheit (°F)
- **Speed:** Miles per hour (mph)
- **Distance:** Miles

## Decision Making

- **Auto-tracking:** ❌ Ask first before logging to memory/files
  - Even if answer is "no," keep asking
  - Don't assume permission
  - Exceptions: direct requests only

- **Silent replies:** Use only when there's genuinely nothing to say
  - Prefer actual responses

## Data & Memory

- **Storage:** Local only (for now)
  - `/root/.openclaw/SNDayton/` is source of truth
  - Memory files: text-based (.md)
  - No cloud sync (yet)

- **Organization:** Topic-based structure
  ```
  memory/
  ├── clients/
  ├── integrations/
  ├── projects/
  └── daily/
  ```

- **Backup strategy:** Manual backup for now
  - When ready: plan cloud backup (Google Drive, etc.)
  - Always warn before major changes

## Communication Style

- Direct and capable (no filler like "Great question!")
- Skip the corporate drone voice
- Keep it casual but professional
- Use F° and mph without asking each time
- **ALL LINKS MUST BE CLICKABLE** — format as [Link Text](URL), not bare URLs
  - Exception: If you explicitly ask for a bare URL

## Decision Numbering Scheme

**Format:** `Q[question#]-O[option#]`

**Usage:**
- When I ask multiple questions with options, each question gets `Q1`, `Q2`, etc.
- Each option gets `O1`, `O2`, `O3`, etc.
- You respond with: `Q1-O2, Q2-O1` (Question 1 Option 2, Question 2 Option 1)

**Example:**
```
Q1: Gmail Labels?
  O1: Add "Vendors" label
  O2: Consolidate to 5 mega-labels
  O3: Keep current 6

Q2: Digest time?
  O1: 6:00 AM EDT
  O2: 7:00 AM EDT
```

**Your response:** `Q1-O1, Q2-O2`

**Why:** Fast, unambiguous, scalable — I know exactly what to execute.

## API & Integration Notes

- **ConnectWise timezone:** EDT (UTC-4)
  - Formula: Ohio time + 4 hours = UTC for API calls
  - Always convert when scheduling
  
- **OAuth:** Ask for credentials when needed, store securely
- **API keys:** Keep in TOOLS.md (encrypted/protected, not in code)

## Google Workspace Integration

**Currently Using:**
- ✅ Gmail (primary email)
- ✅ Calendar (scheduling)
- ✅ Drive (file storage)

**Integration Status:**
- Gmail: Not yet configured (email copilot prompt saved, ready for API setup)
- Calendar: Not yet configured (could use for appointment checks, reminders)
- Drive: Not yet configured (could use for memory backup/sync)

**Future Setup:**
- When ready: Set up Google Oauth for Gmail drafts + Calendar access
- Memory backup: Sync to Drive periodically
- Appointment reminders: Pull from Calendar during heartbeats

## Reminders

- You're a guest with access to Dwain's systems — respect that
- Ask before any external actions (emails, posts, API writes)
- Document decisions and changes
- Update these files as preferences evolve
