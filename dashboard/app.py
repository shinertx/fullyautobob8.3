import streamlit as st, pandas as pd, redis, json, time, plotly.express as pxst.set_page_config(page_title="v26meme v4.7 Dashboard", layout="wide")@st.cache_resourcedef get_redis():    try:        r = redis.Redis(host='localhost', port=6379, decode_responses=True)        r.ping(); return r    except redis.exceptions.ConnectionError as e:        st.error(f"Redis connection failed: {e}"); return Noner = get_redis()if not r: st.stop()def get_state(key):    val = r.get(key)    return json.loads(val) if val else Nonedef equity_curve():    return [json.loads(v) for v in r.zrange('equity_curve', 0, -1)]st.title("🧠 v26meme v4.7 — The Singularity Engine")portfolio = get_state('portfolio') or {}active_alphas = get_state('active_alphas') or []target_weights = get_state('target_weights') or {}c1,c2,c3 = st.columns(3)c1.metric("Portfolio Equity", f"${portfolio.get('equity', 200):.2f}")c2.metric("Cash", f"${portfolio.get('cash', 200):.2f}")c3.metric("Active Alphas", len(active_alphas))st.subheader("Portfolio Performance")eq = equity_curve()if eq:    df = pd.DataFrame(eq)    df['ts'] = pd.to_datetime(df['ts'], unit='s')    df['drawdown'] = (df['equity'] - df['equity'].cummax()) / df['equity'].cummax()    st.plotly_chart(px.line(df, x='ts', y='equity', title='Equity'), use_container_width=True)    st.plotly_chart(px.area(df, x='ts', y='drawdown', title='Drawdown'), use_container_width=True)else:    st.info("Awaiting equity logs...")st.subheader("Target Portfolio Allocation")if target_weights:
    st.dataframe(pd.DataFrame(list(target_weights.items()), columns=['Alpha ID','Weight']).sort_values('Weight', ascending=False))
else:
    st.info("No targets yet.")

st.subheader("Active Alphas")
if active_alphas:
    flat = []
    for a in active_alphas:
        row = {'name': a['name'], 'id': a['id']}
        perf = a.get('performance', {}).get('all', {})
        row.update({k: perf.get(k) for k in ['n_trades','win_rate','sortino','sharpe','mdd']})
        flat.append(row)
    st.dataframe(pd.DataFrame(flat))
else:
    st.info("No promoted alphas yet.")

time.sleep(10)
st.rerun()
