function agregarFila() {
    let tabla = document.getElementById("dataTable").getElementsByTagName('tbody')[0];
    let nuevaFila = tabla.insertRow();
    for (let i = 0; i < 9; i++) {
        let celda = nuevaFila.insertCell(i);
        celda.contentEditable = "true";
    }
}

document.getElementById("dataTable").addEventListener("paste", function (evento) {
    evento.preventDefault();
    let datosPortapapeles = evento.clipboardData || window.clipboardData;
    let datosPegados = datosPortapapeles.getData("Text").trim();
    
    let filas = datosPegados.split("\n"); 
    let cuerpoTabla = document.getElementById("dataTable").getElementsByTagName('tbody')[0];

    filas.forEach((textoFila, indiceFila) => {
        let datosFila = textoFila.split("\t");
        
        if (cuerpoTabla.rows.length <= indiceFila) {
            agregarFila();
        }

        let celdas = cuerpoTabla.rows[indiceFila].cells;
        datosFila.forEach((textoCelda, indiceColumna) => {
            if (indiceColumna < celdas.length) {
                celdas[indiceColumna].innerText = textoCelda.trim();
            }
        });
    });
    asegurarFilaExtra();
});

function enviarDatosAlServidor() {
    let tabla = document.getElementById("dataTable");
    let filas = tabla.getElementsByTagName("tr");
    let datos = [];

    for (let i = 1; i < filas.length; i++) { 
        let datosFila = [];
        let celdas = filas[i].getElementsByTagName("td");
        for (let j = 0; j < celdas.length; j++) {
            datosFila.push(celdas[j].innerText.trim());
        }
        datos.push(datosFila);
    }

    let tarifa_IGR = document.getElementById("tarifa_IGR").value;
    let tarifa_OTROS = document.getElementById("tarifa_OTROS").value;

    let cargaUtil = {
        "data": datos,
        "tarifa_IGR": tarifa_IGR,
        "tarifa_OTROS": tarifa_OTROS
    };

    fetch("/procesar_datos", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(cargaUtil)
    })
    .then(respuesta => respuesta.json())
    .then(datos => {
        window.location.href = datos.download_url;
    })
    .catch(error => alert("Error al enviar los datos: " + error));
}
document.addEventListener("DOMContentLoaded", asegurarFilaExtra);
