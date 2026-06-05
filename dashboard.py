import asyncio
import threading
import os
from flask import Flask, jsonify, request, Response
from functools import wraps

import vars

app = Flask(__name__)

DASHBOARD_LOGIN = os.getenv('DASHBOARD_LOGIN', 'admin')
DASHBOARD_PASSWORD = os.getenv('DASHBOARD_PASSWORD', 'changeme')


def _run_async(coro):
    return asyncio.run_coroutine_threadsafe(coro, vars.main_loop).result(timeout=10)


def _auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != DASHBOARD_LOGIN or auth.password != DASHBOARD_PASSWORD:
            return Response('Unauthorized', 401, {'WWW-Authenticate': 'Basic realm="Dashboard"'})
        return f(*args, **kwargs)
    return decorated


@app.route('/api/stats')
@_auth_required
def api_stats():
    stats = _run_async(vars.database.get_dashboard_stats())
    return jsonify(stats)


@app.route('/')
@_auth_required
def index():
    stats = _run_async(vars.database.get_dashboard_stats())
    users = _run_async(vars.database.get_recent_users(20))
    rows = ''
    for u in users:
        rows += (
            f'<tr><td>{u["user_id"]}</td><td>{u["role"]}</td>'
            f'<td>{u["name"] or "—"}</td><td>{u["subject"] or "—"}</td>'
            f'<td>{(u["created_at"] or "")[:16]}</td></tr>'
        )
    html = f'''<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8"><title>Tutor Bot Dashboard</title>
<meta http-equiv="refresh" content="60">
<style>
  body{{font-family:system-ui,sans-serif;margin:0;background:#f5f5f5;color:#333}}
  h1{{background:#2b5fec;color:#fff;margin:0;padding:16px 24px;font-size:20px}}
  .cards{{display:flex;flex-wrap:wrap;gap:16px;padding:24px}}
  .card{{background:#fff;border-radius:8px;padding:20px 28px;min-width:160px;box-shadow:0 1px 4px rgba(0,0,0,.1)}}
  .card .val{{font-size:36px;font-weight:700;color:#2b5fec}}
  .card .lbl{{font-size:13px;color:#888;margin-top:4px}}
  table{{width:calc(100% - 48px);margin:0 24px 24px;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.1)}}
  th{{background:#2b5fec;color:#fff;padding:10px 14px;text-align:left;font-size:13px}}
  td{{padding:9px 14px;font-size:13px;border-bottom:1px solid #f0f0f0}}
  tr:last-child td{{border-bottom:none}}
</style></head><body>
<h1>🤖 Tutor Bot Dashboard</h1>
<div class="cards">
  <div class="card"><div class="val">{stats["tutors"]}</div><div class="lbl">🧑‍🏫 Репетиторов</div></div>
  <div class="card"><div class="val">{stats["tutees"]}</div><div class="lbl">👨‍🎓 Учеников</div></div>
  <div class="card"><div class="val">{stats["pending"]}</div><div class="lbl">⏳ На модерации</div></div>
  <div class="card"><div class="val">{stats["published_7d"]}</div><div class="lbl">✅ Опубликовано за 7 дней</div></div>
  <div class="card"><div class="val">{stats["avg_rating"] or "—"}</div><div class="lbl">⭐️ Средний рейтинг</div></div>
  <div class="card"><div class="val">{stats["scheduled"]}</div><div class="lbl">📅 Запланировано</div></div>
</div>
<table>
  <tr><th>ID</th><th>Роль</th><th>Имя</th><th>Предмет</th><th>Дата</th></tr>
  {rows}
</table>
</body></html>'''
    return html


def start_dashboard():
    port = int(os.getenv('DASHBOARD_PORT', 8080))
    thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False), daemon=True)
    thread.start()
