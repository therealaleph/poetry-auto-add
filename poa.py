import os
import re
import subprocess
import sys
import logging
logger = logging.getLogger(__name__)
already_added = []
def check_poetry_installed():
    try:
        subprocess.check_call(["poetry", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print("Poetry is not installed. Please install Poetry and rerun the script.")
        sys.exit(1)

def get_library_versions():
    """
    Recursively searches for .py files and requirements.txt in the current
    directory, extracts library versions (ignoring built-in modules), and adds 
    them to poetry, handling potential conflicts and special cases like 
    'six.moves' by installing the top-level package.
    """
    if not os.path.exists("pyproject.toml"):
        create_pyproject = input("pyproject.toml not found. Create one with 'poetry init'? [yes/no]: ")
        if create_pyproject.lower() == "yes":
            try:
                subprocess.check_call(["poetry", "init"])
                logger.info("pyproject.toml created successfully.")
                subprocess.check_call(["poetry", "lock"])
            except subprocess.CalledProcessError as e:
                logger.error(f"Error creating pyproject.toml: {e}")
                return
        else:
            logger.error("Exiting script. Please create a pyproject.toml file first.")
            return

    for root, _, files in os.walk("."):
        for file in files:
            if file.endswith(".py"):
                extract_libraries_from_py(os.path.join(root, file))
            elif file == "requirements.txt":
                extract_libraries_from_requirements(os.path.join(root, file))

def extract_libraries_from_py(file_path):
    """
    Extracts library names and versions from a Python file, ignoring built-in 
    modules and handling special cases like 'six.moves' by installing the 
    top-level package.

    Args:
        file_path: The path to the Python file.
    """

    with open(file_path, "r") as f:
        content = f.read()
        import_statements = re.findall(r"import\s+([\w.]+)", content)
        for library in import_statements:
            if library in sys.builtin_module_names or f"_{library}" in sys.builtin_module_names:
                continue
            library = library.split(".")[0].lower()

            try:
                version = subprocess.check_output(
                    ["poetry", "show", "-t", library]
                ).decode("utf-8")
                version = re.search(r"[\w.-]+\s+\(([\w.]+)\)", version).group(1)
            except:
                try:
                    version = subprocess.check_output(
                        ["pip", "show", library]
                    ).decode("utf-8")
                    version = re.search(r"Version:\s+([\w.]+)", version).group(1)
                except subprocess.CalledProcessError:
                    version = "latest"

            add_to_poetry(library, version)

def extract_libraries_from_requirements(file_path):
    """
    Extracts library names and versions from a requirements.txt file.

    Args:
        file_path: The path to the requirements.txt file.
    """

    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                try:
                    match = re.match(r"([\w.]+)([=><!~]+)([\w.]+)", line)
                    if match:
                        library = match.group(1)
                        version_specifier = match.group(2)
                        version = match.group(3)
                        add_to_poetry(library, f"{version_specifier}{version}")
                    else:
                        add_to_poetry(line, "*") 
                except Exception as e:
                    logger.error(f"Warning: Could not parse line '{line}' in {file_path}: {e}")

def add_to_poetry(library, version):
    """
    Adds a library and its version to poetry, handling conflicts.

    Args:
        library: The name of the library.
        version: The version or version specifier of the library.
    """
    if library in already_added:
        return 
    try:
        current_deps = subprocess.check_output(["poetry", "show", "--tree"]).decode("utf-8")
        if library in current_deps:
            override = input(f"{library} already exists in pyproject.toml. Override? [default: no]: ")
            if override.lower() != "yes":
                logger.info(f"Skipping {library}{version}")
                return
        if version:
            try:
                subprocess.check_call(["poetry", "add", f"{library}=={version}"])
            except:
                subprocess.check_call(["poetry", "add", f"{library}"])
        else:
            subprocess.check_call(["poetry", "add", f"{library}"])
        already_added.append(library)
        logger.info(f"Added {library}{version} to poetry")
    except subprocess.CalledProcessError as e:
        pass

if __name__ == "__main__":
    check_poetry_installed()
    get_library_versions()
