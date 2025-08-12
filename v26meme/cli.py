import click, yaml, os, time, json, hashlib, randomfrom pathlib import Pathfrom dotenv import load_dotenvfrom loguru import loggerfrom v26meme.core.state import StateManagerfrom v26meme.data.lakehouse import Lakehousefrom v26meme.data.universe_screener import UniverseScreenerfrom v26meme.data.screener_store import ScreenerStorefrom v26meme.data.regime import label_regimefrom v26meme.research.feature_factory import FeatureFactoryfrom v26meme.research.generator import GeneticGeneratorfrom v26meme.research.sentiment_features import from_events_to_series, base_from_canonicalfrom v26meme.labs.screener_replay import dynamic_universe_oosfrom v26meme.labs.simlab import SimLabfrom v26meme.allocation.optimizer import PortfolioOptimizerfrom v26meme.execution.exchange import ExchangeFactoryfrom v26meme.execution.handler import ExecutionHandlerfrom v26meme.execution.risk import RiskManagerfrom v26meme.core.dsl import Alphadef load_config(file="configs/config.yaml"):    with open(file, "r") as f: return yaml.safe_load(f)def lagged_zscore(s, lookback=200):    m = s.rolling(lookback, min_periods=max(5, lookback//4)).mean().shift(1)    sd = s.rolling(lookback, min_periods=max(5, lookback//4)).std().shift(1)    return (s - m) / sddef _ensure_lakehouse_bootstrap(cfg):    tf = cfg['harvester_universe']['timeframe']    d = Path("data") / tf    have = list(d.glob("*.parquet"))    if not have:        # build initial lakehouse automatically        from data_harvester import harvest as _harvest        with open("configs/symbols.yaml", "r") as f:            symmap = yaml.safe_load(f)        logger.info("No lakehouse detected; harvesting initial dataset...")        _harvest(cfg, symmap)        logger.info("Initial harvest complete.")@click.group()def cli(): pass@cli.command()def loop():    load_dotenv()    cfg = load_config()    Path("logs").mkdir(exist_ok=True, parents=True)    logger.add("logs/system.log", level=cfg['system']['log_level'], rotation="10 MB", retention="14 days", enqueue=True)    logger.info("🚀 v26meme v4.7 loop starting...")    _ensure_lakehouse_bootstrap(cfg)    state = StateManager(cfg['system']['redis_host'], cfg['system']['redis_port'])    lakehouse = Lakehouse()    screener = UniverseScreener(cfg['data_source']['exchanges'], cfg['screener'])    store = ScreenerStore(cfg['screener'].get('snapshot_dir', 'data/screener_snapshots'))    feature_factory = FeatureFactory()    simlab = SimLab(cfg['execution']['paper_fees_bps'], cfg['execution']['paper_slippage_bps'])    features = ['return_1p', 'volatility_20p', 'momentum_10p', 'rsi_14', 'close_vs_sma50']    generator = GeneticGenerator(features, cfg['discovery']['population_size'])    optimizer = PortfolioOptimizer(cfg)    exchange_factory = ExchangeFactory(os.environ.get("GCP_PROJECT_ID"))    risk = RiskManager(state, cfg)    exec_handler = ExecutionHandler(state, exchange_factory, cfg, risk_manager=risk)    use_feed = cfg.get('feeds', {}).get('cryptopanic', {}).get('enabled', False)    if use_feed:        from v26meme.feeds.cryptopanic import CryptoPanicFeed        feed = CryptoPanicFeed(cfg['feeds']['cryptopanic']['window_hours'], cfg['feeds']['cryptopanic']['min_score'])    else:        feed = None    feed_scores_cache = {}    while True:        try:            logger.info("--- New loop cycle ---")            active_universe = screener.get_active_universe()            lake_syms = lakehouse.get_available_symbols(cfg['harvester_universe']['timeframe'])            tradeable = list(sorted(set(active_universe) & set(lake_syms)))            store.save(tradeable)            if not tradeable:                logger.warning("No tradeable symbols; sleeping.")                time.sleep(cfg['system']['loop_interval_seconds']); continue            logger.info(f"Tradeable: {tradeable}")            if feed:                bases = sorted({base_from_canonical(s) for s in tradeable})                feed_scores_cache = feed.scores_by_ticker(bases)            if not generator.population: generator.initialize_population()            fitness, promoted = {}, []            for formula in generator.population:                fid = hashlib.sha256(json.dumps(formula).encode()).hexdigest()                symbol = random.choice(tradeable)                df = lakehouse.get_data(symbol, cfg['harvester_universe']['timeframe'])                if df.empty:                     fitness[fid] = 0.0                    continue
                df_feat = feature_factory.create(df)
                if feed and feed_scores_cache:
                    base = base_from_canonical(symbol)
                    df_feat['sentiment_ewm'] = from_events_to_series(df_feat.index, feed_scores_cache.get(base, []))
                    if 'sentiment_ewm' not in features:
                        features.append('sentiment_ewm')
                for f in features:
                    df_feat[f] = lagged_zscore(df_feat[f], lookback=200)
                df_feat = df_feat.dropna()
                stats = simlab.run_backtest(df_feat, formula)
                overall = stats.get('all', {})
                if not overall or overall.get('n_trades',0)==0:
                    fitness[fid] = 0.0
                    continue
                mdd_mag = abs(overall.get('mdd', 1.0))
                fitness[fid] = overall.get('sortino',0) * (1 - mdd_mag)
                gate = cfg['discovery']['promotion_criteria']
                promo = (overall.get('n_trades',0) >= gate['min_trades']
                         and overall.get('sortino',0) >= gate['min_sortino']
                         and overall.get('sharpe',0) >= gate['min_sharpe']
                         and overall.get('win_rate',0) >= gate.get('min_win_rate',0.0)
                         and mdd_mag <= gate['max_mdd'])
                if promo:
                    alpha = Alpha(id=fid, name=f"alpha_{fid[:6]}", formula=formula, universe=[symbol],
                                  timeframe=cfg['harvester_universe']['timeframe'], performance=stats)
                    promoted.append(alpha.dict())
                    logger.success(f"PROMOTED: {alpha.name} on {symbol}")

            generator.run_evolution_cycle(fitness)
            logger.info("Discovery evolved to new generation.")

            active = state.get_active_alphas()
            seen = {a['id'] for a in active}
            for a in promoted:
                if a['id'] not in seen: active.append(a)

            btc = lakehouse.get_data("BTC_USD_SPOT", cfg['harvester_universe']['timeframe'])
            regime = label_regime(btc).iloc[-1] if not btc.empty else "chop"
            logger.info(f"Regime: {regime}")
            tw = optimizer.get_weights(active, regime)
            state.set("target_weights", tw)
            exec_handler.reconcile(tw, active)
            state.set_active_alphas(active)
            state.log_historical_equity(state.get_portfolio()['equity'])

            logger.info(f"Cycle done. Sleeping {cfg['system']['loop_interval_seconds']}s.")
            time.sleep(cfg['system']['loop_interval_seconds'])
        except KeyboardInterrupt:
            logger.warning("Shutdown requested.")
            break
        except Exception as e:
            logger.opt(exception=True).error(f"Loop error: {e}")
            time.sleep(cfg['system']['loop_interval_seconds']*2)

@cli.command()
@click.option("--alpha", default="best", help="Alpha id or 'best' to auto-pick highest-sortino active alpha.")
@click.option("--snapshots", default="data/screener_snapshots", help="Directory of PIT snapshots.")
@click.option("--horizon", default=8, help="Bars to hold OOS after each snapshot.")
def replay(alpha, snapshots, horizon):
    cfg = load_config()
    lake = Lakehouse()
    state = StateManager(cfg['system']['redis_host'], cfg['system']['redis_port'])
    snaps = []
    from pathlib import Path
    import json as _json
    for p in sorted(Path(snapshots).glob("*.json")):
        try:
            snaps.append(_json.loads(p.read_text()))
        except Exception:
            pass
    if not snaps:
        print("No snapshots found."); return

    if alpha == "best":
        aa = state.get_active_alphas()
        if not aa:
            print("No active alphas."); return
        aa_sorted = sorted(aa, key=lambda a: a.get('performance',{}).get('all',{}).get('sortino',0), reverse=True)
        chosen = aa_sorted[0]
        formula = chosen['formula']
        print(f"Using best alpha: {chosen['name']} ({chosen['id']})")
    else:
        aa = state.get_active_alphas()
        match = [a for a in aa if a['id'] == alpha]
        if not match:
            print(f"Alpha {alpha} not found in active set."); return
        formula = match[0]['formula']

    feed_scores = None
    if cfg.get('feeds', {}).get('cryptopanic', {}).get('enabled', False):
        from v26meme.feeds.cryptopanic import CryptoPanicFeed
        feed = CryptoPanicFeed(cfg['feeds']['cryptopanic']['window_hours'], cfg['feeds']['cryptopanic']['min_score'])
        coins = sorted({s.split('_')[0] for snap in snaps for s in snap.get('universe', [])})
        by_coin = feed.scores_by_ticker(coins)
        feed_scores = by_coin

    features = ['return_1p', 'volatility_20p', 'momentum_10p', 'rsi_14', 'close_vs_sma50']
    if feed_scores is not None:
        features.append('sentiment_ewm')

    res = dynamic_universe_oos(lake, cfg['harvester_universe']['timeframe'], snaps, formula, features, horizon_bars=horizon, feed_scores=feed_scores)
    print("PIT Replay Summary:", res)

if __name__ == '__main__':
    cli()
