# Simple Keyword Search for Applicable Issues

## Overview

The system now includes simple keyword search functionality to find applicable IPO issues based on company names. This feature searches through the list of applicable issues returned by the CDSC API and finds matches using simple substring matching.

## Features

### 1. Simple Keyword Search
- Searches both `scrip` and `companyName` fields
- Uses simple substring matching (case insensitive)
- Checks if the company name is contained in either field
- Returns the first match found

### 2. Filtering
- **shareGroupName**: Must be "Ordinary Shares"
- **statusName**: Must be "CREATE_APPROVE"

### 3. Response Handling
- Handles various API response structures (data, content, items, results)
- Provides detailed logging for debugging
- Gracefully handles missing or invalid data

## Implementation Details

### Function: `find_applicable_issue_by_company(applicable_issues, company_name)`

**Parameters:**
- `applicable_issues`: List of issues from CDSC API
- `company_name`: Company name to search for

**Returns:**
- Matching issue dictionary or `None` if not found

**Search Process:**
1. **Data Extraction**: Handles nested response structures
2. **Filtering**: Applies required filters (Ordinary Shares, CREATE_APPROVE)
3. **Keyword Matching**: Checks if company name is contained in scrip or companyName fields
4. **First Match**: Returns the first matching issue found

### Integration in Main Flow

The fuzzy search is integrated into the main webhook flow:

```python
# Get applicable issues from API
applicable_issues = get_applicable_issues()

# Find matching issue using fuzzy search
selected_issue = find_applicable_issue_by_company(applicable_issues, company)

# Use selected issue for IPO application
apply_ipo(token, {
    "companyShareId": selected_issue["companyShareId"]
}, user_row)
```

## Example Response Format

The system expects issues in this format:
```json
{
    "object": [{
        "companyShareId": 680,
        "subGroup": "For General Public",
        "scrip": "HIMSTAR",
        "companyName": "Him Star Urja Company Ltd.",
        "shareTypeName": "IPO",
        "shareGroupName": "Ordinary Shares",
        "statusName": "CREATE_APPROVE",
        "issueOpenDate": "Jul 8, 2025 10:00:00 AM",
        "issueCloseDate": "Jul 11, 2025 5:00:00 PM"
    }],
    "totalCount": 0
}
```

## IPO Application

The system applies for IPO using the following endpoint and payload:

**Endpoint:** `https://webbackend.cdsc.com.np/api/meroShare/applicantForm/share/apply`

**Payload Format:**
```json
{
    "demat": "1301170000202829",
    "boid": "00202829",
    "accountNumber": "0070100000569020",
    "customerId": 1552162,
    "accountBranchId": 567,
    "accountTypeId": 1,
    "appliedKitta": "10",
    "crnNumber": "czp00056259",
    "transactionPIN": "1988",
    "companyShareId": "680",
    "bankId": "6"
}
```

**Data Sources:**
- Most fields come from the sheet row (user_row)
- `boid` uses the `username` field from sheet
- `appliedKitta` priority: WhatsApp message > sheet row > default "10"
- `companyShareId` comes from the selected issue

**Message Format Support:**
- Standard formats: "apply ipo for person for company name"
- With kitta: "apply ipo for person for company name 10 kitta"
- Kitta extraction: Number before "kitta" keyword

## Logging

The system provides detailed logging for debugging:
- Total issues to filter
- Filtering results (why issues are skipped)
- Keyword match detection
- Match confirmation

## Error Handling

- Handles missing or invalid response data
- Provides clear error messages for debugging
- Gracefully handles API response structure variations
- Returns `None` when no suitable match is found 