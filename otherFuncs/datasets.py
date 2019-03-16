import numpy as np
from imageio import imread
from random import shuffle
from tqdm import tqdm, trange
import nibabel as nib
import shutil
import os, sys
import otherFuncs.smallFuncs as smallFuncs
import preprocess.normalizeA as normalizeA
import preprocess.applyPreprocess as applyPreprocess
import matplotlib.pyplot as plt
from scipy import ndimage
from shutil import copyfile
import h5py

class ImageLabel:
    Image = np.zeros(3)
    Mask = ''

class info:
    Height = ''
    Width = ''

class data:
    Train = ImageLabel()
    Train_ForTest = ""
    Test = ""
    Validation = ImageLabel()
    Info = info()

class trainCase:
    def __init__(self, Image, Mask):
        self.Image = Image
        self.Mask  = Mask

class testCase:
    def __init__(self, Image, Mask, OrigMask, Affine, Header, original_Shape):
        self.Image = Image
        self.Mask = Mask
        self.OrigMask  = OrigMask
        self.Affine = Affine
        self.Header = Header
        self.original_Shape = original_Shape

def DatasetsInfo(DatasetIx):
    switcher = {
        1: ('SRI_3T', '/array/ssd/msmajdi/data/preProcessed/3T/SRI_3T'),
        2: ('SRI_ReSliced', '/array/ssd/msmajdi/data/preProcessed/3T/SRI_ReSliced'),
        3: ('croppingData', '/array/ssd/msmajdi/data/preProcessed/croppingData'),
        4: ('All_7T', '/array/ssd/msmajdi/data/preProcessed/7T/All_DBD'),
        5: ('20priors', '/array/ssd/msmajdi/data/preProcessed/7T/20priors'),
    }
    return switcher.get(DatasetIx, 'WARNING: Invalid dataset index')

def loadDataset(params):

    if 'fashionMnist' in params.WhichExperiment.Dataset.name:
        Data, _ = fashionMnist(params)
    elif 'kaggleCompetition' in params.WhichExperiment.Dataset.name:
        Data, _ = kaggleCompetition(params)
    else:
        Data, params = readingFromExperiments(params)

    return Data, params

def fashionMnist(params):

    def one_hot(a, num_classes):
        return np.eye(num_classes)[a]

    from keras.datasets import fashion_mnist

    fullData  = fashion_mnist.load_data()

    images = (np.expand_dims(fullData[0][0],axis=3)).astype('float32') / 255
    masks  = one_hot(fullData[0][1],10)

    if params.WhichExperiment.Dataset.Validation.fromKeras:
        data.Train.Image = images
        data.Train.Mask = masks
    else:
        data.Train, data.Validation = TrainValSeperate(params.WhichExperiment.Dataset.Validation.percentage, images, masks, params.WhichExperiment.Dataset.randomFlag)

    data.Test.Image = (np.expand_dims(fullData[1][0],axis=3)).astype('float32') / 255
    data.Test.Label = one_hot(fullData[1][1],10)
    return data, '_'

def kaggleCompetition(params):

    subF = next(os.walk(params.WhichExperiment.Dataset.address))

    for ind in trange(min(len(subF[1]),50), desc='Loading Dataset'):

        imDir = subF[0] + '/' + subF[1][ind] + '/images'
        imMsk = subF[0] + '/' + subF[1][ind] + '/masks'
        a = next(os.walk(imMsk))
        b = next(os.walk(imDir))

        im = np.squeeze(imread(imDir + '/' + b[2][0])[:256,:256,0])
        # im = ndimage.zoom(im,(1,1,2),order=3)

        im = np.expand_dims(im,axis=0)
        im = (np.expand_dims(im,axis=3)).astype('float32') / 255
        images = im if ind == 0 else np.concatenate((images,im),axis=0)

        msk = imread(imMsk + '/' + a[2][0]) if len(a[2]) > 0 else np.zeros(im.shape)
        if len(a[2]) > 1:
            for sF in range(1,len(a[2])):
                msk = msk + imread(imMsk + '/' + a[2][sF])

        msk = np.expand_dims(msk[:256,:256],axis=0)
        msk = (np.expand_dims(msk,axis=3)).astype('float32') / 255
        masks = msk>0.5 if ind == 0 else np.concatenate((masks,msk>0.5 ),axis=0)

    masks = np.concatenate((masks,1-masks),axis=3)

    if params.WhichExperiment.Dataset.Validation.fromKeras:
        data.Train.Image = images
        data.Train.Mask = masks
    else:
        data.Train, data.Validation = TrainValSeperate(params.WhichExperiment.Dataset.Validation.percentage ,images, masks, params.WhichExperiment.Dataset.randomFlag)

    data.Test = data.Train
    return data, '_'

def paddingNegativeFix(sz, Padding):
    padding = np.array([list(x) for x in Padding])
    crd = -1*padding
    padding[padding < 0] = 0
    crd[crd < 0] = 0
    Padding = tuple([tuple(x) for x in padding])

    # sz = im.shape
    # crd = crd[:3,:]
    for ix in range(3): crd[ix,1] = sz[ix] if crd[ix,1] == 0 else -crd[ix,1]

    return padding, crd

# def fix25D_sd0(Image):
#     return Image[:int(Image.shape[2]/2+5) , : , :]

def readingWithTranpose(Dirr , params):
    ImageF = nib.load( Dirr)
    Image = ImageF.get_data()
    # if params.WhichExperiment.Dataset.slicingInfo.slicingDim == 0: Image = fix25D_sd0(Image)
    
    return ImageF, np.transpose(Image, params.WhichExperiment.Dataset.slicingInfo.slicingOrder)

# TODO: add the saving images with the format mahesh said
# TODO: maybe add the ability to crop the test cases with bigger sizes than network input dimention accuired from train datas
def readingFromExperiments(params):

    NameCascadeMask = params.WhichExperiment.HardParams.Model.Method.ReferenceMask

    def inputPreparationForUnet(im,subject2, params):

        def CroppingInput(im, Padding2):
            if np.min(Padding2) < 0:
                Padding2, crd = paddingNegativeFix(im.shape, Padding2)
                im = im[crd[0,0]:crd[0,1] , crd[1,0]:crd[1,1] , crd[2,0]:crd[2,1]]

            return np.pad(im, Padding2[:3], 'constant')

        if 'Cascade' in params.WhichExperiment.HardParams.Model.Method.Type and 1 not in params.WhichExperiment.Nucleus.Index:
            # subject.NewCropInfo.PadSizeBackToOrig
            BB = subject2.NewCropInfo.OriginalBoundingBox
            im = im[BB[0][0]:BB[0][1]  ,  BB[1][0]:BB[1][1]  ,  BB[2][0]:BB[2][1]]

        # aa = subject.address.split('train/') if len(subject2.address.split('train/')) == 2 else subject.address.split('test/')

        im = CroppingInput(im, subject2.Padding)
        # im = np.transpose(im, params.WhichExperiment.Dataset.slicingInfo.slicingOrder)
        im = np.transpose(im,[2,0,1])
        im = np.expand_dims(im ,axis=3).astype('float32')

        return im

    def readingImage(params, subject2, mode):

        # TODO remove this after couple of runs
        # if 'Cascade' in params.WhichExperiment.HardParams.Model.Method.Type and (int(params.WhichExperiment.Nucleus.Index[0]) == 1) and os.path.isfile(subject2.Temp.address + '/' + subject2.ImageProcessed + '_BeforeThalamsMultiply.nii.gz'):
        #     copyfile( subject2.Temp.address + '/' + subject2.ImageProcessed + '_BeforeThalamsMultiply.nii.gz' , subject2.address + '/' + subject2.ImageProcessed + '.nii.gz')

        def apply_Cascade_PreFinalStageMask_OnImage(imm):

            def dilateMask(mask):
                struc = ndimage.generate_binary_structure(3,2)
                struc = ndimage.iterate_structure(struc, params.WhichExperiment.Dataset.gapDilation )
                return ndimage.binary_dilation(mask, structure=struc)

            Dirr = params.directories.Test.Result
            if 'train' in mode: Dirr += '/TrainData_Output'

            _, Cascade_Mask = readingWithTranpose(Dirr + '/' + subject2.subjectName + '/' + NameCascadeMask + '.nii.gz' , params)
            # _, manualLabel = readingWithTranpose(subject2.Label.address + '/' + NameCascadeMask + '_PProcessed.nii.gz' , params)

            Cascade_Mask_Dilated = dilateMask(Cascade_Mask)
            # imm2 = imm.copy() + 400*Cascade_Mask
            imm[Cascade_Mask_Dilated == 0] = 0
            return imm

        imF, im = readingWithTranpose(subject2.address + '/' + subject2.ImageProcessed + '.nii.gz' , params)

        if 'Cascade' in params.WhichExperiment.HardParams.Model.Method.Type and 1 not in params.WhichExperiment.Nucleus.Index:
            im = apply_Cascade_PreFinalStageMask_OnImage( im)

        im = inputPreparationForUnet(im, subject2, params)
        im = normalizeA.main_normalize(params.preprocess.Normalize , im)
        return im, imF

    def readingNuclei(params, subject, imFshape):

        def backgroundDetector(masks):
            a = np.sum(masks,axis=3)
            background = np.zeros(masks.shape[:3])
            background[np.where(a == 0)] = 1
            background = np.expand_dims(background,axis=3)
            return background

        def readingOriginalMask(NucInd):
            nameNuclei, _,_ = smallFuncs.NucleiSelection(NucInd)
            inputMsk = subject.Label.address + '/' + nameNuclei + '_PProcessed.nii.gz'

            origMsk1N = nib.load(inputMsk).get_data() if os.path.exists(inputMsk) else np.zeros(imFshape)
            origMsk1N = smallFuncs.fixMaskMinMax(origMsk1N)

            

            return np.expand_dims(origMsk1N ,axis=3)

        for cnt, NucInd in enumerate(params.WhichExperiment.Nucleus.Index):

            origMsk1N = readingOriginalMask(NucInd)


            msk1N = np.transpose( np.squeeze(origMsk1N) , params.WhichExperiment.Dataset.slicingInfo.slicingOrder)
            msk1N = inputPreparationForUnet(msk1N, subject, params)

            origMsk = origMsk1N if cnt == 0 else np.concatenate((origMsk, origMsk1N) ,axis=3).astype('float32')
            msk = msk1N if cnt == 0 else np.concatenate((msk,msk1N),axis=3).astype('float32')

        if params.WhichExperiment.HardParams.Model.Method.havingBackGround_AsExtraDimension:
            background = backgroundDetector(msk)
            msk = np.concatenate((msk, background),axis=3).astype('float32')

        return origMsk , msk

    def Error_MisMatch_In_Dim_ImageMask(subject, mode, nameSubject):
        AA = subject.address.split(os.path.dirname(subject.address) + '/')
        shutil.move(subject.address, os.path.dirname(subject.address) + '/' + 'ERROR_' + AA[1])
        print('WARNING:', mode , nameSubject, ' image and mask have different shape sizes')

    def preAnalysis(params):

        def find_PaddingValues(params):

            def findingSubjectsFinalPaddingAmount(wFolder, Input, params):

                def findingPaddedInputSize(params):
                    new_inputSize = np.max(Input.inputSizes, axis=0)
                    # new_inputSize = MaxInputSize

                    a = 2**(params.WhichExperiment.HardParams.Model.num_Layers - 1)
                    for dim in range(3):
                        if new_inputSize[dim] % a != 0: new_inputSize[dim] = a * np.ceil(new_inputSize[dim] / a)

                    return new_inputSize

                def applyingPaddingDimOnSubjects(params, Subjects):
                    fullpadding = params.WhichExperiment.HardParams.Model.InputDimensions - Input.inputSizes
                    md = np.mod(fullpadding,2)
                    for sn, name in enumerate(list(Subjects)):
                        padding = [tuple([0,0])]*4
                        for dim in range(2): # params.WhichExperiment.Dataset.slicingInfo.slicingOrder[:2]:
                            if md[sn, dim] == 0:
                                padding[dim] = tuple([int(fullpadding[sn,dim]/2)]*2)
                            else:
                                padding[dim] = tuple([int(np.floor(fullpadding[sn,dim]/2) + 1) , int(np.floor(fullpadding[sn,dim]/2))])

                        Subjects[name].Padding = tuple(padding)

                    return Subjects

                # TODO check ehjy this works for test only cases even though i am not feeding teh dimension for padding; check where im adding dimension to the params

                if 'Train' in wFolder:
                    if params.WhichExperiment.Dataset.InputPadding.Automatic:
                        params.WhichExperiment.HardParams.Model.InputDimensions = findingPaddedInputSize( params )
                    else:
                        params.WhichExperiment.HardParams.Model.InputDimensions = params.WhichExperiment.Dataset.InputPadding.HardDimensions


                #! finding the amount of padding for each subject in each direction
                Input.Subjects = applyingPaddingDimOnSubjects(params, Input.Subjects)

                return Input

            if params.directories.Train.Input.Subjects: params.directories.Train.Input = findingSubjectsFinalPaddingAmount('Train', params.directories.Train.Input, params)
            if params.directories.Test.Input.Subjects:  params.directories.Test.Input  = findingSubjectsFinalPaddingAmount('Test', params.directories.Test.Input, params)

            return params

        def find_AllInputSizes(params):

            def newCropedSize(subject, params, mode):

                def readingCascadeCropSizes(subject):
                    dirr = params.directories.Test.Result
                    if 'train' in mode: dirr += '/TrainData_Output'

                    BBf = np.loadtxt(dirr + '/' + subject.subjectName  + '/BB_' + NameCascadeMask + '.txt',dtype=int)
                    BB = BBf[:,:2]
                    BBd = BBf[:,2:]

                    #! because on the slicing direction we don't want the extra dilated effect to be considered
                    BBd[params.WhichExperiment.Dataset.slicingInfo.slicingDim] = BB[params.WhichExperiment.Dataset.slicingInfo.slicingDim]
                    BBd = BBd[params.WhichExperiment.Dataset.slicingInfo.slicingOrder]
                    return BBd

                if 'Cascade' in params.WhichExperiment.HardParams.Model.Method.Type and 1 not in params.WhichExperiment.Nucleus.Index:
                    BB = readingCascadeCropSizes(subject)

                    origSize = np.array( nib.load(subject.address + '/' + subject.ImageProcessed + '.nii.gz').shape )
                    origSize = origSize[params.WhichExperiment.Dataset.slicingInfo.slicingOrder]


                    subject.NewCropInfo.OriginalBoundingBox = BB
                    subject.NewCropInfo.PadSizeBackToOrig   = tuple([ tuple([BB[d][0] , origSize[d]-BB[d][1]]) for d in range(3) ])

                    Shape = np.array([BB[d][1]-BB[d][0] for d  in range(3)])
                else:
                    Shape = np.array( nib.load(subject.address + '/' + subject.ImageProcessed + '.nii.gz').shape )
                    Shape = Shape[params.WhichExperiment.Dataset.slicingInfo.slicingOrder]

                # Shape = tuple(Shape[params.WhichExperiment.Dataset.slicingInfo.slicingOrder])
                return Shape, subject

            def loopOverAllSubjects(Input, mode):
                inputSize = []
                for sj in Input.Subjects:
                    Shape, Input.Subjects[sj] = newCropedSize(Input.Subjects[sj], params, mode)
                    inputSize.append(Shape)

                Input.inputSizes = np.array(inputSize)
                return Input

            if params.directories.Train.Input.Subjects: params.directories.Train.Input = loopOverAllSubjects(params.directories.Train.Input, 'train')
            if params.directories.Test.Input.Subjects: params.directories.Test.Input  = loopOverAllSubjects(params.directories.Test.Input, 'test')

            return params

        def find_correctNumLayers(params):

            HardParams = params.WhichExperiment.HardParams

            if params.WhichExperiment.Dataset.InputPadding.Automatic and params.WhichExperiment.Dataset.HDf5.mode_saveTrue_LoadFalse:
                MinInputSize = np.min(params.directories.Train.Input.inputSizes, axis=0)
            else:
                MinInputSize = params.WhichExperiment.Dataset.InputPadding.HardDimensions

            kernel_size = HardParams.Model.ConvLayer.Kernel_size.conv
            num_Layers  = HardParams.Model.num_Layers

            if np.min(MinInputSize[:2] - np.multiply( kernel_size,(2**(num_Layers - 1)))) < 0:  # ! check if the figure map size at the most bottom layer is bigger than convolution kernel size
                print('WARNING: INPUT IMAGE SIZE IS TOO SMALL FOR THE NUMBER OF LAYERS')
                num_Layers = int(np.floor( np.log2(np.min( np.divide(MinInputSize[:2],kernel_size) )) + 1))
                print('# LAYERS  OLD:',HardParams.Model.num_Layers  ,  ' =>  NEW:',num_Layers)

            params.WhichExperiment.HardParams.Model.num_Layers = num_Layers
            return params

        params = find_AllInputSizes(params)
        params = find_correctNumLayers(params)
        params = find_PaddingValues(params)

        return params

    def main_ReadingDataset(params):

        if params.WhichExperiment.Dataset.HDf5.mode:
            f = h5py.File(params.WhichExperiment.Experiment.address + '/' + params.WhichExperiment.Nucleus.name + '.h5py' , 'w')

        def trainFlag():
            Flag_TestOnly = params.preprocess.TestOnly
            Flag_TrainDice = params.WhichExperiment.HardParams.Model.Measure_Dice_on_Train_Data
            Flag_cascadeMethod = 'Cascade' in params.WhichExperiment.HardParams.Model.Method.Type and int(params.WhichExperiment.Nucleus.Index[0]) == 1
            Flag_notEmpty = params.directories.Train.Input.Subjects
            return ( (not Flag_TestOnly) or Flag_TrainDice or Flag_cascadeMethod ) and Flag_notEmpty

        if trainFlag():
            TrainList, ValList = percentageDivide(params.WhichExperiment.Dataset.Validation.percentage, list(params.directories.Train.Input.Subjects), params.WhichExperiment.Dataset.randomFlag)

        Th = 0.5*params.WhichExperiment.HardParams.Model.LabelMaxValue

        def separateTrainVal_and_concatenateTrain(TrainData):

            def separatingConcatenatingIndexes(sjList):
                for ix, nameSubject in enumerate(sjList):
                    im, msk = TrainData[nameSubject].Image  , TrainData[nameSubject].Mask

                    if params.WhichExperiment.Dataset.slicingInfo.slicingDim == 0: 
                        im = im[:int(im.shape[0]/2+5),...]
                        msk = msk[:int(msk.shape[0]/2+5),...]


                    images = im     if ix == 0 else np.concatenate((images,im    ),axis=0)
                    masks  = msk>Th if ix == 0 else np.concatenate((masks,msk>Th ),axis=0)

                return trainCase(Image=images, Mask=masks.astype('float32'))

            if params.WhichExperiment.Dataset.Validation.fromKeras:
                Train = separatingConcatenatingIndexes(list(TrainData))
                Validation = ''
            else:
                Train = separatingConcatenatingIndexes(TrainList)
                Validation = separatingConcatenatingIndexes(ValList)

            return Train, Validation

        def readingAllSubjects(Subjects, mode):

            def ErrorInPaddingCheck(subject):
                ErrorFlag = False
                if np.min(subject.Padding) < 0:
                    if np.min(subject.Padding) < -params.WhichExperiment.HardParams.Model.paddingErrorPatience:
                        AA = subject.address.split(os.path.dirname(subject.address) + '/')
                        shutil.move(subject.address, os.path.dirname(subject.address) + '/' + 'ERROR_' + AA[1])
                        print('WARNING: subject: ',subject.subjectName,' size is out of the training network input dimensions')
                        ErrorFlag = True
                    else:
                        Dirsave = smallFuncs.mkDir(params.directories.Test.Result + '/' + subject.subjectName,)
                        np.savetxt(Dirsave + '/paddingError.txt', subject.Padding, fmt='%d')
                        print('WARNING: subject: ',subject.subjectName,' padding error patience activated, Error:', np.min(subject.Padding))
                return ErrorFlag

            ListSubjects = list(Subjects)

            Data = {}
            for nameSubject in tqdm(ListSubjects, desc='Loading Dataset: ' + mode):
                
                if ErrorInPaddingCheck(Subjects[nameSubject]): continue

                im, imF = readingImage(params, Subjects[nameSubject], mode)
                origMsk , msk = readingNuclei(params, Subjects[nameSubject], imF.shape)

                if im[...,0].shape == msk[...,0].shape:

                    if params.WhichExperiment.Dataset.HDf5.mode:
                        f["/%s/%s/Image"%(mode,nameSubject)] = im
                        f["/%s/%s/Mask"%(mode,nameSubject)] = msk>Th
                        # f["/%s/%s"%(mode,nameSubject)].attrs["Affine"] = imF.get_affine()
                        # f["/%s/%s"%(mode,nameSubject)].attrs["Header"] = imF.get_header()
                        f["/%s/%s"%(mode,nameSubject)].attrs["original_Shape"] = imF.shape
                        f['/%s/%s'%(mode,nameSubject)].attrs["Padding"] = Subjects[nameSubject].Padding
                        f['/%s/%s'%(mode,nameSubject)].attrs["NewCropInfo/OriginalBoundingBox"] = Subjects[nameSubject].NewCropInfo.OriginalBoundingBox
                        f['/%s/%s'%(mode,nameSubject)].attrs["NewCropInfo/PadSizeBackToOrig"]   = Subjects[nameSubject].NewCropInfo.PadSizeBackToOrig

                    Data[nameSubject] = testCase(Image=im, Mask=msk>Th ,OrigMask=(origMsk>Th).astype('float32'), Affine=imF.get_affine(), Header=imF.get_header(), original_Shape=imF.shape)
                else:
                    Error_MisMatch_In_Dim_ImageMask(Subjects[nameSubject] , mode, nameSubject)

            # if params.WhichExperiment.Dataset.HDf5.mode:  f.close()

            return Data

        DataAll = data()
        if trainFlag():
            DataAll.Train_ForTest = readingAllSubjects(params.directories.Train.Input.Subjects, 'train')
            # if not params.WhichExperiment.Dataset.HDf5.mode:
            DataAll.Train, DataAll.Validation = separateTrainVal_and_concatenateTrain( DataAll.Train_ForTest )

        if params.directories.Test.Input.Subjects: DataAll.Test = readingAllSubjects(params.directories.Test.Input.Subjects, 'test')

        # DataAll.Info.Height, DataAll.Info.Width = params.WhichExperiment.HardParams.Model.InputDimensions[:2]
        # params.WhichExperiment.HardParams.Model.imageInfo = DataAll.Info
        # with h5py.File(params.WhichExperiment.Experiment.address + '/' + params.WhichExperiment.Nucleus.name + '.h5py' , 'w') as f:
        #     f.create_dataset('%s/%s/Image'%(mode_TrainVal,nameSubject)  , data=im)

        return DataAll, params

    params = preAnalysis(params)

    if params.WhichExperiment.Dataset.HDf5.mode_saveTrue_LoadFalse:
        Data, params = main_ReadingDataset(params)
    else:
        print('load HDF5')

    return Data, params

def TrainValSeperate(percentage, images, masks, randomFlag):

    subjectsList = list(range(images.shape[0]))
    TrainList, ValList = percentageDivide(percentage, subjectsList, randomFlag)


    Validation = ImageLabel()
    Validation.Image = images[ValList, ...]
    Validation.Mask = masks[ValList, ...]

    Train = ImageLabel()
    Train.Image = images[TrainList, ...]
    Train.Mask = masks[TrainList, ...]

    return Train, Validation

def percentageDivide(percentage, subjectsList, randomFlag):

    L = len(subjectsList)
    indexes = np.array(range(L))

    if randomFlag: shuffle(indexes)
    per = int( percentage * L )
    if per == 0 and L > 1: per = 1

    # TestValList = subjectsList[indexes[:per]]
    TestValList = [subjectsList[i] for i in indexes[:per]]
    # TrainList = subjectsList[indexes[per:]]
    TrainList = [subjectsList[i] for i in indexes[per:]]

    return TrainList, TestValList

def movingFromDatasetToExperiments(params):

    # def checkAugmentedData(params):
    #     def listAugmentationFolders(mode, params):
    #         Dir_Aug1 = params.WhichExperiment.Dataset.address + '/Augments/' + mode
    #         flag_Aug = os.path.exists(Dir_Aug1)
    #         ListAugments = smallFuncs.listSubFolders(Dir_Aug1, params) if flag_Aug else list('')
    #         return flag_Aug, {'address': Dir_Aug1 , 'list': ListAugments , 'mode':mode}
    #     flagAg, AugDataL = np.zeros(3), list(np.zeros(3))
    #     if params.Augment.Mode:
    #         if params.Augment.Linear.Rotation.Mode:     flagAg[0], AugDataL[0] = listAugmentationFolders('Linear_Rotation', params)
    #         if params.Augment.Linear.Shift.Mode:        flagAg[1], AugDataL[1] = listAugmentationFolders('Linear_Shift', params)
    #         if params.Augment.NonLinear.Mode: flagAg[2], AugDataL[2] = listAugmentationFolders('NonLinear', params)
    #     return flagAg, AugDataL
    # def copyAugmentData(DirOut, AugDataL, subject):
    #     if 'NonLinear' in AugDataL['mode']: AugDataL['list'] = [i for i in AugDataL['list'] if subject in i.split('Ref_')[0]]
    #     for subjectsAgm in AugDataL['list']:
    #         if subject in subjectsAgm: shutil.copytree(AugDataL['address'] + '/' + subjectsAgm  ,  DirOut + '/' + subjectsAgm)

    if len(os.listdir(params.directories.Train.address)) != 0 or len(os.listdir(params.directories.Test.address)) != 0:
        print('*** DATASET ALREADY EXIST; PLEASE REMOVE \'train\' & \'test\' SUBFOLDERS ***')
        sys.exit

    else:
        List = smallFuncs.listSubFolders(params.WhichExperiment.Dataset.address, params)
        # flagAg, AugDataL = checkAugmentedData(params)

        TestParams  = params.WhichExperiment.Dataset.Test
        _, TestList = percentageDivide(TestParams.percentage, List, params.WhichExperiment.Dataset.randomFlag) if 'percentage' in TestParams.mode else TestParams.subjects
        for subject in List:

            DirOut, _ = (params.directories.Test.address , 'test') if subject in TestList else (params.directories.Train.address, 'train')

            if not os.path.exists(DirOut + '/' + subject):
                shutil.copytree(params.WhichExperiment.Dataset.address + '/' + subject  ,  DirOut + '/' + subject)

            # if 'train' in mode:
            #     for AgIx in range(len(AugDataL)):
            #         if flagAg[AgIx]: copyAugmentData(DirOut, AugDataL[AgIx], subject)

        # params = smallFuncs.inputNamesCheck(params, 'experiment')

    return True
