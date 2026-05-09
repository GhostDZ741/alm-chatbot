"""SQLite CRM – memoria persistente del bot sin depender de Google Sheets."""

import sqlite3
from datetime import datetime
from pathlib import Path
from config import DATABASE_PATH, BOT_NAME


def _conn():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(DATABASE_PATH))
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    _migrate(db)
    return db


def _migrate(db: sqlite3.Connection):
    db.executescript("""
        CREATE TABLE IF NOT EXISTS conversaciones (
            sender_id   TEXT NOT NULL,
            channel     TEXT NOT NULL DEFAULT 'whatsapp',
            sender_name TEXT DEFAULT 'Cliente',
            message     TEXT NOT NULL,
            response    TEXT NOT NULL,
            intent      TEXT DEFAULT 'CONTINUAR',
            business    TEXT DEFAULT '',
            city        TEXT DEFAULT '',
            pain_point  TEXT DEFAULT '',
            status      TEXT DEFAULT 'ACTIVO',
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS leads (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id   TEXT NOT NULL UNIQUE,
            channel     TEXT DEFAULT 'whatsapp',
            sender_name TEXT DEFAULT 'Cliente',
            business    TEXT DEFAULT '',
            city        TEXT DEFAULT '',
            pain_point  TEXT DEFAULT '',
            status      TEXT DEFAULT 'NUEVO',
            notas       TEXT DEFAULT '',
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_conv_sender ON conversaciones(sender_id);
        CREATE INDEX IF NOT EXISTS idx_leads_sender ON leads(sender_id);
    """)
    db.commit()


# ── Conversaciones ────────────────────────────────────────

def guardar_mensaje(sender_id: str, channel: str, sender_name: str,
                    message: str, response: str, intent: str):
    with _conn() as db:
        db.execute(
            """INSERT INTO conversaciones
               (sender_id, channel, sender_name, message, response, intent)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (sender_id, channel, sender_name, message, response, intent),
        )
        db.commit()


def obtener_historial(sender_id: str, limite: int = 10) -> list[dict]:
    with _conn() as db:
        rows = db.execute(
            """SELECT message, response, intent, created_at
               FROM conversaciones
               WHERE sender_id = ?
               ORDER BY created_at DESC LIMIT ?""",
            (sender_id, limite),
        ).fetchall()
    return [dict(r) for r in reversed(rows)]


def formatear_historial(sender_id: str) -> str:
    historial = obtener_historial(sender_id)
    if not historial:
        return "Sin historial previo."
    partes = []
    for h in historial:
        partes.append(f"[CLIENTE]: {h['message']}")
        partes.append(f"[{BOT_NAME}]: {h['response']}")
    return "\n".join(partes)


# ── Leads ─────────────────────────────────────────────────

def upsert_lead(sender_id: str, channel: str, sender_name: str,
                business: str = "", city: str = "",
                pain_point: str = "", status: str = "NUEVO"):
    with _conn() as db:
        existing = db.execute(
            "SELECT id FROM leads WHERE sender_id = ?", (sender_id,)
        ).fetchone()
        if existing:
            db.execute(
                """UPDATE leads SET sender_name=?, channel=?, business=?,
                   city=?, pain_point=?, status=?, updated_at=datetime('now')
                   WHERE sender_id=?""",
                (sender_name, channel, business, city, pain_point, status, sender_id),
            )
        else:
            db.execute(
                """INSERT INTO leads
                   (sender_id, channel, sender_name, business, city, pain_point, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (sender_id, channel, sender_name, business, city, pain_point, status),
            )
        db.commit()


def actualizar_lead(sender_id: str, **kwargs):
    campos = {k: v for k, v in kwargs.items() if v}
    if not campos:
        return
    set_clause = ", ".join(f"{k}=?" for k in campos)
    with _conn() as db:
        db.execute(
            f"UPDATE leads SET {set_clause} WHERE sender_id=?",
            (*campos.values(), sender_id),
        )
        db.commit()


def obtener_leads(limit: int = 50) -> list[dict]:
    with _conn() as db:
        rows = db.execute(
            """SELECT * FROM leads ORDER BY updated_at DESC LIMIT ?""", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]
