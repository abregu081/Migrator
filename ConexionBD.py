import mysql.connector
from mysql.connector import Error
from Setting import Setting
import Controller_Error
import sys

class ConexionBD:
    @staticmethod
    def ConectarBDAbrir(setting):
        """
        Abre la conexión a la base de datos usando los parámetros obtenidos.
        """
        try:
            conn = mysql.connector.connect(
                host=setting.Host,    
                user=setting.user,
                password=setting.password,
                database=setting.database,
                charset='utf8mb4',
                auth_plugin="mysql_native_password"
            )
            if conn.is_connected():
                return conn
            else:
                return None
        except Error as error:
            error_msg = str(error) + ' ' + str(sys.exc_info())
            Controller_Error.Logs_Error.CapturarEvento("CapturarDatosBD", "ConectarBDAbrir", error_msg)
            return None

    @staticmethod
    def CerrarBDCerrar(conn):
        """
        Cierra la conexión y verifica si se ha cerrado correctamente.
        """
        try:
            conn.close()
            if conn.is_connected():
                return True
            else:
                return False
        except Error as error:
            Controller_Error.Logs_Error.CapturarEvento("CapturarDatosBD", "CerrarBDCerrar", str(error))
            return True

    @staticmethod
    def ObtenerSettingCompleto():
        """
        Combina los datos de conexión (Host, user, password, database) que se obtienen desde
        ConsultarDatos_ConexionDB con el resto de datos (Token, Estacion, etc.) que se obtienen desde
        Consultar_datos_de_archivo_txt.
        """
        try:
            # Se obtienen los parámetros de conexión a la DB
            dbSetting = Setting.ConsultarDatos_ConexionDB("Setting.ini")
            # Se obtienen otros parámetros (Token, Estacion, etc.)
            otherSetting = Setting.Consultar_datos_de_archivo_txt()
            dbSetting.Estacion = otherSetting.Estacion
            return dbSetting
        except Exception as error:
            Controller_Error.Logs_Error.CapturarEvento("CapturarDatosBD", "ObtenerSettingCompleto", str(error))
            return None


