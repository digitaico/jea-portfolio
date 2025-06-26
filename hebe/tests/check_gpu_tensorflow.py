# --- check gpu under Tnesorflow
import tensorflow as tf

gpus = tf.config.list_physical_devices('GPU')
if gpus:
    print("GPU(s) found:")
    for gpu in gpus:
        print(f" {gpu.name}")
else:
    print("No GPU detected under Tensorflow")



