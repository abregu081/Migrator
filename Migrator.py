import ConsultaSQL
import Controller_Error
import pyodbc
import os
import ConexionBD

# ---------------------------------------------------------
# Pruebas por si se rompe algo :'D
# ---------------------------------------------------------
def _prueba_conexion_mysql():
    """Verifica que MySQL responda y devuelva al menos un medio."""
    try:
        medios = ConsultaSQL.ObtenerMediosDeProduccion()
        if not medios:
            raise RuntimeError("Conexión MySQL OK, pero la consulta está vacía.")
        print(f"[Prueba] Conexión MySQL OK.  Medios encontrados: {len(medios)}")
        return True
    except Exception as e:
        Controller_Error.Logs_Error.CapturarEvento("MainTest", "_prueba_conexion_mysql", str(e))
        return False

def _prueba_archivo_access(carpeta_destino):
    """Comprueba que exista al menos un .accdb con la tabla 'registros'."""
    try:
        accdbs = [f for f in os.listdir(carpeta_destino) if f.lower().endswith(".accdb")]
        if not accdbs:
            raise FileNotFoundError("No se generó ningún archivo .accdb en la carpeta destino.")

        ruta = os.path.join(carpeta_destino, accdbs[0])
        conn_str = rf"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};Dbq={ruta};"
        with pyodbc.connect(conn_str, autocommit=True) as conn, conn.cursor() as c:
            tablas = [row.table_name.lower() for row in c.tables(tableType="TABLE")]
            if "registros" not in tablas:
                raise RuntimeError(f"El archivo {ruta} no contiene la tabla 'registros'.")
        print(f"[Prueba] Revisión de Access OK → {ruta}")
        return True
    except Exception as e:
        Controller_Error.Logs_Error.CapturarEvento("MainTest", "_prueba_archivo_access", str(e))
        return False

def ejecutar_carga():
    todo_ok = True
    todo_ok &= _prueba_conexion_mysql()
    try:
        ConsultaSQL.exportar_todos_los_medios_a_access()
        print("[Main] Sincronización ejecutada correctamente.")
    except Exception as e:
        Controller_Error.Logs_Error.CapturarEvento("Main", "exportar_todos", str(e))
        todo_ok = False
    carpeta = ConsultaSQL.CARPETA_ACCESS
    todo_ok &= _prueba_archivo_access(carpeta)

    print("[Main] Resultado final:",
          "TODO CORRECTO" if todo_ok else "ALGUNA PRUEBA FALLÓ")
    return todo_ok

if __name__ == "__main__":
    ejecutar_carga()
