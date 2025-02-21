# ~ launch.py | by ANXETY ~

from TunnelHub import Tunnel    # Tunneling
import json_utils as js         # JSON

from IPython.display import clear_output
from IPython import get_ipython
from datetime import timedelta
from pathlib import Path
import subprocess
import requests
import logging
import shlex
import time
import json
import yaml
import os
import re


CD = os.chdir
ipySys = get_ipython().system

# Constants
HOME = Path.home()
VENV = HOME / 'venv'
SCR_PATH = HOME / 'ANXETY'
SETTINGS_PATH = SCR_PATH / 'settings.json'

ENV_NAME = js.read(SETTINGS_PATH, 'ENVIRONMENT.env_name')
UI = js.read(SETTINGS_PATH, 'WEBUI.current')
WEBUI = js.read(SETTINGS_PATH, 'WEBUI.webui_path')

# USER VENV | python
# py = Path(VENV) / 'bin/python3'
py = 'python3'


## ================ loading settings V5 ==================
def load_settings(path):
    """Load settings from a JSON file."""
    try:
        return {
            **js.read(path, 'ENVIRONMENT'),
            **js.read(path, 'WIDGETS'),
            **js.read(path, 'WEBUI')
        }
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading settings: {e}")
        return {}
        
# Load settings
settings = load_settings(SETTINGS_PATH)
locals().update(settings)

## ======================= Other =========================

def Trashing():
    dirs = ["A1111", "ReForge", "ComfyUI", "Forge"]
    paths = [Path(HOME) / name for name in dirs]

    for path in paths:
        cmd = f"find {path} -type d -name .ipynb_checkpoints -exec rm -rf {{}} +"
        subprocess.run(shlex.split(cmd), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def _update_config_paths():
    """Update configuration paths in WebUI config file"""
    config_mapping = {
        "tagger_hf_cache_dir": f"{WEBUI}/models/interrogators/",
        "ad_extra_models_dir": adetailer_dir,
        "sd_checkpoint_hash": "",
        "sd_model_checkpoint": "",
        "sd_vae": "None"
    }

    config_file = f"{WEBUI}/config.json"
    for key, value in config_mapping.items():
        if js.key_exists(config_file, key):
            js.update(config_file, key, str(value))
        else:
            js.save(config_file, key, str(value))

def get_launch_command(tunnel_port):
    """Construct launch command based on configuration"""
    base_args = commandline_arguments
    password = 'ha4ez7147b5vdlu5u8f8flrllgn61kpbgbh6emil'

    if UI == 'ComfyUI':
        return f'{py} main.py {base_args}'

    common_args = ' --enable-insecure-extension-access --disable-console-progressbars --theme dark --share'
    if ENV_NAME == "Kaggle":
        common_args += f' --encrypt-pass={password}'

    return f'{py} launch.py {base_args}{common_args}'

## ===================== Tunneling =======================

class TunnelManager:
    """Class for managing tunnel services"""
    
    def __init__(self, tunnel_port):
        self.tunnel_port = tunnel_port
        self.tunnels = []
        self.success_urls = []
        self.error_urls = []
        self.public_ip = self._get_public_ip()

    def _get_public_ip(self) -> str:
        """Retrieve and cache public IPv4 address"""
        cached_ip = js.read(SETTINGS_PATH, 'ENVIRONMENT.public_ip')
        if cached_ip:
            return cached_ip
        
        try:
            response = requests.get('https://api64.ipify.org?format=json&ipv4=true', timeout=5)
            public_ip = response.json().get('ip', 'N/A')
            js.update(SETTINGS_PATH, "ENVIRONMENT.public_ip", public_ip)
            return public_ip
        except Exception as e:
            print(f"Error getting public IP address: {e}")
            return 'N/A'

    def _check_service_availability(self, url, name):
        """Check if a tunnel service is reachable"""
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                print(f"\033[32m> [SUCCESS]: Tunnel '\033[0m{name}\033[32m' is reachable at \033[0m{url}")
                self.success_urls.append(url)
                return True
        except requests.RequestException as e:
            print(f"\033[31m> [ERROR]: Tunnel '\033[0m{name}\033[31m' - {e}\033[0m")
            self.error_urls.append(url)
        return False

    def setup_tunnels(self):
        """Configure all available tunnel services"""
        services = [
            ('https://www.cloudflare.com', 'Cloudflared', {
                "command": f"cl tunnel --url localhost:{self.tunnel_port}",
                "pattern": re.compile(r"[\w-]+\.trycloudflare\.com")
            }),
            ('https://pinggy.io', 'Pinggy', {
                "command": f"ssh -o StrictHostKeyChecking=no -p 80 -R0:localhost:{self.tunnel_port} a.pinggy.io",
                "pattern": re.compile(r"[\w-]+\.a\.free\.pinggy\.link")
            }),
            ('https://localtunnel.me', 'Localtunnel', {
                "command": f"lt --port {self.tunnel_port}",
                "pattern": re.compile(r"[\w-]+\.loca\.lt"),
                "note": f"Password : \033[32m{self.public_ip}\033[0m"
            })
        ]

        if zrok_token:
            env_path = HOME / '.zrok/environment.json'
            current_token = None
            
            if env_path.exists():
                with open(env_path, 'r') as f:
                    current_token = json.load(f).get('zrok_token')

            if current_token != zrok_token:
                ipySys('zrok disable &> /dev/null')
                ipySys(f'zrok enable {zrok_token} &> /dev/null')

            services.append(('https://status.zrok.io', 'Zrok', {
                "command": f"zrok share public http://localhost:{self.tunnel_port}/ --headless",
                "pattern": re.compile(r"[\w-]+\.share\.zrok\.io")
            }))

        if ngrok_token:
            config_path = HOME / '.config/ngrok/ngrok.yml'
            current_token = None
            
            if config_path.exists():
                with open(config_path, 'r') as f:
                    current_token = yaml.safe_load(f).get('agent', {}).get('authtoken')

            if current_token != ngrok_token:
                ipySys(f'ngrok config add-authtoken {ngrok_token}')

            services.append(('https://ngrok.com', 'Ngrok', {
                "command": f"ngrok http http://localhost:{self.tunnel_port} --log stdout",
                "pattern": re.compile(r"https://[\w-]+\.ngrok-free\.app")
            }))

        for url, name, config in services:
            if self._check_service_availability(url, name):
                self.tunnels.append({**config, "name": name})

        return (
            self.tunnels,
            len(self.success_urls + self.error_urls),    # Total Tunnel
            len(self.success_urls),
            len(self.error_urls)
        )

## ========================= Main ========================

if __name__ == "__main__":
    """Main execution flow"""
    print('Please Wait...\n')

    # Initialize tunnel manager and services
    tunnel_port = 8188 if UI == 'ComfyUI' else 7860
    tunnel_mgr = TunnelManager(tunnel_port)
    tunnels, total, success, errors = tunnel_mgr.setup_tunnels()
    
    # Set up tunneling service
    tunnelingService = Tunnel(tunnel_port)
    tunnelingService.logger.setLevel(logging.DEBUG)
    
    for tunnel in tunnels:
        tunnelingService.add_tunnel(**tunnel)

    clear_output(wait=True)

    # Launch sequence
    Trashing()
    _update_config_paths()
    LAUNCHER = get_launch_command(tunnel_port)
    
    # Setup pinggy timer
    ipySys(f'echo -n {int(time.time())+(3600+20)} > {WEBUI}/static/timer-pinggy.txt')

    with tunnelingService:
        CD(WEBUI)

        if UI == 'ComfyUI':
            COMFYUI_SETTINGS_PATH = SCR_PATH / 'ComfyUI.json'
            if check_custom_nodes_deps:
                ipySys(f'{py} install-deps.py')
                clear_output(wait=True)

            if not js.key_exists(COMFYUI_SETTINGS_PATH, 'install_req', True):
                print("Installing ComfyUI dependencies...")
                subprocess.run(['pip', 'install', '-r', 'requirements.txt'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                js.save(COMFYUI_SETTINGS_PATH, 'install_req', True)
                clear_output(wait=True)
        
        print(f"\033[34m>> Total Tunnels:\033[0m {total} | \033[32mSuccess:\033[0m {success} | \033[31mErrors:\033[0m {errors}\n")
        print(f"🔧 WebUI: \033[34m{UI}\033[0m")
        
        try:
            ipySys(LAUNCHER)
        except KeyboardInterrupt:
            pass

    # Post-execution cleanup
    if zrok_token:
        ipySys('zrok disable &> /dev/null')
        print('🔐 Zrok tunnel disabled :3')

    # Display session duration
    try:
        with open(f'{WEBUI}/static/timer.txt') as f:
            timer = float(f.read())
            duration = timedelta(seconds=time.time() - timer)
            print(f"\n⌚️ Session duration: \033[33m{str(duration).split('.')[0]}\033[0m")
    except FileNotFoundError:
        pass