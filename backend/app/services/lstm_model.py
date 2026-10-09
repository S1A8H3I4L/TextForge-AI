"""LSTM architecture: Embedding -> stacked LSTM -> Dense(softmax)."""


def build_lstm_model(
    vocab_size: int,
    seq_length: int,
    embedding_dim: int = 128,
    lstm_units: int = 256,
    lstm_layers: int = 2,
    dropout: float = 0.2,
):
    # Imported lazily so the API (auth, history...) can start without loading TensorFlow.
    from tensorflow import keras
    from tensorflow.keras import layers

    model = keras.Sequential(name="textforge_lstm")
    model.add(layers.Input(shape=(seq_length,), dtype="int32"))
    model.add(layers.Embedding(vocab_size, embedding_dim, mask_zero=False))
    for i in range(lstm_layers):
        last = i == lstm_layers - 1
        model.add(layers.LSTM(lstm_units, return_sequences=not last))
        model.add(layers.Dropout(dropout))
    model.add(layers.Dense(vocab_size, activation="softmax"))

    # sparse_categorical_crossentropy == categorical_crossentropy on integer labels,
    # without materialising a (samples x vocab) one-hot matrix in memory.
    model.compile(
        loss="sparse_categorical_crossentropy",
        optimizer=keras.optimizers.Adam(learning_rate=1e-3),
        metrics=["accuracy"],
    )
    return model
