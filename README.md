# v26meme — The 90-Day Gambit

**Mission:** To architect and deploy a fully autonomous intelligence capable of turning $200 into $1,000,000 in 90 days.

**The North Star:** To achieve a 5,000x return through relentless, machine-driven discovery and exploitation of market inefficiencies. The PnL is the only measure of success.

---

## Architecture Overview

The system is an event-driven, phased autonomous agent designed for extreme capital velocity. It promotes strategies through a series of rigorous, automated validation gates, moving from hyper-incubation to aggressive compounding at machine speed.

### The Autonomous Phased Mandate

This is the core risk management pipeline. No strategy can risk significant capital without proving its worth in an evidence-based process.

1.  **Phase 0: Hyper-Incubation (Continuous)**
    *   **Goal:** Discover a statistically significant market edge with high frequency. The system must generate and discard thousands of strategies per day.
    *   **Process:** The Genetic Engine in `research/` evolves `StrategyCard` variations and backtests them in `SimLab`.
    *   **Promotion Rule:** A strategy graduates *only* if it meets hyper-aggressive performance criteria (high Sortino, low MDD, high trade frequency).

2.  **Phase 1: Rapid Validation (Micro-Capital)**
    *   **Goal:** Prove the incubated edge survives real-world costs with minimal delay.
    *   **Process:** Deploys graduates with a tiny, fixed capital allocation (e.g., $5). All execution data is fed back to `FieldLab` to refine cost models in real-time.
    *   **Promotion Rule:** Graduates *only* if it remains profitable after fees and slippage over a statistically significant number of live trades.

3.  **Phase 2: Aggressive Compounding (Risk-Managed Capital)**
    *   **Goal:** Apply maximum calculated risk to the proven edge to achieve exponential growth.
    *   **Process:** Uses a context-aware bandit allocator and **Fractional Kelly** sizing to determine the optimal position size for maximum geometric growth.
    *   **Promotion Rule:** The system scales its risk as the portfolio grows, constantly recalculating its optimal bet size to balance growth with the risk of ruin.

### Core Components

-   **Strategy DSL (`core/dsl.py`):** The system's language. `StrategyCard` and `Gene` objects form the immutable DNA of every trading hypothesis.
-   **Discovery Engine (`research/`):** The creative heart. A genetic algorithm that evolves entire strategies, combining genes to discover novel market edges.
-   **4-Lab Stack (`labs/`):** The validation and learning environment.
    -   `SimLab`: A high-speed backtesting engine for Phase 0 incubation.
    -   `FieldLab`: Learns real-world costs (slippage, fees) from live trades in Phase 1.
    -   *(Future)* `CounterfactualLab`: Will explore "what if" scenarios.
    -   *(Future)* `WorldLab`: Will run macro-level simulations of the entire portfolio.
-   **Allocator (`allocation/allocator.py`):** The capital manager. A context-aware Multi-Armed Bandit that intelligently assigns capital to the most promising strategies for the current market regime.
-   **Policy-as-Code (`core/policy.py`):** The supreme risk authority. A central engine that enforces global risk rules (e.g., portfolio drawdown limits) that no strategy can bypass.
-   **State & Event Store (`core/event_store.py`):** The system's memory. Logs every decision, observation, and trade to an immutable log, creating a perfect audit trail and enabling the dashboard.

---

## Quick Start (GCP Deployment)

1.  **Setup VM:** Launch a Debian/Ubuntu VM on GCP (e.g., `e2-medium`).
2.  **Install Code:** Use the master script provided by your technical co-founder.
3.  **Configure Environment:** Create/edit the `.env` file. For live operation, use GCP Secret Manager.
4.  **Bootstrap:** `python -m v26meme.cli bootstrap`
5.  **Run Autonomously:**
    *   `tmux new -s trading_session`
    *   `python -m v26meme.cli loop` (Detach with Ctrl+B, then D)
6.  **Launch Dashboard:**
    *   `tmux new -s dashboard_session`
    *   `streamlit run dashboard/app.py` (Ensure port 8501 is open in GCP firewall)

---

## **EXTREME RISK DISCLAIMER**

This project's goal is to achieve a **~9.89% compounded daily return**, a hyper-aggressive target that carries a **profound and probable risk of total capital loss.** This is a high-stakes research project, not a guaranteed investment. Do not run this system with capital you are not prepared to lose entirely. You are 100% responsible for all financial outcomes.