"""Upload to ModelScope Space using Bearer token API"""
import os
import sys
import requests

TOKEN = os.environ.get("MODELSCOPE_TOKEN")
if not TOKEN:
    print("请设置环境变量 MODELSCOPE_TOKEN")
    print("例如: $env:MODELSCOPE_TOKEN='你的token'")
    sys.exit(1)

BASE = "C:/Users/F/Desktop/fund_backtest"
SPACE_ID = "konatos/etf-backtest"
API_BASE = "https://www.modelscope.cn/api/v1"

files_to_upload = [
    "app.py", "data_fetcher.py", "backtest.py", "charts.py",
    "requirements.txt", "streamlit_app.py", "README.md",
    "egg.jpg",
]

headers = {"Authorization": f"Bearer {TOKEN}"}

print(f"Uploading {len(files_to_upload)} files to {SPACE_ID}...")
print()

for fname in files_to_upload:
    path = os.path.join(BASE, fname)
    if not os.path.exists(path):
        print(f"  SKIP {fname} (not found)")
        continue

    print(f"  Uploading {fname}...", end=" ")
    try:
        with open(path, "rb") as f:
            resp = requests.post(
                f"{API_BASE}/spaces/{SPACE_ID}/upload",
                headers=headers,
                files={"file": (fname, f, "application/octet-stream")},
                timeout=60,
            )
        if resp.status_code in (200, 201):
            print("OK")
        else:
            print(f"FAILED ({resp.status_code} {resp.text[:80]})")
    except Exception as e:
        print(f"ERROR ({e})")

# Trigger rebuild
print("\n  Triggering rebuild...", end=" ")
try:
    resp = requests.post(
        f"https://www.modelscope.cn/api/spaces/{SPACE_ID}/rebuild",
        headers=headers,
        json={},
        timeout=30,
    )
    if resp.status_code in (200, 201, 202):
        print("OK")
    else:
        print(f"maybe OK (status {resp.status_code})")
except Exception as e:
    print(f"note: {e}")
    print("  Rebuild may need to be triggered manually from the webpage")

print()
print("Done! Visit: https://www.modelscope.cn/spaces/konatos/etf-backtest")
