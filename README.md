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

| 平台 | 链接 | 中国大陆访问 |
|------|------|-------------|
| 🇨🇳 **ModelScope (推荐)** | [→ 立即使用](https://www.modelscope.cn/studios/konatos/etf-backtest) | ✅ **无需 VPN，直连** |
| 🌐 Hugging Face | [→ 备用链接](https://huggingface.co/spaces/konatos/etf-backtest) | ❌ 需要 VPN |

> 💡 **中国大陆用户推荐使用 ModelScope**，无需任何网络工具即可流畅访问。

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

## 🌐 部署说明

### 🇨🇳 部署到 ModelScope（中国大陆推荐）

> ModelScope（魔搭社区）是阿里云旗下的 AI 社区，在中国大陆无需 VPN 即可访问。

#### 前提
1. 注册 [ModelScope](https://www.modelscope.cn) 账号
2. 在 [个人设置页面](https://www.modelscope.cn/settings) 创建 **Access Token**

#### 部署步骤

1. **创建 Space**
   - 登录 ModelScope → 点击头像 → **"我的 Space"**
   - 点击 **"创建 Space"**
   - 填写：
     - **Space 名称**: `etf-backtest`
     - **运行环境**: 选择 **Streamlit**
   - 点击 **"创建"**

2. **Git 推送代码**
   ```bash
   # 添加 ModelScope 远程仓库
   git remote add modelscope https://oauth2:你的token@www.modelscope.cn/studios/konatos/etf-backtest.git

   # 推送代码
   git push modelscope main:master
   ```

3. **等待部署完成**（约 2-5 分钟）
   - 访问：`https://www.modelscope.cn/studios/konatos/etf-backtest`

### 🌐 部署到 Hugging Face Spaces（备用）

#### 前提
1. 注册 [Hugging Face](https://huggingface.co) 账号

#### 部署步骤

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

3. **或者使用脚本上传**
   ```bash
   pip install huggingface_hub
   # 设置你的 HF Token
   $env:HF_TOKEN='你的token'
   python hf_upload.py
   ```

4. **等待部署完成**（约2-5分钟）
   - 访问：`https://konatos-etf-backtest.hf.space`

## 📁 项目结构

```
fund_backtest/
├── app.py              # Streamlit 主界面（入口）
├── data_fetcher.py     # 数据获取（akshare）
├── backtest.py         # 回测引擎（定投 + 一次性）
├── charts.py           # 可视化图表（Plotly）
├── streamlit_app.py    # 备选入口
├── requirements.txt    # Python 依赖
├── Dockerfile          # Docker 配置（可选）
├── hf_upload.py        # Hugging Face 上传脚本
├── ms_upload.py        # ModelScope 上传脚本
└── README.md           # 本文件
```

## 📦 依赖安装

```bash
pip install streamlit pandas numpy plotly akshare
```

## 📄 数据来源

所有行情数据通过 [AKShare](https://akshare.akfamily.xyz/) 获取，数据源来自东方财富、新浪财经等国内主流金融数据平台。