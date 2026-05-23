"""
回测引擎模块：支持等额定投和一次性投入两种策略
"""

import pandas as pd
import numpy as np
from typing import Optional


def backtest_lump_sum(
    df: pd.DataFrame,
    invest_amount: float,
) -> pd.DataFrame:
    """
    一次性投入策略回测

    参数:
        df: 历史数据 DataFrame (必须包含 date, close 列)
        invest_amount: 投入总金额

    返回:
        DataFrame 包含每日持仓市值、累计收益率等
    """
    if df.empty or "close" not in df.columns:
        raise ValueError("数据为空或缺少 close 列")

    result = df[["date", "close"]].copy()

    # 首日买入份额
    first_price = result["close"].iloc[0]
    shares = invest_amount / first_price

    # 每日持仓市值
    result["hold_value"] = result["close"] * shares
    result["total_cost"] = invest_amount
    result["return_rate"] = (result["hold_value"] / invest_amount - 1) * 100

    return result


def backtest_dca(
    df: pd.DataFrame,
    monthly_amount: float,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    dca_day: int = 1,
) -> pd.DataFrame:
    """
    等额定投策略回测（按月定投）

    参数:
        df: 历史数据 DataFrame (必须包含 date, close 列)
        monthly_amount: 每月定投金额
        start_date: 定投开始日期 (YYYY-MM-DD)，默认从数据第一天开始
        end_date: 定投结束日期 (YYYY-MM-DD)，默认到最后一天
        dca_day: 每月定投日（几号），默认1号

    返回:
        DataFrame 包含每日持仓市值、累计投入、累计收益率等
    """
    if df.empty or "close" not in df.columns:
        raise ValueError("数据为空或缺少 close 列")

    result = df[["date", "close"]].copy()

    # 过滤时间范围
    if start_date:
        result = result[result["date"] >= pd.Timestamp(start_date)].reset_index(drop=True)
    if end_date:
        result = result[result["date"] <= pd.Timestamp(end_date)].reset_index(drop=True)

    if result.empty:
        raise ValueError("指定时间范围内无数据")

    result["year"] = result["date"].dt.year
    result["month"] = result["date"].dt.month

    # 计算每个定投日的买入
    total_shares = 0.0
    total_cost = 0.0
    hold_values = []
    costs = []

    # 按年月分组，找到每月定投日或最近交易日
    monthly_groups = result.groupby(["year", "month"])

    for (year, month), group in monthly_groups:
        # 尝试找到定投日当天或之后的第一个交易日
        target_day = pd.Timestamp(year=year, month=month, day=dca_day)

        # 找定投日当天或之后的第一个交易日
        invest_day = group[group["date"] >= target_day]
        if invest_day.empty:
            # 如果定投日之后没有交易日，取当月最后一个交易日
            invest_row = group.iloc[-1]
        else:
            invest_row = invest_day.iloc[0]

        price = invest_row["close"]
        if pd.notna(price) and price > 0:
            shares_bought = monthly_amount / price
            total_shares += shares_bought
            total_cost += monthly_amount

        # 记录每日持仓（针对该分组中每一天）
        for idx in group.index:
            close_price = result.loc[idx, "close"]
            if pd.notna(close_price) and close_price > 0:
                hold_values.append(close_price * total_shares)
            else:
                hold_values.append(0.0)
            costs.append(total_cost)

    result["hold_value"] = hold_values
    result["total_cost"] = costs
    result["return_rate"] = np.where(
        result["total_cost"] > 0,
        (result["hold_value"] / result["total_cost"] - 1) * 100,
        0.0,
    )

    return result[["date", "close", "hold_value", "total_cost", "return_rate"]]