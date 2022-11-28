from glob import glob
from os import makedirs, path
from shutil import copy, copytree, rmtree
from yaml import load, FullLoader


src_dir = "src"
steps = []
dependencies = {}
common_files = []


class InvalidCommonFileException(Exception):
    def __init__(self, message):
        self.message = message


def clean():
    rmtree("gen", ignore_errors=True)


def load_dependencies():
    global dependencies
    with open(f"{src_dir}/dependencies.yml", "r") as file:
        dependencies = load(file, Loader=FullLoader)


def load_common_files():
    global common_files
    common_files = [
        "/".join(common_filepath.split("/")[2:])
        for common_filepath in glob(f"{src_dir}/common/**/*.py", recursive=True)
    ]


def build_custom_dependencies_for_file(current: str, next_in_hierarchy: list, dep: dict):
    if current in dep:
        custom_req = dep[current]["_req"] if "_req" in dep[current] else []
        custom_dep = dep[current]["_dep"] if "_dep" in dep[current] else []
        new_current = next_in_hierarchy.pop(0)
        next_req, next_dep = build_custom_dependencies_for_file(
            new_current, next_in_hierarchy, dep[current]
        )
        return custom_req + next_req, custom_dep + next_dep
    return [], []


def build_dependencies_for_file(file: str):
    globals_dep = dependencies["globals"]
    req = globals_dep["_req"]
    dep = globals_dep["_dep"]
    current, *next_in_hierarchy = file.split(".")
    custom_req, custom_dep = build_custom_dependencies_for_file(
        current, next_in_hierarchy, dependencies["lambda"]
    )
    return req + custom_req, dep + custom_dep


def generate_lambda_src():
    for filepath in glob(f"{src_dir}/lambda/*.py"):
        file = filepath.split("/")[-1]
        new_dir = path.join("gen", *file.split(".")[:-1])
        makedirs(new_dir)
        copy(filepath, f"{new_dir}/index.py")
        reqs, deps = build_dependencies_for_file(file)
        with open(f"{new_dir}/requirements.txt", "w") as req_file:
            req_file.write("\n".join(reqs))

        for dep in deps:
            # module
            if ".py" not in dep:
                dep = dep.replace(".", "/")
                copytree(f"{src_dir}/common/{dep}", f"{new_dir}/{dep}")
                continue

            if dep not in common_files:
                raise InvalidCommonFileException(
                    f"File '{file}' requires common file '{dep}', but it wasn't found in 'src/common' folder"
                )
            dep_dir = "/".join(dep.split("/")[:-1])

            # nested file
            if dep_dir:
                makedirs(f"{new_dir}/{dep_dir}", exist_ok=True)

            copy(f"{src_dir}/common/{dep}", f"{new_dir}/{dep}")


def add_step(comment: str, func):
    steps.append((comment, func))


def run():
    length = len(steps)
    length_str_size = len(str(length))
    for i, step in enumerate(steps):
        comment, func = step
        print(f"[{i+1: <{length_str_size}}/{length}]: {comment}")
        func()


def main():
    add_step("Cleaning 'gen' folder", clean)
    add_step("Load dependencies file", load_dependencies)
    add_step("Load common files", load_common_files)
    add_step("Generate lambda sources", generate_lambda_src)

    run()


if __name__ == "__main__":
    main()
