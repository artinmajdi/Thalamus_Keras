import os, sys
# __file__ = '/array/ssd/msmajdi/code/Thalamus_Keras/mainTest.py'  #! only if I'm using Hydrogen Atom
sys.path.append(os.path.dirname(__file__))
from otherFuncs.choosingModel import architecture, modelTrain
import numpy as np
from otherFuncs.datasets import loadDataset
from keras.models import load_model, Model
import matplotlib.pyplot as plt
from time import time
from tqdm import tqdm
from keras import backend as K
from otherFuncs import params
import tensorflow as tf
from otherFuncs.smallFuncs import terminalEntries, inputNamesCheck, imShow
params = terminalEntries(params)
params = inputNamesCheck(params)
os.environ["CUDA_VISIBLE_DEVICES"] = params.directories.Experiment.HardParams.Machine.GPU_Index


#! configing the GPU
session = tf.Session(   config=tf.ConfigProto( allow_soft_placement=True , gpu_options=tf.GPUOptions(allow_growth=True) )   )
K.set_session(session)


#! loading the dataset
Data = loadDataset( params )


#! Actual architecture
pred = {}
for params.directories.Experiment.HardParams.Model.architectureType in tqdm(['U-Net' , 'CNN_Segmetnation']): #]): #
    t = time()
    model, params = architecture(Data, params)
    model, hist   = modelTrain(Data, params, model)
    # model = load_model(params.directories.Train.Model + '/model.h5')
    pred[params.directories.Experiment.HardParams.Model.architectureType] = model.predict(Data.Test.Image)
    print(time() - t)


#! showing the outputs
ind = 5
imShow(Data.Test.Image[...,0], Data.Test.Label[...,0], pred, ind)

K.clear_session()
