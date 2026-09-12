# Documentación de funciones (identificadores SF)

Este documento es la única fuente de explicación del comportamiento interno del sistema.
En el código fuente del backend (`backend/src/*.py`) y del frontend (`front/main.js`) las
funciones no llevan comentarios descriptivos: cada una está identificada únicamente con un
código `SFx`, **único en todo el proyecto** (no se repite entre archivos). Este documento
describe, para cada identificador, qué hace, qué parámetros recibe, dónde está ubicado y cómo
funciona internamente.

## Organización del backend

El backend está dividido en un archivo por responsabilidad, sin más archivos de los
necesarios:

```
backend/src/
  alfabeto.py             -> validación del alfabeto y utilidades de índices/desplazamiento
  cifrado.py               -> las dos operaciones de cifrado: César y Atbash
  descifrado.py            -> César inverso + la autodetección automática (orquesta todo)
  analisis_frecuencia.py   -> el motor de Al-Kindi: corpus propio, diccionario, puntuación
  entry.py                 -> punto de entrada del Worker de Cloudflare (rutas HTTP, CORS)
```

`alfabeto.py`, `cifrado.py`, `descifrado.py` y `analisis_frecuencia.py` son Python puro (sin
dependencias del runtime de Cloudflare), por lo que pueden importarse y probarse de forma
aislada. Solo `entry.py` depende del módulo `workers`, propio de Cloudflare.

## Fundamento criptográfico (Al-Kindi)

El descifrado automático (sin intervención humana) se basa en el **análisis de frecuencias**,
técnica de criptoanálisis descrita por primera vez por **Abū Yūsuf Ya'qūb ibn Isḥāq al-Kindī**
(أبو يوسف يعقوب بن إسحاق الكندي) en su tratado *Risāla fī Istikhrāj al-Muʿammā* (siglo IX). El
método combina dos ingredientes, tal como los describía Al-Kindi: (1) qué tan frecuente es
cada carácter en el idioma, y (2) el conocimiento del propio idioma (qué es una palabra real).
Aquí eso se traduce en un **diccionario** de palabras españolas (`DICCIONARIO`, en
`analisis_frecuencia.py`) combinado con la frecuencia de cada letra (`FREC_ESPANOL`, calculada
—no copiada— a partir de un corpus de texto escrito para este proyecto).

El sistema **descifra el texto con las 26 claves posibles** (Atbash + los 25 desplazamientos
César), calcula un **único puntaje numérico** para cada una de las 26 soluciones candidatas
(`SF13`), y se queda con la que obtiene el **valor más alto** (`max(candidatos, key=...)` en
`SF7`). No hay desempates artificiales ni reglas en cascada: es un solo número por candidato y
gana el mayor, exactamente como debe funcionar un criptoanálisis por frecuencias.

### Cómo se calcula el puntaje de cada candidato

`puntaje_total (SF13) = puntaje_por_frecuencia_de_caracteres (SF11) + puntaje_por_diccionario (SF12)`

- **SF11 — frecuencia de caracteres:** cada letra del candidato aporta un peso igual a su
  frecuencia estadística en español (`FREC_ESPANOL`); se promedia entre todas las letras del
  candidato. Un candidato compuesto por letras poco comunes en español (por ejemplo, muchas
  "k", "w" o "x") obtiene un promedio bajo; uno con la mezcla típica del español (mucha "a",
  "e", "o", "s", "n"...) obtiene un promedio alto.
- **SF12 — coincidencia con el diccionario:** se separa el candidato en palabras (cortando en
  cualquier carácter no alfabético) y se suma la longitud de cada palabra de 2 o más letras
  que exista en `DICCIONARIO`. Una palabra larga reconocida (por ejemplo "AMANECER") pesa
  mucho más que una corta ("LA"), porque es prácticamente imposible que una palabra larga
  aparezca por pura casualidad en un candidato incorrecto.

Ambos números se sencillamente **suman**: cuando el candidato contiene palabras reales, el
término del diccionario domina el resultado (es la señal más fuerte); cuando no se reconoce
ninguna palabra (textos muy genéricos o con vocabulario fuera del diccionario), el desempate lo
resuelve la frecuencia de caracteres. Por diseño, solo se le muestra al usuario la línea
descifrada ganadora: el usuario nunca elige entre candidatos.

### El diccionario (`DICCIONARIO`)

No es una lista copiada de internet: se construye combinando dos fuentes propias del proyecto,
ambas dentro de `analisis_frecuencia.py`:

1. `PALABRAS_BASE`: un conjunto escrito a mano con las palabras gramaticales más frecuentes del
   español (artículos, preposiciones, pronombres, verbos auxiliares muy comunes, saludos).
2. Todas las palabras que aparecen realmente en `CORPUS_REFERENCIA` (extraídas con `SF10`),
   el mismo texto en español escrito para este proyecto que también sirve para calcular
   `FREC_ESPANOL`. Esto añade automáticamente sustantivos y verbos de vocabulario cotidiano
   (familia, comida, tecnología, naturaleza, ciudad, deporte, historia, etc.) sin tener que
   escribirlos dos veces ni copiar un diccionario externo.

`DICCIONARIO = PALABRAS_BASE | palabras_extraidas_del_corpus` termina con más de 400 palabras.

### Límite honesto del método (léelo si algo "no acierta")

El análisis de frecuencias necesita que una parte razonable del mensaje haya sido realmente
sustituida por el cifrado. Si el alfabeto que el usuario define **no incluye** las letras
españolas comunes que aparecen en su texto (por ejemplo, un alfabeto compuesto casi
enteramente de símbolos poco frecuentes, jeroglíficos u otros alfabetos, con solo un puñado de
letras latinas), la mayor parte del mensaje pasa sin cifrar (tal como exige el enunciado: los
caracteres fuera del alfabeto se "pasan por alto"). Con muy pocos caracteres realmente
cifrados, **ningún método automático — ni tampoco un humano —** puede garantizar recuperar la
clave real entre las 26 hipótesis posibles: varias claves distintas pueden producir, por pura
coincidencia, texto que parece español válido. Esto no es un error de la implementación, es
una limitación matemática del criptoanálisis por frecuencias con muestras pequeñas. Para
resultados fiables, el alfabeto debe incluir las letras del español que realmente se van a
usar en el texto a cifrar.

---

## `backend/src/alfabeto.py`

### Constantes
- `LIMITE_ALFABETO = 256`: número máximo de caracteres distintos permitidos en el alfabeto.
  El frontend usa exactamente el mismo número (constante `LIMITE_ALFABETO` en `main.js`,
  atributo `maxlength="256"` en el campo de alfabeto) para que ambos lados estén siempre de
  acuerdo.
- `DESPLAZAMIENTO_MIN = 1`, `DESPLAZAMIENTO_MAX = 25`: rango permitido para el desplazamiento
  César. También coincide exactamente con los atributos `min="1"` / `max="25"` del campo de
  desplazamiento en `front/index.html` y con los límites del stepper (`SF26`).

### SF1
- **Parámetros:** `alfabeto` (str) — el conjunto de caracteres que el usuario quiere usar.
- **Ubicación:** `backend/src/alfabeto.py`.
- **Qué hace:** valida que el alfabeto sea utilizable: que sea una cadena no vacía, que no
  supere `LIMITE_ALFABETO` (256) caracteres, que no tenga caracteres repetidos y que tenga al
  menos 2 caracteres distintos (mínimo necesario para que un desplazamiento tenga efecto).
- **Cómo lo hace:** convierte la cadena en lista de caracteres Unicode (cada carácter, sin
  importar si es ASCII, chino, árabe, un jeroglífico, etc., cuenta como un solo elemento
  porque Python 3 itera cadenas por punto de código completo, no por bytes ni por unidades
  UTF-16) y compara `len(lista)` contra `len(set(lista))` para detectar duplicados.
- **Devuelve:** tupla `(valido: bool, mensaje_error: str)`.
- **Quién la usa:** `SF17`, `SF18`, `SF19` (en `entry.py`) antes de cualquier operación de
  cifrado/descifrado.

### SF2
- **Parámetros:** `alfabeto` (str).
- **Ubicación:** `backend/src/alfabeto.py`.
- **Qué hace:** construye el mapa `carácter -> posición` dentro del alfabeto (posición 0 a
  `len(alfabeto)-1`).
- **Cómo lo hace:** comprensión de diccionario sobre `enumerate(alfabeto)`.
- **Quién la usa:** `SF4`, `SF5` (en `cifrado.py`) y `SF6` (en `descifrado.py`) para saber en
  qué posición está cada carácter antes de desplazarlo o invertirlo.

### SF3
- **Parámetros:** `desplazamiento` (int, 1-25), `longitud_alfabeto` (int).
- **Ubicación:** `backend/src/alfabeto.py`.
- **Qué hace:** valida que el desplazamiento sea un entero dentro del rango permitido
  (1 a 25, tal como exige el proyecto) y lo normaliza al tamaño real del alfabeto mediante
  módulo, para que el índice resultante nunca se salga de rango.
- **Cómo lo hace:** `desplazamiento % longitud_alfabeto`.
- **Lanza:** `ValueError` con mensaje en español si el valor no es un entero válido o está
  fuera de 1-25.
- **Quién la usa:** `SF4` (en `cifrado.py`) y `SF6` (en `descifrado.py`).

---

## `backend/src/cifrado.py`

Importa `SF2` y `SF3` de `alfabeto.py`.

### SF4 (César — cifrar)
- **Parámetros:** `texto` (str, texto plano en español), `alfabeto` (str), `desplazamiento`
  (int, 1-25).
- **Ubicación:** `backend/src/cifrado.py`.
- **Qué hace:** cifra `texto` con César sobre el alfabeto dado.
- **Cómo lo hace:** para cada carácter del texto, si está dentro del alfabeto (según el mapa
  de `SF2`) se reemplaza por el carácter que está `desplazamiento` posiciones adelante (con
  vuelta cíclica, `% len(alfabeto)`); si el carácter **no** está en el alfabeto (espacios,
  puntuación no incluida, letras no incluidas, etc.) se deja exactamente igual — se "pasa por
  alto", tal como pide el enunciado.
- **Devuelve:** el texto cifrado (str).
- **Quién la usa:** `SF18` en `entry.py` cuando el usuario elige el método "CESAR".

### SF5 (Atbash — cifra y descifra, es autoinverso)
- **Parámetros:** `texto` (str), `alfabeto` (str).
- **Ubicación:** `backend/src/cifrado.py`.
- **Qué hace:** aplica la transformación Atbash: cada carácter se reemplaza por el que ocupa
  la posición simétrica del alfabeto (`longitud - 1 - posición`). Al ser una involución
  (aplicarla dos veces devuelve el texto original), la misma función sirve para cifrar y para
  descifrar; no existe una función Atbash separada en `descifrado.py` porque sería código
  duplicado.
- **Quién la usa:** `SF18` en `entry.py` cuando el usuario elige "ATBASH" para cifrar, y
  `SF7` en `descifrado.py`, que la importa para generar el candidato Atbash durante la
  autodetección.

---

## `backend/src/descifrado.py`

Importa `SF2`, `SF3` y las constantes de `alfabeto.py`; importa `SF5` de `cifrado.py`; importa
`SF13` de `analisis_frecuencia.py`.

### SF6 (César — descifrar)
- **Parámetros:** `texto` (str), `alfabeto` (str), `desplazamiento` (int, 1-25).
- **Ubicación:** `backend/src/descifrado.py`.
- **Qué hace:** operación inversa de `SF4`: resta el desplazamiento en vez de sumarlo (mismo
  criterio de "pasar por alto" los caracteres fuera del alfabeto).
- **Quién la usa:** `SF7`, que la invoca 25 veces (una por cada desplazamiento posible) para
  generar los candidatos que luego se puntúan con `SF13`.

### SF7 (autodetección — el "cerebro" de Al-Kindi)
- **Parámetros:** `texto_cifrado` (str), `alfabeto` (str).
- **Ubicación:** `backend/src/descifrado.py`.
- **Qué hace:** implementa la autodetección exigida por el proyecto: sin ninguna intervención
  humana, determina si el texto fue cifrado con Atbash o con César (y con qué desplazamiento).
- **Cómo lo hace:**
  1. Genera el candidato de descifrado Atbash con `SF5` (de `cifrado.py`).
  2. Genera los 25 candidatos de descifrado César (desplazamientos 1 a 25) con `SF6`.
  3. Calcula el puntaje único combinado (`SF13`, de `analisis_frecuencia.py`) de cada uno de
     los 26 candidatos.
  4. Elige el candidato con el puntaje **más alto**: `max(candidatos, key=lambda c:
     c["puntaje"])`. Un solo número, gana el mayor — sin reglas de desempate en cascada.
- **Devuelve:** diccionario `{"metodo": "ATBASH"|"CESAR", "desplazamiento": int|None,
  "texto": str, "puntaje": float}`.
- **Quién la usa:** `SF19` (en `entry.py`). Solo el resultado de esta función se le muestra al
  usuario — es la única línea "correcta" que exige el enunciado.

---

## `backend/src/analisis_frecuencia.py`

El motor de Al-Kindi. No depende de ningún otro archivo del proyecto.

### `CORPUS_REFERENCIA` (constante, no es función)
Texto en español de varios párrafos, **escrito específicamente para este proyecto** (no
copiado de ninguna fuente externa), usado para derivar empíricamente la frecuencia de cada
letra — el mismo principio que usó Al-Kindi: analizar texto real en vez de citar una tabla.
Se escribió con vocabulario variado a propósito para que aparezcan también las letras menos
frecuentes del español (`k`, `w`, `x`, `z`, `j`, `ñ`, `q`, etc.) y para nutrir el diccionario
(ver `DICCIONARIO` más abajo) con sustantivos y verbos reales, no solo palabras gramaticales.

### `PALABRAS_BASE` (constante, no es función)
Conjunto escrito a mano con las palabras gramaticales más frecuentes del español (artículos,
preposiciones, pronombres, verbos auxiliares comunes, saludos, sin tildes y en mayúsculas).
Es la mitad "manual" del diccionario; la otra mitad se extrae automáticamente del corpus
(ver `SF10` y `DICCIONARIO`).

### SF8
- **Parámetros:** `texto` (str).
- **Ubicación:** `backend/src/analisis_frecuencia.py`.
- **Qué hace:** normaliza vocales acentuadas a su forma base (á→a, é→e, í→i, ó→o, ú→u, ü→u,
  incluyendo mayúsculas) usando una tabla de traducción (`TABLA_ACENTOS`). **No** afecta la
  letra `ñ` (se preserva tal cual porque es una letra distinta en el alfabeto español, con su
  propia frecuencia).
- **Por qué existe:** el análisis debe contar "e" y "é" como la misma letra estadística, y
  reconocer "CAMPESINO" y "CAMPESINO" (con o sin tilde) como la misma palabra del diccionario;
  esta función solo se usa para esa normalización interna, nunca para el texto que finalmente
  se le muestra al usuario.
- **Quién la usa:** `SF9`, `SF10`.

### SF9
- **Parámetros:** `texto` (str).
- **Ubicación:** `backend/src/analisis_frecuencia.py`.
- **Qué hace:** cuenta cuántas veces aparece cada letra española (a-z, ñ) en el texto.
- **Cómo lo hace:** pasa el texto por `SF8` (quita tildes de vocales) y lo pone en
  minúsculas; recorre carácter por carácter y, si el carácter es una de las 27 letras del
  español, incrementa su contador y el total.
- **Devuelve:** tupla `(conteo: dict[letra, int], total: int)`.
- **Quién la usa:** se llama una vez sobre `CORPUS_REFERENCIA` al importar el módulo (para
  calcular `FREC_ESPANOL`) y luego se reutiliza dentro de `SF11` para analizar cada candidato
  de descifrado.

### SF10
- **Parámetros:** `texto` (str).
- **Ubicación:** `backend/src/analisis_frecuencia.py`.
- **Qué hace:** separa el texto en palabras.
- **Cómo lo hace:** pasa el texto por `SF8` y lo pone en mayúsculas; recorre carácter por
  carácter agrupando letras consecutivas en una palabra; cualquier carácter no alfabético
  (espacio, coma, símbolo fuera del alfabeto, dígito, etc.) cierra la palabra actual y
  comienza una nueva.
- **Devuelve:** lista de palabras (str, en mayúsculas, sin tildes en vocales).
- **Quién la usa:** se llama una vez sobre `CORPUS_REFERENCIA` al importar el módulo (para
  construir `DICCIONARIO`) y luego se reutiliza dentro de `SF12` para analizar cada candidato
  de descifrado.

### `FREC_ESPANOL` (constante calculada, no hardcodeada)
Justo después de definir `SF9`, el módulo la ejecuta una vez sobre `CORPUS_REFERENCIA` y
convierte los conteos en porcentajes: `FREC_ESPANOL = {letra: (veces/total)*100 ...}`. Al
calcularse en código a partir de un texto propio, no reproduce ninguna tabla de una fuente
externa.

### `DICCIONARIO` (constante calculada)
`DICCIONARIO = PALABRAS_BASE | set(SF10(CORPUS_REFERENCIA))`: une las palabras gramaticales
escritas a mano con todas las palabras distintas que aparecen en el corpus propio. Resultado:
más de 400 palabras españolas reales (artículos, verbos, sustantivos de vocabulario cotidiano)
sin copiar ningún diccionario externo.

### SF11 (puntaje por frecuencia de caracteres)
- **Parámetros:** `texto` (str) — un candidato de texto descifrado.
- **Ubicación:** `backend/src/analisis_frecuencia.py`.
- **Qué hace:** calcula qué tan "española" es la mezcla de letras del candidato, en un único
  número que **hay que maximizar** (a diferencia de una distancia estadística, que se
  minimizaría).
- **Cómo lo hace:** cuenta las letras del texto con `SF9`; a cada letra observada le asigna
  como peso su frecuencia en `FREC_ESPANOL`, suma esos pesos y divide entre el total de letras
  contadas (promedio). Un candidato con muchas vocales y consonantes comunes del español
  (a, e, o, s, n, r...) obtiene un promedio alto; uno dominado por letras raras en español
  obtiene un promedio bajo.
- **Caso especial:** si el texto no contiene ninguna letra española reconocible (`total == 0`),
  devuelve `0.0` (neutral: ni ayuda ni perjudica al candidato).
- **Quién la usa:** `SF13`.

### SF12 (puntaje por diccionario)
- **Parámetros:** `texto` (str) — un candidato de texto descifrado.
- **Ubicación:** `backend/src/analisis_frecuencia.py`.
- **Por qué existe:** el promedio de frecuencia de `SF11` es fiable con textos largos, pero
  con textos o palabras muy cortas la estadística tiene demasiado poco material y puede
  equivocarse por azar. Reconocer palabras reales del diccionario es una señal mucho más
  fuerte, incluso con una sola palabra.
- **Cómo lo hace:** separa el texto en palabras con `SF10` y suma la **longitud** de cada
  palabra de 2 o más letras que aparezca en `DICCIONARIO` (las palabras de una sola letra no
  se cuentan porque podrían coincidir por puro azar, y se pondera por longitud para que una
  coincidencia larga —p. ej. "AMANECER"— pese mucho más que una corta y sea prácticamente
  imposible que ocurra por casualidad en un candidato equivocado).
- **Devuelve:** un entero (0 si no reconoce ninguna palabra del diccionario).
- **Quién la usa:** `SF13`.

### SF13 (puntaje total — el número que decide todo)
- **Parámetros:** `texto` (str) — un candidato de texto descifrado.
- **Ubicación:** `backend/src/analisis_frecuencia.py`.
- **Qué hace:** suma `SF11(texto) + SF12(texto)` en un único valor.
- **Por qué así:** el enunciado del usuario pedía exactamente esto — probar todas las
  soluciones posibles y quedarse con la de **mayor valor**. Al ser una sola suma, `SF7` puede
  usar `max()` directamente sobre los 26 candidatos sin reglas de desempate adicionales.
- **Quién la usa:** `SF7` (en `descifrado.py`), para comparar los 26 candidatos posibles.

---

## `backend/src/entry.py`

Punto de entrada del *Cloudflare Worker* (Python). Depende del módulo `workers`, propio del
runtime de Cloudflare, por lo que no se puede importar ni probar fuera de ese entorno; toda la
lógica de negocio vive en los cuatro archivos anteriores, precisamente para poder probarla de
forma aislada.

### SF14
- **Parámetros:** ninguno.
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** devuelve el diccionario de cabeceras CORS (`access-control-allow-origin: *`,
  métodos y headers permitidos) que se agrega a **todas** las respuestas, ya que el frontend
  (GitHub Pages) y el backend (Cloudflare Workers) viven en dominios distintos.

### SF15
- **Parámetros:** `datos` (dict, serializable a JSON), `estado` (int, código HTTP,
  por defecto 200).
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** construye la respuesta HTTP final: serializa `datos` a JSON con
  `ensure_ascii=False` (para que caracteres especiales como chino/árabe/jeroglíficos/acentos
  viajen tal cual, en UTF-8, y no como secuencias de escape), añade las cabeceras CORS de
  `SF14` más `content-type: application/json; charset=utf-8`, y arma el objeto `Response` que
  exige el runtime de Cloudflare.

### SF16
- **Parámetros:** `request` (objeto `Request` del runtime de Cloudflare).
- **Ubicación:** `backend/src/entry.py`. Función asíncrona.
- **Qué hace:** lee el cuerpo de la petición HTTP como texto (`await request.text()`) y lo
  interpreta como JSON. Si el cuerpo viene vacío devuelve un diccionario vacío en lugar de
  fallar.

### SF17
- **Parámetros:** `payload` (dict) — se espera la clave `alfabeto`.
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** implementa la ruta `POST /api/alfabeto/validar`. Llama a `SF1` (de
  `alfabeto.py`) y traduce el resultado a la forma de respuesta HTTP: `({"valido": True,
  "longitud": N}, 200)` o `({"valido": False, "error": "..."}, 400)`.

### SF18
- **Parámetros:** `payload` (dict) — espera `alfabeto`, `metodo` ("CESAR"|"ATBASH"), `texto`
  y, si el método es César, `desplazamiento`.
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** implementa la ruta `POST /api/cifrar`. Valida el alfabeto (`SF1`) y el texto,
  y según el método invoca `SF5` (Atbash, de `cifrado.py`) o `SF4` (César, de `cifrado.py`,
  validando además que el desplazamiento sea un entero entre 1 y 25). Es el único lugar del
  sistema donde el usuario elige explícitamente el método/módulo de cifrado, tal como exige
  el enunciado.

### SF19
- **Parámetros:** `payload` (dict) — espera `alfabeto` y `texto` (el texto cifrado).
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** implementa la ruta `POST /api/descifrar`. Valida el alfabeto y el texto, y
  delega toda la decisión a `SF7` (de `descifrado.py`, motor de autodetección de Al-Kindi).
  Devuelve el método detectado, el desplazamiento (o `None` si fue Atbash) y el texto
  resultante. El usuario no interviene en ningún punto de esta función.

### `on_fetch` (nombre reservado, no forma parte de la numeración SF)
- **Parámetros:** `request`, `env`, `ctx` (firma exigida por el runtime de Cloudflare
  Workers; el nombre `on_fetch` es obligatorio y no puede renombrarse sin romper el
  despliegue).
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** único punto de entrada HTTP del Worker. Responde `204` con cabeceras CORS
  ante peticiones `OPTIONS` (pre-flight del navegador); enruta `POST /api/alfabeto/validar`
  a `SF17`, `POST /api/cifrar` a `SF18` y `POST /api/descifrar` a `SF19`; cualquier otra
  ruta/método devuelve `404` mediante `SF15`.

---

## `front/main.js`

Lógica de interfaz. Consume la API del backend mediante `fetch`. No contiene lógica
criptográfica: todo el cifrado/descifrado/autodetección ocurre en el backend.

### `URL_API_BASE` (constante, no es función)
Dirección base del backend. Si la página se abre desde `localhost`/`127.0.0.1` (pruebas
locales) apunta automáticamente a `http://127.0.0.1:8787`; en cualquier otro dominio (por
ejemplo GitHub Pages) usa la URL de producción del Worker de Cloudflare, que debe
reemplazarse una vez desplegado (ver `README.md`).

### `LIMITE_ALFABETO` (constante, no es función)
Copia en el frontend del mismo número (`256`) que `alfabeto.py` usa en el backend
(`LIMITE_ALFABETO`). Se usa en `SF27` para el contador en vivo y coincide con el atributo
`maxlength="256"` del campo de alfabeto en `front/index.html`, de modo que el límite es
idéntico y visible en ambos lados.

### SF20
- **Parámetros:** `ruta` (str, p. ej. `/api/cifrar`), `cuerpo` (objeto JS a serializar como
  JSON).
- **Ubicación:** `front/main.js`. Función asíncrona.
- **Qué hace:** helper genérico de comunicación con el backend: hace `fetch` con método
  `POST`, cabecera `content-type: application/json` y el `cuerpo` serializado; si la
  respuesta HTTP no es exitosa, lanza un `Error` con el mensaje que venga en `datos.error`.

### SF21
- **Parámetros:** `mensaje` (str), `esError` (bool).
- **Ubicación:** `front/main.js`.
- **Qué hace:** actualiza los elementos `#alphabet-error` y `#alphabet-status` del DOM según
  si el mensaje es un error o una confirmación.

### SF22
- **Parámetros:** `evento` (evento `submit` del formulario `#alphabet-form`).
- **Ubicación:** `front/main.js`. Función asíncrona.
- **Qué hace:** maneja el envío del formulario de alfabeto: evita el envío nativo del
  formulario, llama a `SF20` contra `/api/alfabeto/validar`, y si es válido guarda el
  alfabeto en la variable de módulo `SFEstadoAlfabeto` y en `localStorage` (para sobrevivir a
  recargas de página), y muestra confirmación con `SF21`. Este alfabeto "aplicado" es el que
  se usará tanto para cifrar como para descifrar.

### SF23
- **Parámetros:** `evento` (evento `submit` del formulario `#encrypt-form`).
- **Ubicación:** `front/main.js`. Función asíncrona.
- **Qué hace:** maneja el cifrado explícito. Exige que ya exista un alfabeto aplicado; lee el
  método elegido (`#encrypt-method`) y el texto (`#encrypt-text`); si el método es César
  añade el desplazamiento (`#encrypt-shift`); llama a `SF20` contra `/api/cifrar` y muestra
  el resultado en `#encrypt-result`.

### SF24
- **Parámetros:** `evento` (evento `submit` del formulario `#decrypt-form`).
- **Ubicación:** `front/main.js`. Función asíncrona.
- **Qué hace:** maneja el descifrado automático. Exige que ya exista un alfabeto aplicado;
  envía el texto cifrado a `/api/descifrar` (sin que el usuario indique método ni
  desplazamiento) y muestra el método detectado, el desplazamiento (o "No aplica" si fue
  Atbash) y el texto descifrado — la única línea que el sistema considera correcta.

### SF25
- **Parámetros:** `idOrigen` (str, id de un elemento del DOM cuyo `textContent` se quiere
  copiar).
- **Ubicación:** `front/main.js`.
- **Qué hace:** copia al portapapeles el contenido del elemento indicado, usado por los
  botones "Copiar al portapapeles" de ambas secciones.

### SF26
- **Parámetros:** ninguno.
- **Ubicación:** `front/main.js`.
- **Qué hace:** conecta el comportamiento del selector de método de cifrado (muestra/oculta
  el campo de desplazamiento según si el método es César o Atbash) y de los botones ▲/▼ del
  stepper de desplazamiento, respetando siempre el límite 1-25 (igual que `DESPLAZAMIENTO_MIN`
  / `DESPLAZAMIENTO_MAX` del backend).

### SF27
- **Parámetros:** ninguno.
- **Ubicación:** `front/main.js`.
- **Qué hace:** conecta el contador en vivo "`X / 256 caracteres`" bajo el campo de alfabeto:
  en cada tecla pulsada, actualiza el conteo y pinta el número en rojo (usando la variable de
  color `--error` del CSS existente) si se supera `LIMITE_ALFABETO`, para que el límite del
  backend sea visible en el frontend antes de enviar el formulario.

### SF28
- **Parámetros:** ninguno.
- **Ubicación:** `front/main.js`.
- **Qué hace:** función de arranque, ejecutada en `DOMContentLoaded`. Restaura el alfabeto
  guardado en `localStorage` (si existe), y registra todos los manejadores de eventos:
  `SF22` en el formulario de alfabeto, `SF23` en el de cifrado, `SF24` en el de descifrado,
  `SF25` en ambos botones de copiar, y llama a `SF26` y `SF27` para inicializar el stepper y
  el contador de caracteres.
