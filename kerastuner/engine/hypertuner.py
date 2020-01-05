"Meta classs for hypertuner"
import time
import keras
import random
import sys
import json
import os
from termcolor import cprint
from xxhash import xxh64 # xxh64 is faster
from tabulate import tabulate

from .instance import Instance


class HyperTuner(object):
    """Abstract hypertuner class."""
    def __init__(self, model_fn, **kwargs):
        self.num_iterations = kwargs.get('num_iterations', 10) # how many models
        self.num_executions = kwargs.get('num_executions', 3) # how many executions
        self.dryrun = kwargs.get('dryrun', False)
        self.max_fail_streak = kwargs.get('max_fail_streak', 20)
        self.num_gpu = kwargs.get('num_gpu', -1)
        self.gpu_mem = kwargs.get('gpu_mem', -1)
        self.local_dir = kwargs.get('local_dir', 'results/')
        self.gs_dir = kwargs.get('gs_dir', None)
        self.model_name = kwargs.get('model_name', str(int(time.time())))
        self.display_model = kwargs.get('display_model', '') # which models to display
        self.invalid_models = 0 # how many models didn't work
        self.collisions = 0 # how many time we regenerated the same model
        self.instances = {} # All the models we trained with their stats and info
        self.current_instance_idx = -1 # track the current instance trained
        self.model_fn = model_fn
        self.ts = int(time.time())


        
        # metrics     
        self.METRIC_NAME = 0
        self.METRIC_DIRECTION = 1
        self.max_acc = -1
        self.min_loss = sys.maxsize
        self.max_val_acc = -1
        self.min_val_loss = sys.maxsize

        
        # including user metrics
        user_metrics = kwargs.get('metrics')
        if user_metrics:
          self.key_metrics = []
          for tm in user_metrics:
            if not isinstance(tm, tuple):
              cprint("[Error] Invalid metric format: %s (%s) - metric format is (metric_name, direction) e.g ('val_acc', 'max') - Ignoring" % (tm, type(tm)), 'red')
              continue
            if tm[self.METRIC_DIRECTION] not in ['min', 'max']:
              cprint("[Error] Invalid metric direction for: %s - metric format is (metric_name, direction). direction is min or max - Ignoring" % tm, 'red')
              continue
            self.key_metrics.append(tm)
        else:
          # sensible default
          self.key_metrics = [('loss', 'min'), ('val_loss', 'min'), ('acc', 'max'), ('val_acc', 'max')]

        # initializing key metrics
        self.stats = {}
        for km in self.key_metrics:
          if km[self.METRIC_DIRECTION] == 'min':
            self.stats[km[self.METRIC_NAME]] = sys.maxsize
          else:
            self.stats[km[self.METRIC_NAME]] = -1

        # output control
        if self.display_model not in ['', 'base', 'multi-gpu', 'both']:
              raise Exception('Invalid display_model value: can be either base, multi-gpu or both')
    
        # create local dir if needed
        if not os.path.exists(self.local_dir):
          os.makedirs(self.local_dir)

    def get_random_instance(self):
      "Return a never seen before random model instance"
      fail_streak = 0
      while 1:
        fail_streak += 1
        try:
          model = self.model_fn()
        except:
          self.invalid_models += 1
          cprint("[WARN] invalid model %s/%s" % (self.invalid_models, self.max_fail_streak), 'yellow')
          if self.invalid_models >= self.max_fail_streak:
            return None
          continue

        idx = self.__compute_model_id(model)
        
        if idx not in self.instances:
          break
        self.collisions += 1
        
      self.instances[idx] = Instance(model, idx, self.model_name, self.num_gpu, self.gpu_mem, self.display_model)
      self.current_instance_idx = idx
      return self.instances[idx] 

    def record_results(self, save_models=True, idx=None):
      """Record instance results
      Args:
        save_model (bool): Save the trained models?
        idx (xxhash): index of the instance. By default use the lastest instance for convience.  
      """

      if not idx:
        instance = self.instances[self.current_instance_idx]
      else:
        instance = self.instances[idx]
      results = instance.record_results(self.local_dir, gs_dir=self.gs_dir, save_models=save_models, prefix=self.model_name, key_metrics=self.key_metrics)

      cprint("Key metrics", "magenta")
      report = [['Metric', 'Best', 'Last']]
      for km in self.key_metrics:
        metric_name = km[self.METRIC_NAME]
        if metric_name in results:
          current_best = self.stats[metric_name]
          res_val = results[metric_name]
          if km[self.METRIC_DIRECTION] == 'min':
            best = min(current_best, res_val)
          else:
            best = max(current_best, res_val)
          self.stats[metric_name] = best
        report.append([metric_name, best, res_val])
      print (tabulate(report, headers="firstrow"))

    def get_model_by_id(self, idx):
      return self.instances.get(idx, None)
     
    def __compute_model_id(self, model):
      return xxh64(str(model.get_config())).hexdigest()

    def statistics(self):
      # FIXME expand statistics
      ###       run = {
      ##  'ts': self.ts,
      ##  'iterations': self.num_iterations,
      ##  'executions': self.num_executions,
      ##  'min_loss': self.min_loss,
      ##}

      print("Invalid models:%s" % self.invalid_models)
      print("Collisions: %s" % self.collisions)