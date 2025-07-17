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

TWILIO_NUMBER = os.getenv('WHATSAPP_NUMBER')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

class ApplyRequest(BaseModel):
    user_name: str

@app.post("/webhook")
async def twilio_webhook(request: Request):
    form = await request.form()
    msg = form.get("Body", "")
    sender = form.get("From")

    sheet_data = get_sheet_data()
    known_people = [row["name"].lower() for row in sheet_data]

    result = extract_person_company_and_kitta(msg, known_people)
    person = result["person"]
    company = result["company"]
    message_kitta = result["kitta"]
    
    if not person or not company:
        result = send_whatsapp(sender, "❌ Couldn't detect person or company.")
        print(f"📱 WhatsApp send result: {result}")
        return Response(content="OK", media_type="text/plain")
    
    print("person", person)
    print("company", company)
    print("message_kitta", message_kitta)
    
    user_row = next((row for row in sheet_data if row["name"].lower() == person), None)
    if not user_row:
        result = send_whatsapp(sender, f"❌ No info found for {person}.")
        print(f"📱 WhatsApp send result: {result}")
        return Response(content="OK", media_type="text/plain")
    print("user_row", user_row)
    
    try:
        token = login(user_row["clientId"], user_row["username"], user_row["password"])
        applicable_issues = get_applicable_issues()
        print("applicable_issues", applicable_issues)
        
        # Find the applicable issue using fuzzy search
        selected_issue = find_applicable_issue_by_company(applicable_issues, company)
        if not selected_issue:
            result = send_whatsapp(sender, f"❌ No applicable issue found for {company.upper()}")
            print(f"📱 WhatsApp send result: {result}")
            return Response(content="OK", media_type="text/plain")
        
        print("selected_issue", selected_issue)
        
        # Check if IPO is already in process
        if selected_issue.get("action") == "inProcess":
            already_filled_message = f"⚠️ Already filled IPO for {selected_issue.get('companyName')} ({selected_issue.get('scrip')}) for {person}"
            result = send_whatsapp(sender, already_filled_message)
            print(f"📱 WhatsApp send result: {result}")
            return Response(content="OK", media_type="text/plain")
        
        # Apply for IPO
        ipo_result = apply_ipo(token, {
            "companyShareId": selected_issue["companyShareId"]
        }, user_row, message_kitta)
        
        # Send success message
        success_message = f"✅ IPO applied successfully for {person} in {selected_issue.get('scrip')} ({selected_issue.get('companyName')})"
        result = send_whatsapp(sender, success_message)
        print(f"📱 WhatsApp send result: {result}")
        return Response(content="OK", media_type="text/plain")
    except Exception as e:
        result = send_whatsapp(sender, f"❌ Error: {str(e)}")
        print(f"📱 WhatsApp send result: {result}")
        return Response(content="OK", media_type="text/plain")

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
        # Login to CDSC
        token = login(user_row["clientId"], user_row["username"], user_row["password"])
        
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
            send_telegram(f"ℹ️ No applicable IPO issue found for {cdsc_name}.")
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
        send_telegram(error_message)
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
    
    send_telegram(completion_message)

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
        # Login to CDSC
        token = login(user_row["clientId"], user_row["username"], user_row["password"])
        
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
            send_telegram(completion_message)
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
            send_telegram(f"ℹ️ No applicable IPO issue found for {cdsc_name}.")
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
        send_telegram(error_message)
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
    
    send_telegram(completion_message)

def send_telegram(message: str) -> Dict[str, Any]:
    """
    Send message via Telegram bot
    """
    try:
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            print("❌ Missing Telegram credentials in environment variables")
            return {"status": "error", "message": "Missing Telegram credentials"}
        
        print(f"📤 Sending Telegram message: {message}")
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        
        response = requests.post(url, json=payload)
        
        print(f"📡 Telegram API Response Status: {response.status_code}")
        print(f"📡 Telegram API Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Telegram message sent successfully")
            return {"status": "success", "message": message}
        else:
            print(f"❌ Failed to send Telegram message. Status: {response.status_code}")
            return {"status": "error", "message": f"API Error: {response.status_code}"}
            
    except Exception as e:
        print(f"❌ Exception in send_telegram: {str(e)}")
        return {"status": "error", "message": str(e)}

def send_whatsapp(to, message):
    try:
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        
        if not account_sid or not auth_token:
            print("❌ Missing Twilio credentials in environment variables")
            return {"status": "error", "message": "Missing credentials"}
        
        print(f"📤 Sending WhatsApp message to {to}: {message}")
        
        response = requests.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json",
            auth=(account_sid, auth_token),
            data={
                "From": TWILIO_NUMBER,
                "To": to,
                "Body": message
            }
        )
        
        print(f"📡 Twilio API Response Status: {response.status_code}")
        print(f"📡 Twilio API Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ WhatsApp message sent successfully")
            return {"status": "success", "message": message}
        else:
            print(f"❌ Failed to send WhatsApp message. Status: {response.status_code}")
            return {"status": "error", "message": f"API Error: {response.status_code}"}
            
    except Exception as e:
        print(f"❌ Exception in send_whatsapp: {str(e)}")
        return {"status": "error", "message": str(e)}
