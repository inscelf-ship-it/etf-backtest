"""
数据获取模块：支持ETF/指数历史行情数据
支持 A股ETF、海外ETF、A股指数 等多类型标的
"""

import os

# 在导入任何网络库之前清除代理设置
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)

import akshare as ak
import pandas as pd
import urllib.request
import json
from datetime import datetime, timedelta
from typing import Optional


# ============================================================
# 可用标的数据库（按分类组织）
# ============================================================
# type: "etf" = ETF基金 (使用 akshare fund_etf_hist_em)
#       "index" = A股股票指数 (使用 akshare stock_zh_index_daily)
# market: 仅用于 index 类型，"sh"或"sz"
ASSETS_DB = {
    # ---- A股宽基 ----
    "沪深300ETF(510300)":        {"code": "510300", "type": "etf", "category": "A股宽基"},
    "中证500ETF(510500)":        {"code": "510500", "type": "etf", "category": "A股宽基"},
    "上证50ETF(510050)":         {"code": "510050", "type": "etf", "category": "A股宽基"},
    "创业板ETF(159915)":         {"code": "159915", "type": "etf", "category": "A股宽基"},
    "科创50ETF(588000)":         {"code": "588000", "type": "etf", "category": "A股宽基"},
    "中证1000ETF(512100)":      {"code": "512100", "type": "etf", "category": "A股宽基"},
    "中证2000ETF(563300)":      {"code": "563300", "type": "etf", "category": "A股宽基"},
    "科创100ETF(588190)":       {"code": "588190", "type": "etf", "category": "A股宽基"},
    # ---- A股策略/红利 ----
    "中证红利ETF(515080)":      {"code": "515080", "type": "etf", "category": "策略红利"},
    "红利低波ETF(512890)":      {"code": "512890", "type": "etf", "category": "策略红利"},
    "红利ETF(510880)":          {"code": "510880", "type": "etf", "category": "策略红利"},
    "自由现金流ETF(159585)":    {"code": "159585", "type": "etf", "category": "策略红利"},
    "基本面50ETF(512750)":      {"code": "512750", "type": "etf", "category": "策略红利"},
    "沪深300价值ETF(562320)":   {"code": "562320", "type": "etf", "category": "策略红利"},
    # ---- 海外指数(QDII-ETF) ----
    "标普500ETF(513500)":       {"code": "513500", "type": "etf", "category": "海外指数"},
    "纳指ETF(513100)":          {"code": "513100", "type": "etf", "category": "海外指数"},
    "日经225ETF(513000)":       {"code": "513000", "type": "etf", "category": "海外指数"},
    "日经225ETF(513880)":       {"code": "513880", "type": "etf", "category": "海外指数"},
    "德国ETF(513030)":          {"code": "513030", "type": "etf", "category": "海外指数"},
    "法国CAC40ETF(513080)":     {"code": "513080", "type": "etf", "category": "海外指数"},
    "恒生ETF(159920)":         {"code": "159920", "type": "etf", "category": "海外指数"},
    "中概互联ETF(513050)":      {"code": "513050", "type": "etf", "category": "海外指数"},
    "东南亚科技ETF(513730)":    {"code": "513730", "type": "etf", "category": "海外指数"},
    # ---- A股行业/主题 ----
    "证券ETF(512880)":          {"code": "512880", "type": "etf", "category": "行业主题"},
    "医药ETF(512010)":          {"code": "512010", "type": "etf", "category": "行业主题"},
    "消费ETF(159928)":          {"code": "159928", "type": "etf", "category": "行业主题"},
    "科技ETF(515000)":          {"code": "515000", "type": "etf", "category": "行业主题"},
    "新能源ETF(515030)":        {"code": "515030", "type": "etf", "category": "行业主题"},
    "半导体ETF(512480)":        {"code": "512480", "type": "etf", "category": "行业主题"},
    "军工ETF(512660)":          {"code": "512660", "type": "etf", "category": "行业主题"},
    "黄金ETF(518880)":          {"code": "518880", "type": "etf", "category": "行业主题"},
    # ---- A股指数（直接跟踪指数本身）----
    "沪深300指数(000300)":      {"code": "000300", "type": "index", "market": "sh", "category": "A股指数"},
    "中证500指数(000905)":      {"code": "000905", "type": "index", "market": "sh", "category": "A股指数"},
    "上证50指数(000016)":       {"code": "000016", "type": "index", "market": "sh", "category": "A股指数"},
    "创业板指(399006)":         {"code": "399006", "type": "index", "market": "sz", "category": "A股指数"},
    "中证红利指数(000922)":     {"code": "000922", "type": "index", "market": "sh", "category": "A股指数"},
    "科创50指数(000688)":       {"code": "000688", "type": "index", "market": "sh", "category": "A股指数"},
}

# 腾讯财经接口的市场映射
_TENCENT_MARKET_MAP = {
    "sh": "sh",
    "sz": "sz",
}


def list_available_assets() -> dict:
    """返回完整标的数据库"""
    return ASSETS_DB


def list_assets_by_category() -> dict:
    """按分类返回标的列表"""
    categories = {}
    for name, info in ASSETS_DB.items():
        cat = info["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append({"name": name, **info})
    return categories


def get_asset_history(
    asset_name: str,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """
    根据标的名称获取历史价格数据

    参数:
        asset_name: 标的显示名称（如 "沪深300ETF(510300)"）
        start_date: 开始日期 'YYYYMMDD'
        end_date: 结束日期 'YYYYMMDD'

    返回:
        DataFrame 包含 date, close 列
    """
    if asset_name not in ASSETS_DB:
        raise ValueError(f"未知标的: {asset_name}")

    info = ASSETS_DB[asset_name]
    asset_type = info["type"]

    if asset_type == "etf":
        return _get_etf_data(info["code"], start_date, end_date)
    elif asset_type == "index":
        market = info["market"]
        return _get_index_data(info["code"], market, start_date, end_date)
    else:
        raise ValueError(f"不支持的资产类型: {asset_type}")


def _get_etf_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """获取ETF历史数据：先试东方财富akshare，失败后fallback腾讯财经"""
    # ---- 方法1: akshare fund_etf_hist_em (东方财富) ----
    try:
        df = ak.fund_etf_hist_em(
            symbol=symbol,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq",
        )
        if df is not None and not df.empty:
            df = df.rename(columns={"日期": "date", "收盘": "close"})
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").reset_index(drop=True)
            return df[["date", "close"]]
    except Exception:
        pass  # fallback 到方法2

    # ---- 方法2: 腾讯财经接口 (适配沪深ETF) ----
    try:
        return _get_etf_data_tencent(symbol, start_date, end_date)
    except Exception as e:
        raise RuntimeError(f"获取ETF数据失败 [{symbol}]: {str(e)}")


def _get_etf_data_tencent(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """使用腾讯财经接口获取ETF历史数据"""
    # 判断market: 6开头上海, 0/159/5开头深圳
    if symbol.startswith("6"):
        market = "sh"
    else:
        market = "sz"

    # 格式化日期
    s_date = datetime.strptime(start_date, "%Y%m%d").strftime("%Y-%m-%d")
    e_date = datetime.strptime(end_date, "%Y%m%d").strftime("%Y-%m-%d")

    url = (
        f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
        f"?param={market}{symbol},day,{s_date},{e_date},400,qfq"
    )

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())

    if data.get("code") != 0:
        raise ValueError(f"腾讯接口返回错误码: {data.get('code')}")

    raw_data = data.get("data", {}).get(f"{market}{symbol}", {})
    # 尝试多个可能的 key 存放K线数据
    klines = raw_data.get("qfqday") or raw_data.get("day") or raw_data.get("data")
    if not klines or not isinstance(klines, list):
        raise ValueError(f"未从腾讯接口获取到K线数据")

    records = []
    for item in klines:
        if len(item) < 6:
            continue
        # 格式: [date, open, close, high, low, volume]
        date_str = str(item[0])
        close_val = float(item[2])
        records.append({"date": date_str, "close": close_val})

    if not records:
        raise ValueError(f"解析K线数据为空")

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    # 按请求的日期范围过滤
    start_ts = pd.Timestamp(start_date)
    end_ts = pd.Timestamp(end_date)
    df = df[(df["date"] >= start_ts) & (df["date"] <= end_ts)].reset_index(drop=True)

    if df.empty:
        raise ValueError(f"在指定日期范围内无数据")

    return df[["date", "close"]]


def _get_index_data(symbol: str, market: str, start_date: str, end_date: str) -> pd.DataFrame:
    """获取A股指数历史数据"""
    try:
        full_symbol = f"{market}{symbol}"
        df = ak.stock_zh_index_daily(symbol=full_symbol)
        if df is None or df.empty:
            raise ValueError(f"未获取到 {symbol} 的数据")
        df = df.rename(columns={"date": "date"})
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)

        # 过滤日期范围
        start_ts = pd.Timestamp(start_date)
        end_ts = pd.Timestamp(end_date)
        df = df[(df["date"] >= start_ts) & (df["date"] <= end_ts)].reset_index(drop=True)

        if df.empty:
            raise ValueError(f"在指定日期范围内无数据")

        return df[["date", "close"]]
    except Exception as e:
        raise RuntimeError(f"获取指数数据失败 [{symbol}]: {str(e)}")


if __name__ == "__main__":
    # 简单测试
    df = get_asset_history("沪深300ETF(510300)", "20230101", "20231231")
    print(df.head())
    print(f"共 {len(df)} 个交易日")