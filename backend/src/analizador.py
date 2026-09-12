from alfabeto import DESPLAZAMIENTO_MIN, DESPLAZAMIENTO_MAX
from cifrado import SF5
from descifrado import SF6
from analisis_frecuencia import SF22


def SF23(texto_cifrado, alfabeto):
    candidatos = []

    texto_atbash = SF5(texto_cifrado, alfabeto)
    candidatos.append({
        "metodo": "ATBASH",
        "desplazamiento": None,
        "texto": texto_atbash,
    })

    for desplazamiento in range(DESPLAZAMIENTO_MIN, DESPLAZAMIENTO_MAX + 1):
        texto_cesar = SF6(texto_cifrado, alfabeto, desplazamiento)
        candidatos.append({
            "metodo": "CESAR",
            "desplazamiento": desplazamiento,
            "texto": texto_cesar,
        })

    return candidatos


def SF24(candidato):
    return candidato["analisis"]["total"]


def SF25(mejor_puntaje, segundo_puntaje, num_letras):
    margen = mejor_puntaje - segundo_puntaje
    margen_relativo = margen / (abs(mejor_puntaje) + 1)
    factor_longitud = min(num_letras / 80, 1.0)

    porcentaje = 45 + min(margen_relativo * 100, 35) + factor_longitud * 20
    porcentaje = max(1.0, min(porcentaje, 99.0))

    if num_letras < 10:
        porcentaje = min(porcentaje, 49.0)

    if margen <= 0:
        porcentaje = min(porcentaje, 20.0)

    if porcentaje >= 75:
        nivel = "alta"
    elif porcentaje >= 50:
        nivel = "media"
    else:
        nivel = "baja"

    return {
        "nivel": nivel,
        "porcentaje": round(porcentaje, 2),
        "margen": round(margen, 4),
    }


def SF26(texto_cifrado, alfabeto):
    candidatos = SF23(texto_cifrado, alfabeto)

    for candidato in candidatos:
        candidato["analisis"] = SF22(candidato["texto"])

    candidatos_ordenados = sorted(candidatos, key=SF24, reverse=True)
    mejor = candidatos_ordenados[0]
    segundo = candidatos_ordenados[1]

    confianza = SF25(
        SF24(mejor),
        SF24(segundo),
        mejor["analisis"]["num_letras"],
    )

    return {
        "metodo": mejor["metodo"],
        "desplazamiento": mejor["desplazamiento"],
        "texto": mejor["texto"],
        "confianza": confianza,
    }
