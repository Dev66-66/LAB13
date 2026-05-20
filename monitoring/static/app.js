async function refreshStats() {
  try {
    const data = await fetch('/api/stats').then(r => r.json());

    // Метрики
    const el = id => document.getElementById(id);
    if (el('agentsOnline'))  el('agentsOnline').textContent  = data.agents_online;
    if (el('totalTasks'))    el('totalTasks').textContent    = data.total_tasks_processed;
    if (el('scaledAgents'))  el('scaledAgents').textContent  = data.scaled_agents;

    // Карточки агентов
    if (Array.isArray(data.agents)) {
      data.agents.forEach(agent => {
        const card = document.querySelector(`[data-agent-id="${agent.id}"]`);
        if (!card) return;
        card.className = `card status-${agent.status}`;
        const statusEl = card.querySelector('.agent-status');
        if (statusEl) {
          statusEl.className = `agent-status badge-${agent.status}`;
          statusEl.textContent = agent.status;
        }
        const tasksEl = card.querySelector('.agent-tasks');
        if (tasksEl) tasksEl.textContent = `${agent.tasks_processed} tasks`;
      });
    }

    // Время последнего обновления
    const lastUpdated = el('lastUpdated');
    if (lastUpdated) {
      lastUpdated.textContent = `Last updated: ${new Date().toLocaleTimeString('ru-RU')}`;
    }

    // Мигание точки — фиолетовый на 300 мс
    const dot = el('refreshDot');
    if (dot) {
      dot.style.background = 'var(--accent)';
      setTimeout(() => { dot.style.background = ''; }, 300);
    }
  } catch (err) {
    console.error('Refresh error:', err);
  }
}

setInterval(refreshStats, 5000);
