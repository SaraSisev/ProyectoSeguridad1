const URL_API_BASE =
  location.hostname === "localhost" || location.hostname === "127.0.0.1"
    ? "http://127.0.0.1:8787"
    : "https://CAMBIA-ESTA-URL.workers.dev";

const LIMITE_ALFABETO = 256;

let SFEstadoAlfabeto = null;

async function SF29(ruta, cuerpo) {
  const respuesta = await fetch(`${URL_API_BASE}${ruta}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(cuerpo),
  });
  const datos = await respuesta.json();
  if (!respuesta.ok) {
    throw new Error(datos.error || "Error en la solicitud al servidor.");
  }
  return datos;
}

function SF30(mensaje, esError) {
  const estado = document.getElementById("alphabet-status");
  const error = document.getElementById("alphabet-error");
  if (esError) {
    error.textContent = mensaje;
    estado.textContent = "";
  } else {
    error.textContent = "";
    estado.textContent = mensaje;
  }
}

async function SF31(evento) {
  evento.preventDefault();
  const entrada = document.getElementById("alphabet-input").value;
  try {
    const datos = await SF29("/api/alfabeto/validar", { alfabeto: entrada });
    SFEstadoAlfabeto = entrada;
    try {
      localStorage.setItem("alfabetoActual", entrada);
    } catch (_) {}
    SF30(`Alfabeto aplicado (${datos.longitud} caracteres).`, false);
  } catch (err) {
    SFEstadoAlfabeto = null;
    SF30(err.message, true);
  }
}

async function SF32(evento) {
  evento.preventDefault();
  const error = document.getElementById("encrypt-error");
  const resultado = document.getElementById("encrypt-result");
  error.textContent = "";
  resultado.textContent = "";

  if (!SFEstadoAlfabeto) {
    error.textContent = "Primero debes aplicar un alfabeto válido.";
    return;
  }

  const metodo = document.getElementById("encrypt-method").value;
  const texto = document.getElementById("encrypt-text").value;
  const cuerpo = { alfabeto: SFEstadoAlfabeto, metodo, texto };

  if (metodo === "CESAR") {
    cuerpo.desplazamiento = Number(document.getElementById("encrypt-shift").value);
  }

  try {
    const datos = await SF29("/api/cifrar", cuerpo);
    resultado.textContent = datos.resultado;
  } catch (err) {
    error.textContent = err.message;
  }
}

async function SF33(evento) {
  evento.preventDefault();
  const error = document.getElementById("decrypt-error");
  const metodoResultado = document.getElementById("decrypt-method-result");
  const shiftResultado = document.getElementById("decrypt-shift-result");
  const textoResultado = document.getElementById("decrypt-text-result");

  error.textContent = "";
  metodoResultado.textContent = "—";
  shiftResultado.textContent = "—";
  textoResultado.textContent = "";

  if (!SFEstadoAlfabeto) {
    error.textContent = "Primero debes aplicar un alfabeto válido.";
    return;
  }

  const texto = document.getElementById("decrypt-text").value;

  try {
    const datos = await SF29("/api/descifrar", { alfabeto: SFEstadoAlfabeto, texto });
    metodoResultado.textContent = datos.metodo === "ATBASH" ? "Atbash" : "César";
    shiftResultado.textContent =
      datos.desplazamiento !== null && datos.desplazamiento !== undefined
        ? datos.desplazamiento
        : "No aplica";
    textoResultado.textContent = datos.resultado;
  } catch (err) {
    error.textContent = err.message;
  }
}

function SF34(idOrigen) {
  const origen = document.getElementById(idOrigen);
  navigator.clipboard.writeText(origen.textContent || "").catch(() => {});
}

function SF35() {
  const metodo = document.getElementById("encrypt-method");
  const grupoShift = document.getElementById("caesar-shift-group");
  const campoShift = document.getElementById("encrypt-shift");
  const arriba = document.getElementById("shift-up");
  const abajo = document.getElementById("shift-down");

  function actualizarVisibilidad() {
    grupoShift.style.display = metodo.value === "CESAR" ? "" : "none";
  }

  metodo.addEventListener("change", actualizarVisibilidad);
  actualizarVisibilidad();

  arriba.addEventListener("click", () => {
    campoShift.value = Math.min(25, Number(campoShift.value) + 1);
  });
  abajo.addEventListener("click", () => {
    campoShift.value = Math.max(1, Number(campoShift.value) - 1);
  });
}

function SF36() {
  const entrada = document.getElementById("alphabet-input");
  const contador = document.getElementById("alphabet-counter");

  function actualizar() {
    const longitud = entrada.value.length;
    contador.textContent = `${longitud} / ${LIMITE_ALFABETO} caracteres`;
    contador.style.color = longitud > LIMITE_ALFABETO ? "var(--error)" : "";
  }

  entrada.addEventListener("input", actualizar);
  actualizar();
}

function SF37() {
  try {
    const guardado = localStorage.getItem("alfabetoActual");
    if (guardado) {
      document.getElementById("alphabet-input").value = guardado;
      SFEstadoAlfabeto = guardado;
      SF30(`Alfabeto restaurado (${guardado.length} caracteres).`, false);
    }
  } catch (_) {}

  document.getElementById("alphabet-form").addEventListener("submit", SF31);
  document.getElementById("encrypt-form").addEventListener("submit", SF32);
  document.getElementById("decrypt-form").addEventListener("submit", SF33);
  document.getElementById("copy-encrypt-result").addEventListener("click", () => SF34("encrypt-result"));
  document.getElementById("copy-decrypt-result").addEventListener("click", () => SF34("decrypt-text-result"));

  SF35();
  SF36();
}

document.addEventListener("DOMContentLoaded", SF37);
