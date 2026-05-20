import json
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AgentBid:
    agent_id: str
    role: str
    bid: int
    status: str


class AuctionManager:
    """Реализует аукционное распределение задач между агентами на основе данных Redis."""

    def get_agent_bids(self, rdb) -> list[AgentBid]:
        """
        Сканирует Redis по паттерну agent:*:status и формирует список ставок.
        Ставка = tasks_processed если агент idle, иначе 1000 (агент занят).
        """
        bids: list[AgentBid] = []
        cursor = 0
        while True:
            cursor, keys = rdb.scan(cursor, match="agent:*:status", count=100)
            for key in keys:
                key_str = key.decode() if isinstance(key, bytes) else key
                # Формат ключа: "agent:{id}:status" → извлекаем id
                parts = key_str.split(":")
                if len(parts) < 3:
                    continue
                agent_id = ":".join(parts[1:-1])

                status_raw = rdb.get(key)
                if status_raw is None:
                    continue
                status = status_raw.decode() if isinstance(status_raw, bytes) else status_raw

                tasks_raw = rdb.get(f"agent:{agent_id}:tasks_processed")
                tasks = int(tasks_raw) if tasks_raw else 0

                bid = tasks if status == "idle" else 1000
                # Роль выводим из ID: "query-analyzer-abc12345" → "query-analyzer"
                role = agent_id.rsplit("-", 1)[0] if "-" in agent_id else agent_id
                bids.append(AgentBid(agent_id=agent_id, role=role, bid=bid, status=status))
            if cursor == 0:
                break
        return bids

    def select_winner(self, bids: list[AgentBid]) -> AgentBid | None:
        """Выбирает агента с наименьшей ставкой среди незанятых (bid < 1000)."""
        available = [b for b in bids if b.bid < 1000]
        if not available:
            return None
        return min(available, key=lambda b: b.bid)

    def log_auction(self, bids: list[AgentBid], winner: AgentBid | None) -> None:
        """Выводит в stdout JSON с результатами аукциона."""
        data = {
            "participants": [
                {"agent_id": b.agent_id, "role": b.role, "bid": b.bid, "status": b.status}
                for b in bids
            ],
            "winner": (
                {"agent_id": winner.agent_id, "role": winner.role, "bid": winner.bid}
                if winner
                else None
            ),
        }
        print(json.dumps(data, ensure_ascii=False))
