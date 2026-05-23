---
title: ETF 组合定投回测工具
emoji: 📊
colorFrom: blue
colorTo: indigo
sdk: streamlit
sdk_version: 1.28.0
app_file: app.py
pinned: false
license: mit
---

# 📊 ETF / 基金数据回测工具

一个基于 Streamlit 的在线 ETF 回测工具，支持**多标的组合比例定投**策略。

## 🚀 在线体验

[![Hugging Face Spaces](https://img.shields.io/badge/%F0%9F%A4%97-Hugging%20Face%20Spaces-blue)](https://huggingface.co/spaces/konatos/etf-backtest)

## ✨ 功能

- **多标的组合定投**：最多同时回测 10 个标的
- **自定义权重**：灵活调整各标的资金分配比例
- **18个热门ETF**：沪深300、中证500、纳指、黄金等
- **任意金额**：自定义投入金额和定投次数
- **灵活时间范围**：支持任意起止日期
- **核心指标**：总收益率、年化CAGR、最大回撤、夏普比率
- **交互式图表**：收益率曲线、持仓对比、回撤曲线（Plotly）
- **数据导出**：支持 CSV 下载

## 🛠 本地运行

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 🌐 部署到 Hugging Face Spaces（国内可访问，免费）

### 前提
1. 注册 [Hugging Face](https://huggingface.co) 账号

### 部署步骤

1. **创建 Space**
   - 登录 Hugging Face
   - 点击右上角头像 → **"New Space"**
   - 填写：
     - **Space Name**: `etf-backtest`
     - **License**: 选择 `MIT`
     - **SDK**: 选择 **Streamlit**
     - **Space Hardware**: 选择 **CPU basic**（免费）
   - 点击 **"Create Space"**

2. **上传代码**
   - 在 Space 页面中，点击 **"Files"** 选项卡
   - 点击 **"Add file"** → **"Upload files"**
   - 拖拽或选择所有 `.py` 文件和 `requirements.txt` 上传

3. **或者使用命令上传**
   ```bash
   pip install huggingface_hub
   python hf_upload.py
   ```

4. **等待部署完成**（约2-5分钟）
   - 访问：`https://konatos-etf-backtest.hf.space`

### ⚠️ 重要：如果页面显示 Welcome

如果部署完成后页面仍然显示 Hugging Face 的欢迎页面，请按以下步骤排查：

1. **检查 Space 设置**
   - 点击 Space 页面顶部的 **Settings** ⚙️ 标签
   - 确认 **SDK** 选择为 **Streamlit**
   - 确认 **App file** 填写为 `app.py`

2. **手动重启**
   - 点击右上角的 **⋮** (更多) 菜单
   - 选择 **"Restart this Space"**

3. **查看构建日志**
   - 点击 **"Factory"** 或 **"Builder"** 标签
   - 查看最新构建的输出，检查是否有报错

4. **删除 Dockerfile（如存在）**
   - 如果 Space 有 Dockerfile，HF 会尝试用 Docker 构建
   - 建议：在 Space 的 **Settings** 中将 SDK 设为 **Streamlit**，HF 会自动忽略 Dockerfile

## 📁 项目结构

```
fund_backtest/
├── app.py              # Streamlit 主界面（HF Spaces 入口）
├── data_fetcher.py     # 数据获取（akshare）
├── backtest.py         # 回测引擎（定投 + 一次性）
├── metrics.py          # 指标计算
├── charts.py           # 可视化图表（Plotly）
├── streamlit_app.py    # 备选入口（streamlit_app.py → app.main()）
├── hf_upload.py        # HF Spaces 上传脚本
├── requirements.txt    # Python 依赖
├── Dockerfile          # Docker 部署配置（可选）
└── README.md           # 本文件