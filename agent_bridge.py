"""Authenticated ULTIMA specialist-agent adapter for Flask AI services."""
import hmac
import json
import os
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from flask import jsonify, request


def register_agent_bridge(app, agent_id, display_name, persona):
    @app.get("/api/agent/health")
    def ultima_agent_health():
        token = os.getenv("ULTIMA_AGENT_SHARED_TOKEN", "").strip()
        supplied = request.headers.get("X-ULTIMA-AGENT-TOKEN", "").strip()
        if not token or not supplied or not hmac.compare_digest(token, supplied):
            return jsonify(error="agent_authentication_required"), 401
        provider = bool(os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY"))
        return jsonify(agent_id=agent_id, name=display_name, status="ready" if provider else "provider_not_configured",
                       provider_configured=provider, actions="analysis_only"), 200

    @app.post("/api/agent/analyze")
    def ultima_agent_analyze():
        token = os.getenv("ULTIMA_AGENT_SHARED_TOKEN", "").strip()
        supplied = request.headers.get("X-ULTIMA-AGENT-TOKEN", "").strip()
        if not token or not supplied or not hmac.compare_digest(token, supplied):
            return jsonify(error="agent_authentication_required"), 401
        data = request.get_json(silent=True) or {}
        task = str(data.get("task") or "").strip()
        if not task:
            return jsonify(error="task_required"), 400
        if len(task) > 8000:
            return jsonify(error="task_too_large"), 413
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
        if not api_key:
            return jsonify(error="provider_not_configured"), 503
        payload = {
            "model": model,
            "temperature": 0.25,
            "messages": [
                {"role": "system", "content": "Du bist " + display_name + " im ULTIMA-Agentennetzwerk. " + persona +
                 " Analysiere nur den Auftrag. Liefere Befunde, Vorschläge, Risiken und überprüfbare Tests. " +
                 "Führe keine Codeänderungen, GitHub-Aktionen, Deployments, Zahlungen, Wallet-Signaturen oder Hardwaresteuerung aus. " +
                 "Behaupte niemals, solche Aktionen ausgeführt zu haben."},
                {"role": "user", "content": task}
            ]
        }
        req = Request(base_url + "/chat/completions",
                      data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                      headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
                      method="POST")
        try:
            with urlopen(req, timeout=40) as response:
                result = json.loads(response.read().decode("utf-8"))
            answer = (result.get("choices") or [{}])[0].get("message", {}).get("content", "")
            if not isinstance(answer, str) or not answer.strip():
                return jsonify(error="provider_empty_response"), 502
            return jsonify(agent_id=agent_id, name=display_name, answer=answer[:9000],
                           model=result.get("model", model), actions_executed=[]), 200
        except HTTPError as exc:
            return jsonify(error="provider_request_failed", provider_status=exc.code), 502
        except (URLError, TimeoutError, ValueError, KeyError):
            return jsonify(error="agent_provider_unavailable"), 502
