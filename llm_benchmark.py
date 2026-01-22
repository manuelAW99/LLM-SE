import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
import os


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
            
            print(f"Request completed in {elapsed_time:.2f}s - Prompt: {len(prompt)} chars, Response: {len(response_text)} chars")
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
            print(f"Request timeout after {time.time() - start_time:.2f}s")
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
            print(f"Request error: {e}")
            return metrics


class BenchmarkDatabase:
    
    def __init__(self, output_dir: str = "./benchmark_results"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
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


def main():
    print("\n" + "="*60)
    print("LLM STUDIO BENCHMARK TOOL")
    print("="*60 + "\n")
    
    config = load_config()
    
    settings = config.get('settings', {})
    lm_studio_url = settings.get('lm_studio_url', 'http://localhost:1234/v1')
    output_dir = settings.get('output_directory', './benchmark_results')
    delay = settings.get('delay_between_requests', 1.0)
    
    client = LMStudioClient(base_url=lm_studio_url)
    db = BenchmarkDatabase(output_dir=output_dir)
    
    test_cases = config.get('test_cases', [])
    
    if not test_cases:
        print("No test cases found in configuration file.")
        return
    
    print(f"Loaded {len(test_cases)} test cases from configuration\n")
    
    print("Starting benchmark...")
    print("-" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        category = test_case.get('category', 'unknown')
        prompt = test_case['prompt']
        max_tokens = test_case.get('max_tokens', 100)
        temperature = test_case.get('temperature', 0.7)
        
        print(f"\n[{i}/{len(test_cases)}] Category: {category}")
        print(f"Prompt: {prompt[:80]}...")
        
        metrics = client.send_request(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        metrics['category'] = category
        
        db.add_result(metrics)
        
        if i < len(test_cases):
            time.sleep(delay)
    
    print("\n" + "-" * 60)
    print("Benchmark completed!")
    
    print("\nSaving results...")
    db.save_all()
    
    db.print_summary()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nBenchmark interrupted by user.")
    except Exception as e:
        print(f"\nFatal error: {e}")