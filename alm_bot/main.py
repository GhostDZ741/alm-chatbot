"""
ALM Chatbot — Servidor FastAPI
───────────────────────────────
Recibe webhooks de Meta (WhatsApp, Instagram, Facebook),
procesa con Groq AI y responde automáticamente.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse

from config import META_VERIFY_TOKEN, WEBHOOK_PATH, BOT_NAME, AGENCY_NAME, PORT
from bot_engine import procesar_mensaje
from sheets_crm import inicializar_hojas

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("alm_bot")


# ── Lifecycle ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info(f"🦁 {BOT_NAME} — {AGENCY_NAME} Bot iniciando...")
    await inicializar_hojas()
    yield
    log.info("Bot detenido.")


app = FastAPI(title=f"{AGENCY_NAME} Chatbot", version="1.0.0", lifespan=lifespan)


# ── Endpoints ─────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "bot": BOT_NAME, "agency": AGENCY_NAME}


@app.get("/")
async def root():
    return {
        "name": f"{BOT_NAME} - {AGENCY_NAME}",
        "version": "1.0.0",
        "status": "running",
        "webhook": WEBHOOK_PATH,
    }


# ── Webhook: Verificación de Meta ─────────────────────────

@app.get(WEBHOOK_PATH)
async def webhook_verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    """
    Meta envía GET para verificar el webhook.
    Debe responder con hub.challenge si el token coincide.
    """
    if hub_mode == "subscribe" and hub_verify_token == META_VERIFY_TOKEN:
        log.info("✅ Webhook verificado por Meta")
        return PlainTextResponse(hub_challenge)
    log.warning("⚠️  Intento de verificación fallido")
    raise HTTPException(status_code=403, detail="Verification failed")


# ── Webhook: Mensajes entrantes ───────────────────────────

@app.post(WEBHOOK_PATH)
async def webhook_message(request: Request):
    """
    Recibe mensajes de WhatsApp / Instagram / Facebook.
    """
    body = await request.json()
    log.info(f"📩 Webhook recibido: {str(body)[:300]}...")

    mensajes_parseados = _parsear_mensajes(body)

    if not mensajes_parseados:
        return {"status": "ok"}  # Meta espera 200 aunque no haya mensajes

    resultados = []
    for msg in mensajes_parseados:
        try:
            resultado = await procesar_mensaje(
                channel=msg["channel"],
                sender_id=msg["sender_id"],
                sender_name=msg.get("sender_name", "Cliente"),
                message_text=msg.get("text", ""),
            )
            resultados.append(resultado)
            log.info(f"✅ {msg['channel']}/{msg['sender_id']}: {resultado['intent']}")
        except Exception as e:
            log.error(f"❌ Error procesando mensaje: {e}", exc_info=True)
            resultados.append({"status": "error", "error": str(e)})

    return {"status": "ok", "results": resultados}


# ── Parseo de mensajes Meta ───────────────────────────────

def _parsear_mensajes(body: dict) -> list[dict]:
    """Extrae los mensajes del payload de Meta."""
    resultados = []

    try:
        # WhatsApp
        if body.get("object") == "whatsapp_business_account":
            for entry in body.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    for msg in value.get("messages", []):
                        contact = (value.get("contacts") or [{}])[0]
                        resultados.append({
                            "channel": "whatsapp",
                            "sender_id": msg.get("from", ""),
                            "sender_name": contact.get("profile", {}).get("name", "Cliente"),
                            "text": msg.get("text", {}).get("body", ""),
                        })

        # Instagram
        elif body.get("object") == "instagram":
            for entry in body.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    if "messages" in value:
                        for msg in value["messages"]:
                            resultados.append({
                                "channel": "instagram",
                                "sender_id": msg.get("from", {}).get("id", ""),
                                "sender_name": msg.get("from", {}).get("username", "Cliente"),
                                "text": msg.get("text", ""),
                            })

        # Facebook Messenger
        if body.get("object") == "page":
            for entry in body.get("entry", []):
                if "messaging" in entry:
                    for msg in entry["messaging"]:
                        resultados.append({
                            "channel": "messenger",
                            "sender_id": msg.get("sender", {}).get("id", ""),
                            "sender_name": "Cliente",
                            "text": msg.get("message", {}).get("text", ""),
                        })
    except Exception as e:
        log.warning(f"⚠️  Error parseando mensaje Meta: {e}")

    return resultados


# ── Entry point ───────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
