# Flask Backend for Resonance.ai WebUI Integration
# This file integrates with your existing resonance_scanner_v12_5.py

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import threading
import time
import json
import os
from datetime import datetime, timezone
import queue
import requests

# Import your existing scanner functions
# from resonance_scanner_v12_5 import *

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables for scanner state
scanner_running = True
scanner_settings = {
    'scan_interval': 2,
    'volume_floor': 2000,
    'alert_mode': 'simple',
    'fast_threshold': 0.013,
    'medium_threshold': 0.018,
    'slow_threshold': 0.024,
    'fast_ratio': 1.3,
    'medium_ratio': 1.7,
    'slow_ratio': 2.2,
    'discord_webhook': '',
    'telegram_token': '',
    'telegram_chat_id': ''
}

# Statistics tracking
stats = {
    'total_scanned': 0,
    'total_alerts': 0,
    'breakouts_today': 0,
    'start_time': datetime.now(timezone.utc),
    'scan_rate': 0,
    'avg_volume': 0,
    'top_gainer': '--'
}

# Queue for real-time updates
update_queue = queue.Queue()

@app.route('/')
def index():
    """Serve the main dashboard"""
    return render_template('index.html')

@app.route('/api/settings', methods=['GET', 'POST'])
def handle_settings():
    """Handle settings GET/POST requests"""
    global scanner_settings
    
    if request.method == 'POST':
        data = request.get_json()
        scanner_settings.update(data)
        
        # Apply settings to the scanner
        apply_scanner_settings(scanner_settings)
        
        return jsonify({'status': 'success', 'message': 'Settings updated'})
    
    return jsonify(scanner_settings)

@app.route('/api/stats')
def get_stats():
    """Get current statistics"""
    current_stats = stats.copy()
    current_stats['uptime'] = str(datetime.now(timezone.utc) - stats['start_time']).split('.')[0]
    return jsonify(current_stats)

@app.route('/api/scanner/toggle', methods=['POST'])
def toggle_scanner():
    """Toggle scanner on/off"""
    global scanner_running
    scanner_running = not scanner_running
    
    status = 'running' if scanner_running else 'stopped'
    socketio.emit('scanner_status', {'status': status, 'running': scanner_running})
    
    return jsonify({'status': status, 'running': scanner_running})

@app.route('/api/test-alert', methods=['POST'])
def test_alert():
    """Test Discord/Telegram alerts"""
    data = request.get_json()
    alert_type = data.get('type', 'discord')
    
    test_message = "🧪 **TEST ALERT** 🧪\n**System**: Resonance.ai WebUI\n**Status**: Alert system working correctly"
    
    try:
        if alert_type == 'discord' and scanner_settings['discord_webhook']:
            response = requests.post(
                scanner_settings['discord_webhook'],
                json={'content': test_message},
                timeout=10
            )
            if response.status_code == 204:
                return jsonify({'status': 'success', 'message': 'Discord test alert sent!'})
            else:
                return jsonify({'status': 'error', 'message': f'Discord error: {response.status_code}'})
                
        elif alert_type == 'telegram' and scanner_settings['telegram_token'] and scanner_settings['telegram_chat_id']:
            url = f"https://api.telegram.org/bot{scanner_settings['telegram_token']}/sendMessage"
            response = requests.post(
                url,
                json={
                    'chat_id': scanner_settings['telegram_chat_id'],
                    'text': test_message,
                    'parse_mode': 'Markdown'
                },
                timeout=10
            )
            if response.status_code == 200:
                return jsonify({'status': 'success', 'message': 'Telegram test alert sent!'})
            else:
                return jsonify({'status': 'error', 'message': f'Telegram error: {response.status_code}'})
        else:
            return jsonify({'status': 'error', 'message': 'Alert service not configured'})
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    print('Client connected')
    # Send current stats to newly connected client
    emit('stats_update', get_stats().data)
    emit('scanner_status', {'status': 'running' if scanner_running else 'stopped', 'running': scanner_running})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    print('Client disconnected')

def apply_scanner_settings(settings):
    """Apply settings to the scanner"""
    # This function would update your scanner's configuration
    # You would modify your original scanner code to read from these settings
    print(f"Applied settings: {settings}")

def scanner_worker():
    """Modified version of your scanner main loop"""
    global stats, scanner_running
    
    # Import your existing functions here
    # from resonance_scanner_v12_5 import get_candles, is_breakout_band, etc.
    
    # This is a simplified version - integrate with your actual scanner code
    coins = ['BTC-USD', 'ETH-USD', 'ADA-USD', 'SOL-USD', 'AVAX-USD', 'LINK-USD']  # Subset for demo
    
    while True:
        if not scanner_running:
            time.sleep(1)
            continue
            
        try:
            for pair in coins:
                if not scanner_running:
                    break
                    
                # Your existing scanning logic would go here
                # candles = get_candles(pair)
                # ... rest of your breakout detection logic
                
                # For demo purposes, simulate scanning
                stats['total_scanned'] += 1
                
                # Emit scan result to WebUI
                scan_data = {
                    'type': 'scan_result',
                    'symbol': pair,
                    'change': (hash(pair) % 1000 - 500) / 100,  # Demo data
                    'band_width': (hash(pair) % 500) / 100,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                socketio.emit('scan_update', scan_data)
                
                # Simulate occasional breakout alerts
                if hash(pair + str(int(time.time()))) % 100 < 5:  # 5% chance
                    alert_data = {
                        'type': 'breakout_alert',
                        'symbol': pair,
                        'change': abs(scan_data['change']),
                        'band_width': scan_data['band_width'],
                        'bands': ['FAST', 'MEDIUM'],
                        'price': 50000.12345,
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }
                    socketio.emit('breakout_alert', alert_data)
                    stats['total_alerts'] += 1
                    stats['breakouts_today'] += 1
                
                time.sleep(0.1)  # Small delay between coins
                
        except Exception as e:
            print(f"Scanner error: {e}")
            
        # Wait between scan cycles
        time.sleep(scanner_settings['scan_interval'])

def stats_updater():
    """Update statistics periodically"""
    global stats
    
    while True:
        # Update stats
        stats['scan_rate'] = stats['total_scanned'] / max(1, (datetime.now(timezone.utc) - stats['start_time']).seconds)
        stats['avg_volume'] = 25000 + (hash(str(time.time())) % 50000)  # Demo data
        
        gainers = ['BTC-USD +3.2%', 'ETH-USD +2.8%', 'SOL-USD +4.1%', 'AVAX-USD +2.3%']
        stats['top_gainer'] = gainers[int(time.time()) % len(gainers)]
        
        # Emit to all connected clients
        socketio.emit('stats_update', stats)
        
        time.sleep(5)  # Update every 5 seconds

if __name__ == '__main__':
    # Start background threads
    scanner_thread = threading.Thread(target=scanner_worker, daemon=True)
    stats_thread = threading.Thread(target=stats_updater, daemon=True)
    
    scanner_thread.start()
    stats_thread.start()
    
    print("🚀 Starting Resonance.ai WebUI Server...")
    print("📊 Dashboard available at: http://localhost:5000")
    
    # Run the Flask-SocketIO server
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
