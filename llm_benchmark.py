import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
import os
import yaml
from lm_studio_manager import LMStudioManager


class LMStudioClient:
    
    def __init__(self, base_url: str = "http://localhost:1234/v1", model: str = None):
        self.base_url = base_url.rstrip('/')
        self.chat_endpoint = f"{self.base_url}/chat/completions"
        self.models_endpoint = f"{self.base_url}/models"
        self.model = model or self._get_available_model()
        
    def _get_available_model(self) -> str:
        try:
            response = requests.get(self.models_endpoint, timeout=5)
            response.raise_for_status()
            models = response.json().get('data', [])
            if models:
                model_name = models[0]['id']
                print(f"Model detected: {model_name}")
                return model_name
            else:
                print("No models found. Using 'local-model' as fallback.")
                return "local-model"
        except Exception as e:
            print(f"Error detecting model: {e}. Using 'local-model' as fallback.")
            return "local-model"
    
    def send_request(self, prompt: str, max_tokens: int = 100, temperature: float = 0.7) -> Dict:
        start_time = time.time()
        timestamp_send = datetime.now().isoformat()
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        try:
            response = requests.post(
                self.chat_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=300
            )
            response.raise_for_status()
            
            end_time = time.time()
            timestamp_response = datetime.now().isoformat()
            elapsed_time = end_time - start_time
            
            response_data = response.json()
            response_text = response_data['choices'][0]['message']['content']
            
            usage = response_data.get('usage', {})
            
            metrics = {
                "timestamp_send": timestamp_send,
                "timestamp_response": timestamp_response,
                "elapsed_time_seconds": round(elapsed_time, 3),
                "prompt": prompt,
                "response": response_text,
                "prompt_length_chars": len(prompt),
                "response_length_chars": len(response_text),
                "prompt_tokens": usage.get('prompt_tokens', None),
                "completion_tokens": usage.get('completion_tokens', None),
                "total_tokens": usage.get('total_tokens', None),
                "max_tokens_requested": max_tokens,
                "temperature": temperature,
                "model": self.model,
                "status": "success"
            }
            
            print(f"✅ {elapsed_time:.2f}s")
            return metrics
            
        except requests.exceptions.Timeout:
            metrics = {
                "timestamp_send": timestamp_send,
                "timestamp_response": datetime.now().isoformat(),
                "elapsed_time_seconds": time.time() - start_time,
                "prompt": prompt,
                "response": None,
                "prompt_length_chars": len(prompt),
                "response_length_chars": 0,
                "prompt_tokens": None,
                "completion_tokens": None,
                "total_tokens": None,
                "max_tokens_requested": max_tokens,
                "temperature": temperature,
                "model": self.model,
                "status": "timeout"
            }
            print(f"⏱️ Timeout")
            return metrics
            
        except Exception as e:
            metrics = {
                "timestamp_send": timestamp_send,
                "timestamp_response": datetime.now().isoformat(),
                "elapsed_time_seconds": time.time() - start_time,
                "prompt": prompt,
                "response": None,
                "prompt_length_chars": len(prompt),
                "response_length_chars": 0,
                "prompt_tokens": None,
                "completion_tokens": None,
                "total_tokens": None,
                "max_tokens_requested": max_tokens,
                "temperature": temperature,
                "model": self.model,
                "status": f"error: {str(e)}"
            }
            print(f"❌ Error")
            return metrics


class BenchmarkDatabase:
    
    def __init__(self, output_dir: str = "./benchmark_results", filename: str = None):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        if filename:
            self.json_file = os.path.join(output_dir, filename)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.json_file = os.path.join(output_dir, f"benchmark_{timestamp}.json")
        
        self.results: List[Dict] = []
        
    def add_result(self, metrics: Dict):
        self.results.append(metrics)
        
    def save_json(self):
        with open(self.json_file, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {
                    "total_requests": len(self.results),
                    "generated_at": datetime.now().isoformat()
                },
                "results": self.results
            }, f, indent=2, ensure_ascii=False)
        
    def save_all(self):
        self.save_json()
        
    def print_summary(self):
        if not self.results:
            print("No results to display.")
            return
            
        successful = [r for r in self.results if r['status'] == 'success']
        failed = [r for r in self.results if r.get('status') != 'success']
        timeouts = [r for r in self.results if r.get('status') == 'timeout']
        
        print("\n" + "="*60)
        print("BENCHMARK SUMMARY")
        print("="*60)
        print(f"Total requests: {len(self.results)}")
        print(f"Successful: {len(successful)}")
        print(f"Failed: {len(failed)}")
        if timeouts:
            print(f"Timeouts: {len(timeouts)}")

        if successful:
            avg_time = sum(r['elapsed_time_seconds'] for r in successful) / len(successful)
            avg_prompt_len = sum(r['prompt_length_chars'] for r in successful) / len(successful)
            avg_response_len = sum(r['response_length_chars'] for r in successful) / len(successful)

            print(f"Average response time: {avg_time:.2f}s")
            print(f"Average prompt length: {avg_prompt_len:.0f} characters")
            print(f"Average response length: {avg_response_len:.0f} characters")

            tokens_available = [r for r in successful if r.get('total_tokens') is not None]
            if tokens_available:
                avg_tokens = sum(r['total_tokens'] for r in tokens_available) / len(tokens_available)
                print(f"Average total tokens: {avg_tokens:.0f}")
        
        print("="*60 + "\n")


def load_config(config_file: str = "prompts_config.json") -> Dict:
    if not os.path.exists(config_file):
        candidate = os.path.join(os.path.dirname(__file__), config_file)
        if os.path.exists(candidate):
            config_file = candidate
        else:
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    return config


def load_experiments_config(config_file: str = "experiments.yaml") -> Dict:
    """Load the experiments configuration from YAML file."""
    if not os.path.exists(config_file):
        candidate = os.path.join(os.path.dirname(__file__), config_file)
        if os.path.exists(candidate):
            config_file = candidate
        else:
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config


def main():
    print("\n" + "="*60)
    print("LLM STUDIO BENCHMARK TOOL - EXPERIMENTS MODE")
    print("="*60 + "\n")
    
    # Load experiments configuration
    experiments_config = load_experiments_config()
    
    # Load general settings from prompts_config.json
    try:
        prompts_config = load_config()
        settings = prompts_config.get('settings', {})
    except:
        settings = {}
    
    lm_studio_url = settings.get('lm_studio_url', 'http://localhost:1234/v1')
    output_dir = settings.get('output_directory', './benchmark_results')
    delay = settings.get('delay_between_requests', 1.0)
    
    # Extract experiment parameters
    repetitions = experiments_config.get('repetitions', 5)
    template = experiments_config.get('template')
    models = experiments_config.get('models', [])
    topics = experiments_config.get('topics', [])
    sizes = experiments_config.get('sizes', [])
    
    # Convert sizes to dict format
    sizes_dict = {}
    for size_item in sizes:
        for size_name, size_value in size_item.items():
            sizes_dict[size_name] = size_value
    
    print(f"Experiment Configuration:")
    print(f"  - Models: {len(models)}")
    print(f"  - Topics: {len(topics)}")
    print(f"  - Sizes: {list(sizes_dict.keys())}")
    print(f"  - Repetitions per query: {repetitions}")
    print(f"\nTotal queries per model: {len(topics) * len(sizes_dict) * repetitions}")
    print(f"Total queries overall: {len(models) * len(topics) * len(sizes_dict) * repetitions}\n")
    
    # Initialize LM Studio Manager
    base_url = lm_studio_url.replace('/v1', '')
    manager = LMStudioManager(base_url=base_url)
    
    if not manager.check_server():
        print("❌ Cannot connect to LM Studio server. Make sure it's running.")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Process each model
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
        filename = f"benchmark_{model_safe_name}_{timestamp}.json"
        db = BenchmarkDatabase(output_dir=output_dir, filename=filename)
        
        # Create client with this model
        client = LMStudioClient(base_url=lm_studio_url, model=model_name)
        
        total_queries = len(topics) * len(sizes_dict) * repetitions
        query_count = 0
        
        print(f"\n🚀 Starting benchmark for {model_name}...")
        print("-" * 60)
        
        # For each topic
        for topic_idx, topic in enumerate(topics, 1):
            print(f"\n📌 Topic {topic_idx}/{len(topics)}: {topic}")
            
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
                        max_tokens=size_value * 2,  # Approximate: 2 tokens per word
                        temperature=0.7
                    )
                    
                    # Add experiment metadata
                    metrics['topic'] = topic
                    metrics['size_category'] = size_name
                    metrics['size_words'] = size_value
                    metrics['repetition'] = rep
                    
                    db.add_result(metrics)
                    
                    if query_count < total_queries:
                        time.sleep(delay)
        
        print("\n" + "-" * 60)
        print(f"✅ Completed benchmark for model: {model_name}")
        
        # Save results for this model
        print(f"💾 Saving results to: {db.json_file}")
        db.save_all()
        db.print_summary()
        
        # Small delay before loading next model
        if model_idx < len(models):
            print("\n⏳ Waiting before loading next model...")
            time.sleep(5)
    
    print("\n" + "="*60)
    print("🎉 ALL EXPERIMENTS COMPLETED!")
    print("="*60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nBenchmark interrupted by user.")
    except Exception as e:
        print(f"\nFatal error: {e}")