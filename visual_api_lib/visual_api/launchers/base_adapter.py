"""
 Copyright (c) 2023 ML course
 Created by Aleksey Korobeynikov
"""

import abc
from dataclasses import dataclass, field
from typing import Dict, List, Set


@dataclass
class Metadata:
    names: Set[str] = field(default_factory=set)
    shape: List[int] = field(default_factory=list)
    layout: str = ''
    precision: str = ''
    type: str = ''
    meta: Dict = field(default_factory=dict)


class BaseLauncher(metaclass=abc.ABCMeta):
    '''
    An abstract Base Launcher with the following interface:
        - Reading the model from disk or other place
        - Loading the model to the device
        - Accessing the information about inputs/outputs
        - The model reshaping
        - Synchronous model inference
    '''
    precisions = ('FP32', 'I32', 'FP16', 'I16', 'I8', 'U8')

    @abc.abstractmethod
    def __init__(self):
        '''
        An abstract Base Launcher constructor.
        Reads the model from disk or other place.
        '''

    @abc.abstractmethod
    def load_model(self):
        '''
        Loads the model on the device.
        '''

    @abc.abstractmethod
    def get_input_layers(self):
        '''
        Gets the names of model inputs and for each one creates the Metadata structure,
           which contains the information about the input shape, layout, precision
           in OpenVINO format, meta (optional)
        Returns:
            - the dict containing Metadata for all inputs
        '''

    @abc.abstractmethod
    def get_output_layers(self):
        '''
        Gets the names of model outputs and for each one creates the Metadata structure,
           which contains the information about the output shape, layout, precision
           in OpenVINO format, meta (optional)
        Returns:
            - the dict containing Metadata for all outputs
        '''

    @abc.abstractmethod
    def reshape_model(self, new_shape):
        '''
        Reshapes the model inputs to fit the new input shape.
        Args:
            - new_shape (dict): the dictionary with inputs names as keys and
                list of new shape as values in the following format:
                {
                    'input_layer_name_1': [1, 128, 128, 3],
                    'input_layer_name_2': [1, 128, 128, 3],
                    ...
                }
        '''

    @abc.abstractmethod
    def infer_sync(self, dict_data):
        '''
        Performs the synchronous model inference. The infer is a blocking method.
        Args:
            - dict_data: it's submitted to the model for inference and has the following format:
                {
                    'input_layer_name_1': data_1,
                    'input_layer_name_2': data_2,
                    ...
                }
        Returns:
            - raw result (dict) - model raw output in the following format:
                {
                    'output_layer_name_1': raw_result_1,
                    'output_layer_name_2': raw_result_2,
                    ...
                }
        '''