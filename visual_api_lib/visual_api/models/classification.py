"""
 Copyright (c) 2023 ML course
 Created by Aleksey Korobeynikov
"""

import numpy as np

from ..common import NumericalValue, ListValue, StringValue, softmax

from .image_model import ImageModel


class Classification(ImageModel):
    __model__ = 'classification'

    def __init__(self, network_info, configuration=None):
        super().__init__(network_info, configuration)
        self._check_io_number(1, 1)
        if self.path_to_labels:
            self.labels = self._load_labels(self.path_to_labels)
        self.out_layer_name = self._get_outputs()

    def _load_labels(self, labels_file):
        with open(labels_file, 'r') as f:
            labels = []
            for s in f:
                begin_idx = s.find(' ')
                if (begin_idx == -1):
                    self.raise_error('The labels file has incorrect format.')
                end_idx = s.find(',')
                labels.append(s[(begin_idx + 1):end_idx])
        return labels

    def _get_outputs(self):
        layer_name = next(iter(self.outputs))
        layer_shape = self.outputs[layer_name].shape

        if layer_shape and len(layer_shape) != 2 and len(layer_shape) != 4:
            self.raise_error('The Classification model wrapper supports topologies only with 2D or 4D output')
        if len(layer_shape) == 4 and (layer_shape[2] != 1 or layer_shape[3] != 1):
            self.raise_error('The Classification model wrapper supports topologies only with 4D '
                             'output which has last two dimensions of size 1')
        if self.labels:
            if (layer_shape[1] == len(self.labels) + 1):
                self.labels.insert(0, 'other')
                self.logger.warning("\tInserted 'other' label as first.")
            if layer_shape[1] != len(self.labels):
                self.raise_error("Model's number of classes and parsed "
                                 'labels must match ({} != {})'.format(layer_shape[1], len(self.labels)))
        return layer_name

    @classmethod
    def parameters(cls):
        parameters = super().parameters()
        parameters['resize_type'].update_default_value('crop')
        parameters.update({
            'topk': NumericalValue(value_type=int, default_value=1, min=1),
            'labels': ListValue(description="List of class labels"),
            'path_to_labels': StringValue(
                description="Path to file with labels. Overrides the labels, if they sets via 'labels' parameter"
            ),
        })
        return parameters

    def postprocess(self, outputs, meta):
        outputs = outputs[self.out_layer_name].squeeze()
        indices = np.argpartition(outputs, -self.topk)[-self.topk:]
        scores = outputs[indices]

        desc_order = scores.argsort()[::-1]
        scores = scores[desc_order]
        indices = indices[desc_order]
        if not np.isclose(np.sum(outputs), 1.0, atol=0.01):
            scores = softmax(scores)
        labels = [self.labels[i] if self.labels else "" for i in indices]
        return list(zip(indices, labels, scores))
