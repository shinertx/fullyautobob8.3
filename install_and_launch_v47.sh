#!/bin/bash
set -euo pipefail
PROJECT_DIR="/home/user/v26meme"
cd "$PROJECT_DIR"

# export .env if present
set -a
[ -f .env ] && source .env || true
set +a

# ensure Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server
redis-cli PING

# venv + deps
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# launch in tmux
tmux has-session -t trading_session 2>/dev/null || tmux new-session -d -s trading_session "bash -lc 'source .venv/bin/activate; set -a; source .env 2>/dev/null || true; set +a; python -m v26meme.cli loop'"
tmux has-session -t dashboard_session 2>/dev/null || tmux new-session -d -s dashboard_session "bash -lc 'source .venv/bin/activate; set -a; source .env 2>/dev/null || true; set +a; streamlit run dashboard/app.py --server.fileWatcherType=none'"

echo "✅ v4.7 launched: tmux sessions [trading_session, dashboard_session]"
echo "   Attach: tmux attach -t trading_session   |   tmux attach -t dashboard_session"
echo "   Detach: Ctrl+B then D"
