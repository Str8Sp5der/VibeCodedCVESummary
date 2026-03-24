#!/usr/bin/env python3
"""Test authentication flow"""
import requests
import json
import time

BASE_URL = 'http://127.0.0.1:5000'

print('1. Registering new user...')
resp = requests.post(f'{BASE_URL}/api/register', 
                    json={'username': 'pocuser', 'password': 'testpass123'}, 
                    timeout=5)
print(f'   Status: {resp.status_code}')
time.sleep(1)

# Login with the new user
print('2. Logging in...')
session = requests.Session()
resp = session.post(f'{BASE_URL}/api/login', 
                   json={'username': 'pocuser', 'password': 'testpass123'}, 
                   timeout=5)
print(f'   Status: {resp.status_code}')
print(f'   Message: {resp.json().get("message")}')
time.sleep(1)

# Test the protected PoC endpoint
print('3. Accessing PoC endpoint (authenticated)...')
resp = session.get(f'{BASE_URL}/api/cve/CVE-2021-44228/poc', timeout=5)
print(f'   Status: {resp.status_code}')
if resp.status_code == 200:
    data = resp.json()
    print(f'   PoC data keys: {list(data.keys())}')
    if 'poc' in data:
        print(f'   Number of PoCs: {len(data["poc"])}')
else:
    print(f'   Error: {resp.text[:200]}')
time.sleep(1)

# Test logout
print('4. Logging out...')
resp = session.post(f'{BASE_URL}/api/logout', timeout=5)
print(f'   Status: {resp.status_code}')
print(f'   Message: {resp.json().get("message")}')
time.sleep(1)

# Test PoC endpoint without authentication
print('5. Accessing PoC endpoint (NOT authenticated)...')
resp = session.get(f'{BASE_URL}/api/cve/CVE-2021-44228/poc', timeout=5)
print(f'   Status: {resp.status_code}')
if resp.status_code == 401:
    print('   ✓ Correctly rejected - requires authentication')
else:
    print(f'   Error: Should be 401 but got {resp.status_code}')
