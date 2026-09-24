from alfabeto import SF2, SF3


def SF37(texto, alfabeto, codigos, desplazamiento):
    paso = SF3(desplazamiento, len(alfabeto))
    longitud = len(alfabeto)
    tabla = {
        codigos[indice]: alfabeto[(indice + paso) % longitud]
        for indice in range(longitud)
    }
    return texto.translate(tabla)


def SF4(texto, alfabeto, desplazamiento):
    codigos = [ord(caracter) for caracter in alfabeto]
    return SF37(texto, alfabeto, codigos, desplazamiento)


def SF5(texto, alfabeto):
    mapa = SF2(alfabeto)
    longitud = len(alfabeto)
    resultado = []
    for caracter in texto:
        if caracter in mapa:
            nuevo_indice = longitud - 1 - mapa[caracter]
            resultado.append(alfabeto[nuevo_indice])
        else:
            resultado.append(caracter)
    return "".join(resultado)
