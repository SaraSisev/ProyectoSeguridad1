from alfabeto import SF3


def SF38(texto, alfabeto, codigos, desplazamiento):
    # Tabla de descifrado por str.translate: la contraparte de SF37 (cifrado.py)
    # pero restando el paso en vez de sumarlo. Usada por SF19 para probar,
    # con velocidad, cada uno de los desplazamientos posibles al hacer fuerza
    # bruta sobre un alfabeto de hasta 1000 caracteres.
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
