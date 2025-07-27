#!/usr/bin/env python3
"""
IPO Status Checker Utility
Checks IPO, FPO, and Right-Share APIs for open status
"""
import requests
import json
import os
import sys
from datetime import datetime

def check_ipo_status():
    """
    Check IPO, FPO, and Right-Share APIs for open status
    This function is called by GitHub Actions to determine if IPOs are available today
    """
    print('🔍 Checking IPO, FPO, and Right-Share APIs...')
    print(f'⏰ Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    # API endpoints to check
    apis = [
        {'name': 'IPO', 'url': 'https://chukul.com/api/ipo/'},
        {'name': 'FPO', 'url': 'https://chukul.com/api/fpo/'},
        {'name': 'Right-Share', 'url': 'https://chukul.com/api/right-share/'}
    ]
    
    any_open = False
    results = []
    
    for api in apis:
        try:
            print(f'📡 Checking {api["name"]} API: {api["url"]}')
            
            response = requests.get(
                api['url'],
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
                timeout=(10, 30)
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f'✅ {api["name"]} API response received')
                
                # Check if response is an array and has items
                if isinstance(data, list) and len(data) > 0:
                    # Check each item for 'status' field
                    for item in data:
                        if isinstance(item, dict) and item.get('status') == 'Open':
                            print(f'🎯 Found OPEN status in {api["name"]} API')
                            any_open = True
                            results.append({
                                'api': api['name'],
                                'status': 'Open',
                                'data': item
                            })
                            break
                    else:
                        print(f'ℹ️ No OPEN status found in {api["name"]} API')
                        results.append({
                            'api': api['name'],
                            'status': 'No Open Items',
                            'data': data[:3] if len(data) > 3 else data  # Show first 3 items
                        })
                else:
                    print(f'⚠️ {api["name"]} API returned empty or invalid data')
                    results.append({
                        'api': api['name'],
                        'status': 'Empty/Invalid Data',
                        'data': data
                    })
            else:
                print(f'❌ {api["name"]} API returned status code: {response.status_code}')
                results.append({
                    'api': api['name'],
                    'status': f'HTTP {response.status_code}',
                    'data': response.text[:200] if response.text else 'No response text'
                })
                
        except requests.exceptions.ConnectionError as e:
            print(f'❌ Connection error for {api["name"]} API: {str(e)}')
            results.append({
                'api': api['name'],
                'status': 'Connection Error',
                'data': str(e)
            })
        except requests.exceptions.Timeout as e:
            print(f'❌ Timeout error for {api["name"]} API: {str(e)}')
            results.append({
                'api': api['name'],
                'status': 'Timeout Error',
                'data': str(e)
            })
        except Exception as e:
            print(f'❌ Unexpected error for {api["name"]} API: {str(e)}')
            results.append({
                'api': api['name'],
                'status': 'Error',
                'data': str(e)
            })
    
    # Set the environment variable
    apply_for_today = 'true' if any_open else 'false'
    
    print(f'\n📊 Summary:')
    print(f'• Any Open Status: {any_open}')
    print(f'• Apply for Today: {apply_for_today}')
    
    print(f'\n📋 Detailed Results:')
    for result in results:
        print(f'• {result["api"]}: {result["status"]}')
    
    # Save results to file
    with open('results.json', 'w') as f:
        json.dump(results, f)
    
    # Set output variables for GitHub Actions
    print(f'\n::set-output name=apply_for_today::{apply_for_today}')
    print(f'::set-output name=any_open::{str(any_open).lower()}')
    
    return apply_for_today, any_open, results

def send_ipo_status_notification():
    """
    Send Telegram notification for IPO status check results
    This function is called by GitHub Actions to send daily status reports
    """
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
    apply_for_today = os.getenv('APPLY_FOR_TODAY', 'false')
    any_open = os.getenv('ANY_OPEN', 'false')
    
    if not telegram_token or not telegram_chat_id:
        print('❌ Telegram credentials not set')
        return
    
    try:
        # Read results from file
        results_data = []
        if os.path.exists('results.json'):
            with open('results.json', 'r') as f:
                results_data = json.load(f)
        
        # Create message
        message = f'📊 Daily IPO Status Check - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n'
        
        if apply_for_today == 'true':
            message += '✅ Apply for Today: TRUE\n'
            message += '🎯 Open IPOs/FPOs/Right-Shares found!\n\n'
        else:
            message += 'ℹ️ Apply for Today: FALSE\n'
            message += '📋 No open IPOs/FPOs/Right-Shares found\n\n'
        
        message += '📋 API Status:\n'
        for result in results_data:
            status_emoji = '✅' if 'Open' in result['status'] else '❌'
            message += f'{status_emoji} {result["api"]}: {result["status"]}\n'
        
        # Send to Telegram
        url = f'https://api.telegram.org/bot{telegram_token}/sendMessage'
        payload = {
            'chat_id': telegram_chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print('✅ Telegram notification sent successfully')
        else:
            print(f'❌ Failed to send Telegram notification: {response.status_code}')
            print(f'Response: {response.text}')
            
    except Exception as e:
        print(f'❌ Error sending Telegram notification: {str(e)}')

if __name__ == "__main__":
    # Check if called with specific arguments for GitHub Actions
    if len(sys.argv) > 1:
        if sys.argv[1] == "check-ipo-status":
            check_ipo_status()
        elif sys.argv[1] == "send-notification":
            send_ipo_status_notification()
        else:
            print(f"Unknown command: {sys.argv[1]}")
            print("Available commands: check-ipo-status, send-notification")
    else:
        # Default to checking IPO status
        check_ipo_status() 