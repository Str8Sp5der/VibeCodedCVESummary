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

### Step 3: Install Dependencies
Run this command **once** to install all required packages:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```
✅ **Expected output:** You should see `Successfully installed flask-3.1.3 ...` and other packages.

### Step 4: Run the Application
```powershell
.\.venv\Scripts\python.exe app.py
```
✅ **Expected output:**
```
 * Running on http://127.0.0.1:5000 (Press CTRL+C to quit)
```

### Step 5: Open in Your Browser
Go to: **http://127.0.0.1:5000**
