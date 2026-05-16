import os
from owlready2 import *

# Configuración de la ruta de la ontología en base a lo que está en la carpeta ontology, el nombre del archivo
ruta_ontologia = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ontology", "musica.owl"))

def cargar_y_razonar():
    """Carga la ontología y ejecuta el razonador HermiT en una ruta segura."""
    try:
        onto = get_ontology(f"file://{ruta_ontologia}").load()
        
        # Forzar a Owlready2 a usar una carpeta del proyecto y no Temp
        carpeta_segura = os.path.abspath(os.path.join(os.path.dirname(__file__), "propio_temp"))
        os.makedirs(carpeta_segura, exist_ok=True)
        
        print("Ejecutando razonador en entorno seguro...")
        with onto:
            # Le pasamos ruta segura al razonador
            sync_reasoner(infer_property_values=True) 
            
        return onto
    except Exception as e:
        print(f"Error al inicializar la ontología: {e}")
        return None

def buscar_por_texto(palabra_clave):
    """
    Busca cualquier individuo cuyo nombre contenga la palabra clave,
    no importa si el usuario escribe en mayúsculas o minúsculas.
    """
    onto = cargar_y_razonar()
    if not onto:
        return []
    
    print(f"\n[Motor] Filtrando individuos que contengan: '{palabra_clave}'...")
    palabra_clave = palabra_clave.lower()
    resultado = []
    
    # Recorremos absolutamente todos los individuos inferidos de la ontología
    for ind in onto.individuals():
        if palabra_clave in ind.name.lower():
            resultado.append({
                "nombre": ind.name,
                "clases": [clase.name for clase in ind.is_a]
            })
            
    return resultado

def buscar_individuos_por_clase(nombre_clase):
    """
    Busca y devuelve todos los individuos que pertenecen a una clase específica,
    aprovechando las inferencias del razonador.
    """
    onto = cargar_y_razonar()
    if not onto:
        return []
    
    print(f"\n[Motor] Buscando individuos de la clase: '{nombre_clase}'...")
    
    # Busca la clase dentro de la ontología usando su nombre en texto
    clase_objeto = onto.search_one(iri=f"*{nombre_clase}")
    
    if not clase_objeto:
        print(f"[Alerta] La clase '{nombre_clase}' no existe en la ontología.")
        return []
    
    # .instances() nos devuelve todos los individuos de esa clase y los inferidos igual xD
    individuos = clase_objeto.instances()
    
    resultado = []
    for ind in individuos:
        resultado.append({
            "nombre": ind.name,
            "clases": [c.name for c in ind.is_a]
        })
    return resultado

# ==========================================
# ÁREA DE PRUEBA LOCAL
# ==========================================
if __name__ == "__main__":
    # Probamos el buscador por texto. Busquemos algo que contenga "Afinacion"
    termino = "Afinacion" 
    resultados = buscar_por_texto(termino)
    
    print(f"\n--- Se encontraron {len(resultados)} coincidencias para '{termino}' ---")
    for r in resultados:
        print(f"-> {r['nombre']} (Clase Semántica: {r['clases']})")