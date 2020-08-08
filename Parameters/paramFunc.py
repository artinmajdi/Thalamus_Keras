import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import modelFuncs.LossFunction as LossFunction
import modelFuncs.Metrics as Metrics
import modelFuncs.Optimizers as Optimizers
import otherFuncs.smallFuncs as smallFuncs
import numpy as np
import json

def temp_Experiments_preSet_V2(UserInfoB):

    class TypeExperimentFuncs():
        def __init__(self):            
            class ReadTrainC:
                def __init__(self, SRI=0 , ET=0 , Main=0 , CSFn1=0 , CSFn2=0):   
                    # class readAugments: Mode, Tag, LoadAll = False, '', False  # temp
                    class readAugments: Mode, Tag, LoadAll = True, '', False
                    self.SRI  = SRI  > 0.5
                    self.ET   = ET   > 0.5
                    self.Main = Main > 0.5
                    self.CSFn1 = CSFn1 > 0.5
                    self.CSFn2 = CSFn2 > 0.5

                    self.ReadAugments = readAugments                    
            self.ReadTrainC = ReadTrainC

            class Transfer_LearningC:
                def __init__(self, Mode=False , FrozenLayers = [0] , Tag = '_TF' , Stage = 0 , permutation_Index = 0):
                    
                    class unet_Freeze():

                        if permutation_Index == 0: # best
                            Contracting = {0:True, 1:True, 2:False, 3:False, 4:False, 5:False }
                            Expanding   = {0:True, 1:False, 2:False, 3:False, 4:False, 5:False }
                            Middle      = False

                        elif permutation_Index == 1:  # full fine tune
                            Contracting = {0:True, 1:True, 2:True, 3:True, 4:True, 5:True }
                            Expanding   = {0:True, 1:True, 2:True, 3:True, 4:True, 5:True }
                            Middle      = True

                        elif permutation_Index == 2: 
                            Contracting = {0:False, 1:False, 2:False, 3:False, 4:False, 5:False }
                            Expanding   = {0:True , 1:False, 2:False, 3:False, 4:False, 5:False }
                            Middle      = False

                        elif permutation_Index == 3:
                            Contracting = {0:True , 1:False, 2:False, 3:False, 4:False, 5:False }
                            Expanding   = {0:False, 1:False, 2:False, 3:False, 4:False, 5:False }
                            Middle      = False

                        elif permutation_Index == 4:
                            Contracting = {0:True , 1:True , 2:False, 3:False, 4:False, 5:False }
                            Expanding   = {0:False, 1:False, 2:False, 3:False, 4:False, 5:False }
                            Middle      = False

                        elif permutation_Index == 5:
                            Contracting = {0:False , 1:False, 2:False, 3:False, 4:False, 5:False }
                            Expanding   = {0:True  , 1:True, 2:False, 3:False, 4:False, 5:False }
                            Middle      = False

                        elif permutation_Index == 6:
                            Contracting = {0:True , 1:False, 2:False, 3:False, 4:False, 5:False }
                            Expanding   = {0:True , 1:False, 2:False, 3:False, 4:False, 5:False }
                            Middle      = False                            

                        elif permutation_Index == 7:
                            Contracting = {0:False , 1:True, 2:False, 3:False, 4:False, 5:False }
                            Expanding   = {0:False , 1:True, 2:False, 3:False, 4:False, 5:False }
                            Middle      = True  

                        elif permutation_Index == 8:
                            Contracting = {0:False , 1:False, 2:True, 3:True, 4:True, 5:True }
                            Expanding   = {0:False , 1:False, 2:True, 3:True, 4:True, 5:True }
                            Middle      = True  


                    self.Mode         = Mode
                    self.FrozenLayers = FrozenLayers
                    self.Stage        = Stage
                    self.Tag          = Tag
                    self.U_Net4       = unet_Freeze()
            self.Transfer_LearningC = Transfer_LearningC

            class InitializeB:
                def __init__(self, FromThalamus=False , FromOlderModel=False , From_3T=False , From_7T=False , From_CSFn1=False):
                    self.FromThalamus   = FromThalamus
                    self.FromOlderModel = FromOlderModel
                    self.From_3T        = From_3T
                    self.From_7T        = From_7T
                    self.From_CSFn1     = From_CSFn1
            self.InitializeB = InitializeB

        def main(self, TypeExperiment = 1, perm_Index = 0):
            switcher = {
                8:  (12  ,   self.ReadTrainC(CSFn2=1)        , self.InitializeB(From_7T=True)        ,  self.Transfer_LearningC()          , '_CSFn2_Init_Main'),
                15: (12  ,   self.ReadTrainC(Main=1,ET=1)         , self.InitializeB(From_3T=True)   ,  self.Transfer_LearningC()          , '_Main_Ps_ET_Init_3T' ),
                }
            return switcher.get(TypeExperiment , 'wrong Index')

    a,b,c,d,e = TypeExperimentFuncs().main(TypeExperiment=UserInfoB['TypeExperiment'], perm_Index=UserInfoB['permutation_Index'])
    b.ReadAugments.Mode = True
    
    UserInfoB['SubExperiment'].Index = a
    UserInfoB['ReadTrain']           = b
    UserInfoB['Transfer_Learning']   = d
    UserInfoB['InitializeB']         = c
    UserInfoB['SubExperiment'].Tag   = e + UserInfoB['tag_temp']  

    return UserInfoB

def Run(UserInfoB, terminal=False):
        
    if terminal: UserInfoB = smallFuncs.terminalEntries(UserInfoB)

    UserInfoB = temp_Experiments_preSet_V2(UserInfoB)

    class params:
        WhichExperiment = func_WhichExperiment(UserInfoB)
        preprocess      = func_preprocess(UserInfoB)
        Augment         = func_Augment(UserInfoB) 
        directories     = smallFuncs.search_ExperimentDirectory(WhichExperiment)
        UserInfo        = UserInfoB

    return params

def func_Exp_subExp_Names(UserInfo):

    def func_subExperiment():
        
        FM = '_FM' + str(UserInfo['simulation'].FirstLayer_FeatureMap_Num)
        DO = UserInfo['DropoutValue']
        SE = UserInfo['SubExperiment']
        NL = '_NL' + str(UserInfo['simulation'].num_Layers)
        ACH =  '_' + 'Res_Unet2'
        US = '_US' + str(UserInfo['upsample'].Scale)
        _, a = LossFunction.LossInfo(UserInfo['lossFunction_Index'])
        LF = '_' + a
        SC = '_SingleClass' if not UserInfo['simulation'].Multi_Class_Mode else ''
        LR = '_wLRScheduler' if UserInfo['simulation'].LR_Scheduler else ''
        lrate = '_lr' + str(UserInfo['simulation'].Learning_Rate) if UserInfo['wmn_csfn'] == 'csfn' else ''


        method = UserInfo['Model_Method']                                                                      
        PI = '' # '_permute' + str(UserInfo['permutation_Index'])

        class subExperiment:
            def __init__(self, tag):                
                self.index = SE.Index
                self.tag = tag
                self.name_thalamus = ''            
                self.name = 'sE' + str(SE.Index) +  '_' + self.tag            
                self.name_Init_from_3T    = 'sE8_'  + method + FM + ACH + NL + '_LS_MyLogDice' + US + SC
                self.name_Init_from_7T    = 'sE12_' + method + FM + ACH + NL + LF + US + SC + '_wLRScheduler_Main_Ps_ET_Init_3T_CV_a' 
                self.name_Init_from_CSFn1 = 'sE9_'  + method + FM + ACH + NL + LF + US + SC + '_CSFn1_Init_Main_CV_a'  
                self.name_Thalmus_network = 'sE8_Predictions_Full_THALAMUS' # sE8_FM20_U-Net4_1-THALMAUS 
                self.crossVal = UserInfo['CrossVal']
       
        tag = method + FM + ACH + NL + LF + US + SC + LR + PI + lrate + SE.Tag
        
        if UserInfo['wmn_csfn'] == 'csfn':
            tag += '_WITH_NEW_CASES'
            tag += '_wBiasCorrection'       
        
        if UserInfo['CrossVal'].Mode: tag += '_CV_' + UserInfo['CrossVal'].index[0] # + '_for_paper' # '_for_percision_recall_curve'
        A = subExperiment(tag)

        if UserInfo['best_network_MPlanar']:

            aa = A.name.split('_FM')
            A.name = aa[0] + '_FM00' + aa[1][2:]



        return A

    def func_Experiment():
        EX = UserInfo['Experiments']
        class Experiment:
            index = EX.Index
            tag   = EX.Tag
            name  = 'exp' + str(EX.Index) + '_' + EX.Tag if EX.Tag else 'exp' + str(EX.Index)
            address = smallFuncs.mkDir(UserInfo['Experiments_Address'] + '/' + name)
            PreSet_Experiment_Info_Index = UserInfo['TypeExperiment']
        return Experiment()

    return func_Experiment(), func_subExperiment()  

def func_WhichExperiment(UserInfo):
    
    def WhichExperiment_Class():

        def HardParamsFuncs():
            def ArchtiectureParams():
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
                    Kernel_size = kernel_size()
                    padding = 'SAME' # valid

                class multiclass:
                    num_classes = ''
                    Mode = False

                class maxPooling:
                    strides = (2,2)
                    pool_size = (2,2)

                class method:
                    Type = ''
                    ReferenceMask = ''
                    havingBackGround_AsExtraDimension = True
                    InputImage2Dvs3D = 2
                    save_Best_Epoch_Model = False
                    Use_Coronal_Thalamus_InSagittal = False
                    Use_TestCases_For_Validation = False
                    ImClosePrediction = False

                return dropout, activation, convLayer, multiclass, maxPooling, method

            dropout, activation, convLayer, multiclass, maxPooling, method = ArchtiectureParams()

            class transfer_Learning:
                Mode = False
                Stage = 0 # 1
                FrozenLayers = [0]
                Tag = '_TF'
            
            class classWeight:
                Weight = {0:1 , 1:1}
                Mode = False


            class layer_Params:
                FirstLayer_FeatureMap_Num = 64
                batchNormalization = True
                ConvLayer = convLayer()
                MaxPooling = maxPooling()
                Dropout = dropout()
                Activitation = activation()
                class_weight = classWeight()

            class InitializeB:
                FromThalamus   = False
                FromOlderModel = False
                From_3T        = False  
                From_7T = False  

            class dataGenerator:
                mode = False
                NumSubjects_Per_batch = 5

            class upsample:
                Mode = False
                Scale = 2
            class model:
                architectureType = 'U-Net'
                epochs = ''
                batch_size = ''
                loss = ''
                metrics = ''
                optimizer = ''  # adamax Nadam Adadelta Adagrad  optimizers.adam(lr=0.001, beta_1=0.9, beta_2=0.999, epsilon=None, decay=0.0, amsgrad=False)
                
                verbose = 2
                num_Layers = ''
                InputDimensions = ''
                Layer_Params = layer_Params()
                showHistory = True
                LabelMaxValue = 1                
                Measure_Dice_on_Train_Data = False
                MultiClass = multiclass()
                Initialize = InitializeB()
                Method = method()
                paddingErrorPatience = 200
                Transfer_Learning = transfer_Learning()
                DataGenerator = dataGenerator()
                Upsample = upsample()
                
                

            lossFunction_Index = 1
            model.loss, _ = LossFunction.LossInfo(lossFunction_Index)

            class machine:
                WhichMachine = 'server'
                GPU_Index = ''

            class image:
                # SlicingDirection = 'axial'.lower()
                SaveMode = 'nifti'.lower()

            class template:
                Image = ''
                Mask  = ''

            class hardParams:
                Model    = model
                Template = template()
                Machine  = machine()
                Image    = image()

            return hardParams

        hardParams = HardParamsFuncs()

        class experiment:
            index = ''
            tag = ''
            name = ''
            address = ''
        
        class CrossVal:
            Mode = False
            index = ['a']
            # All_Indexes = ['a' , 'b']
        class subExperiment:
            index = ''
            tag = ''
            name = ''
            name_thalamus = ''
            crossVal = CrossVal()
            name_Init_from_7T = ''
            name_Init_from_3T = ''

        def datasetFunc():
            class validation:
                percentage = 0.1
                fromKeras = False

            class testDs:
                mode = 'percentage' # 'names'
                percentage = 0.3
                subjects = ''

            if 'names' in testDs.mode:
                testDs.subjects = list([''])

            class slicingDirection:
                slicingOrder = [0,1,2]
                slicingOrder_Reverse = [0,1,2]
                slicingDim = 2

            class inputPadding:
                Automatic = True
                HardDimensions = ''

            class hDF5:
                mode = False
                mode_saveTrue_LoadFalse = True

            class readAugmentFn:
                Mode = False
                Tag = ''
                LoadAll = False

            class readTrain:
                Main  = True
                ET    = True
                SRI   = True
                CSFn1 = False
                CSFn2 = False
                ReadAugments = readAugmentFn()

            class dataset:
                name = ''
                address = ''
                Validation = validation()
                Test = testDs()
                check_vimp_SubjectName = True
                randomFlag = True
                slicingInfo = slicingDirection()
                gapDilation = 5
                gapOnSlicingDimention = 2
                InputPadding = inputPadding()
                ReadTrain = readTrain()
                HDf5 = hDF5()

            # Dataset_Index = 4
            # dataset.name, dataset.address = datasets.DatasetsInfo(Dataset_Index)
            return dataset

        dataset = datasetFunc()

        class nucleus:
            Organ = 'THALAMUS'
            name = ''
            name_Thalamus = ''
            FullIndexes = ''
            Index = ''

        class WhichExperiment:
            Experiment    = experiment()
            SubExperiment = subExperiment()
            address = ''
            Nucleus = nucleus()
            HardParams = hardParams()
            Dataset = dataset()

        return WhichExperiment()
    WhichExperiment = WhichExperiment_Class()

    def func_Nucleus(MultiClassMode):
        def Experiment_Nucleus_Name_MClass(NucleusIndex, MultiClassMode):
            if len(NucleusIndex) == 1 or not MultiClassMode:
                NucleusName , _, _ = smallFuncs.NucleiSelection( NucleusIndex[0] )
            else:
                if (UserInfo['Model_Method'] == 'HCascade') and (1.1 in UserInfo['simulation'].nucleus_Index):
                    NucleusName = 'MultiClass_HCascade_Groups'
                else:
                    NucleusName = ('MultiClass_' + str(NucleusIndex)).replace(', ','').replace('[','').replace(']','')
                
                    

            return NucleusName

        nucleus_Index = UserInfo['simulation'].nucleus_Index if isinstance(UserInfo['simulation'].nucleus_Index,list) else [UserInfo['simulation'].nucleus_Index]
        class nucleus:
            Organ = 'THALAMUS'
            name = Experiment_Nucleus_Name_MClass(nucleus_Index , MultiClassMode )
            name_Thalamus, FullIndexes, _ = smallFuncs.NucleiSelection( 1 )
            Index = nucleus_Index

        return nucleus

    def func_Dataset():

        def Augment_Tag():
            readAugmentTag = ''
            if UserInfo['Augment_Rotation'].Mode: 
                readAugmentTag = 'wRot'   + str(UserInfo['Augment_Rotation'].AngleMax) + 'd'
            elif UserInfo['Augment_Shear'].Mode:  
                readAugmentTag = 'wShear' + str(UserInfo['Augment_Shear'].ShearMax)
            return readAugmentTag
                
        Dataset = WhichExperiment.Dataset
        def slicingInfoFunc():
            class slicingInfo:
                slicingOrder = ''
                slicingOrder_Reverse = ''
                slicingDim = UserInfo['simulation'].slicingDim[0]

            if slicingInfo.slicingDim == 0:
                slicingInfo.slicingOrder         = [1,2,0]
                slicingInfo.slicingOrder_Reverse = [2,0,1]
            elif slicingInfo.slicingDim == 1:
                slicingInfo.slicingOrder         = [2,0,1]
                slicingInfo.slicingOrder_Reverse = [1,2,0]
            else:
                slicingInfo.slicingOrder         = [0,1,2]
                slicingInfo.slicingOrder_Reverse = [0,1,2]

            return slicingInfo

        Dataset.ReadTrain = UserInfo['ReadTrain']
        Dataset.ReadTrain.ReadAugments.Tag = Augment_Tag()

        Dataset.slicingInfo = slicingInfoFunc()

        Dataset.InputPadding.Automatic = UserInfo['InputPadding'].Automatic
        Dataset.InputPadding.HardDimensions = list( np.array(UserInfo['InputPadding'].HardDimensions)[ Dataset.slicingInfo.slicingOrder ] )


        return Dataset

    def func_ModelParams():

        HardParams = WhichExperiment.HardParams
        def ReferenceForCascadeMethod(ModelIdea):

            _ , fullIndexes, _ = smallFuncs.NucleiSelection(ind=1)
            referenceLabel = {}

            if ModelIdea == 'HCascade':

                Name, Indexes = {}, {}
                for i in [1.1, 1.2, 1.3, 1.4]:
                    Name[i], Indexes[i], _ = smallFuncs.NucleiSelection(ind=i)

                for ixf in tuple(fullIndexes) + tuple([1.1, 1.2, 1.3, 1.4]):

                    if ixf in Indexes[1.1]: referenceLabel[ixf] = Name[1.1]
                    elif ixf in Indexes[1.2]: referenceLabel[ixf] = Name[1.2]
                    elif ixf in Indexes[1.3]: referenceLabel[ixf] = Name[1.3]
                    elif ixf in Indexes[1.4]: referenceLabel[ixf] = Name[1.4]
                    elif ixf == 1: referenceLabel[ixf] = 'None'
                    else: referenceLabel[ixf] = '1-THALAMUS'


            elif ModelIdea == 'Cascade':
                for ix in fullIndexes: referenceLabel[ix] = '1-THALAMUS' if ix != 1 else 'None'

            else:
                for ix in fullIndexes: referenceLabel[ix] = 'None'

            return referenceLabel

        def func_NumClasses():

            num_classes = len(UserInfo['simulation'].nucleus_Index) if HardParams.Model.MultiClass.Mode else 1
            num_classes += 1
                
            return num_classes


        def fixing_NetworkParams_BasedOn_InputDim(dim):
            class kernel_size: 
                conv          = tuple([3]*dim)
                convTranspose = tuple([2]*dim)
                output        = tuple([1]*dim)

            class maxPooling: 
                strides   = tuple([2]*dim)
                pool_size = tuple([2]*dim)


            return kernel_size, maxPooling

        def func_Layer_Params(UserInfo):

            Layer_Params = HardParams.Model.Layer_Params
            
            kernel_size, maxPooling = fixing_NetworkParams_BasedOn_InputDim(2)

            Layer_Params.FirstLayer_FeatureMap_Num = UserInfo['simulation'].FirstLayer_FeatureMap_Num
            Layer_Params.ConvLayer.Kernel_size = kernel_size()
            Layer_Params.MaxPooling = maxPooling()
            Layer_Params.Dropout.Value     = UserInfo['DropoutValue']
            Layer_Params.class_weight.Mode = UserInfo['simulation'].Weighted_Class_Mode

            return Layer_Params

        HardParams.Template = UserInfo['Template']
        HardParams.Machine.GPU_Index = str(UserInfo['simulation'].GPU_Index)

     
        HardParams.Model.metrics, _    = Metrics.MetricInfo(3)
        HardParams.Model.optimizer, _  = Optimizers.OptimizerInfo(1, UserInfo['simulation'].Learning_Rate)
        HardParams.Model.num_Layers    = UserInfo['simulation'].num_Layers
        HardParams.Model.batch_size    = UserInfo['simulation'].batch_size
        HardParams.Model.epochs        = UserInfo['simulation'].epochs
        HardParams.Model.DataGenerator = UserInfo['dataGenerator']                
        HardParams.Model.Initialize    = UserInfo['InitializeB']
        HardParams.Model.architectureType = 'Res_Unet2'
        HardParams.Model.Upsample      = UserInfo['upsample']


        HardParams.Model.loss, _ = LossFunction.LossInfo(UserInfo['lossFunction_Index'] ) 

        HardParams.Model.Method.Type                  = UserInfo['Model_Method']
        HardParams.Model.Method.save_Best_Epoch_Model = UserInfo['simulation'].save_Best_Epoch_Model   

        HardParams.Model.Method.Use_Coronal_Thalamus_InSagittal   = UserInfo['simulation'].Use_Coronal_Thalamus_InSagittal
        HardParams.Model.Method.Use_TestCases_For_Validation      = UserInfo['simulation'].Use_TestCases_For_Validation
        HardParams.Model.Method.ImClosePrediction                 = UserInfo['simulation'].ImClosePrediction

        HardParams.Model.MultiClass.Mode = UserInfo['simulation'].Multi_Class_Mode
        HardParams.Model.MultiClass.num_classes = func_NumClasses()
        HardParams.Model.Layer_Params = func_Layer_Params(UserInfo)

        if UserInfo['simulation'].nucleus_Index == 'all': 
            _, nucleus_Index,_ = smallFuncs.NucleiSelection(ind = 1)
        else:
            nucleus_Index = UserInfo['simulation'].nucleus_Index if isinstance(UserInfo['simulation'].nucleus_Index,list) else [UserInfo['simulation'].nucleus_Index]

        # AAA = ReferenceForCascadeMethod(HardParams.Model.Method.Type)
        # HardParams.Model.Method.ReferenceMask = AAA[nucleus_Index[0]]

        HardParams.Model.Method.ReferenceMask = ReferenceForCascadeMethod(HardParams.Model.Method.Type)[nucleus_Index[0]]
        HardParams.Model.Transfer_Learning = UserInfo['Transfer_Learning']

        return HardParams

    def ReadInputDimensions_NLayers(TrainModel_Address):
        with open(TrainModel_Address + '/UserInfo.json','rb') as f:   
            UserInfo_Load = json.load(f)            
        return UserInfo_Load['InputPadding_Dims'], UserInfo_Load['num_Layers']
        
    experiment, subExperiment = func_Exp_subExp_Names(UserInfo)  

    WhichExperiment.Experiment    = experiment
    WhichExperiment.SubExperiment = subExperiment
    WhichExperiment.address       = UserInfo['Experiments_Address']         
    WhichExperiment.HardParams    = func_ModelParams()
    WhichExperiment.Nucleus       = func_Nucleus(WhichExperiment.HardParams.Model.MultiClass.Mode)
    WhichExperiment.Dataset       = func_Dataset()
    WhichExperiment.TestOnly = UserInfo['simulation'].TestOnly
    WhichExperiment.HardParams.Model.TestOnly = UserInfo['simulation'].TestOnly

    def old_adding_TransferLearningParams(WhichExperiment):
        class best_WMn_Model:

            architectureType = 'Res_Unet2'
            EXP_address = '/array/ssd/msmajdi/experiments/keras/exp6/models/'

            Model_Method = WhichExperiment.HardParams.Model.Method.Type
            sdTag = WhichExperiment.Dataset.slicingInfo.slicingDim
            
            if Model_Method == 'Cascade':
                if sdTag == 0:   FM , NL = 10, 3
                elif sdTag == 1: FM , NL = 20, 3
                elif sdTag == 2: FM , NL = 20, 3

            elif Model_Method == 'HCascade':
                if sdTag == 0:   FM , NL = 30, 3
                elif sdTag == 1: FM , NL = 40, 3
                elif sdTag == 2: FM , NL = 40, 3
            else:
                 FM , NL = 20, 3

                    
            sdTag   = '/sd' + str(WhichExperiment.Dataset.slicingInfo.slicingDim)        
            Tag     = 'sE12_' + Model_Method + '_FM' + str(FM) + '_' + architectureType + '_NL' + str(NL) + '_LS_MyBCE_US1_Main_Init_3T_CV_a/'
            address = EXP_address + Tag  + WhichExperiment.Nucleus.name + sdTag + '/model.h5'
        return best_WMn_Model()

    def adding_TransferLearningParams(WhichExperiment):

        def params_bestUnet(Model_Method, sdTag):
            if Model_Method == 'Cascade':
                if sdTag == 0:   FM , NL = 10, 3
                elif sdTag == 1: FM , NL = 20, 3
                elif sdTag == 2: FM , NL = 20, 3

            else:
                FM , NL = 20, 3

            return FM , NL , 'U-Net4'

        def params_bestResUnet2(Model_Method, sdTag):
            if Model_Method == 'Cascade':
                if sdTag == 0:   FM , NL = 40, 3
                elif sdTag == 1: FM , NL = 30, 3
                elif sdTag == 2: FM , NL = 20, 3
            else:
                FM , NL = 20, 3
 
            return FM , NL, 'Res_Unet2'
        
        class best_WMn_Model:
            def __init__(self, WhichExperiment):
                
                SD = WhichExperiment.Dataset.slicingInfo.slicingDim

                LossFunction = 'MyLogDice' # 'MyJoint'
                EXP_address = '/array/ssd/msmajdi/experiments/keras/exp6/models/'
                Model_Method = WhichExperiment.HardParams.Model.Method.Type
                                
                self.FM , self.NL, architectureType = params_bestResUnet2(Model_Method, SD)                    
                Tag     = 'sE12_' + Model_Method + '_FM' + str(self.FM) + '_' + architectureType + '_NL' + str(self.NL) + '_LS_' + LossFunction + '_US1_wLRScheduler_Main_Ps_ET_Init_3T_CV_a/'

                self.address = EXP_address + Tag  + WhichExperiment.Nucleus.name + '/sd' + str(SD) + '/model.h5'

        return best_WMn_Model(WhichExperiment)

        
    WhichExperiment.HardParams.Model.Best_WMn_Model = adding_TransferLearningParams(WhichExperiment)
    

    dir_input_dimension = experiment.address + '/models/' + subExperiment.name + '/' + WhichExperiment.Nucleus.name + '/sd' + str(WhichExperiment.Dataset.slicingInfo.slicingDim)
    if UserInfo['use_train_padding_size']  and UserInfo['simulation'].TestOnly and os.path.isfile(dir_input_dimension + '/UserInfo.json'): 
        InputDimensions, num_Layers = ReadInputDimensions_NLayers(dir_input_dimension)

        WhichExperiment.Dataset.InputPadding.Automatic = False

        # InputDimensions = list( np.array(InputDimensions)[ WhichExperiment.Dataset.slicingInfo.slicingOrder ] )
        WhichExperiment.Dataset.InputPadding.HardDimensions = InputDimensions        
        WhichExperiment.HardParams.Model.InputDimensions = InputDimensions
        WhichExperiment.HardParams.Model.num_Layers = num_Layers

    return WhichExperiment
    
def func_preprocess(UserInfo):

    def preprocess_Class():

        class normalize:
            Mode = True
            Method = 'MinMax'
            per_Subject = True
            per_Dataset = False


        class cropping:
            Mode = True
            Method = 'python'

        class biasCorrection:
            Mode = ''

        class reslicing:
            Mode = ''

        # TODO fix the justfornow
        class debug:
            doDebug = True
            PProcessExist = False  # rename it to preprocess exist
            justForNow = True # it checks the intermediate steps and if it existed don't reproduce it

        class preprocess:
            Mode = ''
            TestOnly = ''
            Debug = debug()
            # Augment = augment()
            Cropping = cropping()
            Reslicing = reslicing()
            Normalize = normalize()
            BiasCorrection = biasCorrection()

        return preprocess()
    preprocess = preprocess_Class()

    preprocess.Mode                = UserInfo['preprocess'].Mode
    preprocess.BiasCorrection.Mode = UserInfo['preprocess'].BiasCorrection
    preprocess.Cropping.Mode       = UserInfo['preprocess'].Cropping
    preprocess.Reslicing.Mode      = UserInfo['preprocess'].Reslicing    
    preprocess.Normalize           = UserInfo['normalize']
    preprocess.TestOnly            = UserInfo['simulation'].TestOnly
    return preprocess

def func_Augment(UserInfo):

    def Augment_Class():
        class rotation:
            Mode = False
            AngleMax = 6

        class shift:
            Mode = False
            ShiftMax = 10

        class shear:
            Mode = False
            ShearMax = 0

        class linearAug:
            Mode = True
            Length = 8
            Rotation = rotation()
            Shift = shift()
            Shear = shear()

        class nonlinearAug:
            Mode = False
            Length = 2
        class augment:
            Mode = False
            Linear = linearAug()
            NonLinear = nonlinearAug()

        return augment()
    Augment = Augment_Class()

    Augment.Mode            = UserInfo['AugmentMode']
    Augment.Linear.Rotation = UserInfo['Augment_Rotation']
    Augment.Linear.Shear    = UserInfo['Augment_Shear']
    Augment.Linear.Length   = UserInfo['Augment_Linear_Length']
    Augment.NonLinear.Mode  = UserInfo['Augment_NonLinearMode']
    return Augment
    


