from alfabeto import SF2, SF3


def SF37(texto, alfabeto, codigos, desplazamiento):
    # Sustituye con una tabla ordinal->carácter aplicada con str.translate
    # en vez de un bucle carácter por carácter en Python. Con alfabetos de
    # hasta 1000 caracteres y hasta 999 desplazamientos posibles que probar
    # en la autodetección (SF19), un bucle interpretado por candidato es
    # demasiado lento; recibir "codigos" (los ord() de cada carácter del
    # alfabeto) ya calculados evita repetir ese trabajo en cada llamada.
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
