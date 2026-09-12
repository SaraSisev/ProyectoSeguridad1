# Sistema de Cifrado y Descifrado — César / Atbash

Proyecto académico de Seguridad. Permite definir un alfabeto propio (hasta 256 caracteres,
incluyendo símbolos especiales de cualquier idioma o codificación), cifrar con César o
Atbash, y descifrar de forma **automática** (sin que el usuario elija el método), usando
análisis de frecuencias en español al estilo de Al-Kindi.

Ver [`FUNCIONES.md`](FUNCIONES.md) para la documentación técnica función por función
(identificadores `SFx`).

## Estructura

```
front/    -> sitio estático (HTML/CSS/JS), se publica en GitHub Pages
backend/  -> Cloudflare Worker en Python (beta "Python Workers"), se publica en Cloudflare
  src/
    alfabeto.py             -> validación del alfabeto y utilidades de índices/desplazamiento
    cifrado.py               -> cifrado César y Atbash
    descifrado.py            -> César inverso + autodetección automática (Atbash o César)
    datos_espanol.py         -> datos del idioma: corpus propio, frecuencias, n-gramas, diccionario
    analisis_frecuencia.py   -> motor de Al-Kindi (calcula y combina 9 componentes de puntaje)
    entry.py                 -> punto de entrada del Worker (rutas HTTP, CORS)
```

## Backend — Cloudflare Workers (Python)

Requisitos: Node.js (para la CLI `wrangler`) y una cuenta de Cloudflare.

```bash
npm install -g wrangler
cd backend
wrangler login
wrangler deploy
```

Al terminar, `wrangler` imprime la URL pública del Worker, algo como:

```
https://cifrado-cesar-atbash-backend.<tu-subdominio>.workers.dev
```

Para probar en local antes de desplegar:

```bash
cd backend
wrangler dev --local --port 8787
```

Y en otra terminal, sirve el frontend en local:

```bash
cd front
python -m http.server 5500
```

`front/main.js` detecta automáticamente cuando la página se abre desde `localhost` o
`127.0.0.1` y en ese caso usa `http://127.0.0.1:8787` como backend, sin necesidad de editar
nada. Abre `http://127.0.0.1:5500` en el navegador para probar todo el flujo completo.

Endpoints expuestos (todos `POST`, cuerpo y respuesta en JSON, con CORS abierto):

- `POST /api/alfabeto/validar` — body `{ "alfabeto": "..." }`
- `POST /api/cifrar` — body `{ "alfabeto": "...", "metodo": "CESAR"|"ATBASH", "texto": "...", "desplazamiento": 1-25 (solo si CESAR) }`
- `POST /api/descifrar` — body `{ "alfabeto": "...", "texto": "..." }` (el método y el desplazamiento se detectan automáticamente)

## Frontend — GitHub Pages

1. Despliega primero el backend y copia la URL que te dio `wrangler`.
2. Abre [`front/main.js`](front/main.js) y reemplaza la primera línea:

   ```js
   const URL_API_BASE = "https://CAMBIA-ESTA-URL.workers.dev";
   ```

   por la URL real de tu Worker.
3. Sube la carpeta `front/` a un repositorio de GitHub y activa GitHub Pages apuntando a esa
   carpeta (Settings → Pages → Deploy from a branch → carpeta `/front`, o mueve su contenido
   a la raíz del repo si prefieres servir desde `/`).
4. GitHub Pages publicará `index.html` en `https://<usuario>.github.io/<repositorio>/`.

## Notas de diseño

- El alfabeto se define una sola vez ("Aplicar alfabeto") y se reutiliza tanto para cifrar
  como para descifrar, tal como pide el enunciado (es la pauta para todo lo demás).
- Los caracteres del texto que no pertenecen al alfabeto definido se dejan sin modificar
  (se "pasan por alto"), tanto al cifrar como al descifrar.
- El backend es Unicode-aware: el alfabeto puede incluir letras latinas, dígitos, signos de
  puntuación, o símbolos de cualquier otro alfabeto/idioma (árabe, chino, etc.), cada uno
  contando como un solo carácter del conjunto, sin importar cuántos bytes ocupe en UTF-8.
