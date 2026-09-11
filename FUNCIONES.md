# Documentación de funciones (identificadores SF)

Este documento es la única fuente de explicación del comportamiento interno del sistema.
En el código fuente (`backend/src/logic.py`, `backend/src/entry.py` y `front/main.js`) las
funciones no llevan comentarios descriptivos: cada una está identificada únicamente con un
código `SFx`. Este archivo describe, para cada identificador, qué hace, qué parámetros
recibe, dónde está ubicado y cómo funciona internamente.

## Fundamento criptográfico (Al-Kindi)

El descifrado automático (sin intervención humana) se basa en el **análisis de frecuencias**,
técnica de criptoanálisis descrita por primera vez por **Abū Yūsuf Ya'qūb ibn Isḥāq al-Kindī**
(أبو يوسف يعقوب بن إسحاق الكندي) en su tratado *Risāla fī Istikhrāj al-Muʿammā* (siglo IX).
El principio es que, en un idioma natural (aquí, español), cada letra aparece con una
frecuencia estadística característica. Como César y Atbash son cifrados de sustitución
monoalfabética, esa distribución de frecuencias se conserva "desplazada" o "invertida" en el
texto cifrado. El sistema prueba todas las hipótesis posibles (Atbash + los 25 desplazamientos
César) y se queda con la única cuyo texto resultante se parece más al español real, combinando
dos señales: (1) qué tan cercana es su distribución de letras a la frecuencia estadística del
español (chi-cuadrado, `SF9`) y (2) cuántas palabras españolas reconocibles contiene
(`SF26`, útil cuando el texto es demasiado corto para que la estadística por sí sola sea
confiable). Por diseño, solo se le muestra al usuario la línea descifrada ganadora: el usuario
nunca elige entre candidatos.

---

## `backend/src/logic.py`

Módulo puro de Python (sin dependencias del runtime de Cloudflare), por lo que puede
importarse y probarse de forma aislada.

### Constantes
- `FREC_ESPANOL`: diccionario `letra -> porcentaje` con la frecuencia estadística de cada
  letra del español (a-z y ñ), usado como referencia por `SF9`.
- `TABLA_ACENTOS`: tabla de traducción (`str.maketrans`) que convierte vocales acentuadas
  (á, é, í, ó, ú, ü, mayúsculas incluidas) en su forma sin tilde, para efectos únicamente de
  conteo estadístico (no altera el texto cifrado/descifrado real).
- `LIMITE_ALFABETO = 256`: número máximo de caracteres distintos permitidos en el alfabeto.
- `DESPLAZAMIENTO_MIN = 1`, `DESPLAZAMIENTO_MAX = 25`: rango permitido para el desplazamiento
  César.
- `PALABRAS_COMUNES`: conjunto de palabras muy frecuentes del español (sin tildes, en
  mayúsculas) usado por `SF26` como segunda señal de detección automática, complementaria al
  análisis estadístico de frecuencias de `SF9`.

### SF1
- **Parámetros:** `alfabeto` (str) — el conjunto de caracteres que el usuario quiere usar.
- **Ubicación:** `backend/src/logic.py`.
- **Qué hace:** valida que el alfabeto sea utilizable: que sea una cadena no vacía, que no
  supere `LIMITE_ALFABETO` (256) caracteres, que no tenga caracteres repetidos y que tenga al
  menos 2 caracteres distintos (mínimo necesario para que un desplazamiento tenga efecto).
- **Cómo lo hace:** convierte la cadena en lista de caracteres Unicode (cada carácter, sin
  importar si es ASCII, chino, árabe, etc., cuenta como un solo elemento porque Python 3
  itera cadenas por punto de código, no por bytes) y compara `len(lista)` contra
  `len(set(lista))` para detectar duplicados.
- **Devuelve:** tupla `(valido: bool, mensaje_error: str)`.
- **Quién la usa:** `SF14`, `SF15`, `SF16` (backend) antes de cualquier operación de
  cifrado/descifrado.

### SF2
- **Parámetros:** `alfabeto` (str).
- **Ubicación:** `backend/src/logic.py`.
- **Qué hace:** construye el mapa `carácter -> posición` dentro del alfabeto (posición 0 a
  `len(alfabeto)-1`).
- **Cómo lo hace:** comprensión de diccionario sobre `enumerate(alfabeto)`.
- **Quién la usa:** `SF4`, `SF5`, `SF6` para saber en qué posición está cada carácter antes
  de desplazarlo o invertirlo.

### SF3
- **Parámetros:** `desplazamiento` (int, 1-25), `longitud_alfabeto` (int).
- **Ubicación:** `backend/src/logic.py`.
- **Qué hace:** valida que el desplazamiento sea un entero dentro del rango permitido
  (1 a 25, tal como exige el proyecto) y lo normaliza al tamaño real del alfabeto mediante
  módulo, para que el índice resultante nunca se salga de rango.
- **Cómo lo hace:** `desplazamiento % longitud_alfabeto`.
- **Lanza:** `ValueError` con mensaje en español si el valor no es un entero válido o está
  fuera de 1-25.
- **Quién la usa:** `SF4`, `SF5`.

### SF4 (César — cifrar)
- **Parámetros:** `texto` (str, texto plano en español), `alfabeto` (str), `desplazamiento`
  (int, 1-25).
- **Ubicación:** `backend/src/logic.py`.
- **Qué hace:** cifra `texto` con César sobre el alfabeto dado.
- **Cómo lo hace:** para cada carácter del texto, si está dentro del alfabeto (según el mapa
  de `SF2`) se reemplaza por el carácter que está `desplazamiento` posiciones adelante (con
  vuelta cíclica, `% len(alfabeto)`); si el carácter **no** está en el alfabeto (espacios,
  puntuación no incluida, letras no incluidas, etc.) se deja exactamente igual — se "pasa por
  alto", tal como pide el enunciado.
- **Devuelve:** el texto cifrado (str).

### SF5 (César — descifrar)
- **Parámetros:** igual que `SF4`.
- **Ubicación:** `backend/src/logic.py`.
- **Qué hace:** operación inversa de `SF4`: resta el desplazamiento en vez de sumarlo.
- **Quién la usa:** el cifrado explícito (`SF15`, cuando el frontend pide descifrar
  manualmente no existe como endpoint separado — el único descifrado expuesto es automático,
  `SF16`) y, sobre todo, `SF10`, que la invoca 25 veces (una por cada desplazamiento posible)
  para generar los candidatos que luego se puntúan con `SF9`.

### SF6 (Atbash — cifrar y descifrar, es autoinverso)
- **Parámetros:** `texto` (str), `alfabeto` (str).
- **Ubicación:** `backend/src/logic.py`.
- **Qué hace:** aplica la transformación Atbash: cada carácter se reemplaza por el que ocupa
  la posición simétrica del alfabeto (`longitud - 1 - posición`). Al ser una involución
  (aplicarla dos veces devuelve el texto original), la misma función sirve para cifrar y para
  descifrar.
- **Quién la usa:** el cifrado explícito cuando el usuario elige método "ATBASH" (`SF15`) y
  `SF10` para generar el candidato Atbash durante la autodetección.

### SF7
- **Parámetros:** `texto` (str).
- **Ubicación:** `backend/src/logic.py`.
- **Qué hace:** normaliza vocales acentuadas a su forma base (á→a, é→e, í→i, ó→o, ú→u, ü→u,
  incluyendo mayúsculas) usando `TABLA_ACENTOS`. **No** afecta la letra `ñ` (se preserva tal
  cual porque es una letra distinta en el alfabeto español con su propia frecuencia en
  `FREC_ESPANOL`).
- **Por qué existe:** el análisis de frecuencias de Al-Kindi (`SF8`/`SF9`) debe contar "e" y
  "é" como la misma letra estadística; esta función solo se usa para esa cuenta, nunca para
  el texto que finalmente se le muestra al usuario.
- **Quién la usa:** `SF8`.

### SF8
- **Parámetros:** `texto` (str) — típicamente un candidato de texto descifrado.
- **Ubicación:** `backend/src/logic.py`.
- **Qué hace:** cuenta cuántas veces aparece cada letra española (a-z, ñ) en el texto.
- **Cómo lo hace:** pasa el texto por `SF7` (quita tildes de vocales) y lo pone en
  minúsculas; recorre carácter por carácter y, si el carácter es una de las claves de
  `FREC_ESPANOL`, incrementa su contador y el total.
- **Devuelve:** tupla `(conteo: dict[letra, int], total: int)`.
- **Quién la usa:** `SF9`.

### SF9 (estadístico de "españolidad" — núcleo del método de Al-Kindi)
- **Parámetros:** `texto` (str) — un candidato de texto descifrado.
- **Ubicación:** `backend/src/logic.py`.
- **Qué hace:** calcula qué tan parecida es la distribución de letras del texto a la
  distribución real del idioma español, mediante el estadístico **chi-cuadrado**:
  `Σ ((observado - esperado)² / esperado)` para cada letra, donde `esperado = total_letras *
  (frecuencia_española / 100)`. Cuanto **menor** el valor, más se parece el texto al español
  real.
- **Caso especial:** si el texto no contiene ninguna letra española reconocible (`total == 0`,
  por ejemplo un texto vacío o compuesto solo de símbolos fuera del alfabeto español), se
  devuelve `float("inf")` para que ese candidato nunca gane la comparación.
- **Quién la usa:** `SF10`, para comparar los 26 candidatos posibles (1 Atbash + 25 César).

### SF26 (segunda señal de Al-Kindi: coincidencia léxica)
- **Parámetros:** `texto` (str) — un candidato de texto descifrado.
- **Ubicación:** `backend/src/logic.py`.
- **Por qué existe:** el chi-cuadrado de `SF9` es fiable con textos largos, pero con textos
  o palabras muy cortas (por ejemplo "HOLA MUNDO", apenas 9 letras) la estadística tiene
  demasiado poco material y puede equivocarse por azar. Al-Kindi combinaba el análisis de
  frecuencias con el conocimiento del idioma; aquí ese conocimiento se aporta mediante un
  diccionario embebido (`PALABRAS_COMUNES`) de palabras muy frecuentes del español
  (artículos, preposiciones, pronombres, verbos comunes, saludos, etc.).
- **Cómo lo hace:** limpia el texto con `SF7` (quita tildes de vocales) y lo pasa a
  mayúsculas; separa el texto en "palabras" agrupando caracteres alfabéticos consecutivos
  (cualquier carácter no alfabético —espacio, coma, símbolo fuera del alfabeto, etc.— corta
  la palabra); suma la **longitud** de cada palabra de 2+ letras que aparezca en
  `PALABRAS_COMUNES` (las palabras de una sola letra no se cuentan porque podrían coincidir
  por puro azar en un texto incorrecto, y se pondera por longitud para que una coincidencia
  larga —p. ej. "AMANECER"— pese mucho más que una corta y sea prácticamente imposible que
  ocurra por casualidad en un candidato equivocado).
- **Devuelve:** un entero (0 si no reconoce ninguna palabra española común).
- **Quién la usa:** `SF10`.

### SF10 (autodetección — el "cerebro" de Al-Kindi)
- **Parámetros:** `texto_cifrado` (str), `alfabeto` (str).
- **Ubicación:** `backend/src/logic.py`.
- **Qué hace:** implementa la autodetección exigida por el proyecto: sin ninguna intervención
  humana, determina si el texto fue cifrado con Atbash o con César (y con qué desplazamiento).
- **Cómo lo hace:**
  1. Genera el candidato de descifrado Atbash con `SF6`.
  2. Genera los 25 candidatos de descifrado César (desplazamientos 1 a 25) con `SF5`.
  3. Calcula, para cada uno de los 26 candidatos, su puntaje chi-cuadrado (`SF9`) y su
     puntaje de coincidencia léxica (`SF26`).
  4. Elige el candidato ganador ordenando primero por **mayor** coincidencia léxica
     (`SF26`) y, solo en caso de empate (por ejemplo, ninguna palabra reconocida en ningún
     candidato, típico de textos largos y genéricos), por **menor** chi-cuadrado (`SF9`).
     En código: `min(candidatos, key=lambda c: (-c["coincidencias"], c["puntaje"]))`.
- **Devuelve:** diccionario `{"metodo": "ATBASH"|"CESAR", "desplazamiento": int|None,
  "texto": str, "puntaje": float, "coincidencias": int}`.
- **Quién la usa:** `SF16` (endpoint de descifrado del backend). Solo el resultado de esta
  función se le muestra al usuario — es la única línea "correcta" que exige el enunciado.

---

## `backend/src/entry.py`

Punto de entrada del *Cloudflare Worker* (Python). Depende del módulo `workers`, propio del
runtime de Cloudflare, por lo que no se puede importar ni probar fuera de ese entorno; toda
la lógica de negocio pesada vive en `logic.py` (arriba) precisamente para poder probarla de
forma aislada.

### SF11
- **Parámetros:** ninguno.
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** devuelve el diccionario de cabeceras CORS (`access-control-allow-origin: *`,
  métodos y headers permitidos) que se agrega a **todas** las respuestas, ya que el frontend
  (GitHub Pages) y el backend (Cloudflare Workers) viven en dominios distintos.

### SF12
- **Parámetros:** `datos` (dict, serializable a JSON), `estado` (int, código HTTP,
  por defecto 200).
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** construye la respuesta HTTP final: serializa `datos` a JSON con
  `ensure_ascii=False` (para que caracteres especiales como chino/árabe/acentos viajen tal
  cual, en UTF-8, y no como secuencias de escape), añade las cabeceras CORS de `SF11` más
  `content-type: application/json; charset=utf-8`, y arma el objeto `Response` que exige el
  runtime de Cloudflare.

### SF13
- **Parámetros:** `request` (objeto `Request` del runtime de Cloudflare).
- **Ubicación:** `backend/src/entry.py`. Función asíncrona.
- **Qué hace:** lee el cuerpo de la petición HTTP como texto (`await request.text()`) y lo
  interpreta como JSON. Si el cuerpo viene vacío devuelve un diccionario vacío en lugar de
  fallar.

### SF14
- **Parámetros:** `payload` (dict) — se espera la clave `alfabeto`.
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** implementa la ruta `POST /api/alfabeto/validar`. Llama a `SF1` y traduce el
  resultado a la forma de respuesta HTTP: `({"valido": True, "longitud": N}, 200)` o
  `({"valido": False, "error": "..."}, 400)`.

### SF15
- **Parámetros:** `payload` (dict) — espera `alfabeto`, `metodo` ("CESAR"|"ATBASH"), `texto`
  y, si el método es César, `desplazamiento`.
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** implementa la ruta `POST /api/cifrar`. Valida el alfabeto (`SF1`) y el texto,
  y según el método invoca `SF6` (Atbash) o `SF4` (César, validando además que el
  desplazamiento sea un entero entre 1 y 25). Es el único lugar del sistema donde el usuario
  elige explícitamente el método/módulo de cifrado, tal como exige el enunciado.

### SF16
- **Parámetros:** `payload` (dict) — espera `alfabeto` y `texto` (el texto cifrado).
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** implementa la ruta `POST /api/descifrar`. Valida el alfabeto y el texto, y
  delega toda la decisión a `SF10` (autodetección de Al-Kindi). Devuelve el método detectado,
  el desplazamiento (o `None` si fue Atbash) y el texto resultante. El usuario no interviene
  en ningún punto de esta función.

### `on_fetch` (nombre reservado, no forma parte de la numeración SF)
- **Parámetros:** `request`, `env`, `ctx` (firma exigida por el runtime de Cloudflare
  Workers; el nombre `on_fetch` es obligatorio y no puede renombrarse sin romper el
  despliegue).
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** único punto de entrada HTTP del Worker. Responde `204` con cabeceras CORS
  ante peticiones `OPTIONS` (pre-flight del navegador); enruta `POST /api/alfabeto/validar`
  a `SF14`, `POST /api/cifrar` a `SF15` y `POST /api/descifrar` a `SF16`; cualquier otra
  ruta/método devuelve `404` mediante `SF12`.

---

## `front/main.js`

Lógica de interfaz. Consume la API del backend mediante `fetch`. No contiene lógica
criptográfica: todo el cifrado/descifrado/autodetección ocurre en el backend.

### `URL_API_BASE` (constante, no es función)
Dirección base del Worker de Cloudflare. Debe reemplazarse por la URL real una vez
desplegado el backend (ver `README.md`).

### SF18
- **Parámetros:** `ruta` (str, p. ej. `/api/cifrar`), `cuerpo` (objeto JS a serializar como
  JSON).
- **Ubicación:** `front/main.js`. Función asíncrona.
- **Qué hace:** helper genérico de comunicación con el backend: hace `fetch` con método
  `POST`, cabecera `content-type: application/json` y el `cuerpo` serializado; si la
  respuesta HTTP no es exitosa, lanza un `Error` con el mensaje que venga en `datos.error`.

### SF19
- **Parámetros:** `mensaje` (str), `esError` (bool).
- **Ubicación:** `front/main.js`.
- **Qué hace:** actualiza los elementos `#alphabet-error` y `#alphabet-status` del DOM según
  si el mensaje es un error o una confirmación.

### SF20
- **Parámetros:** `evento` (evento `submit` del formulario `#alphabet-form`).
- **Ubicación:** `front/main.js`. Función asíncrona.
- **Qué hace:** maneja el envío del formulario de alfabeto: evita el envío nativo del
  formulario, llama a `SF18` contra `/api/alfabeto/validar`, y si es válido guarda el
  alfabeto en la variable de módulo `SFEstadoAlfabeto` y en `localStorage` (para
  sobrevivir a recargas de página), y muestra confirmación con `SF19`. Este alfabeto
  "aplicado" es el que se usará tanto para cifrar como para descifrar, cumpliendo con que
  el conjunto de caracteres es la pauta para todo lo demás.

### SF21
- **Parámetros:** `evento` (evento `submit` del formulario `#encrypt-form`).
- **Ubicación:** `front/main.js`. Función asíncrona.
- **Qué hace:** maneja el cifrado explícito. Exige que ya exista un alfabeto aplicado; lee el
  método elegido (`#encrypt-method`) y el texto (`#encrypt-text`); si el método es César
  añade el desplazamiento (`#encrypt-shift`); llama a `SF18` contra `/api/cifrar` y muestra
  el resultado en `#encrypt-result`.

### SF22
- **Parámetros:** `evento` (evento `submit` del formulario `#decrypt-form`).
- **Ubicación:** `front/main.js`. Función asíncrona.
- **Qué hace:** maneja el descifrado automático. Exige que ya exista un alfabeto aplicado;
  envía el texto cifrado a `/api/descifrar` (sin que el usuario indique método ni
  desplazamiento) y muestra el método detectado, el desplazamiento (o "No aplica" si fue
  Atbash) y el texto descifrado — la única línea que el sistema considera correcta.

### SF23
- **Parámetros:** `idOrigen` (str, id de un elemento del DOM cuyo `textContent` se quiere
  copiar).
- **Ubicación:** `front/main.js`.
- **Qué hace:** copia al portapapeles el contenido del elemento indicado, usado por los
  botones "Copiar al portapapeles" de ambas secciones.

### SF24
- **Parámetros:** ninguno.
- **Ubicación:** `front/main.js`.
- **Qué hace:** conecta el comportamiento del selector de método de cifrado (muestra/oculta
  el campo de desplazamiento según si el método es César o Atbash) y de los botones ▲/▼ del
  stepper de desplazamiento, respetando siempre el límite 1-25.

### SF25
- **Parámetros:** ninguno.
- **Ubicación:** `front/main.js`.
- **Qué hace:** función de arranque, ejecutada en `DOMContentLoaded`. Restaura el alfabeto
  guardado en `localStorage` (si existe), y registra todos los manejadores de eventos:
  `SF20` en el formulario de alfabeto, `SF21` en el de cifrado, `SF22` en el de descifrado,
  `SF23` en ambos botones de copiar, y llama a `SF24` para inicializar el stepper.
