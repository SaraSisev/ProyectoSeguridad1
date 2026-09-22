from alfabeto import DESPLAZAMIENTO_MINIMO, SF36
from cifrado import SF5
from descifrado import SF38
from analisis_frecuencia import SF18


def SF19(texto_cifrado, alfabeto):
    candidatos = []

    texto_atbash = SF5(texto_cifrado, alfabeto)
    candidatos.append({
        "metodo": "ATBASH",
        "desplazamiento": None,
        "texto": texto_atbash,
    })

    # El desplazamiento máximo depende del tamaño real del alfabeto (puede
    # llegar a 1000 caracteres), no de un valor fijo como 25: con un
    # alfabeto de longitud N existen N-1 desplazamientos César no
    # triviales, y hay que probarlos todos para que la autodetección
    # encuentre el correcto sin importar qué desplazamiento se usó al
    # cifrar.
    codigos = [ord(caracter) for caracter in alfabeto]
    desplazamiento_maximo = SF36(len(alfabeto))

    for desplazamiento in range(DESPLAZAMIENTO_MINIMO, desplazamiento_maximo + 1):
        texto_cesar = SF38(texto_cifrado, alfabeto, codigos, desplazamiento)
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
