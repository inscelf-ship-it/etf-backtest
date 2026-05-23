"""
快速测试：验证基准对比的当日收益率/当日收益额 hover 功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from charts import _calc_daily_change, plot_profit_curve, plot_return_rate_curve
import pandas as pd
import numpy as np

# 构造测试数据
dates = pd.date_range("2023-01-01", periods=10, freq="D")
portfolio_df = pd.DataFrame({
    "date": dates,
    "hold_value": np.linspace(100000, 110000, 10),
    "total_cost": [100000] * 10,
    "return_rate": np.linspace(0, 10, 10),
})

# 构造基准数据（与投资组合相同日期 + 前后多一点日期，测试对齐）
bm_dates = pd.date_range("2022-12-30", periods=14, freq="D")
bm_close = np.linspace(100, 110, 14)
benchmark_df = pd.DataFrame({
    "date": bm_dates,
    "close": bm_close,
    "return_rate": (bm_close / bm_close[0] - 1) * 100,
})

# 测试 plot_profit_curve
fig1 = plot_profit_curve(
    portfolio_df,
    benchmark_label="沪深300指数(000300)",
    benchmark_df=benchmark_df,
    total_investment=100000,
)
print("图1 (收益额曲线) 创建成功")
print(f"  轨迹数: {len(fig1.data)}")

# 测试 plot_return_rate_curve
fig2 = plot_return_rate_curve(
    portfolio_df,
    benchmark_label="沪深300指数(000300)",
    benchmark_df=benchmark_df,
)
print("图2 (收益率曲线) 创建成功")
print(f"  轨迹数: {len(fig2.data)}")

# 检查基准轨迹的 customdata 和 hovertemplate 是否包含当日收益字段
# 只检查基准线本身（不含"跑赢"轨迹）
for i, fig in enumerate([fig1, fig2], 1):
    for trace in fig.data:
        if trace.name == "沪深300指数(000300)":
            assert trace.customdata is not None, f"图{i} 基准轨迹缺少 customdata"
            assert "当日收益" in trace.hovertemplate, f"图{i} 基准轨迹 hovertemplate 缺少当日收益字段"
            print(f"图{i} 基准轨迹 '{trace.name}': ✅ customdata 和 hovertemplate 验证通过")

print("\n✅ 所有测试通过！")