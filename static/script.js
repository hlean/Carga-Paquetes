const table = document.getElementById("dataTable");
const tbody = table.querySelector("tbody");
const mensajeError = document.getElementById("mensajeError");

const COLUMNAS = 10; 
const COLUMNA_NRO = 0;

function agregarFila() {
    const fila = tbody.insertRow();
    for (let i = 0; i < COLUMNAS; i++) {
        const celda = fila.insertCell(i);
        celda.contentEditable = i !== COLUMNA_NRO ? "true" : "false";
    }
    actualizarNumerosFila();
}

function actualizarNumerosFila() {
    Array.from(tbody.rows).forEach((fila, index) => {
        fila.cells[COLUMNA_NRO].innerText = index;
    });
}

function asegurarFilaExtra() {
    if (tbody.rows.length === 0) {
        agregarFila();
    }
}

function procesarPegado(evento) {
    evento.preventDefault();

    const texto = (evento.clipboardData || window.clipboardData).getData("Text").trim();
    const filas = texto.split("\n");

    filas.forEach((filaTexto, i) => {
        const datos = filaTexto.split("\t");
        if (tbody.rows.length <= i) {
            agregarFila();
        }
        const celdas = tbody.rows[i].cells;
        datos.forEach((valor, j) => {
            if (j + 1 < COLUMNAS) {
                celdas[j + 1].innerText = valor.trim(); // +1 para saltar "Nro"
            }
        });
    });
    asegurarFilaExtra();
    actualizarNumerosFila();
}

function enviarDatosAlServidor() {
    const datos = Array.from(tbody.rows).map(fila => 
        Array.from(fila.cells).map(celda => celda.innerText.trim())
    );

    const payload = {
        data: datos,
        tarifa_IGR: document.getElementById("tarifa_IGR").value,
        tarifa_OTROS: document.getElementById("tarifa_OTROS").value
    };

    fetch("/procesar_datos", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(res => {
        if (res.success === false) {
            mensajeError.innerHTML = `<p>Filas que fallaron en el formato: ${res.failed_rows.join(", ")}</p>`;
        } else {
            window.location.href = res.download_url;
        }
    })
    .catch(err => alert("Error al enviar los datos: " + err));
}
table.addEventListener("paste", procesarPegado);

document.addEventListener("DOMContentLoaded", () => {
    asegurarFilaExtra();
    actualizarNumerosFila();
});
