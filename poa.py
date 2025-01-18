#!/usr/bin/env python3
import os
import re
import subprocess
import sys
import argparse

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

already_added = set()
successfully_added = []

def print_error(message):
    print(f"{RED}[ERROR]{RESET} {message}")

def print_info(message):
    print(f"{GREEN}[INFO]{RESET} {message}")

def print_warning(message):
    print(f"{YELLOW}[WARNING]{RESET} {message}")

def check_poetry_installed():
    try:
        subprocess.check_call(["poetry", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_error("Poetry is not installed or not found. Please install Poetry and rerun the script.")
        sys.exit(1)

def create_pyproject_if_missing():
    if not os.path.exists("pyproject.toml"):
        answer = input("pyproject.toml not found. Create one with 'poetry init'? [yes/no]: ").strip().lower()
        if answer == "yes":
            try:
                subprocess.check_call(["poetry", "init", "--no-interaction"])
                print_info("pyproject.toml created successfully.")
                subprocess.check_call(["poetry", "lock"])
            except subprocess.CalledProcessError as e:
                print_error(f"Error during pyproject.toml creation: {e}")
                sys.exit(1)
        else:
            print_error("Exiting script. Please create a pyproject.toml file first.")
            sys.exit(1)

def ensure_pipreqs_installed():
    try:
        subprocess.check_call(
            ["poetry", "run", "pipreqs", "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        print_info("pipreqs not found in the Poetry environment. Installing pipreqs with adjusted Python marker.")
        try:
            subprocess.check_call(["poetry", "add", "pipreqs@^0.5.0", "--python", ">=3.12,<3.13"])
        except subprocess.CalledProcessError as e:
            print_error(f"Failed to install pipreqs: {e}")
            sys.exit(1)

def generate_requirements_with_pipreqs(overwrite=False):
    cmd = ["poetry", "run", "pipreqs", "."]
    if overwrite:
        cmd.append("--force")
    try:
        print_info("Running pipreqs to generate requirements.txt...")
        subprocess.check_call(cmd)
        print_info("requirements.txt generated successfully.")
    except subprocess.CalledProcessError as e:
        print_error(f"pipreqs failed: {e}")
        sys.exit(1)

def get_venv_packages():
    if (hasattr(sys, 'real_prefix') or 
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)):
        try:
            result = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True)
            packages = {}
            for line in result.strip().split('\n'):
                if '==' in line:
                    pkg, ver = line.split('==')
                    packages[pkg.lower()] = ver
                elif '@' in line:
                    pkg = line.split('@')[0].strip().lower()
                    packages[pkg] = None
            return packages
        except subprocess.CalledProcessError as e:
            print_warning(f"Could not retrieve packages from the active venv: {e}")
            return {}
    else:
        print_info("No Python virtual environment detected. Skipping venv package addition.")
        return {}

def add_library_to_poetry(library, version, overwrite_existing=False):
    if library in already_added:
        return
    try:
        current_deps = subprocess.check_output(["poetry", "show", "--tree"]).decode("utf-8").lower()
        if library.lower() in current_deps and not overwrite_existing:
            print_info(f"{library} already exists in pyproject.toml. Skipping.")
            return
        if version and version != "*":
            dependency_spec = f"{library}=={version}"
        else:
            dependency_spec = library
        try:
            subprocess.check_call(["poetry", "add", dependency_spec])
            print_info(f"Added {dependency_spec} to Poetry.")
            successfully_added.append(dependency_spec)
        except subprocess.CalledProcessError:
            if version and version != "*":
                print_warning(f"Failed to add {dependency_spec} with version constraint. Trying without version constraint.")
                try:
                    subprocess.check_call(["poetry", "add", library])
                    print_info(f"Added {library} (without version constraint) to Poetry.")
                    successfully_added.append(library)
                except subprocess.CalledProcessError as inner_error:
                    print_warning(f"Skipping {library} due to build errors: {inner_error}")
            else:
                print_warning(f"Skipping {library} due to unresolved installation issues.")
        already_added.add(library)
    except subprocess.CalledProcessError as e:
        print_error(f"Error adding {library}: {e}")

def parse_requirements_and_add(overwrite_existing=False):
    if not os.path.exists("requirements.txt"):
        print_error("requirements.txt not found.")
        sys.exit(1)
    with open("requirements.txt", "r") as req_file:
        for line in req_file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            match = re.match(r"([A-Za-z0-9._-]+)(==([\w.+-]+))?", line)
            if match:
                library = match.group(1)
                version = match.group(3) if match.group(3) else "*"
                add_library_to_poetry(library, version, overwrite_existing)
            else:
                print_warning(f"Could not parse the requirement line: {line}")

def add_venv_packages_to_poetry(overwrite_existing=False):
    venv_packages = get_venv_packages()
    if not venv_packages:
        return
    print_info("Adding packages from the active Python virtual environment to Poetry...")
    for library, version in venv_packages.items():
        if library not in already_added:
            add_library_to_poetry(library, version if version else "*", overwrite_existing)

def clean_up_pyproject():
    if os.path.exists("pyproject.toml"):
        with open("pyproject.toml", "r") as file:
            lines = file.readlines()
        with open("pyproject.toml", "w") as file:
            for line in lines:
                if not re.match(r'\s*readme\s*=\s*"README\.md"', line):
                    file.write(line)
        print_info('Removed `readme = "README.md"` from pyproject.toml.')

def main():
    parser = argparse.ArgumentParser(
        description="Add dependencies to Poetry using pipreqs and Python venv for requirements generation."
    )
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing dependencies in pyproject.toml if they already exist.")
    args = parser.parse_args()
    check_poetry_installed()
    create_pyproject_if_missing()
    ensure_pipreqs_installed()
    generate_requirements_with_pipreqs(overwrite=args.overwrite)
    parse_requirements_and_add(overwrite_existing=args.overwrite)
    add_venv_packages_to_poetry(overwrite_existing=args.overwrite)
    clean_up_pyproject()
    if successfully_added:
        print_info("Done")
        print(GREEN + "These dependencies were added to your Poetry's pyproject.toml:" + RESET)
        for dep in successfully_added:
            print(f"  - {GREEN}{dep}{RESET}")
        print_info("By: https://raw.githubusercontent.com/therealaleph/poetry-auto-add")
    else:
        print_info("No new dependencies were added to Poetry.")

if __name__ == "__main__":
    main()
