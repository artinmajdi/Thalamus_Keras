

#! Nucleus Index
nucleus_Index = [8]


#! Training
num_Layers = 5
epochs = 5
batch_size = 40
Initialize_FromThalamus = True
Initialize_FromOlderModel = False

#! GPU
GPU_Index = 6



#! Template Address
Tempalte_Image = '/array/ssd/msmajdi/code/general/RigidRegistration' + '/origtemplate.nii.gz'
Tempalte_Mask = '/array/ssd/msmajdi/code/general/RigidRegistration' + '/MyCrop_Template2_Gap20.nii.gz'


#! MultiClass
MultiClass_mode = False


#! metric function
#          1: 'Dice'
#          2: 'Accuracy'
#          3: 'Dice & Accuracy'
MetricIx = 3

#! loss function
# lossFunction=   1: 'dice'
#                 2: 'binary Cross Enropy'
#                 3: 'Both'
lossFunctionIx = 1

#! Dataset
# DatasetIx =     1: 'SRI_3T'
#                 2: 'kaggleCompetition'
#                 3: 'fashionMnist'
DatasetIx = 1

#! Optimizer
#          1: 'Adam'
OptimizerIx = 1


#! Experiments Address
Experiments_Address = '/array/ssd/msmajdi/experiments/keras'
Experiments_Index = 1
SubExperiment_Index = 1


#! cropping mode
#           1 or mask:     cropping using the cropped mask acquired from rigid transformation
#           2 or thalamus: cropping using the cropped mask for plain size and Thalamus Prediction for slice numbers
#           3 or both:     cropping using the Thalamus prediction
cropping_method = 2





#! Preprocessing
BiasCorrection = False
Cropping = True
Normalize = True
Augment = False

Augment_Rotation     = True
Augment_Shift        = False
Augment_NonRigidWarp = False