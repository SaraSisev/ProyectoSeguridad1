TABLA_ACENTOS = str.maketrans("áéíóúÁÉÍÓÚüÜ", "aeiouAEIOUuU")

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


def SF8(texto):
    return texto.translate(TABLA_ACENTOS)


def SF9(texto):
    limpio = SF8(texto).lower()
    conteo = {chr(codigo): 0 for codigo in range(ord("a"), ord("z") + 1)}
    conteo["ñ"] = 0
    total = 0
    for caracter in limpio:
        if caracter in conteo:
            conteo[caracter] += 1
            total += 1
    return conteo, total


_CONTEO_CORPUS, _TOTAL_CORPUS = SF9(CORPUS_REFERENCIA)
FREC_ESPANOL = {
    letra: (veces / _TOTAL_CORPUS) * 100
    for letra, veces in _CONTEO_CORPUS.items()
}


def SF10(texto):
    conteo, total = SF9(texto)
    if total == 0:
        return float("inf")
    chi_cuadrado = 0.0
    for letra, frecuencia_esperada in FREC_ESPANOL.items():
        esperado = total * (frecuencia_esperada / 100)
        observado = conteo[letra]
        if esperado > 0:
            chi_cuadrado += ((observado - esperado) ** 2) / esperado
    return chi_cuadrado


def SF11(texto):
    limpio = SF8(texto).upper()
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
