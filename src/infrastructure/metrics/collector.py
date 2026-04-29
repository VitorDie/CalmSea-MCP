import csv
import os
from datetime import datetime

class TCCMetricsCollector:
    def __init__(self, filename="results/benchmark_master.csv"):
        self.filename = filename
        self.temp_entry = None # Buffer para segurar o dado temporariamente
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "provider", "model", "duration", "tokens", "gpu_status", "prompt", "response"])

    def record(self, provider, model, duration, tokens, prompt, response, gpu_status):
        """O Decorator chama isso. Nós apenas guardamos os dados na memória."""
        self.temp_entry = {
            "provider": provider, "model": model, "duration": duration,
            "tokens": tokens, "prompt": prompt, "response": response, "gpu": gpu_status
        }

    def commit(self, is_ok, health_msg):
        """A Main chama isso. Agora sim nós escrevemos no CSV com o veredito do K8s."""
        if not self.temp_entry:
            return

        status = "SUCCESS" if is_ok else f"FAILED ({health_msg})"
        
        with open(self.filename, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                self.temp_entry["provider"],
                self.temp_entry["model"],
                round(self.temp_entry["duration"], 4),
                self.temp_entry["tokens"],
                self.temp_entry["gpu"],
                self.temp_entry["prompt"],
                f"[{status}] | {self.temp_entry['response']}" # Veredito + Resposta da IA
            ])
        self.temp_entry = None # Limpa o buffer para o próximo teste