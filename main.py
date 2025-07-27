from fastapi import FastAPI, Request, Response
from pydantic import BaseModel
from sheets import get_sheet_data
from parser import extract_person_company_and_kitta
from api import login, apply_ipo, get_applicable_issues, find_applicable_issue_by_company
import requests
import os
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables
load_dotenv()

app = FastAPI()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

class ApplyRequest(BaseModel):
    user_name: str

class TelegramUpdate(BaseModel):
    update_id: int
    message: Dict[str, Any] = None
    callback_query: Dict[str, Any] = None

@app.post("/webhook")
async def telegram_webhook(update: TelegramUpdate):
    """
    Handle Telegram bot webhook updates
    """
    if update.message:
        chat_id = update.message.get("chat", {}).get("id")
        text = update.message.get("text", "")
        user_id = update.message.get("from", {}).get("id")
        username = update.message.get("from", {}).get("username", "")
        
        print(f"📱 Received Telegram message from {username} ({user_id}): {text}")
        
        # Process the message
        result = process_telegram_message(chat_id, text, username)
        
        return {"status": "success"}
    
    return {"status": "ignored"}

def process_telegram_message(chat_id: int, text: str, username: str) -> Dict[str, Any]:
    """
    Process Telegram message and send response
    """
    sheet_data = get_sheet_data()
    known_people = [row["name"].lower() for row in sheet_data]

    result = extract_person_company_and_kitta(text, known_people)
    person = result["person"]
    company = result["company"]
    message_kitta = result["kitta"]
    
    if not person or not company:
        response_message = "❌ Couldn't detect person or company.\n\nPlease send a message in this format:\n`[person] [company] [kitta]`\n\nExample:\n`john abc 10`"
        send_telegram_message(chat_id, response_message)
        return {"status": "error", "message": "Couldn't detect person or company"}
    
    print("person", person)
    print("company", company)
    print("message_kitta", message_kitta)
    
    user_row = next((row for row in sheet_data if row["name"].lower() == person), None)
    if not user_row:
        response_message = f"❌ No info found for {person}."
        send_telegram_message(chat_id, response_message)
        return {"status": "error", "message": f"No info found for {person}"}
    
    print("user_row", user_row)
    
    try:
        token = login(user_row["clientId"], user_row["username"], user_row["password"])
        applicable_issues = get_applicable_issues()
        print("applicable_issues", applicable_issues)
        
        # Find the applicable issue using fuzzy search
        selected_issue = find_applicable_issue_by_company(applicable_issues, company)
        if not selected_issue:
            response_message = f"❌ No applicable issue found for {company.upper()}"
            send_telegram_message(chat_id, response_message)
            return {"status": "error", "message": f"No applicable issue found for {company.upper()}"}
        
        print("selected_issue", selected_issue)
        
        # Check if IPO is already in process
        if selected_issue.get("action") == "inProcess":
            already_filled_message = f"⚠️ Already filled IPO for {selected_issue.get('companyName')} ({selected_issue.get('scrip')}) for {person}"
            send_telegram_message(chat_id, already_filled_message)
            return {"status": "warning", "message": "Already filled"}
        
        # Apply for IPO with multiple bank ID handling
        try:
            ipo_result = apply_ipo(token, {
                "companyShareId": selected_issue["companyShareId"]
            }, user_row, message_kitta, selected_issue.get("shareTypeName"))
            
            # Send success message
            success_message = f"✅ IPO applied successfully for {person} in {selected_issue.get('scrip')} ({selected_issue.get('companyName')})"
            send_telegram_message(chat_id, success_message)
            return {"status": "success", "message": success_message}
            
        except Exception as e:
            error_str = str(e).lower()
            
            # Check if the error indicates all bank IDs failed
            if "all bank IDs" in error_str or "no bank ids available" in error_str:
                # All bank IDs failed, send user-friendly error message
                error_message = f"❌ All bank accounts failed for {person} in {selected_issue.get('scrip')} ({selected_issue.get('companyName')}). Please check your bank account details."
                send_telegram_message(chat_id, error_message)
                return {"status": "error", "message": str(e)}
            elif "invalid crn" in error_str:
                # CRN validation error
                error_message = f"❌ Invalid CRN for {person} in {selected_issue.get('scrip')} ({selected_issue.get('companyName')}). Please check your CRN number."
                send_telegram_message(chat_id, error_message)
                return {"status": "error", "message": str(e)}
            elif "connection failed" in error_str or "timeout" in error_str:
                # Connection error
                error_message = f"❌ Connection error for {person} in {selected_issue.get('scrip')} ({selected_issue.get('companyName')}). Please try again later."
                send_telegram_message(chat_id, error_message)
                return {"status": "error", "message": str(e)}
            else:
                # Generic error handling
                error_message = f"❌ Error applying IPO for {person} in {selected_issue.get('scrip')} ({selected_issue.get('companyName')}): {str(e)}"
                send_telegram_message(chat_id, error_message)
                return {"status": "error", "message": str(e)}
        
    except Exception as e:
        error_str = str(e).lower()
        
        # Handle authentication-related errors with user-friendly messages
        if "authentication failed" in error_str or "login failed" in error_str:
            error_message = f"❌ Authentication failed for {person}. Please check your CDSC credentials."
        elif "password expired" in error_str:
            error_message = f"❌ Password expired for {person}. Please change password in CDSC MeroShare."
        elif "account expired" in error_str:
            error_message = f"❌ Account expired for {person}. Please renew account in CDSC MeroShare."
        elif "demat expired" in error_str:
            error_message = f"❌ Demat account expired for {person}. Please renew demat account in CDSC MeroShare."
        elif "connection failed" in error_str or "timeout" in error_str:
            error_message = f"❌ Connection error for {person}. Please try again later."
        else:
            # For other errors, use a generic but user-friendly message
            error_message = f"❌ Error processing request for {person}: {str(e)}"
        
        send_telegram_message(chat_id, error_message)
        return {"status": "error", "message": str(e)}

def send_telegram_message(chat_id: int, message: str) -> Dict[str, Any]:
    """
    Send message to specific Telegram chat
    """
    try:
        if not TELEGRAM_BOT_TOKEN:
            print("❌ Missing Telegram bot token in environment variables")
            return {"status": "error", "message": "Missing Telegram credentials"}
        
        print(f"📤 Sending Telegram message to {chat_id}: {message}")
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        # Use session with retry strategy for Telegram API calls
        from api import session
        response = session.post(url, json=payload, timeout=(10, 30))
        
        print(f"📡 Telegram API Response Status: {response.status_code}")
        print(f"📡 Telegram API Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Telegram message sent successfully")
            return {"status": "success", "message": message}
        else:
            print(f"❌ Failed to send Telegram message. Status: {response.status_code}")
            return {"status": "error", "message": f"API Error: {response.status_code}"}
            
    except Exception as e:
        print(f"❌ Exception in send_telegram_message: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.post("/apply")
async def apply_all_issues(request: ApplyRequest) -> Dict[str, Any]:
    """
    Apply for all applicable IPO issues for a given user.
    Takes user_name as input and applies for all available IPOs.
    """
    user_name = request.user_name
    sheet_data = get_sheet_data()
    known_people = [row["name"].lower() for row in sheet_data]
    
    # Find user in sheet data
    user_row = next((row for row in sheet_data if row["name"].lower() == user_name.lower()), None)
    if not user_row:
        return {
            "status": "error",
            "message": f"No info found for user: {user_name}",
            "applied_issues": [],
            "failed_issues": []
        }
    
    print(f"Found user: {user_name}")
    print(f"User row: {user_row}")
    
    try:
        # Add connection timeout handling
        import time
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                # Login to CDSC
                token = login(user_row["clientId"], user_row["username"], user_row["password"])
                break  # Success, exit retry loop
                
            except Exception as e:
                print(f"❌ Login attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    print(f"⏳ Retrying login in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise Exception(f"Login failed after {max_retries} attempts: {str(e)}")
        
        # Get user details from CDSC API to get the actual name
        from api import get_user_details
        user_details = get_user_details()
        cdsc_name = user_details.get("name", user_name)  # Fallback to user_name if name not found
        
        applicable_issues = get_applicable_issues()
        print(f"Found {len(applicable_issues) if isinstance(applicable_issues, list) else 'unknown'} applicable issues")
        
        applied_issues = []
        failed_issues = []
        
        # Process each applicable issue (already filtered by API)
        if isinstance(applicable_issues, list) and len(applicable_issues) > 0:
            for issue in applicable_issues:
                try:
                    print(f"Processing issue: {issue.get('scrip')} - {issue.get('companyName')}")
                    
                    # Apply for IPO
                    ipo_result = apply_ipo(token, {
                        "companyShareId": issue["companyShareId"]
                    }, user_row)
                    
                    print(f"✅ Successfully applied for {issue.get('scrip')} ({issue.get('companyName')})")
                    applied_issues.append({
                        "company": issue.get('companyName'),
                        "scrip": issue.get('scrip'),
                        "result": ipo_result
                    })
                    
                except Exception as e:
                    print(f"❌ Failed to apply for {issue.get('scrip', 'unknown')}: {str(e)}")
                    failed_issues.append({
                        "company": issue.get('companyName'),
                        "scrip": issue.get('scrip'),
                        "reason": str(e)
                    })
            
            # Note: Telegram notifications are handled by GitHub Actions to avoid duplicates
            return {
                "status": "success",
                "cdsc_name": cdsc_name,
                "message": f"Processed {len(applied_issues)} successful applications and {len(failed_issues)} failures",
                "applied_issues": applied_issues,
                "failed_issues": failed_issues,
                "total_applied": len(applied_issues),
                "total_failed": len(failed_issues)
            }
        else:
            # No applicable issues found
            print(f"ℹ️ No applicable issues found for {cdsc_name}")
            send_telegram_message(TELEGRAM_CHAT_ID, f"ℹ️ No applicable IPO issue found for {cdsc_name}.")
            return {
                "status": "success",
                "message": "No applicable issues found",
                "applied_issues": [],
                "failed_issues": [],
                "total_applied": 0,
                "total_failed": 0
            }
        
    except Exception as e:
        print(f"❌ Error in apply_all_issues: {str(e)}")
        error_message = f"❌ Error in apply_all_issues for {user_name}: {str(e)}"
        send_telegram_message(TELEGRAM_CHAT_ID, error_message)
        return {
            "status": "error",
            "message": f"Error: {str(e)}",
            "applied_issues": [],
            "failed_issues": []
        }
    
    # Send completion notification
    completion_message = f"✅ IPO Application Complete for {user_name}\n\n"
    completion_message += f"📊 Results:\n"
    completion_message += f"• Successfully Applied: {len(applied_issues)}\n"
    completion_message += f"• Failed Applications: {len(failed_issues)}\n\n"
    
    if applied_issues:
        completion_message += "✅ Applied Issues:\n"
        for issue in applied_issues:
            completion_message += f"• {issue['scrip']} - {issue['company']}\n"
    
    if failed_issues:
        completion_message += "\n❌ Failed Issues:\n"
        for issue in failed_issues:
            completion_message += f"• {issue['scrip']} - {issue['company']} ({issue['reason']})\n"
    
    send_telegram_message(TELEGRAM_CHAT_ID, completion_message)

@app.get("/apply/{user_name}")
async def apply_all_issues_get(user_name: str) -> Dict[str, Any]:
    """
    Apply for all applicable IPO issues for a given user (GET endpoint).
    Takes user_name as path parameter and applies for all available IPOs.
    """
    sheet_data = get_sheet_data()
    known_people = [row["name"].lower() for row in sheet_data]
    
    # Find user in sheet data
    user_row = next((row for row in sheet_data if row["name"].lower() == user_name.lower()), None)
    if not user_row:
        return {
            "status": "error",
            "message": f"No info found for user: {user_name}",
            "applied_issues": [],
            "failed_issues": []
        }
    
    print(f"Found user: {user_name}")
    print(f"User row: {user_row}")
    
    try:
        # Add connection timeout handling
        import time
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                # Login to CDSC
                token = login(user_row["clientId"], user_row["username"], user_row["password"])
                break  # Success, exit retry loop
                
            except Exception as e:
                print(f"❌ Login attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    print(f"⏳ Retrying login in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise Exception(f"Login failed after {max_retries} attempts: {str(e)}")
        
        # Get user details from CDSC API to get the actual name
        from api import get_user_details
        user_details = get_user_details()
        cdsc_name = user_details.get("name", user_name)  # Fallback to user_name if name not found
        
        applicable_issues = get_applicable_issues()
        print(f"Found {len(applicable_issues) if isinstance(applicable_issues, list) else 'unknown'} applicable issues")
        
        applied_issues = []
        failed_issues = []
        
        # Process each applicable issue (already filtered by API)
        if isinstance(applicable_issues, list) and len(applicable_issues) > 0:
            for issue in applicable_issues:
                try:
                    print(f"Processing issue: {issue.get('scrip')} - {issue.get('companyName')}")
                    
                    # Apply for IPO
                    ipo_result = apply_ipo(token, {
                        "companyShareId": issue["companyShareId"]
                    }, user_row, None, issue.get("shareTypeName"))
                    
                    print(f"✅ Successfully applied for {issue.get('scrip')} ({issue.get('companyName')})")
                    applied_issues.append({
                        "company": issue.get('companyName'),
                        "scrip": issue.get('scrip'),
                        "result": ipo_result
                    })
                    
                except Exception as e:
                    print(f"❌ Failed to apply for {issue.get('scrip', 'unknown')}: {str(e)}")
                    failed_issues.append({
                        "company": issue.get('companyName'),
                        "scrip": issue.get('scrip'),
                        "reason": str(e)
                    })
            
            # Send completion notification
            completion_message = f"✅ IPO Application Complete for {cdsc_name}\n\n"
            completion_message += f"📊 Results:\n"
            completion_message += f"• Successfully Applied: {len(applied_issues)}\n"
            completion_message += f"• Failed Applications: {len(failed_issues)}\n\n"
            if applied_issues:
                completion_message += "✅ Applied Issues:\n"
                for issue in applied_issues:
                    completion_message += f"• {issue['scrip']} - {issue['company']}\n"
            if failed_issues:
                completion_message += "\n❌ Failed Issues:\n"
                for issue in failed_issues:
                    completion_message += f"• {issue['scrip']} - {issue['company']} ({issue['reason']})\n"
            send_telegram_message(TELEGRAM_CHAT_ID, completion_message)
            return {
                "status": "success",
                "cdsc_name": cdsc_name,
                "message": f"Processed {len(applied_issues)} successful applications and {len(failed_issues)} failures",
                "applied_issues": applied_issues,
                "failed_issues": failed_issues,
                "total_applied": len(applied_issues),
                "total_failed": len(failed_issues)
            }
        else:
            # No applicable issues found
            print(f"ℹ️ No applicable issues found for {cdsc_name}")
            send_telegram_message(TELEGRAM_CHAT_ID, f"ℹ️ No applicable IPO issue found for {cdsc_name}.")
            return {
                "status": "success",
                "message": "No applicable issues found",
                "applied_issues": [],
                "failed_issues": [],
                "total_applied": 0,
                "total_failed": 0
            }
        
    except Exception as e:
        print(f"❌ Error in apply_all_issues: {str(e)}")
        error_message = f"❌ Error in apply_all_issues for {user_name}: {str(e)}"
        send_telegram_message(TELEGRAM_CHAT_ID, error_message)
        return {
            "status": "error",
            "message": f"Error: {str(e)}",
            "applied_issues": [],
            "failed_issues": []
        }
    
    # Send completion notification
    completion_message = f"✅ IPO Application Complete for {user_name}\n\n"
    completion_message += f"📊 Results:\n"
    completion_message += f"• Successfully Applied: {len(applied_issues)}\n"
    completion_message += f"• Failed Applications: {len(failed_issues)}\n\n"
    
    if applied_issues:
        completion_message += "✅ Applied Issues:\n"
        for issue in applied_issues:
            completion_message += f"• {issue['scrip']} - {issue['company']}\n"
    
    if failed_issues:
        completion_message += "\n❌ Failed Issues:\n"
        for issue in failed_issues:
            completion_message += f"• {issue['scrip']} - {issue['company']} ({issue['reason']})\n"
    
    send_telegram_message(TELEGRAM_CHAT_ID, completion_message)

def check_ipo_status():
    """
    Check IPO, FPO, and Right-Share APIs for open status
    This function is called by GitHub Actions to determine if IPOs are available today
    """
    import requests
    import json
    from datetime import datetime
    
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
    import requests
    import json
    import os
    from datetime import datetime
    
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
    import sys
    
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
        # Run the FastAPI app normally
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
