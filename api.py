import requests
import os
from typing import Optional, Dict, Any

# Global variables to store authentication data
cdsc_token = None
cdsc_cookies = None

def login(client_id, username, password):
    """
    Authenticate with CDSC API and store JWT token and cookies
    """
    global cdsc_token, cdsc_cookies
    
    url = "https://webbackend.cdsc.com.np/api/meroShare/auth/"
    payload = {
        "clientId": client_id,
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        # Parse response to check for expiration issues
        response_data = response.json()
        
        # Check for password expiration
        if response_data.get("passwordExpired", False):
            error_msg = f"Password expired for user. Please change password in CDSC MeroShare."
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
        
        # Check for account expiration
        if response_data.get("accountExpired", False):
            error_msg = f"Account expired for user. Please renew account in CDSC MeroShare."
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
        
        # Check for demat expiration
        if response_data.get("dematExpired", False):
            error_msg = f"Demat account expired for user. Please renew demat account in CDSC MeroShare."
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
        
        # Extract JWT token from response headers
        auth_header = response.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            cdsc_token = auth_header.split('Bearer ')[1]
            print(f"Token extracted from header: {cdsc_token[:20]}...")
        else:
            # If not in Authorization header, check for JWT in response body
            cdsc_token = auth_header
        
        # Store cookies for future requests
        cdsc_cookies = response.cookies
        
        return cdsc_token
        
    except requests.exceptions.RequestException as e:
        print(f"CDSC Authentication failed with RequestException: {str(e)}")
        print(f"Exception type: {type(e)}")
        if hasattr(e, 'response'):
            print(f"Response status: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        raise Exception(f"Authentication failed: {str(e)}")
    except Exception as e:
        print(f"CDSC Authentication failed with general exception: {str(e)}")
        print(f"Exception type: {type(e)}")
        raise Exception(f"Authentication failed: {str(e)}")

def get_auth_headers():
    """
    Get headers with authentication for CDSC API calls
    """
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    if cdsc_token:
        headers['Authorization'] = cdsc_token
    
    return headers

def get_applicable_issues():
    """
    Get applicable issues from CDSC API and filter by required criteria.
    Filters by shareGroupName = "Ordinary Shares", statusName = "CREATE_APPROVE", 
    and shareTypeName in ("IPO", "FPO", "RESERVED").
    """
    if not cdsc_token:
        raise Exception("Not authenticated. Please login first.")
    
    url = "https://webbackend.cdsc.com.np/api/meroShare/companyShare/applicableIssue/"
    
    headers = get_auth_headers()
    payload = {"filterFieldParams":[{"key":"companyIssue.companyISIN.script","alias":"Scrip"},{"key":"companyIssue.companyISIN.company.name","alias":"Company Name"},{"key":"companyIssue.assignedToClient.name","value":"","alias":"Issue Manager"}],"page":1,"size":10,"searchRoleViewConstants":"VIEW_APPLICABLE_SHARE","filterDateParams":[{"key":"minIssueOpenDate","condition":"","alias":"","value":""},{"key":"maxIssueCloseDate","condition":"","alias":"","value":""}]}
    
    try:
        response = requests.post(url, json=payload, headers=headers, cookies=cdsc_cookies)
        
        response.raise_for_status()
        response_data = response.json()
        
        # Extract the actual issues from the response
        # The response has a structure like {"object": [...], "totalCount": 0}
        raw_issues = []
        if isinstance(response_data, dict):
            if "object" in response_data:
                print(f"Found issues in 'object' key: {len(response_data['object'])} issues")
                raw_issues = response_data["object"]
            elif "data" in response_data:
                raw_issues = response_data["data"]
            elif "content" in response_data:
                raw_issues = response_data["content"]
            elif "items" in response_data:
                raw_issues = response_data["items"]
            elif "results" in response_data:
                raw_issues = response_data["results"]
            else:
                # If no known structure, return the whole response
                print(f"Unknown response structure, keys: {list(response_data.keys())}")
                raw_issues = response_data
        elif isinstance(response_data, list):
            raw_issues = response_data
        else:
            print(f"Unexpected response format: {type(response_data)}")
            return response_data
        
        # Filter issues by required criteria
        filtered_issues = []
        print(f"Total issues to filter: {len(raw_issues)}")
        for issue in raw_issues:
            # Check if it's a dictionary and has required fields
            if not isinstance(issue, dict):
                print(f"Skipping non-dict issue: {type(issue)}")
                continue
                
            # Filter by shareGroupName = "Ordinary Shares"
            if issue.get("shareGroupName") != "Ordinary Shares":
                print(f"Skipping issue - shareGroupName: {issue.get('shareGroupName')} (expected: Ordinary Shares)")
                continue
                
            # Filter by statusName = "CREATE_APPROVE"
            if issue.get("statusName") != "CREATE_APPROVE":
                print(f"Skipping issue - statusName: {issue.get('statusName')} (expected: CREATE_APPROVE)")
                continue
                
            # Filter by shareTypeName in ("IPO", "FPO", "RESERVED")
            share_type_name = issue.get("shareTypeName", "")
            if share_type_name not in ("IPO", "FPO", "RESERVED"):
                print(f"Skipping issue - shareTypeName: {share_type_name} (expected: IPO, FPO, or RESERVED)")
                continue
                
            # Filter out issues that are already in process
            action = issue.get("action", "")
            if action == "inProcess":
                print(f"Skipping issue - action: {action} (already in process): {issue.get('scrip')} - {issue.get('companyName')}")
                continue
                
            filtered_issues.append(issue)
            print(f"Added filtered issue: {issue.get('scrip')} - {issue.get('companyName')} - {share_type_name}")
        
        print(f"Returning {len(filtered_issues)} filtered issues")
        return filtered_issues
            
    except requests.exceptions.RequestException as e:
        print(f"Get applicable issues failed: {str(e)}")
        if hasattr(e, 'response'):
            print(f"Response status: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        raise Exception(f"Get applicable issues failed: {str(e)}")

def find_applicable_issue_by_company(applicable_issues: list, company_name: str) -> Optional[Dict[str, Any]]:
    """
    Find applicable issue by company name using simple keyword matching.
    Issues are already filtered by get_applicable_issues() function.
    
    Args:
        applicable_issues: List of applicable issues from API (already filtered)
        company_name: Company name to search for
    
    Returns:
        Matching issue dictionary or None if not found
    """
    # Handle case where applicable_issues might be a dict with nested data
    if isinstance(applicable_issues, dict):
        print(f"Response is dict with keys: {list(applicable_issues.keys())}")
        if "object" in applicable_issues:
            applicable_issues = applicable_issues["object"]
            print(f"Extracted {len(applicable_issues)} issues from 'object' key")
        elif "data" in applicable_issues:
            applicable_issues = applicable_issues["data"]
        elif "content" in applicable_issues:
            applicable_issues = applicable_issues["content"]
        elif "items" in applicable_issues:
            applicable_issues = applicable_issues["items"]
        elif "results" in applicable_issues:
            applicable_issues = applicable_issues["results"]
    
    if not applicable_issues or not isinstance(applicable_issues, list):
        print(f"No applicable issues found or invalid format. Type: {type(applicable_issues)}")
        return None
    
    print(f"Searching through {len(applicable_issues)} filtered issues for company: {company_name}")
    
    # Simple keyword search on scrip and companyName
    search_company = company_name.lower()
    
    for issue in applicable_issues:
        scrip = issue.get("scrip", "").lower()
        company_name_issue = issue.get("companyName", "").lower()
        
        # Check if company name is contained in scrip or companyName
        if search_company in scrip or search_company in company_name_issue:
            print(f"Found match: {issue.get('scrip')} - {issue.get('companyName')}")
            return issue
    
    print(f"No matching issue found for company: {company_name}")
    return None

def get_user_details():
    """
    Get user details (demat, boid, etc.) from CDSC API
    """
    if not cdsc_token:
        raise Exception("Not authenticated. Please login first.")
    
    url = "https://webbackend.cdsc.com.np/api/meroShare/ownDetail/"
    
    headers = get_auth_headers()
    
    try:
        response = requests.get(url, headers=headers, cookies=cdsc_cookies)
        response.raise_for_status()
        user_data = response.json()
        
        print(f"User details from CDSC API: {user_data}")
        return user_data
        
    except requests.exceptions.RequestException as e:
        print(f"Get user details failed: {str(e)}")
        if hasattr(e, 'response'):
            print(f"Response status: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        raise Exception(f"Get user details failed: {str(e)}")

def get_bank_ids():
    """
    Get bank IDs from CDSC API
    """
    if not cdsc_token:
        raise Exception("Not authenticated. Please login first.")
    
    url = "https://webbackend.cdsc.com.np/api/meroShare/bank/"
    
    headers = get_auth_headers()
    
    try:
        response = requests.get(url, headers=headers, cookies=cdsc_cookies)
        response.raise_for_status()
        bank_data = response.json()
        
        print(f"Bank data from CDSC API: {bank_data}")
        
        # Extract bank IDs from the response
        bank_ids = []
        if isinstance(bank_data, list):
            for bank in bank_data:
                if isinstance(bank, dict) and "id" in bank:
                    bank_ids.append(str(bank["id"]))
        elif isinstance(bank_data, dict):
            # Handle case where response might be wrapped in an object
            if "object" in bank_data:
                for bank in bank_data["object"]:
                    if isinstance(bank, dict) and "id" in bank:
                        bank_ids.append(str(bank["id"]))
            elif "data" in bank_data:
                for bank in bank_data["data"]:
                    if isinstance(bank, dict) and "id" in bank:
                        bank_ids.append(str(bank["id"]))
        
        print(f"Extracted bank IDs: {bank_ids}")
        return bank_ids
        
    except requests.exceptions.RequestException as e:
        print(f"Get bank IDs failed: {str(e)}")
        if hasattr(e, 'response'):
            print(f"Response status: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        raise Exception(f"Get bank IDs failed: {str(e)}")

def get_account_details(bank_id):
    """
    Get account details from CDSC API for a specific bank
    """
    if not cdsc_token:
        raise Exception("Not authenticated. Please login first.")
    
    url = f"https://webbackend.cdsc.com.np/api/meroShare/bank/{bank_id}"
    
    headers = get_auth_headers()
    
    try:
        response = requests.get(url, headers=headers, cookies=cdsc_cookies)
        response.raise_for_status()
        account_data = response.json()
        
        print(f"Account data from CDSC API for bank {bank_id}: {account_data}")
        
        # Extract account details from the response
        account_details = {}
        
        # Handle array response - always take the first object
        if isinstance(account_data, list) and len(account_data) > 0:
            first_account = account_data[0]
            if isinstance(first_account, dict):
                if "accountBranchId" in first_account:
                    account_details["accountBranchId"] = str(first_account["accountBranchId"])
                if "accountNumber" in first_account:
                    account_details["accountNumber"] = str(first_account["accountNumber"])
                if "accountTypeId" in first_account:
                    account_details["accountTypeId"] = str(first_account["accountTypeId"])
                if "id" in first_account:
                    account_details["customerId"] = str(first_account["id"])
        elif isinstance(account_data, dict):
            # Handle different possible response structures
            if "accountBranchId" in account_data:
                account_details["accountBranchId"] = str(account_data["accountBranchId"])
            if "accountNumber" in account_data:
                account_details["accountNumber"] = str(account_data["accountNumber"])
            if "accountTypeId" in account_data:
                account_details["accountTypeId"] = str(account_data["accountTypeId"])
            if "id" in account_data:
                account_details["customerId"] = str(account_data["id"])
            elif "object" in account_data:
                # Handle case where data might be wrapped in object
                obj_data = account_data["object"]
                if isinstance(obj_data, dict):
                    if "accountBranchId" in obj_data:
                        account_details["accountBranchId"] = str(obj_data["accountBranchId"])
                    if "accountNumber" in obj_data:
                        account_details["accountNumber"] = str(obj_data["accountNumber"])
                    if "accountTypeId" in obj_data:
                        account_details["accountTypeId"] = str(obj_data["accountTypeId"])
                    if "id" in obj_data:
                        account_details["customerId"] = str(obj_data["id"])
        
        print(f"Extracted account details: {account_details}")
        return account_details
        
    except requests.exceptions.RequestException as e:
        print(f"Get account details failed for bank {bank_id}: {str(e)}")
        if hasattr(e, 'response'):
            print(f"Response status: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        raise Exception(f"Get account details failed for bank {bank_id}: {str(e)}")

def apply_ipo(token, data, user_row, message_kitta=None):
    """
    Apply for IPO using CDSC API
    """
    if not cdsc_token:
        raise Exception("Not authenticated. Please login first.")
    
    # Use CDSC API endpoint for IPO application
    url = "https://webbackend.cdsc.com.np/api/meroShare/applicantForm/share/apply"
    
    headers = get_auth_headers()
    
    # Get user details from CDSC API
    user_details = get_user_details()
    
    # Get bank IDs from CDSC API
    bank_ids = get_bank_ids()
    
    if not bank_ids:
        raise Exception("No bank IDs available from CDSC API")
    
    # Determine appliedKitta with priority: message > sheet > default
    applied_kitta = "10"  # Default value
    
    # Check sheet first
    sheet_kitta = user_row.get("appliedKitta")
    if sheet_kitta and sheet_kitta != "":
        applied_kitta = str(sheet_kitta)
    
    # Override with message kitta if provided
    if message_kitta:
        applied_kitta = str(message_kitta)
        print(f"Using kitta from message: {applied_kitta}")
    else:
        print(f"Using kitta from sheet: {applied_kitta}")
    
    # Try each bank ID until one succeeds
    for bank_id in bank_ids:
        print(f"Trying with bank ID: {bank_id}")
        
        try:
            # Get account details for this specific bank
            account_details = get_account_details(bank_id)
            
            # Use demat and boid from CDSC API instead of sheet
            application_data = {
                "demat": f'{user_details.get("demat", "")}',
                "boid": f'{user_details.get("boid", "")}',
                "accountNumber": account_details.get("accountNumber", ""),
                "customerId": account_details.get("customerId", ""),
                "accountBranchId": account_details.get("accountBranchId", ""),
                "accountTypeId": account_details.get("accountTypeId", ""),
                "appliedKitta": f'{applied_kitta}',
                "crnNumber": str(user_row["crnNumber"]),  # CRN as string with leading zeros preserved
                "transactionPIN": f'{user_row["transactionPIN"]}',
                "companyShareId": f'{str(data["companyShareId"])}',  # Convert to string
                "bankId": bank_id
            }
            
            print(f"Applying IPO with data: {application_data}")
            
            response = requests.post(url, json=application_data, headers=headers, cookies=cdsc_cookies)
            response.raise_for_status()
            print(f"IPO Application successful with bank ID: {bank_id}")
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"IPO Application failed with bank ID {bank_id}: {str(e)}")
            if hasattr(e, 'response'):
                print(f"Response status: {e.response.status_code}")
                print(f"Response text: {e.response.text}")
            
            # If this is the last bank ID, raise the exception
            if bank_id == bank_ids[-1]:
                raise Exception(f"IPO Application failed with all bank IDs: {str(e)}")
            else:
                print(f"Trying next bank ID...")
                continue
    
    # This should not be reached, but just in case
    raise Exception("No bank IDs available for IPO application")
