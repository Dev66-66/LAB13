import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from auction import AuctionManager, AgentBid


def test_select_cheapest_agent():
    bids = [
        AgentBid("a1", "qa", 5, "idle"),
        AgentBid("a2", "qa", 2, "idle"),
        AgentBid("a3", "qa", 8, "idle"),
    ]
    winner = AuctionManager().select_winner(bids)
    assert winner.agent_id == "a2"


def test_busy_agent_not_selected():
    bids = [
        AgentBid("a1", "qa", 1000, "busy"),
        AgentBid("a2", "qa", 3, "idle"),
    ]
    winner = AuctionManager().select_winner(bids)
    assert winner.agent_id == "a2"


def test_empty_bids_returns_none():
    assert AuctionManager().select_winner([]) is None
