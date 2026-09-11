import unicodedata

FREC_ESPANOL = {
    "a": 12.53, "b": 1.42, "c": 4.68, "d": 5.86, "e": 13.68, "f": 0.69,
    "g": 1.01, "h": 0.70, "i": 6.25, "j": 0.44, "k": 0.02, "l": 4.97,
    "m": 3.15, "n": 6.71, "ñ": 0.31, "o": 8.68, "p": 2.51, "q": 0.88,
    "r": 6.87, "s": 7.98, "t": 4.63, "u": 3.93, "v": 0.90, "w": 0.02,
    "x": 0.22, "y": 0.90, "z": 0.52,
}

TABLA_ACENTOS = str.maketrans("áéíóúÁÉÍÓÚüÜ", "aeiouAEIOUuU")

PALABRAS_COMUNES = {
    "DE", "LA", "QUE", "EL", "EN", "Y", "A", "LOS", "DEL", "SE", "LAS", "POR",
    "UN", "PARA", "CON", "NO", "UNA", "SU", "AL", "LO", "COMO", "MAS", "PERO",
    "SUS", "LE", "YA", "O", "ESTE", "SI", "PORQUE", "ESTA", "ENTRE", "CUANDO",
    "MUY", "SIN", "SOBRE", "TAMBIEN", "ME", "HASTA", "HAY", "DONDE", "QUIEN",
    "DESDE", "TODO", "NOS", "DURANTE", "TODOS", "UNO", "LES", "NI", "CONTRA",
    "OTROS", "ESE", "ESO", "ANTE", "ELLOS", "ESTO", "MI", "ANTES", "ALGUNOS",
    "UNOS", "YO", "OTRO", "OTRAS", "OTRA", "TANTO", "ESA", "ESTOS", "MUCHO",
    "QUIENES", "NADA", "MUCHOS", "CUAL", "POCO", "ELLA", "ESTAR", "ESTAS",
    "ALGUNAS", "ALGO", "NOSOTROS", "MIS", "TU", "TE", "TI", "TUS", "ELLAS",
    "NOSOTRAS", "VOSOTROS", "VOSOTRAS", "OS", "SUYO", "SUYA", "NUESTRO",
    "NUESTRA", "NUESTROS", "NUESTRAS", "ESOS", "ESAS", "ESTOY", "ESTAMOS",
    "ESTAN", "SOY", "ERES", "ES", "SOMOS", "SOIS", "SON", "SEA", "HE", "HAS",
    "HA", "HEMOS", "HAN", "HABIA", "HABIAN", "SERA", "SERAN", "TENGO",
    "TIENES", "TIENE", "TENEMOS", "TIENEN", "HACER", "HAGO", "HACES", "HACE",
    "HACEMOS", "HACEN", "HOLA", "MUNDO", "GRACIAS", "ADIOS", "AMOR", "VIDA",
    "TIEMPO", "CASA", "AGUA", "DIA", "NOCHE", "SOL", "LUNA", "ATAQUE",
    "AMANECER", "CONFIRMADO", "VERDAD", "MENSAJE", "SECRETO", "BIEN", "MAL",
    "GRANDE", "BUENO", "MALO", "NUEVO", "VIEJO", "HOMBRE", "MUJER", "AMIGO",
    "FAMILIA", "TRABAJO", "VER", "DAR", "IR", "VOY", "VA", "VAMOS", "SABER",
    "QUERER", "QUIERO", "PODER", "PUEDE", "DECIR", "DICE", "AQUI", "ALLI",
    "HOY", "AYER", "MANANA",
}

LIMITE_ALFABETO = 256
DESPLAZAMIENTO_MIN = 1
DESPLAZAMIENTO_MAX = 25


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


def SF3(desplazamiento, longitud_alfabeto):
    if not isinstance(desplazamiento, int) or isinstance(desplazamiento, bool):
        raise ValueError("El desplazamiento debe ser un número entero.")
    if desplazamiento < DESPLAZAMIENTO_MIN or desplazamiento > DESPLAZAMIENTO_MAX:
        raise ValueError(
            f"El desplazamiento debe estar entre {DESPLAZAMIENTO_MIN} y {DESPLAZAMIENTO_MAX}."
        )
    return desplazamiento % longitud_alfabeto


def SF4(texto, alfabeto, desplazamiento):
    mapa = SF2(alfabeto)
    paso = SF3(desplazamiento, len(alfabeto))
    resultado = []
    for caracter in texto:
        if caracter in mapa:
            nuevo_indice = (mapa[caracter] + paso) % len(alfabeto)
            resultado.append(alfabeto[nuevo_indice])
        else:
            resultado.append(caracter)
    return "".join(resultado)


def SF5(texto, alfabeto, desplazamiento):
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


def SF6(texto, alfabeto):
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


def SF7(texto):
    return texto.translate(TABLA_ACENTOS)


def SF8(texto):
    limpio = SF7(texto).lower()
    conteo = {letra: 0 for letra in FREC_ESPANOL}
    total = 0
    for caracter in limpio:
        if caracter in conteo:
            conteo[caracter] += 1
            total += 1
    return conteo, total


def SF9(texto):
    conteo, total = SF8(texto)
    if total == 0:
        return float("inf")
    chi_cuadrado = 0.0
    for letra, frecuencia_esperada in FREC_ESPANOL.items():
        esperado = total * (frecuencia_esperada / 100)
        observado = conteo[letra]
        if esperado > 0:
            chi_cuadrado += ((observado - esperado) ** 2) / esperado
    return chi_cuadrado


def SF26(texto):
    limpio = SF7(texto).upper()
    palabras = []
    actual = []
    for caracter in limpio:
        if caracter.isalpha():
            actual.append(caracter)
        else:
            if actual:
                palabras.append("".join(actual))
                actual = []
    if actual:
        palabras.append("".join(actual))
    return sum(
        len(palabra) for palabra in palabras
        if len(palabra) >= 2 and palabra in PALABRAS_COMUNES
    )


def SF10(texto_cifrado, alfabeto):
    candidatos = []

    texto_atbash = SF6(texto_cifrado, alfabeto)
    candidatos.append({
        "metodo": "ATBASH",
        "desplazamiento": None,
        "texto": texto_atbash,
        "puntaje": SF9(texto_atbash),
        "coincidencias": SF26(texto_atbash),
    })

    for desplazamiento in range(DESPLAZAMIENTO_MIN, DESPLAZAMIENTO_MAX + 1):
        texto_cesar = SF5(texto_cifrado, alfabeto, desplazamiento)
        candidatos.append({
            "metodo": "CESAR",
            "desplazamiento": desplazamiento,
            "texto": texto_cesar,
            "puntaje": SF9(texto_cesar),
            "coincidencias": SF26(texto_cesar),
        })

    return min(candidatos, key=lambda c: (-c["coincidencias"], c["puntaje"]))
