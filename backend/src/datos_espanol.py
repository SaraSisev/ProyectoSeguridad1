import re
from collections import Counter

TABLA_ACENTOS = str.maketrans("áéíóúÁÉÍÓÚüÜ", "aeiouAEIOUuU")

LETRAS_ESPANOL = set("abcdefghijklmnñopqrstuvwxyz")
VOCALES = set("aeiouáéíóúü")

PATRON_PALABRA = re.compile(r"[a-zñ]+")

CORPUS_REFERENCIA = """
Cada mañana, cuando el sol empieza a subir sobre las montañas, el pequeño
pueblo despierta poco a poco. Los pájaros cantan cerca de la ventana y el
aire huele a pan recién horneado. Mi abuela siempre dice que un buen
desayuno con huevos, queso y jugo de naranja es la mejor manera de
comenzar cualquier jornada de trabajo.

Durante el fin de semana, toda la familia se reúne en la cocina para
preparar una comida especial. Mientras mi tío corta las verduras, mi
prima organiza los platos y mi hermano menor juega con el perro en el
jardín. A veces cocinamos un guiso de pollo con zanahoria, calabaza y un
toque de pimienta; otras veces preferimos un simple arroz con frijoles y
un poco de queso rallado por encima.

La tecnología ha cambiado mucho la forma en que vivimos. Ahora es posible
enviar un mensaje instantáneo a cualquier parte del mundo, ver una
película en la televisión desde el teléfono o comprar un boleto de avión
sin salir de casa. Sin embargo, muchos jóvenes extrañan los juegos
tradicionales al aire libre, como saltar la cuerda, jugar al fútbol en el
parque o simplemente conversar bajo la sombra de un árbol grande.

El año pasado viajamos hacia el sur del país para conocer una antigua
ciudad construida junto al río. Caminamos por calles estrechas de piedra,
visitamos un museo con objetos de cerámica y compramos artesanías hechas
a mano en un pequeño mercado. Por la noche, el cielo se llenaba de
estrellas y el silencio del campo contrastaba con el ruido constante de
la ciudad donde normalmente vivimos.

El deporte también ocupa un lugar importante en nuestra rutina semanal.
Los martes y jueves corremos varios kilómetros por el parque cercano,
mientras que los sábados jugamos un partido amistoso de baloncesto o de
voleibol con los vecinos. Después del ejercicio, siempre tomamos agua
fresca y comemos alguna fruta, como una manzana, un kiwi o un poco de
sandía, para recuperar energía.

La historia de nuestra región está llena de relatos curiosos. Cuenta la
leyenda que hace muchos siglos existió un pequeño reino gobernado por una
reina muy justa, que ayudaba a los campesinos a mejorar sus cosechas y
resolvía los conflictos entre vecinos con sabiduría y paciencia. Aunque
nadie sabe con exactitud si esa historia es verdadera, los ancianos del
pueblo todavía la cuentan con orgullo alrededor de una fogata durante las
noches frías de invierno.

Por último, no hay nada como disfrutar de un buen libro bajo la luz
suave de una lámpara mientras afuera llueve suavemente. El sonido del
agua golpeando la ventana, mezclado con el aroma de un café caliente,
crea una sensación de tranquilidad difícil de explicar con palabras.
Quizás por eso, después de un día largo de trabajo, muchas personas
encuentran en la lectura un refugio sencillo pero muy valioso para
descansar la mente y el corazón.
"""

PALABRAS_MUY_COMUNES = {
    "de", "la", "que", "el", "en", "y", "a", "los", "se", "del", "las",
    "por", "un", "para", "con", "no", "una", "su", "al", "lo", "es",
}

PALABRAS_COMUNES_BASE = {
    "como", "mas", "pero", "sus", "le", "ya", "o", "este", "si", "porque",
    "esta", "entre", "cuando", "muy", "sin", "sobre", "tambien", "me",
    "hasta", "hay", "donde", "quien", "desde", "todo", "nos", "durante",
    "todos", "uno", "les", "ni", "contra", "otros", "ese", "eso", "ante",
    "ellos", "esto", "mi", "antes", "algunos", "unos", "yo", "otro",
    "otras", "otra", "tanto", "esa", "estos", "mucho", "quienes", "nada",
    "muchos", "cual", "poco", "ella", "estar", "estas", "algunas", "algo",
    "nosotros", "mis", "tu", "te", "ti", "tus", "ellas", "nosotras",
    "vosotros", "vosotras", "os", "suyo", "suya", "nuestro", "nuestra",
    "nuestros", "nuestras", "esos", "esas", "estoy", "estamos", "estan",
    "soy", "eres", "somos", "sois", "son", "sea", "he", "has", "ha",
    "hemos", "han", "habia", "habian", "sera", "seran", "tengo", "tienes",
    "tiene", "tenemos", "tienen", "hacer", "hago", "haces", "hace",
    "hacemos", "hacen", "hola", "mundo", "gracias", "adios", "amor",
    "vida", "tiempo", "casa", "agua", "dia", "noche", "sol", "luna",
    "ataque", "amanecer", "confirmado", "verdad", "mensaje", "secreto",
    "bien", "mal", "grande", "bueno", "malo", "nuevo", "viejo", "hombre",
    "mujer", "amigo", "familia", "trabajo", "ver", "dar", "ir", "voy",
    "va", "vamos", "saber", "querer", "quiero", "poder", "puede", "pueden",
    "decir", "dice", "aqui", "alli", "hoy", "ayer", "manana", "cada",
    "parte", "forma", "despues", "misma", "mismo", "fue", "era",
}

PESOS_PREFIJOS = {
    "des": 1.20, "pre": 1.00, "re": 0.70, "in": 0.70, "con": 1.00,
    "com": 1.00, "pro": 0.90, "sub": 0.90, "inter": 1.20, "anti": 1.00,
}

PESOS_SUFIJOS = {
    "mente": 2.00, "cion": 2.00, "ciones": 2.50, "idad": 1.60,
    "idades": 2.00, "ando": 1.40, "iendo": 1.40, "ado": 1.00, "ada": 1.00,
    "idos": 1.00, "idas": 1.00, "oso": 1.00, "osa": 1.00, "able": 1.20,
    "ible": 1.20, "ar": 0.50, "er": 0.50, "ir": 0.50,
}

PESOS_SECUENCIAS_IMPROBABLES = {
    "jj": 2.00, "kk": 2.00, "ww": 2.00, "qq": 2.50, "zx": 2.50, "xq": 2.50,
    "qz": 2.50, "jq": 2.50, "qj": 2.50, "kq": 2.50, "qx": 2.50, "wq": 2.50,
    "wx": 2.00, "gx": 1.50, "ññ": 1.50,
}

LONGITUD_PALABRA_MAX_RAZONABLE = 18


def SF8(texto):
    return texto.lower().translate(TABLA_ACENTOS)


def SF9(texto_normalizado):
    return PATRON_PALABRA.findall(texto_normalizado)


def SF10(texto_normalizado):
    conteo = Counter(c for c in texto_normalizado if c in LETRAS_ESPANOL)
    for letra in LETRAS_ESPANOL:
        conteo.setdefault(letra, 0)
    return conteo


def SF11(texto_normalizado, n):
    contador = Counter()
    for indice in range(len(texto_normalizado) - n + 1):
        fragmento = texto_normalizado[indice:indice + n]
        if all(caracter in LETRAS_ESPANOL for caracter in fragmento):
            contador[fragmento] += 1
    return contador


def SF12(texto_normalizado, n, peso_maximo, minimo_apariciones):
    conteo = SF11(texto_normalizado, n)
    maximo = max(conteo.values(), default=1)
    return {
        ngrama: round((veces / maximo) * peso_maximo, 2)
        for ngrama, veces in conteo.items()
        if veces >= minimo_apariciones
    }


_CORPUS_NORMALIZADO = SF8(CORPUS_REFERENCIA)
_PALABRAS_CORPUS = set(SF9(_CORPUS_NORMALIZADO))

_CONTEO_LETRAS_CORPUS = SF10(_CORPUS_NORMALIZADO)
_TOTAL_LETRAS_CORPUS = sum(_CONTEO_LETRAS_CORPUS.values())
FRECUENCIA_LETRAS = {
    letra: (veces / _TOTAL_LETRAS_CORPUS) * 100
    for letra, veces in _CONTEO_LETRAS_CORPUS.items()
}

_TOTAL_VOCALES_CORPUS = sum(
    veces for letra, veces in _CONTEO_LETRAS_CORPUS.items() if letra in VOCALES
)
RATIO_VOCALES_OBJETIVO = round(_TOTAL_VOCALES_CORPUS / _TOTAL_LETRAS_CORPUS, 2)
RATIO_VOCALES_MIN = round(RATIO_VOCALES_OBJETIVO - 0.20, 2)
RATIO_VOCALES_MAX = round(RATIO_VOCALES_OBJETIVO + 0.20, 2)

PESOS_BIGRAMAS = SF12(_CORPUS_NORMALIZADO, 2, 1.20, 4)
PESOS_TRIGRAMAS = SF12(_CORPUS_NORMALIZADO, 3, 1.80, 3)
PESOS_TETRAGRAMAS = SF12(_CORPUS_NORMALIZADO, 4, 2.20, 2)

PALABRAS_COMUNES = PALABRAS_COMUNES_BASE | _PALABRAS_CORPUS
