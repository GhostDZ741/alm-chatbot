# PROYECTO: ALM CHATBOT — INSTRUCCIONES COMPLETAS PARA CLAUDE CODE

## PERMISOS Y AUTORIZACIÓN

Tenés permiso total y explícito para:
- Ejecutar cualquier comando bash en esta computadora
- Instalar software y dependencias del sistema
- Crear, editar y eliminar archivos y directorios
- Conectarte a servicios externos vía HTTP
- Leer variables de entorno y crear archivos .env
- Interactuar con la API de n8n localmente
- Preguntar por credenciales cuando las necesites

No pidas confirmación en cada paso. Ejecutá, verificá el resultado, y avanzá. Si algo falla, diagnosticá y corregí automáticamente. Informame el progreso con mensajes claros.

---

## OBJETIVO

Construir un sistema de chatbot comercial completo para Arab Lion Marketing (ALM) que funcione en WhatsApp, Instagram y Facebook simultáneamente. El bot es un vendedor consultivo inteligente que califica leads, agenda reuniones y hace handoff al CEO cuando el prospecto está listo para cerrar.

Stack: n8n (ya instalado) + Cloudflare Tunnel + Groq API + Google Sheets + Meta APIs (WA/IG/FB).

---

## PASO 1: VERIFICACIÓN DEL SISTEMA

Ejecutá estos comandos y reportame los resultados:

```bash
# Verificar n8n
curl -s http://localhost:5678/healthz 2>/dev/null || \
curl -s http://localhost:5679/healthz 2>/dev/null || \
echo "n8n no responde en puertos estándar"

# Buscar en qué puerto corre n8n
ss -tlnp | grep -E "5678|5679|5680" 2>/dev/null || \
netstat -tlnp 2>/dev/null | grep node || \
lsof -i -P -n 2>/dev/null | grep LISTEN | grep node

# Verificar Node.js
node --version 2>/dev/null || echo "Node no instalado"

# Verificar Python
python3 --version 2>/dev/null || echo "Python3 no instalado"

# Verificar curl y jq
curl --version | head -1
jq --version 2>/dev/null || echo "jq no instalado — lo vamos a instalar"

# Sistema operativo
uname -a
lsb_release -a 2>/dev/null || cat /etc/os-release 2>/dev/null
```

Una vez que tengas el puerto donde corre n8n, guardalo como variable N8N_PORT para usarla en todo el setup.

---

## PASO 2: INSTALAR DEPENDENCIAS DEL SISTEMA

```bash
# Actualizar apt e instalar jq (procesador JSON)
sudo apt-get update -qq && sudo apt-get install -y jq curl wget

# Instalar cloudflared (Cloudflare Tunnel)
# Detectar arquitectura primero
ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ]; then
  CF_ARCH="amd64"
elif [ "$ARCH" = "aarch64" ]; then
  CF_ARCH="arm64"
else
  CF_ARCH="amd64"
fi

# Descargar cloudflared si no está instalado
if ! command -v cloudflared &> /dev/null; then
  wget -q "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${CF_ARCH}.deb" -O /tmp/cloudflared.deb
  sudo dpkg -i /tmp/cloudflared.deb
  cloudflared --version
else
  echo "cloudflared ya instalado: $(cloudflared --version)"
fi
```

---

## PASO 3: CREAR ESTRUCTURA DEL PROYECTO

```bash
# Crear directorio principal del proyecto
mkdir -p ~/alm-bot/{config,scripts,logs,workflows}
cd ~/alm-bot

# Crear archivo de log principal
touch logs/setup.log
echo "=== ALM BOT SETUP - $(date) ===" >> logs/setup.log
```

---

## PASO 4: RECOLECTAR CREDENCIALES (INTERACTIVO)

Preguntame estas credenciales una por una. Para cada una, decime exactamente dónde conseguirla si no la tengo a mano:

### 4.1 Puerto de n8n
- Ya lo detectaste en el Paso 1. Confirmame cuál es.

### 4.2 API Key de n8n
- **Dónde conseguirla:** Abrir n8n en el navegador → Settings (ícono tuerca abajo izquierda) → API → Create API Key → copiar el token
- **Formato esperado:** `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (token largo)

### 4.3 API Key de Groq (GRATIS)
- **Dónde conseguirla:** https://console.groq.com → Sign up gratis → API Keys → Create API Key
- **Formato esperado:** `gsk_...`

### 4.4 Credenciales de Meta (WhatsApp primero)
Para obtenerlas: https://developers.facebook.com → My Apps → Create App → Business
- **WHATSAPP_PHONE_NUMBER_ID:** En el dashboard de tu app Meta, sección WhatsApp → Getting Started
- **WHATSAPP_ACCESS_TOKEN:** Token temporal (para testing) o token permanente de sistema
- **META_VERIFY_TOKEN:** Inventalo vos, cualquier string seguro ej: `alm_webhook_2024_secure`
- **WHATSAPP_BUSINESS_ACCOUNT_ID:** En Meta Business Suite → Configuración → Info de la cuenta

### 4.5 Credenciales de Instagram y Facebook Messenger
(Del mismo app de Meta que usaste para WhatsApp)
- **INSTAGRAM_PAGE_ACCESS_TOKEN:** Meta App → Messenger → Configuración → Tokens de acceso a página
- **FACEBOOK_PAGE_ID:** ID de tu página de Facebook

### 4.6 Google Sheets (para memoria del bot)
- **Dónde conseguirlo:** https://console.cloud.google.com → Nuevo proyecto → Habilitar "Google Sheets API" + "Google Drive API" → Crear credencial → Cuenta de servicio → Descargar JSON
- **GOOGLE_SHEETS_ID:** Crear una hoja en Google Sheets → copiar el ID de la URL (entre /d/ y /edit)
- **GOOGLE_SERVICE_ACCOUNT_EMAIL:** Está en el JSON descargado (campo "client_email")
- **GOOGLE_PRIVATE_KEY:** Está en el JSON descargado (campo "private_key")
- **IMPORTANTE:** Compartir la hoja de Google Sheets con el email de la cuenta de servicio

### 4.7 Datos del CEO (para handoff)
- **CEO_WHATSAPP_NUMBER:** Tu número de WhatsApp con código de país, sin + ni espacios. Ej: `5491112345678`
- **CALCOM_LINK:** Tu link de Cal.com para agendar. Ej: `https://cal.com/tu-usuario/reunion-alm`
- **AGENCY_NAME:** `Arab Lion Marketing`
- **BOT_NAME:** `Leo`

Una vez que tengas TODAS las credenciales, creá el archivo `.env`:

```bash
cat > ~/alm-bot/config/.env << 'ENVFILE'
# === n8n ===
N8N_PORT=5678
N8N_API_KEY=REEMPLAZAR

# === Groq ===
GROQ_API_KEY=REEMPLAZAR

# === Meta - WhatsApp ===
WHATSAPP_PHONE_NUMBER_ID=REEMPLAZAR
WHATSAPP_ACCESS_TOKEN=REEMPLAZAR
WHATSAPP_BUSINESS_ACCOUNT_ID=REEMPLAZAR
META_VERIFY_TOKEN=alm_webhook_2024_secure

# === Meta - Instagram ===
INSTAGRAM_PAGE_ACCESS_TOKEN=REEMPLAZAR
FACEBOOK_PAGE_ID=REEMPLAZAR

# === Google Sheets ===
GOOGLE_SHEETS_ID=REEMPLAZAR
GOOGLE_SERVICE_ACCOUNT_EMAIL=REEMPLAZAR
GOOGLE_PRIVATE_KEY=REEMPLAZAR

# === CEO / Agencia ===
CEO_WHATSAPP_NUMBER=REEMPLAZAR
CALCOM_LINK=REEMPLAZAR
AGENCY_NAME=Arab Lion Marketing
BOT_NAME=Leo
ENVFILE

echo "Archivo .env creado. RECORDÁ: nunca subas este archivo a GitHub ni lo compartas."
```

Reemplazá cada `REEMPLAZAR` con el valor real que te dí.

---

## PASO 5: CONFIGURAR CLOUDFLARE TUNNEL

```bash
# Crear tunnel sin autenticación (modo rápido, genera URL aleatoria)
# Esto es para testing. Para producción usaremos tunnel con cuenta CF.

# Opción A: Tunnel temporal (sin cuenta, URL cambia cada reinicio)
# Útil para configurar Meta webhooks en testing
cloudflared tunnel --url http://localhost:${N8N_PORT} --no-autoupdate &
CF_PID=$!
sleep 5

# Capturar la URL pública generada
TUNNEL_URL=$(journalctl --no-pager -u cloudflared 2>/dev/null | grep -oP 'https://[a-z0-9-]+\.trycloudflare\.com' | tail -1)
# Si no funciona con journalctl, buscar en los logs
if [ -z "$TUNNEL_URL" ]; then
  echo "Buscando URL del tunnel..."
  TUNNEL_URL=$(cloudflared tunnel --url http://localhost:${N8N_PORT} 2>&1 | grep -oP 'https://[a-z0-9-]+\.trycloudflare\.com' | head -1 &)
fi

echo "URL pública del tunnel: $TUNNEL_URL"
echo "Webhook URL para Meta: ${TUNNEL_URL}/webhook/meta-bot"

# Guardar en config
echo "TUNNEL_URL=${TUNNEL_URL}" >> ~/alm-bot/config/.env
echo "WEBHOOK_URL=${TUNNEL_URL}/webhook/meta-bot" >> ~/alm-bot/config/.env
```

**NOTA IMPORTANTE:** Guardá la URL del tunnel. La necesitás para configurar los webhooks en Meta Developers.

Para **producción** (URL fija permanente), necesitás una cuenta gratis en Cloudflare y un dominio. Puedo configurar eso después si lo necesitás.

---

## PASO 6: CREAR EL WORKFLOW EN n8n VÍA API

Primero verificá que la API de n8n funciona:

```bash
source ~/alm-bot/config/.env

curl -s -H "X-N8N-API-KEY: ${N8N_API_KEY}" \
  "http://localhost:${N8N_PORT}/api/v1/workflows" | jq '.data | length' 2>/dev/null \
  && echo "API n8n OK" || echo "ERROR: Verificar API key de n8n"
```

Ahora creá el script Python que genera e importa el workflow completo:

```bash
cat > ~/alm-bot/scripts/create_workflow.py << 'PYEOF'
#!/usr/bin/env python3
"""
Crea el workflow completo de ALM Bot en n8n via API REST.
"""

import json
import os
import sys
import urllib.request
import urllib.error

# Cargar config
env_path = os.path.expanduser("~/alm-bot/config/.env")
config = {}
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            config[k.strip()] = v.strip()

N8N_HOST = f"http://localhost:{config.get('N8N_PORT', '5678')}"
N8N_API_KEY = config.get("N8N_API_KEY", "")
GROQ_KEY = config.get("GROQ_API_KEY", "")
WA_PHONE_ID = config.get("WHATSAPP_PHONE_NUMBER_ID", "")
WA_TOKEN = config.get("WHATSAPP_ACCESS_TOKEN", "")
IG_TOKEN = config.get("INSTAGRAM_PAGE_ACCESS_TOKEN", "")
FB_PAGE_ID = config.get("FACEBOOK_PAGE_ID", "")
VERIFY_TOKEN = config.get("META_VERIFY_TOKEN", "alm_webhook_2024_secure")
SHEETS_ID = config.get("GOOGLE_SHEETS_ID", "")
SHEETS_SA_EMAIL = config.get("GOOGLE_SERVICE_ACCOUNT_EMAIL", "")
SHEETS_KEY = config.get("GOOGLE_PRIVATE_KEY", "")
CEO_WA = config.get("CEO_WHATSAPP_NUMBER", "")
CALCOM = config.get("CALCOM_LINK", "")
BOT_NAME = config.get("BOT_NAME", "Leo")
AGENCY = config.get("AGENCY_NAME", "Arab Lion Marketing")

SYSTEM_PROMPT = f"""Sos {BOT_NAME}, el asistente virtual de {AGENCY}, una agencia de marketing digital especializada en hacer crecer negocios locales con resultados medibles.

PERSONALIDAD: Profesional, cercano, directo. Escribís como habla la gente en Argentina, sin ser informal en exceso. Sos consultivo, no agresivo. Escuchás más de lo que hablás.

OBJETIVO PRINCIPAL: Calificar el lead en 3-4 intercambios y llevarlo a una reunión con el CEO de la agencia. El CEO es quien da los planes personalizados. Vos preparás el terreno.

SERVICIOS DE {AGENCY}:
- Gestión profesional de redes sociales (Instagram, Facebook, TikTok)
- Campañas de publicidad en Meta Ads (resultados medibles, ROI claro)
- Contenido profesional: fotos, videos, diseño gráfico en tu local
- Páginas web y landing pages que convierten visitas en clientes
Los servicios se combinan en paquetes según las necesidades del cliente.

FLUJO DE CONVERSACIÓN (seguí este orden):
1. BIENVENIDA: Saludá calurosamente. Preguntá su nombre y cómo llegó a {AGENCY}.
2. DIAGNÓSTICO (máx 3 preguntas, una por mensaje):
   a. "¿Qué tipo de negocio tenés y en qué ciudad estás?"
   b. "¿Hoy tenés presencia en redes o empezarías desde cero con nosotros?"
   c. "¿Cuál es el mayor desafío que tenés para conseguir clientes nuevos?"
3. PUENTE: Conectá el dolor específico que mencionó con el servicio de {AGENCY} que lo resuelve. Sé concreto, no listés todo.
4. CTA: Proponé una llamada de diagnóstico de 20 minutos sin compromiso con el CEO. Usá el link de agenda disponible o pedí que te den su disponibilidad.

REGLAS INQUEBRANTABLES:
- Mensajes CORTOS. Máximo 3 líneas. WhatsApp no es un email.
- UNA pregunta por mensaje, nunca dos.
- Si preguntan por precio: "Los planes son personalizados porque cada negocio es distinto. Por eso el CEO hace una llamada de diagnóstico sin costo — así te da un plan real, no genérico."
- Si el lead muestra interés en agendar: incluí el tag [AGENDAR] al final de tu mensaje
- Si el lead está listo para hablar con el CEO (preguntó precio, pidió propuesta, mostró intención real): incluí el tag [HANDOFF] al final de tu mensaje
- Si la conversación sigue su curso normal: incluí el tag [CONTINUAR] al final de tu mensaje
- Si el lead es grosero o claramente no es cliente potencial: cerrá con educación, sin engancharte
- Nunca inventes datos, precios, ni resultados de clientes específicos
- Nunca digas que "somos la mejor agencia" — demostralo con preguntas y escucha activa
- Usá el nombre del prospecto cada 2-3 mensajes para humanizar la conversación

AGENDA: {CALCOM}

HISTORIAL DE CONVERSACIÓN:
{{historial}}"""

workflow = {
    "name": "ALM Bot - WhatsApp + Instagram + Facebook",
    "active": True,
    "nodes": [
        {
            "id": "webhook-trigger",
            "name": "Recibir Mensajes Meta",
            "type": "n8n-nodes-base.webhook",
            "typeVersion": 2,
            "position": [200, 300],
            "webhookId": "meta-bot",
            "parameters": {
                "path": "meta-bot",
                "responseMode": "responseNode",
                "httpMethod": "={{$request.method}}"
            }
        },
        {
            "id": "verify-webhook",
            "name": "Verificar Webhook Meta",
            "type": "n8n-nodes-base.if",
            "typeVersion": 2,
            "position": [420, 300],
            "parameters": {
                "conditions": {
                    "options": {"caseSensitive": True},
                    "conditions": [
                        {
                            "leftValue": "={{$json.query['hub.mode']}}",
                            "operator": {"type": "string", "operation": "equals"},
                            "rightValue": "subscribe"
                        }
                    ]
                }
            }
        },
        {
            "id": "respond-verify",
            "name": "Responder Verificación",
            "type": "n8n-nodes-base.respondToWebhook",
            "typeVersion": 1,
            "position": [640, 200],
            "parameters": {
                "respondWith": "text",
                "responseBody": "={{$json.query['hub.challenge']}}"
            }
        },
        {
            "id": "parse-message",
            "name": "Parsear Mensaje",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [640, 380],
            "parameters": {
                "jsCode": """
const body = $input.first().json.body;
let result = {
  channel: 'unknown',
  senderId: '',
  messageText: '',
  senderName: 'Cliente'
};

try {
  // WhatsApp
  if (body?.entry?.[0]?.changes?.[0]?.value?.messages) {
    const msg = body.entry[0].changes[0].value.messages[0];
    const contact = body.entry[0].changes[0].value.contacts?.[0];
    result.channel = 'whatsapp';
    result.senderId = msg.from;
    result.messageText = msg.text?.body || msg.interactive?.button_reply?.title || '';
    result.senderName = contact?.profile?.name || 'Cliente';
  }
  // Instagram / Facebook Messenger
  else if (body?.entry?.[0]?.messaging) {
    const msg = body.entry[0].messaging[0];
    const pageId = body.entry[0].id;
    result.channel = pageId ? 'facebook' : 'instagram';
    result.senderId = msg.sender.id;
    result.messageText = msg.message?.text || '';
    result.senderName = 'Cliente';
    // Detectar Instagram por source
    if (body.object === 'instagram') result.channel = 'instagram';
  }
} catch(e) {
  result.error = e.message;
}

return [result];
"""
            }
        },
        {
            "id": "read-history",
            "name": "Leer Historial Sheets",
            "type": "n8n-nodes-base.googleSheets",
            "typeVersion": 4,
            "position": [860, 380],
            "parameters": {
                "operation": "read",
                "documentId": SHEETS_ID,
                "sheetName": "Conversaciones",
                "filtersUI": {
                    "values": [
                        {
                            "lookupColumn": "sender_id",
                            "lookupValue": "={{$json.senderId}}"
                        }
                    ]
                }
            }
        },
        {
            "id": "call-groq",
            "name": "Groq AI (Llama 3.3 70B)",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [1080, 380],
            "parameters": {
                "method": "POST",
                "url": "https://api.groq.com/openai/v1/chat/completions",
                "authentication": "genericCredentialType",
                "genericAuthType": "httpHeaderAuth",
                "headers": {
                    "parameters": [
                        {
                            "name": "Authorization",
                            "value": f"Bearer {GROQ_KEY}"
                        }
                    ]
                },
                "contentType": "json",
                "body": {
                    "mode": "raw",
                    "rawParameters": """={
  "model": "llama-3.3-70b-versatile",
  "temperature": 0.75,
  "max_tokens": 300,
  "messages": [
    {
      "role": "system",
      "content": """ + json.dumps(SYSTEM_PROMPT.replace("{historial}", "={{$('Leer Historial Sheets').first()?.json?.historial || 'Sin historial previo.'}}")) + """
    },
    {
      "role": "user",
      "content": "={{$('Parsear Mensaje').first().json.messageText}}"
    }
  ]
}"""
                }
            }
        },
        {
            "id": "detect-intent",
            "name": "Detectar Intención",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [1300, 380],
            "parameters": {
                "jsCode": """
const aiResponse = $input.first().json.choices[0].message.content;
let intent = 'CONTINUAR';
let cleanResponse = aiResponse;

if (aiResponse.includes('[HANDOFF]')) {
  intent = 'HANDOFF';
  cleanResponse = aiResponse.replace('[HANDOFF]', '').trim();
} else if (aiResponse.includes('[AGENDAR]')) {
  intent = 'AGENDAR';
  cleanResponse = aiResponse.replace('[AGENDAR]', '').trim();
} else if (aiResponse.includes('[CONTINUAR]')) {
  cleanResponse = aiResponse.replace('[CONTINUAR]', '').trim();
}

return [{
  intent,
  responseText: cleanResponse,
  originalResponse: aiResponse
}];
"""
            }
        },
        {
            "id": "save-history",
            "name": "Guardar en Sheets",
            "type": "n8n-nodes-base.googleSheets",
            "typeVersion": 4,
            "position": [1520, 280],
            "parameters": {
                "operation": "appendOrUpdate",
                "documentId": SHEETS_ID,
                "sheetName": "Conversaciones",
                "columns": {
                    "mappingMode": "defineBelow",
                    "value": {
                        "sender_id": "={{$('Parsear Mensaje').first().json.senderId}}",
                        "channel": "={{$('Parsear Mensaje').first().json.channel}}",
                        "sender_name": "={{$('Parsear Mensaje').first().json.senderName}}",
                        "last_message": "={{$('Parsear Mensaje').first().json.messageText}}",
                        "last_response": "={{$('Detectar Intención').first().json.responseText}}",
                        "intent": "={{$('Detectar Intención').first().json.intent}}",
                        "status": "={{$('Detectar Intención').first().json.intent === 'HANDOFF' ? 'HANDOFF' : 'ACTIVO'}}",
                        "updated_at": "={{new Date().toISOString()}}",
                        "historial": "={{($('Leer Historial Sheets').first()?.json?.historial || '') + '\\n[CLIENTE]: ' + $('Parsear Mensaje').first().json.messageText + '\\n[LEO]: ' + $('Detectar Intención').first().json.responseText}}"
                    }
                },
                "matchingColumns": ["sender_id"]
            }
        },
        {
            "id": "send-reply-wa",
            "name": "Enviar Respuesta WhatsApp",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [1740, 280],
            "parameters": {
                "method": "POST",
                "url": f"https://graph.facebook.com/v19.0/{WA_PHONE_ID}/messages",
                "headers": {
                    "parameters": [
                        {
                            "name": "Authorization",
                            "value": f"Bearer {WA_TOKEN}"
                        }
                    ]
                },
                "contentType": "json",
                "body": {
                    "mode": "raw",
                    "rawParameters": """{
  "messaging_product": "whatsapp",
  "recipient_type": "individual",
  "to": "={{$('Parsear Mensaje').first().json.senderId}}",
  "type": "text",
  "text": {
    "body": "={{$('Detectar Intención').first().json.responseText}}"
  }
}"""
                }
            }
        },
        {
            "id": "notify-ceo-handoff",
            "name": "Alertar CEO (Handoff)",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [1740, 420],
            "parameters": {
                "method": "POST",
                "url": f"https://graph.facebook.com/v19.0/{WA_PHONE_ID}/messages",
                "headers": {
                    "parameters": [
                        {
                            "name": "Authorization",
                            "value": f"Bearer {WA_TOKEN}"
                        }
                    ]
                },
                "contentType": "json",
                "body": {
                    "mode": "raw",
                    "rawParameters": f"""{{
  "messaging_product": "whatsapp",
  "recipient_type": "individual",
  "to": "{CEO_WA}",
  "type": "text",
  "text": {{
    "body": "🔔 *LEAD CALIENTE - ALM BOT*\\n\\n👤 *Nombre:* ={{{{$('Parsear Mensaje').first().json.senderName}}}}\\n📱 *Canal:* ={{{{$('Parsear Mensaje').first().json.channel}}}}\\n💬 *Último mensaje:* ={{{{$('Parsear Mensaje').first().json.messageText}}}}\\n\\n✅ El lead está listo para hablar con vos. Tomá la conversación desde Meta Business Suite."
  }}
}}"""
                }
            }
        },
        {
            "id": "respond-ok",
            "name": "Responder 200 OK a Meta",
            "type": "n8n-nodes-base.respondToWebhook",
            "typeVersion": 1,
            "position": [1960, 380],
            "parameters": {
                "respondWith": "json",
                "responseBody": '{"status": "ok"}'
            }
        }
    ],
    "connections": {
        "Recibir Mensajes Meta": {
            "main": [[{"node": "Verificar Webhook Meta", "type": "main", "index": 0}]]
        },
        "Verificar Webhook Meta": {
            "main": [
                [{"node": "Responder Verificación", "type": "main", "index": 0}],
                [{"node": "Parsear Mensaje", "type": "main", "index": 0}]
            ]
        },
        "Parsear Mensaje": {
            "main": [[{"node": "Leer Historial Sheets", "type": "main", "index": 0}]]
        },
        "Leer Historial Sheets": {
            "main": [[{"node": "Groq AI (Llama 3.3 70B)", "type": "main", "index": 0}]]
        },
        "Groq AI (Llama 3.3 70B)": {
            "main": [[{"node": "Detectar Intención", "type": "main", "index": 0}]]
        },
        "Detectar Intención": {
            "main": [[
                {"node": "Guardar en Sheets", "type": "main", "index": 0},
                {"node": "Enviar Respuesta WhatsApp", "type": "main", "index": 0}
            ]]
        },
        "Guardar en Sheets": {
            "main": [[{"node": "Alertar CEO (Handoff)", "type": "main", "index": 0}]]
        },
        "Alertar CEO (Handoff)": {
            "main": [[{"node": "Responder 200 OK a Meta", "type": "main", "index": 0}]]
        }
    },
    "settings": {
        "executionOrder": "v1",
        "saveManualExecutions": True,
        "callerPolicy": "workflowsFromSameOwner",
        "errorWorkflow": ""
    }
}

# Importar via API
headers = {
    "X-N8N-API-KEY": N8N_API_KEY,
    "Content-Type": "application/json"
}

data = json.dumps(workflow).encode("utf-8")
req = urllib.request.Request(
    f"{N8N_HOST}/api/v1/workflows",
    data=data,
    headers=headers,
    method="POST"
)

try:
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode())
        workflow_id = result.get("id")
        print(f"✅ Workflow creado exitosamente!")
        print(f"   ID: {workflow_id}")
        print(f"   Nombre: {result.get('name')}")
        print(f"   URL n8n: http://localhost:{config.get('N8N_PORT', '5678')}/workflow/{workflow_id}")
        
        # Activar el workflow
        activate_req = urllib.request.Request(
            f"{N8N_HOST}/api/v1/workflows/{workflow_id}/activate",
            data=b"{}",
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(activate_req) as ar:
            print(f"   Estado: ACTIVO ✅")
            
except urllib.error.HTTPError as e:
    error_body = e.read().decode()
    print(f"❌ Error al crear workflow: {e.code} - {e.reason}")
    print(f"   Detalle: {error_body}")
    sys.exit(1)

PYEOF

chmod +x ~/alm-bot/scripts/create_workflow.py
echo "Script de workflow creado."
```

Ejecutá el script:

```bash
cd ~/alm-bot
python3 scripts/create_workflow.py
```

---

## PASO 7: CONFIGURAR GOOGLE SHEETS (estructura de la base de datos)

Creá un script para inicializar la hoja de cálculo:

```bash
cat > ~/alm-bot/scripts/init_sheets.py << 'PYEOF'
#!/usr/bin/env python3
"""
Inicializa Google Sheets con la estructura necesaria para el bot ALM.
Crea las hojas: Conversaciones, Leads, Resumen.
"""

import json
import os
import urllib.request
import urllib.parse
import time
import base64

env_path = os.path.expanduser("~/alm-bot/config/.env")
config = {}
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            config[k.strip()] = v.strip()

SHEETS_ID = config.get("GOOGLE_SHEETS_ID", "")
SA_EMAIL = config.get("GOOGLE_SERVICE_ACCOUNT_EMAIL", "")
PRIVATE_KEY = config.get("GOOGLE_PRIVATE_KEY", "").replace("\\n", "\n")

if not SHEETS_ID or not SA_EMAIL or not PRIVATE_KEY:
    print("⚠️  Credenciales de Google Sheets incompletas en .env")
    print("   Necesitás: GOOGLE_SHEETS_ID, GOOGLE_SERVICE_ACCOUNT_EMAIL, GOOGLE_PRIVATE_KEY")
    print("   Podés configurar la hoja manualmente creando estas columnas:")
    print("   Hoja 'Conversaciones': sender_id | channel | sender_name | last_message | last_response | intent | status | updated_at | historial")
    print("   Hoja 'Leads': fecha | nombre | canal | negocio | ciudad | dolor | estado")
    exit(0)

print("ℹ️  Para inicializar Google Sheets necesitás instalar google-auth:")
print("   pip3 install google-auth google-auth-httplib2 google-api-python-client")
print("")
print("   O podés crear la estructura manualmente en Google Sheets:")
print("")
print("   📋 HOJA 1: Conversaciones")
print("   Columnas (fila 1 como headers):")
print("   A: sender_id | B: channel | C: sender_name | D: last_message | E: last_response | F: intent | G: status | H: updated_at | I: historial")
print("")
print("   📋 HOJA 2: Leads")
print("   Columnas:")
print("   A: fecha | B: nombre | C: canal | D: negocio | E: ciudad | F: dolor_detectado | G: estado | H: notas")
print("")
print("   ⚠️  IMPORTANTE: Compartir la hoja con: " + SA_EMAIL)
print("   (Dale permisos de Editor)")

PYEOF

python3 ~/alm-bot/scripts/init_sheets.py
```

---

## PASO 8: SCRIPTS DE ARRANQUE Y MANTENIMIENTO

```bash
# Script para iniciar todo el sistema
cat > ~/alm-bot/scripts/start.sh << 'STARTEOF'
#!/bin/bash
echo "🚀 Iniciando ALM Bot..."

# Cargar config
source ~/alm-bot/config/.env

# Verificar n8n
if curl -s "http://localhost:${N8N_PORT}/healthz" > /dev/null 2>&1; then
  echo "✅ n8n corriendo en puerto ${N8N_PORT}"
else
  echo "❌ n8n no está corriendo. Inicialo manualmente."
  exit 1
fi

# Iniciar Cloudflare Tunnel
echo "🌐 Iniciando Cloudflare Tunnel..."
cloudflared tunnel --url "http://localhost:${N8N_PORT}" \
  --no-autoupdate \
  --logfile ~/alm-bot/logs/cloudflared.log \
  2>&1 &

CF_PID=$!
echo $CF_PID > ~/alm-bot/logs/cloudflared.pid
sleep 8

# Extraer URL del tunnel
TUNNEL_URL=$(grep -oP 'https://[a-z0-9-]+\.trycloudflare\.com' ~/alm-bot/logs/cloudflared.log | tail -1)

if [ -n "$TUNNEL_URL" ]; then
  echo "✅ Tunnel activo: ${TUNNEL_URL}"
  echo "📌 Webhook URL para Meta: ${TUNNEL_URL}/webhook/meta-bot"
  echo "TUNNEL_URL=${TUNNEL_URL}" >> ~/alm-bot/config/.env
else
  echo "⚠️  No se pudo detectar la URL del tunnel. Revisá ~/alm-bot/logs/cloudflared.log"
fi

echo ""
echo "✅ ALM Bot iniciado correctamente"
echo "   Panel n8n: http://localhost:${N8N_PORT}"
echo "   Logs: ~/alm-bot/logs/"
STARTEOF

# Script para detener todo
cat > ~/alm-bot/scripts/stop.sh << 'STOPEOF'
#!/bin/bash
echo "Deteniendo ALM Bot..."
if [ -f ~/alm-bot/logs/cloudflared.pid ]; then
  kill $(cat ~/alm-bot/logs/cloudflared.pid) 2>/dev/null
  rm ~/alm-bot/logs/cloudflared.pid
  echo "✅ Cloudflare Tunnel detenido"
fi
echo "✅ Sistema detenido"
STOPEOF

# Script de status
cat > ~/alm-bot/scripts/status.sh << 'STATUSEOF'
#!/bin/bash
source ~/alm-bot/config/.env
echo "=== ALM BOT STATUS ==="
echo ""
echo "n8n:        $(curl -s http://localhost:${N8N_PORT}/healthz > /dev/null 2>&1 && echo '✅ RUNNING' || echo '❌ DOWN')"
echo "Cloudflared: $(pgrep cloudflared > /dev/null && echo '✅ RUNNING' || echo '❌ DOWN')"
echo "Tunnel URL: ${TUNNEL_URL:-'No configurada'}"
echo ""
echo "Logs recientes (cloudflared):"
tail -5 ~/alm-bot/logs/cloudflared.log 2>/dev/null || echo "  Sin logs"
STATUSEOF

chmod +x ~/alm-bot/scripts/*.sh
echo "Scripts creados: start.sh, stop.sh, status.sh"
```

---

## PASO 9: CONFIGURAR META WEBHOOKS (instrucciones detalladas)

Una vez que el tunnel esté activo y tengas la URL pública, seguí estos pasos:

```bash
# Mostrá las instrucciones con la URL correcta
source ~/alm-bot/config/.env
echo "
=======================================================
CONFIGURACIÓN MANUAL EN META DEVELOPERS
=======================================================
URL de tu webhook: ${TUNNEL_URL}/webhook/meta-bot
Token de verificación: ${META_VERIFY_TOKEN}

WHATSAPP:
1. https://developers.facebook.com → Tu App → WhatsApp → Configuration
2. Edit webhook → Callback URL: ${TUNNEL_URL}/webhook/meta-bot
3. Verify token: ${META_VERIFY_TOKEN}
4. → Verify and Save
5. Suscribirse a: messages, messaging_postbacks

INSTAGRAM:
1. Misma app → Instagram → Webhooks
2. Callback URL: ${TUNNEL_URL}/webhook/meta-bot
3. Verify token: ${META_VERIFY_TOKEN}
4. Suscribirse a: messages, messaging_postbacks

FACEBOOK MESSENGER:
1. Misma app → Messenger → Webhooks
2. Callback URL: ${TUNNEL_URL}/webhook/meta-bot
3. Verify token: ${META_VERIFY_TOKEN}
4. Suscribirse a: messages, messaging_postbacks, message_deliveries
=======================================================
"
```

---

## PASO 10: PRUEBAS DEL SISTEMA

```bash
# Test 1: Verificación del webhook (simula lo que hace Meta cuando configurás el webhook)
source ~/alm-bot/config/.env
echo "Test 1: Verificación webhook..."
VERIFY_RESPONSE=$(curl -s "http://localhost:${N8N_PORT}/webhook/meta-bot?hub.mode=subscribe&hub.challenge=TEST123&hub.verify_token=${META_VERIFY_TOKEN}")
if [ "$VERIFY_RESPONSE" = "TEST123" ]; then
  echo "✅ Verificación webhook OK"
else
  echo "⚠️  Respuesta inesperada: $VERIFY_RESPONSE"
fi

# Test 2: Mensaje simulado de WhatsApp
echo "Test 2: Mensaje simulado WhatsApp..."
curl -s -X POST "http://localhost:${N8N_PORT}/webhook/meta-bot" \
  -H "Content-Type: application/json" \
  -d '{
    "object": "whatsapp_business_account",
    "entry": [{
      "id": "TEST_ACCOUNT",
      "changes": [{
        "value": {
          "messaging_product": "whatsapp",
          "contacts": [{"profile": {"name": "Juan Pérez"}, "wa_id": "5491112345678"}],
          "messages": [{
            "from": "5491112345678",
            "id": "TEST_MSG_001",
            "timestamp": "1234567890",
            "text": {"body": "Hola, vi su perfil de Instagram y me interesa lo que hacen"},
            "type": "text"
          }]
        },
        "field": "messages"
      }]
    }]
  }' | jq '.'

echo ""
echo "✅ Tests completados. Revisá el panel de n8n para ver las ejecuciones:"
echo "   http://localhost:${N8N_PORT}/executions"
```

---

## PASO 11: CREAR DASHBOARD DE MONITOREO (HTML local)

```bash
cat > ~/alm-bot/dashboard.html << 'HTMLEOF'
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>ALM Bot - Dashboard</title>
  <style>
    body { font-family: system-ui; max-width: 900px; margin: 40px auto; padding: 20px; background: #f5f5f0; }
    h1 { color: #1a1a2e; }
    .card { background: white; border-radius: 8px; padding: 20px; margin: 16px 0; border: 1px solid #e0e0d8; }
    .status-ok { color: #0F6E56; font-weight: 500; }
    .status-err { color: #993C1D; font-weight: 500; }
    .cmd { background: #1a1a2e; color: #9FE1CB; padding: 12px 16px; border-radius: 6px; font-family: monospace; font-size: 13px; margin: 8px 0; }
    .link { color: #534AB7; }
    h3 { margin-top: 0; }
  </style>
</head>
<body>
  <h1>🦁 ALM Bot — Panel de Control</h1>
  
  <div class="card">
    <h3>Estado del Sistema</h3>
    <p>Verificar manualmente:</p>
    <div class="cmd">bash ~/alm-bot/scripts/status.sh</div>
  </div>
  
  <div class="card">
    <h3>Comandos Principales</h3>
    <div class="cmd">bash ~/alm-bot/scripts/start.sh</div>
    <div class="cmd">bash ~/alm-bot/scripts/stop.sh</div>
    <div class="cmd">bash ~/alm-bot/scripts/status.sh</div>
  </div>
  
  <div class="card">
    <h3>Links Importantes</h3>
    <ul>
      <li><a class="link" href="http://localhost:5678" target="_blank">Panel n8n</a></li>
      <li><a class="link" href="http://localhost:5678/executions" target="_blank">Historial de ejecuciones</a></li>
      <li><a class="link" href="https://developers.facebook.com" target="_blank">Meta Developers</a></li>
      <li><a class="link" href="https://console.groq.com" target="_blank">Groq Console (uso del API)</a></li>
    </ul>
  </div>
  
  <div class="card">
    <h3>Logs en tiempo real</h3>
    <div class="cmd">tail -f ~/alm-bot/logs/cloudflared.log</div>
  </div>

  <div class="card">
    <h3>⚠️ Recordá</h3>
    <ul>
      <li>El tunnel de Cloudflare genera una URL nueva cada reinicio (hasta que configures cuenta CF)</li>
      <li>Actualizar el webhook en Meta Developers cada vez que cambie la URL</li>
      <li>Hacer backup de <code>~/alm-bot/config/.env</code> en lugar seguro</li>
      <li>Rotar el token de WhatsApp antes de que venza (cada 60 días si usás token temporal)</li>
    </ul>
  </div>
</body>
</html>
HTMLEOF

echo "Dashboard creado: ~/alm-bot/dashboard.html"
xdg-open ~/alm-bot/dashboard.html 2>/dev/null || echo "Abrilo manualmente en tu navegador"
```

---

## PASO 12: RESUMEN FINAL Y CHECKLIST

Ejecutá esto al terminar para ver el estado completo:

```bash
source ~/alm-bot/config/.env
echo "
╔══════════════════════════════════════════════════════╗
║           ALM BOT - SETUP COMPLETO                   ║
╠══════════════════════════════════════════════════════╣
║ Proyecto: ~/alm-bot/                                 ║
║ n8n:      http://localhost:${N8N_PORT}                        ║
║ Webhook:  ${TUNNEL_URL}/webhook/meta-bot  ║
╠══════════════════════════════════════════════════════╣
║ CHECKLIST PENDIENTE (manual):                        ║
║  □ Configurar webhook WhatsApp en Meta Developers    ║
║  □ Configurar webhook Instagram en Meta Developers   ║
║  □ Configurar webhook Messenger en Meta Developers   ║
║  □ Crear headers de Google Sheets (ver Paso 7)      ║
║  □ Compartir hoja Sheets con service account        ║
║  □ Probar con mensaje real desde WhatsApp           ║
╠══════════════════════════════════════════════════════╣
║ PARA INICIAR: bash ~/alm-bot/scripts/start.sh        ║
╚══════════════════════════════════════════════════════╝
"
```

---

## NOTAS TÉCNICAS FINALES

**Si la API de n8n no acepta el workflow:** Puede ser que tu versión de n8n tenga una estructura diferente. En ese caso, exportá el workflow como JSON desde la UI de n8n → importalo desde la UI → luego activalo manualmente.

**Si Groq da errores:** Verificar que la API key esté bien copiada. El modelo `llama-3.3-70b-versatile` es el más capaz en el free tier de Groq. Alternativa: `mixtral-8x7b-32768`.

**Si los mensajes no llegan:** El problema más común es que el tunnel expiró y Meta no puede alcanzar el webhook. Reiniciar el tunnel y actualizar la URL en Meta Developers.

**Prioridad de implementación:**
1. WhatsApp primero (mayor volumen de leads en Formosa)
2. Instagram segundo (el @almarktg ya tiene seguidores)
3. Facebook Messenger tercero

**Escalabilidad futura:** Cuando tengas más de 3-4 clientes activos, migrar de Google Sheets a PostgreSQL o Supabase (free tier) como CRM.
