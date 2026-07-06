"""Reference client-side sync engine for the field-officer mobile app.

This runs ON THE DEVICE (not the server). It maintains a local SQLite mirror,
pulls deltas, queues offline-created claims, and pushes them when connectivity
returns. Included here so the server and client halves of the protocol live
together and can be integration-tested.

Usage:
    engine = SyncEngine("/data/fra_local.db", api_base, token)
    engine.init_schema()
    engine.pull("village"); engine.pull("fra_claim")
    engine.queue_claim({...})           # offline
    engine.push()                       # when online
"""
import hashlib
import json
import sqlite3
import urllib.request

SCHEMA = """
CREATE TABLE IF NOT EXISTS sync_state (
    entity TEXT PRIMARY KEY,
    last_server_time TEXT
);
CREATE TABLE IF NOT EXISTS mirror (
    entity TEXT, server_id TEXT, payload TEXT, updated_at TEXT,
    PRIMARY KEY (entity, server_id)
);
CREATE TABLE IF NOT EXISTS pending_claims (
    client_ref TEXT PRIMARY KEY, payload TEXT,
    sync_status TEXT DEFAULT 'PENDING', server_id TEXT, conflict_reason TEXT
);
"""


def _checksum(records) -> str:
    blob = json.dumps(records, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()


class SyncEngine:
    def __init__(self, db_path, api_base, token, http=None):
        self.db = sqlite3.connect(db_path)
        self.db.row_factory = sqlite3.Row
        self.api_base = api_base.rstrip("/")
        self.token = token
        self._http = http or self._urllib_call  # injectable for tests

    # -- transport ----------------------------------------------------------
    def _urllib_call(self, method, path, body=None):  # pragma: no cover - network
        url = f"{self.api_base}{path}"
        if not url.startswith(("http://", "https://")):
            raise ValueError("Only http(s) URLs are permitted")
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", f"Bearer {self.token}")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept-Encoding", "gzip")
        with urllib.request.urlopen(req) as resp:  # nosec B310 - scheme validated above
            return json.loads(resp.read().decode())

    # -- schema -------------------------------------------------------------
    def init_schema(self):
        self.db.executescript(SCHEMA)
        self.db.commit()

    def _watermark(self, entity):
        row = self.db.execute("SELECT last_server_time FROM sync_state WHERE entity=?",
                              (entity,)).fetchone()
        return row["last_server_time"] if row else None

    # -- pull (server -> device) -------------------------------------------
    def pull(self, entity):
        since = self._watermark(entity)
        total = 0
        cursor = None
        server_time = since
        from urllib.parse import quote
        while True:
            qs = f"/api/v1/sync/pull/?entity={entity}"
            if since:
                qs += f"&since={quote(since)}"
            if cursor:
                qs += f"&cursor={quote(cursor)}"
            resp = self._http("GET", qs)
            if resp["checksum"] != _checksum(resp["records"]):
                raise ValueError("Checksum mismatch on pulled batch (corruption).")
            for rec in resp["records"]:
                self.db.execute(
                    "INSERT OR REPLACE INTO mirror(entity, server_id, payload, updated_at)"
                    " VALUES (?,?,?,?)",
                    (entity, rec["id"], json.dumps(rec), rec["updated_at"]))
                total += 1
            server_time = resp["server_time"]
            if resp["has_more"]:
                cursor = resp["next_cursor"]
            else:
                break
        self.db.execute(
            "INSERT OR REPLACE INTO sync_state(entity, last_server_time) VALUES (?,?)",
            (entity, server_time))
        self.db.commit()
        return total

    # -- offline create + push (device -> server) --------------------------
    def queue_claim(self, client_ref, payload):
        self.db.execute(
            "INSERT OR REPLACE INTO pending_claims(client_ref, payload, sync_status)"
            " VALUES (?,?, 'PENDING')", (client_ref, json.dumps(payload)))
        self.db.commit()

    def push(self, device_id="device-1"):
        rows = self.db.execute(
            "SELECT client_ref, payload FROM pending_claims WHERE sync_status='PENDING'"
        ).fetchall()
        if not rows:
            return {"accepted_count": 0, "conflict_count": 0}
        claims = []
        for r in rows:
            item = json.loads(r["payload"])
            item["client_ref"] = r["client_ref"]
            claims.append(item)
        resp = self._http("POST", "/api/v1/sync/push/",
                          {"device_id": device_id, "claims": claims})
        for a in resp["accepted"]:
            self.db.execute(
                "UPDATE pending_claims SET sync_status='SYNCED', server_id=? WHERE client_ref=?",
                (a["server_id"], a["client_ref"]))
        for c in resp["conflicts"]:
            self.db.execute(
                "UPDATE pending_claims SET sync_status='CONFLICT', conflict_reason=? WHERE client_ref=?",
                (c["reason"], c["client_ref"]))
        self.db.commit()
        return resp
