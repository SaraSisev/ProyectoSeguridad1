# Documentación de funciones (identificadores SF)

Este documento es la única fuente de explicación del comportamiento interno del sistema.
En el código fuente del backend (`backend/src/*.py`) y del frontend (`front/main.js`) las
funciones no llevan comentarios descriptivos: cada una está identificada únicamente con un
código `SFx`, **único en todo el proyecto** (no se repite entre archivos). Este documento
describe, para cada identificador, qué hace, qué parámetros recibe, dónde está ubicado y cómo
funciona internamente.

## Organización del backend

```
backend/src/
  alfabeto.py             -> validación del alfabeto y utilidades de índices/desplazamiento
  cifrado.py               -> las dos operaciones de cifrado: César y Atbash
  descifrado.py            -> César inverso + la autodetección automática (orquesta todo)
  datos_espanol.py         -> datos del idioma: corpus propio, frecuencias, n-gramas, diccionario
  analisis_frecuencia.py   -> el motor de Al-Kindi: calcula y combina los puntajes
  entry.py                 -> punto de entrada del Worker de Cloudflare (rutas HTTP, CORS)
```

Todos salvo `entry.py` son Python puro (sin dependencias del runtime de Cloudflare), por lo
que pueden importarse y probarse de forma aislada. Solo `entry.py` depende del módulo
`workers`, propio de Cloudflare.

## Fundamento criptográfico (Al-Kindi)

El descifrado automático (sin intervención humana) se basa en el **análisis de frecuencias**,
técnica de criptoanálisis descrita por primera vez por **Abū Yūsuf Ya'qūb ibn Isḥāq al-Kindī**
(أبو يوسف يعقوب بن إسحاق الكندي) en su tratado *Risāla fī Istikhrāj al-Muʿammā* (siglo IX).
Al-Kindi no memorizaba una tabla de frecuencias ajena: analizaba texto real del idioma para
derivar empíricamente sus patrones. Siguiendo ese mismo principio, **todos los datos
lingüísticos de este proyecto** (`datos_espanol.py`) se calculan a partir de un corpus de
texto en español **escrito específicamente para este proyecto** (`CORPUS_REFERENCIA`), nunca
copiados de una tabla externa.

### Cómo se decide el descifrado correcto

El sistema **descifra el texto con las 26 claves posibles** (Atbash + los 25 desplazamientos
César), calcula un **único puntaje numérico** para cada una de las 26 soluciones candidatas
(`SF22`), y se queda con la que obtiene el **valor más alto**
(`max(candidatos, key=lambda c: c["analisis"]["total"])`, en `SF7`). Un solo número por
candidato, gana el mayor — sin reglas de desempate en cascada.

Ese número combina **nueve componentes independientes**, cada uno midiendo una propiedad
distinta de lo que hace que un texto "se vea como español real". Se suman entre sí (las
penalizaciones se restan) porque cada componente aporta evidencia independiente: cuantos más
componentes den una señal positiva, más confianza hay en que ese candidato es el texto
original.

| Componente | Función | Qué mide |
|---|---|---|
| Frecuencia de letras | `SF13` | ¿La mezcla de letras se parece a la del español? (chi-cuadrado) |
| Palabras del diccionario | `SF14` | ¿Aparecen palabras reales del español, y qué tan comunes son? |
| Bigramas | `SF15` + `PESOS_BIGRAMAS` | ¿Aparecen combinaciones de 2 letras típicas del español ("de", "en", "ar"...)? |
| Trigramas | `SF15` + `PESOS_TRIGRAMAS` | Lo mismo, con combinaciones de 3 letras ("que", "con", "ado"...) |
| Tetragramas | `SF15` + `PESOS_TETRAGRAMAS` | Lo mismo, con combinaciones de 4 letras ("para", "ente"...) |
| Prefijos | `SF16` | ¿Las palabras empiezan con prefijos típicos del español ("des-", "con-"...)? |
| Sufijos | `SF17` | ¿Las palabras terminan en sufijos típicos ("-mente", "-ando", "-idad"...)? |
| Proporción de vocales | `SF19` | ¿La proporción vocales/consonantes es la típica del español? |
| Estructura de palabra | `SF21` | ¿Las palabras tienen forma razonable (no son cadenas de puras consonantes, ni tienen letras repetidas 4+ veces)? |
| Secuencias improbables (penalización) | `SF18` | ¿Aparecen combinaciones casi imposibles en español ("qq", "jj", "wq"...)? |

### De dónde sale cada dato (nada citado de internet)

- **`FRECUENCIA_LETRAS`, `PESOS_BIGRAMAS`, `PESOS_TRIGRAMAS`, `PESOS_TETRAGRAMAS`,
  `RATIO_VOCALES_OBJETIVO`**: se calculan contando directamente sobre `CORPUS_REFERENCIA`
  (ver `SF10`, `SF11`, `SF12` en `datos_espanol.py`). Si alguien cambia el corpus, estos
  números se recalculan solos la próxima vez que se importa el módulo — no son constantes
  copiadas, son el resultado de un cálculo sobre texto propio.
- **`PALABRAS_MUY_COMUNES` y `PALABRAS_COMUNES_BASE`**: lista de palabras gramaticales del
  español escrita a mano (artículos, preposiciones, pronombres, verbos auxiliares); es
  conocimiento básico del idioma, no un dataset de una fuente específica. `PALABRAS_COMUNES`
  final añade además, automáticamente, todas las palabras distintas que aparecen en
  `CORPUS_REFERENCIA`.
- **`PESOS_PREFIJOS`, `PESOS_SUFIJOS`, `PESOS_SECUENCIAS_IMPROBABLES`**: reglas generales de
  formación de palabras y de ortografía del español (por ejemplo, que "-mente" forma
  adverbios, o que "qq"/"jj" no existen en español), escritas a mano por ser conocimiento
  general del idioma, igual que uno "sabe" que en inglés "-ing" es un sufijo común sin
  necesitar citar una fuente.

### Límite honesto del método (léelo si algo "no acierta")

El análisis de frecuencias necesita que una parte razonable del mensaje haya sido realmente
sustituida por el cifrado. Si el alfabeto que el usuario define **no incluye** las letras
españolas comunes que aparecen en su texto, la mayor parte del mensaje pasa sin cifrar (tal
como exige el enunciado: los caracteres fuera del alfabeto se "pasan por alto"). Con muy pocos
caracteres realmente cifrados, ningún método automático — ni tampoco un humano — puede
garantizar recuperar la clave real entre las 26 hipótesis posibles. Para resultados fiables,
el alfabeto debe incluir las letras del español que realmente se van a usar en el texto a
cifrar.

---

## `backend/src/alfabeto.py`

### Constantes
- `LIMITE_ALFABETO = 256`: máximo de caracteres distintos del alfabeto. El frontend usa el
  mismo número (`LIMITE_ALFABETO` en `main.js`, `maxlength="256"` en el HTML).
- `DESPLAZAMIENTO_MIN = 1`, `DESPLAZAMIENTO_MAX = 25`: rango del desplazamiento César, igual
  que los atributos `min`/`max` del campo de desplazamiento en `front/index.html`.

### SF1
- **Parámetros:** `alfabeto` (str).
- **Ubicación:** `backend/src/alfabeto.py`.
- **Qué hace:** valida que el alfabeto sea utilizable: cadena no vacía, máximo 256
  caracteres, sin repetidos, al menos 2 caracteres distintos.
- **Cómo lo hace:** convierte la cadena en lista de caracteres Unicode (cada carácter, sea
  ASCII, chino, árabe, un jeroglífico, etc., cuenta como un solo elemento porque Python 3
  itera por punto de código completo) y compara `len(lista)` contra `len(set(lista))`.
- **Devuelve:** tupla `(valido: bool, mensaje_error: str)`.
- **Quién la usa:** `SF26`, `SF27`, `SF28` (en `entry.py`).

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
- **Quién la usa:** `SF27` en `entry.py`.

### SF5 (Atbash — cifra y descifra, es autoinverso)
- **Parámetros:** `texto` (str), `alfabeto` (str).
- **Ubicación:** `backend/src/cifrado.py`.
- **Qué hace:** cada carácter se reemplaza por el simétrico del alfabeto
  (`longitud - 1 - posición`). Al ser una involución, sirve para cifrar y descifrar con la
  misma función.
- **Quién la usa:** `SF27` en `entry.py` (cifrar) y `SF7` en `descifrado.py` (candidato Atbash
  durante la autodetección).

---

## `backend/src/descifrado.py`

Importa `SF2`, `SF3` y constantes de `alfabeto.py`; `SF5` de `cifrado.py`; `SF22` de
`analisis_frecuencia.py`.

### SF6 (César — descifrar)
- **Parámetros:** `texto` (str), `alfabeto` (str), `desplazamiento` (int, 1-25).
- **Ubicación:** `backend/src/descifrado.py`.
- **Qué hace:** inversa de `SF4`: resta el desplazamiento en vez de sumarlo.
- **Quién la usa:** `SF7`, 25 veces (una por desplazamiento).

### SF7 (autodetección — el "cerebro" de Al-Kindi)
- **Parámetros:** `texto_cifrado` (str), `alfabeto` (str).
- **Ubicación:** `backend/src/descifrado.py`.
- **Qué hace:** determina, sin intervención humana, si el texto fue cifrado con Atbash o
  César (y con qué desplazamiento).
- **Cómo lo hace:** genera el candidato Atbash (`SF5`) y los 25 candidatos César (`SF6`);
  calcula el análisis multi-componente completo de cada uno con `SF22`; elige el de mayor
  `analisis["total"]` con `max(...)`.
- **Devuelve:** `{"metodo": "ATBASH"|"CESAR", "desplazamiento": int|None, "texto": str,
  "analisis": {"total": float, "componentes": {...}, "ratio_vocales": float,
  "num_palabras": int}}`.
- **Quién la usa:** `SF28` (en `entry.py`), que solo expone al usuario `metodo`,
  `desplazamiento` y `texto` — la única línea "correcta" que exige el enunciado.

---

## `backend/src/datos_espanol.py`

Todos los datos del idioma español que usa el motor de análisis. No depende de ningún otro
archivo del proyecto.

### `CORPUS_REFERENCIA` (constante)
Texto en español de varios párrafos, escrito específicamente para este proyecto, usado para
derivar **todos** los datos de abajo. Tiene vocabulario variado a propósito (para que
aparezcan letras poco frecuentes como `k`, `w`, `x`, `z`, `j`, `ñ`, `q`) y nutre también el
diccionario con sustantivos y verbos reales, no solo palabras gramaticales.

### `LETRAS_ESPANOL`, `VOCALES`, `PATRON_PALABRA` (constantes)
El alfabeto español en minúsculas, el conjunto de vocales (con tilde), y la expresión regular
`[a-zñ]+` usada para separar palabras.

### SF8
- **Parámetros:** `texto` (str).
- **Ubicación:** `backend/src/datos_espanol.py`.
- **Qué hace:** normaliza el texto para el análisis: lo pasa a minúsculas y sustituye vocales
  acentuadas por su forma base (á→a, é→e, í→i, ó→o, ú→u, ü→u). No toca la `ñ` (letra distinta,
  con su propia frecuencia). Nunca se usa para el texto que ve el usuario, solo para análisis
  interno.
- **Quién la usa:** internamente en este módulo (para construir todos los datos derivados del
  corpus) y en `analisis_frecuencia.py` (`SF22`) para normalizar cada candidato.

### SF9
- **Parámetros:** `texto_normalizado` (str, ya pasado por `SF8`).
- **Ubicación:** `backend/src/datos_espanol.py`.
- **Qué hace:** separa el texto en palabras usando `PATRON_PALABRA` (agrupa letras
  consecutivas; cualquier otro carácter corta la palabra).
- **Quién la usa:** para construir `PALABRAS_COMUNES` a partir del corpus, y en
  `analisis_frecuencia.py` (`SF22`) para obtener las palabras de cada candidato.

### SF10
- **Parámetros:** `texto_normalizado` (str).
- **Ubicación:** `backend/src/datos_espanol.py`.
- **Qué hace:** cuenta cuántas veces aparece cada letra española en el texto (incluye las 27
  letras con conteo 0 si no aparecen, para que ninguna falte del diccionario resultante).
- **Devuelve:** `Counter` (subclase de dict).
- **Quién la usa:** una sola vez, sobre `CORPUS_REFERENCIA`, para calcular `FRECUENCIA_LETRAS`
  y `RATIO_VOCALES_OBJETIVO`.

### SF11
- **Parámetros:** `texto_normalizado` (str), `n` (int, tamaño del n-grama: 2, 3 o 4).
- **Ubicación:** `backend/src/datos_espanol.py`.
- **Qué hace:** cuenta cuántas veces aparece cada secuencia contigua de `n` letras (ventana
  deslizante), descartando cualquier fragmento que contenga un carácter que no sea una letra
  española (para no mezclar fragmentos que crucen espacios o signos de puntuación).
- **Devuelve:** `Counter` de n-gramas.
- **Quién la usa:** `SF12`.

### SF12
- **Parámetros:** `texto_normalizado` (str), `n` (int), `peso_maximo` (float), 
  `minimo_apariciones` (int).
- **Ubicación:** `backend/src/datos_espanol.py`.
- **Qué hace:** construye una tabla de pesos para n-gramas: cuenta con `SF11`, descarta los
  que aparecen menos de `minimo_apariciones` veces (para no incluir ruido estadístico de un
  corpus pequeño) y escala el conteo del más frecuente restante a `peso_maximo` (los demás en
  proporción).
- **Devuelve:** `dict[ngrama, peso]`.
- **Quién la usa:** para construir `PESOS_BIGRAMAS` (n=2, peso máx. 1.20, mínimo 4
  apariciones), `PESOS_TRIGRAMAS` (n=3, peso máx. 1.80, mínimo 3) y `PESOS_TETRAGRAMAS` (n=4,
  peso máx. 2.20, mínimo 2) — todos calculados sobre `CORPUS_REFERENCIA` al importar el
  módulo.

### Constantes calculadas del corpus
- `FRECUENCIA_LETRAS`: porcentaje de cada letra española en `CORPUS_REFERENCIA` (via `SF10`).
- `RATIO_VOCALES_OBJETIVO`, `RATIO_VOCALES_MIN` (objetivo − 0.20), `RATIO_VOCALES_MAX`
  (objetivo + 0.20): proporción real de vocales sobre el total de letras del corpus, con un
  margen de tolerancia de ±0.20 alrededor de ese valor.
- `PESOS_BIGRAMAS`, `PESOS_TRIGRAMAS`, `PESOS_TETRAGRAMAS`: ver `SF12`.
- `PALABRAS_COMUNES = PALABRAS_COMUNES_BASE | palabras_del_corpus`: más de 400 palabras.

### Constantes escritas a mano (conocimiento general del idioma)
- `PALABRAS_MUY_COMUNES`: las ~20 palabras gramaticales más frecuentes del español (de, la,
  que, el, en, y, a, los...).
- `PALABRAS_COMUNES_BASE`: un conjunto más amplio de palabras gramaticales y verbos/adjetivos
  comunes.
- `PESOS_PREFIJOS`: prefijos españoles típicos (des-, pre-, re-, in-, con-, com-, pro-, sub-,
  inter-, anti-) con un peso relativo.
- `PESOS_SUFIJOS`: sufijos españoles típicos (-mente, -ción, -idad, -ando, -iendo, -ado,
  -oso/a, -able/ible, -ar/-er/-ir) con un peso relativo.
- `PESOS_SECUENCIAS_IMPROBABLES`: combinaciones de letras casi inexistentes en español (jj,
  kk, ww, qq, zx, xq...) con una penalización.
- `LONGITUD_PALABRA_MAX_RAZONABLE = 18`: longitud a partir de la cual una "palabra" empieza a
  penalizarse por ser sospechosamente larga.

---

## `backend/src/analisis_frecuencia.py`

El motor de puntuación. Importa de `datos_espanol.py` todo lo que necesita.

### SF13 (frecuencia de letras)
- **Parámetros:** `texto_normalizado` (str).
- **Ubicación:** `backend/src/analisis_frecuencia.py`.
- **Qué hace:** mide qué tan parecida es la mezcla de letras del candidato a
  `FRECUENCIA_LETRAS`, con el estadístico chi-cuadrado clásico:
  `Σ (observado - esperado)² / esperado`, normalizado entre el total de letras y convertido a
  un puntaje acotado con `35 / (1 + chi_cuadrado_normalizado)`. Cuanto más se parezca la
  distribución, más cerca de 35; cuanto más se aleje, más cerca de 0.
- **Caso especial:** sin letras españolas reconocibles, devuelve `-20.0` (penaliza fuerte:
  un candidato sin ninguna letra española no puede ser texto en español).
- **Quién la usa:** `SF22`.

### SF14 (palabras del diccionario)
- **Parámetros:** `palabras` (list[str]).
- **Ubicación:** `backend/src/analisis_frecuencia.py`.
- **Qué hace:** recorre las palabras del candidato; si una palabra está en
  `PALABRAS_MUY_COMUNES` suma `3.0 + min(longitud, 8) * 0.80`; si está en `PALABRAS_COMUNES`
  suma `1.5 + min(longitud, 8) * 0.50`. Las palabras muy comunes (artículos, preposiciones)
  valen más porque su aparición es un indicio fortísimo de español real; las palabras comunes
  valen algo menos. Ambas ganan un poco más de puntaje cuanto más largas son (hasta 8 letras),
  porque una coincidencia larga es más difícil que ocurra por azar.
- **Quién la usa:** `SF22`.

### SF15 (patrones — bigramas, trigramas y tetragramas)
- **Parámetros:** `texto_normalizado` (str), `tabla_pesos` (dict, una de `PESOS_BIGRAMAS`,
  `PESOS_TRIGRAMAS` o `PESOS_TETRAGRAMAS`).
- **Ubicación:** `backend/src/analisis_frecuencia.py`.
- **Qué hace:** función genérica reutilizada tres veces (una por tamaño de n-grama): para cada
  patrón de la tabla, cuenta cuántas veces aparece como subcadena en el texto
  (`texto.count(patron)`) y suma `apariciones * peso`.
- **Quién la usa:** `SF22`, una vez con cada una de las tres tablas.

### SF16 (prefijos)
- **Parámetros:** `palabras` (list[str]).
- **Ubicación:** `backend/src/analisis_frecuencia.py`.
- **Qué hace:** para cada palabra, revisa si empieza con alguno de `PESOS_PREFIJOS`
  (exigiendo que la palabra sea al menos 2 letras más larga que el prefijo, para no contar
  palabras que son *solo* el prefijo) y suma el peso correspondiente.
- **Quién la usa:** `SF22`.

### SF17 (sufijos)
- **Parámetros:** `palabras` (list[str]).
- **Ubicación:** `backend/src/analisis_frecuencia.py`.
- **Qué hace:** simétrico a `SF16` pero con `PESOS_SUFIJOS` y `endswith`.
- **Quién la usa:** `SF22`.

### SF18 (penalización de secuencias improbables)
- **Parámetros:** `texto_normalizado` (str).
- **Ubicación:** `backend/src/analisis_frecuencia.py`.
- **Qué hace:** para cada secuencia de `PESOS_SECUENCIAS_IMPROBABLES`, cuenta apariciones y
  acumula la penalización. Se resta (no se suma) al puntaje total en `SF22`.
- **Quién la usa:** `SF22`.

### SF19 (proporción de vocales)
- **Parámetros:** `texto_normalizado` (str).
- **Ubicación:** `backend/src/analisis_frecuencia.py`.
- **Qué hace:** calcula la proporción de vocales sobre el total de letras del candidato y la
  compara con `RATIO_VOCALES_OBJETIVO`: `puntaje = 12.0 - |ratio - objetivo| * 40`; si la
  proporción se sale del rango razonable (`RATIO_VOCALES_MIN`/`MAX`), resta 8 puntos extra
  (penaliza candidatos con casi solo consonantes o casi solo vocales, típicos de una clave
  incorrecta).
- **Devuelve:** tupla `(puntaje: float, ratio: float)`.
- **Caso especial:** sin letras, devuelve `(-20.0, 0.0)`.
- **Quién la usa:** `SF22`.

### SF20 (secuencia de consonantes más larga — auxiliar)
- **Parámetros:** `palabra` (str).
- **Ubicación:** `backend/src/analisis_frecuencia.py`.
- **Qué hace:** recorre la palabra letra por letra llevando la racha actual de consonantes
  seguidas (se reinicia en cada vocal) y devuelve la racha más larga encontrada.
- **Quién la usa:** `SF21`.

### SF21 (estructura de palabra)
- **Parámetros:** `palabras` (list[str]).
- **Ubicación:** `backend/src/analisis_frecuencia.py`.
- **Qué hace:** puntúa qué tan "plausibles" son las palabras del candidato como palabras
  reales: suma un pequeño bono por tener varias palabras (`min(num_palabras, 6) * 0.50`), y
  penaliza por cada palabra que sea sospechosamente larga (más de
  `LONGITUD_PALABRA_MAX_RAZONABLE`), que no tenga ninguna vocal, que tenga una racha de 5+
  consonantes seguidas (`SF20`), o que repita el mismo carácter 4 o más veces seguidas (por
  ejemplo "aaaa"), algo virtualmente inexistente en español real.
- **Caso especial:** sin palabras (candidato vacío), devuelve `-15.0`.
- **Quién la usa:** `SF22`.

### SF22 (puntaje total — el número que decide todo)
- **Parámetros:** `texto` (str) — un candidato completo de texto descifrado.
- **Ubicación:** `backend/src/analisis_frecuencia.py`.
- **Qué hace:** normaliza el texto (`SF8`) y lo separa en palabras (`SF9`); calcula los nueve
  componentes (`SF13` a `SF21`) y los suma en un único total: `frecuencia + comunes +
  bigramas + trigramas + tetragramas + prefijos + sufijos + vocales + estructura -
  penalizacion`.
- **Devuelve:** `{"total": float, "componentes": {...cada uno por separado, útil para
  depurar...}, "ratio_vocales": float, "num_palabras": int}`.
- **Por qué así:** el pedido original era exactamente esto — descifrar con las 26 claves
  posibles y quedarse con la de **mayor valor**. Al ser una sola suma, `SF7` puede usar
  `max()` directamente sobre `analisis["total"]` de los 26 candidatos, sin reglas de
  desempate adicionales.
- **Quién la usa:** `SF7` (en `descifrado.py`).

---

## `backend/src/entry.py`

Punto de entrada del *Cloudflare Worker* (Python). Depende del módulo `workers`, propio del
runtime de Cloudflare, por lo que no se puede importar ni probar fuera de ese entorno; toda la
lógica de negocio vive en los cinco archivos anteriores, precisamente para poder probarla de
forma aislada.

### SF23
- **Parámetros:** ninguno.
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** devuelve las cabeceras CORS (`access-control-allow-origin: *`, métodos y
  headers permitidos) que se agregan a **todas** las respuestas, ya que el frontend (GitHub
  Pages) y el backend (Cloudflare Workers) viven en dominios distintos.

### SF24
- **Parámetros:** `datos` (dict), `estado` (int, por defecto 200).
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** construye la respuesta HTTP: serializa `datos` a JSON con
  `ensure_ascii=False` (para que chino/árabe/jeroglíficos/acentos viajen tal cual, en UTF-8),
  añade las cabeceras de `SF23` más `content-type: application/json; charset=utf-8`.

### SF25
- **Parámetros:** `request` (objeto `Request` de Cloudflare). Función asíncrona.
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** lee el cuerpo como texto y lo interpreta como JSON; si viene vacío, devuelve
  un diccionario vacío.

### SF26
- **Parámetros:** `payload` (dict, espera `alfabeto`).
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** implementa `POST /api/alfabeto/validar` llamando a `SF1`.

### SF27
- **Parámetros:** `payload` (dict, espera `alfabeto`, `metodo`, `texto`, y
  `desplazamiento` si el método es César).
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** implementa `POST /api/cifrar`: valida con `SF1`, invoca `SF5` (Atbash) o `SF4`
  (César, validando el desplazamiento). Único lugar donde el usuario elige el método de
  cifrado, tal como exige el enunciado.

### SF28
- **Parámetros:** `payload` (dict, espera `alfabeto` y `texto`).
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** implementa `POST /api/descifrar`: valida con `SF1` y delega toda la decisión
  a `SF7`. El usuario no interviene en ningún punto.

### `on_fetch` (nombre reservado, no forma parte de la numeración SF)
- **Parámetros:** `request`, `env`, `ctx` (firma exigida por Cloudflare; el nombre es
  obligatorio).
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** único punto de entrada HTTP. Responde `204` a `OPTIONS` (pre-flight CORS);
  enruta `POST /api/alfabeto/validar` a `SF26`, `POST /api/cifrar` a `SF27` y
  `POST /api/descifrar` a `SF28`; cualquier otra ruta devuelve `404`.

---

## `front/main.js`

Lógica de interfaz. Consume la API del backend mediante `fetch`. No contiene lógica
criptográfica: todo el cifrado/descifrado/autodetección ocurre en el backend.

### `URL_API_BASE` (constante)
Si la página se abre desde `localhost`/`127.0.0.1` usa `http://127.0.0.1:8787`; en cualquier
otro dominio usa la URL de producción del Worker (reemplazar tras desplegar, ver `README.md`).

### `LIMITE_ALFABETO` (constante)
Copia en el frontend del mismo `256` que usa `alfabeto.py`, para el contador en vivo (`SF36`).

### SF29
- **Parámetros:** `ruta` (str), `cuerpo` (objeto JS). Función asíncrona.
- **Ubicación:** `front/main.js`.
- **Qué hace:** helper de `fetch` con método POST y JSON; lanza `Error` si la respuesta no es
  exitosa.

### SF30
- **Parámetros:** `mensaje` (str), `esError` (bool).
- **Ubicación:** `front/main.js`.
- **Qué hace:** actualiza `#alphabet-error`/`#alphabet-status`.

### SF31
- **Parámetros:** `evento` (submit de `#alphabet-form`). Función asíncrona.
- **Ubicación:** `front/main.js`.
- **Qué hace:** valida el alfabeto contra el backend (`SF29`), lo guarda en
  `SFEstadoAlfabeto` y `localStorage` si es válido.

### SF32
- **Parámetros:** `evento` (submit de `#encrypt-form`). Función asíncrona.
- **Ubicación:** `front/main.js`.
- **Qué hace:** cifra el texto con el método/desplazamiento elegidos, vía `SF29`.

### SF33
- **Parámetros:** `evento` (submit de `#decrypt-form`). Función asíncrona.
- **Ubicación:** `front/main.js`.
- **Qué hace:** envía el texto cifrado a `/api/descifrar` (sin indicar método) y muestra el
  resultado detectado automáticamente.

### SF34
- **Parámetros:** `idOrigen` (str).
- **Ubicación:** `front/main.js`.
- **Qué hace:** copia al portapapeles el contenido de un elemento del DOM.

### SF35
- **Parámetros:** ninguno.
- **Ubicación:** `front/main.js`.
- **Qué hace:** muestra/oculta el campo de desplazamiento según el método elegido, y conecta
  los botones ▲/▼ del stepper (límite 1-25).

### SF36
- **Parámetros:** ninguno.
- **Ubicación:** `front/main.js`.
- **Qué hace:** contador en vivo "`X / 256 caracteres`" bajo el campo de alfabeto; lo pinta en
  rojo (`var(--error)`) si se supera `LIMITE_ALFABETO`.

### SF37
- **Parámetros:** ninguno.
- **Ubicación:** `front/main.js`.
- **Qué hace:** arranque en `DOMContentLoaded`: restaura el alfabeto de `localStorage`, y
  registra `SF31`-`SF34` como manejadores de eventos, más `SF35` y `SF36`.
