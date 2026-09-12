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

El conjunto de caracteres (alfabeto) debe contener entre 2 y 256 caracteres diferentes.

No se permiten caracteres repetidos dentro del conjunto.

Los únicos métodos de cifrado permitidos son César y Atbash.

El desplazamiento de César debe ser un número entero entre 1 y 25 inclusive. A diferencia de
un simple cálculo de módulo, el sistema **rechaza explícitamente** cualquier valor fuera de
ese rango (incluyendo 0 y números negativos) en vez de convertirlo automáticamente a un valor
equivalente dentro del rango.

Para obtener un descifrado correcto al usar el método César o Atbash de forma manual, se debe
utilizar exactamente el mismo conjunto y el mismo orden de caracteres empleados durante el
cifrado. El descifrado automático no necesita que el usuario indique el método ni el
desplazamiento, pero sí necesita el mismo alfabeto.

El análisis automático que decide entre César y Atbash está preparado principalmente para
textos en español.

## LIMITACIONES

César y Atbash son métodos de cifrado antiguos y no protegen información de manera segura.
César puede romperse probando sus 25 desplazamientos posibles, y Atbash ni siquiera utiliza
una clave: es una transformación fija y pública. Por esta razón, el programa solamente debe
utilizarse con fines educativos.

El descifrado automático no siempre identifica correctamente el texto original. Los mensajes
cortos ofrecen poca información para el análisis de frecuencias, diccionario y patrones de
letras. También pueden presentarse errores con nombres propios, abreviaturas, textos en otros
idiomas, códigos, o cadenas de caracteres sin sentido en español.

Cuando varios candidatos obtienen puntajes muy parecidos o incluso idénticos, el programa
igual selecciona uno (el de mayor puntaje, o el primero generado en caso de empate exacto)
aunque no exista evidencia suficiente para asegurar que sea correcto. Esto ocurre sobre todo
cuando el alfabeto definido cubre muy pocos de los caracteres que realmente aparecen en el
texto: la mayor parte del mensaje pasa sin cifrar (por diseño, los caracteres fuera del
alfabeto se dejan igual) y las 26 hipótesis posibles terminan pareciéndose demasiado entre sí.

El sistema no expone ningún porcentaje o indicador de confianza: siempre presenta el
candidato ganador como resultado único, sin distinguir si el margen frente a la segunda mejor
opción fue amplio o casi nulo. Esta es una decisión de diseño (se evaluó un indicador de
confianza durante el desarrollo y se retiró) para que la salida sea siempre una sola línea,
sin datos adicionales que el usuario deba interpretar.

El tiempo de respuesta aumenta cuando se usa un texto más largo o un alfabeto con más
caracteres, porque el descifrado automático genera y analiza 26 posibilidades completas por
cada solicitud, y cada una revisa el texto varias veces (una por cada señal: frecuencia de
letras, diccionario, bigramas, trigramas, tetragramas, prefijos, sufijos, vocales y
estructura de palabra).

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

También se probó el texto `ABC` con desplazamiento `-1`. A diferencia de un cálculo de módulo
simple (que convertiría `-1` en `25`), el sistema **rechazó la solicitud** con el mensaje "El
desplazamiento debe estar entre 1 y 25", porque el proyecto exige que el desplazamiento sea
siempre un valor positivo dentro de ese rango.

En otra prueba se utilizó el texto `ABC 123!` con desplazamiento `1` y el alfabeto `ABC`. Las
letras cambiaron a `BCA`, mientras que el espacio, los números y el signo de exclamación
permanecieron iguales por no pertenecer al alfabeto definido. El resultado fue `BCA 123!`.

Para Atbash se probó el texto `ABC XYZ` con el alfabeto A-Z. El resultado esperado y obtenido
fue `ZYX CBA`. Al aplicar Atbash nuevamente sobre ese resultado, se recuperó exactamente
`ABC XYZ`, confirmando que Atbash es su propia operación inversa.

## PRUEBAS REALES

Se ejecutaron las 23 pruebas automatizadas incluidas en el proyecto
(`backend/tests/test_logica.py`), que cubren validación del alfabeto, límites del
desplazamiento, cifrado y descifrado César, Atbash, autodetección con los 25 desplazamientos
posibles y con Atbash, y alfabetos con símbolos especiales y caracteres chinos. Las 23
pruebas terminaron correctamente.

También se ejecutó un banco de 280 casos de descifrado automático
(`backend/tests/benchmark_precision.py`) usando 40 oraciones completas de varias palabras,
cada una cifrada con 6 claves distintas (5 desplazamientos de muestra más Atbash). El programa
resolvió correctamente los 280 casos, es decir, 100 % de precisión. Este resultado corresponde
a oraciones completas y no significa que el programa siempre tendrá una precisión del 100 %
con cualquier tipo de texto.

Para comprobar el comportamiento con textos cortos se ejecutó el mismo banco de pruebas pero
con 40 palabras sueltas o muy cortas (`HOLA`, `SI`, `MEXICO`, `AMOR`, etc.), también con 6
claves cada una, para un total de 280 casos. El programa acertó en 135 casos y falló en 145,
lo que representa una precisión de 48.21 %. Los errores aparecieron con prácticamente todas
las palabras de una sola sílaba o muy cortas, confirmando la limitación esperada: el análisis
de frecuencias necesita varias palabras para tener suficiente información.

También se probaron los límites de entrada directamente contra la API. El programa aceptó un
texto de 10 000 caracteres y rechazó uno de 10 001. Aceptó un alfabeto de 256 caracteres
distintos y rechazó uno de 257. Rechazó también alfabetos vacíos, alfabetos con caracteres
repetidos, métodos de cifrado desconocidos, desplazamientos que no son números enteros, y
desplazamientos fuera del rango 1-25 (incluyendo 0 y negativos).

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
