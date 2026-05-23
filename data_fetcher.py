"""
数据获取模块：使用 akshare 获取ETF/基金历史行情数据
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta


def get_etf_history(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    获取ETF历史净值/价格数据

    参数:
        symbol: ETF代码，如 '510300'（沪深300ETF）
        start_date: 开始日期 'YYYYMMDD'
        end_date: 结束日期 'YYYYMMDD'

    返回:
        DataFrame 包含日期和复权净值/价格
    """
    try:
        # 获取ETF历史数据（包含复权因子）
        df = ak.fund_etf_hist_em(
            symbol=symbol,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq",  # 前复权
        )

        if df is None or df.empty:
            raise ValueError(f"未获取到 {symbol} 的数据")

        # 标准化列名
        df = df.rename(
            columns={
                "日期": "date",
                "收盘": "close",
                "开盘": "open",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
            }
        )
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)

        return df[["date", "close", "open", "high", "low", "volume"]]

    except Exception as e:
        raise RuntimeError(f"获取ETF数据失败 [{symbol}]: {str(e)}")


def list_available_etfs() -> list:
    """
    获取常见宽基ETF列表（部分热门）
    """
    etfs = [
        {"code": "510300", "name": "沪深300ETF"},
        {"code": "510500", "name": "中证500ETF"},
        {"code": "510050", "name": "上证50ETF"},
        {"code": "159915", "name": "创业板ETF"},
        {"code": "588000", "name": "科创50ETF"},
        {"code": "512100", "name": "中证1000ETF"},
        {"code": "513100", "name": "纳指ETF"},
        {"code": "159941", "name": "纳指ETF"},
        {"code": "513050", "name": "中概互联ETF"},
        {"code": "159920", "name": "恒生ETF"},
        {"code": "510310", "name": "沪深300ETF易方达"},
        {"code": "512880", "name": "证券ETF"},
        {"code": "159949", "name": "创业板50ETF"},
        {"code": "515000", "name": "科技ETF"},
        {"code": "512010", "name": "医药ETF"},
        {"code": "159928", "name": "消费ETF"},
        {"code": "518880", "name": "黄金ETF"},
    ]
    return etfs


if __name__ == "__main__":
    # 简单测试
    df = get_etf_history("510300", "20230101", "20231231")
    print(df.head())
    print(f"\n共 {len(df)} 个交易日")