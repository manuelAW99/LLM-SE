#!/usr/bin/env python3
"""
Script para probar la configuración de experiments antes de ejecutar todo.
"""
import yaml

def test_experiments_config():
    with open('experiments.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    print("=== Configuración de Experimentos ===\n")
    
    repetitions = config.get('repetitions', 5)
    template = config.get('template')
    models = config.get('models', [])
    topics = config.get('topics', [])
    sizes = config.get('sizes', [])
    
    print(f"Repeticiones: {repetitions}")
    print(f"Template: {template}")
    print(f"\nModelos ({len(models)}):")
    for i, model in enumerate(models, 1):
        print(f"  {i}. {model}")
    
    print(f"\nTópicos ({len(topics)}):")
    for i, topic in enumerate(topics, 1):
        print(f"  {i}. {topic}")
    
    print(f"\nTamaños:")
    sizes_dict = {}
    for size_item in sizes:
        for size_name, size_value in size_item.items():
            sizes_dict[size_name] = size_value
            print(f"  - {size_name}: {size_value} palabras")
    
    # Ejemplo de prompts generados
    print(f"\n=== Ejemplos de Prompts ===\n")
    topic_example = topics[0]
    for size_name, size_value in sizes_dict.items():
        prompt = template.format(size=size_value, topic=topic_example)
        print(f"{size_name}: \"{prompt}\"")
    
    # Cálculos
    total_per_model = len(topics) * len(sizes_dict) * repetitions
    total_overall = len(models) * total_per_model
    
    print(f"\n=== Estadísticas ===")
    print(f"Queries por modelo: {total_per_model}")
    print(f"Queries totales: {total_overall}")
    print(f"Archivos JSON a generar: {len(models)}")

if __name__ == "__main__":
    test_experiments_config()
