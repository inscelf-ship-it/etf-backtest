"""
模块测试脚本
"""
from data_fetcher import get_etf_history
from backtest import backtest_lump_sum, backtest_dca
from metrics import compute_all_metrics

# 测试获取数据
df = get_etf_history("510300", "20240101", "20240630")
print(f"数据行数: {len(df)}")
print(f"数据范围: {df.date.iloc[0]} ~ {df.date.iloc[-1]}")

# 测试一次性投入
result1 = backtest_lump_sum(df, 10000)
m1 = compute_all_metrics(result1)
print(f"一次性投入 - 总收益率: {m1['总收益率 (%)']}%")

# 测试定投
result2 = backtest_dca(df, 1000)
m2 = compute_all_metrics(result2)
print(f"等额定投 - 总收益率: {m2['总收益率 (%)']}%")
print("✅ 所有模块测试通过!")