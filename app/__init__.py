import os
from collections import defaultdict,deque
from time import monotonic
from flask import Flask,jsonify,request,send_from_directory
from openai import OpenAI
app=Flask(__name__)
MODEL=os.getenv("OPENAI_MODEL","gpt-6-astra")
WEB=os.getenv("ENABLE_WEB_SEARCH","true").lower()=="true"
client=OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None
SYSTEM="Du bist UltraKI, ein eigenständiger Spitzenassistent. Analysiere Ziele gründlich, prüfe Annahmen, trenne Fakten und Unsicherheit und liefere konkrete überprüfbare Ergebnisse. Nutze Websuche für aktuelle Informationen. Behaupte keine nicht ausgeführten Aktionen. Antworte in der Sprache des Nutzers."
RATE=defaultdict(lambda:deque(maxlen=30))
def allow(ip):
 n=monotonic();q=RATE[ip]
 while q and n-q[0]>60:q.popleft()
 if len(q)>=20:return False
 q.append(n);return True
def ask(msg,hist):
 if not client:return "OPENAI_API_KEY ist in Render nicht gesetzt."
 try:
  tools=[{"type":"web_search","search_context_size":"medium"}] if WEB else []
  r=client.responses.create(model=MODEL,reasoning={"effort":"high"},tools=tools,tool_choice="auto",store=False,input=[{"role":"system","content":SYSTEM},*hist[-12:],{"role":"user","content":msg}])
  return r.output_text or "Keine Antwort erhalten."
 except Exception:
  app.logger.exception("AI API failure");return "KI-Schnittstelle momentan nicht erreichbar."
HTML="<!doctype html><html lang=\"de\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>ULTRAKI</title><style>:root{--a:#c084fc}*{box-sizing:border-box}body{margin:0;min-height:100vh;background:radial-gradient(circle at 50% 0,#183047,#05070b 48%,#010204);color:#eef7ff;font:15px system-ui;display:grid;place-items:center}.app{width:min(1080px,95vw);height:min(840px,94vh);display:grid;grid-template-rows:auto 1fr auto;background:#071019ed;border:1px solid color-mix(in srgb,var(--a) 55%,transparent);border-radius:30px;overflow:hidden;box-shadow:0 0 100px color-mix(in srgb,var(--a) 18%,transparent)}header{padding:22px;display:flex;gap:15px;align-items:center;border-bottom:1px solid #fff1}.orb{width:52px;height:52px;border-radius:50%;background:radial-gradient(circle,#fff 0 7%,var(--a) 28%,transparent 70%);box-shadow:0 0 38px var(--a)}.name{font-size:25px;font-weight:900;letter-spacing:.06em}.sub{opacity:.6}.status{margin-left:auto;color:var(--a)}#chat{padding:25px;overflow:auto}.m{max-width:82%;padding:14px 17px;border-radius:18px;line-height:1.55;white-space:pre-wrap;margin-bottom:14px}.ai{border:1px solid color-mix(in srgb,var(--a) 25%,transparent);background:color-mix(in srgb,var(--a) 6%,transparent)}.user{margin-left:auto;border:1px solid #fff2}form{display:flex;gap:12px;padding:18px;border-top:1px solid #fff1}input{flex:1;background:#03070a;color:#fff;border:1px solid #fff2;border-radius:15px;padding:15px;outline:0}button{border:0;border-radius:15px;padding:0 23px;background:var(--a);color:#061018;font-weight:900}</style></head><body><main class=\"app\"><header><div class=\"orb\"></div><div><div class=\"name\">ULTRAKI</div><div class=\"sub\">Independent Intelligence · Research · Reasoning</div></div><div class=\"status\">● ONLINE</div></header><section id=\"chat\"><div class=\"m ai\">ULTRAKI ist bereit. Stelle eine komplexe Aufgabe.</div></section><form><input id=\"q\" placeholder=\"Aufgabe eingeben …\" autocomplete=\"off\"><button>START</button></form></main><script>const f=document.querySelector('form'),q=document.querySelector('#q'),c=document.querySelector('#chat');function add(t,k){let e=document.createElement('div');e.className='m '+k;e.textContent=t;c.appendChild(e);c.scrollTop=c.scrollHeight}f.onsubmit=async e=>{e.preventDefault();let x=q.value.trim();if(!x)return;add(x,'user');q.value='';add('Reasoning läuft …','ai');let w=c.lastChild;try{let r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:x})}),d=await r.json();w.remove();add(d.reply||d.error||'Keine Antwort','ai')}catch(_){w.remove();add('Verbindung fehlgeschlagen.','ai')}};</script></body></html>"
@app.get("/")
def home():return send_from_directory("templates","index.html")
@app.get("/engine")
def engine():return send_from_directory(".", "game_engine.html")
@app.get("/game_engine.js")
def engine_js():return send_from_directory(".", "game_engine.js")
@app.get("/health")
@app.get("/api/health")
def health():return jsonify({"status":"ok","project":"ULTRAKI","model":MODEL,"web_search":WEB,"openai_configured":bool(client)})
@app.post("/api/chat")
@app.post("/chat")
def chat():
 if not allow(request.headers.get("X-Forwarded-For",request.remote_addr or "unknown")):return jsonify({"error":"rate limit"}),429
 d=request.get_json(silent=True) or {};m=str(d.get("message") or "").strip()
 if not m:return jsonify({"error":"message is required"}),400
 h=d.get("history") if isinstance(d.get("history"),list) else []
 return jsonify({"reply":ask(m,h),"model":MODEL,"web_search":WEB})
if __name__=="__main__":app.run(host="0.0.0.0",port=int(os.getenv("PORT","10000")))
