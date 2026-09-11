# UltraKI.AI

Flask-basierter UltraKI-Prototyp mit Registrierung, Login, SQLite-Chatverlauf und OpenAI-Anbindung.

## Analyse
Der vorhandene `UltraKI.py` verweist auf fehlende Templates und enthält unsichere Fallback-Secret-Keys sowie einen zu breiten `except`. Diese Punkte werden in der nächsten Code-Bereinigung behoben. `Design.html` bleibt als Designartefakt erhalten.

## Konfiguration
`OPENAI_API_KEY` und optional `SECRET_KEY` über Umgebungsvariablen setzen; keine Schlüssel ins Repository schreiben.
