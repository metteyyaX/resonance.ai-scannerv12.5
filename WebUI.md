# Resonance.ai WebUI Setup Guide

This guide will help you set up the professional web dashboard for your Resonance.ai Breakout Scanner, enabling real-time monitoring, configuration management, and alert testing through a modern browser interface.

## 📋 Prerequisites

- Python 3.7+
- Your existing `resonance_scanner_v12_5.py` file
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Network access (for external alerts)

## 🚀 Quick Start Installation

### Step 1: Install Required Dependencies

```bash
pip install flask flask-socketio python-socketio eventlet
```

### Step 2: Create Project Structure

Create the following directory structure:
```
resonance-webui/
├── resonance_scanner_v12_5.py    # Your existing scanner
├── app.py                        # Flask backend server
├── templates/
│   └── index.html               # WebUI dashboard
└── static/                      # (optional for additional assets)
```

### Step 3: Create the Flask Backend (app.py)

Save the Flask backend code (from the artifacts above) as `app.py` in your project directory.

### Step 4: Create Templates Directory

```bash
mkdir templates
```

Save the WebUI HTML code as `templates/index.html`.

### Step 5: Integrate with Your Scanner

Add these imports to the top of your `resonance_scanner_v12_5.py`:

```python
import socketio
import threading
from flask import Flask
import json
from datetime import datetime, timezone
```

Then add the WebUI integration code (from the integration artifacts) to your scanner file.

### Step 6: Update Your Main Execution

Replace your existing main execution block:

```python
# Replace this:
if __name__ == "__main__":
    print("\n--- Resonance.ai Breakout Scanner Activated ---")
    while True:
        # ... your existing loop

# With this:
if __name__ == "__main__":
    run_with_webui_integration()
```

## 🏃‍♂️ Running the System

### Method 1: Integrated Launch (Recommended)

```bash
python resonance_scanner_v12_5.py
```

This will automatically:
- Start the WebUI server on `http://localhost:5000`
- Begin the breakout scanner
- Enable real-time communication between scanner and WebUI

### Method 2: Separate Launch

Terminal 1 (Backend Server):
```bash
python app.py
```

Terminal 2 (Scanner):
```bash
python resonance_scanner_v12_5.py
```

## 🌐 Accessing the Dashboard

1. **Open your web browser**
2. **Navigate to**: `http://localhost:5000`
3. **For network access**: Use `http://YOUR_IP:5000`

## 📱 WebUI Features Overview

### 🎛️ Main Dashboard

- **Live Statistics**: Real-time scanning metrics and performance data
- **Scanner Status**: Start/stop controls with visual indicators  
- **Uptime Counter**: Tracks how long the system has been running
- **Breakout Counter**: Total alerts generated today

### 📊 Live Scan Feed

- **Real-time Results**: See every coin scan as it happens
- **Color-coded Changes**: Green for positive, red for negative price movements
- **Timestamp Tracking**: Precise timing for each scan
- **Auto-scrolling**: Latest results always visible

### ⚙️ Configuration Panel

**Basic Controls:**
- Scanner on/off toggle
- Scan interval adjustment (1-60 seconds)
- Volume floor configuration
- Alert mode selection (Simple/Pro)

**Advanced Settings:**
- Breakout thresholds (Fast/Medium/Slow)
- Volume spike ratios
- Alert service configuration
- Real-time settings application

### 🚨 Alert Management

**Discord Integration:**
- Webhook URL configuration
- Test alert functionality
- Real-time alert delivery

**Telegram Integration:**
- Bot token configuration
- Chat ID setup
- Test message sending

**Alert History:**
- Recent breakout alerts display
- Detailed breakdown information
- Clear/filter options

### 📈 Performance Monitoring

- **Scan Rate**: Coins processed per second
- **Memory Usage**: System resource tracking
- **Network Status**: Connection health monitoring
- **Error Tracking**: Failed scans and alerts

## 🔧 Advanced Configuration

### Environment Variables

Create a `.env` file for production deployment:

```bash
# Scanner Settings
SCAN_INTERVAL=2
VOLUME_FLOOR=2000
ALERT_MODE=simple

# Flask Settings  
FLASK_ENV=production
SECRET_KEY=your-production-secret-key

# Alert Services
DISCORD_WEBHOOK=https://discord.com/api/webhooks/...
TELEGRAM_BOT_TOKEN=123456789:ABCDEF...
TELEGRAM_CHAT_ID=123456789

# Server Settings
HOST=0.0.0.0
PORT=5000
```

### Custom Styling

The WebUI uses CSS custom properties for easy theming:

```css
:root {
    --primary: #6366f1;        /* Main accent color */
    --success: #10b981;        /* Success/profit color */
    --danger: #ef4444;         /* Alert/loss color */
    --dark: #1f2937;          /* Background color */
    /* Modify these in the HTML <style> section */
}
```

### Database Integration (Optional)

For persistent data storage, add SQLite integration:

```python
import sqlite3

def init_database():
    conn = sqlite3.connect('resonance.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY,
            symbol TEXT,
            price REAL,
            change_percent REAL,
            timestamp DATETIME,
            bands TEXT
        )
    ''')
    conn.commit()
    conn.close()
```

## 🔐 Security Considerations

### Production Deployment

1. **Change the secret key**: Update `app.config['SECRET_KEY']`
2. **Use environment variables**: Store sensitive data securely
3. **Enable HTTPS**: Use SSL certificates for encrypted communication
4. **Firewall rules**: Restrict access to authorized IPs only
5. **Regular updates**: Keep dependencies current

### API Key Protection

```python
# Use environment variables for sensitive data
import os
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK')
```

## 🚨 Troubleshooting

### Common Issues

**WebUI won't load:**
- Check if port 5000 is available
- Verify Flask server is running
- Check browser console for JavaScript errors

**Scanner not connecting:**
- Ensure both scanner and WebUI are running
- Check firewall settings
- Verify socketio connections in browser dev tools

**Alerts not sending:**
- Test webhook/bot token configuration
- Check network connectivity
- Verify alert service credentials

**Performance issues:**
- Reduce scan interval if system is overloaded
- Monitor memory usage in WebUI
- Check for network latency issues

### Debug Mode

Enable detailed logging:

```python
# In app.py
app.config['DEBUG'] = True
socketio.run(app, debug=True, log_output=True)
```

### Log Analysis

Monitor console output for:
- Scanner errors and exceptions
- WebSocket connection status
- API response codes
- Performance metrics

## 🌟 Advanced Features

### Keyboard Shortcuts

- **Ctrl + Space**: Toggle scanner on/off
- **Ctrl + S**: Save current settings
- **Ctrl + R**: Reset settings to defaults

### Mobile Responsiveness

The WebUI is fully responsive and works on:
- Desktop computers
- Tablets 
- Mobile phones
- Different screen orientations

### Data Export

**Settings Export:**
- Download configuration as JSON
- Import/export scanner profiles
- Backup and restore capabilities

**Alert History:**
- Export breakout data to CSV
- Historical analysis tools
- Performance reporting

## 🔄 Updates and Maintenance

### Updating the WebUI

1. **Backup your settings**: Export configuration first
2. **Update files**: Replace HTML/CSS/JavaScript code
3. **Restart services**: Restart Flask server and scanner
4. **Test functionality**: Verify all features work correctly

### Version Control

Track changes with Git:

```bash
git init
git add .
git commit -m "Initial WebUI setup"
```

### Monitoring

**Health Checks:**
- Scanner uptime monitoring
- WebUI response time tracking
- Alert delivery confirmation
- Error rate monitoring

## 🎯 Performance Optimization

### Resource Management

**Memory Usage:**
- Monitor Python process memory
- Clear old scan data periodically
- Optimize data structures

**CPU Usage:**
- Adjust scan intervals based on system load
- Use efficient data processing
- Monitor thread usage

**Network Optimization:**
- Cache API responses where possible
- Minimize WebSocket message frequency
- Compress large data transfers

### Scaling Considerations

**Multiple Instances:**
- Load balance across multiple scanners
- Centralized alert management
- Distributed configuration management

**Cloud Deployment:**
- Use Docker containers
- Deploy to AWS/GCP/Azure
- Implement auto-scaling

## 📞 Support and Resources

### Documentation Links

- **Flask Documentation**: https://flask.palletsprojects.com/
- **SocketIO Documentation**: https://python-socketio.readthedocs.io/
- **Coinbase API Reference**: https://docs.cloud.coinbase.com/

### Community Resources

- **GitHub Issues**: Report bugs and feature requests
- **Discord Community**: Get help from other users
- **Video Tutorials**: Step-by-step setup guides

### Professional Services

For custom development or enterprise deployment:
- Custom feature development
- Cloud infrastructure setup
- 24/7 monitoring and support
- Training and onboarding

---

## 🎉 Congratulations!

You now have a professional-grade web dashboard for your Resonance.ai Breakout Scanner! The WebUI provides real-time monitoring, easy configuration management, and comprehensive alert testing capabilities.

**Next Steps:**
1. Configure your Discord and Telegram alerts
2. Customize the thresholds for your trading strategy  
3. Monitor the performance and adjust settings as needed
4. Set up automated backups of your configuration

**Happy Trading!** 📈🚀
