import json

from workers import Response

from alfabeto import SF1, DESPLAZAMIENTO_MIN, DESPLAZAMIENTO_MAX
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
    return json.loads(crudo)


def SF24(payload):
    alfabeto = payload.get("alfabeto", "")
    valido, error = SF1(alfabeto)
    if not valido:
        return {"valido": False, "error": error}, 400
    return {"valido": True, "longitud": len(alfabeto)}, 200


def SF25(payload):
    alfabeto = payload.get("alfabeto", "")
    metodo = payload.get("metodo", "")
    texto = payload.get("texto", "")

    valido, error = SF1(alfabeto)
    if not valido:
        return {"error": error}, 400
    if not isinstance(texto, str) or texto == "":
        return {"error": "El texto a cifrar no puede estar vacío."}, 400

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
    texto = payload.get("texto", "")

    valido, error = SF1(alfabeto)
    if not valido:
        return {"error": error}, 400
    if not isinstance(texto, str) or texto == "":
        return {"error": "El texto a descifrar no puede estar vacío."}, 400

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
        datos, estado = SF24(payload)
        return SF22(datos, estado)

    if request.method == "POST" and ruta.endswith("/api/cifrar"):
        payload = await SF23(request)
        datos, estado = SF25(payload)
        return SF22(datos, estado)

    if request.method == "POST" and ruta.endswith("/api/descifrar"):
        payload = await SF23(request)
        datos, estado = SF26(payload)
        return SF22(datos, estado)

    return SF22({"error": "Ruta no encontrada."}, 404)
