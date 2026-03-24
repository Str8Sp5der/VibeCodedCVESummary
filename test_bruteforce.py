#!/usr/bin/env python3
"""Test brute-force protection"""
import requests
import json
import time

BASE_URL = 'http://127.0.0.1:5000'

print('Testing brute-force protection...')
print('1. Registering attacker user...')
resp = requests.post(f'{BASE_URL}/api/register', 
                    json={'username': 'attacker', 'password': 'badpass123'}, 
                    timeout=5)
print(f'   Status: {resp.status_code}')
time.sleep(1)

print('2. Making 5 failed login attempts (spaced 2 seconds apart)...')
for i in range(5):
    resp = requests.post(f'{BASE_URL}/api/login', 
                        json={'username': 'attacker', 'password': 'wrongpass'}, 
                        timeout=5)
    print(f'   Attempt {i+1}: Status {resp.status_code}')
    time.sleep(2)  # Space out requests to avoid rate limit

print('3. 6th attempt should be blocked with 429...')
resp = requests.post(f'{BASE_URL}/api/login', 
                    json={'username': 'attacker', 'password': 'wrongpass'}, 
                    timeout=5)
print(f'   Attempt 6: Status {resp.status_code}')
if resp.status_code == 429:
    print('   ✓ Account locked due to brute-force')
else:
    print(f'   Error: Expected 429 "Account locked", got {resp.status_code}')

print('\n4. Correct password still fails during lockout...')
resp = requests.post(f'{BASE_URL}/api/login', 
                    json={'username': 'attacker', 'password': 'badpass123'}, 
                    timeout=5)
print(f'   Status: {resp.status_code} - Account still locked')
if resp.status_code == 429:
    print('   ✓ Correct password rejected during lockout')
