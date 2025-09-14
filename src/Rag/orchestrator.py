from agents import TipAgent, MetaAgent, RoutineAgent

def Orchestrator(game: str, query: str) -> str:
    tips = TipAgent(game, query)
    meta = MetaAgent(game)
    routine = RoutineAgent(game)
    return f"--- Tips ---\n{tips}\n\n--- Meta ---\n{meta}\n\n--- Routine ---\n{routine}"
