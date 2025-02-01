from importlib.metadata import distribution, PackageNotFoundError
from pathlib import Path
import subprocess
import sys
import os
import re

def get_enabled_subdirectories_with_files(base_directory):
    """Gets subdirectories containing requirements.txt and install.py files."""
    base_path = Path(base_directory)
    subdirs_with_files = []

    for subdir in base_path.iterdir():
        if subdir.is_dir() and not subdir.name.endswith(".disabled") and not subdir.name.startswith('.') and subdir.name != '__pycache__':
            print(f"\033[1;34mChecking dependencies >> \033[0m{subdir.name}")
            requirements_file = subdir / "requirements.txt"
            install_script = subdir / "install.py"

            if requirements_file.exists() or install_script.exists():
                subdirs_with_files.append((subdir, requirements_file, install_script))

    print()  # Space
    return subdirs_with_files

def is_package_installed(package_name, required_version=None):
    """Checks if the package is installed and compares versions."""
    try:
        dist = distribution(package_name)
        installed_version = dist.version
        if required_version:
            return compare_versions(installed_version, required_version) >= 0
        return True
    except PackageNotFoundError:
        return False

def compare_versions(installed_version, required_version):
    """Compares two version strings."""
    installed_parts = list(map(int, re.findall(r'\d+', installed_version)))
    required_parts = list(map(int, re.findall(r'\d+', required_version)))
    
    for installed, required in zip(installed_parts, required_parts):
        if installed < required:
            return -1
        elif installed > required:
            return 1
    return len(installed_parts) - len(required_parts)

def install_package(package_spec):
    """Installs a package."""
    print(f"\033[1;33mInstalling '{package_spec}'\033[0m")
    subprocess.run([sys.executable, "-m", "pip", "install", package_spec], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def install_requirements(requirements_file_path, installed_packages):
    """Installs libraries from requirements.txt."""
    if requirements_file_path.exists():
        with open(requirements_file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line in installed_packages:
                    continue
                
                match = re.match(r'^([^=><]+)([<>=!]+)(.+)', line)
                if match:
                    package_name, comparison_operator, required_version = map(str.strip, match.groups())
                    if not is_package_installed(package_name, required_version):
                        install_package(f"{package_name}{comparison_operator}{required_version}")
                        installed_packages.add(line)
                else:
                    package_name = line.strip()
                    if not is_package_installed(package_name):
                        install_package(package_name)
                        installed_packages.add(package_name)

def run_install_script(install_script_path):
    """Runs install.py if it exists."""
    if install_script_path.exists():
        print(f"\033[1;34mRunning install script from {install_script_path}...\033[0m")
        subprocess.run([sys.executable, str(install_script_path)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def log_installed_packages(installed_packages, log_file_path):
    """Logs installed packages to a file."""
    with open(log_file_path, 'w') as f:
        for package in installed_packages:
            f.write(package + '\n')

def main():
    """Main function that searches for and installs libraries."""
    custom_nodes_directory = "custom_nodes"
    log_file_path = "installed_packages.txt"
    installed_packages = set()

    # Load existing installed packages from log file
    if Path(log_file_path).exists():
        with open(log_file_path, 'r') as f:
            installed_packages.update(line.strip() for line in f)

    subdirs_with_files = get_enabled_subdirectories_with_files(custom_nodes_directory)

    try:
        for full_path, requirements_file, install_script in subdirs_with_files:
            install_requirements(requirements_file, installed_packages)
            run_install_script(install_script)

        # Log installed packages
        log_installed_packages(installed_packages, log_file_path)

    except KeyboardInterrupt:
        print("\n\033[1;31mScript interrupted by user. Exiting...\033[0m")
    except Exception as e:
        print(f"\n\033[1;31mAn error occurred: {e}\033[0m")

if __name__ == "__main__":
    main()