# Copyright 2019 The Keras Tuner Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"Tuner that runs multiple executions per Trial."

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from ..engine import trial as trial_lib
from ..engine import tuner as tuner_module
from ..engine import oracle as oracle_module
from ..engine import hyperparameters as hp_module
from ..abstractions.tensorflow import TENSORFLOW_UTILS as tf_utils

import collections
import random
import json
from tensorflow import keras


class MultipleExecutionsTuner(tuner_module.Tuner):


    def __init__(self,
                 oracle,
                 hypermodel,
                 executions_per_trial=1,
                 **kwargs):
        super(MultipleExecutionsTuner, self).__init__(
            oracle, hypermodel, **kwargs)
        if isinstance(oracle.objective, (list, tuple)):
            raise ValueError(
                'Multi-objective is not supported, found: {}'.format(
                    oracle.objective))
        self.executions_per_trial = executions_per_trial
        # This is the `step` that will be reported to the Oracle at the end
        # of the Trial. Since intermediate results are not used, this is set
        # to 0.
        self._reported_step = 0

    def on_epoch_end(self, trial, model, epoch, logs=None):
        # Intermediate results are not passed to the Oracle, and
        # checkpointing is handled via a `ModelCheckpoint` callback.
        pass

    def run_trial(self, trial, *fit_args, **fit_kwargs):
        fit_kwargs = copy.copy(fit_kwargs)
        original_callbacks = fit_kwargs.get('callbacks', [])[:]
        fit_kwargs['callbacks'] = self._inject_callbacks(
            original_callbacks, trial)
        metrics = collections.defaultdict(list)

        # Run the training process multiple times.
        for execution in self.executions_per_trial:
            model = self._build_model(trial.hyperparameters.copy())
            self._compile_model(model)
            history = model.fit(*fit_args, **fit_kwargs)
            for metric, epoch_values in history.history:
                metrics[metrics].append(epoch_values[-1])

        # Average the results across executions and send to the Oracle.
        averaged_metrics = {}
        for metric, execution_values in metrics:
            averaged_metrics[metric] = np.mean(execution_values)
        self.oracle.update_trial(
            trial.trial_id, metrics=averaged_metrics, step=self._reported_step)

    def _inject_callbacks(self, callbacks, trial):
        callbacks = super(MultipleExecutionsTuner, self)._inject_callbacks(
            callbacks, trial)
        model_checkpoint = keras.callbacks.ModelCheckpoint(
            filepath=self._get_checkpoint_fname(trial, self._reported_step),
            monitor=self.objective.name,
            mode=self.objective.direction,
            save_best_only=True,
            save_weights_only=True)
        callbacks.append(model_checkpoint)
        return callbacks


