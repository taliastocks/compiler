import fire

from .language_models import program as program_module


def main(package_path: str, entrypoint: str = 'main.main'):
    program = program_module.Program()
    program.register_package((), package_path)

    entrypoint_module_path, entrypoint_method_name = entrypoint.rsplit('.', 1)
    entrypoint_module_path = tuple(entrypoint_module_path.split('.'))

    module = program.get_module(entrypoint_module_path)
    method = getattr(module, entrypoint_method_name)
    method()


fire.Fire(main)
