#!/usr/bin/env python3
"""
Script para analizar los archivos JSON de la carpeta local_client
y calcular los promedios de total_tokens separados por size_words
"""

import json
import os
from pathlib import Path
from collections import defaultdict


def analyze_local_client_results():
    """Lee los JSON de local_client y calcula promedios de total_tokens por size_words"""
    
    # Ruta a la carpeta local_client
    local_client_dir = Path(__file__).parent / "local_client"
    
    # Verificar que existe la carpeta
    if not local_client_dir.exists():
        print(f"Error: La carpeta {local_client_dir} no existe")
        return
    
    # Diccionario para almacenar tokens por size_words
    tokens_by_size = defaultdict(list)
    
    # Leer todos los archivos JSON en local_client
    json_files = list(local_client_dir.glob("*.json"))
    
    if not json_files:
        print(f"No se encontraron archivos JSON en {local_client_dir}")
        return
    
    print(f"Analizando {len(json_files)} archivos JSON en local_client...\n")
    
    # Procesar cada archivo JSON
    for json_file in json_files:
        print(f"Procesando: {json_file.name}")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extraer resultados
            results = data.get('results', [])
            
            # Agrupar por size_words
            for result in results:
                if result.get('status') == 'success':
                    size_words = result.get('size_words')
                    total_tokens = result.get('total_tokens')
                    
                    if size_words is not None and total_tokens is not None:
                        tokens_by_size[size_words].append(total_tokens)
        
        except Exception as e:
            print(f"  Error al procesar {json_file.name}: {e}")
    
    # Calcular y mostrar promedios
    print("\n" + "="*60)
    print("PROMEDIOS DE TOTAL_TOKENS POR SIZE_WORDS")
    print("="*60)
    
    if not tokens_by_size:
        print("No se encontraron datos para calcular promedios")
        return
    
    # Ordenar por size_words
    for size_words in sorted(tokens_by_size.keys()):
        tokens = tokens_by_size[size_words]
        avg_tokens = sum(tokens) / len(tokens)
        
        print(f"\nSize Words: {size_words}")
        print(f"  - Número de muestras: {len(tokens)}")
        print(f"  - Promedio total_tokens: {avg_tokens:.2f}")
        print(f"  - Mínimo: {min(tokens)}")
        print(f"  - Máximo: {max(tokens)}")
    
    print("\n" + "="*60)
    
    # Resumen general
    all_tokens = [token for tokens in tokens_by_size.values() for token in tokens]
    if all_tokens:
        print(f"\nRESUMEN GENERAL:")
        print(f"  - Total de muestras: {len(all_tokens)}")
        print(f"  - Promedio general: {sum(all_tokens) / len(all_tokens):.2f}")
        print(f"  - Mínimo global: {min(all_tokens)}")
        print(f"  - Máximo global: {max(all_tokens)}")


if __name__ == "__main__":
    analyze_local_client_results()
