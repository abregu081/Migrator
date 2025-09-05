from cx_Freeze import setup, Executable

# Datos de la versión
version = "1.10"
changelog = """
Migrator de SQL a Access
"""
# Escribir la versión y cambios en un archivo
with open("Version.txt", "w", encoding="utf-8") as version_file:
    version_file.write(f"Versión: {version}\n")
    version_file.write(changelog)

# Configuración de cx_Freeze
includes = ["mysql.connector.plugins.mysql_native_password"]
includefiles = ["Version.txt"]
excludes = ['Tkinter']
packages = packages = ['os', 'csv', 'sys', 're', "ConexionBD","Setting",'collections',"pyodbc", 'datetime', 'ConsultaSQL',"Controller_Error"]

setup(
    name="Migrator",
    version=version,
    description="Migrator",
    options={'build_exe': {'excludes': excludes, 'packages': packages,'includes': includes ,'include_files': includefiles}},
    executables=[Executable("Migrator.py")]
)



