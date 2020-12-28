from __future__ import absolute_import

from .state import State
from kerastuner.abstractions.host import Host
from kerastuner.abstractions.display import fatal, subsection
from kerastuner.abstractions.display import display_settings, fatal
from kerastuner.abstractions.tensorflow import TENSORFLOW as tf
from kerastuner.abstractions.tensorflow import TENSORFLOW_UTILS as tf_utils
from kerastuner import config


class HostState(State):
    """
    Track underlying Host state

    Args:
        results_dir (str, optional): Tuning results dir. Defaults to results/.

        tmp_dir (str, optional): Temporary dir. Wipped at tuning start.
        Defaults to tmp/.

        export_dir (str, optional): Export model dir. Defaults to export/.
    """
    def __init__(self, **kwargs):
        super(HostState, self).__init__(**kwargs)

        self.results_dir = self._register('results_dir', 'results/', True)
        self.tmp_dir = self._register('tmp_dir', 'tmp/')
        self.export_dir = self._register('export_dir', 'export/', True)

        # ensure the user don't shoot himself in the foot
        if self.results_dir == self.tmp_dir:
            fatal('Result dir and tmp dir must be different')

        # create directory if needed
        tf_utils.create_directory(self.results_dir)
        tf_utils.create_directory(self.tmp_dir, remove_existing=True)
        tf_utils.create_directory(self.export_dir)

        # init _HOST
        config._Host = Host()
        status = config._Host.get_status()
        tf_version = status['software']['tensorflow']
        major, minor, rev = tf_version.split('.')
        if major == '1':
            if int(minor) >= 13:
                print('ok')
            else:
                fatal("Keras Tuner only work with TensorFlow version >= 1.13\
                    current version: %s - please upgrade" % tf_version)

    def summary(self, extended=False):
        subsection('Directories')
        settings = {
            "results": self.results_dir,
            "tmp": self.tmp_dir,
            "export": self.export_dir
        }
        display_settings(settings)
        if extended:
            config._Host.summary(extended=extended)

    def to_config(self):
        res = {}
        # collect user params
        for name in self.user_parameters:
            res[name] = getattr(self, name)

        # adding host hardware & software information
        res.update(config._Host.to_config())

        return res
