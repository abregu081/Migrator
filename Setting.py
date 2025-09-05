import os
import Setting
import Controller_Error
import sys

class Setting:
 def __init__(self):
    self.RutaBD = None
    self.Estacion = None
    self.Planta = []
    self.HotName = []
    self.Host = None
    self.user = None
    self.password = None
    self.database = None

 @staticmethod
 def ConsultarDatos_ConexionDB(archivo):
    try:
       archivo_txt= Setting.Capturar_datos_txt("Setting.ini")
       dict_valores = Setting.Crear_tupla_Setting(archivo_txt)
       dato = Setting()
       dato.Host = dict_valores["host"]
       dato.user = dict_valores["user"]
       dato.password = dict_valores["password"]
       dato.database = dict_valores["database"]
       return dato
    except Exception as errorConexion:
       Controller_Error.Logs_Error.CapturarEvento("CapturarDatosBD", "Capturar_datos_txt_Setting", str(errorConexion))
    
 
 #Metodo para abrir el archivo setting.ini, lo busca local en la carpeta donde esta el software
 @staticmethod
 def Capturar_datos_txt(Archivo):
   try:
      script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
      ruta_archivo = os.path.join(script_dir, Archivo)
      print(ruta_archivo)
      with open(ruta_archivo, 'r') as archivo:
          archivo_txt = archivo.readlines()
          archivo_txt = [linea.strip() for linea in archivo_txt]
      return archivo_txt
   except Exception as error1:
            Controller_Error.Logs_Error.CapturarEvento("CapturarDatosBD", "Capturar_datos_txt_Setting", str(error1))


 @staticmethod
 def obtener_estacion_de_archivo_txt():
    try:
       archivo_txt= Setting.Capturar_datos_txt("Setting.ini")
       dict_valores = Setting.Crear_tupla_Setting(archivo_txt)
       dato = Setting()
       dato.Estacion = dict_valores["Estacion"]
       return dato
    except Exception as ErrorEstacion:
       Controller_Error.Logs_Error.CapturarEvento("CapturarDatosBD", "Consultar_dato estacion", str(ErrorEstacion)) 
    

 #Captura datos del archivo Setting.ini
 @staticmethod
 def Consultar_datos_de_archivo_txt():
  try:
    archivo_txt = Setting.Capturar_datos_txt("Setting.ini")
    dict_valores = Setting.Crear_tupla_Setting(archivo_txt)
    #Se crea objeto de la clase
    nuevoregistro = Setting()
    nuevoregistro.RutaBD = dict_valores["RutaBD"] 
    return nuevoregistro
  except Exception as error1:
     Controller_Error.Logs_Error.CapturarEvento("CapturarDatosBD", "Consultar_datos_de_archivo_txt_Setting", str(error1)) 

 #Metodo para crear una tupla de datos obtenida del archivo Setting.ini
 @staticmethod
 def Crear_tupla_Setting(valores_txt):
  try:
    dict_valores = {}
    for valor_txt in valores_txt:
       valor1 = valor_txt.rfind("//")
       if valor1 < 0:
         valor12 = valor_txt.rfind("")
         if valor_txt.rfind("") != 0:
           valor3 = valor_txt.rfind("=")
           if valor3 >= 0:
             valores_split = valor_txt.split('=')
             dict_valores[valores_split[0].strip()] = valores_split[1].strip()
    return dict_valores
  except Exception as error1:
     Controller_Error.Logs_Error.CapturarEvento("CapturarDatosBD", "Crear_tupla_Setting", str(error1)) 