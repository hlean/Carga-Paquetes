import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta

def cargar_datos(file):
    df = pd.read_excel(file)
    df.columns = df.iloc[0]
    df.columns = ["DESTINO", "FECHA", "HOTEL", "TARIFA AMICHI x PAX", "VTA TTL x 2 PAXS", "BASE", "CANT DE HAB", "CANT DE PAX", "VUELOS"]
    df["FECHA"] = pd.to_datetime(df["FECHA"], format="%d-%m-%Y", errors="coerce")
    df = df[df["DESTINO"] != "DESTINO"].reset_index(drop=True)  # Eliminar encabezados repetidos
    df = df.dropna(how='all').reset_index(drop=True)  # Eliminar filas vacías
    df = df.dropna(subset=["FECHA"]).reset_index(drop=True)  # Eliminar filas sin fecha
    return df

def procesar_datos(df, tarifa_IGR, tarifa_OTROS):
    def separar_vuelos(df):
        vuelos_separados = df['VUELOS'].str.split(r'//|/', expand=True)
        for i in range(4):
            df[f"EXTRA {i + 1}"] = vuelos_separados[i] if i < vuelos_separados.shape[1] else ""

        for index, row in df.iterrows():
            extra_1 = row['EXTRA 1'] if row['EXTRA 1'] is not None else ""
            extra_2 = row['EXTRA 2'] if row['EXTRA 2'] is not None else ""
            extra_3 = row['EXTRA 3'] if row['EXTRA 3'] is not None else ""
            extra_4 = row['EXTRA 4'] if row['EXTRA 4'] is not None else ""

            if extra_1.strip() != "" and extra_2.strip() != "" and extra_3.strip() != "" and extra_4.strip() == "":
                df.at[index, 'EXTRA 2'] = extra_3
                df.at[index, 'EXTRA 3'] = ""

        return df
    
    df = separar_vuelos(df)

    def convertir_fecha(fecha_str, anio=2025):
        try:
            return datetime.strptime(fecha_str + str(anio), "%d%b%Y").strftime("%d/%m/%Y")
        except ValueError:
            return None  

    def convertir_hora(hora_str):
        try:
            return datetime.strptime(hora_str, "%H%M").time()  # Devuelve un objeto time
        except ValueError:
            return None 
    
    def calcular_duracion(hora_inicio, hora_fin):
        if hora_inicio and hora_fin:
            t1 = datetime.combine(datetime.min, hora_inicio)
            t2 = datetime.combine(datetime.min, hora_fin)

            if t2 < t1:
                t2 += timedelta(days=1)

            duracion = t2 - t1
            horas, minutos = divmod(duracion.seconds, 3600)
            minutos = (duracion.seconds % 3600) // 60 
            return f"{horas:02}:{minutos:02}"
        return None 

    def limpiar_valor(valor):
        if isinstance(valor, str): 
            valor = valor.replace('$', '').replace(',', '')  
        try:
            return float(valor)  
        except ValueError:
            return np.nan 

    def calcular_base_simple(texto, destino):
        try:
            tarifa_simple = df.loc[df["VUELOS"] == texto, "VTA TTL x 2 PAXS"].values[0]
            base = df.loc[df["VUELOS"] == texto, "BASE"].values[0]

            if pd.isna(tarifa_simple) or pd.isna(base):
                return np.nan 

            tarifa_simple = limpiar_valor(tarifa_simple)

            tarifa_simple = float(tarifa_simple)
            if base == "SGL":
                if destino == "IGR":
                    return round(tarifa_simple * (1 + tarifa_IGR / 100), 0)
                else:
                    return round(tarifa_simple * (1 + tarifa_OTROS / 100), 0)
            else:
                return ""    
        except Exception:
            return np.nan 

    def calcular_base_doble(texto, destino):
        try:
            tarifa_doble = df.loc[df["VUELOS"] == texto, "TARIFA AMICHI x PAX"].values[0]
            base = df.loc[df["VUELOS"] == texto, "BASE"].values[0]

            if pd.isna(tarifa_doble) or pd.isna(base):
                return np.nan 

            tarifa_doble = limpiar_valor(tarifa_doble)

            tarifa_doble = float(tarifa_doble) 
            if base == "DBL":      
                if destino == "IGR":
                    return round(tarifa_doble * (1 + tarifa_OTROS / 100), 0)
                else:
                    return round(tarifa_doble * (1 + tarifa_OTROS / 100), 0)            
            else:
                return  ""   
        except Exception:
            return np.nan 

    def calcular_cantidad_dias(fecha_ida, fecha_vuelta):
        if fecha_ida and fecha_vuelta:
            fecha_ida = pd.to_datetime(fecha_ida, dayfirst=True).date()  
            fecha_vuelta = pd.to_datetime(fecha_vuelta, dayfirst=True).date() 

            if fecha_vuelta < fecha_ida:
                fecha_ida, fecha_vuelta = fecha_vuelta, fecha_ida

            duracion_viaje = (fecha_vuelta - fecha_ida).days
            return duracion_viaje
        return None

    def crear_codigo(destino_ida, destino_vuelta, texto):
        hotel = df.loc[df["VUELOS"] == texto, "HOTEL"].values[0]
        codigo = destino_ida + "-" + destino_vuelta + "-" + hotel
        return codigo.replace(" ", "-")

    def extraer_vuelos(texto, row_index):
        texto_sin_espacios = re.sub(r'\s+', '', str(texto)) 
        pattern = r'(\d{2}[A-Z]{3})([A-Z]{2}\d+)([A-Z]{3})([A-Z]{3})(\d{4})(\d{4})'
        vuelos = re.findall(pattern, str(texto_sin_espacios)) 
        
        if len(vuelos) == 2: 
            ida, vuelta = vuelos        
            destino = ida[3]
            hora_salida_ida = convertir_hora(ida[4])
            hora_llegada_ida = convertir_hora(ida[5])
            hora_salida_vuelta = convertir_hora(vuelta[4])
            hora_llegada_vuelta = convertir_hora(vuelta[5])
            fecha_idea = convertir_fecha(ida[0])
            fecha_vuelta = convertir_fecha(vuelta[0])
            duracion_ida = calcular_duracion(hora_salida_ida, hora_llegada_ida)
            duracion_vuelta = calcular_duracion(hora_salida_vuelta, hora_llegada_vuelta)
            cantidad_noches = calcular_cantidad_dias(fecha_idea, fecha_vuelta)
            codigo = crear_codigo(ida[2], ida[3], texto)
            
            return pd.Series([
                codigo, "Si", fecha_idea, fecha_vuelta, cantidad_noches, "Vuelo", "Si", 
                ida[2], fecha_idea, hora_salida_ida, 0, duracion_ida, "AR", 
                ida[3], fecha_idea, hora_llegada_ida, vuelta[2], fecha_vuelta, hora_salida_vuelta, 0,
                duracion_vuelta, "AR", vuelta[3], fecha_vuelta, hora_llegada_vuelta, 
                calcular_base_simple(texto, destino),
                calcular_base_doble(texto, destino), "", "",
                "ARS", "Si", "", "", "", ""
            ])
        '''
        if len(vuelos) == 3:
            inicial = vuelos[0]
            ultimo = vuelos[2]

            destino = inicial[3]
            hora_salida_ida = convertir_hora(inicial[4])
            hora_llegada_ida = convertir_hora(inicial[5])
            hora_salida_vuelta = convertir_hora(ultimo[4])
            hora_llegada_vuelta = convertir_hora(ultimo[5])
            fecha_idea = convertir_fecha(inicial[0])
            fecha_vuelta = convertir_fecha(ultimo[0])
            duracion_ida = calcular_duracion(hora_salida_ida, hora_llegada_ida)
            duracion_vuelta = calcular_duracion(hora_salida_vuelta, hora_llegada_vuelta)
            cantidad_noches = calcular_cantidad_dias(fecha_idea, fecha_vuelta)
            codigo = crear_codigo(inicial[2], inicial[3], texto)
            
            return pd.Series([
                codigo, "Si", fecha_idea, fecha_vuelta, cantidad_noches, "Vuelo", "Si", 
                inicial[2], fecha_idea, hora_salida_ida, 0, duracion_ida, "AR", 
                inicial[3], fecha_idea, hora_llegada_ida, ultimo[2], fecha_vuelta, hora_salida_vuelta, 0,
                duracion_vuelta, "AR", ultimo[3], fecha_vuelta, hora_llegada_vuelta, 
                calcular_base_simple(texto, destino),
                calcular_base_doble(texto, destino), "", "",
                "ARS", "Si", "", "", "", ""
            ])
        '''
        if len(vuelos) == 4:
            ida_1, vuelta_1 = vuelos[0], vuelos[1]
            ida_2, vuelta_2 = vuelos[2], vuelos[3]
        
            destino = ida_1[3]
            hora_salida_ida = convertir_hora(ida_1[4])
            hora_llegada_ida = convertir_hora(vuelta_1[5])
            hora_salida_vuelta = convertir_hora(vuelta_1[4])
            hora_llegada_vuelta = convertir_hora(vuelta_2[5])
            fecha_idea = convertir_fecha(ida_1[0])
            fecha_vuelta = convertir_fecha(vuelta_2[0])
            duracion_ida = calcular_duracion(hora_salida_ida, hora_llegada_ida)
            duracion_vuelta = calcular_duracion(hora_salida_vuelta, hora_llegada_vuelta)
            cantidad_noches = calcular_cantidad_dias(fecha_idea, fecha_vuelta)
            codigo = crear_codigo(ida_1[2], vuelta_1[3], texto)

            return pd.Series([
                codigo, "Si", fecha_idea, fecha_vuelta, cantidad_noches, "Vuelo", "Si", 
                ida_1[2], fecha_idea, hora_salida_ida, 0, duracion_ida, "AR", 
                vuelta_1[3], fecha_idea, hora_llegada_ida, ida_2[2], fecha_vuelta, hora_salida_vuelta, 0,
                duracion_vuelta, "AR", vuelta_2[3], fecha_vuelta, hora_llegada_vuelta, 
                calcular_base_simple(texto, destino),
                calcular_base_doble(texto, destino), "", "",
                "ARS", "Si", "", "", "", ""
            ])
        
        return pd.Series([None] * 35)

    df_vuelos = df.apply(lambda row: extraer_vuelos(row["VUELOS"], row.name), axis=1)
    df_vuelos.columns = [
        "ID Paquete","Incluye transfer","Fecha de salida","Fecha de regreso","Cantidad de Noches","Tipo de transporte de origen","Info de vuelo",
        "Ciudad de salida","Día salida ida","Horario salida ida","Cantidad escalas ida","Duración total ida","Iata aerolínea ida",
        "Ciudad de llegada","Día llegada ida","Horario llegada ida","Ciudad de salida vuelta","Día salida vuelta","Horario salida vuelta","Cantidad escalas vuelta",
        "Duración total vuelta","Iata aerolínea vuelta","Ciudad de llegada vuelta","Día llegada vuelta","Horario llegada vuelta",
        "Precio single (por persona con impuestos)","Precio doble (por pesona con imp)","Precio triple (por persona con imp)","Precio cuadruple (por persona con imp)",
        "Moneda","Incluye equipaje","Impuesto single (por persona)","Impuesto doble (por pesona)","Impuesto triple (por persona)","Impuesto cuadruple (por persona)"
    ]

    return df_vuelos
