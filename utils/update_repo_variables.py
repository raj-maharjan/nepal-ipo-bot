#!/usr/bin/env python3
"""
Update Repository Variables using GitHub API
"""
import requests
import json
import os
import sys

def update_repo_variables(apply_for_today, any_open):
    """
    Update repository variables using GitHub API
    """
    # Get GitHub token and repository info
    github_token = os.getenv('GITHUB_TOKEN')
    github_repository = os.getenv('GITHUB_REPOSITORY')
    
    # For GitHub Actions, GITHUB_TOKEN is automatically available
    if not github_token:
        print("❌ GITHUB_TOKEN not found")
        print("💡 This script should be run in a GitHub Actions environment")
        return False
    
    if not github_token:
        print("❌ GITHUB_TOKEN not found")
        return False
    
    if not github_repository:
        print("❌ GITHUB_REPOSITORY not found")
        return False
    
    # GitHub API endpoint for repository variables
    api_url = f"https://api.github.com/repos/{github_repository}/actions/variables"
    
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    
    # Variables to update
    variables = {
        'APPLY_FOR_TODAY': str(apply_for_today).lower(),
        'ANY_OPEN': str(any_open).lower()
    }
    
    print(f"🔄 Updating repository variables...")
    print(f"• APPLY_FOR_TODAY: {variables['APPLY_FOR_TODAY']}")
    print(f"• ANY_OPEN: {variables['ANY_OPEN']}")
    
    success_count = 0
    
    for var_name, var_value in variables.items():
        try:
            # Check if variable exists
            check_url = f"{api_url}/{var_name}"
            check_response = requests.get(check_url, headers=headers)
            
            if check_response.status_code == 200:
                # Variable exists, update it
                update_url = f"{api_url}/{var_name}"
                update_data = {
                    'name': var_name,
                    'value': var_value
                }
                
                response = requests.patch(update_url, headers=headers, json=update_data)
                
                if response.status_code == 204:
                    print(f"✅ Updated {var_name} = {var_value}")
                    success_count += 1
                else:
                    print(f"❌ Failed to update {var_name}: {response.status_code}")
                    print(f"Response: {response.text}")
            else:
                # Variable doesn't exist, create it
                create_data = {
                    'name': var_name,
                    'value': var_value
                }
                
                response = requests.post(api_url, headers=headers, json=create_data)
                
                if response.status_code == 201:
                    print(f"✅ Created {var_name} = {var_value}")
                    success_count += 1
                else:
                    print(f"❌ Failed to create {var_name}: {response.status_code}")
                    print(f"Response: {response.text}")
                    
        except Exception as e:
            print(f"❌ Error updating {var_name}: {str(e)}")
    
    if success_count == len(variables):
        print(f"🎉 Successfully updated {success_count}/{len(variables)} variables")
        return True
    else:
        print(f"⚠️ Updated {success_count}/{len(variables)} variables")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python update_repo_variables.py <apply_for_today> <any_open>")
        print("Example: python update_repo_variables.py true false")
        sys.exit(1)
    
    apply_for_today = sys.argv[1].lower() == 'true'
    any_open = sys.argv[2].lower() == 'true'
    
    success = update_repo_variables(apply_for_today, any_open)
    sys.exit(0 if success else 1) 