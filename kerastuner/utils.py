def compute_max_batch_size(model, gpu_mem, max_size=8000):
    """Compute the largest batch size possible
      max_size (int): maximum batch size. 8k seems the limit based of https://research.fb.com/publications/accurate-large-minibatch-sgd-training-imagenet-in-1-hour/
    """

    batch_size, num_params = __compute_batch_size(model, gpu_mem, max_size)


def __compute_batch_size(model, memory, max_size):
    "Find the largest batch size usuable so we maximize ressources usage"
    batch_size = 16
    while 1:
        bs = batch_size + 2
        if bs >= max_size:
            break
        memory_needed, model_num_params = __get_model_memory_usage(model, bs)
        if memory_needed > memory:
            break
        batch_size = bs
    return batch_size, model_num_params


def __get_model_memory_usage(model, batch_size):
    "comput the memory usage for a given model and batch "
    import numpy as np
    from keras import backend as K

    shapes_mem_count = 0
    for l in model.layers:
        single_layer_mem = 1
        for s in l.output_shape:
            if s is None:
                continue
            single_layer_mem *= s
        shapes_mem_count += single_layer_mem

    trainable_count = np.sum([K.count_params(p)
                              for p in set(model.trainable_weights)])
    non_trainable_count = np.sum([K.count_params(p)
                                  for p in set(model.non_trainable_weights)])

    total_memory = 4.0*batch_size * \
        (shapes_mem_count + trainable_count + non_trainable_count)
    gbytes = np.round(total_memory / (1024.0 ** 3), 3)
    # print("train count ", trainable_count, "mem per instance", 
    # total_memory, "gbytes ", gbytes)
    return gbytes, trainable_count
