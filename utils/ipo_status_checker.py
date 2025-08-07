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
    
    # API endpoints to check - ShareSansar API with different type_ids
    apis = [
        {'name': 'IPO', 'type_id': 1},
        {'name': 'FPO', 'type_id': 2},
        {'name': 'Right-Share', 'type_id': 3}
    ]
    
    results = []
    
    for api in apis:
        try:
            print(f'📡 Checking {api["name"]} API (type_id: {api["type_id"]})')
            
            # ShareSansar API URL with type_id parameter
            url = f'https://www.sharesansar.com/existing-issues?draw=1&columns%5B0%5D%5Bdata%5D=DT_Row_Index&columns%5B0%5D%5Bname%5D=&columns%5B0%5D%5Bsearchable%5D=false&columns%5B0%5D%5Borderable%5D=false&columns%5B0%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B0%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B1%5D%5Bdata%5D=company.symbol&columns%5B1%5D%5Bname%5D=&columns%5B1%5D%5Bsearchable%5D=true&columns%5B1%5D%5Borderable%5D=false&columns%5B1%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B1%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B2%5D%5Bdata%5D=company.companyname&columns%5B2%5D%5Bname%5D=&columns%5B2%5D%5Bsearchable%5D=true&columns%5B2%5D%5Borderable%5D=false&columns%5B2%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B2%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B3%5D%5Bdata%5D=ratio_value&columns%5B3%5D%5Bname%5D=&columns%5B3%5D%5Bsearchable%5D=false&columns%5B3%5D%5Borderable%5D=false&columns%5B3%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B3%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B4%5D%5Bdata%5D=total_units&columns%5B4%5D%5Bname%5D=&columns%5B4%5D%5Bsearchable%5D=false&columns%5B4%5D%5Borderable%5D=false&columns%5B4%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B4%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B5%5D%5Bdata%5D=issue_price&columns%5B5%5D%5Bname%5D=&columns%5B5%5D%5Bsearchable%5D=false&columns%5B5%5D%5Borderable%5D=false&columns%5B5%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B5%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B6%5D%5Bdata%5D=price_range&columns%5B6%5D%5Bname%5D=&columns%5B6%5D%5Bsearchable%5D=false&columns%5B6%5D%5Borderable%5D=false&columns%5B6%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B6%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B7%5D%5Bdata%5D=cutoff_price&columns%5B7%5D%5Bname%5D=&columns%5B7%5D%5Bsearchable%5D=false&columns%5B7%5D%5Borderable%5D=false&columns%5B7%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B7%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B8%5D%5Bdata%5D=opening_date&columns%5B8%5D%5Bname%5D=&columns%5B8%5D%5Bsearchable%5D=true&columns%5B8%5D%5Borderable%5D=false&columns%5B8%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B8%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B9%5D%5Bdata%5D=closing_date&columns%5B9%5D%5Bname%5D=&columns%5B9%5D%5Bsearchable%5D=true&columns%5B9%5D%5Borderable%5D=false&columns%5B9%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B9%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B10%5D%5Bdata%5D=final_date&columns%5B10%5D%5Bname%5D=&columns%5B10%5D%5Bsearchable%5D=true&columns%5B10%5D%5Borderable%5D=false&columns%5B10%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B10%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B11%5D%5Bdata%5D=listing_date&columns%5B11%5D%5Bname%5D=&columns%5B11%5D%5Bsearchable%5D=true&columns%5B11%5D%5Borderable%5D=false&columns%5B11%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B11%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B12%5D%5Bdata%5D=issue_manager&columns%5B12%5D%5Bname%5D=&columns%5B12%5D%5Bsearchable%5D=false&columns%5B12%5D%5Borderable%5D=false&columns%5B12%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B12%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B13%5D%5Bdata%5D=status&columns%5B13%5D%5Bname%5D=&columns%5B13%5D%5Bsearchable%5D=false&columns%5B13%5D%5Borderable%5D=false&columns%5B13%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B13%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B14%5D%5Bdata%5D=view&columns%5B14%5D%5Bname%5D=&columns%5B14%5D%5Bsearchable%5D=false&columns%5B14%5D%5Borderable%5D=false&columns%5B14%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B14%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B15%5D%5Bdata%5D=right_eligibility_link&columns%5B15%5D%5Bname%5D=&columns%5B15%5D%5Bsearchable%5D=false&columns%5B15%5D%5Borderable%5D=false&columns%5B15%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B15%5D%5Bsearch%5D%5Bregex%5D=false&start=0&length=20&search%5Bvalue%5D=&search%5Bregex%5D=false&type={api["type_id"]}&_=1754586778076'
            
            # Headers matching the curl request
            headers = {
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'accept-language': 'en-US,en;q=0.9,es;q=0.8,hi;q=0.7,ne;q=0.6',
                'priority': 'u=1, i',
                'referer': 'https://www.sharesansar.com/existing-issues',
                'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
                'x-requested-with': 'XMLHttpRequest'
            }
            
            response = requests.get(
                url,
                headers=headers,
                timeout=(10, 30)
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f'✅ {api["name"]} API response received')
                
                # Check if response has 'data' field and it's an array with items
                if isinstance(data, dict) and 'data' in data and isinstance(data['data'], list) and len(data['data']) > 0:
                    # Check each item for 'status' field (status = 0 means eligible/open)
                    for item in data['data']:
                        if isinstance(item, dict) and item.get('status') == 0:
                            print(f'🎯 Found OPEN status in {api["name"]} API')
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
                            'data': data['data'][:3] if len(data['data']) > 3 else data['data']  # Show first 3 items
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
    apply_for_today = 'true' if any(result['status'] == 'Open' for result in results) else 'false'
    
    print(f'\n📊 Summary:')
    print(f'• Apply for Today: {apply_for_today}')
    
    print(f'\n📋 Detailed Results:')
    for result in results:
        print(f'• {result["api"]}: {result["status"]}')
    
    # Save results to file
    with open('results.json', 'w') as f:
        json.dump(results, f)
    
    # Set output variables for GitHub Actions (using new syntax)
    print(f'\napply_for_today={apply_for_today}')
    
    return apply_for_today, results

def send_ipo_status_notification():
    """
    Send Telegram notification for IPO status check results
    This function is called by GitHub Actions to send daily status reports
    """
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
    apply_for_today = os.getenv('APPLY_FOR_TODAY', 'false')
    
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