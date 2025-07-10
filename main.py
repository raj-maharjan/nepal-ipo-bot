from fastapi import FastAPI, Request, Response
from sheets import get_sheet_data
from parser import extract_person_company_and_kitta
from api import login, apply_ipo, get_applicable_issues, find_applicable_issue_by_company
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

TWILIO_NUMBER = os.getenv('WHATSAPP_NUMBER')

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
