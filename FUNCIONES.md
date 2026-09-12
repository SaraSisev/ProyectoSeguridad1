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
  descifrado.py            -> únicamente la primitiva de César inverso (con un desplazamiento dado)
  datos_espanol.py         -> datos del idioma: corpus propio, frecuencias, n-gramas, diccionario
  analisis_frecuencia.py   -> calcula los 9 componentes del puntaje de un candidato
  analizador.py            -> orquesta: genera las 26 hipótesis, puntúa, decide y calcula confianza
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

`analizador.py` (`SF26`) prueba las 26 claves posibles (Atbash + los 25 desplazamientos
César), calcula el puntaje multi-componente de cada una (`analisis_frecuencia.SF22`) y se
queda con la de **mayor valor**. Ese puntaje combina nueve señales independientes:

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

### El nivel de confianza (`analizador.py`)

Elegir "la mejor de 26 opciones" no significa que esa opción sea necesariamente correcta —
depende de qué tan claramente le gana a las demás. Por eso, además del resultado, el sistema
reporta un **nivel de confianza** (`SF25`), calculado a partir de:

1. **El margen**: qué tan por encima quedó el puntaje ganador respecto al segundo mejor. Un
   margen grande significa que ninguna otra clave se le acerca; un margen de 0 significa que
   varias claves son indistinguibles entre sí (ninguna evidencia real).
2. **La cantidad de letras** realmente analizadas en el candidato ganador. Con muy pocas
   letras (menos de 10), la confianza nunca puede pasar de "media" — no hay suficiente
   material para que el análisis estadístico sea fiable.

Esto es justo lo que le faltaba a una versión anterior de este sistema: con alfabetos que
cubren muy pocas letras del texto (por ejemplo, un alfabeto de símbolos exóticos con solo un
par de letras latinas), el margen entre candidatos se vuelve muy pequeño o incluso cero
(porque casi todo el texto pasa sin cifrar y es idéntico en las 26 hipótesis), y ahora el
sistema lo refleja honestamente como confianza **baja** en vez de presentar cualquier
resultado con la misma seguridad.

### De dónde sale cada dato (nada citado de internet)

- **`FRECUENCIA_LETRAS`, `PESOS_BIGRAMAS`, `PESOS_TRIGRAMAS`, `PESOS_TETRAGRAMAS`,
  `RATIO_VOCALES_OBJETIVO`**: se calculan contando directamente sobre `CORPUS_REFERENCIA`
  (ver `SF10`, `SF11`, `SF12` en `datos_espanol.py`). Si alguien cambia el corpus, estos
  números se recalculan solos la próxima vez que se importa el módulo.
- **`PALABRAS_MUY_COMUNES` y `PALABRAS_COMUNES_BASE`**: palabras gramaticales del español
  escritas a mano (artículos, preposiciones, pronombres, verbos auxiliares); conocimiento
  básico del idioma, no un dataset de una fuente específica. `PALABRAS_COMUNES` final añade
  además, automáticamente, todas las palabras del corpus.
- **`PESOS_PREFIJOS`, `PESOS_SUFIJOS`, `PESOS_SECUENCIAS_IMPROBABLES`**: reglas generales de
  formación de palabras y ortografía del español, escritas a mano por ser conocimiento
  general del idioma.

### Límite honesto del método

El análisis de frecuencias necesita que una parte razonable del mensaje haya sido realmente
sustituida por el cifrado. Si el alfabeto no incluye las letras españolas que aparecen en el
texto, la mayor parte del mensaje pasa sin cifrar (se "pasa por alto", tal como exige el
enunciado), y con muy poca señal cifrada ningún método —automático o humano— puede garantizar
recuperar la clave real. Ahora esto ya no es un fallo silencioso: se refleja como confianza
baja en la respuesta.

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
- **Quién la usa:** `SF30`, `SF31`, `SF32` (en `entry.py`).

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
- **Quién la usa:** `SF31` en `entry.py`.

### SF5 (Atbash — cifra y descifra, es autoinverso)
- **Parámetros:** `texto` (str), `alfabeto` (str).
- **Ubicación:** `backend/src/cifrado.py`.
- **Qué hace:** cada carácter se reemplaza por el simétrico del alfabeto
  (`longitud - 1 - posición`). Al ser una involución, sirve para cifrar y descifrar con la
  misma función.
- **Quién la usa:** `SF31` en `entry.py` (cifrar) y `SF23` en `analizador.py` (candidato
  Atbash durante la autodetección).

---

## `backend/src/descifrado.py`

Solo contiene la primitiva de descifrado César; la orquestación de las 26 hipótesis vive en
`analizador.py`, para separar "cómo se descifra con una clave" de "cómo se decide cuál clave
es la correcta".

### SF6 (César — descifrar con un desplazamiento dado)
- **Parámetros:** `texto` (str), `alfabeto` (str), `desplazamiento` (int, 1-25).
- **Ubicación:** `backend/src/descifrado.py`.
- **Qué hace:** inversa de `SF4`: resta el desplazamiento en vez de sumarlo (mismo criterio
  de "pasar por alto" los caracteres fuera del alfabeto).
- **Quién la usa:** `SF23` (en `analizador.py`), 25 veces, una por cada desplazamiento
  candidato.

---

## `backend/src/datos_espanol.py`

Todos los datos del idioma español que usa el motor de análisis. No depende de ningún otro
archivo del proyecto.

### `CORPUS_REFERENCIA` (constante)
Texto en español de varios párrafos, escrito específicamente para este proyecto, usado para
derivar **todos** los datos de abajo.

### `LETRAS_ESPANOL`, `VOCALES`, `PATRON_PALABRA` (constantes)
El alfabeto español en minúsculas, el conjunto de vocales (con tilde), y la expresión regular
`[a-zñ]+` usada para separar palabras.

### SF8
- **Parámetros:** `texto` (str).
- **Ubicación:** `backend/src/datos_espanol.py`.
- **Qué hace:** normaliza el texto para el análisis: minúsculas + vocales acentuadas a su
  forma base (á→a, é→e, í→i, ó→o, ú→u, ü→u). No toca la `ñ`. Nunca se usa para el texto que
  ve el usuario, solo para análisis interno.
- **Quién la usa:** internamente en este módulo y en `analisis_frecuencia.py` (`SF22`).

### SF9
- **Parámetros:** `texto_normalizado` (str, ya pasado por `SF8`).
- **Ubicación:** `backend/src/datos_espanol.py`.
- **Qué hace:** separa el texto en palabras usando `PATRON_PALABRA`.
- **Quién la usa:** para construir `PALABRAS_COMUNES` a partir del corpus, y en
  `analisis_frecuencia.py` (`SF22`).

### SF10
- **Parámetros:** `texto_normalizado` (str).
- **Ubicación:** `backend/src/datos_espanol.py`.
- **Qué hace:** cuenta cuántas veces aparece cada letra española (incluye las 27 letras con
  conteo 0 si no aparecen).
- **Quién la usa:** una vez, sobre `CORPUS_REFERENCIA`, para `FRECUENCIA_LETRAS` y
  `RATIO_VOCALES_OBJETIVO`.

### SF11
- **Parámetros:** `texto_normalizado` (str), `n` (int: 2, 3 o 4).
- **Ubicación:** `backend/src/datos_espanol.py`.
- **Qué hace:** cuenta apariciones de cada secuencia contigua de `n` letras (ventana
  deslizante), descartando fragmentos que crucen espacios o signos de puntuación.
- **Quién la usa:** `SF12`.

### SF12
- **Parámetros:** `texto_normalizado` (str), `n` (int), `peso_maximo` (float),
  `minimo_apariciones` (int).
- **Ubicación:** `backend/src/datos_espanol.py`.
- **Qué hace:** construye una tabla de pesos de n-gramas: cuenta con `SF11`, descarta los que
  aparecen menos de `minimo_apariciones` veces (para no incluir ruido de un corpus pequeño) y
  escala el más frecuente a `peso_maximo`.
- **Quién la usa:** para `PESOS_BIGRAMAS` (n=2, máx. 1.20, mínimo 4), `PESOS_TRIGRAMAS` (n=3,
  máx. 1.80, mínimo 3) y `PESOS_TETRAGRAMAS` (n=4, máx. 2.20, mínimo 2).

### Constantes calculadas del corpus
`FRECUENCIA_LETRAS`, `RATIO_VOCALES_OBJETIVO`/`MIN`/`MAX`, `PESOS_BIGRAMAS`,
`PESOS_TRIGRAMAS`, `PESOS_TETRAGRAMAS`, `PALABRAS_COMUNES` (ver funciones de arriba).

### Constantes escritas a mano (conocimiento general del idioma)
`PALABRAS_MUY_COMUNES`, `PALABRAS_COMUNES_BASE`, `PESOS_PREFIJOS`, `PESOS_SUFIJOS`,
`PESOS_SECUENCIAS_IMPROBABLES`, `LONGITUD_PALABRA_MAX_RAZONABLE = 18`.

---

## `backend/src/analisis_frecuencia.py`

El motor de puntuación de un solo candidato. Importa de `datos_espanol.py` todo lo que
necesita.

### SF13 (frecuencia de letras)
- **Parámetros:** `texto_normalizado` (str).
- **Ubicación:** `backend/src/analisis_frecuencia.py`.
- **Qué hace:** chi-cuadrado clásico entre la mezcla de letras del candidato y
  `FRECUENCIA_LETRAS`, normalizado y convertido a un puntaje acotado:
  `35 / (1 + chi_cuadrado_normalizado)`.
- **Caso especial:** sin letras españolas reconocibles, devuelve `-20.0`.
- **Quién la usa:** `SF22`.

### SF14 (palabras del diccionario)
- **Parámetros:** `palabras` (list[str]).
- **Ubicación:** `backend/src/analisis_frecuencia.py`.
- **Qué hace:** suma `3.0 + min(long, 8) * 0.80` por cada palabra en `PALABRAS_MUY_COMUNES`, y
  `1.5 + min(long, 8) * 0.50` por cada una en `PALABRAS_COMUNES`.
- **Quién la usa:** `SF22`.

### SF15 (patrones — bigramas, trigramas, tetragramas)
- **Parámetros:** `texto_normalizado` (str), `tabla_pesos` (dict).
- **Ubicación:** `backend/src/analisis_frecuencia.py`.
- **Qué hace:** función genérica reutilizada tres veces: para cada patrón de la tabla, cuenta
  apariciones como subcadena (`texto.count(patron)`) y suma `apariciones * peso`.
- **Quién la usa:** `SF22`, una vez por cada una de las tres tablas.

### SF16 (prefijos) / SF17 (sufijos)
- **Parámetros:** `palabras` (list[str]).
- **Ubicación:** `backend/src/analisis_frecuencia.py`.
- **Qué hacen:** revisan si cada palabra empieza (`SF16`) o termina (`SF17`) con alguna
  entrada de `PESOS_PREFIJOS`/`PESOS_SUFIJOS` y suman el peso correspondiente.
- **Quién las usa:** `SF22`.

### SF18 (penalización de secuencias improbables)
- **Parámetros:** `texto_normalizado` (str).
- **Ubicación:** `backend/src/analisis_frecuencia.py`.
- **Qué hace:** cuenta apariciones de cada secuencia de `PESOS_SECUENCIAS_IMPROBABLES` y
  acumula la penalización (se resta en `SF22`).
- **Quién la usa:** `SF22`.

### SF19 (proporción de vocales)
- **Parámetros:** `texto_normalizado` (str).
- **Ubicación:** `backend/src/analisis_frecuencia.py`.
- **Qué hace:** `puntaje = 12.0 - |ratio - objetivo| * 40`; resta 8 puntos extra si el ratio
  se sale de `RATIO_VOCALES_MIN`/`MAX`.
- **Devuelve:** `(puntaje, ratio)`. Sin letras: `(-20.0, 0.0)`.
- **Quién la usa:** `SF22`.

### SF20 (secuencia de consonantes más larga — auxiliar) / SF21 (estructura de palabra)
- **Parámetros:** `SF20` recibe una `palabra` (str); `SF21` recibe `palabras` (list[str]).
- **Ubicación:** `backend/src/analisis_frecuencia.py`.
- **Qué hacen:** `SF20` mide la racha más larga de consonantes seguidas de una palabra.
  `SF21` puntúa la plausibilidad de las palabras: bono por tener varias, penalización por
  palabras muy largas, sin vocales, con 5+ consonantes seguidas (`SF20`), o con un carácter
  repetido 4+ veces. Sin palabras, devuelve `-15.0`.
- **Quién las usa:** `SF22`.

### SF22 (puntaje total de un candidato)
- **Parámetros:** `texto` (str) — un candidato completo de texto descifrado.
- **Ubicación:** `backend/src/analisis_frecuencia.py`.
- **Qué hace:** normaliza (`SF8`) y separa en palabras (`SF9`); calcula los nueve componentes
  (`SF13`-`SF21`) y los suma en un total.
- **Devuelve:** `{"total": float, "componentes": {...9 valores, útiles para depurar...},
  "ratio_vocales": float, "num_palabras": int, "num_letras": int}`. `num_letras` es el total
  de letras españolas reconocidas en el candidato, usado por `SF25` para el nivel de
  confianza.
- **Quién la usa:** `SF23`/`SF26` (en `analizador.py`).

---

## `backend/src/analizador.py`

Orquesta el criptoanálisis completo: genera las 26 hipótesis, las puntúa, elige la ganadora y
calcula qué tan confiable es esa elección.

### SF23 (generar las 26 hipótesis)
- **Parámetros:** `texto_cifrado` (str), `alfabeto` (str).
- **Ubicación:** `backend/src/analizador.py`.
- **Qué hace:** genera el candidato Atbash (`cifrado.SF5`) y los 25 candidatos César
  (`descifrado.SF6`, desplazamientos 1 a 25 — el mismo rango permitido al cifrar, no se
  prueban desplazamientos fuera de ese rango porque nunca podrían haberse usado para cifrar).
- **Devuelve:** lista de `{"metodo": "ATBASH"|"CESAR", "desplazamiento": int|None,
  "texto": str}` (sin puntaje todavía).
- **Quién la usa:** `SF26`.

### SF24 (extraer el puntaje de un candidato ya analizado)
- **Parámetros:** `candidato` (dict, con clave `"analisis"` ya calculada).
- **Ubicación:** `backend/src/analizador.py`.
- **Qué hace:** devuelve `candidato["analisis"]["total"]`. Existe como función separada (en
  vez de un `lambda` inline) para poder reutilizarla tanto al ordenar los candidatos como al
  calcular la confianza.
- **Quién la usa:** `SF26` (como `key` de `sorted` y para leer los dos mejores puntajes).

### SF25 (calcular el nivel de confianza)
- **Parámetros:** `mejor_puntaje` (float), `segundo_puntaje` (float), `num_letras` (int).
- **Ubicación:** `backend/src/analizador.py`.
- **Qué hace:**
  1. `margen = mejor_puntaje - segundo_puntaje`: qué tanto le ganó el primero al segundo.
  2. `margen_relativo = margen / (abs(mejor_puntaje) + 1)`: el margen expresado como
     proporción del puntaje ganador (para que un margen de "10" signifique algo distinto si
     el puntaje ganador es 20 que si es 200).
  3. `factor_longitud = min(num_letras / 80, 1.0)`: crece con la cantidad de letras
     analizadas, tope en 80 letras (a partir de ahí ya hay material de sobra).
  4. `porcentaje = 45 + min(margen_relativo * 100, 35) + factor_longitud * 20`, acotado entre
     1 y 99.
  5. Si `num_letras < 10`, el porcentaje nunca pasa de 49 (nunca "alta" confianza con textos
     casi vacíos de letras).
  6. Si `margen <= 0` (empate exacto entre el primero y el segundo — cero evidencia real que
     distinga una clave de otra), el porcentaje nunca pasa de 20 (siempre confianza "baja").
     Este último caso es el que corrige el problema de los alfabetos que no cubren ninguna
     letra del texto: si todas las hipótesis dan exactamente el mismo resultado, no hay
     ninguna base para preferir una sobre otra.
  7. Nivel: `"alta"` si porcentaje ≥ 75, `"media"` si ≥ 50, si no `"baja"`.
- **Devuelve:** `{"nivel": str, "porcentaje": float, "margen": float}`.
- **Quién la usa:** `SF26`.

### SF26 (analizar el texto cifrado — punto de entrada del criptoanálisis)
- **Parámetros:** `texto_cifrado` (str), `alfabeto` (str).
- **Ubicación:** `backend/src/analizador.py`.
- **Qué hace:** genera las hipótesis (`SF23`), calcula el análisis completo de cada una
  (`analisis_frecuencia.SF22`), las ordena de mayor a menor puntaje (`sorted(..., key=SF24,
  reverse=True)`), toma la primera y la segunda, y calcula la confianza de la elección
  (`SF25`) comparando ambas.
- **Devuelve:** `{"metodo": str, "desplazamiento": int|None, "texto": str, "confianza":
  {...}}`.
- **Quién la usa:** `SF32` (en `entry.py`). Solo el resultado de esta función se le muestra al
  usuario — es la única línea "correcta" que exige el enunciado, ahora acompañada de qué tan
  seguro está el sistema de esa elección.

---

## `backend/src/entry.py`

Punto de entrada del *Cloudflare Worker* (Python). Depende del módulo `workers`, propio del
runtime de Cloudflare, por lo que no se puede importar ni probar fuera de ese entorno; toda la
lógica de negocio vive en los archivos anteriores, precisamente para poder probarla de forma
aislada.

### SF27
- **Parámetros:** ninguno.
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** devuelve las cabeceras CORS (`access-control-allow-origin: *`, métodos y
  headers permitidos) que se agregan a **todas** las respuestas.

### SF28
- **Parámetros:** `datos` (dict), `estado` (int, por defecto 200).
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** construye la respuesta HTTP: serializa `datos` a JSON con
  `ensure_ascii=False` (para que chino/árabe/jeroglíficos/acentos viajen tal cual, en UTF-8),
  añade las cabeceras de `SF27` más `content-type: application/json; charset=utf-8`.

### SF29
- **Parámetros:** `request` (objeto `Request` de Cloudflare). Función asíncrona.
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** lee el cuerpo como texto y lo interpreta como JSON; si viene vacío, devuelve
  un diccionario vacío.

### SF30
- **Parámetros:** `payload` (dict, espera `alfabeto`).
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** implementa `POST /api/alfabeto/validar` llamando a `SF1`.

### SF31
- **Parámetros:** `payload` (dict, espera `alfabeto`, `metodo`, `texto`, y
  `desplazamiento` si el método es César).
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** implementa `POST /api/cifrar`: valida con `SF1`, invoca `SF5` (Atbash) o `SF4`
  (César, validando el desplazamiento). Único lugar donde el usuario elige el método de
  cifrado.

### SF32
- **Parámetros:** `payload` (dict, espera `alfabeto` y `texto`).
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** implementa `POST /api/descifrar`: valida con `SF1` y delega toda la decisión
  a `SF26` (en `analizador.py`). Devuelve método, desplazamiento, texto y confianza. El
  usuario no interviene en ningún punto.

### `on_fetch` (nombre reservado, no forma parte de la numeración SF)
- **Parámetros:** `request`, `env`, `ctx` (firma exigida por Cloudflare; el nombre es
  obligatorio).
- **Ubicación:** `backend/src/entry.py`.
- **Qué hace:** único punto de entrada HTTP. Responde `204` a `OPTIONS`; enruta
  `POST /api/alfabeto/validar` a `SF30`, `POST /api/cifrar` a `SF31` y
  `POST /api/descifrar` a `SF32`; cualquier otra ruta devuelve `404`.

---

## `front/main.js`

Lógica de interfaz. Consume la API del backend mediante `fetch`. No contiene lógica
criptográfica: todo el cifrado/descifrado/autodetección ocurre en el backend.

### `URL_API_BASE` (constante)
Si la página se abre desde `localhost`/`127.0.0.1` usa `http://127.0.0.1:8787`; en cualquier
otro dominio usa la URL de producción del Worker (reemplazar tras desplegar, ver `README.md`).

### `LIMITE_ALFABETO` (constante)
Copia en el frontend del mismo `256` que usa `alfabeto.py`, para el contador en vivo (`SF36`).

### SF33
- **Parámetros:** `ruta` (str), `cuerpo` (objeto JS). Función asíncrona.
- **Ubicación:** `front/main.js`.
- **Qué hace:** helper de `fetch` con método POST y JSON; lanza `Error` si la respuesta no es
  exitosa.

### SF34
- **Parámetros:** `mensaje` (str), `esError` (bool).
- **Ubicación:** `front/main.js`.
- **Qué hace:** actualiza `#alphabet-error`/`#alphabet-status`.

### SF35
- **Parámetros:** `evento` (submit de `#alphabet-form`). Función asíncrona.
- **Ubicación:** `front/main.js`.
- **Qué hace:** valida el alfabeto contra el backend (`SF33`), lo guarda en
  `SFEstadoAlfabeto` y `localStorage` si es válido.

### SF36
- **Parámetros:** `evento` (submit de `#encrypt-form`). Función asíncrona.
- **Ubicación:** `front/main.js`.
- **Qué hace:** cifra el texto con el método/desplazamiento elegidos, vía `SF33`.

### SF37
- **Parámetros:** `evento` (submit de `#decrypt-form`). Función asíncrona.
- **Ubicación:** `front/main.js`.
- **Qué hace:** envía el texto cifrado a `/api/descifrar` (sin indicar método) y muestra el
  método, desplazamiento, **nivel de confianza** (`#decrypt-confidence-result`, como
  "`nivel (XX%)`") y el texto descifrado.

### SF38
- **Parámetros:** `idOrigen` (str).
- **Ubicación:** `front/main.js`.
- **Qué hace:** copia al portapapeles el contenido de un elemento del DOM.

### SF39
- **Parámetros:** ninguno.
- **Ubicación:** `front/main.js`.
- **Qué hace:** muestra/oculta el campo de desplazamiento según el método elegido, y conecta
  los botones ▲/▼ del stepper (límite 1-25).

### SF40
- **Parámetros:** ninguno.
- **Ubicación:** `front/main.js`.
- **Qué hace:** contador en vivo "`X / 256 caracteres`" bajo el campo de alfabeto; lo pinta en
  rojo si se supera `LIMITE_ALFABETO`.

### SF41
- **Parámetros:** ninguno.
- **Ubicación:** `front/main.js`.
- **Qué hace:** arranque en `DOMContentLoaded`: restaura el alfabeto de `localStorage`, y
  registra `SF35`-`SF38` como manejadores de eventos, más `SF39` y `SF40`.
