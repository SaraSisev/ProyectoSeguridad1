# Documentación de funciones (identificadores SF)

Este documento es la única fuente de explicación del comportamiento interno del sistema.
En el código fuente del backend (`backend/src/*.py`) y del frontend (`front/main.js`) las
funciones no llevan comentarios descriptivos: cada una está identificada únicamente con un
código `SFx`. Este archivo describe, para cada identificador, qué hace, qué parámetros
recibe, dónde está ubicado y cómo funciona internamente.

## Organización del backend

El backend está dividido en un archivo por responsabilidad, sin más archivos de los
necesarios:

```
backend/src/
  alfabeto.py             -> validación del alfabeto y utilidades de índices/desplazamiento
  cifrado.py               -> las dos operaciones de cifrado: César y Atbash
  descifrado.py            -> César inverso + la autodetección automática (orquesta todo)
  analisis_frecuencia.py   -> el motor de Al-Kindi: corpus propio, frecuencias, puntuación
  entry.py                 -> punto de entrada del Worker de Cloudflare (rutas HTTP, CORS)
```

`alfabeto.py`, `cifrado.py`, `descifrado.py` y `analisis_frecuencia.py` son Python puro (sin
dependencias del runtime de Cloudflare), por lo que pueden importarse y probarse de forma
aislada. Solo `entry.py` depende del módulo `workers`, propio de Cloudflare.

## Fundamento criptográfico (Al-Kindi)

El descifrado automático (sin intervención humana) se basa en el **análisis de frecuencias**,
técnica de criptoanálisis descrita por primera vez por **Abū Yūsuf Ya'qūb ibn Isḥāq al-Kindī**
(أبو يوسف يعقوب بن إسحاق الكندي) en su tratado *Risāla fī Istikhrāj al-Muʿammā* (siglo IX). El
método original de Al-Kindi no consistía en memorizar una tabla de frecuencias ajena, sino en
**analizar un cuerpo de texto real** del idioma para derivar empíricamente con qué frecuencia
aparece cada letra. Por eso, en `analisis_frecuencia.py`, la tabla de frecuencias del español
**no está copiada de ninguna fuente**: se calcula en tiempo de importación a partir de un
corpus de texto en español escrito específicamente para este proyecto (`CORPUS_REFERENCIA`),
contando letra por letra igual que habría hecho Al-Kindi con un texto real.

Como César y Atbash son cifrados de sustitución monoalfabética, la distribución de
frecuencias del idioma se conserva "desplazada" o "invertida" en el texto cifrado. El sistema
prueba todas las hipótesis posibles (Atbash + los 25 desplazamientos César) y se queda con la
que más se parece al español real, combinando dos señales:

1. **Estadística de letras** (`SF10`): qué tan cercana es la distribución de letras del
   candidato a `FREC_ESPANOL` (estadístico chi-cuadrado).
2. **Reconocimiento léxico** (`SF11`): cuántas palabras españolas reconocibles contiene el
   candidato, usando un pequeño diccionario embebido (`PALABRAS_COMUNES`). Esta señal es
   necesaria porque con textos muy cortos (por ejemplo una sola palabra) la estadística por sí
   sola no tiene suficiente material para ser confiable.

Por diseño, solo se le muestra al usuario la línea descifrada ganadora: el usuario nunca elige
entre candidatos.

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
- `DESPLAZAMIENTO_MIN = 1`, `DESPLAZAMIENTO_MAX = 25`: rango permitido para el desplazamiento
  César.

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
- **Quién la usa:** `SF15`, `SF16`, `SF17` (en `entry.py`) antes de cualquier operación de
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
- **Quién la usa:** `SF16` en `entry.py` cuando el usuario elige el método "CESAR".

### SF5 (Atbash — cifra y descifra, es autoinverso)
- **Parámetros:** `texto` (str), `alfabeto` (str).
- **Ubicación:** `backend/src/cifrado.py`.
- **Qué hace:** aplica la transformación Atbash: cada carácter se reemplaza por el que ocupa
  la posición simétrica del alfabeto (`longitud - 1 - posición`). Al ser una involución
  (aplicarla dos veces devuelve el texto original), la misma función sirve para cifrar y para
  descifrar; no existe una función Atbash separada en `descifrado.py` porque sería código
  duplicado.
- **Quién la usa:** `SF16` en `entry.py` cuando el usuario elige "ATBASH" para cifrar, y
  `SF7` en `descifrado.py`, que la importa para generar el candidato Atbash durante la
  autodetección.

---

## `backend/src/descifrado.py`

Importa `SF2`, `SF3` y las constantes de `alfabeto.py`; importa `SF5` de `cifrado.py`; importa
`SF10` y `SF11` de `analisis_frecuencia.py`.

### SF6 (César — descifrar)
- **Parámetros:** `texto` (str), `alfabeto` (str), `desplazamiento` (int, 1-25).
- **Ubicación:** `backend/src/descifrado.py`.
- **Qué hace:** operación inversa de `SF4`: resta el desplazamiento en vez de sumarlo (mismo
  criterio de "pasar por alto" los caracteres fuera del alfabeto).
- **Quién la usa:** `SF7`, que la invoca 25 veces (una por cada desplazamiento posible) para
  generar los candidatos que luego se puntúan con `SF10`/`SF11`.

### SF7 (autodetección — el "cerebro" de Al-Kindi)
- **Parámetros:** `texto_cifrado` (str), `alfabeto` (str).
- **Ubicación:** `backend/src/descifrado.py`.
- **Qué hace:** implementa la autodetección exigida por el proyecto: sin ninguna intervención
  humana, determina si el texto fue cifrado con Atbash o con César (y con qué desplazamiento).
- **Cómo lo hace:**
  1. Genera el candidato de descifrado Atbash con `SF5` (de `cifrado.py`).
  2. Genera los 25 candidatos de descifrado César (desplazamientos 1 a 25) con `SF6`.
  3. Calcula, para cada uno de los 26 candidatos, su puntaje chi-cuadrado (`SF10`) y su
     puntaje de coincidencia léxica (`SF11`), ambos de `analisis_frecuencia.py`.
  4. Elige el candidato ganador ordenando primero por **mayor** coincidencia léxica y, solo
     en caso de empate (por ejemplo, ninguna palabra reconocida en ningún candidato, típico
     de textos largos y genéricos), por **menor** chi-cuadrado. En código:
     `min(candidatos, key=lambda c: (-c["coincidencias"], c["puntaje"]))`.
- **Devuelve:** diccionario `{"metodo": "ATBASH"|"CESAR", "desplazamiento": int|None,
  "texto": str, "puntaje": float, "coincidencias": int}`.
- **Quién la usa:** `SF17` (en `entry.py`). Solo el resultado de esta función se le muestra al
  usuario — es la única línea "correcta" que exige el enunciado.

---

## `backend/src/analisis_frecuencia.py`

El motor de Al-Kindi. No depende de ningún otro archivo del proyecto.

### `CORPUS_REFERENCIA` (constante, no es función)
Texto en español de varios párrafos, **escrito específicamente para este proyecto** (no
copiado de ninguna fuente externa), usado para derivar empíricamente la frecuencia de cada
letra — el mismo principio que usó Al-Kindi: analizar texto real en vez de citar una tabla.
Se escribió con vocabulario variado a propósito para que aparezcan también las letras menos
frecuentes del español (`k`, `w`, `x`, `z`, `j`, `ñ`, `q`, etc.) y la muestra sea razonable.

### `PALABRAS_COMUNES` (constante, no es función)
Conjunto de palabras muy frecuentes del español (artículos, preposiciones, pronombres, verbos
comunes, saludos, sin tildes y en mayúsculas) usado por `SF11` como segunda señal de
detección, complementaria al análisis estadístico de `SF10`.

### SF8
- **Parámetros:** `texto` (str).
- **Ubicación:** `backend/src/analisis_frecuencia.py`.
- **Qué hace:** normaliza vocales acentuadas a su forma base (á→a, é→e, í→i, ó→o, ú→u, ü→u,
  incluyendo mayúsculas) usando una tabla de traducción (`TABLA_ACENTOS`). **No** afecta la
  letra `ñ` (se preserva tal cual porque es una letra distinta en el alfabeto español, con su
  propia frecuencia).
- **Por qué existe:** el análisis de frecuencias debe contar "e" y "é" como la misma letra
  estadística; esta función solo se usa para esa cuenta, nunca para el texto que finalmente
  se le muestra al usuario.
- **Quién la usa:** `SF9`, `SF11`.

### SF9
- **Parámetros:** `texto` (str).
- **Ubicación:** `backend/src/analisis_frecuencia.py`.
- **Qué hace:** cuenta cuántas veces aparece cada letra española (a-z, ñ) en el texto.
- **Cómo lo hace:** pasa el texto por `SF8` (quita tildes de vocales) y lo pone en
  minúsculas; recorre carácter por carácter y, si el carácter es una de las 27 letras del
  español, incrementa su contador y el total.
- **Devuelve:** tupla `(conteo: dict[letra, int], total: int)`.
- **Quién la usa:** se llama una vez sobre `CORPUS_REFERENCIA` al importar el módulo (para
  calcular `FREC_ESPANOL`) y luego se reutiliza dentro de `SF10` para analizar cada candidato
  de descifrado.

### `FREC_ESPANOL` (constante calculada, no hardcodeada)
Justo después de definir `SF9`, el módulo la ejecuta una vez sobre `CORPUS_REFERENCIA` y
convierte los conteos en porcentajes: `FREC_ESPANOL = {letra: (veces/total)*100 ...}`. Esta es
la tabla de frecuencias "de referencia" contra la que se compara cada candidato de descifrado;
al calcularse en código a partir de un texto propio, no reproduce ninguna tabla de una fuente
externa.

### SF10 (estadístico de "españolidad" — núcleo del método de Al-Kindi)
- **Parámetros:** `texto` (str) — un candidato de texto descifrado.
- **Ubicación:** `backend/src/analisis_frecuencia.py`.
- **Qué hace:** calcula qué tan parecida es la distribución de letras del texto a
  `FREC_ESPANOL`, mediante el estadístico **chi-cuadrado**:
  `Σ ((observado - esperado)² / esperado)` para cada letra, donde `esperado = total_letras *
  (frecuencia_esperada / 100)`. Cuanto **menor** el valor, más se parece el texto al español
  de referencia.
- **Caso especial:** si el texto no contiene ninguna letra española reconocible (`total == 0`),
  se devuelve `float("inf")` para que ese candidato nunca gane la comparación.
- **Quién la usa:** `SF7` (en `descifrado.py`), para comparar los 26 candidatos posibles.

### SF11 (segunda señal: coincidencia léxica)
- **Parámetros:** `texto` (str) — un candidato de texto descifrado.
- **Ubicación:** `backend/src/analisis_frecuencia.py`.
- **Por qué existe:** el chi-cuadrado de `SF10` es fiable con textos largos, pero con textos o
  palabras muy cortas la estadística tiene demasiado poco material y puede equivocarse por
  azar. Al-Kindi combinaba el análisis de frecuencias con el conocimiento del idioma; aquí ese
  conocimiento se aporta mediante `PALABRAS_COMUNES`.
- **Cómo lo hace:** limpia el texto con `SF8` (quita tildes de vocales) y lo pasa a
  mayúsculas; separa el texto en "palabras" agrupando caracteres alfabéticos consecutivos
  (cualquier carácter no alfabético —espacio, coma, símbolo fuera del alfabeto, etc.— corta
  la palabra); suma la **longitud** de cada palabra de 2+ letras que aparezca en
  `PALABRAS_COMUNES` (las palabras de una sola letra no se cuentan porque podrían coincidir
  por puro azar, y se pondera por longitud para que una coincidencia larga pese mucho más que
  una corta y sea prácticamente imposible que ocurra por casualidad en un candidato
  equivocado).
- **Devuelve:** un entero (0 si no reconoce ninguna palabra española común).
- **Quién la usa:** `SF7`.

---

## `backend/src/entry.py`

Punto de entrada del *Cloudflare Worker* (Python). Depende del módulo `workers`, propio del
runtime de Cloudflare, por lo que no se puede importar ni probar fuera de ese entorno; toda la
lógica de negocio vive en los cuatro archivos anteriores, precisamente para poder probarla de
forma aislada.

### SF12
- **Parámetros:** ninguno.
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** devuelve el diccionario de cabeceras CORS (`access-control-allow-origin: *`,
  métodos y headers permitidos) que se agrega a **todas** las respuestas, ya que el frontend
  (GitHub Pages) y el backend (Cloudflare Workers) viven en dominios distintos.

### SF13
- **Parámetros:** `datos` (dict, serializable a JSON), `estado` (int, código HTTP,
  por defecto 200).
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** construye la respuesta HTTP final: serializa `datos` a JSON con
  `ensure_ascii=False` (para que caracteres especiales como chino/árabe/jeroglíficos/acentos
  viajen tal cual, en UTF-8, y no como secuencias de escape), añade las cabeceras CORS de
  `SF12` más `content-type: application/json; charset=utf-8`, y arma el objeto `Response` que
  exige el runtime de Cloudflare.

### SF14
- **Parámetros:** `request` (objeto `Request` del runtime de Cloudflare).
- **Ubicación:** `backend/src/entry.py`. Función asíncrona.
- **Qué hace:** lee el cuerpo de la petición HTTP como texto (`await request.text()`) y lo
  interpreta como JSON. Si el cuerpo viene vacío devuelve un diccionario vacío en lugar de
  fallar.

### SF15
- **Parámetros:** `payload` (dict) — se espera la clave `alfabeto`.
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** implementa la ruta `POST /api/alfabeto/validar`. Llama a `SF1` (de
  `alfabeto.py`) y traduce el resultado a la forma de respuesta HTTP: `({"valido": True,
  "longitud": N}, 200)` o `({"valido": False, "error": "..."}, 400)`.

### SF16
- **Parámetros:** `payload` (dict) — espera `alfabeto`, `metodo` ("CESAR"|"ATBASH"), `texto`
  y, si el método es César, `desplazamiento`.
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** implementa la ruta `POST /api/cifrar`. Valida el alfabeto (`SF1`) y el texto,
  y según el método invoca `SF5` (Atbash, de `cifrado.py`) o `SF4` (César, de `cifrado.py`,
  validando además que el desplazamiento sea un entero entre 1 y 25). Es el único lugar del
  sistema donde el usuario elige explícitamente el método/módulo de cifrado, tal como exige
  el enunciado.

### SF17
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
  a `SF15`, `POST /api/cifrar` a `SF16` y `POST /api/descifrar` a `SF17`; cualquier otra
  ruta/método devuelve `404` mediante `SF13`.

---

## `front/main.js`

Lógica de interfaz. Consume la API del backend mediante `fetch`. No contiene lógica
criptográfica: todo el cifrado/descifrado/autodetección ocurre en el backend.

### `URL_API_BASE` (constante, no es función)
Dirección base del backend. Si la página se abre desde `localhost`/`127.0.0.1` (pruebas
locales) apunta automáticamente a `http://127.0.0.1:8787`; en cualquier otro dominio (por
ejemplo GitHub Pages) usa la URL de producción del Worker de Cloudflare, que debe
reemplazarse una vez desplegado (ver `README.md`).

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
  alfabeto en la variable de módulo `SFEstadoAlfabeto` y en `localStorage` (para sobrevivir a
  recargas de página), y muestra confirmación con `SF19`. Este alfabeto "aplicado" es el que
  se usará tanto para cifrar como para descifrar.

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
