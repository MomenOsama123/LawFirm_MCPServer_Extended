from pathlib import Path
from collections import defaultdict
from datetime import datetime
import json

class MemoryConsolidator:
    """
         Performs a periodic consolidation pass over episodic memory.

         Responsibilities:
         - Detect contradictory facts.
         - Update semantic memory.
         - Archive superseded facts.
         - Maintain version history.
         - Apply expiration rules.

         This class is independent from the MemoryRouter and
         should be executed on a schedule or external trigger.
    """
    EPISODIC_STORE = Path(__file__).parent / "episodic_store.json"
    SEMANTIC_STORE = Path(__file__).parent / "semantic_store.json"
    HISTORY_STORE = Path(__file__).parent / "history_store.json"
    
    def load_json(self , path:Path):
        """Load data from a JSON file."""
        
        if not path.exists():
            return []
        with open(path ,"r",encoding="utf-8") as file:
            return json.load(file)
        
    def save_json(self,path:Path,data):
        """Save data to a JSON file."""
        with open(path ,"w",encoding="utf-8") as file:
            json.dump(data , file , indent=4,ensure_ascii=False)
    
    def find_contradictions(self, episodic):
        """
            Group episodic facts by their fact name and
            detect conflicting values.
         """

        grouped = defaultdict(list)

        for entry in episodic:
             grouped[entry["fact"]].append(entry)

        contradictions = {}

        for fact, entries in grouped.items():
             values = {entry["value"] for entry in entries}

             if len(values) > 1:
                 contradictions[fact] = entries

        return contradictions
    
    def resolve_contradiction(self, entries):
        """
            Resolve a contradiction by selecting
            the newest episodic entry.
        """

        entries.sort(key=lambda x: x["timestamp"])

        return entries[-1], entries[:-1]

    def update_fact(self, semantic, history, old_fact, new_fact):
        """
                Update a semantic fact while preserving the previous version.
        """

        # Archive the old fact
        archived_fact = old_fact.copy()
        archived_fact["status"] = "superseded"
        archived_fact["superseded_at"] = datetime.now().isoformat()

        # Save old version to history
        history.append({
            "fact": old_fact["fact"],
            "old_value": old_fact["value"],
            "new_value": new_fact["value"],
            "updated_at": datetime.now().isoformat()
        })

        # Replace semantic value
        old_fact["value"] = new_fact["value"]
        old_fact["updated_at"] = datetime.now().isoformat()

        return archived_fact
    
    def apply_expiration_rule(self, semantic):
        """
            Mark expired facts instead of deleting them.
        """

        now = datetime.now()

        for fact in semantic:
            expires_at = fact.get("expires_at")
    
            if not expires_at:
                continue
            
            expiration_date = datetime.fromisoformat(expires_at)
    
            if expiration_date <= now:
                fact["status"] = "expired"
                fact["expired_at"] = now.isoformat()
    
    
    def run(self):
        """
        Execute one consolidation pass.
        This method should be triggered periodically,
        not during individual writes.
        """

        episodic = self.load_json(self.EPISODIC_STORE)
        semantic = self.load_json(self.SEMANTIC_STORE)
        history = self.load_json(self.HISTORY_STORE)

        contradictions = self.find_contradictions(episodic)

        for fact, entries in contradictions.items():

            newest_fact, old_facts = self.resolve_contradiction(entries)

            existing_fact = next(
                (item for item in semantic if item["fact"] == fact),
                None
            )

            if existing_fact:
                archived = self.update_fact(
                    semantic,
                    history,
                    existing_fact,
                    newest_fact
                )

                history.append(archived)

            else:
                semantic.append(newest_fact)
                for old_fact in old_facts:
                    archived = old_fact.copy()
                    archived["status"] = "superseded"
                    archived["superseded_at"] = datetime.now().isoformat()
                    history.append(archived)
                
                
        self.apply_expiration_rule(semantic)
        self.save_json(self.SEMANTIC_STORE, semantic)
        self.save_json(self.HISTORY_STORE, history)