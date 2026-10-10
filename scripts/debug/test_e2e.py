"""手工 E2E 验证脚本 — 不参与 pytest 收集。

运行前提：后端已启动在 http://localhost:8000，且 admin/admin123 可登录。
执行：python scripts/debug/test_e2e.py
"""
import httpx
import sys

BASE = "http://localhost:8000"

def check(name, condition, detail=""):
    status = "✓" if condition else "✗"
    print(f"{status} {name}", end="")
    if detail:
        print(f"  ({detail})", end="")
    if not condition:
        print("")
        sys.exit(1)
    print()

print("=== PKB Backend E2E Test v2 ===\n")

# 1. health
r = httpx.get(f"{BASE}/api/health", timeout=10)
check("health ok", r.status_code == 200)

# 2. login
r = httpx.post(f"{BASE}/api/auth/login", json={"username": "admin", "password": "admin123"}, timeout=10)
check("login 200", r.status_code == 200, str(r.json())[:50])
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

# 3. upload fresh txt
content = "PKB fresh final e2e test.\n中文搜索关键词 知识库 v4 final.\nLast line.\n"
files = {"files": ("pkb-e2e.txt", content.encode("utf-8"), "text/plain")}
data = {"tag_names": "e2e-test"}
r = httpx.post(f"{BASE}/api/files/upload", headers=h, files=files, data=data, timeout=10)
check("upload 200", r.status_code == 200, str(r.json())[:80])
upload_result = r.json()
item = upload_result["items"][0]
check("upload status = created", item["status"] == "created", f"status={item['status']}")
doc = item["file"]
pid = doc["public_id"]
check("public_id 26 chars", len(pid) == 26)
check("size_bytes > 0", doc["size_bytes"] > 0, f"size={doc['size_bytes']}")

# 4. list
r = httpx.get(f"{BASE}/api/files", headers=h, timeout=10)
check("list total >= 1", r.json()["total"] >= 1)

# 5. preview
r = httpx.get(f"{BASE}/api/files/{pid}/preview", headers=h, timeout=10)
check("preview 200", r.status_code == 200, f"status={r.status_code}")
content_json = r.json()
check("preview content has keyword", "知识库" in content_json.get("content", ""))

# 6. download
r = httpx.get(f"{BASE}/api/files/{pid}/download", headers=h, timeout=10)
check("download 200", r.status_code == 200, f"status={r.status_code}")
downloaded = r.content.decode("utf-8", errors="replace")
check("download content match", content in downloaded, f"got: {downloaded[:60]}")
check("download filename", r.headers.get("content-disposition", "") != "")

# 7. duplicate
files2 = {"files": ("dup.txt", content.encode("utf-8"), "text/plain")}
r2 = httpx.post(f"{BASE}/api/files/upload", headers=h, files=files2, data=data, timeout=10)
check("duplicate status", r2.json()["items"][0]["status"] == "duplicate")

# 8. tags list
r = httpx.get(f"{BASE}/api/tags", headers=h, timeout=10)
tag_names = [t["name"] for t in r.json()]
check("tag e2e-test exists", "e2e-test" in tag_names, str(tag_names))

# 9. file detail (preview_url + download_url)
r = httpx.get(f"{BASE}/api/files/{pid}", headers=h, timeout=10)
check("detail preview_url", r.json()["preview_url"] == f"/api/files/{pid}/preview")
check("detail download_url", r.json()["download_url"] == f"/api/files/{pid}/download")

# 10. soft delete
r = httpx.delete(f"{BASE}/api/files/{pid}", headers=h, timeout=10)
check("soft delete", r.json()["deleted_at"] is not None)

# 11. trashed filter
r = httpx.get(f"{BASE}/api/files", headers=h, params={"status": "trashed"}, timeout=10)
check("trashed total >= 1", r.json()["total"] >= 1)

# 12. active filter excludes deleted
r = httpx.get(f"{BASE}/api/files", headers=h, params={"status": "active"}, timeout=10)
check("active excludes deleted", all(it["deleted_at"] is None for it in r.json()["items"]))

# 13. restore
r = httpx.post(f"{BASE}/api/files/{pid}/restore", headers=h, timeout=10)
check("restore clears deleted_at", r.json()["deleted_at"] is None)

# 14. search (LIKE 兜底)
r = httpx.get(f"{BASE}/api/files", headers=h, params={"q": "知识库"}, timeout=10)
check("search returns results", r.json()["total"] >= 1, f"total={r.json()['total']}")

# 15. update title
r = httpx.patch(f"{BASE}/api/files/{pid}", headers=h, json={"title": "renamed title"}, timeout=10)
check("title updated", r.json()["title"] == "renamed title")

# 16. update tags
r = httpx.get(f"{BASE}/api/tags", headers=h, timeout=10)
all_tags = r.json()
new_tag = next((t for t in all_tags if t["name"] == "work-notes"), None)
if new_tag is None:
    new_tag = httpx.post(f"{BASE}/api/tags", headers=h, json={"name": "work-notes", "color": "#ff4949"}, timeout=10).json()
r = httpx.put(f"{BASE}/api/files/{pid}/tags", headers=h, json={"tag_ids": [new_tag["id"]]}, timeout=10)
check("tags updated", len(r.json()["tags"]) == 1 and r.json()["tags"][0]["name"] == "work-notes")

# 17. background extract_status (wait)
import time
time.sleep(4)
r = httpx.get(f"{BASE}/api/files/{pid}", headers=h, timeout=10)
check("extract_status in [done/pending]", r.json()["extract_status"] in ("done", "pending", "skipped"), f"status={r.json()['extract_status']}")
print(f"  extract_status={r.json()['extract_status']}")

# 18. filter by tag_id
r = httpx.get(f"{BASE}/api/files", headers=h, params={"tag_id": new_tag["id"]}, timeout=10)
check("tag filter works", r.json()["total"] >= 1)

# 19. bad login
r = httpx.post(f"{BASE}/api/auth/login", json={"username": "admin", "password": "wrong"}, timeout=10)
check("wrong password → 401", r.status_code == 401)

# 20. no token → 401
r = httpx.get(f"{BASE}/api/files", timeout=10)
check("no token → 401", r.status_code == 401)

print("\n🎉 ALL 20 E2E TESTS PASSED 🎉")
