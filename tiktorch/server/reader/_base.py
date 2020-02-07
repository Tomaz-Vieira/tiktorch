import zipfile
import imp
from typing import List, Optional

import yaml

from pybio.spec import schema
from pybio.spec import node as nodes
from pybio.spec.utils import NodeTransformer


MODEL_EXTENSIONS = (".model.yaml", ".model.yml")


class ImportTransformer(NodeTransformer):
    def __init__(self, src: zipfile.ZipFile):
        self._src = src

    def transform_ImportablePath(self, node: nodes.ImportablePath):
        # TODO: Namespace modules eg "user_modules.<uuid>.module"
        code = self._src.read(node.filepath)
        mymodule = imp.new_module(f"user_modules.")
        exec(code, mymodule.__dict__)
        model_factory = getattr(mymodule, node.callable_name)
        return model_factory

    def transform_ImportableModule(self, node):
        raise NotImplementedError


def guess_model_path(file_names: List[str]) -> Optional[str]:
    for file_name in file_names:
        if file_name.endswith(MODEL_EXTENSIONS):
            return file_name

    return None


def eval_model(model_file: zipfile.ZipFile):
    config_file_name = guess_model_path(model_file.namelist())
    config_file = model_file.read(config_file_name)
    config_data = yaml.safe_load(config_file)

    model_config = schema.ModelSpec().load(config_data)

    import_transformer = ImportTransformer(model_file)
    model_config_evaluated = import_transformer.transform(model_config)
    model = model_config_evaluated.source(**model_config.optional_kwargs)
    return model
