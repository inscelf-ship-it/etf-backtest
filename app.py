"""
Streamlit 主界面 - ETF/基金数据回测工具
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date

from data_fetcher import get_etf_history, list_available_etfs
from backtest import backtest_lump_sum, backtest_dca
from metrics import compute_all_metrics
from charts import create_dashboard, plot_return_rate_curve

# 页面配置
st.set_page_config(
    page_title="ETF回测工具",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    st.title("📊 ETF / 基金数据回测工具")
    st.markdown("---")

    # ===== 侧边栏：参数输入 =====
    with st.sidebar:
        st.header("⚙️ 回测参数")

        # 策略选择
        strategy = st.radio(
            "选择策略",
            options=["等额定投 (DCA)", "一次性投入"],
            index=0,
            help="等额定投：每月固定日期买入固定金额\n一次性投入：初始一次性买入",
        )

        # ETF 选择
        etfs = list_available_etfs()
        etf_options = {f"{e['code']} - {e['name']}": e["code"] for e in etfs}
        selected_etf_label = st.selectbox(
            "选择ETF",
            options=list(etf_options.keys()),
            index=0,
            help="选择要回测的ETF代码",
        )
        etf_code = etf_options[selected_etf_label]
        etf_name = selected_etf_label

        # 投资金额
        if strategy == "等额定投 (DCA)":
            invest_amount = st.number_input(
                "每月定投金额 (元)",
                min_value=100.0,
                max_value=1_000_000.0,
                value=1000.0,
                step=100.0,
                format="%.0f",
                help="每月固定投入金额",
            )
        else:
            invest_amount = st.number_input(
                "投入总金额 (元)",
                min_value=100.0,
                max_value=10_000_000.0,
                value=10000.0,
                step=1000.0,
                format="%.0f",
                help="一次性投入的总金额",
            )

        # 时间范围
        # 默认过去5年
        today = date.today()
        default_start = date(today.year - 5, today.month, 1)

        start_date = st.date_input(
            "开始日期",
            value=default_start,
            max_value=today,
            help="回测开始日期（数据将从此日期开始获取）",
        )
        end_date = st.date_input(
            "结束日期",
            value=today,
            max_value=today,
            min_value=start_date,
            help="回测结束日期",
        )

        # 定投日（仅定投策略）
        dca_day = 1
        if strategy == "等额定投 (DCA)":
            dca_day = st.slider(
                "每月定投日",
                min_value=1,
                max_value=28,
                value=1,
                help="每月几号执行定投（如遇非交易日则顺延）",
            )

        # 运行按钮
        st.markdown("---")
        run_button = st.button("🚀 开始回测", type="primary", use_container_width=True)

    # ===== 主区域 =====
    if not run_button:
        # 未点击运行时的欢迎提示
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.info(
                """
            👈 **请在左侧设置回测参数**

            支持功能：
            - ✅ 任意ETF代码回测
            - ✅ 等额定投 / 一次性投入
            - ✅ 收益率曲线（交互式）
            - ✅ 年化收益 / 最大回撤 / 夏普比率
            - ✅ 持仓市值 vs 累计投入对比
            """
            )
        return

    # ===== 执行回测 =====
    with st.spinner(f"正在获取 {etf_name} 的历史数据..."):
        try:
            # 格式化日期
            start_str = start_date.strftime("%Y%m%d")
            end_str = end_date.strftime("%Y%m%d")

            # 获取数据（多获取一些用于计算，但显示时截断）
            df = get_etf_history(etf_code, start_str, end_str)

            if df.empty:
                st.error(f"未获取到 {etf_name} 在 {start_date} ~ {end_date} 范围内的数据")
                return

            st.success(f"✅ 获取到 {len(df)} 个交易日数据 | {etf_name}")

        except Exception as e:
            st.error(f"数据获取失败: {str(e)}")
            return

    # 执行回测
    with st.spinner("正在执行回测计算..."):
        try:
            if strategy == "一次性投入":
                result = backtest_lump_sum(df, invest_amount)
                strategy_label = f"一次性投入 ¥{invest_amount:,.0f}"
            else:
                result = backtest_dca(
                    df,
                    monthly_amount=invest_amount,
                    start_date=start_date.strftime("%Y-%m-%d"),
                    end_date=end_date.strftime("%Y-%m-%d"),
                    dca_day=dca_day,
                )
                strategy_label = f"等额定投 每月¥{invest_amount:,.0f}"

            # 计算指标
            metrics = compute_all_metrics(result)

        except Exception as e:
            st.error(f"回测计算失败: {str(e)}")
            return

    # ===== 显示结果 =====
    st.markdown("---")
    st.header(f"📈 回测结果：{etf_name}")

    # ===== 指标卡片 =====
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="总收益率",
            value=f"{metrics['总收益率 (%)']:.2f}%",
            delta=f"{metrics['盈亏金额 (元)']:+,.0f}元",
        )

    with col2:
        st.metric(
            label="年化收益率 (CAGR)",
            value=f"{metrics['年化收益率 (CAGR, %)']:.2f}%",
            delta=f"持有 {metrics['持有年限']:.1f} 年",
            delta_color="off",
        )

    with col3:
        st.metric(
            label="最大回撤",
            value=f"-{metrics['最大回撤 (%)']:.2f}%",
            delta_color="inverse",
        )

    with col4:
        st.metric(
            label="夏普比率",
            value=f"{metrics['夏普比率']:.2f}",
            delta=">1 较好" if metrics['夏普比率'] > 1 else "<1 一般" if metrics['夏普比率'] > 0 else "负值",
            delta_color="off",
        )

    # 第二行指标
    col1, col2, col3, _ = st.columns(4)

    with col1:
        st.metric(label="总投入", value=f"¥{metrics['总投入 (元)']:,.2f}")

    with col2:
        st.metric(
            label="最终市值",
            value=f"¥{metrics['最终市值 (元)']:,.2f}",
            delta=f"{'盈利' if metrics['盈亏金额 (元)'] > 0 else '亏损'} ¥{abs(metrics['盈亏金额 (元)']):,.2f}",
        )

    with col3:
        st.metric(label="交易日数", value=f"{metrics['交易日数']} 天")

    # ===== 图表 =====
    st.markdown("---")

    # 综合仪表盘
    title = f"{etf_name} | {strategy_label} | {start_date} ~ {end_date}"
    fig = create_dashboard(result, title=title)
    st.plotly_chart(fig, use_container_width=True)

    # ===== 数据表格 =====
    with st.expander("📋 查看回测明细数据"):
        display_df = result[["date", "close", "hold_value", "total_cost", "return_rate"]].copy()
        display_df.columns = ["日期", "收盘价", "持仓市值", "累计投入", "累计收益率(%)"]
        display_df["日期"] = display_df["日期"].dt.strftime("%Y-%m-%d")
        display_df["收盘价"] = display_df["收盘价"].round(4)
        display_df["持仓市值"] = display_df["持仓市值"].round(2)
        display_df["累计投入"] = display_df["累计投入"].round(2)
        display_df["累计收益率(%)"] = display_df["累计收益率(%)"].round(2)

        st.dataframe(display_df, use_container_width=True, height=400)

        # 下载CSV
        csv = display_df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="📥 下载CSV数据",
            data=csv,
            file_name=f"etf_backtest_{etf_code}_{start_date}_{end_date}.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()