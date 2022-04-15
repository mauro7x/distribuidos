import os
from jinja2 import Template
from constants import INPUT_FILEPATH, OUTPUT_FILEPATH, DEFAULT_N_CLIENTS


def config():
    return int(os.getenv('N_CLIENTS', DEFAULT_N_CLIENTS))


def read_file(filepath):
    with open(filepath, 'r') as file:
        source = file.read()
    return source


def save_file(content, filepath):
    with open(filepath, 'w') as file:
        file.write(content)


def apply_template(source, n_clients):
    template = Template(source)
    return template.render(n_clients=n_clients)


def main():
    print("Reading template file content...")
    source = read_file(INPUT_FILEPATH)
    print("Reading config...")
    n_clients = config()
    print(f"Applying template with {n_clients} clients")
    result = apply_template(source, n_clients)
    print("Saving output file...")
    save_file(result, OUTPUT_FILEPATH)
    print(f"Output file wrote to {OUTPUT_FILEPATH}")


if __name__ == "__main__":
    main()
