# 📊 ETF / 基金数据回测工具

一个基于 Streamlit 的在线 ETF 回测工具，支持**等额定投**和**一次性投入**两种策略。

## 🚀 在线体验

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://YOUR_USERNAME-etf-backtest.streamlit.app)

## ✨ 功能

- **多策略支持**：等额定投（DCA）、一次性投入
- **18个热门ETF**：沪深300、中证500、纳指、黄金等
- **任意金额**：自定义投入金额
- **灵活时间范围**：支持任意起止日期
- **核心指标**：总收益率、年化CAGR、最大回撤、夏普比率
- **交互式图表**：收益率曲线、持仓对比、回撤曲线（Plotly）
- **数据导出**：支持 CSV 下载

## 🛠 本地运行

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 🌐 部署到 Streamlit Cloud（免费）

### 前提
1. 拥有 [GitHub](https://github.com) 账号
2. 拥有 [Streamlit](https://streamlit.io) 账号（可用 GitHub 登录）

### 部署步骤

1. **在 GitHub 创建仓库**，上传本项目所有文件

2. **登录 Streamlit Cloud**
   - 访问 https://share.streamlit.io
   - 点击 "Create app"
   - 选择你的 GitHub 仓库
   - 填写：
     - **Repository**: `你的用户名/仓库名`
     - **Branch**: `main`
     - **Main file path**: `app.py`
   - 点击 "Deploy"

3. **等待部署完成**（约2-5分钟）
   - 首次部署会安装依赖，后续启动更快

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