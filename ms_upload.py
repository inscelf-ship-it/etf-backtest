"""Upload to ModelScope Space using web API with token"""
import os
import requests
import re

TOKEN = os.environ.get("MODELSCOPE_TOKEN")
if not TOKEN:
    raise ValueError("请设置环境变量 MODELSCOPE_TOKEN，例如: $env:MODELSCOPE_TOKEN='你的token'")
BASE = "C:/Users/F/Desktop/fund_backtest"
SPACE_ID = "konatos/etf-backtest"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
})

# Set token as both cookie and header
session.cookies.set("m_session_id", TOKEN, domain=".modelscope.cn")
session.headers["Authorization"] = f"Bearer {TOKEN}"

# Step 1: Visit the space page to get CSRF token and info
print("Fetching space page...")
resp = session.get(f"https://www.modelscope.cn/spaces/{SPACE_ID}", timeout=15)
html = resp.text

# Extract CSRF token
csrf_match = re.search(r'csrf_token[^>]*content="([^"]+)"', html)
if csrf_match:
    csrf = csrf_match.group(1)
else:
    # From cookie
    for c in session.cookies:
        if c.name == "csrf_token":
            csrf = c.value
            break
    else:
        csrf = None

print(f"CSRF: {csrf[:20] if csrf else 'not found'}...")

# Try to find the upload API endpoint
# ModelScope Spaces may use the same API as HF
# Try: https://www.modelscope.cn/api/spaces/{id}/upload

# Step 2: Try uploading files
files_to_upload = [
    "app.py", "data_fetcher.py", "backtest.py", "charts.py",
    "requirements.txt", "streamlit_app.py", "README.md",
    "egg.jpg",
]

for fname in files_to_upload:
    path = os.path.join(BASE, fname)
    if not os.path.exists(path):
        print(f"  SKIP {fname}")
        continue
    
    print(f"Uploading {fname}...", end=" ")
    
    # Try different API endpoints
    for api_path in [
        f"https://www.modelscope.cn/api/spaces/{SPACE_ID}/upload",
        f"https://www.modelscope.cn/api/v1/spaces/{SPACE_ID}/upload",
        f"https://www.modelscope.cn/api/v1/space/{SPACE_ID}/upload",
    ]:
        try:
            with open(path, "rb") as f:
                file_data = f.read()
            
            files_param = {"file": (fname, file_data, "application/octet-stream")}
            
            headers = {
                "Referer": f"https://www.modelscope.cn/spaces/{SPACE_ID}",
                "X-CSRF-Token": csrf or "",
                "Authorization": f"Bearer {TOKEN}",
            }
            
            resp = session.post(api_path, files=files_param, headers=headers, timeout=30)
            
            if resp.status_code in (200, 201):
                print(f"OK -> {api_path}")
                break
            else:
                print(f"\n  Try {api_path}: {resp.status_code} {resp.text[:100]}")
        except Exception as e:
            print(f"\n  Error {api_path}: {e}")
    else:
        print("FAILED all endpoints")

# Step 3: Trigger rebuild
print("\nTriggering rebuild...")
rebuild_ok = False
for rebuild_url in [
    f"https://www.modelscope.cn/api/v1/spaces/{SPACE_ID}/rebuild",
    f"https://www.modelscope.cn/api/spaces/{SPACE_ID}/rebuild",
]:
    try:
        resp = session.post(rebuild_url, headers=headers, timeout=30)
        if resp.status_code in (200, 201, 202):
            print(f"Rebuild triggered: {rebuild_url}")
            rebuild_ok = True
            break
        else:
            print(f"  Try {rebuild_url}: {resp.status_code}")
    except Exception as e:
        print(f"  Try {rebuild_url}: {e}")

if not rebuild_ok:
    print("⚠️ Rebuild API not available - visit the space page to trigger rebuild manually")

print("\nDone!")
print(f"\nVisit: https://www.modelscope.cn/spaces/{SPACE_ID}")
