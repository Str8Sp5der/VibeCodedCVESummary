## Quick Start

### Prerequisites
- **Python 3.9+** installed on your system
- **Windows PowerShell** or **Command Prompt**
- ~50MB free disk space for the SQLite database

### Step 1: Get the Project
```powershell
# Clone the repository
git clone https://github.com/Str8Sp5der/VibeCodedCVESummary
cd VibeCodedCVESummary

# Or if already downloaded, navigate to the folder
cd C:\Users\<YourUsername>\Downloads\VibeCodedCVESummary
```

### Step 2: Create Virtual Environment
```powershell
python -m venv .venv
```
✅ **Expected output:** A `.venv` folder is created in the project directory.

### Step 3: Install Dependency Management Tool
Install `pip-tools` to manage and auto-upgrade dependencies to latest versions:
```powershell
.\.venv\Scripts\python.exe -m pip install pip-tools>=7.0.0
```
✅ **Expected output:** `Successfully installed pip-tools`

### Step 4: Compile and Install Latest Dependencies
Compile `requirements.in` to generate `requirements.txt` with the latest available versions:
```powershell
.\.venv\Scripts\python.exe -m piptools compile requirements.in --upgrade
```
Then install the compiled requirements:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```
✅ **Expected output:** You should see packages installed with the latest compatible versions.

### Step 5: Run the Application
```powershell
.\.venv\Scripts\python.exe app.py
```
✅ **Expected output:**
```
 * Running on http://127.0.0.1:5000 (Press CTRL+C to quit)
```

### Step 6: Open in Your Browser
Go to: **http://127.0.0.1:5000**

---

## How to Use the App

1. **Register an Account** — Click "Sign Up" in the top-right corner
2. **Login** — Enter your username and password
3. **Search for CVEs** — Type a CVE ID (e.g., `CVE-2024-1234`) or search term in the search box
4. **View Details** — Click on a CVE to see CVSS scores, affected systems, and PoC exploits
5. **Logout** — Click "Logout" when finished

---

## Stopping the App
In the PowerShell window, press:
```
CTRL+C
```

---

## Running Again (Next Time)
To run the app again, skip Steps 1-4 and just run:
```powershell
.\.venv\Scripts\python.exe app.py
```

**To ensure you have the latest security patches**, periodically recompile dependencies:
```powershell
.\.venv\Scripts\python.exe -m piptools compile requirements.in --upgrade
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

---

## Automatic Dependency Updates (Production)
For production environments, ensure dependencies are always updated to latest versions:
```powershell
# Before each deployment
.\.venv\Scripts\python.exe -m piptools compile requirements.in --upgrade
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

This ensures critical security patches are applied immediately without manual intervention.

---

## Optional: Increase API Rate Limits
For higher rate limits (50 requests/30s instead of 5), get a free NVD API key:
1. Apply at: https://nvd.nist.gov/developers/request-an-api-key
2. Set the key before running:
```powershell
$env:NVD_API_KEY="your-api-key-here"
.\.venv\Scripts\python.exe app.py
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'bleach'` | Re-run Step 4: `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` |
| `pip-tools not found` | Re-run Step 3: `.\.venv\Scripts\python.exe -m pip install pip-tools>=7.0.0` |
| PowerShell says "scripts disabled" | Use Command Prompt: `.\.venv\Scripts\activate.bat` then `python app.py` |
| Port 5000 in use | Change port in `app.py` (last line) to `port=5001` |
| `python: command not found` | Always use `.\.venv\Scripts\python.exe` (not just `python`) |
| Browser can't connect | Ensure terminal shows `Running on http://127.0.0.1:5000` |

---
