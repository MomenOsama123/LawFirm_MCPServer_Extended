from .consolidation import MemoryConsolidator

def run_consolidation():
    """
        External trigger for the periodic consolidation pass
    """
    
    consolidator = MemoryConsolidator()
    consolidator.run()
    
if __name__=="__main__":
    run_consolidation()