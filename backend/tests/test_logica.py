import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from alfabeto import SF1, LIMITE_ALFABETO, LIMITE_TEXTO, DESPLAZAMIENTO_MIN, DESPLAZAMIENTO_MAX
from cifrado import SF4, SF5
from descifrado import SF6
from analizador import SF20

ALFABETO = "ABCDEFGHIJKLMNÑOPQRSTUVWXYZ"
ALFABETO_SIMPLE = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

_resultados = []


def prueba(nombre):
    def decorador(funcion):
        _resultados.append((nombre, funcion))
        return funcion
    return decorador


@prueba("alfabeto vacio se rechaza")
def t01():
    valido, _ = SF1("")
    assert valido is False


@prueba("alfabeto de 1 caracter se rechaza")
def t02():
    valido, _ = SF1("A")
    assert valido is False


@prueba("alfabeto de 2 caracteres se acepta")
def t03():
    valido, _ = SF1("AB")
    assert valido is True


@prueba(f"alfabeto de {LIMITE_ALFABETO} caracteres repetidos se rechaza (no son {LIMITE_ALFABETO} distintos)")
def t04():
    valido, _ = SF1("A" * LIMITE_ALFABETO)
    assert valido is False


@prueba(f"alfabeto de {LIMITE_ALFABETO} caracteres distintos se acepta")
def t04b():
    alfabeto_limite = "".join(chr(c) for c in range(0x21, 0x21 + LIMITE_ALFABETO))
    valido, _ = SF1(alfabeto_limite)
    assert valido is True
    assert len(alfabeto_limite) == LIMITE_ALFABETO


@prueba(f"alfabeto de {LIMITE_ALFABETO + 1} caracteres distintos se rechaza")
def t05():
    alfabeto_257 = "".join(chr(c) for c in range(0x21, 0x21 + LIMITE_ALFABETO + 1))
    valido, _ = SF1(alfabeto_257)
    assert valido is False


@prueba("alfabeto con caracteres repetidos se rechaza")
def t06():
    valido, _ = SF1("AAB")
    assert valido is False


@prueba("alfabeto con simbolos, digitos y CJK se acepta")
def t07():
    valido, _ = SF1("ABC0123 .,¡!¿?中文")
    assert valido is True


@prueba("desplazamiento 0 se rechaza")
def t08():
    try:
        SF4("A", ALFABETO, 0)
        assert False, "deberia haber lanzado ValueError"
    except ValueError:
        pass


@prueba(f"desplazamiento {DESPLAZAMIENTO_MAX + 1} se rechaza")
def t09():
    try:
        SF4("A", ALFABETO, DESPLAZAMIENTO_MAX + 1)
        assert False, "deberia haber lanzado ValueError"
    except ValueError:
        pass


@prueba("desplazamiento negativo se rechaza (a diferencia de un modulo simple)")
def t10():
    try:
        SF4("A", ALFABETO, -1)
        assert False, "deberia haber lanzado ValueError"
    except ValueError:
        pass


@prueba(f"desplazamiento {DESPLAZAMIENTO_MIN} se acepta")
def t11():
    resultado = SF4("A", ALFABETO, DESPLAZAMIENTO_MIN)
    assert resultado == "B"


@prueba(f"desplazamiento {DESPLAZAMIENTO_MAX} se acepta")
def t12():
    resultado = SF4("A", ALFABETO_SIMPLE, DESPLAZAMIENTO_MAX)
    assert resultado == "Z"


@prueba("cesar: HOLA con shift 3 da KROD (calculo manual verificado, alfabeto A-Z sin Ñ)")
def t13():
    assert SF4("HOLA", ALFABETO_SIMPLE, 3) == "KROD"


@prueba("cesar: roundtrip cifrar/descifrar para todos los shifts 1-25")
def t14():
    texto = "LA FAMILIA COME EN LA COCINA"
    for shift in range(DESPLAZAMIENTO_MIN, DESPLAZAMIENTO_MAX + 1):
        cifrado = SF4(texto, ALFABETO, shift)
        descifrado = SF6(cifrado, ALFABETO, shift)
        assert descifrado == texto, f"fallo en shift={shift}"


@prueba("cesar: los caracteres fuera del alfabeto se pasan por alto")
def t15():
    resultado = SF4("ABC 123!", "ABC", 1)
    assert resultado == "BCA 123!"


@prueba("atbash: ABC XYZ da ZYX CBA")
def t16():
    assert SF5("ABC XYZ", "ABCDEFGHIJKLMNOPQRSTUVWXYZ") == "ZYX CBA"


@prueba("atbash: aplicarlo dos veces devuelve el texto original (es autoinverso)")
def t17():
    texto = "HOLA MUNDO"
    una_vez = SF5(texto, ALFABETO)
    dos_veces = SF5(una_vez, ALFABETO)
    assert dos_veces == texto


@prueba("autodeteccion: frase larga cifrada con Cesar shift 7 se identifica correctamente")
def t18():
    texto = (
        "EL RAPIDO ZORRO MARRON SALTA SOBRE EL PERRO PEREZOSO MIENTRAS EL SOL SE OCULTA "
        "EN EL HORIZONTE Y LOS PAJAROS VUELAN HACIA EL SUR BUSCANDO UN LUGAR CALIDO PARA "
        "PASAR EL INVIERNO SIN PREOCUPACIONES NI DIFICULTADES EN EL CAMINO LARGO"
    )
    cifrado = SF4(texto, ALFABETO, 7)
    resultado = SF20(cifrado, ALFABETO)
    assert resultado["metodo"] == "CESAR"
    assert resultado["desplazamiento"] == 7
    assert resultado["texto"] == texto


@prueba("autodeteccion: los 25 desplazamientos posibles se detectan correctamente en una frase")
def t19():
    texto = "ESTA ES UNA PRUEBA DE COMUNICACION ENTRE VARIAS PERSONAS DE LA MISMA FAMILIA"
    for shift in range(DESPLAZAMIENTO_MIN, DESPLAZAMIENTO_MAX + 1):
        cifrado = SF4(texto, ALFABETO, shift)
        resultado = SF20(cifrado, ALFABETO)
        assert resultado["metodo"] == "CESAR" and resultado["desplazamiento"] == shift, (
            f"fallo en shift={shift}: detecto {resultado['metodo']} {resultado['desplazamiento']}"
        )


@prueba("autodeteccion: frase larga cifrada con Atbash se identifica correctamente")
def t20():
    texto = "LA FAMILIA COME EN LA COCINA TODOS LOS DIAS DESPUES DEL TRABAJO"
    cifrado = SF5(texto, ALFABETO)
    resultado = SF20(cifrado, ALFABETO)
    assert resultado["metodo"] == "ATBASH"
    assert resultado["texto"] == texto


@prueba("autodeteccion: alfabeto mixto con simbolos y CJK, roundtrip completo")
def t21():
    alfabeto_mixto = "ABCDEFGHIJKLMNÑOPQRSTUVWXYZ0123456789 .,¡!¿?中文"
    texto = "ATAQUE AL AMANECER, CONFIRMADO ¿VERDAD? 中文"
    cifrado = SF4(texto, alfabeto_mixto, 11)
    descifrado = SF6(cifrado, alfabeto_mixto, 11)
    assert descifrado == texto


@prueba("caso documentado: palabra suelta muy corta puede fallar la autodeteccion")
def t22():
    # Esta prueba documenta una limitacion conocida, no exige que el sistema acierte:
    # con muy pocas letras, el analisis de frecuencias no tiene material suficiente.
    # Se deja registrada para poder monitorear si el comportamiento cambia con el tiempo.
    cifrado = SF5("HOLA", ALFABETO)
    resultado = SF20(cifrado, ALFABETO)
    # No se afirma nada sobre el resultado: solo que la funcion no truena.
    assert "metodo" in resultado and "texto" in resultado


def ejecutar():
    fallos = []
    for nombre, funcion in _resultados:
        try:
            funcion()
        except AssertionError as error:
            fallos.append((nombre, str(error)))
        except Exception as error:  # noqa: BLE001
            fallos.append((nombre, f"{type(error).__name__}: {error}"))

    total = len(_resultados)
    exitosas = total - len(fallos)
    print(f"{exitosas}/{total} pruebas pasaron.")
    if fallos:
        print("\nFallos:")
        for nombre, detalle in fallos:
            print(f" - {nombre}: {detalle}")
        raise SystemExit(1)


if __name__ == "__main__":
    ejecutar()
