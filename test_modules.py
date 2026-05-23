"""
模块测试脚本（适配当前版本）
"""
from data_fetcher import get_asset_history, list_available_assets, list_assets_by_category
from backtest import backtest_multi_dca
from charts import create_portfolio_dashboard, plot_asset_radar

# 测试1: 列出可用标的
print("=" * 50)
print("📋 测试1: 列出可用标的")
assets = list_available_assets()
print(f"总标的数据: {len(assets)} 个")
categories = list_assets_by_category()
for cat, items in categories.items():
    print(f"  {cat}: {len(items)} 个")

# 测试2: 获取数据
print("\n" + "=" * 50)
print("📊 测试2: 获取 ETF 历史数据")
df1 = get_asset_history("沪深300ETF(510300)", "20240101", "20240630")
print(f"沪深300ETF: {len(df1)} 行, {df1.date.iloc[0].date()} ~ {df1.date.iloc[-1].date()}")

df2 = get_asset_history("纳指ETF(513100)", "20240101", "20240630")
print(f"纳指ETF:     {len(df2)} 行, {df2.date.iloc[0].date()} ~ {df2.date.iloc[-1].date()}")

df3 = get_asset_history("日经225ETF(513000)", "20240101", "20240630")
print(f"日经225ETF:  {len(df3)} 行, {df3.date.iloc[0].date()} ~ {df3.date.iloc[-1].date()}")

# 测试3: 组合定投回测
print("\n" + "=" * 50)
print("📈 测试3: 组合定投回测 (3只ETF等权重)")
price_dict = {
    "沪深300ETF(510300)": df1,
    "纳指ETF(513100)": df2,
    "日经225ETF(513000)": df3,
}
weights = {
    "沪深300ETF(510300)": 0.4,
    "纳指ETF(513100)": 0.3,
    "日经225ETF(513000)": 0.3,
}

result = backtest_multi_dca(
    price_dict=price_dict,
    weights=weights,
    total_investment=100000.0,
    num_installments=12,
    start_date="2024-01-01",
    end_date="2024-06-30",
    dca_day=1,
)

summary = result["summary"]
print(f"总投入:     ¥{summary['总投入']:,.2f}")
print(f"最终市值:   ¥{summary['最终市值']:,.2f}")
print(f"总收益率:   {summary['总收益率%']:.2f}%")
print(f"年化收益率: {summary['年化收益率%']:.2f}%")
print(f"最大回撤:   {summary['最大回撤%']:.2f}%")
print(f"夏普比率:   {summary['夏普比率']:.4f}")
print(f"定投次数:   {summary['定投总次数']}次")
print(f"标的数量:   {summary['标的数量']}个")
print(f"持有天数:   {summary['持有天数']}天")

# 各标的明细
for name, info in summary["资产明细"].items():
    print(f"  {name}: 权重{info['权重%']}% | 收益率{info['收益率%']}% | 年化{info['年化收益率%']}%")

# 测试4: 生成图表
print("\n" + "=" * 50)
print("📊 测试4: 生成图表")
fig = create_portfolio_dashboard(result["portfolio"], result["assets"], title="测试回测")
print(f"组合仪表盘图表生成: ✅ ({len(fig.data)} 个trace)")

fig2 = plot_asset_radar(summary["资产明细"])
print(f"收益-风险气泡图生成: ✅ ({len(fig2.data)} 个trace)")

print("\n" + "=" * 50)
print("✅ 所有模块测试通过!")
print("=" * 50)