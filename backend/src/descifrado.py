from alfabeto import SF2, SF3, DESPLAZAMIENTO_MIN, DESPLAZAMIENTO_MAX
from cifrado import SF5
from analisis_frecuencia import SF10, SF11


def SF6(texto, alfabeto, desplazamiento):
    mapa = SF2(alfabeto)
    paso = SF3(desplazamiento, len(alfabeto))
    resultado = []
    for caracter in texto:
        if caracter in mapa:
            nuevo_indice = (mapa[caracter] - paso) % len(alfabeto)
            resultado.append(alfabeto[nuevo_indice])
        else:
            resultado.append(caracter)
    return "".join(resultado)


def SF7(texto_cifrado, alfabeto):
    candidatos = []

    texto_atbash = SF5(texto_cifrado, alfabeto)
    candidatos.append({
        "metodo": "ATBASH",
        "desplazamiento": None,
        "texto": texto_atbash,
        "puntaje": SF10(texto_atbash),
        "coincidencias": SF11(texto_atbash),
    })

    for desplazamiento in range(DESPLAZAMIENTO_MIN, DESPLAZAMIENTO_MAX + 1):
        texto_cesar = SF6(texto_cifrado, alfabeto, desplazamiento)
        candidatos.append({
            "metodo": "CESAR",
            "desplazamiento": desplazamiento,
            "texto": texto_cesar,
            "puntaje": SF10(texto_cesar),
            "coincidencias": SF11(texto_cesar),
        })

    return min(candidatos, key=lambda c: (-c["coincidencias"], c["puntaje"]))
