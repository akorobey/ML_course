"""
 Copyright (c) 2023 ML course
 Created by Aleksey Korobeynikov
"""

import importlib
import numpy as np
import logging as log
import torch
from pathlib import Path

from .base_launcher import BaseLauncher, Metadata
from ..common import NetworkInfo, prepend_to_path


"""
  PyTorch supports loading models in 2 modes:
    1) state_dict:
           model = TheModelClass(*args, **kwargs)
           model.load_state_dict(torch.load(PATH))
           model.eval()
    2) load entire model (doen't need class of model):
           model = torch.load(PATH)
           model.eval()
"""

class PyTorchLauncher(BaseLauncher):
    __provider__ = "pytorch"

    def __init__(self, model_configuration):
        # Load and compile model
        if "module_name" in model_configuration:
            # 1 mode from model class and state_dict
            with prepend_to_path([str(Path(model_configuration.get("module_name", "")).parent.resolve())]):
                module = importlib.import_module(Path(model_configuration.get("module_name", "")).name)
                creator = getattr(module, model_configuration.get("model_name", ""))
                self.model = creator()
                weights = model_configuration.get("model_path", "")
                self.model.load_state_dict(torch.load(weights, map_location='cpu'))
        else:
            # 2 mode from .pt file
            self.model = torch.load(model_configuration.get("model_path", ""))
        self.model_configuration = model_configuration
        self.device = "cpu"
        self.compile_model()
        # get info about model
        self.model_info = NetworkInfo(self.get_input_layers(), self.get_output_layers())

    def compile_model(self, model_type="baseline"):
        if model_type == 'baseline':
            log.info('Inference will be executed on baseline model')
        elif model_type == 'scripted':
            log.info('Inference will be executed on scripted model')
            self.model = torch.jit.script(self.model)
        else:
            raise ValueError(f'Model type {model_type} is not supported for inference')
        self.model.to(self.device)
        self.model.eval()


    def get_input_layers(self):
        input_info = {}
        for input_node, input_shape in self.model_configuration["inputs"].items():
            layout = ""
            if len(input_shape) == 4:
                layout = 'NCHW'
            input_info[input_node] = Metadata(input_node, shape=input_shape, layout=layout)

        return input_info

    def get_output_layers(self):
        output_info = {}
        for output_node, ouptut_shape in self.model_configuration["outputs"].items():
            output_info[output_node] = Metadata(output_node, shape=ouptut_shape)

        return output_info

    def infer_sync(self, dict_data):
        # convert types of tensors
        for key, input_tensor in dict_data.items():
            dict_data[key] = torch.Tensor(input_tensor.astype(self.model_info.inputs_info[key].type))

        outputs = self.model(*list(dict_data.values()))

        output_dict = {}
        for key, value in zip(self.model_info.outputs_info.keys(), outputs):
            output_dict[key] = value.detach().numpy()

        return output_dict
