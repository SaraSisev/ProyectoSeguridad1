# Pruebas, restricciones y limitaciones del sistema

Este documento resume las pruebas de escritorio y las pruebas reales realizadas sobre el
sistema de cifrado y descifrado, y a partir de ellas define las restricciones y limitaciones
reales del programa. Los números y ejemplos de este documento se obtuvieron ejecutando
directamente el código del proyecto (no son estimaciones): la suite automatizada está en
[`backend/tests/test_logica.py`](backend/tests/test_logica.py) y el banco de precisión en
[`backend/tests/benchmark_precision.py`](backend/tests/benchmark_precision.py), ambos
reproducibles con `python test_logica.py` y `python benchmark_precision.py` desde
`backend/tests/`.

## RESTRICCIONES

El texto a cifrar o descifrar debe contener entre 1 y 10 000 caracteres. Este máximo se
definió después de medir el tiempo de análisis con textos de distintos tamaños (ver la
sección de rendimiento, más abajo): 10 000 caracteres se procesan en medio segundo
aproximadamente, un tiempo razonable para una respuesta web; se estableció ese valor como
techo para evitar solicitudes que tarden demasiado o consuman recursos de forma excesiva.

El conjunto de caracteres (alfabeto) debe contener entre 2 y 1000 caracteres diferentes
(el límite se definió inicialmente en 256 y luego se amplió a 1000, sin volver a medir
tiempos: un alfabeto más grande solo afecta la construcción del mapa de índices, un costo
insignificante frente al análisis del texto).

No se permiten caracteres repetidos dentro del conjunto.

Los únicos métodos de cifrado permitidos son César y Atbash.

El desplazamiento de César debe ser un número entero entre 1 y (longitud del alfabeto - 1)
inclusive: con el alfabeto clásico de 26-27 letras ese máximo es 25 o 26, pero con un alfabeto
personalizado de, por ejemplo, 101 o 1000 caracteres, el máximo válido es 100 o 999
respectivamente — el rango depende del alfabeto que se aplique, no es un número fijo. A
diferencia de un simple cálculo de módulo, el sistema **rechaza explícitamente** cualquier
valor fuera de ese rango (incluyendo 0 y números negativos) en vez de convertirlo
automáticamente a un valor equivalente dentro del rango.

> **Corrección:** en una versión anterior el máximo estaba fijo en 25 sin importar el alfabeto
> aplicado, lo que impedía cifrar y, sobre todo, **descifrar automáticamente** cualquier mensaje
> cuyo desplazamiento real superara 25 en un alfabeto de más de 26 caracteres (el caso normal,
> ya que el alfabeto por defecto tiene más de 100 caracteres). Se corrigió para que el máximo se
> calcule a partir de la longitud real del alfabeto en cada solicitud.

Para obtener un descifrado correcto al usar el método César o Atbash de forma manual, se debe
utilizar exactamente el mismo conjunto y el mismo orden de caracteres empleados durante el
cifrado. El descifrado automático no necesita que el usuario indique el método ni el
desplazamiento, pero sí necesita el mismo alfabeto.

El análisis automático que decide entre César y Atbash está preparado principalmente para
textos en español.

## LIMITACIONES

César y Atbash son métodos de cifrado antiguos y no protegen información de manera segura.
César puede romperse probando todos sus desplazamientos posibles (longitud del alfabeto menos
uno; con el alfabeto por defecto, cientos de posibilidades, todas verificables en segundos), y
Atbash ni siquiera utiliza una clave: es una transformación fija y pública. Por esta razón, el
programa solamente debe utilizarse con fines educativos.

El descifrado automático no siempre identifica correctamente el texto original. Los mensajes
cortos ofrecen poca información para el análisis de frecuencias, diccionario y patrones de
letras. También pueden presentarse errores con nombres propios, abreviaturas, textos en otros
idiomas, códigos, o cadenas de caracteres sin sentido en español.

Cuando varios candidatos obtienen puntajes muy parecidos o incluso idénticos, el programa
igual selecciona uno (el de mayor puntaje, o el primero generado en caso de empate exacto)
aunque no exista evidencia suficiente para asegurar que sea correcto. Esto ocurre sobre todo
cuando el alfabeto definido cubre muy pocos de los caracteres que realmente aparecen en el
texto: la mayor parte del mensaje pasa sin cifrar (por diseño, los caracteres fuera del
alfabeto se dejan igual) y las hipótesis generadas terminan pareciéndose demasiado entre sí.

El sistema no expone ningún porcentaje o indicador de confianza: siempre presenta el
candidato ganador como resultado único, sin distinguir si el margen frente a la segunda mejor
opción fue amplio o casi nulo. Esta es una decisión de diseño (se evaluó un indicador de
confianza durante el desarrollo y se retiró) para que la salida sea siempre una sola línea,
sin datos adicionales que el usuario deba interpretar.

El tiempo de respuesta aumenta cuando se usa un texto más largo o un alfabeto con más
caracteres, porque el descifrado automático genera y analiza una posibilidad por cada
desplazamiento posible del alfabeto (longitud del alfabeto menos uno, más Atbash) en cada
solicitud, y cada una revisa el texto varias veces (una por cada señal: frecuencia de letras,
diccionario, bigramas, trigramas, tetragramas, prefijos, sufijos, vocales y estructura de
palabra). Con el alfabeto por defecto (poco más de 100 caracteres) y el límite máximo de 1000
caracteres, ese número de posibilidades pasa de un centenar a casi mil; la sustitución de
caracteres se implementa con tablas de traducción (`str.translate`) en vez de un bucle en
Python por carácter para que ese crecimiento no vuelva la respuesta perceptiblemente más
lenta.

## PRUEBAS DE ESCRITORIO

En una prueba de César se utilizó el texto `HOLA`, el alfabeto de la A a la Z (sin la Ñ) y un
desplazamiento de 3.

- H avanzó hasta K.
- O avanzó hasta R.
- L avanzó hasta O.
- A avanzó hasta D.

El resultado esperado y obtenido fue `KROD`. Esta cuenta se verificó también con el alfabeto
español completo (que incluye la Ñ): al insertarse la Ñ entre la N y la O, todas las letras
posteriores a la N se recorren una posición, así que el mismo texto y el mismo desplazamiento
producen un resultado distinto (`KRÑD` en vez de `KROD`). Esto no es un error: confirma que el
resultado depende exactamente del alfabeto usado, tal como exige la restricción de "mismo
conjunto y mismo orden".

También se probó el texto `ABC` con desplazamiento `-1` sobre el alfabeto español completo (27
caracteres). A diferencia de un cálculo de módulo simple (que convertiría `-1` en `26`), el
sistema **rechazó la solicitud** con el mensaje "El desplazamiento debe estar entre 1 y 26
para un alfabeto de 27 caracteres", porque el proyecto exige que el desplazamiento sea siempre
un valor positivo dentro del rango válido para el alfabeto usado.

En otra prueba se utilizó el texto `ABC 123!` con desplazamiento `1` y el alfabeto `ABC`. Las
letras cambiaron a `BCA`, mientras que el espacio, los números y el signo de exclamación
permanecieron iguales por no pertenecer al alfabeto definido. El resultado fue `BCA 123!`.

Para Atbash se probó el texto `ABC XYZ` con el alfabeto A-Z. El resultado esperado y obtenido
fue `ZYX CBA`. Al aplicar Atbash nuevamente sobre ese resultado, se recuperó exactamente
`ABC XYZ`, confirmando que Atbash es su propia operación inversa.

## PRUEBAS REALES

Se ejecutaron las 25 pruebas automatizadas incluidas en el proyecto
(`backend/tests/test_logica.py`), que cubren validación del alfabeto, límites del
desplazamiento, cifrado y descifrado César, Atbash, autodetección con todos los
desplazamientos posibles del alfabeto usado y con Atbash, alfabetos con símbolos especiales y
caracteres chinos, y dos pruebas de regresión que verifican específicamente desplazamientos
mayores a 25 (63 sobre un alfabeto de 101 caracteres, y el máximo de 999 sobre el alfabeto
límite de 1000) — el caso que la versión anterior no podía resolver. Las 25 pruebas terminaron
correctamente.

También se ejecutó un banco de 280 casos de descifrado automático
(`backend/tests/benchmark_precision.py`) usando 40 oraciones completas de varias palabras,
cada una cifrada con 6 claves distintas (5 desplazamientos de muestra más Atbash). El programa
resolvió correctamente los 280 casos, es decir, 100 % de precisión. Este resultado corresponde
a oraciones completas y no significa que el programa siempre tendrá una precisión del 100 %
con cualquier tipo de texto.

Para comprobar el comportamiento con textos cortos se ejecutó el mismo banco de pruebas pero
con 40 palabras sueltas o muy cortas (`HOLA`, `SI`, `MEXICO`, `AMOR`, etc.), también con 6
claves cada una, para un total de 280 casos. Inicialmente (justo después de corregir el rango
de desplazamientos, ver más arriba) el programa acertaba solo 130 casos (46.43 %): el
diccionario de `datos_espanol.py` solo tenía palabras gramaticales (artículos, preposiciones,
conjunciones) y ninguna palabra cotidiana real (`hola`, `casa`, `agua`...), así que `SF10` no
aportaba ninguna señal a favor del candidato correcto y la decisión quedaba en manos de
señales estadísticas poco confiables con tan pocas letras. Se corrigieron dos causas
concretas:

1. **Diccionario insuficiente.** Se amplió `PALABRAS_COMUNES` de ~95 a más de 540 palabras de
   uso cotidiano (sustantivos, adjetivos, verbos comunes), manteniendo intactos los dos
   niveles de peso ya existentes (`PALABRAS_MUY_COMUNES`/`PALABRAS_COMUNES`) y su fórmula de
   puntaje en `SF10`. Esto por sí solo subió la precisión a 86.43 % (242/280).
2. **Penalización de vocales mal calibrada para muestras pequeñas.** `SF15` restaba 8 puntos
   fijos (atenuados, pero no eliminados) cuando el ratio de vocales caía fuera de 0.25-0.65,
   sin importar cuántas letras aportara el candidato. Una palabra real y corta como `agua`
   (75 % de vocales) activaba esa penalización y perdía frente a un candidato sin sentido
   que, por azar, tuviera un ratio más "típico" — incluso ganándole al bono de diccionario
   recién agregado. Se ajustó `SF15` para que esa penalización fija solo se aplique con
   muestra completa (`len(letras) >= MUESTRA_MINIMA_CONFIABLE`), dejando para muestras
   pequeñas únicamente el término suave basado en la distancia al ratio objetivo (que ya
   se atenuaba correctamente). Esto subió la precisión a 96.43 % (270/280).

Al probar con alfabetos personalizados más grandes (el típico de ~100 caracteres, con
mayúsculas, minúsculas, acentos, dígitos y símbolos) aparecieron dos causas adicionales,
ambas relacionadas con qué tan fácil es que un candidato de puro ruido "parezca" español por
pura casualidad cuando el alfabeto mezcla letras con signos de puntuación:

3. **Coincidencias de diccionario en fragmentos sueltos.** `SF8` corta una "palabra" en
   cualquier carácter no alfabético, así que un signo de puntuación intercalado en un
   candidato de ruido puede dejar una letra o dos aisladas entre símbolos (por ejemplo
   `"&es&"` produce la "palabra" `"es"`). Como el diccionario ampliado ya cubre muchas
   palabras de 1-2 letras reales, esas coincidencias aisladas puntuaban igual que un acierto
   real y podían inflar un candidato de ruido por encima de una palabra real más larga que no
   está en el diccionario (por ejemplo `pajaro`, que solo apareció en el diccionario después
   del punto 1 pero perdía contra fragmentos de 1-2 letras de candidatos de ruido). Se ajustó
   `SF10` para ignorar coincidencias de menos de 3 letras.
4. **Un acierto de diccionario no siempre alcanzaba a superar una racha de suerte
   estadística.** Con muestras de 4-6 letras, un candidato sin sentido puede coincidir por
   azar con dos o tres bigramas típicos del español y tener una frecuencia de letras
   razonablemente cercana a la esperada, acumulando un puntaje comparable al de una palabra
   real. Se subió el peso base de `SF10` (de 3.0/1.5 a 4.0/2.5 según el nivel) para que un
   acierto de diccionario genuino pese más que esas coincidencias parciales.

Estos cuatro ajustes en conjunto subieron la precisión con palabras sueltas a **97.14 %
(272/280)**, sin afectar el 100 % obtenido con oraciones completas. Los 8 casos que persisten
son palabras de 2-3 letras que compiten directamente contra la palabra más frecuente del
idioma (`SI` pierde contra `LA`, `SOL` en Atbash pierde contra `LOS`, `NO` en Atbash pierde
contra `ON`) — ambigüedades genuinas del espacio de claves con apenas 2-3 letras de evidencia,
no errores de implementación; ni un cripto-analista humano podría distinguirlas de forma
confiable con solo estadística de frecuencias.

Aparte, con alfabetos que incluyen mayúsculas y minúsculas como símbolos separados existe una
ambigüedad estructural distinta: como el análisis normaliza todo a minúsculas antes de
puntuar (`SF7`), una palabra y su variante en mayúsculas (`pajaro` / `PAJARO`) obtienen
**exactamente el mismo puntaje**. Para desplazamientos donde esa coincidencia de mayúsculas
ocurre, el sistema entrega la palabra correcta pero con el casing equivocado — nunca ruido —
y cuál de las dos gana depende del orden en que se generan los candidatos, no de evidencia
lingüística real. No es un error de descifrado (la palabra se identifica bien) sino un límite
de tratar mayúsculas y minúsculas como símbolos distintos del alfabeto mientras el análisis
lingüístico las trata como la misma letra.

También se probaron los límites de entrada directamente contra la API. El programa aceptó un
texto de 10 000 caracteres y rechazó uno de 10 001. Aceptó un alfabeto de 256 caracteres
distintos y rechazó uno de 257 (límite vigente en el momento de esta prueba; se amplió
después a 1000 caracteres, sin cambiar el mecanismo de validación). Rechazó también alfabetos vacíos, alfabetos con caracteres
repetidos, métodos de cifrado desconocidos, desplazamientos que no son números enteros, y
desplazamientos fuera del rango válido para el alfabeto usado (incluyendo 0, negativos, y
valores mayores o iguales a la longitud del alfabeto).

Durante estas pruebas se encontraron y corrigieron dos problemas reales:

1. **Un cuerpo de solicitud con JSON mal formado o que no era un objeto** (por ejemplo, un
   arreglo) hacía que la API respondiera con un error 500 y expusiera el detalle interno del
   error (incluyendo rutas de archivos del servidor) en vez de un mensaje controlado. Se
   corrigió para que ahora responda siempre con un error 400 y un mensaje claro, sin exponer
   información interna.
2. **Inconsistencia de normalización Unicode:** un mismo alfabeto puede escribirse de dos
   formas distintas a nivel de código (por ejemplo, una "É" puede ser un solo carácter Unicode,
   o una "E" seguida de un acento combinado por separado); ambas se ven idénticas al leerlas,
   pero antes de la corrección el programa las trataba como alfabetos de distinta longitud,
   provocando que un texto cifrado con una de las dos formas no se descifrara correctamente
   con la otra. Se corrigió normalizando el alfabeto y el texto a la forma estándar (NFC) al
   recibir cada solicitud en la API. Esta corrección se verificó cifrando con la forma
   "descompuesta" del alfabeto y descifrando con la forma "compuesta": antes de la corrección
   el resultado era incorrecto, después de la corrección se recuperó el texto original
   exactamente.

Se midió también el tiempo de respuesta del descifrado automático con distintos tamaños de
texto (alfabeto de 45 caracteres, desplazamiento fijo): 100 caracteres se resolvieron en
0.007 s, 1 000 en 0.05 s, 5 000 en 0.24 s, 10 000 en 0.50 s, 20 000 en 0.83 s y 50 000 en
2.23 s. El tiempo crece de forma aproximadamente lineal con la longitud del texto. Con un
alfabeto de 256 caracteres y un texto de 10 000 caracteres, el tiempo fue de 0.63 s.

Finalmente, se probó la API ya publicada en Cloudflare Workers
(`https://cifrado-cesar-atbash-backend.saracuevasc0.workers.dev`). Se cifró la frase
"HOLA MUNDO ESTE ES UN MENSAJE DE PRUEBA" con Atbash y se envió el resultado de vuelta al
endpoint de descifrado automático, sin indicar el método usado. El sistema detectó
correctamente Atbash y recuperó el texto original completo. También se confirmó en producción
que un JSON mal formado responde con error 400 controlado, igual que en las pruebas locales.
