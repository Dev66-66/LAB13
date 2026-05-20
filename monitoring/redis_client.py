import redis as redis_lib


class MonitoringRedisClient:
    """Агрегирует данные о состоянии агентов из Redis для дашборда мониторинга."""

    def __init__(self, rdb: redis_lib.Redis) -> None:
        self.rdb = rdb

    def get_all_agents(self) -> list[dict]:
        """Сканирует agent:*:status и возвращает список агентов с их метриками."""
        agents: list[dict] = []
        cursor = 0
        while True:
            cursor, keys = self.rdb.scan(cursor, match="agent:*:status", count=100)
            for key in keys:
                key_str = key.decode() if isinstance(key, bytes) else key
                parts = key_str.split(":")
                if len(parts) < 3:
                    continue
                agent_id = ":".join(parts[1:-1])

                status_raw = self.rdb.get(key)
                status = status_raw.decode() if status_raw else "offline"

                tasks_raw = self.rdb.get(f"agent:{agent_id}:tasks_processed")
                tasks = int(tasks_raw) if tasks_raw else 0

                role = agent_id.rsplit("-", 1)[0] if "-" in agent_id else agent_id

                agents.append({
                    "id": agent_id,
                    "role": role,
                    "status": status,
                    "tasks_processed": tasks,
                })
            if cursor == 0:
                break
        return agents

    def get_system_metrics(self) -> dict:
        """Возвращает агрегированные метрики системы: агенты, задачи, масштабирование."""
        agents = self.get_all_agents()
        total_agents = len(agents)
        online_agents = sum(1 for a in agents if a["status"] != "offline")
        total_tasks = sum(a["tasks_processed"] for a in agents)
        scaled_agents = self.rdb.scard("scaled_agents") or 0
        return {
            "total_agents": total_agents,
            "online_agents": online_agents,
            "total_tasks_processed": total_tasks,
            "scaled_agents": int(scaled_agents),
        }
