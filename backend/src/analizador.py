from alfabeto import DESPLAZAMIENTO_MIN, DESPLAZAMIENTO_MAX
from cifrado import SF5
from descifrado import SF6
from analisis_frecuencia import SF18


def SF19(texto_cifrado, alfabeto):
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


def SF20(texto_cifrado, alfabeto):
    candidatos = SF19(texto_cifrado, alfabeto)

    for candidato in candidatos:
        candidato["analisis"] = SF18(candidato["texto"])

    mejor = max(candidatos, key=lambda c: c["analisis"]["total"])

    return {
        "metodo": mejor["metodo"],
        "desplazamiento": mejor["desplazamiento"],
        "texto": mejor["texto"],
    }
