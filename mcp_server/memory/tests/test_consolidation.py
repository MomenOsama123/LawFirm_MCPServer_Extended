import json
from mcp_server.memory.consolidation import MemoryConsolidator
from datetime import datetime, timedelta


def test_fact_update_creates_history(tmp_path):
    """
        Updating a fact should preserve the old version
        in the version history.
    """
    consolidator = MemoryConsolidator()
    consolidator.EPISODIC_STORE = tmp_path / "episodic_store.json"
    consolidator.SEMANTIC_STORE = tmp_path / "semantic_store.json"
    consolidator.HISTORY_STORE = tmp_path / "history_store.json"
    
    episodic_data=[
        {
            "fact":"allergy",
            "value":"None",
            "timestamp":"2026-01-01T00:00:00",
        },
        {
            "fact":"allergy",
            "value":"Penicillin",
            "timestamp":"2026-05-01T00:00:00",
        }
    ]
    
    sensory_data=[
        {
            "fact":"allergy",
            "value":"None",
        }
    ]
    with open(consolidator.EPISODIC_STORE, 'w') as f:
        json.dump(episodic_data, f)
    
    with open(consolidator.SEMANTIC_STORE, 'w') as f:
        json.dump([], f)
    
    with open(consolidator.HISTORY_STORE, 'w') as f:
        json.dump([], f)
    
    consolidator.run()
    history = consolidator.load_json(consolidator.HISTORY_STORE)
    assert len(history) >0  
    


def test_expitation_rule():
    """
        Expired facts should be marked as expired instead of being deleted.
    """  
    consolidator = MemoryConsolidator()
    semantic_data=[
        {
             "fact": "temporary_address",
            "value": "Alex",
            "expires_at": (
                datetime.now() - timedelta(days=1)).isoformat()
        }
    ]
    consolidator.apply_expiration_rule(semantic_data)
    assert semantic_data[0]["status"] == "expired"
    

def test_contradiction_resolution():
    """
    The newest episodic fact should win.
    """

    consolidator = MemoryConsolidator()

    entries = [
        {
            "fact": "allergy",
            "value": "None",
            "timestamp": "2026-01-01T00:00:00"
        },
        {
            "fact": "allergy",
            "value": "Penicillin",
            "timestamp": "2026-05-01T00:00:00"
        }
    ]

    newest, old = consolidator.resolve_contradiction(entries)

    assert newest["value"] == "Penicillin"
    assert len(old) == 1
    

def test_old_fact_is_superseded():
    """
    Old facts should never be deleted.
    """

    consolidator = MemoryConsolidator()

    semantic = [
        {
            "fact": "allergy",
            "value": "None"
        }
    ]

    history = []

    archived = consolidator.update_fact(
        semantic,
        history,
        semantic[0],
        {
            "fact": "allergy",
            "value": "Penicillin"
        }
    )

    assert archived["status"] == "superseded"
    assert "superseded_at" in archived