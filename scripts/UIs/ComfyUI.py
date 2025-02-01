# ~ ComfyUI.py | by ANXETY ~

from Manager import m_download, m_clone    # Every Download | Clone
import json_utils as js                    # JSON

from IPython.display import clear_output
from IPython.utils import capture
from IPython import get_ipython
from pathlib import Path
import subprocess
import asyncio
import os


CD = os.chdir
ipySys = get_ipython().system

# Constants
UI = 'ComfyUI'

HOME = Path.home()
WEBUI = HOME / UI
SCR_PATH = HOME / 'ANXETY'
SETTINGS_PATH = SCR_PATH / 'settings.json'

REPO_URL = f"https://huggingface.co/NagisaNao/ANXETY/resolve/main/{UI}.zip"
BRANCH = js.read(SETTINGS_PATH, 'ENVIRONMENT.branch')
EXTS = js.read(SETTINGS_PATH, 'WEBUI.extension_dir')

CD(HOME)


## ================== WEB UI OPERATIONS ==================

async def _download_file(url, directory, filename):
    os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, filename)
    process = await asyncio.create_subprocess_shell(
        f'curl -sLo {file_path} {url}',
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    await process.communicate()

async def download_files(file_list):
    tasks = []
    for file_info in file_list:
        parts = file_info.split(',')
        url = parts[0].strip()
        directory = parts[1].strip() if len(parts) > 1 else WEBUI   # Default Save Path
        filename = parts[2].strip() if len(parts) > 2 else os.path.basename(url)
        tasks.append(_download_file(url, directory, filename))
    await asyncio.gather(*tasks)

async def download_configuration():
    ## FILES
    url_comfy = f'https://raw.githubusercontent.com/anxety-solo/sdAIgen/{BRANCH}/__configs__/ComfyUI'
    files = [
        f'{url_comfy}/install-deps.py',
        f'{url_comfy}/comfy.settings.json, {WEBUI}/user/default',
        f'{url_comfy}/workflows/anxety-workflow.json, {WEBUI}/user/default/workflows'
    ]
    await download_files(files)

    ## REPOS
    extensions_list = [
        "https://github.com/ltdrdata/ComfyUI-Manager Manager",
        "https://github.com/pythongosssss/ComfyUI-Custom-Scripts",
        "https://github.com/WASasquatch/was-node-suite-comfyui WAS-Nodes",
        "https://github.com/pythongosssss/ComfyUI-WD14-Tagger WD14-Tagger",
        "https://github.com/Fannovel16/comfyui_controlnet_aux ControlNet-AUX",
        "https://github.com/jags111/efficiency-nodes-comfyui Efficiency-Nodes",
        "https://github.com/ssitu/ComfyUI_UltimateSDUpscale UltimateSDUpscale",
        "https://github.com/Kosinkadink/ComfyUI-Advanced-ControlNet Advanced-ControlNet"
    ]
    CD(EXTS)

    tasks = []
    for command in extensions_list:
        tasks.append(asyncio.create_subprocess_shell(
            f'git clone --depth 1 --recursive {command}',
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        ))
    
    await asyncio.gather(*tasks)

def unpack_webui():
    zip_path = f"{HOME}/{UI}.zip"
    m_download(f'{REPO_URL} {HOME} {UI}.zip')
    ipySys(f'unzip -q -o {zip_path} -d {WEBUI}')
    ipySys(f'rm -rf {zip_path}')

## ====================== MAIN CODE ======================
if __name__ == "__main__":
    with capture.capture_output():
        unpack_webui()
        asyncio.run(download_configuration())