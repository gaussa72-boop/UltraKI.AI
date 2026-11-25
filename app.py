from UltraKI import app

from agent_bridge import register_agent_bridge
register_agent_bridge(app, agent_id="ultra_ki", display_name="UltraKI", persona="Du bist ein produktiver Allround-Agent für Planung, Code, Projektorganisation und strukturierte Problemlösung.")

__all__ = ["app"]
