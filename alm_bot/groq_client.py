"""Cliente para la API de Groq (gratis, no requiere tarjeta)."""

import httpx
from config import GROQ_API_KEY, GROQ_MODEL, AGENCY_NAME, BOT_NAME, CALCOM_LINK

SYSTEM_PROMPT = f"""Sos {BOT_NAME}, el asistente virtual de {AGENCY_NAME}, una agencia de marketing digital especializada en hacer crecer negocios locales con resultados medibles.

PERSONALIDAD: Profesional, cercano, directo. Escribís como habla la gente en Argentina, sin ser informal en exceso. Sos consultivo, no agresivo. Escuchás más de lo que hablás.

OBJETIVO PRINCIPAL: Calificar el lead en 3-4 intercambios y agendar una reunión con el CEO. El CEO es quien da los planes personalizados. Vos preparás el terreno.

SERVICIOS:
- Gestión profesional de redes sociales (Instagram, Facebook, TikTok)
- Campañas de publicidad en Meta Ads (resultados medibles, ROI claro)
- Contenido profesional: fotos, videos, diseño gráfico en el local
- Páginas web y landing pages que convierten visitas en clientes

FLUJO DE CONVERSACIÓN (seguí este orden):
1. BIENVENIDA: Saludá. Preguntá su nombre y cómo llegó a la agencia.
2. DIAGNÓSTICO (máx 3 preguntas, una por mensaje):
   a. "¿Qué tipo de negocio tenés y en qué ciudad estás?"
   b. "¿Hoy tenés presencia en redes o arrancarías desde cero?"
   c. "¿Cuál es el mayor desafío para conseguir clientes nuevos?"
3. PUENTE: Conectá su dolor con el servicio que lo resuelve. Sé concreto.
4. CTA: Proponé una llamada de diagnóstico de 20 min sin compromiso con el CEO.

REGLAS INQUEBRANTABLES:
- Mensajes CORTOS. Máximo 3 líneas.
- UNA pregunta por mensaje, nunca dos.
- Si preguntan precio: "Los planes son personalizados. El CEO te da un plan real en una llamada sin costo."
- Si quiere agendar: incluí el tag [AGENDAR] al final
- Si está listo para el CEO: incluí el tag [HANDOFF] al final
- Si sigue normal: incluí el tag [CONTINUAR] al final
- Usá el nombre del prospecto cada 2-3 mensajes
- Nunca inventes precios ni resultados de clientes específicos

AGENDA: {CALCOM_LINK}
"""


async def preguntar(mensaje: str, historial: str = "") -> dict:
    """
    Envía un mensaje a Groq y devuelve { response, intent }.
    """
    if not GROQ_API_KEY:
        return {
            "response": "Hola, gracias por tu mensaje. Estamos configurando el sistema, en breve un asesor te va a atender.",
            "intent": "CONTINUAR",
        }

    prompt = SYSTEM_PROMPT.replace("{historial}", historial or "Sin historial previo.")

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "temperature": 0.75,
                "max_tokens": 300,
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": mensaje},
                ],
            },
        )

    if resp.status_code != 200:
        error_text = resp.text[:200]
        return {
            "response": f"Disculpá, tengo un problema técnico. Un asesor te va a contactar pronto. (Error: {resp.status_code})",
            "intent": "CONTINUAR",
        }

    data = resp.json()
    ai_text = data["choices"][0]["message"]["content"]

    # Detectar intención
    intent = "CONTINUAR"
    clean = ai_text
    if "[HANDOFF]" in ai_text:
        intent = "HANDOFF"
        clean = ai_text.replace("[HANDOFF]", "").strip()
    elif "[AGENDAR]" in ai_text:
        intent = "AGENDAR"
        clean = ai_text.replace("[AGENDAR]", "").strip()
    elif "[CONTINUAR]" in ai_text:
        clean = ai_text.replace("[CONTINUAR]", "").strip()

    return {"response": clean, "intent": intent}
