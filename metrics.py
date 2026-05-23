"""
指标计算模块：收益率、年化收益、最大回撤、夏普比率等
"""

import pandas as pd
import numpy as np


def calculate_cagr(total_return_rate: float, years: float) -> float:
    """
    计算年化复合收益率 (CAGR)

    参数:
        total_return_rate: 总收益率（百分比，如 25 表示 25%）
        years: 持有年限

    返回:
        年化收益率百分比
    """
    if years <= 0:
        return 0.0
    total_return_decimal = total_return_rate / 100.0
    cagr = (1 + total_return_decimal) ** (1 / years) - 1
    return cagr * 100


def calculate_max_drawdown(hold_values: pd.Series) -> float:
    """
    计算最大回撤

    参数:
        hold_values: 持仓市值序列

    返回:
        最大回撤百分比（正数，如 15.5 表示回撤15.5%）
    """
    if hold_values.empty:
        return 0.0

    # 计算运行峰值
    running_max = hold_values.cummax()
    # 计算从峰值回撤
    drawdown = (hold_values - running_max) / running_max
    max_dd = drawdown.min()
    return abs(max_dd) * 100


def calculate_sharpe_ratio(return_rates: pd.Series, risk_free_rate: float = 0.02) -> float:
    """
    计算夏普比率 (Sharpe Ratio)

    参数:
        return_rates: 每日收益率序列（百分比格式，如 0.5 表示0.5%）
        risk_free_rate: 年化无风险利率，默认 2%

    返回:
        夏普比率（年化）
    """
    if return_rates.empty or len(return_rates) < 2:
        return 0.0

    # 确保使用小数形式计算
    daily_rf = risk_free_rate / 252  # 年化转日化
    excess_returns = return_rates / 100.0 - daily_rf

    if excess_returns.std() == 0:
        return 0.0

    sharpe_daily = excess_returns.mean() / excess_returns.std()
    # 年化夏普
    sharpe_annual = sharpe_daily * np.sqrt(252)
    return round(sharpe_annual, 4)


def compute_all_metrics(result_df: pd.DataFrame) -> dict:
    """
    计算所有回测指标

    参数:
        result_df: 回测结果 DataFrame (包含 date, hold_value, total_cost, return_rate)

    返回:
        字典包含各项指标
    """
    if result_df.empty:
        return {}

    # 最终数据
    final_hold_value = result_df["hold_value"].iloc[-1]
    total_cost = result_df["total_cost"].iloc[-1]
    final_return_rate = result_df["return_rate"].iloc[-1]

    # 持有年限
    start_date = result_df["date"].iloc[0]
    end_date = result_df["date"].iloc[-1]
    years = (end_date - start_date).days / 365.25

    # 年化收益
    cagr = calculate_cagr(final_return_rate, years)

    # 最大回撤
    max_dd = calculate_max_drawdown(result_df["hold_value"])

    # 每日收益率（用于夏普比率）
    result_df = result_df.copy()
    result_df["daily_return"] = result_df["close"].pct_change() * 100
    daily_returns = result_df["daily_return"].dropna()

    # 夏普比率（用持仓市值的每日变化，而非单纯价格）
    result_df["hold_daily_return"] = result_df["hold_value"].pct_change() * 100
    hold_daily_returns = result_df["hold_daily_return"].dropna()

    sharpe = calculate_sharpe_ratio(hold_daily_returns)

    # 投入本金总额
    total_invested = result_df["total_cost"].iloc[-1]

    # 盈亏金额
    profit = final_hold_value - total_invested

    return {
        "总收益率 (%)": round(final_return_rate, 2),
        "年化收益率 (CAGR, %)": round(cagr, 2),
        "最大回撤 (%)": round(max_dd, 2),
        "夏普比率": sharpe,
        "总投入 (元)": round(total_invested, 2),
        "最终市值 (元)": round(final_hold_value, 2),
        "盈亏金额 (元)": round(profit, 2),
        "持有年限": round(years, 2),
        "交易日数": len(result_df),
    }