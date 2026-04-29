import os
import time

class K8sHealthChecker:
    def check_health(self, ns, timeout=60):
        # Correção 4: Validação de estados reais de erro do K8s
        start = time.time()
        fail_states = ["CrashLoopBackOff", "Error", "ImagePullBackOff", "ErrImagePull"]
        
        while time.time() - start < timeout:
            cmd = f"kubectl get pods -n {ns} --no-headers"
            pods = os.popen(cmd).readlines()
            
            if not pods: 
                time.sleep(2); continue
                
            states = [p.split()[2] for p in pods]
            
            if any(s in fail_states for s in states):
                return False, f"Falha: {', '.join(states)}"
            
            if all(s in ["Running", "Completed"] for s in states):
                return True, "Sucesso: Ambiente íntegro"
            
            time.sleep(3)
        return False, "Timeout: Pods não estabilizaram"