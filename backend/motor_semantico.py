import os
from owlready2 import *

# Configuración de la ruta de la ontología en base a lo que está en la carpeta ontology, el nombre del archivo
ruta_ontologia = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ontology", "musica.owl"))

# Variable global para mantener la ontología y sus inferencias cargadas en memoria RAM
_onto_instancia = None

def cargar_y_razonar():
    """Carga la ontología y ejecuta el razonador HermiT en una ruta segura (una sola vez)."""
    global _onto_instancia
    
    # Si ya está cargada en memoria, la devolvemos directamente sin repetir el proceso
    if _onto_instancia is not None:
        return _onto_instancia
        
    try:
        print("[Motor] Cargando ontología musical por primera vez...")
        onto = get_ontology(f"file://{ruta_ontologia}").load()
        
        # Forzar a Owlready2 a usar una carpeta del proyecto y no Temp 
        carpeta_segura = os.path.abspath(os.path.join(os.path.dirname(__file__), "propio_temp"))
        os.makedirs(carpeta_segura, exist_ok=True)
        
        print("Ejecutando razonador en entorno seguro...")
        with onto:
            # Le pasamos ruta segura al razonador
            sync_reasoner(infer_property_values=True) 
            
        _onto_instancia = onto  # Guardamos el resultado en la variable global
        print("[Motor] ¡Ontología e Inferencias listas en memoria! 🧠")
        return _onto_instancia
        
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
# ÁREA DE PRUEBAS LOCALES
# ==========================================
if __name__ == "__main__":
    # Probamos el buscador por texto. Ejemplo Buscamos algo que contenga "Afinacion"
    termino = "Afinacion" 
    resultados = buscar_por_texto(termino)
    
    print(f"\n--- Se encontraron {len(resultados)} coincidencias para '{termino}' ---")
    for r in resultados:
        print(f"-> {r['nombre']} (Clase Semántica: {r['clases']})")