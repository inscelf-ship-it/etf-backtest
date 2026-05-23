"""
可视化图表模块：使用 plotly 创建交互式图表
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


def plot_return_rate_curve(result_df: pd.DataFrame, title: str = "收益率曲线") -> go.Figure:
    """
    绘制收益率曲线图

    参数:
        result_df: 回测结果 DataFrame
        title: 图表标题

    返回:
        plotly Figure 对象
    """
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=result_df["date"],
            y=result_df["return_rate"],
            mode="lines",
            name="累计收益率",
            line=dict(color="#00BFFF", width=2),
            hovertemplate="日期: %{x|%Y-%m-%d}<br>收益率: %{y:.2f}%<extra></extra>",
        )
    )

    # 添加零线
    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="gray",
        opacity=0.5,
    )

    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=18)),
        xaxis_title="日期",
        yaxis_title="累计收益率 (%)",
        hovermode="x unified",
        template="plotly_white",
        height=500,
        xaxis=dict(rangeslider=dict(visible=True), type="date"),
        yaxis=dict(tickformat=".2f", ticksuffix="%"),
    )

    return fig


def plot_asset_comparison(result_df: pd.DataFrame) -> go.Figure:
    """
    绘制持仓市值 vs 累计投入对比图

    参数:
        result_df: 回测结果 DataFrame

    返回:
        plotly Figure 对象
    """
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=result_df["date"],
            y=result_df["hold_value"],
            mode="lines",
            name="持仓市值",
            line=dict(color="#FF6B6B", width=2),
            fill="tozeroy",
            fillcolor="rgba(255, 107, 107, 0.1)",
            hovertemplate="日期: %{x|%Y-%m-%d}<br>市值: ¥%{y:.2f}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=result_df["date"],
            y=result_df["total_cost"],
            mode="lines",
            name="累计投入",
            line=dict(color="#4ECDC4", width=2, dash="dash"),
            hovertemplate="日期: %{x|%Y-%m-%d}<br>投入: ¥%{y:.2f}<extra></extra>",
        )
    )

    fig.update_layout(
        title=dict(text="持仓市值 vs 累计投入", x=0.5, font=dict(size=18)),
        xaxis_title="日期",
        yaxis_title="金额 (元)",
        hovermode="x unified",
        template="plotly_white",
        height=450,
        xaxis=dict(rangeslider=dict(visible=True), type="date"),
        yaxis=dict(tickformat=","),
    )

    return fig


def plot_drawdown(result_df: pd.DataFrame) -> go.Figure:
    """
    绘制回撤曲线图

    参数:
        result_df: 回测结果 DataFrame

    返回:
        plotly Figure 对象
    """
    # 计算每日回撤
    running_max = result_df["hold_value"].cummax()
    drawdown = (result_df["hold_value"] - running_max) / running_max * 100

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=result_df["date"],
            y=drawdown,
            mode="lines",
            name="回撤",
            line=dict(color="#FF4757", width=1.5),
            fill="tozeroy",
            fillcolor="rgba(255, 71, 87, 0.15)",
            hovertemplate="日期: %{x|%Y-%m-%d}<br>回撤: %{y:.2f}%<extra></extra>",
        )
    )

    fig.update_layout(
        title=dict(text="回撤曲线", x=0.5, font=dict(size=18)),
        xaxis_title="日期",
        yaxis_title="回撤 (%)",
        hovermode="x unified",
        template="plotly_white",
        height=350,
        xaxis=dict(rangeslider=dict(visible=False), type="date"),
        yaxis=dict(tickformat=".2f", ticksuffix="%", autorange="reversed"),
    )

    return fig


def create_dashboard(result_df: pd.DataFrame, title: str = "回测结果") -> go.Figure:
    """
    创建综合仪表盘（子图组合）

    参数:
        result_df: 回测结果 DataFrame
        title: 总标题

    返回:
        plotly Figure 对象（含多个子图）
    """
    # 计算回撤
    running_max = result_df["hold_value"].cummax()
    drawdown = (result_df["hold_value"] - running_max) / running_max * 100

    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=("累计收益率", "持仓市值 vs 累计投入", "回撤曲线"),
        row_heights=[0.4, 0.35, 0.25],
    )

    # 收益率曲线
    fig.add_trace(
        go.Scatter(
            x=result_df["date"],
            y=result_df["return_rate"],
            mode="lines",
            name="累计收益率",
            line=dict(color="#00BFFF", width=2),
            hovertemplate="日期: %{x|%Y-%m-%d}<br>收益率: %{y:.2f}%<extra></extra>",
        ),
        row=1,
        col=1,
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.3, row=1, col=1)

    # 市值 vs 投入
    fig.add_trace(
        go.Scatter(
            x=result_df["date"],
            y=result_df["hold_value"],
            mode="lines",
            name="持仓市值",
            line=dict(color="#FF6B6B", width=2),
            fill="tozeroy",
            fillcolor="rgba(255, 107, 107, 0.05)",
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=result_df["date"],
            y=result_df["total_cost"],
            mode="lines",
            name="累计投入",
            line=dict(color="#4ECDC4", width=2, dash="dash"),
        ),
        row=2,
        col=1,
    )

    # 回撤曲线
    fig.add_trace(
        go.Scatter(
            x=result_df["date"],
            y=drawdown,
            mode="lines",
            name="回撤",
            line=dict(color="#FF4757", width=1.5),
            fill="tozeroy",
            fillcolor="rgba(255, 71, 87, 0.1)",
        ),
        row=3,
        col=1,
    )

    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=20)),
        template="plotly_white",
        height=900,
        hovermode="x unified",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    )

    fig.update_xaxes(rangeslider=dict(visible=False), row=3, col=1)
    fig.update_yaxes(tickformat=".2f", ticksuffix="%", row=1, col=1)
    fig.update_yaxes(tickformat=",", row=2, col=1)
    fig.update_yaxes(tickformat=".2f", ticksuffix="%", autorange="reversed", row=3, col=1)

    return fig