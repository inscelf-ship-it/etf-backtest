"""上传文件到 Hugging Face Space（使用 huggingface_hub 库）"""
from huggingface_hub import HfApi, login
import os

# 使用环境变量获取 Token，避免硬编码泄露
TOKEN = os.environ.get("HF_TOKEN")
if not TOKEN:
    raise ValueError("请设置环境变量 HF_TOKEN，例如: $env:HF_TOKEN='hf_xxxx'  (Windows PowerShell)")

SPACE_ID = "konatos/etf-backtest"
BASE = "c:/Users/F/Desktop/fund_backtest"

# 需要上传的所有文件（包含 Dockerfile 和 README）
files = [
    "app.py",           # 主程序（HF Spaces Streamlit SDK 默认入口）
    "data_fetcher.py",
    "backtest.py",
    "metrics.py",
    "charts.py",
    "requirements.txt",
    "streamlit_app.py", # 备选入口
    "README.md",        # Space 的首页说明
]

api = HfApi()

print("=" * 50)
print(f"上传文件到 Space: {SPACE_ID}")
print("=" * 50)

for fname in files:
    path = os.path.join(BASE, fname)
    if not os.path.exists(path):
        print(f"⚠️ {fname} 不存在，跳过")
        continue
    try:
        api.upload_file(
            path_or_fileobj=path,
            path_in_repo=fname,
            repo_id=SPACE_ID,
            repo_type="space",
            token=TOKEN,
        )
        print(f"✅ {fname} 上传成功")
    except Exception as e:
        print(f"❌ {fname} 上传失败: {e}")

print("\n" + "=" * 50)
print("全部完成！")
print("")
print("=" * 50)