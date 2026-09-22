# Sistema de Cifrado y Descifrado — César / Atbash

Proyecto académico de Seguridad. Permite definir un alfabeto propio (hasta 1000 caracteres,
incluyendo símbolos especiales de cualquier idioma o codificación), cifrar con César o
Atbash, y descifrar de forma **automática** (sin que el usuario elija el método), usando
análisis de frecuencias en español al estilo de Al-Kindi.

Ver [`FUNCIONES.md`](FUNCIONES.md) para la documentación técnica función por función
(identificadores `SFx`), y [`PRUEBAS_Y_LIMITACIONES.md`](PRUEBAS_Y_LIMITACIONES.md) para las
restricciones, limitaciones y resultados de las pruebas reales realizadas sobre el sistema.

## Estructura

```
frontend/    -> sitio estático (HTML/CSS/JS), se publica en GitHub Pages
backend/  -> Cloudflare Worker en Python (beta "Python Workers"), se publica en Cloudflare
  src/
    alfabeto.py             -> validación del alfabeto y utilidades de índices/desplazamiento
    cifrado.py               -> cifrado César y Atbash
    descifrado.py            -> primitiva de César inverso (con un desplazamiento dado)
    datos_espanol.py         -> datos fijos del idioma: frecuencias, n-gramas, diccionario, morfología
    analisis_frecuencia.py   -> calcula los 9 componentes del puntaje de un candidato
    analizador.py            -> genera todas las hipótesis posibles, puntúa y elige la ganadora (Al-Kindi)
    entry.py                 -> punto de entrada del Worker (rutas HTTP, CORS)
```

## Backend — Cloudflare Workers (Python)

**Ya desplegado en:** https://cifrado-cesar-atbash-backend.cifrador-cesar-atbash.workers.dev

> Nota: la URL cambió de cuenta de Cloudflare al corregir el descifrado (septiembre 2026). La
> URL anterior (`cifrado-cesar-atbash-backend.saracuevasc0.workers.dev`) seguía apuntando al
> código sin corregir; `frontend/main.js` ya apunta a la URL nueva.

Requisitos: Node.js (para la CLI `wrangler`) y una cuenta de Cloudflare.

```bash
npm install -g wrangler
cd backend
wrangler login
wrangler deploy
```

Al terminar, `wrangler` imprime la URL pública del Worker. Si vuelves a desplegar (por
ejemplo tras editar el código), el comando reutiliza la misma URL — no cambia.

Para probar en local antes de desplegar:

```bash
cd backend
wrangler dev --local --port 8787
```

Y en otra terminal, sirve el frontend en local:

```bash
cd frontend
python -m http.server 5500
```

`frontend/main.js` detecta automáticamente cuando la página se abre desde `localhost` o
`127.0.0.1` y en ese caso usa `http://127.0.0.1:8787` como backend, sin necesidad de editar
nada. Abre `http://127.0.0.1:5500` en el navegador para probar todo el flujo completo.

Endpoints expuestos (todos `POST`, cuerpo y respuesta en JSON, con CORS abierto):

- `POST /api/alfabeto/validar` — body `{ "alfabeto": "..." }`
- `POST /api/cifrar` — body `{ "alfabeto": "...", "metodo": "CESAR"|"ATBASH", "texto": "...", "desplazamiento": entero entre 1 y (longitud del alfabeto - 1), solo si CESAR }`
- `POST /api/descifrar` — body `{ "alfabeto": "...", "texto": "..." }` (el método y el desplazamiento se detectan automáticamente)

## Frontend — GitHub Pages

`frontend/main.js` ya apunta a la URL real del backend desplegado, así que no hay que editar
nada más:

1. Sube la carpeta `frontend/` a un repositorio de GitHub y activa GitHub Pages apuntando a esa
   carpeta (Settings → Pages → Deploy from a branch → carpeta `/frontend`, o mueve su contenido
   a la raíz del repo si prefieres servir desde `/`).
2. GitHub Pages publicará `index.html` en `https://<usuario>.github.io/<repositorio>/`.

Si en el futuro rehaces el Worker con otro nombre/subdominio, recuerda actualizar
`URL_API_BASE` en [`frontend/main.js`](frontend/main.js).

## Notas de diseño

- El alfabeto se define una sola vez ("Aplicar alfabeto") y se reutiliza tanto para cifrar
  como para descifrar, tal como pide el enunciado (es la pauta para todo lo demás).
- Los caracteres del texto que no pertenecen al alfabeto definido se dejan sin modificar
  (se "pasan por alto"), tanto al cifrar como al descifrar.
- El backend es Unicode-aware: el alfabeto puede incluir letras latinas, dígitos, signos de
  puntuación, o símbolos de cualquier otro alfabeto/idioma (árabe, chino, etc.), cada uno
  contando como un solo carácter del conjunto, sin importar cuántos bytes ocupe en UTF-8. El
  alfabeto y el texto se normalizan a la forma Unicode NFC al llegar a la API, para evitar
  inconsistencias cuando el "mismo" carácter se escribe con distinta representación interna.
- El texto a cifrar/descifrar tiene un límite de 10 000 caracteres (definido tras medir el
  rendimiento real, ver `PRUEBAS_Y_LIMITACIONES.md`).
