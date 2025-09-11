#!/usr/bin/env python3
"""
Feature Toggle Helper for Resonance Scanner v13.3 Enhanced
This script helps enable/disable optional features easily
"""

import json
import re
import sys
from pathlib import Path

class FeatureToggler:
    def __init__(self):
        self.scanner_file = Path("resonance_scannerv13_3_ws.py")
        self.config_file = Path("envelope.json")
        
    def toggle_sqlite(self, enable=True):
        """Toggle SQLite storage feature"""
        print(f"{'Enabling' if enable else 'Disabling'} SQLite storage...")
        
        # Update configuration
        config = self.load_config()
        if "STORAGE" not in config:
            config["STORAGE"] = {}
        if "SQLITE" not in config["STORAGE"]:
            config["STORAGE"]["SQLITE"] = {}
        
        config["STORAGE"]["SQLITE"]["ENABLED"] = enable
        if enable and "DB_PATH" not in config["STORAGE"]["SQLITE"]:
            config["STORAGE"]["SQLITE"]["DB_PATH"] = "./data/db/scanner.db"
        
        self.save_config(config)
        
        # Toggle code comments
        if enable:
            self.uncomment_feature("sqlite")
        else:
            self.comment_feature("sqlite")
        
        print(f"✓ SQLite storage {'enabled' if enable else 'disabled'}")
    
    def toggle_telegram(self, enable=True, token=None, chat_id=None):
        """Toggle Telegram alerts feature"""
        print(f"{'Enabling' if enable else 'Disabling'} Telegram alerts...")
        
        # Update configuration
        config = self.load_config()
        if "ALERTS" not in config:
            config["ALERTS"] = {}
        if "TELEGRAM" not in config["ALERTS"]:
            config["ALERTS"]["TELEGRAM"] = {}
        
        config["ALERTS"]["TELEGRAM"]["ENABLED"] = enable
        if enable:
            if token:
                config["ALERTS"]["TELEGRAM"]["TOKEN"] = token
            if chat_id:
                config["ALERTS"]["TELEGRAM"]["CHAT_ID"] = chat_id
        
        self.save_config(config)
        
        # Toggle code comments
        if enable:
            self.uncomment_feature("telegram")
        else:
            self.comment_feature("telegram")
        
        print(f"✓ Telegram alerts {'enabled' if enable else 'disabled'}")
    
    def uncomment_feature(self, feature):
        """Uncomment feature-specific code blocks"""
        if not self.scanner_file.exists():
            print(f"Warning: {self.scanner_file} not found")
            return
        
        content = self.scanner_file.read_text()
        
        if feature == "sqlite":
            # Uncomment SQLite imports
            content = re.sub(r'^# (import sqlite3)$', r'\1', content, flags=re.MULTILINE)
            
            # Uncomment SQLite configuration
            content = re.sub(r'^# (SQLITE_ENABLED = .+)$', r'\1', content, flags=re.MULTILINE)
            content = re.sub(r'^# (SQLITE_DB_PATH = .+)$', r'\1', content, flags=re.MULTILINE)
            
            # Uncomment SQLite functions (multi-line)
            content = re.sub(
                r'^# def init_sqlite_db\(\):(.+?)^# def',
                lambda m: m.group(0).replace('# ', ''),
                content,
                flags=re.MULTILINE | re.DOTALL
            )
            content = re.sub(
                r'^# def save_to_sqlite\(.+?\):(.+?)^# def',
                lambda m: m.group(0).replace('# ', ''),
                content,
                flags=re.MULTILINE | re.DOTALL
            )
            
            # Uncomment SQLite calls
            content = re.sub(r'^#     (.*sqlite.*)', r'    \1', content, flags=re.MULTILINE)
        
        elif feature == "telegram":
            # Uncomment Telegram configuration
            content = re.sub(r'^# (TELEGRAM_ENABLED = .+)$', r'\1', content, flags=re.MULTILINE)
            content = re.sub(r'^# (TELEGRAM_TOKEN = .+)$', r'\1', content, flags=re.MULTILINE)
            content = re.sub(r'^# (TELEGRAM_CHAT_ID = .+)$', r'\1', content, flags=re.MULTILINE)
            
            # Uncomment Telegram functions
            content = re.sub(
                r'^# def send_telegram_alert\(.+?\):(.+?)^# def',
                lambda m: m.group(0).replace('# ', ''),
                content,
                flags=re.MULTILINE | re.DOTALL
            )
            content = re.sub(
                r'^# def format_telegram_message\(.+?\):(.+?)^# def',
                lambda m: m.group(0).replace('# ', ''),
                content,
                flags=re.MULTILINE | re.DOTALL
            )
            
            # Uncomment Telegram calls
            content = re.sub(r'^#     (.*telegram.*)', r'    \1', content, flags=re.MULTILINE)
        
        self.scanner_file.write_text(content)
    
    def comment_feature(self, feature):
        """Comment out feature-specific code blocks"""
        if not self.scanner_file.exists():
            print(f"Warning: {self.scanner_file} not found")
            return
        
        content = self.scanner_file.read_text()
        
        if feature == "sqlite":
            # Comment SQLite imports
            content = re.sub(r'^(import sqlite3)$', r'# \1', content, flags=re.MULTILINE)
            
            # Comment SQLite configuration
            content = re.sub(r'^(SQLITE_ENABLED = .+)$', r'# \1', content, flags=re.MULTILINE)
            content = re.sub(r'^(SQLITE_DB_PATH = .+)$', r'# \1', content, flags=re.MULTILINE)
        
        elif feature == "telegram":
            # Comment Telegram configuration
            content = re.sub(r'^(TELEGRAM_ENABLED = .+)$', r'# \1', content, flags=re.MULTILINE)
            content = re.sub(r'^(TELEGRAM_TOKEN = .+)$', r'# \1', content, flags=re.MULTILINE)
            content = re.sub(r'^(TELEGRAM_CHAT_ID = .+)$', r'# \1', content, flags=re.MULTILINE)
        
        self.scanner_file.write_text(content)
    
    def load_config(self):
        """Load configuration from envelope.json"""
        if self.config_file.exists():
            return json.loads(self.config_file.read_text())
        return {}
    
    def save_config(self, config):
        """Save configuration to envelope.json"""
        self.config_file.write_text(json.dumps(config, indent=2))
    
    def status(self):
        """Show current feature status"""
        config = self.load_config()
        
        print("\n=== Feature Status ===")
        
        # SQLite status
        sqlite_enabled = config.get("STORAGE", {}).get("SQLITE", {}).get("ENABLED", False)
        sqlite_path = config.get("STORAGE", {}).get("SQLITE", {}).get("DB_PATH", "Not configured")
        print(f"SQLite Storage: {'✓ Enabled' if sqlite_enabled else '✗ Disabled'}")
        if sqlite_enabled:
            print(f"  Database: {sqlite_path}")
        
        # Telegram status
        telegram_enabled = config.get("ALERTS", {}).get("TELEGRAM", {}).get("ENABLED", False)
        telegram_token = config.get("ALERTS", {}).get("TELEGRAM", {}).get("TOKEN", "")
        telegram_chat = config.get("ALERTS", {}).get("TELEGRAM", {}).get("CHAT_ID", "")
        print(f"Telegram Alerts: {'✓ Enabled' if telegram_enabled else '✗ Disabled'}")
        if telegram_enabled:
            print(f"  Token: {'✓ Configured' if telegram_token and telegram_token != 'YOUR_TELEGRAM_BOT_TOKEN' else '✗ Not configured'}")
            print(f"  Chat ID: {'✓ Configured' if telegram_chat and telegram_chat != 'YOUR_TELEGRAM_CHAT_ID' else '✗ Not configured'}")
        
        # Discord status
        discord_enabled = config.get("SCANNER", {}).get("DISCORD", {}).get("ENABLED", True)
        discord_webhook = config.get("SCANNER", {}).get("DISCORD", {}).get("WEBHOOK_URL", "")
        print(f"Discord Alerts: {'✓ Enabled' if discord_enabled else '✗ Disabled'}")
        if discord_enabled:
            print(f"  Webhook: {'✓ Configured' if discord_webhook and discord_webhook != 'YOUR_DISCORD_WEBHOOK_URL_HERE' else '✗ Not configured'}")
        
        print()

def main():
    toggler = FeatureToggler()
    
    if len(sys.argv) < 2:
        print("Resonance Scanner Feature Toggle Helper")
        print("Usage:")
        print("  python feature_toggle.py status                      - Show feature status")
        print("  python feature_toggle.py enable-sqlite               - Enable SQLite storage")
        print("  python feature_toggle.py disable-sqlite              - Disable SQLite storage")
        print("  python feature_toggle.py enable-telegram TOKEN CHAT  - Enable Telegram alerts")
        print("  python feature_toggle.py disable-telegram            - Disable Telegram alerts")
        print("  python feature_toggle.py enable-all                  - Enable all features")
        print("  python feature_toggle.py disable-all                 - Disable all features")
        toggler.status()
        return
    
    command = sys.argv[1].lower()
    
    if command == "status":
        toggler.status()
    
    elif command == "enable-sqlite":
        toggler.toggle_sqlite(True)
        toggler.status()
    
    elif command == "disable-sqlite":
        toggler.toggle_sqlite(False)
        toggler.status()
    
    elif command == "enable-telegram":
        if len(sys.argv) < 4:
            print("Error: Please provide TOKEN and CHAT_ID")
            print("Usage: python feature_toggle.py enable-telegram YOUR_TOKEN YOUR_CHAT_ID")
            return
        toggler.toggle_telegram(True, sys.argv[2], sys.argv[3])
        toggler.status()
    
    elif command == "disable-telegram":
        toggler.toggle_telegram(False)
        toggler.status()
    
    elif command == "enable-all":
        print("Enabling all optional features...")
        toggler.toggle_sqlite(True)
        toggler.toggle_telegram(True)
        print("\nNote: Remember to configure Telegram credentials in envelope.json")
        toggler.status()
    
    elif command == "disable-all":
        print("Disabling all optional features...")
        toggler.toggle_sqlite(False)
        toggler.toggle_telegram(False)
        toggler.status()
    
    else:
        print(f"Unknown command: {command}")
        print("Run without arguments to see usage")

if __name__ == "__main__":
    main()
