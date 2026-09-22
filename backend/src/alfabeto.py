LIMITE_ALFABETO = 1000
LIMITE_TEXTO = 10000
DESPLAZAMIENTO_MINIMO = 1


def SF1(alfabeto):
    if not isinstance(alfabeto, str) or len(alfabeto) == 0:
        return False, "El alfabeto no puede estar vacío."
    caracteres = list(alfabeto)
    if len(caracteres) > LIMITE_ALFABETO:
        return False, f"El alfabeto no puede superar los {LIMITE_ALFABETO} caracteres."
    if len(set(caracteres)) != len(caracteres):
        return False, "El alfabeto no puede contener caracteres repetidos."
    if len(set(caracteres)) < 2:
        return False, "El alfabeto debe tener al menos 2 caracteres distintos."
    return True, ""


def SF2(alfabeto):
    return {caracter: indice for indice, caracter in enumerate(alfabeto)}


def SF36(longitud_alfabeto):
    return longitud_alfabeto - 1


def SF3(desplazamiento, longitud_alfabeto):
    if not isinstance(desplazamiento, int) or isinstance(desplazamiento, bool):
        raise ValueError("El desplazamiento debe ser un número entero.")
    desplazamiento_maximo = SF36(longitud_alfabeto)
    if desplazamiento < DESPLAZAMIENTO_MINIMO or desplazamiento > desplazamiento_maximo:
        raise ValueError(
            f"El desplazamiento debe estar entre {DESPLAZAMIENTO_MINIMO} "
            f"y {desplazamiento_maximo} para un alfabeto de "
            f"{longitud_alfabeto} caracteres."
        )
    return desplazamiento % longitud_alfabeto
