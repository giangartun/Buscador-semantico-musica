import os
from owlready2 import *

# 1. Definir la ruta del archivo OWL (Subiendo un nivel a la carpeta ontology)
ruta_ontologia = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ontology", "musica.owl"))

print(f"Cargando ontología desde: {ruta_ontologia}")

try:
    # 2. Cargar la ontología en Owlready2
    onto = get_ontology(f"file://{ruta_ontologia}").load()
    print("¡Ontología cargada con éxito ")
    
    # 3. Mostrar las clases disponibles para verificar que leyó bien
    print("\n--- Clases encontradas en tu Ontología ---")
    clases = list(onto.classes())
    
    if clases:
        for clase in clases: # Muestra las primeras 10 para no llenar la consola
            print(f"- {clase.name}")
    else:
        print("La ontología se cargó, pero no se encontraron clases. Revisa el archivo.")

except Exception as e:
    print(f"Error al cargar la ontología: {e}")