#  Exporta registros de MySQL a Access (.accdb) por medio,
#  usando la carpeta definida en Setting.ini → RutaBD.
#  Mantiene en la tabla 'servicio' la marca de la última

import os
import pyodbc
import mysql.connector
from mysql.connector import Error
from ConexionBD import ConexionBD
import Controller_Error
from datetime import datetime, timedelta, time
import Controller_Error
import Setting as setting_mod 
_cfg = setting_mod.Setting.Consultar_datos_de_archivo_txt()  
CARPETA_ACCESS = (_cfg.RutaBD if _cfg and _cfg.RutaBD else "DB_Access")

def _nombre_archivo_access(nombre_medio: str,
                           medio_id: int,
                           carpeta_destino: str = CARPETA_ACCESS) -> str:
    filename = f"{nombre_medio.replace(' ', '_')}_medio_{medio_id}.accdb"
    return os.path.join(carpeta_destino, filename)

def ObtenerMediosDeProduccion():
    setting = ConexionBD.ObtenerSettingCompleto()
    if setting is None:
        return []
    conn = ConexionBD.ConectarBDAbrir(setting)
    if conn is None:
        return []
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(
                """
                SELECT
                    ID_Medios_de_produccion AS id,
                    Nombre,           
                    Descripcion,
                    Linea_produccion_id
                FROM medios_de_produccion
                """
            )
            return cursor.fetchall()
    except Exception as err:
        Controller_Error.Logs_Error.CapturarEvento(
            "ConsultaSQL", "ObtenerMediosDeProduccion", str(err)
        )
        return []
    finally:
        conn.close()

def crear_bases_access_por_medio(lista_medios,carpeta_destino: str = CARPETA_ACCESS):
    """Genera la .accdb del medio si no existe todavía."""
    os.makedirs(carpeta_destino, exist_ok=True)

    for medio in lista_medios:
        ruta = _nombre_archivo_access(medio["Nombre"], medio["id"], carpeta_destino)
        if os.path.exists(ruta):
            continue 
        try:
            conn_str = rf"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};Dbq={ruta};"
            with pyodbc.connect(conn_str, autocommit=True) as conn, conn.cursor() as c:

                # Tabla principal
                c.execute(
                    """
                    CREATE TABLE registros (
                        IDregistros AUTOINCREMENT PRIMARY KEY,
                        Fecha      DATE,
                        Hora       TIME,
                        Modelo     TEXT,
                        Serial     TEXT,
                        Resultado  TEXT,
                        Detalle    TEXT,
                        Medio      TEXT,
                        Hostname   TEXT,
                        Planta     TEXT,
                        Banda      TEXT,
                        Box        TEXT,
                        IMEI       TEXT,
                        SKU        TEXT,
                        TestTime   TEXT,
                        runtime    TEXT,
                        ModelFile TEXT,
                        medio_id   INT
                    )
                    """
                )
                # Tabla de control
                c.execute(
                    """
                    CREATE TABLE servicio (
                        id AUTOINCREMENT PRIMARY KEY,
                        ultima_ejecucion DATETIME
                    )
                    """
                )
                c.execute("INSERT INTO servicio (ultima_ejecucion) VALUES (NULL)")

        except Exception as e:
            Controller_Error.Logs_Error.CapturarEvento(
                "ConsultaSQL", "crear_bases_access_por_medio", str(e)
            )

def Obtener_Registros_Medios_Produccion(medio_id: int, fecha_desde=None):
    setting = ConexionBD.ObtenerSettingCompleto()
    if setting is None:
        return []
    conn = ConexionBD.ConectarBDAbrir(setting)
    if conn is None:
        return []

    try:
        with conn.cursor(dictionary=True) as cursor:
            sql = """
                SELECT
                    Fecha, Hora, Modelo, Serial, Resultado, Detalle,Medio,
                    hostname, Planta, Banda, Box, IMEI, SKU,
                    TestTime, Runtime, ModelFile, medio_id
                FROM registros
                WHERE medio_id = %s
            """
            params = [medio_id]

            if fecha_desde:
                sql += " AND Fecha >= %s"
                params.append(fecha_desde)

            cursor.execute(sql, tuple(params))
            return cursor.fetchall()
    except Exception as err:
        Controller_Error.Logs_Error.CapturarEvento(
            "ConsultaSQL", "Obtener_Registros_Medios_Produccion", str(err)
        )
        return []
    finally:
        conn.close()

# Primero, define el mapeo de campos al inicio de la función
mapeo_campos = {
    "Fecha": "Fecha",
    "Hora": "Hora",
    "Modelo": "Modelo",
    "Serial": "Serial",
    "Resultado": "Resultado",
    "Detalle": "Detalle",
    "Medio": "Medio",
    "hostname": "Hostname",  # Nota: mapeo de hostname en minúscula a Hostname
    "Planta": "Planta",
    "Banda": "Banda",
    "Box": "Box",
    "IMEI": "IMEI",
    "SKU": "SKU",
    "TestTime": "TestTime",
    "Runtime": "Runtime",
    "ModelFile": "ModelFile",
    "medio_id": "Medio_id"
}

def obtener_registros_existentes(cursor, medio_id):
    """Obtiene los registros existentes para un medio específico."""
    try:
        cursor.execute("""
            SELECT Fecha, Serial
            FROM registros 
            WHERE medio_id = ?
        """, (medio_id,))
        # Formatea la fecha de Access utilizando strftime
        return {(
            row.Fecha.strftime("%Y-%m-%d") if hasattr(row.Fecha, "strftime") else str(row.Fecha), 
            row.Serial
        ) for row in cursor.fetchall()}
    except Exception as e:
        Controller_Error.Logs_Error.CapturarEvento(
            "ConsultaSQL", "obtener_registros_existentes", str(e)
        )
        return set()

    

def insertar_registros_en_access(registros, archivo_access: str):
    conn_str = rf"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};Dbq={archivo_access};"
    try:
        conn = pyodbc.connect(conn_str, autocommit=False)
        c = conn.cursor()
    except Exception as e:
        Controller_Error.Logs_Error.CapturarEvento(
            "ConsultaSQL", "insertar_registros_en_access",
            f"No pude abrir Access: {e}"
        )
        return

    try:
        # Delete records older than 40 days
        fecha_limite = datetime.now().date() - timedelta(days=40)
        c.execute("DELETE FROM registros WHERE Fecha < ?", (fecha_limite,))
        
        # Obtener registros existentes
        if registros and len(registros) > 0:
            medio_id = registros[0].get('medio_id')
            registros_existentes = obtener_registros_existentes(c, medio_id)
        else:
            registros_existentes = set()

        nuevas = []
        for r in registros:
            # Convertir la fecha a string con formato "YYYY-MM-DD"
            fecha_str = (r['Fecha'].strftime("%Y-%m-%d") if hasattr(r['Fecha'], "strftime") else str(r['Fecha']))
            registro_key = (fecha_str, r['Serial'])
            if registro_key in registros_existentes:
                continue

            # Convertir r["Hora"] al formato de Access
            hora_td = r["Hora"]
            if isinstance(hora_td, timedelta):
                total_s = int(hora_td.total_seconds())
                h = (total_s // 3600) % 24
                m = (total_s % 3600) // 60
                s = total_s % 60
                hora_val = time(h, m, s)
            else:
                hora_val = hora_td

            # Crear registro normalizado
            registro_normalizado = {}
            for k, v in r.items():
                if k in mapeo_campos:
                    registro_normalizado[mapeo_campos[k]] = v if v is not None else ""

            registro_normalizado["Hora"] = hora_val

            nuevas.append((
                registro_normalizado.get("Fecha"),
                registro_normalizado.get("Hora"),
                registro_normalizado.get("Modelo", ""),
                registro_normalizado.get("Serial", ""),
                registro_normalizado.get("Resultado", ""),
                registro_normalizado.get("Detalle", ""),
                registro_normalizado.get("Medio", ""),
                registro_normalizado.get("Hostname", ""),
                registro_normalizado.get("Planta", ""),
                registro_normalizado.get("Banda", ""),
                registro_normalizado.get("Box", ""),
                registro_normalizado.get("IMEI", ""),
                registro_normalizado.get("SKU", ""),
                registro_normalizado.get("TestTime", ""),
                registro_normalizado.get("Runtime", ""),
                registro_normalizado.get("ModelFile", ""),
                registro_normalizado.get("Medio_id")
            ))

        if nuevas:
            print(f"Insertando {len(nuevas)} nuevos registros...")
            c.executemany(
                """
                INSERT INTO registros (
                    Fecha, Hora, Modelo, Serial, Resultado, Detalle, Medio,
                    Hostname, Planta, Banda, Box, IMEI, SKU,
                    TestTime, Runtime, ModelFile, Medio_id
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                nuevas
            )
            
            # Update ultima_ejecucion with current timestamp
            current_time = datetime.now()
            c.execute("UPDATE servicio SET ultima_ejecucion = ? WHERE id = 1", (current_time,))
            
            if c.rowcount == 0:
                c.execute("INSERT INTO servicio (ultima_ejecucion) VALUES (?)", (current_time,))
            
            conn.commit()
        else:
            print("No hay nuevos registros para insertar")
            
    except Exception as e:
        conn.rollback()
        Controller_Error.Logs_Error.CapturarEvento(
            "ConsultaSQL", "insertar_registros_en_access",
            f"Error processing records: {e}"
        )
    finally:
        conn.close()

def exportar_todos_los_medios_a_access():
    try:
        medios = ObtenerMediosDeProduccion()
        print(f"Medios obtenidos: {medios}")
    except Exception as e:
        Controller_Error.Logs_Error.CapturarEvento(
            "ConsultaSQL", "exportar_todos_los_medios_a_access", f"Error al obtener medios: {e}"
        )
        return

    try:
        crear_bases_access_por_medio(medios, CARPETA_ACCESS)
        print("Bases Access creadas correctamente.")
    except Exception as e:
        Controller_Error.Logs_Error.CapturarEvento(
            "ConsultaSQL", "exportar_todos_los_medios_a_access", f"Error al crear bases Access: {e}"
        )
        return

    for medio in medios:
        try:
            ruta = _nombre_archivo_access(medio["Nombre"], medio["id"], CARPETA_ACCESS)
            print(f"Procesando medio {medio['Nombre']}")
            
            
            fecha_desde = datetime.now().date() - timedelta(days=40)

            registros = Obtener_Registros_Medios_Produccion(medio["id"], fecha_desde)
            print(f"Registros obtenidos para el medio {medio['Nombre']}: {len(registros)}")
            
            insertar_registros_en_access(registros, ruta)
            print(f"Registros insertados correctamente en {ruta}")
            
        except Exception as e:
            Controller_Error.Logs_Error.CapturarEvento(
                "ConsultaSQL", "exportar_todos_los_medios_a_access",
                f"Error processing medio {medio['Nombre']}: {e}"
            )
            continue

if __name__ == "__main__":
    exportar_todos_los_medios_a_access()
