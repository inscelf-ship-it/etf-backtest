"""
上传文件到 ModelScope Space（魔搭社区，国内直接访问）
使用方式：
  1. 在 https://modelscope.cn 注册账号
  2. 创建 Space：选择 "创建Space"，填名称(如 etf-backtest)，SDK 选 Streamlit
  3. 获取你的 Access Token：https://modelscope.cn/my/myaccesstoken
  4. 运行脚本：
     $env:MODELSCOPE_TOKEN="你的token"; python modelscope_upload.py
"""
import os
import json
import urllib.request
import urllib.parse
import urllib.error
import pathlib

TOKEN = os.environ.get("MODELSCOPE_TOKEN")
if not TOKEN:
    raise ValueError("请设置环境变量 MODELSCOPE_TOKEN，例如: $env:MODELSCOPE_TOKEN='你的token'")

# === 修改为你的 ModelScope Space ID ===
# 格式: "username/space-name"  (你的魔搭用户名/创建的Space名)
SPACE_ID = "konatos/etf-backtest"  # ⚠️ 请修改为实际值

BASE = "C:/Users/F/Desktop/fund_backtest"

# 需要上传的文件
files = [
    "app.py",
    "data_fetcher.py",
    "backtest.py",
    "charts.py",
    "requirements.txt",
    "streamlit_app.py",
    "README.md",
]

# ModelScope API endpoint
API_BASE = "https://www.modelscope.cn/api/v1"

def upload_file_to_modelscope(local_path, remote_path):
    """使用 multipart/form-data 上传文件到 ModelScope Space"""
    import requests

    url = f"{API_BASE}/spaces/{SPACE_ID}/upload"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
    }

    with open(local_path, "rb") as f:
        files = {
            "file": (remote_path, f, "application/octet-stream"),
        }
        resp = requests.post(url, headers=headers, files=files, timeout=60)

    if resp.status_code in (200, 201):
        return True
    else:
        print(f"  响应: {resp.status_code} {resp.text[:200]}")
        return False


def create_space_if_not_exists():
    """尝试获取 Space 信息，如果不存在则创建"""
    import requests

    url = f"{API_BASE}/spaces/{SPACE_ID}"
    headers = {"Authorization": f"Bearer {TOKEN}"}
    resp = requests.get(url, headers=headers, timeout=15)

    if resp.status_code == 200:
        print(f"✅ Space {SPACE_ID} 已存在")
        return True
    elif resp.status_code == 404:
        print(f"⚠️ Space {SPACE_ID} 不存在，请先在网页端创建")
        print(f"   访问 https://modelscope.cn/create/space")
        return False
    else:
        print(f"⚠️ 检查 Space 出错: {resp.status_code} {resp.text[:200]}")
        return False


def main():
    print("=" * 50)
    print(f"上传文件到 ModelScope Space: {SPACE_ID}")
    print("=" * 50)

    # 检查 modelscope 依赖
    try:
        import requests
    except ImportError:
        print("❌ 需要安装 requests: pip install requests")
        return

    # 检查 Space 是否存在（可选）
    exists = create_space_if_not_exists()
    if not exists:
        print("⚠️ 请先在浏览器中创建 Space，然后再运行上传脚本")
        print("   步骤：")
        print("   1. 登录 https://modelscope.cn")
        print("   2. 点击头像 → '我的Space' → '创建Space'")
        print("   3. 填入名称(如 etf-backtest)，SDK 选择 Streamlit")
        print("   4. 创建完成后，修改此脚本中的 SPACE_ID")
        return

    success_count = 0
    fail_count = 0

    for fname in files:
        path = os.path.join(BASE, fname)
        if not os.path.exists(path):
            print(f"⚠️ {fname} 不存在，跳过")
            continue
        print(f"📤 上传 {fname}...", end=" ")
        try:
            ok = upload_file_to_modelscope(path, fname)
            if ok:
                print("✅")
                success_count += 1
            else:
                print("❌ 失败")
                fail_count += 1
        except Exception as e:
            print(f"❌ 异常: {e}")
            fail_count += 1

    print("\n" + "=" * 50)
    print(f"完成！成功: {success_count}, 失败: {fail_count}")
    if success_count > 0:
        print(f"\n🔗 访问地址: https://modelscope.cn/spaces/{SPACE_ID}")
        print("\n⚠️ 首次部署可能需要 1-3 分钟构建")


if __name__ == "__main__":
    main()