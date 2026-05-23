"""
可视化图表模块：使用 plotly 创建交互式图表（多标的组合版）
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np


def create_portfolio_dashboard(
    portfolio_df: pd.DataFrame,
    asset_details: dict,
    title: str = "组合回测结果",
) -> go.Figure:
    """
    创建组合综合仪表盘

    参数:
        portfolio_df: 组合每日数据 (date, hold_value, total_cost, return_rate, drawdown)
        asset_details: {标的名称: DataFrame(每日明细)}
        title: 总标题

    返回:
        plotly Figure 对象
    """
    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        subplot_titles=(
            "组合累计收益率",
            "组合持仓市值 vs 累计投入",
            "回撤曲线",
            "各标的累计收益率对比",
        ),
        row_heights=[0.3, 0.25, 0.2, 0.25],
    )

    # 颜色方案
    colors = [
        "#00BFFF", "#FF6B6B", "#4ECDC4", "#FFD93D",
        "#6C5CE7", "#A8E6CF", "#FF8A5C", "#3DC1D3",
        "#E77F67", "#786FA6", "#F3A683",
    ]

    # ---- 子图1: 组合收益率 ----
    fig.add_trace(
        go.Scatter(
            x=portfolio_df["date"],
            y=portfolio_df["return_rate"],
            mode="lines",
            name="组合收益率",
            line=dict(color="#00BFFF", width=2.5),
            hovertemplate="日期: %{x|%Y-%m-%d}<br>收益率: %{y:.2f}%<extra></extra>",
        ),
        row=1, col=1,
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.3, row=1, col=1)

    # ---- 子图2: 市值 vs 投入 ----
    fig.add_trace(
        go.Scatter(
            x=portfolio_df["date"],
            y=portfolio_df["hold_value"],
            mode="lines",
            name="持仓市值",
            line=dict(color="#FF6B6B", width=2),
            fill="tozeroy",
            fillcolor="rgba(255, 107, 107, 0.05)",
            hovertemplate="日期: %{x|%Y-%m-%d}<br>市值: ¥%{y:.2f}<extra></extra>",
        ),
        row=2, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=portfolio_df["date"],
            y=portfolio_df["total_cost"],
            mode="lines",
            name="累计投入",
            line=dict(color="#4ECDC4", width=2, dash="dash"),
            hovertemplate="日期: %{x|%Y-%m-%d}<br>投入: ¥%{y:.2f}<extra></extra>",
        ),
        row=2, col=1,
    )

    # ---- 子图3: 回撤 ----
    if "drawdown" in portfolio_df.columns:
        fig.add_trace(
            go.Scatter(
                x=portfolio_df["date"],
                y=portfolio_df["drawdown"],
                mode="lines",
                name="回撤",
                line=dict(color="#FF4757", width=1.5),
                fill="tozeroy",
                fillcolor="rgba(255, 71, 87, 0.1)",
                hovertemplate="日期: %{x|%Y-%m-%d}<br>回撤: %{y:.2f}%<extra></extra>",
            ),
            row=3, col=1,
        )

    # ---- 子图4: 各标的收益率对比 ----
    for i, (asset_name, df) in enumerate(asset_details.items()):
        color = colors[i % len(colors)]
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["return_rate"],
                mode="lines",
                name=asset_name,
                line=dict(color=color, width=1.5),
                hovertemplate=f"{asset_name}<br>日期: %{{x|%Y-%m-%d}}<br>收益率: %{{y:.2f}}%<extra></extra>",
            ),
            row=4, col=1,
        )

    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=20)),
        template="plotly_white",
        height=1100,
        hovermode="x unified",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(size=10)),
    )

    fig.update_xaxes(rangeslider=dict(visible=False), row=4, col=1)
    fig.update_yaxes(tickformat=".2f", ticksuffix="%", row=1, col=1)
    fig.update_yaxes(tickformat=",", row=2, col=1)
    fig.update_yaxes(tickformat=".2f", ticksuffix="%", autorange="reversed", row=3, col=1)
    fig.update_yaxes(tickformat=".2f", ticksuffix="%", row=4, col=1)

    return fig


def plot_asset_radar(asset_final: dict) -> go.Figure:
    """
    绘制各标的收益-风险雷达图（年化收益 vs 最大回撤）
    """
    names = []
    returns = []
    drawdowns = []
    weights = []

    for name, info in asset_final.items():
        names.append(name.split("(")[0])
        returns.append(info["年化收益率%"])
        drawdowns.append(info["最大回撤%"])
        weights.append(info["权重%"])

    fig = go.Figure()

    for i, name in enumerate(names):
        color = colors_list[i % len(colors_list)]
        # 收益/回撤散点
        fig.add_trace(
            go.Scatter(
                x=[drawdowns[i]],
                y=[returns[i]],
                mode="markers+text",
                marker=dict(
                    size=weights[i] * 2 + 10,
                    color=color,
                    line=dict(width=2, color="white"),
                    sizemin=15,
                ),
                text=name,
                textposition="top center",
                name=name,
                hovertemplate=f"{names[i]}<br>权重: {weights[i]}%<br>年化收益: {returns[i]:.1f}%<br>最大回撤: {drawdowns[i]:.1f}%<extra></extra>",
            )
        )

    fig.update_layout(
        title=dict(text="各标的 收益 vs 风险（气泡大小=权重）", x=0.5, font=dict(size=16)),
        xaxis_title="最大回撤 (%)",
        yaxis_title="年化收益率 (%)",
        template="plotly_white",
        height=500,
        hovermode="closest",
        showlegend=False,
    )

    return fig


colors_list = [
    "#00BFFF", "#FF6B6B", "#4ECDC4", "#FFD93D",
    "#6C5CE7", "#A8E6CF", "#FF8A5C", "#3DC1D3",
    "#E77F67", "#786FA6",
]