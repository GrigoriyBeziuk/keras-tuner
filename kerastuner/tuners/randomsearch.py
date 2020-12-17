"Basic randomsearch tuner"
from termcolor import cprint
from ..engine import Tuner
from kerastuner.abstractions.display import subsection
from kerastuner.distributions import RandomDistributions


class RandomSearch(Tuner):
    "Basic hypertuner"

    def __init__(self, model_fn, objective, **kwargs):
        """ RandomSearch hypertuner
        Args:
            epoch_budget (int): How many epochs to spend hyper-tuning. Default 3171
            max_epochs (int): How long to train model at most. default 50
            model_name (str): used to prefix results. Default: timestamp

            executions (int): number of execution for each model tested

            display_model (str): base: cpu/single gpu version, multi-gpu: multi-gpu, both: base and multi-gpu. default (Nothing)

            num_gpu (int): number of gpu to use. Default 0
            gpu_mem (int): amount of RAM per GPU. Used for batch size calculation

            local_dir (str): where to store results and models. Default results/
            gs_dir (str): Google cloud bucket to use to store results and model (optional). Default None

            dry_run (bool): do not train the model just run the pipeline. Default False
            max_fail_streak (int): number of failed model before giving up. Default 20
        """

        # Do the super last -- it uses the variable setup by the tuner
        super(RandomSearch, self).__init__(model_fn, objective, 'RandomSearch',
                                           RandomDistributions, **kwargs)

    def tune(self, x, y, **kwargs):

        while self.state.remaining_budget:
            instance = self.new_instance()

            # not instances left time to wrap-up
            if not instance:
                break

            # train n executions for the given model
            for cur_execution in range(self.state.num_executions):
                # FIXME: move this to the execution code
                subsection("execution: %s/%s" % (cur_execution + 1,
                                                 self.state.num_executions))
                epochs = self.state.max_epochs
                instance_state = instance.fit(x, y, epochs, **kwargs)  # nopep8 pylint: disable=unused-variable
