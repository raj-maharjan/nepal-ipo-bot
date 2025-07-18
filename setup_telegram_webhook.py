#!/usr/bin/env python3
"""
Telegram Bot Webhook Setup Script

This script helps you set up the webhook for your Telegram bot.
Run this script after deploying your application to set the webhook URL.
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_webhook():
    """Set up the Telegram bot webhook"""
    
    # Get bot token from environment
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found in environment variables")
        print("Please add TELEGRAM_BOT_TOKEN to your .env file")
        return False
    
    # Get webhook URL from user
    webhook_url = input("Enter your webhook URL (e.g., https://your-domain.com/webhook): ").strip()
    
    if not webhook_url:
        print("❌ Webhook URL is required")
        return False
    
    if not webhook_url.startswith('https://'):
        print("❌ Webhook URL must use HTTPS")
        return False
    
    # Set webhook
    webhook_api_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    payload = {
        "url": webhook_url,
        "allowed_updates": ["message"]
    }
    
    try:
        print(f"🔗 Setting webhook to: {webhook_url}")
        response = requests.post(webhook_api_url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ Webhook set successfully!")
                print(f"📊 Webhook info: {result.get('result')}")
                return True
            else:
                print(f"❌ Failed to set webhook: {result.get('description')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error setting webhook: {str(e)}")
        return False

def get_webhook_info():
    """Get current webhook information"""
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found in environment variables")
        return False
    
    try:
        webhook_api_url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
        response = requests.get(webhook_api_url)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                webhook_info = result.get('result', {})
                print("📊 Current webhook info:")
                print(f"URL: {webhook_info.get('url', 'Not set')}")
                print(f"Has custom certificate: {webhook_info.get('has_custom_certificate', False)}")
                print(f"Pending update count: {webhook_info.get('pending_update_count', 0)}")
                print(f"Last error date: {webhook_info.get('last_error_date')}")
                print(f"Last error message: {webhook_info.get('last_error_message')}")
                return True
            else:
                print(f"❌ Failed to get webhook info: {result.get('description')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting webhook info: {str(e)}")
        return False

def delete_webhook():
    """Delete the current webhook"""
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found in environment variables")
        return False
    
    try:
        webhook_api_url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
        response = requests.post(webhook_api_url)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ Webhook deleted successfully!")
                return True
            else:
                print(f"❌ Failed to delete webhook: {result.get('description')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error deleting webhook: {str(e)}")
        return False

def main():
    """Main function"""
    print("🤖 Telegram Bot Webhook Setup")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Set webhook")
        print("2. Get webhook info")
        print("3. Delete webhook")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            setup_webhook()
        elif choice == '2':
            get_webhook_info()
        elif choice == '3':
            delete_webhook()
        elif choice == '4':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-4.")

if __name__ == "__main__":
    main() 