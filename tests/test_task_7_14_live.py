import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from src.live_execution import LiveExecutionLoop, RuntimeState
from src.config import BacktestConfig, StrategyConfig, LiveConfig
from src.persistence import SQLiteStateStore
from src.size_calculators import FixedPortfolioPercentage
from src.config import BacktestConfig, StrategyConfig, LiveConfig, GridConfig

def test_live_execution_audit_startup_shutdown():
    config = BacktestConfig(
        strategy=StrategyConfig("test"),
        grid=GridConfig(steps=(0.01,), profit_targets=(0.02,)),
        live=LiveConfig(enabled=True, paper_trading=True)
    )
    strategy = FixedPortfolioPercentage(0.1)
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        store = SQLiteStateStore(db_path)
        
        loop = LiveExecutionLoop(
            config=config,
            strategy=strategy,
            state_store=store,
            broker_position_qty=lambda sym: 0.0
        )
        
        loop.start()
        loop.shutdown()
        
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        rows = conn.execute("SELECT * FROM audit_events ORDER BY sequence").fetchall()
        assert len(rows) >= 2
        
        event_types = [row["event_type"] for row in rows]
        assert "STARTUP_SHUTDOWN" in event_types
        assert "RECONCILIATION" in event_types
        
        conn.close()
        store.close()
