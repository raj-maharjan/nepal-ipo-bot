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
    Get applicable issues from CDSC API
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
        if isinstance(response_data, dict):
            if "object" in response_data:
                print(f"Found issues in 'object' key: {len(response_data['object'])} issues")
                return response_data["object"]
            elif "data" in response_data:
                return response_data["data"]
            elif "content" in response_data:
                return response_data["content"]
            elif "items" in response_data:
                return response_data["items"]
            elif "results" in response_data:
                return response_data["results"]
            else:
                # If no known structure, return the whole response
                print(f"Unknown response structure, keys: {list(response_data.keys())}")
                return response_data
        elif isinstance(response_data, list):
            return response_data
        else:
            print(f"Unexpected response format: {type(response_data)}")
            return response_data
            
    except requests.exceptions.RequestException as e:
        print(f"Get applicable issues failed: {str(e)}")
        if hasattr(e, 'response'):
            print(f"Response status: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        raise Exception(f"Get applicable issues failed: {str(e)}")

def find_applicable_issue_by_company(applicable_issues: list, company_name: str) -> Optional[Dict[str, Any]]:
    """
    Find applicable issue by company name using simple keyword matching.
    Filters by shareGroupName = "Ordinary Shares" and statusName = "CREATE_APPROVE".
    
    Args:
        applicable_issues: List of applicable issues from API
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
    
    # Filter issues by required criteria
    filtered_issues = []
    print(f"Total issues to filter: {len(applicable_issues)}")
    for issue in applicable_issues:
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
            
        filtered_issues.append(issue)
        print(f"Added filtered issue: {issue.get('scrip')} - {issue.get('companyName')}")
    
    if not filtered_issues:
        print("No issues found matching the required filters (Ordinary Shares, CREATE_APPROVE)")
        return None
    
    # Simple keyword search on scrip and companyName
    search_company = company_name.lower()
    
    for issue in filtered_issues:
        scrip = issue.get("scrip", "").lower()
        company_name_issue = issue.get("companyName", "").lower()
        
        # Check if company name is contained in scrip or companyName
        if search_company in scrip or search_company in company_name_issue:
            print(f"Found match: {issue.get('scrip')} - {issue.get('companyName')}")
            return issue
    
    print(f"No matching issue found for company: {company_name}")
    return None

def apply_ipo(token, data, user_row, message_kitta=None):
    """
    Apply for IPO using CDSC API
    """
    if not cdsc_token:
        raise Exception("Not authenticated. Please login first.")
    
    # Use CDSC API endpoint for IPO application
    url = "https://webbackend.cdsc.com.np/api/meroShare/applicantForm/share/apply"
    
    headers = get_auth_headers()
    
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
    
    application_data = {
        "demat": f'{user_row["demat"]}',
        "boid": f'{user_row["username"]}',  # boid is the username field
        "accountNumber": f'{user_row["accountNumber"]}',
        "customerId": user_row["customerId"],
        "accountBranchId": user_row["accountBranchId"],
        "accountTypeId": user_row["accountTypeId"],
        "appliedKitta": f'{applied_kitta}',
        "crnNumber": f'{user_row["crnNumber"]}',  # CRN in quotes
        "transactionPIN": f'{user_row["transactionPIN"]}',
        "companyShareId": f'{str(data["companyShareId"])}',  # Convert to string
        "bankId": f'{user_row["bankId"]}'
    }
    
    print(f"Applying IPO with data: {application_data}")
    
    try:
        response = requests.post(url, json=application_data, headers=headers, cookies=cdsc_cookies)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"IPO Application failed: {str(e)}")
        if hasattr(e, 'response'):
            print(f"Response status: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        raise Exception(f"IPO Application failed: {str(e)}")
