from collections import deque #for rolling buffer 
from typing import Any      #for user messages


class RollingBuffer:
    """
    Stores only the rolling conversation history.
    Pruning this buffer must never affect the Scratchpad.
    """
    def __init__(self,max_messages:int =100):
        self.max_messages=max_messages
        self.messages=deque(maxlen=max_messages)

    def add_message(self,role:str,content:str):
        self.messages.append({
            "role":role,
            "content":content
        })
        
    def prune(self , keep_last:int):
        """
            Keep only the last `keep_last` messages.
        """
        if keep_last<=0:
            self.messages.clear()
            return
        
        self.messages=deque(
            list(self.messages)[-keep_last:],
            maxlen=self.max_messages
        )
        
    def get_messages(self):
        return list(self.messages)
    
    
    def __len__(self):
        return len(self.messages)
    
    


class Scratchpad:
        """
            Holds the agent's current reasoning state.
            Completely independent from the RollingBuffer.
        """
    
        def __init__(self):
            self.current_plan=None
            self.active_subgoal=None
            self.working_state={}

        def set_plan(self,plan:str):
            self.current_plan=plan
        
        def set_subgoal(self,subgoal:str):
            self.active_subgoal=subgoal

        def update_state(self, key: str, value: Any):            
            self.working_state[key]=value
            
        def get_state(self,key:Any):
            return self.working_state.get(key)        
        
        
        def clear(self):
            self.current_plan=None
            self.active_subgoal=None
            self.working_state.clear()