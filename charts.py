"""
可视化图表模块 — 收益额曲线 + 收益率曲线（仅2张图，不可拖拽）
支持基准对比（沪深300 / 标普500 等）
所有数值保留小数点后2位
"""

import plotly.graph_objects as go
import pandas as pd


def _calc_daily_change(series: pd.Series) -> pd.Series:
    """计算每日变化量（当日收益/收益率），结果精确到2位小数"""
    result = pd.Series(0.0, index=series.index)
    diff = series.iloc[1:].values - series.iloc[:-1].values
    result.iloc[1:] = [round(float(v), 2) for v in diff]
    return result


def _normalize_benchmark(benchmark_df: pd.DataFrame, portfolio_dates: pd.Series) -> pd.DataFrame:
    """将基准数据对齐到组合日期范围，并归一化到起始值为0%收益率"""
    if benchmark_df is None or benchmark_df.empty:
        return None
    bm = benchmark_df.copy()
    bm["date"] = pd.to_datetime(bm["date"])
    start = portfolio_dates.min()
    end = portfolio_dates.max()
    bm = bm[(bm["date"] >= start) & (bm["date"] <= end)].reset_index(drop=True)
    if bm.empty:
        return None
    first_close = bm["close"].iloc[0]
    if first_close <= 0:
        return None
    bm["return_rate"] = (bm["close"] / first_close - 1) * 100
    return bm[["date", "close", "return_rate"]]


def _align_to_portfolio_dates(benchmark_df: pd.DataFrame, portfolio_dates: pd.Series) -> pd.Series:
    """将基准的return_rate对齐到组合的日期序列（向后填充）"""
    if benchmark_df is None:
        return None
    bm = benchmark_df.set_index("date")["return_rate"]
    aligned = bm.reindex(portfolio_dates).ffill()
    return aligned.bfill()


def plot_profit_curve(
    portfolio_df: pd.DataFrame,
    benchmark_label: str = None,
    benchmark_df: pd.DataFrame = None,
    title: str = "收益额曲线",
    total_investment: float = 100000,
) -> go.Figure:
    """收益额随时间曲线，可选叠加基准对比"""
    fig = go.Figure()
    profit = [round(float(v), 2) for v in (portfolio_df["hold_value"] - portfolio_df["total_cost"])]
    daily_profit = _calc_daily_change(portfolio_df["hold_value"] - portfolio_df["total_cost"])
    daily_profit_list = [round(float(v), 2) for v in daily_profit]

    # 累计收益曲线（hover时显示当日收益额）
    fig.add_trace(go.Scatter(
        x=portfolio_df["date"], y=profit,
        mode="lines", name="累计收益额",
        line=dict(color="#2962FF", width=2),
        fill="tozeroy", fillcolor="rgba(41, 98, 255, 0.05)",
        customdata=list(zip(daily_profit_list)),
        hovertemplate=(
            "<b>%{x|%Y-%m-%d}</b><br>" +
            "累计收益额: %{y:+,.2f}元<br>" +
            "当日收益额: %{customdata[0]:+,.2f}元<br>" +
            "<extra></extra>"
        ),
    ))

    # 基准对比线
    if benchmark_label and benchmark_df is not None:
        aligned_bm_return = _align_to_portfolio_dates(benchmark_df, portfolio_df["date"])
        if aligned_bm_return is not None:
            bm_profit = [round(float(v) / 100 * total_investment, 2) for v in aligned_bm_return]
            bm_daily_profit = _calc_daily_change(pd.Series(bm_profit))
            bm_daily_profit_list = [round(float(v), 2) for v in bm_daily_profit]
            out_perform = [round(float(p) - float(b), 2) for p, b in zip(profit, bm_profit)]

            fig.add_trace(go.Scatter(
                x=portfolio_df["date"], y=bm_profit,
                mode="lines", name=benchmark_label,
                line=dict(color="#FF9800", width=2, dash="dash"),
                customdata=list(zip(bm_daily_profit_list)),
                hovertemplate="<b>%{x|%Y-%m-%d}</b><br>" +
                              f"{benchmark_label}累计收益额: %{{y:+,.2f}}元<br>" +
                              "基准当日收益额: %{customdata[0]:+,.2f}元<br>" +
                              "<extra></extra>",
            ))

            # 跑赢基准曲线（默认隐藏）
            fig.add_trace(go.Scatter(
                x=portfolio_df["date"], y=out_perform,
                mode="lines", name=f"跑赢{benchmark_label}",
                line=dict(color="#9C27B0", width=1.5, dash="dot"),
                yaxis="y3",
                hovertemplate="<b>%{x|%Y-%m-%d}</b><br>" +
                              f"跑赢{benchmark_label}: %{{y:+,.2f}}元<br>" +
                              "<extra></extra>",
                visible="legendonly",
            ))

    fig.update_layout(
        title=dict(text=title, x=0.5),
        xaxis=dict(title=None, tickformat="%Y-%m", showgrid=False, zeroline=False),
        yaxis=dict(title=None, tickformat=",.2f", showgrid=True, gridcolor="rgba(0,0,0,0.06)",
                   zeroline=True, zerolinecolor="rgba(0,0,0,0.15)"),
        yaxis2=dict(title=None, tickformat=",.2f", overlaying="y", side="right",
                    showgrid=False, zeroline=False, showticklabels=False),
        yaxis3=dict(title=None, tickformat=",.2f", overlaying="y", side="right",
                    showgrid=False, zeroline=False, showticklabels=False,
                    position=0.98),
        hovermode="x unified",
        hoverdistance=10,
        hoverlabel=dict(bgcolor="white", font_size=12, namelength=-1),
        margin=dict(l=40, r=50, t=40, b=30),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        dragmode=False, height=380,
        font=dict(size=12),
        legend=dict(orientation="h", y=1.08, x=0.5, xanchor="center"),
    )

    return fig


def plot_return_rate_curve(
    portfolio_df: pd.DataFrame,
    benchmark_label: str = None,
    benchmark_df: pd.DataFrame = None,
    title: str = "收益率曲线",
) -> go.Figure:
    """收益率随时间曲线，可选叠加基准对比"""
    fig = go.Figure()
    return_rate = [round(float(v), 2) for v in portfolio_df["return_rate"]]
    daily_return = _calc_daily_change(portfolio_df["return_rate"])
    daily_return_list = [round(float(v), 2) for v in daily_return]

    # 累计收益率曲线（hover时显示当日收益率）
    fig.add_trace(go.Scatter(
        x=portfolio_df["date"], y=return_rate,
        mode="lines", name="累计收益率",
        line=dict(color="#66BB6A", width=2),
        fill="tozeroy", fillcolor="rgba(102, 187, 106, 0.05)",
        customdata=list(zip(daily_return_list)),
        hovertemplate=(
            "<b>%{x|%Y-%m-%d}</b><br>" +
            "累计收益率: %{y:.2f}%<br>" +
            "当日收益率: %{customdata[0]:+.2f}%<br>" +
            "<extra></extra>"
        ),
    ))

    # 基准对比线
    if benchmark_label and benchmark_df is not None:
        aligned_bm_return = _align_to_portfolio_dates(benchmark_df, portfolio_df["date"])
        if aligned_bm_return is not None:
            bm_rates = [round(float(v), 2) for v in aligned_bm_return]
            bm_daily_return = _calc_daily_change(pd.Series(bm_rates))
            bm_daily_return_list = [round(float(v), 2) for v in bm_daily_return]
            out_perform = [round(float(p) - float(b), 2) for p, b in zip(return_rate, bm_rates)]

            fig.add_trace(go.Scatter(
                x=portfolio_df["date"], y=bm_rates,
                mode="lines", name=benchmark_label,
                line=dict(color="#FF9800", width=2, dash="dash"),
                customdata=list(zip(bm_daily_return_list)),
                hovertemplate="<b>%{x|%Y-%m-%d}</b><br>" +
                              f"{benchmark_label}累计收益率: %{{y:.2f}}%<br>" +
                              "基准当日收益率: %{customdata[0]:+.2f}%<br>" +
                              "<extra></extra>",
            ))

            # 跑赢基准（默认隐藏）
            fig.add_trace(go.Scatter(
                x=portfolio_df["date"], y=out_perform,
                mode="lines", name=f"跑赢{benchmark_label}",
                line=dict(color="#9C27B0", width=1.5, dash="dot"),
                yaxis="y3",
                hovertemplate="<b>%{x|%Y-%m-%d}</b><br>" +
                              f"跑赢{benchmark_label}: %{{y:+.2f}}%<br>" +
                              "<extra></extra>",
                visible="legendonly",
            ))

    fig.update_layout(
        title=dict(text=title, x=0.5),
        xaxis=dict(title=None, tickformat="%Y-%m", showgrid=False, zeroline=False),
        yaxis=dict(title=None, tickformat=".2f", showgrid=True, gridcolor="rgba(0,0,0,0.06)",
                   zeroline=True, zerolinecolor="rgba(0,0,0,0.15)"),
        yaxis2=dict(title=None, tickformat=".2f", overlaying="y", side="right",
                    showgrid=False, zeroline=False, showticklabels=False),
        yaxis3=dict(title=None, tickformat=".2f", overlaying="y", side="right",
                    showgrid=False, zeroline=False, showticklabels=False,
                    position=0.98),
        hovermode="x unified",
        hoverdistance=10,
        hoverlabel=dict(bgcolor="white", font_size=12, namelength=-1),
        margin=dict(l=40, r=50, t=40, b=30),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        dragmode=False, height=380,
        font=dict(size=12),
        legend=dict(orientation="h", y=1.08, x=0.5, xanchor="center"),
    )

    return fig