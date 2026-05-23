# 📊 ETF / 基金数据回测工具

一个基于 Streamlit 的在线 ETF 回测工具，支持**多标的组合比例定投**策略。

## 🚀 在线体验

[![Hugging Face Spaces](https://img.shields.io/badge/%F0%9F%A4%97-Hugging%20Face%20Spaces-blue)](https://huggingface.co/spaces/inscelf-ship-it/etf-backtest)

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
1. 拥有 [GitHub](https://github.com) 账号
2. 注册 [Hugging Face](https://huggingface.co) 账号

### 部署步骤

1. **在 GitHub 创建仓库**，上传本项目所有文件
   - 本项目已托管在 https://github.com/inscelf-ship-it/etf-backtest

2. **登录 Hugging Face**
   - 访问 https://huggingface.co
   - 点击右上角 **"Sign Up"** 注册（可用 GitHub 或 Google 登录）

3. **创建 Space**
   - 点击右上角头像 → **"New Space"**
   - 填写：
     - **Space Name**: `etf-backtest`
     - **License**: 选择 `MIT`
     - **SDK**: 选择 **Streamlit**
   - 在 **"Link GitHub Repository"** 处勾选并输入：
     - `inscelf-ship-it/etf-backtest`
   - 点击底部 **"Create Space"**

4. **等待部署完成**（约2-5分钟）
   - Hugging Face 会自动从 GitHub 拉取代码并部署
   - 部署完成后访问地址为：
     `https://inscelf-ship-it-etf-backtest.hf.space`

## 📁 项目结构

```
fund_backtest/
├── app.py              # Streamlit 主界面
├── data_fetcher.py     # 数据获取（akshare）
├── backtest.py         # 回测引擎（定投 + 一次性）
├── metrics.py          # 指标计算
├── charts.py           # 可视化图表（Plotly）
├── requirements.txt    # Python 依赖
└── README.md           # 本文件