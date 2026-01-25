#!/usr/bin/env python3
"""
Script de prueba rápida del sistema de experimentación.
Ejecuta solo 1 repetición de 1 topic con 1 size para verificar que todo funcione.
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm_benchmark import *

def quick_test():
    print("\n" + "="*60)
    print("QUICK TEST - EXPERIMENTS MODE")
    print("="*60 + "\n")
    
    # Load experiments configuration
    experiments_config = load_experiments_config()
    
    # Load general settings
    try:
        prompts_config = load_config()
        settings = prompts_config.get('settings', {})
    except:
        settings = {}
    
    lm_studio_url = settings.get('lm_studio_url', 'http://localhost:1234/v1')
    output_dir = settings.get('output_directory', './benchmark_results')
    
    # Extract experiment parameters (REDUCED FOR TESTING)
    template = experiments_config.get('template')
    models = experiments_config.get('models', [])[:1]  # Solo 1 modelo
    topics = experiments_config.get('topics', [])[:2]  # Solo 2 topics
    sizes = experiments_config.get('sizes', [])[:1]    # Solo 1 size
    repetitions = 2  # Solo 2 repeticiones
    
    # Convert sizes to dict format
    sizes_dict = {}
    for size_item in sizes:
        for size_name, size_value in size_item.items():
            sizes_dict[size_name] = size_value
    
    print(f"Quick Test Configuration:")
    print(f"  - Models: {len(models)} ({models})")
    print(f"  - Topics: {len(topics)} ({topics})")
    print(f"  - Sizes: {list(sizes_dict.keys())}")
    print(f"  - Repetitions: {repetitions}")
    print(f"\nTotal queries: {len(models) * len(topics) * len(sizes_dict) * repetitions}\n")
    
    # Initialize LM Studio Manager
    base_url = lm_studio_url.replace('/v1', '')
    manager = LMStudioManager(base_url=base_url)
    
    if not manager.check_server():
        print("❌ Cannot connect to LM Studio server. Make sure it's running.")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Process first model only
    for model_idx, model_name in enumerate(models, 1):
        print("\n" + "="*60)
        print(f"MODEL {model_idx}/{len(models)}: {model_name}")
        print("="*60)
        
        # Load the model
        print(f"\n🔄 Loading model: {model_name}")
        if not manager.load_model(model_name):
            print(f"❌ Failed to load model {model_name}. Skipping...")
            continue
        
        # Create database for this model
        model_safe_name = model_name.replace('/', '_').replace(' ', '_')
        filename = f"benchmark_TEST_{model_safe_name}_{timestamp}.json"
        db = BenchmarkDatabase(output_dir=output_dir, filename=filename)
        
        # Create client
        client = LMStudioClient(base_url=lm_studio_url, model=model_name)
        
        total_queries = len(topics) * len(sizes_dict) * repetitions
        query_count = 0
        
        print(f"\n🚀 Starting quick test for {model_name}...")
        print("-" * 60)
        
        # For each topic
        for topic_idx, topic in enumerate(topics, 1):
            print(f"\n📍 Topic {topic_idx}/{len(topics)}: {topic}")
            
            # For each size
            for size_name, size_value in sizes_dict.items():
                prompt = template.format(size=size_value, topic=topic)
                
                print(f"  📊 Size: {size_name} ({size_value} words)")
                
                # Repeat N times
                for rep in range(1, repetitions + 1):
                    query_count += 1
                    print(f"    [{query_count}/{total_queries}] Rep {rep}/{repetitions}... ", end="")
                    
                    metrics = client.send_request(
                        prompt=prompt,
                        max_tokens=size_value * 2,
                        temperature=0.7
                    )
                    
                    # Add experiment metadata
                    metrics['topic'] = topic
                    metrics['size_category'] = size_name
                    metrics['size_words'] = size_value
                    metrics['repetition'] = rep
                    
                    db.add_result(metrics)
                    
                    time.sleep(0.5)  # Shorter delay for testing
        
        print("\n" + "-" * 60)
        print(f"✅ Quick test completed for model: {model_name}")
        
        # Save results
        print(f"💾 Saving results to: {db.json_file}")
        db.save_all()
        db.print_summary()
    
    print("\n" + "="*60)
    print("🎉 QUICK TEST COMPLETED!")
    print("="*60)

if __name__ == "__main__":
    try:
        quick_test()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
