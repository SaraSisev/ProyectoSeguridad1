import json
import unicodedata

from workers import Response

from alfabeto import SF1, DESPLAZAMIENTO_MIN, DESPLAZAMIENTO_MAX, LIMITE_TEXTO
from cifrado import SF4, SF5
from analizador import SF20


def SF21():
    return {
        "access-control-allow-origin": "*",
        "access-control-allow-methods": "GET, POST, OPTIONS",
        "access-control-allow-headers": "content-type",
    }


def SF22(datos, estado=200):
    encabezados = SF21()
    encabezados["content-type"] = "application/json; charset=utf-8"
    return Response(json.dumps(datos, ensure_ascii=False), status=estado, headers=encabezados)


async def SF23(request):
    crudo = await request.text()
    if not crudo:
        return {}
    try:
        payload = json.loads(crudo)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def SF24(payload):
    alfabeto = payload.get("alfabeto", "")
    if isinstance(alfabeto, str):
        alfabeto = unicodedata.normalize("NFC", alfabeto)
    valido, error = SF1(alfabeto)
    if not valido:
        return {"valido": False, "error": error}, 400
    return {"valido": True, "longitud": len(alfabeto)}, 200


def SF25(payload):
    alfabeto = payload.get("alfabeto", "")
    if isinstance(alfabeto, str):
        alfabeto = unicodedata.normalize("NFC", alfabeto)
    metodo = payload.get("metodo", "")
    texto = payload.get("texto", "")
    if isinstance(texto, str):
        texto = unicodedata.normalize("NFC", texto)

    valido, error = SF1(alfabeto)
    if not valido:
        return {"error": error}, 400
    if not isinstance(texto, str) or texto == "":
        return {"error": "El texto a cifrar no puede estar vacío."}, 400
    if len(texto) > LIMITE_TEXTO:
        return {"error": f"El texto no puede superar los {LIMITE_TEXTO} caracteres."}, 400

    if metodo == "ATBASH":
        resultado = SF5(texto, alfabeto)
        return {"metodo": "ATBASH", "desplazamiento": None, "resultado": resultado}, 200

    if metodo == "CESAR":
        desplazamiento = payload.get("desplazamiento")
        if not isinstance(desplazamiento, int) or isinstance(desplazamiento, bool):
            return {"error": "El desplazamiento debe ser un número entero."}, 400
        if desplazamiento < DESPLAZAMIENTO_MIN or desplazamiento > DESPLAZAMIENTO_MAX:
            return {
                "error": f"El desplazamiento debe estar entre {DESPLAZAMIENTO_MIN} y {DESPLAZAMIENTO_MAX}."
            }, 400
        resultado = SF4(texto, alfabeto, desplazamiento)
        return {"metodo": "CESAR", "desplazamiento": desplazamiento, "resultado": resultado}, 200

    return {"error": "Método de cifrado no reconocido."}, 400


def SF26(payload):
    alfabeto = payload.get("alfabeto", "")
    if isinstance(alfabeto, str):
        alfabeto = unicodedata.normalize("NFC", alfabeto)
    texto = payload.get("texto", "")
    if isinstance(texto, str):
        texto = unicodedata.normalize("NFC", texto)

    valido, error = SF1(alfabeto)
    if not valido:
        return {"error": error}, 400
    if not isinstance(texto, str) or texto == "":
        return {"error": "El texto a descifrar no puede estar vacío."}, 400
    if len(texto) > LIMITE_TEXTO:
        return {"error": f"El texto no puede superar los {LIMITE_TEXTO} caracteres."}, 400

    mejor = SF20(texto, alfabeto)
    return {
        "metodo": mejor["metodo"],
        "desplazamiento": mejor["desplazamiento"],
        "resultado": mejor["texto"],
    }, 200


async def on_fetch(request, env, ctx):
    if request.method == "OPTIONS":
        return Response(None, status=204, headers=SF21())

    ruta = request.url.split("?")[0].rstrip("/")

    if request.method == "POST" and ruta.endswith("/api/alfabeto/validar"):
        payload = await SF23(request)
        if payload is None:
            return SF22({"error": "El cuerpo de la solicitud no es un JSON válido."}, 400)
        datos, estado = SF24(payload)
        return SF22(datos, estado)

    if request.method == "POST" and ruta.endswith("/api/cifrar"):
        payload = await SF23(request)
        if payload is None:
            return SF22({"error": "El cuerpo de la solicitud no es un JSON válido."}, 400)
        datos, estado = SF25(payload)
        return SF22(datos, estado)

    if request.method == "POST" and ruta.endswith("/api/descifrar"):
        payload = await SF23(request)
        if payload is None:
            return SF22({"error": "El cuerpo de la solicitud no es un JSON válido."}, 400)
        datos, estado = SF26(payload)
        return SF22(datos, estado)

    return SF22({"error": "Ruta no encontrada."}, 404)
