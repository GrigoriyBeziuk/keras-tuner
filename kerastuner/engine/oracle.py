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
"Oracle base class."


class Oracle(object):

    def __init__(self):
        self.space = hp_module.HyperParameters()

    def update_space(self, new_entries):
        """Add new hyperparameters to the tracking space.

        Already recorded parameters get ignored.

        Args:
            new_entries: A list of HyperParameter objects to track.
        """
        ref_names = {p.name for p in self.space}
        for p in new_entries:
            if p.name not in ref_names:
                self.space.append(p)

    def populate_space(self, space):
        """Fill a given hyperparameter space with values.

        Args:
            space: A list of HyperParameter objects
                to provide values for.

        Returns:
            A dictionary mapping parameter names to suggested values.
            Note that if the Oracle is keeping tracking of a large
            space, it may return values for more parameters
            than what was listed in `space`.
        """
        raise NotImplementedError

    def result(self, score, values):
        """Record the neasured objective for a set of parameter values.

        If not overriden, this method does nothing.

        Args:
            score: Scalar. Lower is better.
            values: Dictionary mapping parameter names to values
                used for obtaining the score.
        """
        pass

    def _raise_if_unknown_hyperparameter(self, hyperparameters):
        names = {p.name for p in hyperparameters}
        ref_names = {p.name for p in self.space}
        diff = names - ref_names
        if diff:
            raise ValueError(
                'Unknown parameters requested, call `update_space` first. '
                'Unknown:', diff)
