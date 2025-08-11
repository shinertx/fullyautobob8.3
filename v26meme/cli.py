from __future__ import annotations
import os, yaml, click, time, random
from loguru import logger
from typing import Dict
from v26meme.core.event_store import EventStore
from v26meme.core.dsl import EdgeCard
from v26meme.core.policy import Policy
from v26meme.core.regime import label_regime
from v26meme.data.ccxt_conn import get_exchange, fetch_ohlcv
from v26meme.research.generator import GeneticGenerator
from v26meme.research.triage import calculate_fitness
from v26meme.labs.simlab import run_backtest
from v26meme.labs.fieldlab import FieldLab
from v26meme.allocation.allocator import BanditAllocator

def load_config():
    with open("configs/config.yaml", "r") as f: return yaml.safe_load(f)

def setup_logging(log_dir, level):
    log_path = os.path.join(log_dir, "system.log")
    logger.add(log_path, level=level, rotation="10 MB", compression="zip", enqueue=True, backtrace=True, diagnose=True)

@click.group()
def cli(): pass

@cli.command()
def bootstrap():
    cfg = load_config()
    for key in ['DATA_DIR', 'LOG_DIR', 'STATE_DIR']:
        os.makedirs(os.environ.get(key, f'./{key.split("_")[0].lower()}'), exist_ok=True)
    click.echo("✅ Directories bootstrapped.")

@cli.command()
def loop():
    cfg = load_config()
    log_dir, state_dir = os.environ.get('LOG_DIR', './logs'), os.environ.get('STATE_DIR', './state')
    setup_logging(log_dir, cfg['system']['log_level'])
    logger.info("🚀 v26meme Autonomous Intelligence Starting...")

    es, policy, field_lab, generator, allocator = EventStore(log_dir), Policy(cfg), FieldLab(state_dir), GeneticGenerator(cfg), BanditAllocator(cfg['growth'])
    exchange = get_exchange('kraken', {'apiKey': os.environ.get('KRAKEN_API_KEY'), 'secret': os.environ.get('KRAKEN_API_SECRET')})
    
    portfolio_state = {"equity": 200.0, "cash": 200.0}
    active_edges: Dict[str, EdgeCard] = {}
    es.emit("system.start", {"config": cfg, "initial_state": portfolio_state})

    while True:
        try:
            logger.info("--- Starting new loop cycle ---")
            market_data = fetch_ohlcv(exchange, "BTC/USDT", cfg['universe']['timeframe'], cfg['universe']['fetch_limit'])
            if market_data is None:
                time.sleep(cfg['system']['loop_interval_seconds']); continue
            
            current_regime = label_regime(market_data)
            logger.info(f"Current market regime: {current_regime.upper()}")
            es.emit("sense.regime", {"regime": current_regime})

            logger.info("Entering Discovery Phase (Phase 0)...")
            fitness_scores = {}
            if not generator.population: generator.initialize_population()
            for card in generator.population:
                symbol = random.choice(cfg['universe']['symbols'])
                df = fetch_ohlcv(exchange, symbol, cfg['universe']['timeframe'], cfg['universe']['fetch_limit'])
                if df is None: continue
                sim_stats = run_backtest(df, card, cfg['execution']['paper_fees_bps'], cfg['execution']['paper_slippage_bps'])
                fitness_scores[card.id] = calculate_fitness(sim_stats)
                promo_cfg = cfg['discovery']['promotion_criteria']
                if (sim_stats.get('n_trades', 0) >= promo_cfg['min_trades'] and sim_stats.get('sortino', 0) >= promo_cfg['min_sortino'] and sim_stats.get('mdd', 1) <= promo_cfg['max_mdd'] and sim_stats.get('ci_lower_bound', -1) > promo_cfg['min_ci_lower_bound']):
                    if card.id not in active_edges:
                        edge = EdgeCard(strategy_card=card, phase="1_probing", sim_performance=sim_stats)
                        active_edges[card.id] = edge
                        logger.success(f"PROMOTED: Strategy {card.name} to Phase 1.")
                        es.emit("strategy.promoted", {"edge_id": edge.get_id(), "to_phase": "1_probing", "stats": sim_stats})
            
            generator.run_evolution_cycle(fitness_scores)
            logger.info(f"Discovery: Evolved to new generation of {len(generator.population)} strategies.")

            logger.info("Entering Allocation & Execution Phase...")
            live_edges = [e for e in active_edges.values() if e.phase in ["1_probing", "2_growth"] and e.is_active]
            if live_edges:
                for edge in live_edges:
                    if edge.phase == "1_probing" and random.random() < 0.1: # Simulate trade signal
                        pnl = cfg['live_probing']['trade_size_usd'] * random.uniform(-0.03, 0.05)
                        edge.live_trade_count += 1
                        edge.live_pnl_usd += pnl
                        allocator.update_score(edge.get_id(), current_regime, 1 if pnl > 0 else -1)
                        promo_cfg = cfg['live_probing']['promotion_criteria']
                        if (edge.live_trade_count >= promo_cfg['min_live_trades'] and edge.live_pnl_usd >= promo_cfg['min_net_pnl_usd']):
                            edge.phase = "2_growth"
                            logger.success(f"PROMOTED: Strategy {edge.strategy_card.name} to Phase 2.")
                            es.emit("strategy.promoted", {"edge_id": edge.get_id(), "to_phase": "2_growth"})
            
            logger.info(f"--- Loop cycle finished. Waiting {cfg['system']['loop_interval_seconds']}s ---")
            time.sleep(cfg['system']['loop_interval_seconds'])
        except KeyboardInterrupt:
            logger.warning("Shutdown signal received."); break
        except Exception as e:
            logger.opt(exception=True).critical(f"CRITICAL ERROR in main loop: {e}")
            es.emit("system.error", {"error": str(e)})
            time.sleep(cfg['system']['loop_interval_seconds'] * 2)
