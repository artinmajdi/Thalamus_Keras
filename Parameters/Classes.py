
class template:
    Image = ''
    Mask  = ''

class dropout:
    Mode = True
    Value = 0.2

class kernel_size:
    conv = (3,3)
    convTranspose = (2,2)
    output = (1,1)

class activation:
    layers = 'relu'
    output = 'sigmoid'

class convLayer:
    # strides = (1,1)
    Kernel_size = kernel_size
    padding = 'SAME' # valid

class multiclass:
    num_classes = ''
    mode = ''

class maxPooling:
    strides = (2,2)
    pool_size = (2,2)



class model:
    architectureType = 'U-Net'
    epochs = ''
    batch_size = ''
    loss = ''
    metrics = ''
    optimizer = ''  # adamax Nadam Adadelta Adagrad  optimizers.adam(lr=0.001, beta_1=0.9, beta_2=0.999, epsilon=None, decay=0.0, amsgrad=False)
    num_Layers = ''
    InputDimensions = ''
    batchNormalization = True # True
    ConvLayer = convLayer
    MaxPooling = maxPooling
    Dropout = dropout
    Activitation = activation
    showHistory = True
    LabelMaxValue = 1
    Measure_Dice_on_Train_Data = False
    MultiClass = multiclass
    #! only one of these two can be true at the same time
    InitializeFromThalamus = ''
    InitializeFromOlderModel = ''




class machine:
    WhichMachine = 'server'
    GPU_Index = ''

class image:
    SlicingDirection = 'axial'.lower()
    SaveMode = 'nifti'.lower()

class nucleus:
    Organ = 'THALAMUS' # 'Hippocampus
    name = ''
    name_Thalamus = ''
    FullIndexes = ''
    Index = ''


class hardParams:
    Model    = model
    Template = template
    Machine  = machine
    Image    = image

class experiment:
    index = ''
    tag = 'tmp'
    name = ''
    address = ''


class subExperiment:
    index = ''
    tag = ''
    name = ''
    name_thalamus = ''

class validation:
    percentage = 0.1
    fromKeras = True

class test:
    mode = 'percentage' # 'names'
    percentage = 0.3
    subjects = ''

# TODO IMPORT TEST SUBJECTS NAMES AS A LIST
if 'names' in test.mode: # import test.subjects
    test.subjects = list([''])

class dataset:
    name = ''
    address = ''
    Validation = validation
    Test = test
    onlySubjectsWvimp = True

class WhichExperiment:
    Experiment    = experiment
    SubExperiment = subExperiment
    address = ''
    Nucleus = nucleus
    HardParams = hardParams
    Dataset = dataset

class reference:
    name = ''
    address = ''

class Augment:
    Mode = ''
    LinearAugmentLength = 2  # number
    NonLinearAugmentLength = 2
    Rotation = ''
    Shift = ''
    NonRigidWarp = ''


class Normalize:
    Mode = ''
    Method = 'MinMax'


class Cropping:
    Mode = ''
    Method = ''

class BiasCorrection:
    Mode = ''

# TODO fix the justfornow
class Debug:
    doDebug = True
    PProcessExist = False  # rename it to preprocess exist
    justForNow = True # it checks the intermediate steps and if it existed don't reproduce it

class preprocess:
    Mode = ''
    CreatingTheExperiment = False
    TestOnly = ''
    Debug = Debug
    Augment = Augment
    Cropping = Cropping
    Normalize = Normalize
    BiasCorrection = BiasCorrection




# class trainCase:
#     def __init__(self, Image, Mask):
#         self.Image = Image
#         self.Mask  = Mask

# class testCase:
#     def __init__(self, Image, Mask, OrigMask, Affine, Header, original_Shape):
#         self.Image = Image
#         self.Mask = Mask
#         self.OrigMask  = OrigMask
#         self.Affine = Affine
#         self.Header = Header
#         self.original_Shape = original_Shape

