import re

TABLA_ACENTOS = str.maketrans("áéíóúÁÉÍÓÚüÜ", "aeiouAEIOUuU")

LETRAS_ESPANOL = set("abcdefghijklmnñopqrstuvwxyz")
VOCALES = set("aeiouáéíóúü")

PATRON_PALABRA = re.compile(r"[a-zñ]+")

FRECUENCIA_LETRAS = {
    "a": 12.53, "b": 1.42, "c": 4.68, "d": 5.86, "e": 13.68, "f": 0.69,
    "g": 1.01, "h": 0.70, "i": 6.25, "j": 0.44, "k": 0.02, "l": 4.97,
    "m": 3.15, "n": 6.71, "ñ": 0.31, "o": 8.68, "p": 2.51, "q": 0.88,
    "r": 6.87, "s": 7.98, "t": 4.63, "u": 3.93, "v": 0.90, "w": 0.01,
    "x": 0.22, "y": 0.90, "z": 0.52,
}

PALABRAS_MUY_COMUNES = {
    "de", "la", "que", "el", "en", "y", "a", "los", "se", "del", "las",
    "por", "un", "para", "con", "no", "una", "su", "al", "lo", "es", "si",
}

PALABRAS_COMUNES = {
    "como", "mas", "pero", "sus", "le", "ya", "o", "este", "porque",
    "esta", "entre", "cuando", "muy", "sin", "sobre", "tambien", "me",
    "hasta", "hay", "donde", "quien", "desde", "todo", "nos", "durante",
    "todos", "uno", "les", "ni", "contra", "otros", "ese", "eso", "ante",
    "ellos", "esto", "antes", "algunos", "unos", "yo", "otro", "otras",
    "otra", "tanto", "esa", "estos", "mucho", "quienes", "nada", "muchos",
    "cual", "poco", "ella", "estar", "estas", "algunas", "algo",
    "nosotros", "mi", "mis", "tu", "te", "tus", "ellas", "cada", "bien",
    "puede", "pueden", "hacer", "tiene", "tienen", "ser", "son", "fue",
    "era", "han", "ha", "sea", "solo", "parte", "tiempo", "forma",
    "despues", "nuevo", "misma", "mismo",
    "hola", "adios", "gracias", "amor", "perro", "gato", "agua", "sol",
    "luna", "paz", "vida", "mal", "hoy", "aqui", "alli", "ahi", "familia",
    "mesa", "libro", "noche", "dia", "dias", "cielo", "tierra", "fuego",
    "aire", "mar", "rio", "flor", "flores", "arbol", "arboles", "niño",
    "niña", "niños", "niñas", "hombre", "hombres", "mujer", "mujeres",
    "amigo", "amiga", "amigos", "escuela", "trabajo", "mexico", "casa",
    "gente", "mundo", "mano", "manos", "ojo", "ojos", "pais", "gobierno",
    "problema", "momento", "persona", "personas", "manera", "historia",
    "lugar", "sistema", "programa", "empresa", "grupo", "nombre",
    "numero", "punto", "caso", "ejemplo", "estado", "ciudad", "nivel",
    "area", "proceso", "servicio", "proyecto", "resultado", "relacion",
    "medio", "razon", "tipo", "hecho", "palabra", "palabras", "cosa",
    "cosas", "dato", "valor", "cambio", "poder", "cuerpo", "espacio",
    "efecto", "calidad", "precio", "salud", "arte", "papel", "puerta",
    "ventana", "calle", "pueblo", "mercado", "dinero", "negocio",
    "internet", "musica", "cancion", "juego", "deporte", "equipo",
    "clase", "curso", "profesor", "alumno", "idea", "ideas", "ley",
    "leyes", "derecho", "libertad", "padre", "madre", "hijo", "hija",
    "hermano", "hermana", "abuelo", "abuela", "esposo", "esposa",
    "vecino", "hogar", "jardin", "edificio", "barrio", "nacion",
    "comida", "pan", "carne", "pescado", "fruta", "leche", "huevo",
    "arroz", "ropa", "zapato", "reloj", "coche", "carro", "auto",
    "avion", "camino", "puente", "grande", "pequeno", "pequena",
    "bueno", "buena", "malo", "mala", "viejo", "vieja", "importante",
    "mayor", "menor", "alto", "alta", "bajo", "baja", "diferente",
    "mejor", "peor", "primero", "primera", "segundo", "segunda",
    "ultimo", "ultima", "siguiente", "claro", "clara", "cierto",
    "cierta", "facil", "dificil", "largo", "larga", "corto", "corta",
    "joven", "feliz", "triste", "fuerte", "debil", "rico", "pobre",
    "rapido", "lento", "seguro", "segura", "limpio", "sucio",
    "caliente", "frio", "fria", "siempre",
    "nunca", "tampoco", "ahora", "luego", "entonces", "casi", "aun",
    "todavia", "incluso", "ademas", "realmente", "verdad", "manana",
    "ayer", "temprano", "tarde", "pronto", "cerca", "lejos", "dentro",
    "fuera", "arriba", "abajo", "adelante", "atras", "dos", "tres",
    "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez",
    "quiero", "puedo", "debo", "voy", "vamos", "vengo", "veo", "digo",
    "dice", "sabe", "sabes", "gusta", "gustan", "creo", "pienso",
    "siento", "vivo", "vive", "viven", "trabajo", "trabaja", "estudio",
    "estudia", "juega", "come", "bebe", "duerme", "camina", "corre",
    "llega", "sale", "entra", "busca", "encuentra", "necesito",
    "necesita",
    "pajaro", "pajaros", "vaca", "caballo", "conejo", "pato", "pollo",
    "raton", "oso", "leon", "tigre", "elefante", "mono", "oveja",
    "cerdo", "burro", "ganso", "aguila", "serpiente", "rana", "abeja",
    "mosca", "hormiga", "araña", "mariposa", "pez", "peces", "tortuga",
    "delfin", "ballena", "tiburon", "cabra", "lobo", "zorro", "ardilla",
    "monte", "bosque", "selva", "valle", "playa", "isla", "desierto",
    "nube", "nubes", "lluvia", "nieve", "viento", "piedra", "arena",
    "estrella", "estrellas", "planeta", "verano", "invierno", "otoño",
    "primavera", "clima", "cuerpo", "cabeza", "cara", "boca", "nariz",
    "oreja", "brazo", "pierna", "pie", "pies", "dedo", "corazon",
    "sangre", "piel", "hueso", "cerebro", "cuarto", "cocina", "baño",
    "cama", "silla", "techo", "pared", "piso", "patio", "ciudad",
    "region", "pais", "campo", "granja",
    "bicicleta", "avion", "tren", "barco", "camion", "autobus",
    "carretera", "esquina", "semaforo", "tienda", "hospital", "iglesia",
    "parque", "cine", "teatro", "hotel", "banco", "oficina", "fabrica",
    "reloj", "telefono", "camara", "television", "radio", "periodico",
    "revista", "carta", "sobre", "regalo", "fiesta", "cumpleaños",
    "boda", "viaje", "vacaciones", "montaña", "montañas", "risa", "llanto",
    "sueño", "sueños", "miedo", "alegria", "tristeza", "enojo",
    "sorpresa", "esperanza", "abrazo", "beso", "saludo", "adios",
    "buenos", "dias", "tardes", "noches", "gracias", "perdon", "favor",
    "quiere", "quieren", "puedes", "puede", "sabemos", "vemos",
    "vamos", "vienen", "viene", "hacemos", "hago", "decimos", "hablo",
    "habla", "hablan", "escribo", "escribe", "escriben", "leo", "lee",
    "leen", "abre", "cierra", "compra", "vende", "paga", "cuesta",
    "ayuda", "ayudan", "espera", "piensa", "piensan", "recuerda",
    "olvida", "aprende", "enseña", "escucha", "mira", "canta", "baila",
    "pinta", "dibuja", "construye", "rompe", "arregla", "limpia",
    "cocina", "prepara",
}

PESOS_BIGRAMAS = {
    "de": 1.20, "en": 1.10, "es": 1.00, "la": 1.00, "el": 1.00, "si": 1.00,
    "qu": 1.20,
    "ue": 1.00, "os": 0.80, "as": 0.80, "ar": 0.75, "er": 0.75, "ir": 0.70,
    "ra": 0.70, "re": 0.70, "on": 0.70, "ci": 0.65, "co": 0.65, "nt": 0.65,
    "te": 0.65, "do": 0.60, "ad": 0.60, "se": 0.60, "an": 0.60, "or": 0.60,
    "al": 0.60, "ma": 0.55, "ta": 0.55, "na": 0.55, "ro": 0.55, "da": 0.55,
    "io": 0.80,
}

PESOS_TRIGRAMAS = {
    "que": 2.50, "ent": 1.50, "est": 1.50, "con": 1.50, "del": 1.50,
    "los": 1.40, "las": 1.40, "por": 1.30, "una": 1.30, "ado": 1.20,
    "ido": 1.20, "ion": 1.20, "cio": 1.50, "ara": 1.00, "nte": 1.00,
    "sta": 1.00, "era": 1.00, "ien": 1.00, "res": 1.00, "des": 1.00,
    "aci": 1.00, "tos": 0.90, "dad": 0.90, "men": 0.90,
}

PESOS_TETRAGRAMAS = {
    "cion": 2.20, "esta": 1.80, "para": 1.80, "ente": 1.70, "ando": 1.60,
    "iend": 1.60, "acio": 2.00, "mien": 1.40, "idad": 1.40, "todo": 1.20,
    "como": 1.20, "pero": 1.20, "tien": 1.20,
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

RATIO_VOCALES_MIN = 0.25
RATIO_VOCALES_OBJETIVO = 0.45
RATIO_VOCALES_MAX = 0.65

LONGITUD_PALABRA_MAX_RAZONABLE = 18


def SF7(texto):
    return texto.lower().translate(TABLA_ACENTOS)


def SF8(texto_normalizado):
    return PATRON_PALABRA.findall(texto_normalizado)
