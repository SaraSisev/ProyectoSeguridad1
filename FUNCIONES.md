# Documentación de funciones (identificadores SF)

Este documento es la única fuente de explicación del comportamiento interno del sistema.
En el código fuente del backend (`backend/src/*.py`) y del frontend (`frontend/main.js`) las
funciones no llevan comentarios descriptivos: cada una está identificada únicamente con un
código `SFx`, **único en todo el proyecto** (no se repite entre archivos). Este documento
describe, para cada identificador, qué hace, qué parámetros recibe, dónde está ubicado y cómo
funciona internamente.

## Organización del backend

```
backend/src/
  alfabeto.py             -> validación del alfabeto y utilidades de índices/desplazamiento
  cifrado.py               -> las dos operaciones de cifrado: César y Atbash
  descifrado.py            -> únicamente la primitiva de César inverso (con un desplazamiento dado)
  datos_espanol.py         -> datos fijos del idioma: frecuencias, n-gramas, diccionario, morfología
  analisis_frecuencia.py   -> calcula los 9 componentes del puntaje de un candidato
  analizador.py            -> genera las 26 hipótesis, las puntúa y elige la ganadora
  entry.py                 -> punto de entrada del Worker de Cloudflare (rutas HTTP, CORS)
```

Todos salvo `entry.py` son Python puro (sin dependencias del runtime de Cloudflare), por lo
que pueden importarse y probarse de forma aislada. Solo `entry.py` depende del módulo
`workers`, propio de Cloudflare.

## Fundamento criptográfico (Al-Kindi)

El descifrado automático (sin intervención humana) se basa en el **análisis de frecuencias**,
técnica de criptoanálisis descrita por primera vez por **Abū Yūsuf Ya'qūb ibn Isḥāq al-Kindī**
(أبو يوسف يعقوب بن إسحاق الكندي) en su tratado *Risāla fī Istikhrāj al-Muʿammā* (siglo IX):
observó que, en un idioma natural, cada letra y cada combinación de letras aparece con una
frecuencia estadística característica, y que esa "huella" del idioma permite reconocer el
texto correcto entre varias hipótesis de descifrado.

### Cómo se decide el descifrado correcto

`analizador.py` (`SF20`) prueba las 26 claves posibles (Atbash + los 25 desplazamientos
César), calcula el puntaje multi-componente de cada una (`analisis_frecuencia.SF18`) y se
queda con la de **mayor valor** (`max(candidatos, key=lambda c: c["analisis"]["total"])`). Un
solo número por candidato, gana el mayor — sin intervención humana y sin mostrar las otras 25
opciones descartadas.

Ese número combina **nueve señales independientes**, cada una midiendo una propiedad distinta
de "qué tan español real" se ve un texto. Se suman entre sí (las penalizaciones se restan)
porque cada señal aporta evidencia independiente: cuantas más señales apunten en la misma
dirección, más confianza hay en que ese candidato es el texto original.

| Componente | Función | Qué mide |
|---|---|---|
| Frecuencia de letras | `SF9` | ¿La mezcla de letras se parece a la del español? (chi-cuadrado) |
| Palabras del diccionario | `SF10` | ¿Aparecen palabras reales del español, y qué tan comunes son? |
| Bigramas | `SF11` + `PESOS_BIGRAMAS` | ¿Aparecen combinaciones de 2 letras típicas del español ("de", "en", "ar"...)? |
| Trigramas | `SF11` + `PESOS_TRIGRAMAS` | Lo mismo, con combinaciones de 3 letras ("que", "con", "ado"...) |
| Tetragramas | `SF11` + `PESOS_TETRAGRAMAS` | Lo mismo, con combinaciones de 4 letras ("para", "ente"...) |
| Prefijos | `SF12` | ¿Las palabras empiezan con prefijos típicos del español ("des-", "con-"...)? |
| Sufijos | `SF13` | ¿Las palabras terminan en sufijos típicos ("-mente", "-ando", "-idad"...)? |
| Proporción de vocales | `SF15` | ¿La proporción vocales/consonantes es la típica del español? |
| Estructura de palabra | `SF17` | ¿Las palabras tienen forma razonable (no son cadenas de puras consonantes, ni tienen letras repetidas 4+ veces)? |
| Secuencias improbables (penalización) | `SF14` | ¿Aparecen combinaciones casi imposibles en español ("qq", "jj", "wq"...)? |

### De dónde salen los datos del idioma

Todos los valores de `datos_espanol.py` (frecuencia de cada letra, pesos de n-gramas,
diccionario, prefijos, sufijos, secuencias improbables, proporción de vocales) son
**constantes fijas conocidas del idioma español** — el mismo tipo de dato que cualquier
estudio de estadística del lenguaje reporta (por ejemplo, que la "e" es la letra más frecuente
del español, o que "-mente" es un sufijo muy común). No dependen de ningún archivo de texto
externo cargado en tiempo de ejecución: son literales, igual que en el ejemplo de referencia
en el que se basa este módulo.

### Alcance de la detección automática

El sistema está optimizado para **conjuntos de palabras y frases** (varias palabras juntas),
que es el caso de uso principal del proyecto. Con una frase de varias palabras, las nueve
señales (frecuencia, diccionario, n-gramas, morfología) coinciden todas en la clave correcta y
la detección es muy confiable. Con una sola palabra muy corta (3-4 letras), puede que no haya
suficiente evidencia estadística y el sistema elija una clave incorrecta — esto es una
limitación matemática esperada del análisis de frecuencias con muestras pequeñas, no un error
del programa. Los límites exactos (a partir de cuántas letras/palabras la detección es
confiable) se determinan con pruebas de escritorio sobre el sistema ya desplegado.

---

## `backend/src/alfabeto.py`

### Constantes
- `LIMITE_ALFABETO = 1000`: máximo de caracteres distintos del alfabeto. El frontend usa el
  mismo número (`LIMITE_ALFABETO` en `main.js`, `maxlength="1000"` en el HTML).
- `LIMITE_TEXTO = 10000`: máximo de caracteres del texto a cifrar/descifrar. Se definió
  midiendo el tiempo real de análisis (ver `PRUEBAS_Y_LIMITACIONES.md`): 10 000 caracteres se
  procesan en medio segundo aproximadamente. Se valida en `entry.py` (`SF25`, `SF26`) y el
  frontend usa el mismo número como `maxlength="10000"` en ambos campos de texto.
- `DESPLAZAMIENTO_MIN = 1`, `DESPLAZAMIENTO_MAX = 25`: rango del desplazamiento César, igual
  que los atributos `min`/`max` del campo de desplazamiento en `frontend/index.html`.

### SF1
- **Parámetros:** `alfabeto` (str).
- **Ubicación:** `backend/src/alfabeto.py`.
- **Qué hace:** valida que el alfabeto sea utilizable: cadena no vacía, máximo 1000
  caracteres, sin repetidos, al menos 2 caracteres distintos.
- **Cómo lo hace:** convierte la cadena en lista de caracteres Unicode (cada carácter, sea
  ASCII, chino, árabe, un jeroglífico, etc., cuenta como un solo elemento porque Python 3
  itera por punto de código completo) y compara `len(lista)` contra `len(set(lista))`.
- **Devuelve:** tupla `(valido: bool, mensaje_error: str)`.
- **Quién la usa:** `SF24`, `SF25`, `SF26` (en `entry.py`).

### SF2
- **Parámetros:** `alfabeto` (str).
- **Ubicación:** `backend/src/alfabeto.py`.
- **Qué hace:** construye el mapa `carácter -> posición` dentro del alfabeto.
- **Quién la usa:** `SF4`, `SF5` (en `cifrado.py`) y `SF6` (en `descifrado.py`).

### SF3
- **Parámetros:** `desplazamiento` (int, 1-25), `longitud_alfabeto` (int).
- **Ubicación:** `backend/src/alfabeto.py`.
- **Qué hace:** valida el rango 1-25 y normaliza el desplazamiento al tamaño real del
  alfabeto (`% longitud_alfabeto`).
- **Lanza:** `ValueError` si no es un entero válido o está fuera de rango.
- **Quién la usa:** `SF4` (en `cifrado.py`) y `SF6` (en `descifrado.py`).

---

## `backend/src/cifrado.py`

Importa `SF2` y `SF3` de `alfabeto.py`.

### SF4 (César — cifrar)
- **Parámetros:** `texto` (str), `alfabeto` (str), `desplazamiento` (int, 1-25).
- **Ubicación:** `backend/src/cifrado.py`.
- **Qué hace:** cifra `texto` con César. Para cada carácter, si está en el alfabeto, se
  reemplaza por el que está `desplazamiento` posiciones adelante (cíclico); si no está en el
  alfabeto se deja igual ("se pasa por alto").
- **Quién la usa:** `SF25` en `entry.py`.

### SF5 (Atbash — cifra y descifra, es autoinverso)
- **Parámetros:** `texto` (str), `alfabeto` (str).
- **Ubicación:** `backend/src/cifrado.py`.
- **Qué hace:** cada carácter se reemplaza por el simétrico del alfabeto
  (`longitud - 1 - posición`). Al ser una involución, sirve para cifrar y descifrar con la
  misma función.
- **Quién la usa:** `SF25` en `entry.py` (cifrar) y `SF19` en `analizador.py` (candidato
  Atbash durante la autodetección).

---

## `backend/src/descifrado.py`

Solo contiene la primitiva de descifrado César; la orquestación de las 26 hipótesis vive en
`analizador.py`.

### SF6 (César — descifrar con un desplazamiento dado)
- **Parámetros:** `texto` (str), `alfabeto` (str), `desplazamiento` (int, 1-25).
- **Ubicación:** `backend/src/descifrado.py`.
- **Qué hace:** inversa de `SF4`: resta el desplazamiento en vez de sumarlo (mismo criterio
  de "pasar por alto" los caracteres fuera del alfabeto).
- **Quién la usa:** `SF19` (en `analizador.py`), 25 veces, una por cada desplazamiento
  candidato.

---

## `backend/src/datos_espanol.py`

Todos los datos del idioma español que usa el motor de análisis, como constantes fijas. No
depende de ningún otro archivo del proyecto.

### `LETRAS_ESPANOL`, `VOCALES`, `PATRON_PALABRA`, `TABLA_ACENTOS` (constantes)
El alfabeto español en minúsculas, el conjunto de vocales (con tilde), la expresión regular
`[a-zñ]+` usada para separar palabras, y la tabla de traducción de vocales acentuadas a su
forma base.

### `FRECUENCIA_LETRAS` (constante)
Porcentaje de aparición de cada letra española en el idioma (a=12.53%, e=13.68%, etc.).

### `PALABRAS_MUY_COMUNES`, `PALABRAS_COMUNES` (constantes)
Diccionario en dos niveles: ~20 palabras gramaticales de uso constante (de, la, que, el...) y
un conjunto más amplio de palabras y verbos comunes.

### `PESOS_BIGRAMAS`, `PESOS_TRIGRAMAS`, `PESOS_TETRAGRAMAS` (constantes)
Peso de las combinaciones de 2, 3 y 4 letras más típicas del español ("de", "que", "para",
"ente"...).

### `PESOS_PREFIJOS`, `PESOS_SUFIJOS` (constantes)
Prefijos (des-, con-, re-...) y sufijos (-mente, -ción, -ando...) típicos del español, con un
peso relativo.

### `PESOS_SECUENCIAS_IMPROBABLES` (constante)
Combinaciones de letras casi inexistentes en español (jj, kk, qq, wx...), con una
penalización.

### `RATIO_VOCALES_MIN`/`OBJETIVO`/`MAX`, `LONGITUD_PALABRA_MAX_RAZONABLE` (constantes)
Proporción típica de vocales sobre el total de letras en español (0.25 a 0.65, objetivo 0.45)
y longitud a partir de la cual una "palabra" se considera sospechosamente larga (18).

### SF7
- **Parámetros:** `texto` (str).
- **Ubicación:** `backend/src/datos_espanol.py`.
- **Qué hace:** normaliza el texto para el análisis: minúsculas + vocales acentuadas a su
  forma base (á→a, é→e, í→i, ó→o, ú→u, ü→u). No toca la `ñ`. Nunca se usa para el texto que
  ve el usuario, solo para análisis interno.
- **Quién la usa:** internamente en `analisis_frecuencia.py` (`SF18`).

### SF8
- **Parámetros:** `texto_normalizado` (str, ya pasado por `SF7`).
- **Ubicación:** `backend/src/datos_espanol.py`.
- **Qué hace:** separa el texto en palabras usando `PATRON_PALABRA`.
- **Quién la usa:** en `analisis_frecuencia.py` (`SF18`).

---

## `backend/src/analisis_frecuencia.py`

El motor de puntuación de un solo candidato. Importa de `datos_espanol.py` todo lo que
necesita.

### SF9 (frecuencia de letras)
- **Parámetros:** `texto_normalizado` (str).
- **Ubicación:** `backend/src/analisis_frecuencia.py`.
- **Qué hace:** chi-cuadrado clásico entre la mezcla de letras del candidato y
  `FRECUENCIA_LETRAS`, normalizado y convertido a un puntaje acotado:
  `35 / (1 + chi_cuadrado_normalizado)`.
- **Caso especial:** sin letras españolas reconocibles, devuelve `-20.0`.
- **Quién la usa:** `SF18`.

### SF10 (palabras del diccionario)
- **Parámetros:** `palabras` (list[str]).
- **Ubicación:** `backend/src/analisis_frecuencia.py`.
- **Qué hace:** suma `3.0 + min(long, 8) * 0.80` por cada palabra en `PALABRAS_MUY_COMUNES`, y
  `1.5 + min(long, 8) * 0.50` por cada una en `PALABRAS_COMUNES`.
- **Quién la usa:** `SF18`.

### SF11 (patrones — bigramas, trigramas, tetragramas)
- **Parámetros:** `texto_normalizado` (str), `tabla_pesos` (dict).
- **Ubicación:** `backend/src/analisis_frecuencia.py`.
- **Qué hace:** función genérica reutilizada tres veces: para cada patrón de la tabla, cuenta
  apariciones como subcadena (`texto.count(patron)`) y suma `apariciones * peso`.
- **Quién la usa:** `SF18`, una vez por cada una de las tres tablas.

### SF12 (prefijos) / SF13 (sufijos)
- **Parámetros:** `palabras` (list[str]).
- **Ubicación:** `backend/src/analisis_frecuencia.py`.
- **Qué hacen:** revisan si cada palabra empieza (`SF12`) o termina (`SF13`) con alguna
  entrada de `PESOS_PREFIJOS`/`PESOS_SUFIJOS` y suman el peso correspondiente.
- **Quién las usa:** `SF18`.

### SF14 (penalización de secuencias improbables)
- **Parámetros:** `texto_normalizado` (str).
- **Ubicación:** `backend/src/analisis_frecuencia.py`.
- **Qué hace:** cuenta apariciones de cada secuencia de `PESOS_SECUENCIAS_IMPROBABLES` y
  acumula la penalización (se resta en `SF18`).
- **Quién la usa:** `SF18`.

### SF15 (proporción de vocales)
- **Parámetros:** `texto_normalizado` (str).
- **Ubicación:** `backend/src/analisis_frecuencia.py`.
- **Qué hace:** `puntaje = 12.0 - |ratio - objetivo| * 40`; resta 8 puntos extra si el ratio
  se sale de `RATIO_VOCALES_MIN`/`MAX`.
- **Devuelve:** `(puntaje, ratio)`. Sin letras: `(-20.0, 0.0)`.
- **Quién la usa:** `SF18`.

### SF16 (secuencia de consonantes más larga — auxiliar) / SF17 (estructura de palabra)
- **Parámetros:** `SF16` recibe una `palabra` (str); `SF17` recibe `palabras` (list[str]).
- **Ubicación:** `backend/src/analisis_frecuencia.py`.
- **Qué hacen:** `SF16` mide la racha más larga de consonantes seguidas de una palabra.
  `SF17` puntúa la plausibilidad de las palabras: bono por tener varias, penalización por
  palabras muy largas, sin vocales, con 5+ consonantes seguidas (`SF16`), o con un carácter
  repetido 4+ veces. Sin palabras, devuelve `-15.0`.
- **Quién las usa:** `SF18`.

### SF18 (puntaje total de un candidato)
- **Parámetros:** `texto` (str) — un candidato completo de texto descifrado.
- **Ubicación:** `backend/src/analisis_frecuencia.py`.
- **Qué hace:** normaliza (`SF7`) y separa en palabras (`SF8`); calcula los nueve componentes
  (`SF9`-`SF17`) y los suma en un total.
- **Devuelve:** `{"total": float, "componentes": {...9 valores, útiles para depurar...},
  "ratio_vocales": float, "num_palabras": int, "num_letras": int}`.
- **Quién la usa:** `SF19`/`SF20` (en `analizador.py`).

---

## `backend/src/analizador.py`

Orquesta el criptoanálisis completo: genera las 26 hipótesis, las puntúa y elige la ganadora.

### SF19 (generar las 26 hipótesis)
- **Parámetros:** `texto_cifrado` (str), `alfabeto` (str).
- **Ubicación:** `backend/src/analizador.py`.
- **Qué hace:** genera el candidato Atbash (`cifrado.SF5`) y los 25 candidatos César
  (`descifrado.SF6`, desplazamientos 1 a 25 — el mismo rango permitido al cifrar; no se
  prueban desplazamientos fuera de ese rango porque nunca podrían haberse usado para cifrar).
- **Devuelve:** lista de `{"metodo": "ATBASH"|"CESAR", "desplazamiento": int|None,
  "texto": str}`.
- **Quién la usa:** `SF20`.

### SF20 (analizar el texto cifrado — punto de entrada del criptoanálisis)
- **Parámetros:** `texto_cifrado` (str), `alfabeto` (str).
- **Ubicación:** `backend/src/analizador.py`.
- **Qué hace:** genera las hipótesis (`SF19`), calcula el análisis completo de cada una
  (`analisis_frecuencia.SF18`), y elige la de mayor `analisis["total"]` con `max(...)`.
- **Devuelve:** `{"metodo": str, "desplazamiento": int|None, "texto": str}`.
- **Quién la usa:** `SF26` (en `entry.py`). Solo el resultado de esta función se le muestra al
  usuario — es la única línea "correcta" que exige el enunciado.

---

## `backend/src/entry.py`

Punto de entrada del *Cloudflare Worker* (Python). Depende del módulo `workers`, propio del
runtime de Cloudflare, por lo que no se puede importar ni probar fuera de ese entorno; toda la
lógica de negocio vive en los archivos anteriores, precisamente para poder probarla de forma
aislada.

### SF21
- **Parámetros:** ninguno.
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** devuelve las cabeceras CORS (`access-control-allow-origin: *`, métodos y
  headers permitidos) que se agregan a **todas** las respuestas.

### SF22
- **Parámetros:** `datos` (dict), `estado` (int, por defecto 200).
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** construye la respuesta HTTP: serializa `datos` a JSON con
  `ensure_ascii=False` (para que chino/árabe/jeroglíficos/acentos viajen tal cual, en UTF-8),
  añade las cabeceras de `SF21` más `content-type: application/json; charset=utf-8`.

### SF23
- **Parámetros:** `request` (objeto `Request` de Cloudflare). Función asíncrona.
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** lee el cuerpo como texto y lo interpreta como JSON; si viene vacío, devuelve
  un diccionario vacío.
- **Manejo de errores (agregado tras las pruebas reales, ver `PRUEBAS_Y_LIMITACIONES.md`):**
  si el cuerpo no es JSON válido, o es JSON válido pero no es un objeto (por ejemplo un
  arreglo), devuelve `None` en vez de dejar que `json.JSONDecodeError` o un `AttributeError`
  posterior se propaguen sin control. Antes de este cambio, una solicitud mal formada
  provocaba un error 500 que exponía el traceback interno del servidor al cliente.
- **Quién revisa el resultado:** `on_fetch`, que responde `400` con un mensaje claro si
  `SF23` devuelve `None`, antes de intentar enrutar la solicitud.

### SF24
- **Parámetros:** `payload` (dict, espera `alfabeto`).
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** implementa `POST /api/alfabeto/validar`. Normaliza el alfabeto a la forma
  Unicode NFC (`unicodedata.normalize("NFC", ...)`) antes de validarlo con `SF1` — ver la nota
  sobre normalización Unicode más abajo.

### SF25
- **Parámetros:** `payload` (dict, espera `alfabeto`, `metodo`, `texto`, y
  `desplazamiento` si el método es César).
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** implementa `POST /api/cifrar`: normaliza alfabeto y texto a NFC, valida con
  `SF1`, verifica que el texto no esté vacío ni supere `LIMITE_TEXTO`, e invoca `SF5` (Atbash)
  o `SF4` (César, validando el desplazamiento). Único lugar donde el usuario elige el método
  de cifrado.

### SF26
- **Parámetros:** `payload` (dict, espera `alfabeto` y `texto`).
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** implementa `POST /api/descifrar`: normaliza alfabeto y texto a NFC, valida con
  `SF1`, verifica el límite de longitud del texto, y delega toda la decisión a `SF20` (en
  `analizador.py`). Devuelve método, desplazamiento y texto. El usuario no interviene en
  ningún punto.

### Normalización Unicode (NFC) — corrección encontrada en pruebas reales
`SF24`, `SF25` y `SF26` normalizan el alfabeto (y el texto) a la forma Unicode NFC apenas se
reciben del cuerpo de la solicitud, usando el módulo estándar `unicodedata`. Esto corrige una
inconsistencia real: un mismo alfabeto "visualmente idéntico" puede representarse con distinta
cantidad de puntos de código Unicode según cómo se haya escrito o copiado (por ejemplo, una
"É" como un solo carácter precompuesto, o como una "E" seguida de un acento combinado por
separado); sin normalizar, esas dos representaciones tienen distinta longitud interna y
producen resultados de cifrado/descifrado distintos aunque el usuario las vea como "el mismo"
alfabeto. El detalle completo de cómo se encontró y verificó esta corrección está en
`PRUEBAS_Y_LIMITACIONES.md`.

### `on_fetch` (nombre reservado, no forma parte de la numeración SF)
- **Parámetros:** `request`, `env`, `ctx` (firma exigida por Cloudflare; el nombre es
  obligatorio).
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** único punto de entrada HTTP. Responde `204` a `OPTIONS`; si `SF23` no pudo
  interpretar el cuerpo como un objeto JSON, responde `400` de inmediato; en caso contrario
  enruta `POST /api/alfabeto/validar` a `SF24`, `POST /api/cifrar` a `SF25` y
  `POST /api/descifrar` a `SF26`; cualquier otra ruta devuelve `404`.

---

## `frontend/main.js`

Lógica de interfaz. Consume la API del backend mediante `fetch`. No contiene lógica
criptográfica: todo el cifrado/descifrado/autodetección ocurre en el backend.

### `URL_API_BASE` (constante)
Si la página se abre desde `localhost`/`127.0.0.1` usa `http://127.0.0.1:8787`; en cualquier
otro dominio usa la URL de producción del Worker (reemplazar tras desplegar, ver `README.md`).

### `LIMITE_ALFABETO` (constante)
Copia en el frontend del mismo `1000` que usa `alfabeto.py`, para el contador en vivo (`SF34`).

### SF27
- **Parámetros:** `ruta` (str), `cuerpo` (objeto JS). Función asíncrona.
- **Ubicación:** `frontend/main.js`.
- **Qué hace:** helper de `fetch` con método POST y JSON; lanza `Error` si la respuesta no es
  exitosa.

### SF28
- **Parámetros:** `mensaje` (str), `esError` (bool).
- **Ubicación:** `frontend/main.js`.
- **Qué hace:** actualiza `#alphabet-error`/`#alphabet-status`.

### SF29
- **Parámetros:** `evento` (submit de `#alphabet-form`). Función asíncrona.
- **Ubicación:** `frontend/main.js`.
- **Qué hace:** valida el alfabeto contra el backend (`SF27`), lo guarda en
  `SFEstadoAlfabeto` y `localStorage` si es válido.

### SF30
- **Parámetros:** `evento` (submit de `#encrypt-form`). Función asíncrona.
- **Ubicación:** `frontend/main.js`.
- **Qué hace:** cifra el texto con el método/desplazamiento elegidos, vía `SF27`.

### SF31
- **Parámetros:** `evento` (submit de `#decrypt-form`). Función asíncrona.
- **Ubicación:** `frontend/main.js`.
- **Qué hace:** envía el texto cifrado a `/api/descifrar` (sin indicar método) y muestra el
  método, desplazamiento y el texto descifrado detectados automáticamente.

### SF32
- **Parámetros:** `idOrigen` (str).
- **Ubicación:** `frontend/main.js`.
- **Qué hace:** copia al portapapeles el contenido de un elemento del DOM.

### SF33
- **Parámetros:** ninguno.
- **Ubicación:** `frontend/main.js`.
- **Qué hace:** muestra/oculta el campo de desplazamiento según el método elegido, y conecta
  los botones ▲/▼ del stepper (límite 1-25).

### SF34
- **Parámetros:** ninguno.
- **Ubicación:** `frontend/main.js`.
- **Qué hace:** contador en vivo "`X / 1000 caracteres`" bajo el campo de alfabeto; lo pinta en
  rojo si se supera `LIMITE_ALFABETO`.

### SF35
- **Parámetros:** ninguno.
- **Ubicación:** `frontend/main.js`.
- **Qué hace:** arranque en `DOMContentLoaded`: restaura el alfabeto de `localStorage`, y
  registra `SF29`-`SF32` como manejadores de eventos, más `SF33` y `SF34`.
