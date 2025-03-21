from flask import Flask, render_template, request, redirect, send_from_directory, jsonify
import os
import pandas as pd
from Carga import procesar_datos 

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/procesar_datos", methods=["POST"])
def procesar_datos_tabla():
    try:
        data = request.json.get("data")
        tarifa_IGR = float(request.json.get("tarifa_IGR"))
        tarifa_OTROS = float(request.json.get("tarifa_OTROS"))

        columnas = ["DESTINO", "FECHA", "HOTEL", "TARIFA AMICHI x PAX", "VTA TTL x 2 PAXS", "BASE", "CANT DE HAB", "CANT DE PAX", "VUELOS"]
        df = pd.DataFrame(data, columns=columnas)
        df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce")
        df_procesado = procesar_datos(df, tarifa_IGR, tarifa_OTROS)

        output_file = "Resultados_Datos.xlsx"
        output_path = os.path.join("/tmp", output_file)
        df_procesado.to_excel(output_path, index=False)

        filas_fallidas = df_procesado[df_procesado.isnull().any(axis=1)].index.tolist()
        
        if filas_fallidas:
            return jsonify({
                "success": False,
                "error": "Algunas filas no pudieron ser procesadas por formato erroneo.",
                "failed_rows": filas_fallidas
            }), 400
        
        return jsonify({"success": True, "download_url": f"/download/{output_file}"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/download/<filename>")
def download(filename):
    # Se usa el directorio temporal /tmp de Vercel
    return send_from_directory(directory="/tmp", path=filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
