"""
回测引擎模块：支持多标的组合定投/一次性投入
"""

import pandas as pd
import numpy as np
from typing import Optional


def backtest_multi_dca(
    price_dict: dict[str, pd.DataFrame],
    weights: dict[str, float],
    total_investment: float,
    num_installments: int,
    start_date: str,
    end_date: str,
    dca_day: int = 1,
    dca_mode: str = "月度定投",
) -> dict:
    """
    多标的组合定投/一次性投入回测

    参数:
        price_dict: {标的名称: DataFrame(date, close)} 每个标的的价格数据
        weights: {标的名称: 权重(小数)} 权重总和=1
        total_investment: 总资金
        num_installments: 期数（月度/周度定投时有效）
        start_date: 开始日期 YYYY-MM-DD
        end_date: 结束日期 YYYY-MM-DD
        dca_day: 每月定投日（月度模式有效）
        dca_mode: "月度定投" | "周定投" | "一次性投入"

    返回:
        {
            "portfolio": DataFrame(全组合每日市值/收益)
            "assets": {标的名称: DataFrame(该标的每日明细)}
            "summary": 综合指标
        }
    """
    if not price_dict:
        raise ValueError("标的列表为空")
    if len(weights) != len(price_dict):
        raise ValueError("权重数量与标的数量不匹配")
    if abs(sum(weights.values()) - 1.0) > 0.001:
        raise ValueError(f"权重之和必须为100%，当前为 {sum(weights.values())*100:.1f}%")

    start_ts = pd.Timestamp(start_date)
    end_ts = pd.Timestamp(end_date)

    # ========== 对每个标的分别运行 ==========
    asset_results = {}

    for asset_name, df in price_dict.items():
        weight = weights[asset_name]
        # 该标的总资金
        asset_total = total_investment * weight

        df = df.copy()
        df = df[(df["date"] >= start_ts) & (df["date"] <= end_ts)].reset_index(drop=True)
        if df.empty:
            raise ValueError(f"{asset_name} 在指定时间范围内无数据")

        if dca_mode == "一次性投入":
            # 首次交易日一次性买入
            first_valid = df.iloc[0]
            price = first_valid["close"]
            if pd.isna(price) or price <= 0:
                raise ValueError(f"{asset_name} 首日价格无效")
            shares = asset_total / price
            total_shares = shares
            total_cost = asset_total
            hold_values = []
            costs = []
            for idx in df.index:
                close_price = df.loc[idx, "close"]
                if pd.notna(close_price) and close_price > 0:
                    hold_values.append(close_price * total_shares)
                else:
                    hold_values.append(0.0)
                costs.append(total_cost)

            df["hold_value"] = hold_values
            df["total_cost"] = costs
            df["shares"] = [total_shares] * len(df)
            df["return_rate"] = np.where(
                df["total_cost"] > 0,
                (df["hold_value"] / df["total_cost"] - 1) * 100,
                0.0,
            )
            df["asset_weight"] = weight

            asset_results[asset_name] = df[
                ["date", "close", "shares", "hold_value", "total_cost", "return_rate", "asset_weight"]
            ]
            continue

        # 定投模式（月度/周度）
        per_installment = asset_total / num_installments

        if dca_mode == "周定投":
            df["week"] = df["date"].dt.isocalendar().year.astype(str) + "-W" + df["date"].dt.isocalendar().week.astype(str).str.zfill(2)
            groups = df.groupby("week", sort=True)
        else:
            # 月度定投
            df["year"] = df["date"].dt.year
            df["month"] = df["date"].dt.month
            groups = df.groupby(["year", "month"], sort=True)

        total_shares = 0.0
        total_cost = 0.0
        hold_values = []
        costs = []
        shares_history = []
        invest_count = 0

        for _, group in groups:
            if dca_mode == "周定投":
                # 每周最后一个交易日买入
                invest_row = group.iloc[-1]
            else:
                # 月度定投: 找>=定投日的第一个交易日
                target_day = pd.Timestamp(year=group["date"].iloc[0].year, month=group["date"].iloc[0].month, day=dca_day)
                invest_day = group[group["date"] >= target_day]
                if invest_day.empty:
                    invest_row = group.iloc[-1]
                else:
                    invest_row = invest_day.iloc[0]

            price = invest_row["close"]
            if pd.notna(price) and price > 0 and invest_count < num_installments:
                shares_bought = per_installment / price
                total_shares += shares_bought
                total_cost += per_installment
                invest_count += 1

            for idx in group.index:
                close_price = df.loc[idx, "close"]
                if pd.notna(close_price) and close_price > 0:
                    hold_values.append(close_price * total_shares)
                else:
                    hold_values.append(0.0)
                costs.append(total_cost)
                shares_history.append(total_shares)

        df["hold_value"] = hold_values
        df["total_cost"] = costs
        df["shares"] = shares_history
        df["return_rate"] = np.where(
            df["total_cost"] > 0,
            (df["hold_value"] / df["total_cost"] - 1) * 100,
            0.0,
        )
        df["asset_weight"] = weight

        asset_results[asset_name] = df[
            ["date", "close", "shares", "hold_value", "total_cost", "return_rate", "asset_weight"]
        ]

    # ========== 构建组合 ==========
    date_set = set()
    for df in asset_results.values():
        date_set.update(df["date"].dt.date)
    common_dates = sorted(date_set)

    portfolio_rows = []
    for d in common_dates:
        dt = pd.Timestamp(d)
        total_value = 0.0
        total_cost = 0.0
        for asset_name, df in asset_results.items():
            mask = df["date"].dt.date == d
            if mask.any():
                row = df[mask].iloc[0]
                total_value += row["hold_value"]
                total_cost += row["total_cost"]
        rr = (total_value / total_cost - 1) * 100 if total_cost > 0 else 0.0
        portfolio_rows.append({
            "date": dt,
            "hold_value": total_value,
            "total_cost": total_cost,
            "return_rate": rr,
        })

    portfolio_df = pd.DataFrame(portfolio_rows)
    portfolio_df = portfolio_df.sort_values("date").reset_index(drop=True)

    # ========== 汇总指标 ==========
    total_cost_final = portfolio_df["total_cost"].iloc[-1]
    total_value_final = portfolio_df["hold_value"].iloc[-1]
    final_return = portfolio_df["return_rate"].iloc[-1]

    days = (portfolio_df["date"].iloc[-1] - portfolio_df["date"].iloc[0]).days
    years = days / 365.25 if days > 0 else 0
    if years > 0 and total_cost_final > 0:
        cagr = (1 + final_return / 100) ** (1 / years) - 1
        cagr *= 100
    else:
        cagr = 0.0

    # 最大回撤
    running_max = portfolio_df["hold_value"].cummax()
    drawdown = ((portfolio_df["hold_value"] - running_max) / running_max)
    max_dd = abs(drawdown.min()) * 100 if not drawdown.empty else 0.0

    # 夏普比率
    portfolio_df["daily_return"] = portfolio_df["hold_value"].pct_change() * 100
    daily_returns = portfolio_df["daily_return"].dropna()
    if len(daily_returns) > 1 and daily_returns.std() > 0:
        excess = daily_returns / 100.0 - 0.02 / 252
        sharpe_daily = excess.mean() / excess.std()
        sharpe = sharpe_daily * np.sqrt(252)
    else:
        sharpe = 0.0

    # 各标的最终数据
    asset_final = {}
    for asset_name, df in asset_results.items():
        last = df.iloc[-1]
        first_idx = df["total_cost"].gt(0).idxmax()
        first_valid = df.loc[first_idx]
        days_held = (df["date"].iloc[-1] - first_valid["date"]).days
        yrs = days_held / 365.25 if days_held > 0 else 0
        asset_cagr = 0.0
        if yrs > 0 and last["total_cost"] > 0:
            ret = (last["hold_value"] / last["total_cost"] - 1)
            asset_cagr = (1 + ret) ** (1 / yrs) - 1

        amax = df["hold_value"].cummax()
        add = ((df["hold_value"] - amax) / amax)
        amax_dd = abs(add.min()) * 100 if not add.empty else 0.0

        asset_final[asset_name] = {
            "总投入": round(last["total_cost"], 2),
            "最终市值": round(last["hold_value"], 2),
            "收益率%": round(last["return_rate"], 2),
            "年化收益率%": round(asset_cagr * 100, 2),
            "最大回撤%": round(amax_dd, 2),
            "权重%": round(df["asset_weight"].iloc[0] * 100, 1),
        }

    summary = {
        "总投入": round(total_cost_final, 2),
        "最终市值": round(total_value_final, 2),
        "收益额": round(total_value_final - total_cost_final, 2),
        "总收益率%": round(final_return, 2),
        "年化收益率%": round(cagr, 2),
        "最大回撤%": round(max_dd, 2),
        "夏普比率": round(sharpe, 4),
        "定投总次数": num_installments,
        "每期定投额": round(per_installment if dca_mode != "一次性投入" else 0, 2),
        "持有天数": days,
        "年数": round(years, 2),
        "标的数量": len(price_dict),
        "策略": dca_mode,
        "资产明细": asset_final,
    }

    portfolio_df["drawdown"] = drawdown * 100 if not drawdown.empty else 0.0

    return {
        "portfolio": portfolio_df,
        "assets": asset_results,
        "summary": summary,
    }