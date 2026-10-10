"""手工调试脚本 — 不参与 pytest 收集。

运行前提：后端已启动在 http://localhost:8000，且 admin/admin123 可登录。
执行：python scripts/debug/quick_download.py
"""
import httpx

BASE = "http://localhost:8000"
h = {"Authorization": "Bearer " + httpx.post(f"{BASE}/api/auth/login", json={"username":"admin","password":"admin123"}).json()["access_token"]}
r = httpx.get(f"{BASE}/api/files", headers=h, params={"status":"active"}, timeout=10)
items = r.json()["items"]
print("active files:", len(items))
if items:
    pid = items[0]["public_id"]
    stored = items[0].get("stored_path","(not in response)")
    print("stored_path:", stored)
    print("delete_at:", items[0].get("deleted_at"))
    r = httpx.get(f"{BASE}/api/files/{pid}/download", headers=h, timeout=10)
    cd = r.headers.get("content-disposition", "")[:60]
    print(f"download {pid}: status={r.status_code}, bytes={len(r.content)}, cd={cd}")
    if r.status_code >= 400:
        print("body:", r.text[:300])
