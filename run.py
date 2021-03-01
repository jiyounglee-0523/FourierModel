import subprocess
import os

# Configuration before run
os.environ["CUDA_VISIBLE_DEVICES"] = '0'
PATH = '/home/generativeODE/disentangled_ODE/'
SRC_PATH = PATH+'main.py'

TRAINING_CONFIG = {
    "in_features":1,
    "out_features":1,
    "latent_dimension":3,
    "expfunc":'fourier',
    "n_harmonics":50,
    "n_eig":2,
    #"path":'/data/private/generativeODE/galerkin_pretest/dilation_test/',    #  change this!
    "path": './',
    "filename": 'dataset6_with50integerharmonics',                      #  change this!
    "dataset_type":'dataset6',
    "description":'dataset6 with 50 integer harmonics to model sin(1.7x)',             # change this!
    "n_epochs":100000,
    "batch_size":1024,
}
TRAINING_CONFIG_LIST = ["--{}".format(k,v) if (isinstance(v, bool) and (v)) else "--{}={}".format(k,v) for (k,v) in list(TRAINING_CONFIG.items())]

# Run script
subprocess.run(['python',SRC_PATH]+TRAINING_CONFIG_LIST)