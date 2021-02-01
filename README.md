# Keras Tuner

An hyperparameter tuner for [Keras](https://keras.io).


# Example
Here's how to perform hyperparameter tuning on the MNIST digits dataset.

```py
from tensorflow import keras
from tensorflow.keras import layers

import numpy as np

from tuner import SequentialRandomSearch
from hypermodel import HyperModel
from hyperparameters import HyperParameters


(x, y), (val_x, val_y) = keras.datasets.mnist.load_data()
x = x.astype('float32') / 255.
val_x = val_x.astype('float32') / 255.


"""Basic case:
- We define a `build_model` function
- It returns a compiled model
- It uses hyperparameters defined on the fly
"""


def build_model(hp):
    model = keras.Sequential()
    model.add(layers.Flatten(input_shape=(28, 28)))
    for i in range(hp.Range('num_layers', 2, 20)):
        model.add(layers.Dense(units=hp.Range('units_' + str(i), 32, 512, 32),
                               activation='relu'))
    model.add(layers.Dense(10, activation='softmax'))
    model.compile(
        optimizer=keras.optimizers.Adam(
            hp.Choice('learning_rate', [1e-2, 1e-3, 1e-4])),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy'])
    return model


tuner = SequentialRandomSearch(
    build_model,
    objective='val_accuracy')

tuner.search(trials=2,
             x=x,
             y=y,
             epochs=5,
             validation_data=(val_x, val_y))

```
