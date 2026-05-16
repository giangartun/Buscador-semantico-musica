import os
from owlready2 import *

# 1. Definir la ruta del archivo OWL (Subiendo un nivel a la carpeta ontology)
ruta_ontologia = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ontology", "musica.owl"))

print(f"Cargando ontología desde: {ruta_ontologia}")

try:
    # 2. Cargar la ontología en Owlready2
    onto = get_ontology(f"file://{ruta_ontologia}").load()
    print("¡Ontología cargada con éxito! ")
    
    # 3. Mostrar las clases disponibles en el archivo base
    print("\n--- Clases encontradas en la Ontología ---")
    clases = list(onto.classes())
    if clases:
        for clase in clases: 
            print(f"- {clase.name}")
    else:
        print("La ontología se cargó, pero no se encontraron clases.")

    # 4. Ejecutar el Razonador Lógico para la Inferencia Semántica
    print("\nEjecutando el razonador lógico (HermiT)... Espera unos segundos...")
    with onto:
        sync_reasoner()  # Aquí ocurre la inferencia
    print("¡Razonamiento completado con éxito!")

# 5. Mostrar los individuos con sus inferencias
    print("\n--- Individuos e Inferencias encontradas ---")
    individuos = list(onto.individuals())
    
    if individuos:
        print(f"Total de individuos encontrados: {len(individuos)}. Mostrando los primeros 15:\n")
        for ind in individuos[:15]:  # Limitamos a 15 para la prueba
            # '.is_a' nos dice todas las clases a las que pertenece, reales e inferidas
            clases_del_individuo = [clase.name for clase in ind.is_a]
            print(f"- {ind.name} -> Pertenece a: {clases_del_individuo}")
    else:
        print("No se encontraron individuos creados aún.")

except Exception as e:
    print(f"\nError en el proceso: {e}")