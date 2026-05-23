"""
Streamlit 主界面 - 多标的组合比例定投回测工具
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date

from data_fetcher import get_asset_history, list_assets_by_category, list_available_assets
from backtest import backtest_multi_dca
from charts import create_portfolio_dashboard, plot_asset_radar

# 页面配置
st.set_page_config(
    page_title="组合定投回测工具",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

MAX_ASSETS = 10


def main():
    st.title("📊 多标的组合比例定投回测工具")
    st.markdown("---")

    # ===== 侧边栏 =====
    with st.sidebar:
        st.header("⚙️ 回测参数")

        # ----- 资金参数 -----
        st.subheader("💰 资金设置")
        total_investment = st.number_input(
            "定投总资金 (元)",
            min_value=1000.0,
            max_value=100_000_000.0,
            value=100_000.0,
            step=10_000.0,
            format="%.0f",
            help="用于定投的总资金量",
        )
        num_installments = st.number_input(
            "定投总次数 (每月一次)",
            min_value=1,
            max_value=600,
            value=12,
            step=1,
            help="资金分多少个月定投完毕（每次投入 = 总资金 ÷ 次数）",
        )

        # 每次定投额提示
        per_amount = total_investment / num_installments
        st.caption(
            f"📌 每次定投 **¥{per_amount:,.0f}** = "
            f"总资金 ¥{total_investment:,.0f} ÷ {num_installments}次"
        )

        st.markdown("---")

        # ----- 时间范围 -----
        st.subheader("📅 时间范围")
        today = date.today()
        default_start = date(today.year - 10, today.month, 1)

        start_date = st.date_input(
            "开始日期",
            value=default_start,
            max_value=today,
        )
        end_date = st.date_input(
            "结束日期",
            value=today,
            max_value=today,
            min_value=start_date,
        )

        dca_day = st.slider(
            "每月定投日",
            min_value=1,
            max_value=28,
            value=1,
            help="每月几号执行定投（如遇非交易日则顺延）",
        )

        st.markdown("---")

        # ----- 选择标的 -----
        st.subheader(f"🎯 选择标的 (最多{MAX_ASSETS}个)")

        # 获取按分类的标的
        categories = list_assets_by_category()
        categories_order = [
            "A股宽基", "策略红利", "海外指数", "行业主题", "A股指数"
        ]

        all_options = list(list_available_assets().keys())
        # 默认选中几个热门标的
        default_selection = [
            "沪深300ETF(510300)",
            "中证红利ETF(515080)",
            "纳指ETF(513100)",
            "日经225ETF(513000)",
            "自由现金流ETF(159585)",
        ]
        # 只保留在 all_options 中的默认项
        default_selection = [x for x in default_selection if x in all_options]

        selected_assets = st.multiselect(
            "搜索或选择标的",
            options=all_options,
            default=default_selection,
            max_selections=MAX_ASSETS,
            placeholder="输入名称搜索...",
        )

        if not selected_assets:
            st.warning("请至少选择 1 个标的")
            st.stop()

        st.caption(f"已选 {len(selected_assets)}/{MAX_ASSETS} 个标的")

        # ----- 权重分配 -----
        st.subheader("⚖️ 权重分配")
        st.caption("拖动滑块调整各标的权重（自动归一化到100%）")

        # 初始化权重：等权重
        weights_raw = {}
        equal_weight = 100.0 / len(selected_assets)
        for asset in selected_assets:
            # 使用 session_state 记住权重值
            key = f"weight_{asset}"
            default_w = equal_weight
            if key not in st.session_state:
                st.session_state[key] = default_w

        # 显示权重滑块
        col_w1, col_w2 = st.columns([3, 1])
        with col_w1:
            st.markdown("**标的**")
        with col_w2:
            st.markdown("**权重%**")

        total_input = 0.0
        weight_values = {}
        for asset in selected_assets:
            key = f"weight_{asset}"
            col1, col2 = st.columns([3, 1])
            with col1:
                # 截断显示名称
                display_name = asset
                if len(display_name) > 28:
                    display_name = display_name[:26] + "..."
                st.markdown(f"<small>{display_name}</small>", unsafe_allow_html=True)
            with col2:
                w = st.number_input(
                    label="",
                    key=key,
                    min_value=0.0,
                    max_value=100.0,
                    value=st.session_state.get(key, equal_weight),
                    step=1.0,
                    format="%.0f",
                    label_visibility="collapsed",
                )
            weight_values[asset] = w
            total_input += w

        # 显示总权重
        if total_input > 0:
            st.caption(f"总权重: {total_input:.0f}% {'✅ 已归一化' if abs(total_input - 100) < 0.1 else '⚠️ 未归一化'}")
            # 自动归一化到 100%
            if abs(total_input - 100) > 0.1 and total_input > 0:
                if st.button("🔄 自动归一化权重到100%", use_container_width=True):
                    for asset in selected_assets:
                        key = f"weight_{asset}"
                        old_w = weight_values[asset]
                        new_w = old_w / total_input * 100
                        st.session_state[key] = round(new_w, 1)
                    st.rerun()

        # 实际使用的权重（归一化到100%）
        if total_input > 0:
            actual_weights = {a: w / total_input for a, w in weight_values.items()}
        else:
            actual_weights = {a: 0.0 for a in selected_assets}

        # 显示最终权重分配
        st.markdown("---")
        st.caption("📊 最终权重配置：")
        weight_df = pd.DataFrame([
            {"标的": a, "权重%": round(actual_weights[a] * 100, 1)}
            for a in selected_assets
        ])
        st.dataframe(weight_df, use_container_width=True, hide_index=True)

        st.markdown("---")
        run_button = st.button("🚀 开始回测", type="primary", use_container_width=True)

    # ===== 主区域 =====
    if not run_button:
        # 欢迎界面
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.info(
                """
            👈 **请在左侧设置回测参数**

            ### ✨ 新增功能

            - ✅ **最多10种标的** 同时回测
            - ✅ **自定义权重** 分配资金比例
            - ✅ **总资金 + 定投次数** 灵活设置
            - ✅ **日经225、红利指数、自由现金流** 等更多标的
            - ✅ **组合收益/回撤/夏普** 综合指标
            - ✅ **各标的收益率对比** 一目了然

            ### 💡 使用说明

            1. 左侧设置 **总资金** 和 **定投次数**
            2. 选择 **标的** 并调整 **权重**
            3. 点击 **开始回测**
            """
            )
        return

    # ===== 执行回测 =====
    start_str = start_date.strftime("%Y%m%d")
    end_str = end_date.strftime("%Y%m%d")
    start_str_dash = start_date.strftime("%Y-%m-%d")
    end_str_dash = end_date.strftime("%Y-%m-%d")

    # 获取所有标的数据
    price_dict = {}
    progress_bar = st.progress(0, text="正在获取标的数据...")
    status_text = st.empty()

    fetch_ok = True
    for i, asset_name in enumerate(selected_assets):
        status_text.text(f"📥 获取 {asset_name} 的历史数据...")
        progress_bar.progress((i + 1) / len(selected_assets))
        try:
            df = get_asset_history(asset_name, start_str, end_str)
            if df.empty:
                st.error(f"❌ {asset_name} 在指定日期范围内无数据")
                fetch_ok = False
                break
            price_dict[asset_name] = df
        except Exception as e:
            st.error(f"❌ 获取 {asset_name} 失败: {str(e)}")
            fetch_ok = False
            break

    progress_bar.empty()
    status_text.empty()

    if not fetch_ok or not price_dict:
        st.stop()

    st.success(f"✅ 成功获取 {len(price_dict)} 个标的数据")

    # 执行回测
    with st.spinner("🔄 正在执行组合定投回测..."):
        try:
            result = backtest_multi_dca(
                price_dict=price_dict,
                weights=actual_weights,
                total_investment=total_investment,
                num_installments=num_installments,
                start_date=start_str_dash,
                end_date=end_str_dash,
                dca_day=dca_day,
            )
        except Exception as e:
            st.error(f"❌ 回测计算失败: {str(e)}")
            st.stop()

    summary = result["summary"]
    portfolio_df = result["portfolio"]
    asset_details = result["assets"]

    # ===== 显示结果 =====
    st.markdown("---")
    st.header("📈 组合回测结果")

    # ===== 综合指标卡片 =====
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="组合总收益率",
            value=f"{summary['总收益率%']:.2f}%",
            delta=f"{summary['收益额']:+,.0f}元",
        )

    with col2:
        st.metric(
            label="年化收益率 (CAGR)",
            value=f"{summary['年化收益率%']:.2f}%",
            delta=f"持有 {summary['年数']:.1f} 年",
            delta_color="off",
        )

    with col3:
        st.metric(
            label="最大回撤",
            value=f"-{summary['最大回撤%']:.2f}%",
            delta_color="inverse",
        )

    with col4:
        st.metric(
            label="夏普比率",
            value=f"{summary['夏普比率']:.2f}",
            delta=">1 较好" if summary['夏普比率'] > 1 else "<1 一般" if summary['夏普比率'] > 0 else "负值",
            delta_color="off",
        )

    # 第二行指标
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="总投入", value=f"¥{summary['总投入']:,.2f}")

    with col2:
        st.metric(label="最终市值", value=f"¥{summary['最终市值']:,.2f}")

    with col3:
        st.metric(label="定投次数", value=f"{summary['定投总次数']}次")

    with col4:
        st.metric(label="每期定投额", value=f"¥{summary['每期定投额']:,.2f}")

    # ===== 各标的明细表 =====
    st.markdown("---")
    st.subheader("📋 各标的回测明细")

    detail_rows = []
    for asset_name, info in summary["资产明细"].items():
        detail_rows.append({
            "标的": asset_name,
            "权重%": info["权重%"],
            "总投入": info["总投入"],
            "最终市值": info["最终市值"],
            "收益率%": info["收益率%"],
            "年化收益率%": info["年化收益率%"],
            "最大回撤%": info["最大回撤%"],
        })

    detail_df = pd.DataFrame(detail_rows)
    detail_df = detail_df.sort_values("权重%", ascending=False).reset_index(drop=True)

    # 格式化显示
    display_detail = detail_df.copy()
    display_detail["总投入"] = display_detail["总投入"].apply(lambda x: f"¥{x:,.2f}")
    display_detail["最终市值"] = display_detail["最终市值"].apply(lambda x: f"¥{x:,.2f}")
    display_detail["收益率%"] = display_detail["收益率%"].apply(lambda x: f"{x:.2f}%")
    display_detail["年化收益率%"] = display_detail["年化收益率%"].apply(lambda x: f"{x:.2f}%")
    display_detail["最大回撤%"] = display_detail["最大回撤%"].apply(lambda x: f"-{x:.2f}%")

    st.dataframe(display_detail, use_container_width=True, hide_index=True)

    # ===== 仪表盘图表 =====
    st.markdown("---")
    st.subheader("📊 组合可视化分析")

    # 组合名称
    portfolio_name = f"{' + '.join([a.split('(')[0][:6] for a in selected_assets[:4]])}" + \
                     (f" 等{len(selected_assets)}标的" if len(selected_assets) > 4 else "")

    title = (
        f"{portfolio_name} | 总资金¥{total_investment:,.0f}×{num_installments}次 "
        f"| {start_date} ~ {end_date}"
    )

    fig_dashboard = create_portfolio_dashboard(portfolio_df, asset_details, title=title)
    st.plotly_chart(fig_dashboard, use_container_width=True)

    # ===== 收益-风险气泡图 =====
    st.markdown("---")
    fig_radar = plot_asset_radar(summary["资产明细"])
    st.plotly_chart(fig_radar, use_container_width=True)

    # ===== 明细数据 =====
    st.markdown("---")
    with st.expander("📋 查看组合每日明细数据"):
        display_df = portfolio_df[["date", "hold_value", "total_cost", "return_rate", "drawdown"]].copy()
        display_df.columns = ["日期", "持仓市值", "累计投入", "累计收益率(%)", "回撤(%)"]
        display_df["日期"] = display_df["日期"].dt.strftime("%Y-%m-%d")
        display_df["持仓市值"] = display_df["持仓市值"].round(2)
        display_df["累计投入"] = display_df["累计投入"].round(2)
        display_df["累计收益率(%)"] = display_df["累计收益率(%)"].round(2)
        display_df["回撤(%)"] = display_df["回撤(%)"].round(2)

        st.dataframe(display_df, use_container_width=True, height=400)

        # 下载CSV
        csv = display_df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="📥 下载组合明细CSV",
            data=csv,
            file_name=f"portfolio_backtest_{start_date}_{end_date}.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()