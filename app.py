"""
Streamlit 主界面 — ETF定投回测工具
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from typing import Dict
import pathlib as _pl_pathlib
import json as _json
import base64 as _b64

from data_fetcher import get_asset_history, list_available_assets
from backtest import backtest_multi_dca
from charts import plot_profit_curve, plot_return_rate_curve

st.set_page_config(page_title="ETF定投回测", page_icon="📊", layout="wide", initial_sidebar_state="collapsed")

MAX_ASSETS = 10

PRESET_PORTFOLIOS: Dict[str, list] = {
    "经典股债平衡": ["沪深300ETF(510300)", "中证红利ETF(515080)", "纳指ETF(513100)"],
    "全球分散投资": ["纳指ETF(513100)", "日经225ETF(513000)", "标普500ETF(513500)", "沪深300ETF(510300)"],
    "红利+现金流": ["中证红利ETF(515080)", "自由现金流ETF(159585)"],
    "科技成长": ["纳指ETF(513100)", "半导体ETF(512480)", "创业板ETF(159915)"],
    "高股息防守": ["中证红利ETF(515080)", "自由现金流ETF(159585)", "港股红利ETF(513820)"],
    "自定义": None,
}

# CSS
st.markdown("""
<style>
    .block-container { max-width: 1400px; padding: 2.5rem 1.5rem 1rem 1.5rem; }
    .stApp > header, #MainMenu, .stDeployButton { display: none; }
    .main-title { font-size: 1.8rem; font-weight: 700; text-align: center; margin-top: 1rem; padding-top: 0.5rem; }
    .subtitle { text-align: center; color: #6B7280; font-size: 0.85rem; margin-top: -0.2rem; margin-bottom: 1rem; }
    .footer { text-align: center; color: #9CA3AF; font-size: 0.8rem; margin-top: 1.5rem; padding-top: 0.8rem; border-top: 1px solid #E5E7EB; width: 100%; }
    .footer a { color: #2962FF; text-decoration: none; }
    div[data-testid="stMetricValue"] { font-size: 1.2rem; font-weight: 700; }
    div[data-testid="stMetricLabel"] { font-size: 0.75rem; }
    div[data-testid="stHorizontalRadio"] label { font-size: 0.9rem; font-weight: 600; padding: 0.4rem 1.2rem; }
    div[data-testid="stHorizontalRadio"] { gap: 0.2rem; }
</style>
""", unsafe_allow_html=True)


st.markdown('<div class="main-title">📊 多标的组合回测工具</div>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">测试不同ETF组合的长期表现</p>', unsafe_allow_html=True)

# -- Left: params | Right: results --
col_left, col_right = st.columns([3, 7])

with col_left:
    with st.container(border=True):
        preset_names = list(PRESET_PORTFOLIOS.keys())
        preset_index = preset_names.index("自定义") if "自定义" in preset_names else 0
        selected_preset = st.selectbox("预设组合", preset_names, index=preset_index)
        preset_assets = PRESET_PORTFOLIOS.get(selected_preset)

        st.divider()

        today = date.today()
        default_start = date(today.year - 10, today.month, 1)
        c1, c2 = st.columns(2)
        with c1:
            start_date = st.date_input("开始", value=default_start, max_value=today)
        with c2:
            end_date = st.date_input("结束", value=today, max_value=today, min_value=start_date)

        st.divider()

        # Collapsible expander for investment mode
        with st.expander("⚙️ 投资模式设置", expanded=False):
            dca_mode = st.radio(
                "投资方式",
                ["月度定投", "周定投", "一次性投入"],
                index=0,
                horizontal=True,
                label_visibility="collapsed",
            )
            if dca_mode == "一次性投入":
                total_investment = st.number_input("总资金(元)", min_value=1000.0, max_value=100_000_000.0,
                                                    value=100_000.0, step=10_000.0, format="%.0f")
                st.caption("一次性投入：首交易日全部买入")
                num_installments = 1
                dca_day = 1
            else:
                c1, c2 = st.columns(2)
                with c1:
                    total_investment = st.number_input("总资金(元)", min_value=1000.0, max_value=100_000_000.0,
                                                        value=100_000.0, step=10_000.0, format="%.0f")
                with c2:
                    if dca_mode == "月度定投":
                        max_times = 600
                        default_times = 12
                        help_text = "每月几号买入（非交易日顺延）"
                    else:
                        max_times = 600
                        default_times = 48
                        help_text = "每周最后一个交易日买入"
                    num_installments = st.number_input("定投次数", min_value=1, max_value=max_times,
                                                        value=default_times, step=1)
                if dca_mode == "月度定投":
                    dca_day = st.slider("定投日", 1, 28, 1, help=help_text)
                else:
                    dca_day = 1
                per_amount = total_investment / num_installments
                st.caption(f"每次 ¥{per_amount:,.0f}")

        st.divider()

        all_options = list(list_available_assets().keys())
        if preset_assets is not None:
            default_sel = [x for x in preset_assets if x in all_options]
        else:
            default_sel = [x for x in ["沪深300ETF(510300)", "中证红利ETF(515080)", "纳指ETF(513100)", "日经225ETF(513000)", "自由现金流ETF(159585)"] if x in all_options]
        selected_assets = st.multiselect("ETF标的", all_options, default=default_sel, max_selections=MAX_ASSETS, placeholder="搜索...")
        if not selected_assets:
            st.warning("请至少选1个标的")
            st.stop()
        st.caption(f"已选 {len(selected_assets)}/{MAX_ASSETS}")

        st.divider()

        # Weights (simple equal-weight input)
        n_assets = len(selected_assets)
        
        # Init session_state weights if needed
        for asset in selected_assets:
            if f"w_{asset}" not in st.session_state:
                st.session_state[f"w_{asset}"] = 100.0 / n_assets

        # Show weight inputs
        for asset in selected_assets:
            st.number_input(asset, key=f"w_{asset}", min_value=0.0, max_value=100.0,
                            step=1.0, format="%.0f")

        # Calculate total weight from current widget values
        total_w = sum(st.session_state.get(f"w_{a}", 0) for a in selected_assets)

        if total_w > 0:
            ok = abs(total_w - 100) < 0.1
            st.caption(f"总权重: {total_w:.0f}% {'✅' if ok else '⚠️ 需=100%'}")
            if not ok:
                if st.button("归一化"):
                    for a in selected_assets:
                        st.session_state[f"w_{a}"] = round(st.session_state[f"w_{a}"] / total_w * 100, 1)
                    st.rerun()

        if total_w > 0:
            actual_weights = {a: st.session_state[f"w_{a}"] / total_w for a in selected_assets}
        else:
            actual_weights = {a: 1.0 / n_assets for a in selected_assets}

        st.divider()

        run = st.button("🚀 开始回测", type="primary", use_container_width=True)
        if run:
            st.session_state.has_run = True

# ===== Right panel =====
with col_right:
    if not st.session_state.get("has_run", False):
        st.info("👈 设置参数后点击 **开始回测**")
    else:
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")
        start_dash = start_date.strftime("%Y-%m-%d")
        end_dash = end_date.strftime("%Y-%m-%d")

        # Build param hash to detect changes
        param_key = f"{start_str}_{end_str}_{sorted(selected_assets)}_{sorted(actual_weights.items())}_{total_investment}_{num_installments}_{dca_day}_{dca_mode}"
        if "params_hash" not in st.session_state or st.session_state.params_hash != param_key:
            # Clear older cached benchmark data
            for k in list(st.session_state.keys()):
                if k.startswith("bm_"):
                    del st.session_state[k]
            # Fetch portfolio assets
            price_dict = {}
            pb = st.progress(0, text="获取数据...")
            ok = True
            for i, name in enumerate(selected_assets):
                pb.progress((i + 1) / len(selected_assets), text=f"📥 {name}")
                try:
                    df = get_asset_history(name, start_str, end_str)
                    if df.empty:
                        st.error(f"❌ {name} 无数据"); ok = False; break
                    price_dict[name] = df
                except Exception as e:
                    st.error(f"❌ {name}: {e}"); ok = False; break
            pb.empty()
            if not ok or not price_dict:
                st.stop()

            st.session_state.price_dict_cache = price_dict

            with st.spinner("🔄 回测计算..."):
                try:
                    result = backtest_multi_dca(
                        price_dict=price_dict, weights=actual_weights,
                        total_investment=total_investment, num_installments=num_installments,
                        start_date=start_dash, end_date=end_dash, dca_day=dca_day,
                        dca_mode=dca_mode,
                    )
                    st.session_state.result_cache = result
                    st.session_state.params_hash = param_key
                except Exception as e:
                    st.error(f"❌ {e}"); st.stop()

        result = st.session_state.result_cache
        s = result["summary"]
        pdf = result["portfolio"]

        # 5 metrics
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("总收益率", f"{s['总收益率%']:.2f}%")
        m2.metric("年化收益率", f"{s['年化收益率%']:.2f}%")
        m3.metric("最大回撤", f"-{s['最大回撤%']:.2f}%")
        m4.metric("夏普比率", f"{s['夏普比率']:.2f}")
        m5.metric("最终资产", f"¥{s['最终市值']:,.0f}")

        # Benchmark selector (radio row)
        benchmark_options = ["无对比", "沪深300指数(000300)", "标普500ETF(513500)"]
        bm_key = "benchmark_selected"
        if bm_key not in st.session_state:
            st.session_state[bm_key] = "无对比"
        bm_col1, bm_col2 = st.columns([2, 5])
        with bm_col1:
            st.caption("📊 基准对比")
        with bm_col2:
            st.session_state[bm_key] = st.radio(
                "基准",
                benchmark_options,
                index=benchmark_options.index(st.session_state[bm_key]),
                horizontal=True,
                label_visibility="collapsed",
            )

        # Tab radio for chart switching
        chart_tab = st.radio(
            "图表选择", ["📈 收益率", "💰 收益额"],
            index=0, horizontal=True, label_visibility="collapsed",
        )

        # Cache and fetch benchmark data
        bm_label = st.session_state[bm_key]
        bm_df = None
        if bm_label != "无对比" and bm_label:
            bm_cache_key = f"bm_{bm_label}"
            if bm_cache_key not in st.session_state:
                try:
                    bm_raw = get_asset_history(bm_label, start_str, end_str)
                    if not bm_raw.empty:
                        first_close = bm_raw["close"].iloc[0]
                        if first_close > 0:
                            bm_raw["return_rate"] = (bm_raw["close"] / first_close - 1) * 100
                            st.session_state[bm_cache_key] = bm_raw
                except Exception:
                    pass
            bm_df = st.session_state.get(bm_cache_key)

        # Show selected chart
        with st.container(border=True):
            bm_label_for_chart = bm_label if bm_label != "无对比" else None
            if chart_tab == "📈 收益率":
                fig = plot_return_rate_curve(pdf, benchmark_label=bm_label_for_chart, benchmark_df=bm_df)
            else:
                fig = plot_profit_curve(pdf, benchmark_label=bm_label_for_chart, benchmark_df=bm_df, total_investment=s["总投入"])
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "staticPlot": False, "scrollZoom": False, "doubleClick": False})

        # Detail table
        st.divider()
        rows = []
        for name, info in s["资产明细"].items():
            rows.append({"标的": name, "权重%": info["权重%"], "收益%": info["收益率%"], "市值": f"¥{info['最终市值']:,.0f}"})
        st.dataframe(pd.DataFrame(rows).sort_values("权重%", ascending=False).reset_index(drop=True),
                     use_container_width=True, hide_index=True, column_config={
                         "标的": st.column_config.TextColumn("标的"),
                         "权重%": st.column_config.NumberColumn("权重%", format="%.1f%%"),
                         "收益%": st.column_config.NumberColumn("收益%", format="%.2f%%"),
                         "市值": st.column_config.TextColumn("市值"),
                     })

        c1, c2, c3 = st.columns(3)
        c1.write(f"总投入: ¥{s['总投入']:,.0f}")
        c2.write(f"总收益: ¥{s['收益额']:+,.0f}")
        strategy_label = s.get("策略", "月度定投")
        c3.write(f"{strategy_label} / {s.get('定投总次数', 0)}次 / {s['年数']:.1f}年")

# ---- 浏览计数 ----
_visitor_file = _pl_pathlib.Path(__file__).parent / "_visitor_count.json"
_today_str = date.today().isoformat()
if "_visitor_counted" not in st.session_state:
    _visitor_data = {"total": 0, "daily": {}}
    if _visitor_file.exists():
        try:
            _visitor_data = _json.loads(_visitor_file.read_text(encoding="utf-8"))
        except Exception:
            _visitor_data = {"total": 0, "daily": {}}
    _visitor_data["total"] = _visitor_data.get("total", 0) + 1
    _daily_map = _visitor_data.get("daily", {})
    _daily_map[_today_str] = _daily_map.get(_today_str, 0) + 1
    _visitor_data["daily"] = _daily_map
    try:
        _visitor_file.write_text(_json.dumps(_visitor_data, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass
    st.session_state._visitor_counted = True
_visitor_data = {"total": 1, "daily": {_today_str: 1}}
if _visitor_file.exists():
    try:
        _visitor_data = _json.loads(_visitor_file.read_text(encoding="utf-8"))
    except Exception:
        pass
_today_visitors = _visitor_data.get("daily", {}).get(_today_str, 0)
_total_visitors = _visitor_data.get("total", 0)

st.markdown(
    '<div style="text-align:center; color:#9CA3AF; font-size:0.75rem; margin-top:1.5rem; padding-top:0.5rem; border-top:1px solid #E5E7EB; line-height:1.6;">'
    '⚠️ <strong>免责声明</strong>：投资有风险，本工具仅为历史数据回测，不构成任何投资建议，不对数据准确性及未来收益负责。</div>',
    unsafe_allow_html=True,
)

st.markdown(
    f'<div class="footer">🛠️ <strong>makeby 牧濑红莉栖 & Cline</strong> &nbsp;|&nbsp; 今日 {_today_visitors} 次 &nbsp;·&nbsp; 累计 {_total_visitors} 次</div>',
    unsafe_allow_html=True,
)

# ---- 彩蛋 ----
_egg_img_path = _pl_pathlib.Path(__file__).parent / "egg.jpg"
_egg_img_b64 = _b64.b64encode(_egg_img_path.read_bytes()).decode() if _egg_img_path.exists() else ""

_egg_q = [
    # 原始 20 条
    "这、这可不是为了你才做的！", "谁是助手啊！", "不准叫我克里斯蒂娜！",
    "你是笨蛋吗？还是快死了？", "别一本正经地说中二台词啊！", "我只是稍微有点在意而已。",
    "哼，我才没有担心你。", "你那贫弱的大脑终于开始运转了吗？", "妄想也该有个限度吧。",
    "真拿你没办法……", "世界又不是围着你转的。", "这、这种事情我怎么可能会高兴啊！",
    "少得意忘形了。", "你的逻辑漏洞多到让我头疼。", "别靠这么近！",
    "我只是出于科学兴趣才帮你的。", "你脑子里的电波能不能停一下？", "才不是因为喜欢你才留下来的。",
    "真是个让人操心的家伙。", "哼，下次可别指望我还会帮你。",
    # 新增 20 条（由用户提供）
    "不要叫我克里斯蒂娜！！你这个笨蛋变态中二病！！", "我才没有脸红！这只是物理现象！",
    "让我来帮助你就直说，何必拐弯抹角的。", "哼，勉强夸你一句，可别得意忘形啊。",
    "你……你这种态度，会让人误会的！", "真搞不懂，为什么我非得陪你做这种蠢事……",
    "不管在哪条世界线，你都不是一个人。不管在哪条世界线，我都一定会找到你。",
    "未来是没有人能预测的，是无法重来的。正因如此，人们才能接受各种痛苦、不幸与飞来横祸，迈步前进。",
    "时间根据每个人的主观感受，既会变长，也会变短。相对论真是既浪漫又伤感的东西呢。",
    "不要想一味的改变现在，这只会让过去变得面目全非罢了。",
    "无论发生什么，只要你相信自己，就一定能够克服困难。", "过去的事情无法改变，但我们可以选择如何面对它。",
    "……我只是在陈述事实而已，别想太多了！", "我可没有在担心你，只是顺便看看而已！",
    "你以为这样就能敷衍过去吗？太天真了！", "听好了！这只是科学上的必然结果，才不是因为你！",
    "开什么玩笑！我可是认真在讨论的！", "不要擅自在那里自以为了解我！",
    "如果你只是想来嘲讽我的话，请回吧。", "我都说了，不要随便决定别人的事情！",
]
_egg_q_json = _json.dumps(_egg_q, ensure_ascii=False)

st.components.v1.html(f"""
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:-apple-system,BlinkMacSystemFont,sans-serif; }}
#egg-trigger {{ display:inline-block; color:#9CA3AF; font-size:0.75rem; cursor:pointer; text-decoration:underline; text-underline-offset:2px; background:transparent; border:none; padding:0; }}
#egg-trigger:hover {{ color:#D1D5DB; }}
#egg-overlay {{ display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; z-index:999999; background:rgba(0,0,0,0.25); justify-content:center; align-items:center; }}
#egg-overlay.show {{ display:flex; }}
#egg-img {{ max-height:95vh; max-width:95vw; width:auto; height:auto; border-radius:12px; display:block; user-select:none; object-fit:contain; box-shadow:0 4px 30px rgba(0,0,0,0.35); position:relative; z-index:1; }}
@media (max-width:768px) {{ #egg-img {{ max-height:98vh; max-width:98vw; object-fit:contain; }} }}
#egg-close {{ position:fixed; top:20px; right:20px; z-index:9999999; background:rgba(0,0,0,0.5); color:#fff; border:none; border-radius:50%; width:40px; height:40px; font-size:22px; cursor:pointer; line-height:40px; text-align:center; padding:0; backdrop-filter:blur(4px); transition:all 0.2s; }}
#egg-close:hover {{ background:rgba(0,0,0,0.7); transform:scale(1.1); }}
.dm-el {{ position:fixed; font-size:19px; font-weight:600; text-shadow:0 0 8px rgba(0,0,0,.95),0 0 4px rgba(0,0,0,.8),0 0 2px #000; white-space:nowrap; z-index:999999; opacity:1; transition:opacity 0.5s ease; pointer-events:none; }}
</style>
<div style="text-align:center; padding:0; margin:0;">
  <button id="egg-trigger">✉️ frostbitem@foxmail.com</button>
</div>
<div id="egg-overlay">
  <img id="egg-img" src="data:image/jpeg;base64,{_egg_img_b64}">
  <button id="egg-close">✕</button>
</div>
<script>
(function(){{
  var quotes = {_egg_q_json};
  var doc = document;
  var overlay = doc.getElementById('egg-overlay');
  var img = doc.getElementById('egg-img');
  var closeBtn = doc.getElementById('egg-close');
  var trigger = doc.getElementById('egg-trigger');
  if(!overlay||!img||!trigger) return;
  var activeDanmaku = 0;
  var MAX_DM = 20;
  var colors = ['#FFD700','#FF6B6B','#00E5FF','#69F0AE','#FF4081','#E040FB','#40C4FF','#FFD740','#FFAB40','#B388FF'];
  var fullscreenEl = doc.documentElement;
  function enterFull() {{
    var el = fullscreenEl;
    if(el.requestFullscreen) el.requestFullscreen();
    else if(el.webkitRequestFullscreen) el.webkitRequestFullscreen();
    else if(el.msRequestFullscreen) el.msRequestFullscreen();
  }}
  function exitFull() {{
    var d = doc;
    if(d.exitFullscreen) d.exitFullscreen();
    else if(d.webkitExitFullscreen) d.webkitExitFullscreen();
    else if(d.msExitFullscreen) d.msExitFullscreen();
  }}
  function show() {{
    overlay.classList.add('show');
    enterFull();
  }}
  function hide() {{
    overlay.classList.remove('show');
    exitFull();
    var els = overlay.querySelectorAll('.dm-el');
    for(var i=0;i<els.length;i++) els[i].remove();
    activeDanmaku = 0;
  }}
  trigger.addEventListener('click', function(e){{ e.preventDefault(); show(); }});
  if(closeBtn) closeBtn.addEventListener('click', function(e){{ e.stopPropagation(); e.preventDefault(); hide(); }});
  overlay.addEventListener('click', function(e){{ if(e.target===overlay) hide(); }});
  doc.addEventListener('fullscreenchange', function() {{
    if(!doc.fullscreenElement && overlay.classList.contains('show')) hide();
  }});
  doc.addEventListener('webkitfullscreenchange', function() {{
    if(!doc.webkitFullscreenElement && overlay.classList.contains('show')) hide();
  }});
  function getDanmakuPosition() {{
    // Place text in safe viewport zone: 5%-65% left, 5%-85% top
    // This ensures text (max 40vw wide) stays fully visible
    var lMin=25, lMax=65, tMin=20, tMax=80; // image exclusion zone
    var lPct, tPct;
    for(var tries=0; tries<30; tries++) {{
      lPct = 5 + Math.random() * 60;
      tPct = 5 + Math.random() * 80;
      if(lPct < lMin || lPct > lMax || tPct < tMin || tPct > tMax) break;
    }}
    lPct = Math.max(5, Math.min(65, lPct));
    tPct = Math.max(5, Math.min(85, tPct));
    return {{leftPct:lPct, topPct:tPct}};
  }}
  img.addEventListener('click', function(e) {{
    if(activeDanmaku >= MAX_DM) return;
    var text = quotes[Math.floor(Math.random() * quotes.length)];
    var color = colors[Math.floor(Math.random() * colors.length)];
    var el = doc.createElement('div');
    el.className = 'dm-el';
    var pos = getDanmakuPosition();
    el.textContent = text;
    el.style.cssText = 'position:fixed; left:'+pos.leftPct+'vw; top:'+pos.topPct+'vh; '+
      'font-size:'+(18+Math.floor(Math.random()*6))+'px; font-weight:600; color:'+color+'; '+
      'text-shadow:0 0 8px rgba(0,0,0,.95),0 0 4px rgba(0,0,0,.8),0 0 2px #000; '+
      'white-space:nowrap; z-index:999999; opacity:1; transition:opacity 0.5s ease; '+
      'pointer-events:none;';
    overlay.appendChild(el);
    activeDanmaku++;
    setTimeout(function() {{
      if(el && el.parentNode) {{ el.style.opacity = '0';
        setTimeout(function() {{ if(el && el.parentNode) el.parentNode.removeChild(el); activeDanmaku--; }}, 500); }}
    }}, 4000);
  }});
}})();
</script>
""", height=55, scrolling=False)