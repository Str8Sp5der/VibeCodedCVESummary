#!/usr/bin/env python3
"""Quick focused test with proper spacing - avoids rate limit"""
import requests
import time

BASE_URL = 'http://127.0.0.1:5000'

# Register
print('Registering user...')
r = requests.post(f'{BASE_URL}/api/register', json={'username': 'finaltest', 'password': 'FinalPass123!'})
print(f'  Result: {r.status_code} {r.json().get("message", "OK")}')
time.sleep(2)

# Login
print('Logging in...')
s = requests.Session()
r = s.post(f'{BASE_URL}/api/login', json={'username': 'finaltest', 'password': 'FinalPass123!'})
print(f'  Result: {r.status_code}')
print(f'  Authenticated: {r.status_code == 200}')
time.sleep(1)

# Access protected endpoint
print('Accessing protected PoC endpoint...')
r = s.get(f'{BASE_URL}/api/cve/CVE-2021-44228/poc')
print(f'  Result: {r.status_code}')
print(f'  Got PoCs: {len(r.json().get("poc", [])) if r.status_code == 200 else 0}')
time.sleep(1)

# Logout
print('Logging out...')
r = s.post(f'{BASE_URL}/api/logout')
print(f'  Result: {r.status_code}')
time.sleep(1)

# Try to access after logout
print('Trying PoC endpoint after logout...')
r = s.get(f'{BASE_URL}/api/cve/CVE-2021-44228/poc')
print(f'  Result: {r.status_code} (should be 401)')
print(f'  ✓ Session properly cleared' if r.status_code == 401 else '  ✗ Session not cleared')
