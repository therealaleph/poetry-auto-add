# Poetry Library Version Extractor

This script extracts library versions from Python files and `requirements.txt` files, and adds them to a `pyproject.toml` using Poetry, handling potential conflicts and special cases. It ensures all necessary libraries are added to your Poetry environment.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [License](#license)

## Features

- Checks if Poetry is installed; prompts user if not.
- Searches recursively for `.py` files and `requirements.txt` files.
- Extracts library versions, ignoring built-in modules.
- Handles special cases like `six.moves` by installing the top-level package.
- Manages conflicts by prompting the user for overrides.

## Installation

To use this script, you need to have Python and Poetry installed on your system.

### Poetry Installation

Please follow the instructions from [Poetry's official documentation](https://python-poetry.org/docs/#installation) to install Poetry.

## Usage

1. Clone this repository:
    ```sh
    git clone https://github.com/therealaleph/poetry-auto-add.git
    cd poetry-auto-add
    ```

2. Ensure you have Poetry installed. If not, you will be prompted to install it and rerun the script.

3. Run the script:
    ```sh
    python poa.py
    ```

4. If a `pyproject.toml` file is not found, you will be asked if you want to create one using `poetry init`.

5. The script will recursively search for `.py` files and `requirements.txt` files, extract the library versions, and add them to `pyproject.toml`.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
