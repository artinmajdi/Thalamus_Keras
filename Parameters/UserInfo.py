class experiment:
    # Address to the experiment directory
    exp_address = '/array/hdd/msmajdi/experiments/exp6/'

    # Path to the training data
    train_address = '/array/hdd/msmajdi/data/preprocessed/train/'

    # Path to the testing data
    test_address = '/array/hdd/msmajdi/data/preprocessed/test/'

    # Subexperiment name
    subexperiment_name = 'test_03_wmn'

    # Reading augmented data. If TRUE, it'll read the data stored inside the subfolder called 'Augments'
    ReadAugments_Mode = True

    # Path to the code
    code_address = '/array/ssd/msmajdi/code/CNN/'


""" if init_address will be left empty, the default address will be used for initialization """


class initialize:
    # If TRUE, network weights will be initialized
    mode = True

    # modality of the input data. wmn / csfn
    modality_default = 'wmn'

    # Path to the initialization network. If left empty, the algorithm will use the default path to sample initialization networks
    init_address = ''  # '/array/ssd/msmajdi/code/Trained_Models/WMn/'


# This class specifies while thalamic sides will be analysed
class thalamic_side:
    # Left Thalamus
    left = True

    # Right Thalamus
    right = True

    # This can be left empty. It is used during the training & testing process
    active_side = ''


class normalize:
    """ Network initialization 

        Mode (boolean): If TRUE, input data will be normalized using the specified method

        Method (str):
          - MinMax: Data will be normalized into 0 minimum & 1 maximum
          - 1Std0Mean: Data will be normalized into 0 minimum & 1 standard deviation
          - Both: Data will be normalized using both above methods       
    """

    Mode = True
    Method = '1Std0Mean'


class preprocess:
    """ Pre-processing flags
      - Mode             (boolean):   TRUE/FALSE
      - BiasCorrection   (boolean):   Bias Field Correction
      - Cropping         (boolean):   Cropping the input data using the cropped template
      - Reslicing        (boolean):   Re-slicing the input data into the same resolution
      - save_debug_files (boolean):   TRUE/FALSE
      - Normalize        (normalize): Data normalization
    """
    Mode = True
    BiasCorrection = False
    Cropping = True
    Reslicing = True
    save_debug_files = True
    Normalize = normalize()


class TestOnly:
    # If TRUE , it will run the trained model on test cases.
    mode = True

    """ Address to the main folder holding the trained model.
        This address only applies if mode==True. otherwise it will use the address specified by experiment & subexperiment 
        This directory should point to the parent folder holding on trained models: 
            ACTUAL_TRAINED_MODEL_ADDRESS = model_adress + '/' + FeatureMapNum (e.g. FM20) + '/' + Nucleus_name (e.g. 2-AV) + '/' + Orientation Index (e.g. sd2)
    """
    model_address = ''


class simulation:
    def __init__(self):
        # If TRUE, it will ignore the train data and run the already trained network on test data
        self.TestOnly = TestOnly()

        # Number of epochs used during training
        self.epochs = 5

        # The GPU card used for training/testing
        self.GPU_Index = "3"

        # Batch size used during training
        self.batch_size = 10

        # If TRUE, it will use test cases for validation during training
        self.Use_TestCases_For_Validation = True

        # If TRUE, it will perform morphological closing onto the predicted segments
        self.ImClosePrediction = True

        # If TRUE, it will Use a learning rate scheduler 
        self.LR_Scheduler = True

        # Initial Learning rate
        self.Learning_Rate = 1e-3

        # Number of layers
        self.num_Layers = 3

        """ Loss function index
                1: binary_crossentropy
                2: categorical_crossentropy
                3: multi class binary_crossentropy 
                4: Logarithm of Dice
                5: Logarithm of Dice + binary_crossentropy
                6: Gmean: Square root of (Logarithm of Dice + binary_crossentropy),
                7: Dice (default) 
        """
        self.lossFunction_Index = 7

        # nuclei indeces
        self.nucleus_Index = [1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]

        # slicing orientation. should be left as is
        self.slicingDim = [2, 1, 0]

        # If TRUE, it will use the network input dimentions obtained from training data for testing data
        self.use_train_padding_size = False

        # If TRUE, it will only load the subject folders that include "vimp" in their name
        self.check_vimp_SubjectName = True

        # Architecture type
        self.architectureType = 'Res_Unet2'

        # Number of feature maps for the first layer of Resnet
        self.FirstLayer_FeatureMap_Num = 20


class InputPadding:
    def __init__(self):
        """ Network Input Dimension
            If Automatic is set to TRUE, it will determine the network input dimention from all training & testing data
            Othewise, it will use the values set in the "HardDimensions" variable
        """
        self.Automatic = True
        self.HardDimensions = [116, 144, 84]


code_address = experiment().code_address


class Templatecs:
    def __init__(self):
        """ The path to template nifti image and its corresponding cropping mask

        Args:
            Image   (str): path to original template
            Mask    (Str): path to the cropping mask
            Address (Str): path to the main folder
        """
        self.Image = code_address + 'general/RigidRegistration' + '/origtemplate.nii.gz'
        self.Mask = code_address + 'general/RigidRegistration' + '/CropMaskV3.nii.gz'
        self.Address = code_address + 'general/RigidRegistration/'


Template = Templatecs()
