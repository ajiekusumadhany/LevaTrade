"""
Notification System - File-based communication between bot and dashboard
"""
import json
import os
import time
from datetime import datetime
from typing import Dict, Any

NOTIFICATION_FILE = "notifications.json"

def send_notification(notification_type: str, data: Dict[str, Any]):
    """Send notification by writing to file"""
    try:
        notification = {
            'type': notification_type,
            'data': data,
            'timestamp': datetime.now().isoformat(),
            'id': int(time.time() * 1000)  # Unique ID based on timestamp
        }
        
        # Read existing notifications
        notifications = []
        if os.path.exists(NOTIFICATION_FILE):
            try:
                with open(NOTIFICATION_FILE, 'r') as f:
                    notifications = json.load(f)
            except:
                notifications = []
        
        # Add new notification
        notifications.append(notification)
        
        # Keep only last 50 notifications to prevent file from growing too large
        notifications = notifications[-50:]
        
        # Write back to file
        with open(NOTIFICATION_FILE, 'w') as f:
            json.dump(notifications, f)
            
        print(f"📡 Notification sent: {notification_type} for {data.get('symbol', 'unknown')}")
        
    except Exception as e:
        print(f"⚠️ Failed to send notification: {e}")

def get_new_notifications(last_id: int = 0) -> list:
    """Get notifications newer than last_id"""
    try:
        if not os.path.exists(NOTIFICATION_FILE):
            return []
            
        with open(NOTIFICATION_FILE, 'r') as f:
            notifications = json.load(f)
            
        # Return notifications with ID greater than last_id
        new_notifications = [n for n in notifications if n['id'] > last_id]
        return new_notifications
        
    except Exception as e:
        print(f"⚠️ Failed to read notifications: {e}")
        return []

def clear_old_notifications():
    """Clear notifications older than 1 hour"""
    try:
        if not os.path.exists(NOTIFICATION_FILE):
            return
            
        with open(NOTIFICATION_FILE, 'r') as f:
            notifications = json.load(f)
            
        # Keep only notifications from last hour
        current_time = time.time()
        one_hour_ago = current_time - 3600
        
        filtered_notifications = []
        for notification in notifications:
            notification_time = notification['id'] / 1000  # Convert back to timestamp
            if notification_time > one_hour_ago:
                filtered_notifications.append(notification)
        
        # Write back filtered notifications
        with open(NOTIFICATION_FILE, 'w') as f:
            json.dump(filtered_notifications, f)
            
    except Exception as e:
        print(f"⚠️ Failed to clear old notifications: {e}")