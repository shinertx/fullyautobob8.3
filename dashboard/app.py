import os, json, pandas as pd, streamlit as st, plotly.express as px, time

st.set_page_config(page_title="v26meme Dashboard", page_icon="🧠", layout="wide")
LOG_DIR = os.environ.get("LOG_DIR", "./logs")
EVENTS_PATH = os.path.join(LOG_DIR, "events.ndjson")

@st.cache_data(ttl=5)
def load_events():
    if not os.path.exists(EVENTS_PATH): return pd.DataFrame()
    try:
        with open(EVENTS_PATH, "r") as f: lines = f.readlines()
        events = [json.loads(line) for line in lines if line.strip()]
        df = pd.DataFrame(events)
        df['ts'] = pd.to_datetime(df['ts'], unit='s')
        return df.sort_values('ts', ascending=False)
    except: return pd.DataFrame()

events_df = load_events()
st.title("🧠 v26meme — Autonomous Trading Intelligence")
if events_df.empty:
    st.warning("No events found. Is the bot running?"); st.stop()

st.caption(f"Last event: {events_df['ts'].iloc[0].strftime('%Y-%m-%d %H:%M:%S')} UTC")
col1, col2, col3, col4 = st.columns(4)
regime_events = events_df[events_df['type'] == 'sense.regime']
col1.metric("Market Regime", regime_events['payload'].iloc[0]['regime'].upper() if not regime_events.empty else "UNKNOWN")
promoted_events = events_df[events_df['type'] == 'strategy.promoted']
col2.metric("Probing Strategies", len(promoted_events[promoted_events['payload'].apply(lambda p: p.get('to_phase') == '1_probing')]['payload'].apply(lambda p: p.get('edge_id')).unique()))
col3.metric("Growth Strategies", len(promoted_events[promoted_events['payload'].apply(lambda p: p.get('to_phase') == '2_growth')]['payload'].apply(lambda p: p.get('edge_id')).unique()))
col4.metric("System Errors", len(events_df[events_df['type'] == 'system.error']))

st.subheader("Phase 0: Discovery Engine")
promo_events_df = promoted_events[promoted_events['payload'].apply(lambda p: p.get('to_phase') == '1_probing')].copy()
if not promo_events_df.empty:
    def get_stats(p): return p.get('stats', {})
    sim_stats = pd.json_normalize(promo_events_df['payload'].apply(get_stats))
    sim_stats['name'] = promoted_events['payload'].apply(lambda p: p.get('edge_id'))
    st.dataframe(sim_stats[['name', 'n_trades', 'sortino', 'mdd', 'win_rate', 'expectancy']].round(3))
else:
    st.info("No strategies promoted from incubation yet.")

st.subheader("Recent Events")
st.dataframe(events_df[['ts', 'type', 'payload']].head(50))
time.sleep(15)
st.rerun()
