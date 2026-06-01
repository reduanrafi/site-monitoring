# Simple Uptime Monitor

Checks your websites every 5 minutes and pings you when one goes down (and
again when it recovers). Runs free on GitHub Actions — no server of your own,
so it stays up even when your sites don't.

## Setup (about 5 minutes)

1. **Make a new GitHub repo** (private is fine). Add two files:
   - `monitor.py` at the root
   - `uptime.yml` at `.github/workflows/uptime.yml`

2. **Edit the `SITES` list** at the top of `monitor.py` with your real URLs —
   your Vercel site, your Plesk API, your cPanel sites, all of them.

3. **Pick a notification channel** and add the matching secrets under
   *repo → Settings → Secrets and variables → Actions → New repository secret*.
   You can set up more than one; you can also start with just Telegram.

   **Telegram (easiest, free, instant):**
   - Message `@BotFather` on Telegram, send `/newbot`, follow the prompts, copy
     the token it gives you.
   - Message your new bot once (say "hi"), then open
     `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` in a browser and find
     your numeric `chat.id`.
   - Add secrets `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`.

   **Discord:** make a channel webhook (Channel settings → Integrations →
   Webhooks) and add it as `DISCORD_WEBHOOK_URL`.

   **Email:** add `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`,
   `SMTP_FROM`, `SMTP_TO`. (For Gmail you'll need an app password, not your
   normal password.)

4. **Test it:** go to the **Actions** tab → *Uptime Monitor* → **Run workflow**.
   The first run just records a baseline. To prove alerts work, add a fake URL
   like `https://this-domain-does-not-exist-12345.com` and run it again.

That's it — from then on it runs itself every 5 minutes.

## Good to know

- GitHub's scheduled runs have a **5-minute minimum** and can occasionally be
  delayed a few minutes when their system is busy. Fine for most sites; if you
  need 1-minute checks, run `monitor.py` from a cron job on a small always-on
  box (or a VPS / Raspberry Pi) instead — the same script works there.
- GitHub **pauses scheduled workflows after ~60 days with no repo activity**.
  Any commit (or a manual run) wakes it back up.
- It only alerts on a **change of state**, so a site that's down for hours gives
  you one "DOWN" message, not one every five minutes — and a "RECOVERED"
  message when it's back.
- It treats any HTTP status under 400 as "up". If a site returns 401/403 by
  design, point it at a public health URL instead, or adjust the check.

## Running locally instead of GitHub Actions

```bash
pip install requests
export TELEGRAM_BOT_TOKEN=...  TELEGRAM_CHAT_ID=...   # or your chosen channel
python monitor.py
```

Then schedule it with cron, e.g. every 5 minutes:

```
*/5 * * * * cd /path/to/monitor && /usr/bin/python3 monitor.py >> log.txt 2>&1
```
