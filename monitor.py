#!/usr/bin/env python3
"""
Simple uptime monitor.

Checks a list of URLs and sends an alert ONLY when a site changes state
(goes down, or comes back up) — so you don't get spammed every 5 minutes
while a site is down.

Works on GitHub Actions (recommended), a cron job, or your laptop.
Notifications go to whichever channel(s) you configure via environment
variables: Telegram, Discord, and/or email. Configure none and it just
prints to the log.
"""

import json
import os
import smtplib
import time
from email.mime.text import MIMEText
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# 1. YOUR SITES — edit this list. Use a real health/status URL where you have
#    one (e.g. your API), otherwise just the homepage is fine.
# ---------------------------------------------------------------------------
SITES = [
    "https://www.wetopianmarket.com.bd/",
    "https://api.wetopianmarket.com.bd",
    "http://luxbeyond.com.bd/",
    "http://luxbeyond.store/",
    "https://ettabashop.com/",
]

TIMEOUT = 30          # seconds to wait before calling a site "down"
RETRIES = 2           # extra attempts before declaring down (rides out blips)
RETRY_DELAY = 3       # seconds between attempts

STATE_FILE = Path("status.json")


def is_up(url):
    """Return (up: bool, detail: str). Treats any HTTP < 400 as up."""
    detail = ""
    for attempt in range(RETRIES + 1):
        try:
            r = requests.get(
                url,
                timeout=TIMEOUT,
                allow_redirects=True,
                headers={"User-Agent": "uptime-monitor"},
            )
            if r.status_code < 400:
                return True, f"HTTP {r.status_code}"
            detail = f"HTTP {r.status_code}"
        except requests.RequestException as e:
            detail = type(e).__name__
        if attempt < RETRIES:
            time.sleep(RETRY_DELAY)
    return False, detail


def notify(subject, body):
    """Send an alert to every channel that is configured via env vars."""
    # --- Telegram ---
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat = os.getenv("TELEGRAM_CHAT_ID")
    if token and chat:
        try:
            requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat, "text": f"{subject}\n{body}"},
                timeout=15,
            )
        except requests.RequestException as e:
            print("Telegram send failed:", e)

    # --- Discord ---
    hook = os.getenv("DISCORD_WEBHOOK_URL")
    if hook:
        try:
            requests.post(hook, json={"content": f"**{subject}**\n{body}"}, timeout=15)
        except requests.RequestException as e:
            print("Discord send failed:", e)

    # --- Email (SMTP) ---
    host = os.getenv("SMTP_HOST")
    if host:
        try:
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = os.getenv("SMTP_FROM", os.getenv("SMTP_USER", ""))
            msg["To"] = os.getenv("SMTP_TO", "")
            with smtplib.SMTP(host, int(os.getenv("SMTP_PORT", "587"))) as s:
                s.starttls()
                s.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"))
                s.send_message(msg)
        except Exception as e:
            print("Email send failed:", e)


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def main():
    old = load_state()
    new = {}

    for url in SITES:
        up, detail = is_up(url)
        new[url] = "up" if up else "down"
        prev = old.get(url)
        print(f"{url}: {new[url]} ({detail})")

        # Alert when a site goes down (and isn't already known-down),
        # and again when it recovers.
        if new[url] == "down" and prev != "down":
            notify("🔴 DOWN", f"{url} is DOWN ({detail})")
        elif new[url] == "up" and prev == "down":
            notify("🟢 RECOVERED", f"{url} is back UP ({detail})")

    STATE_FILE.write_text(json.dumps(new, indent=2))


if __name__ == "__main__":
    main()
