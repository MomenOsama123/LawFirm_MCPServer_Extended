from mcp_server.memory.short_term import RollingBuffer, Scratchpad


def test_pruning_buffer_does_not_affect_scratchpad():
    buffer = RollingBuffer()
    scratchpad = Scratchpad()

    buffer.add_message("user", "Hello")
    buffer.add_message("assistant", "Hi")

    scratchpad.set_plan("Book a flight")
    scratchpad.set_subgoal("Search flights")
    scratchpad.update_state("destination", "Alexandria")

    buffer.prune(0)

    assert len(buffer) == 0

    assert scratchpad.current_plan == "Book a flight"
    assert scratchpad.active_subgoal == "Search flights"
    assert scratchpad.get_state("destination") == "Alexandria"