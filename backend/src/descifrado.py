from alfabeto import SF2, SF3


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
