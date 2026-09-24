from alfabeto import SF3


def SF38(texto, alfabeto, codigos, desplazamiento):
    paso = SF3(desplazamiento, len(alfabeto))
    longitud = len(alfabeto)
    tabla = {
        codigos[indice]: alfabeto[(indice - paso) % longitud]
        for indice in range(longitud)
    }
    return texto.translate(tabla)


def SF6(texto, alfabeto, desplazamiento):
    codigos = [ord(caracter) for caracter in alfabeto]
    return SF38(texto, alfabeto, codigos, desplazamiento)
