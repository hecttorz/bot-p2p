import telebot
import requests
import json

# 1. REEMPLAZA ESTO CON EL TOKEN QUE TE DARÁ EL BOTFATHER
TOKEN_TELEGRAM = "8995400628:AAFyjpJ5BPk1CVHM1x9Zj9RctXMnLsc7xjc"

bot = telebot.TeleBot(TOKEN_TELEGRAM)

def obtener_precio_p2p(fiat, trade_type):
    """Consulta el precio real en el P2P de Binance"""
    url = 'https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search'
    
    payload = {
        "asset": "USDT",
        "fiat": fiat,
        "merchantCheck": True,
        "page": 1,
        "rows": 1, # Tomamos la mejor oferta disponible
        "publisherType": "merchant",
        "tradeType": trade_type
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        respuesta = requests.post(url, json=payload, headers=headers)
        if respuesta.status_code == 200:
            datos = respuesta.json()
            if datos['data']:
                # Extrae el precio del primer comerciante de la lista
                return float(datos['data'][0]['adv']['price'])
        return None
    except Exception as e:
        print(f"Error consultando Binance P2P ({fiat}): {e}")
        return None

@bot.message_handler(commands=['start', 'help'])
def enviar_bienvenida(message):
    texto = (
        "👋 ¡Hola! Soy tu bot de cálculo de tasas P2P.\n\n"
        "Usa el comando /tasa para obtener el cálculo en tiempo real:\n"
        "📌 *(Venta USDT/VES ÷ Compra CLP/USDT) menos el 7%*"
    )
    bot.reply_to(message, texto, parse_mode="Markdown")

@bot.message_handler(commands=['tasa'])
def calcular_tasa(message):
    # Enviar mensaje temporal de carga
    mensaje_espera = bot.reply_to(message, "⏳ Consultando Binance P2P en tiempo real...")
    
    # 1. Obtener los precios del P2P
    ves = obtener_precio_p2p("VES", "SELL") # Venta USDT -> VES
    clp = obtener_precio_p2p("CLP", "BUY")  # Compra CLP -> USDT
    
    if ves is None or clp is None:
        bot.edit_message_text("❌ Error al conectar con Binance. Inténtalo de nuevo en unos segundos.", 
                              chat_id=message.chat.id, 
                              message_id=mensaje_espera.message_id)
        return

    # 2. Aplicar la lógica matemática
    division = ves / clp
    descuento = division * 0.07
    resultado_final = division - descuento

    # 3. Formatear la respuesta
    respuesta_texto = (
        "📊 *CÁLCULO DE TASA EN TIEMPO REAL*\n"
        "====================================\n\n"
        f"🇻🇪 *USDT a VES (Venta):* Bs. {ves:,.2f}\n"
        f"🇨🇱 *CLP a USDT (Compra):* $ {clp:,.2f}\n\n"
        "------------------------------------\n"
        f"🧮 *División directa:* {division:.6f}\n"
        "📉 *Descuento aplicado:* 7.00%\n\n"
        f"🚀 *TASA NETO FINAL: {resultado_final:.6f}* VES/CLP\n"
        "====================================\n"
        "_(Cada peso chileno equivale al resultado final en bolívares)_"
    )

    # Editar el mensaje de espera con el resultado final
    bot.edit_message_text(respuesta_texto, 
                          chat_id=message.chat.id, 
                          message_id=mensaje_espera.message_id, 
                          parse_mode="Markdown")

if __name__ == "__main__":
    print("Bot encendido y escuchando mensajes...")
    bot.infinity_polling()
