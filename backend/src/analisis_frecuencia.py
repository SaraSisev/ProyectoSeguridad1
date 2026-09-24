import re
from collections import Counter

from datos_espanol import (
    SF7,
    SF8,
    LETRAS_ESPANOL,
    VOCALES,
    FRECUENCIA_LETRAS,
    PALABRAS_MUY_COMUNES,
    PALABRAS_COMUNES,
    PESOS_BIGRAMAS,
    PESOS_TRIGRAMAS,
    PESOS_TETRAGRAMAS,
    PESOS_PREFIJOS,
    PESOS_SUFIJOS,
    PESOS_SECUENCIAS_IMPROBABLES,
    RATIO_VOCALES_OBJETIVO,
    RATIO_VOCALES_MIN,
    RATIO_VOCALES_MAX,
    LONGITUD_PALABRA_MAX_RAZONABLE,
)

PATRON_REPETICION = re.compile(r"(.)\1{3,}")

MUESTRA_MINIMA_CONFIABLE = 15
NEUTRO_FRECUENCIA = 8.0


def SF9(texto_normalizado):
    letras = [c for c in texto_normalizado if c in LETRAS_ESPANOL]
    total = len(letras)
    if total == 0:
        return -20.0

    observadas = Counter(letras)
    chi_cuadrado = 0.0
    for letra, frecuencia_esperada in FRECUENCIA_LETRAS.items():
        esperado = total * frecuencia_esperada / 100
        if esperado == 0:
            continue
        observado = observadas.get(letra, 0)
        chi_cuadrado += ((observado - esperado) ** 2) / esperado

    chi_cuadrado_normalizado = chi_cuadrado / total
    puntaje_bruto = 35.0 / (1.0 + chi_cuadrado_normalizado)

    confianza = min(1.0, total / MUESTRA_MINIMA_CONFIABLE)
    return NEUTRO_FRECUENCIA + confianza * (puntaje_bruto - NEUTRO_FRECUENCIA)


def SF10(palabras):
    puntaje = 0.0
    for palabra in palabras:
        if len(palabra) < 3:
            continue
        if palabra in PALABRAS_MUY_COMUNES:
            puntaje += 4.0 + min(len(palabra), 8) * 0.80
        elif palabra in PALABRAS_COMUNES:
            puntaje += 2.5 + min(len(palabra), 8) * 0.50
    return puntaje


def SF11(texto_normalizado, tabla_pesos):
    puntaje = 0.0
    for patron, peso in tabla_pesos.items():
        apariciones = texto_normalizado.count(patron)
        puntaje += apariciones * peso
    return puntaje


def SF12(palabras):
    puntaje = 0.0
    for palabra in palabras:
        for prefijo, peso in PESOS_PREFIJOS.items():
            if len(palabra) > len(prefijo) + 1 and palabra.startswith(prefijo):
                puntaje += peso
    return puntaje


def SF13(palabras):
    puntaje = 0.0
    for sufijo, peso in PESOS_SUFIJOS.items():
        for palabra in palabras:
            if len(palabra) > len(sufijo) and palabra.endswith(sufijo):
                puntaje += peso
    return puntaje


def SF14(texto_normalizado):
    penalizacion = 0.0
    for secuencia, peso in PESOS_SECUENCIAS_IMPROBABLES.items():
        penalizacion += texto_normalizado.count(secuencia) * peso
    return penalizacion


def SF15(texto_normalizado):
    letras = [c for c in texto_normalizado if c in LETRAS_ESPANOL]
    if not letras:
        return -20.0, 0.0

    vocales = sum(1 for c in letras if c in VOCALES)
    ratio = vocales / len(letras)
    distancia = abs(ratio - RATIO_VOCALES_OBJETIVO)
    puntaje_bruto = 12.0 - distancia * 40

    confianza = min(1.0, len(letras) / MUESTRA_MINIMA_CONFIABLE)

    if confianza >= 1.0 and (ratio < RATIO_VOCALES_MIN or ratio > RATIO_VOCALES_MAX):
        puntaje_bruto -= 8.0

    puntaje = puntaje_bruto * confianza

    return puntaje, ratio


def SF16(palabra):
    mas_larga = 0
    actual = 0
    for caracter in palabra:
        if caracter not in VOCALES:
            actual += 1
            mas_larga = max(mas_larga, actual)
        else:
            actual = 0
    return mas_larga


def SF17(palabras):
    if not palabras:
        return -15.0

    puntaje = min(len(palabras), 6) * 0.50

    for palabra in palabras:
        if len(palabra) > LONGITUD_PALABRA_MAX_RAZONABLE:
            puntaje -= (len(palabra) - LONGITUD_PALABRA_MAX_RAZONABLE) * 0.50

        contiene_vocal = any(c in VOCALES for c in palabra)
        if len(palabra) > 1 and not contiene_vocal:
            puntaje -= min(len(palabra), 4) * 0.75

        secuencia_consonantes = SF16(palabra)
        if secuencia_consonantes >= 5:
            puntaje -= (secuencia_consonantes - 4) * 1.50

        if PATRON_REPETICION.search(palabra):
            puntaje -= 3.0

    return puntaje


def SF18(texto):
    normalizado = SF7(texto)
    palabras = SF8(normalizado)

    puntaje_frecuencia = SF9(normalizado)
    puntaje_comunes = SF10(palabras)
    puntaje_bigramas = SF11(normalizado, PESOS_BIGRAMAS)
    puntaje_trigramas = SF11(normalizado, PESOS_TRIGRAMAS)
    puntaje_tetragramas = SF11(normalizado, PESOS_TETRAGRAMAS)
    puntaje_prefijos = SF12(palabras)
    puntaje_sufijos = SF13(palabras)
    puntaje_vocales, ratio_vocales = SF15(normalizado)
    puntaje_estructura = SF17(palabras)
    penalizacion = SF14(normalizado)

    total = (
        puntaje_frecuencia
        + puntaje_comunes
        + puntaje_bigramas
        + puntaje_trigramas
        + puntaje_tetragramas
        + puntaje_prefijos
        + puntaje_sufijos
        + puntaje_vocales
        + puntaje_estructura
        - penalizacion
    )

    return {
        "total": total,
        "componentes": {
            "frecuencia_letras": puntaje_frecuencia,
            "palabras_comunes": puntaje_comunes,
            "bigramas": puntaje_bigramas,
            "trigramas": puntaje_trigramas,
            "tetragramas": puntaje_tetragramas,
            "prefijos": puntaje_prefijos,
            "sufijos": puntaje_sufijos,
            "vocales": puntaje_vocales,
            "estructura_palabras": puntaje_estructura,
            "secuencias_improbables": -penalizacion,
        },
        "ratio_vocales": ratio_vocales,
        "num_palabras": len(palabras),
        "num_letras": sum(1 for c in normalizado if c in LETRAS_ESPANOL),
    }
