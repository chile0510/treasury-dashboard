# -*- coding: utf-8 -*-
"""
watcher.py — Watch OneDrive Excel file for changes and auto-sync.

Usage:
    python tools/watcher.py

Watches the OneDrive folder. When the Excel file is modified:
1. Waits 5 seconds (debounce for OneDrive sync)
2. Reads Excel → updates treasury_data.py
3. Git commits + pushes → Vercel auto-deploys

Press Ctrl+C to stop.
"""

import os
import sys
import time
import threading
from datetime import datetime

# Add project root to path
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

from tools.sync_excel import parse_excel, write_treasury_data, git_push, EXCEL_DIR, EXCEL_PATH, OUTPUT_FILE

# Debounce timer (seconds) — wait for OneDrive to finish syncing
DEBOUNCE_SECONDS = 5


class ExcelWatcher:
    """Simple file watcher using polling (no external dependencies)."""

    def __init__(self):
        self._last_mtime = 0
        self._timer = None
        self._running = True

    def _get_mtime(self) -> float:
        """Get file modification time."""
        try:
            return os.path.getmtime(EXCEL_PATH)
        except OSError:
            return 0

    def _do_sync(self):
        """Execute the sync process."""
        print(f"\n{'='*60}")
        print(f"[WATCHER] {datetime.now():%H:%M:%S} | Change detected! Syncing...")
        print(f"{'='*60}")

        try:
            data = parse_excel(EXCEL_PATH)

            s = data["summary"]
            print(f"  Loans: {len(data['loans'])} | Invest: {len(data['investments'])}")
            print(f"  Total Loan: {s['totalLoan']/1e9:,.1f} ty | Total Invest: {s['totalInvest']/1e9:,.1f} ty")

            write_treasury_data(data, OUTPUT_FILE)
            git_push(PROJECT_DIR)

            print(f"[WATCHER] Sync complete! Dashboard will update in ~60s")
        except Exception as e:
            print(f"[WATCHER] ERROR: {e}")

        print(f"[WATCHER] Watching for changes... (Ctrl+C to stop)\n")

    def _schedule_sync(self):
        """Schedule a sync with debounce."""
        if self._timer:
            self._timer.cancel()
        self._timer = threading.Timer(DEBOUNCE_SECONDS, self._do_sync)
        self._timer.start()

    def watch(self):
        """Start watching the Excel file for changes."""
        self._last_mtime = self._get_mtime()

        print(f"")
        print(f"  Treasury Dashboard — Excel Watcher")
        print(f"  {'='*40}")
        print(f"  Watching: {EXCEL_PATH}")
        print(f"  Output:   {OUTPUT_FILE}")
        print(f"  Debounce: {DEBOUNCE_SECONDS}s")
        print(f"  {'='*40}")
        print(f"")

        # Initial sync
        if os.path.isfile(EXCEL_PATH):
            print(f"[WATCHER] Running initial sync...")
            self._do_sync()
        else:
            print(f"[WATCHER] WARNING: Excel file not found. Waiting for it to appear...")

        print(f"[WATCHER] Watching for changes... (Ctrl+C to stop)\n")

        try:
            while self._running:
                current_mtime = self._get_mtime()
                if current_mtime > self._last_mtime and current_mtime > 0:
                    self._last_mtime = current_mtime
                    print(f"[WATCHER] {datetime.now():%H:%M:%S} | File modified, scheduling sync...")
                    self._schedule_sync()
                time.sleep(2)  # Poll every 2 seconds
        except KeyboardInterrupt:
            print(f"\n[WATCHER] Stopped by user.")
            if self._timer:
                self._timer.cancel()


def main():
    if not os.path.isdir(EXCEL_DIR):
        print(f"[WATCHER] ERROR: OneDrive folder not found:")
        print(f"  {EXCEL_DIR}")
        print(f"\nMake sure OneDrive is synced and the path is correct.")
        sys.exit(1)

    watcher = ExcelWatcher()
    watcher.watch()


if __name__ == "__main__":
    main()
