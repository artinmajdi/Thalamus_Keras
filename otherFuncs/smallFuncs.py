import nibabel as nib
import numpy as np
from shutil import copyfile
import matplotlib.pyplot as plt
import os, sys
# sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from skimage import measure
from copy import deepcopy
import json

# TODO: use os.path.dirname & os.path.abspath instead of '/' remover
def NucleiSelection(ind = 1):

    def func_NucleusName(ind):
        if ind in range(20):
            if ind == 1:
                NucleusName = '1-THALAMUS'
            elif ind == 2:
                NucleusName = '2-AV'
            elif ind == 4:
                NucleusName = '4-VA'
            elif ind == 5:
                NucleusName = '5-VLa'
            elif ind == 6:
                NucleusName = '6-VLP'
            elif ind == 7:
                NucleusName = '7-VPL'
            elif ind == 8:
                NucleusName = '8-Pul'
            elif ind == 9:
                NucleusName = '9-LGN'
            elif ind == 10:
                NucleusName = '10-MGN'
            elif ind == 11:
                NucleusName = '11-CM'
            elif ind == 12:
                NucleusName = '12-MD-Pf'
            elif ind == 13:
                NucleusName = '13-Hb'
            elif ind == 14:
                NucleusName = '14-MTT'
        else:
            if ind == 1.1:
                NucleusName = 'lateral_ImClosed'
            elif ind == 1.2:
                NucleusName = 'posterior_ImClosed'
            elif ind == 1.3:
                NucleusName = 'Medial_ImClosed'
            elif ind == 1.4:
                NucleusName = 'Anterior_ImClosed'
            elif ind == 1.9:
                NucleusName = 'HierarchicalCascade'

        return NucleusName

    def func_FullIndexes(ind):
        if ind in range(20):
            return [1,2,4,5,6,7,8,9,10,11,12,13,14]
        elif ind == 1.1:
            return [4,5,6,7]
        elif ind == 1.2:
            return [8,9,10]
        elif ind == 1.3:
            return [11,12,13]
        elif ind == 1.4:
            return [2]
        elif ind == 1.9:
            return [1.1 , 1.2 , 1.3 , 1.4]

    name = func_NucleusName(ind)
    FullIndexes = func_FullIndexes(ind)
    Full_Names = [func_NucleusName(ix) for ix in FullIndexes]

    return name, FullIndexes, Full_Names

# TODO: repalce all NucleiSelection()  with NucleiIndex class
class NucleiIndex:
    def __init__(self, index=1, method=''):
        self.index       = index
        self.method      = method
        self.child       = ()
        self.parent      = None
        self.grandParent = None
        
        def Name_of_Nucleus(self):
            NucleusName = {
                1: '1-THALAMUS',
                2: '2-AV',
                4: '4-VA',
                5: '5-VLa',
                6: '6-VLP',
                7: '7-VPL',
                8: '8-Pul',
                9: '9-LGN',
                10: '10-MGN',
                11: '11-CM',
                12: '12-MD-Pf',
                13: '13-Hb',
                14: '14-MTT',
                1.1: 'lateral_ImClosed',
                1.2: 'posterior_ImClosed',
                1.3: 'Medial_ImClosed',
                1.4: 'Anterior_ImClosed',
                1.9: 'HierarchicalCascade' }
            self.name = NucleusName.get(self.index, 'Wrong Nucleus Index')

        def func_Parent_child(self):

            def func_Cascade(self):
                if self.index  == 1: self.parent , self.child = ( None , [2,4,5,6,7,8,9,10,11,12,13,14] )
                else:                self.parent , self.child = ( 1    , None )

            def func_HCascade(self):
                switcher_Parent = {
                    1: (None, [1.1 , 1.2 , 1.3 , 2]), # parent, child
                    1.1: (1, [4,5,6,7]),
                    1.2: (1, [8,9,10]), 
                    1.3: (1, [11,12,13]), 
                    1.4: (1, None), 
                    2:   (1, None) }                                                                                         
                if switcher_Parent.get(self.index): self.parent , self.child = switcher_Parent.get(self.index)
                else: 
                    _ , TH_child = switcher_Parent.get(1)
                    for ix in TH_child:
                        HC_parent, HC_child = switcher_Parent.get(ix)
                        if HC_child and self.index in HC_child: self.grandParent , self.parent , self.child = (HC_parent , ix , None)


            if   self.method == 'Cascade':  func_Cascade(self)
            elif self.method == 'HCascade': func_HCascade(self) 

        Name_of_Nucleus(self)
        func_Parent_child(self)

    def HCascade_Parents_Identifier(self, Nuclei_List):
        List_of_Parents = []

        b = NucleiIndex(1,'HCascade')        
        for ix in b.child:
            c = NucleiIndex(ix,'HCascade')
            if c.child and bool(set(Nuclei_List ) & set(c.child)): List_of_Parents.append(ix)

        return List_of_Parents
        
    def remove_Thalamus_From_List(self, Nuclei_List):
        if 1 in Nuclei_List: Nuclei_List.remove(1)
        return Nuclei_List
            
# a = NucleiIndex(6,'HCascade')

def gpuSetting(GPU_Index):
    
    os.environ["CUDA_VISIBLE_DEVICES"] = GPU_Index
    import tensorflow as tf
    from keras import backend as K
    K.set_session(tf.Session(   config=tf.ConfigProto( allow_soft_placement=True , gpu_options=tf.GPUOptions(allow_growth=True) )   ))    
    # K.set_session(tf.Session(   config=tf.ConfigProto( allow_soft_placement=True )   ))
    return K


def listSubFolders(Dir, params):

    subFolders = [s for s in next(os.walk(Dir))[1] if 'ERROR' not in s]
    if params.WhichExperiment.Dataset.check_vimp_SubjectName:  subFolders = [s for s in subFolders if 'vimp' in s]

    subFolders.sort()
    return subFolders

def mkDir(Dir):
    if not os.path.isdir(Dir): os.makedirs(Dir)
    return Dir

def saveImage(Image , Affine , Header , outDirectory):
    mkDir(outDirectory.split(os.path.basename(outDirectory))[0])
    out = nib.Nifti1Image((Image).astype('float32'),Affine)
    out.get_header = Header
    nib.save(out , outDirectory)

def nibShow(im1,im2):
    a = nib.viewers.OrthoSlicer3D(im1,title='1')
    b = nib.viewers.OrthoSlicer3D(im2,title='2')
    a.link_to(b)
    a.show()

def fixMaskMinMax(Image):
    if Image.max() > 1 or Image.min() < 0:
        print('smallFuncs','error in label values', 'min',Image.min() , 'max', Image.max() )
        Image = np.float32(Image)
        Image = ( Image-Image.min() )/( Image.max() - Image.min() )
        
    return Image

def terminalEntries(UserInfo):

    for en in range(len(sys.argv)):
        entry = sys.argv[en]

        if entry.lower() in ('-g','--gpu'):  # gpu num
            UserInfo['simulation'].GPU_Index = sys.argv[en+1]

        elif entry.lower() in ('-sd','--slicingdim'):
            if sys.argv[en+1].lower() == 'all':
                UserInfo['simulation'].slicingDim = [0,1,2]

            elif sys.argv[en+1][0] == '[':
                B = sys.argv[en+1].split('[')[1].split(']')[0].split(",")
                UserInfo['simulation'].slicingDim = [int(k) for k in B]

            else:
                UserInfo['simulation'].slicingDim = [int(sys.argv[en+1])]

        elif entry in ('-Aug','--AugmentMode'):
            a = int(sys.argv[en+1])
            UserInfo['AugmentMode'] = True if a > 0 else False

        elif entry in ('-v','--verbose'):
            UserInfo['verbose'] = int(sys.argv[en+1])

        elif entry.lower() in ('-n','--nuclei'):  # nuclei index
            if sys.argv[en+1].lower() == 'all':
                _, UserInfo['simulation'].nucleus_Index,_ = NucleiSelection(ind = 1)

            elif sys.argv[en+1].lower() == 'allh':
                _, NucleiIndexes ,_ = NucleiSelection(ind = 1) 
                UserInfo['simulation'].nucleus_Index = tuple(NucleiIndexes) + tuple([1.1,1.2,1.3])

            elif sys.argv[en+1][0] == '[':
                B = sys.argv[en+1].split('[')[1].split(']')[0].split(",")
                UserInfo['simulation'].nucleus_Index = [int(k) for k in B]

            else:
                UserInfo['simulation'].nucleus_Index = [float(sys.argv[en+1])] # [int(sys.argv[en+1])]

        elif entry.lower() in ('-l','--loss'):
            UserInfo['lossFunctionIx'] = int(sys.argv[en+1])

        elif entry.lower() in ('-d','--dataset'):
            UserInfo['DatasetIx'] = int(sys.argv[en+1])

        elif entry.lower() in ('-e','--epochs'):
            UserInfo['simulation'].epochs = int(sys.argv[en+1])

        elif entry.lower() in ('-lr','--Learning_Rate'):
            UserInfo['simulation'].Learning_Rate = float(sys.argv[en+1])
            
        elif entry.lower() in ('-nl','--num_Layers'):
            UserInfo['simulation'].num_Layers = int(sys.argv[en+1])

        elif entry.lower() in ('-FM','--FirstLayer_FeatureMap_Num'):
            UserInfo['simulation'].FirstLayer_FeatureMap_Num = int(sys.argv[en+1])

        elif entry.lower() in ('-m','--Model_Method'):
            if int(sys.argv[en+1]) == 1:
                UserInfo['Model_Method'] = 'Cascade' 
            elif int(sys.argv[en+1]) == 2: #'FCN_2D' 
                UserInfo['Model_Method'] = 'HCascade' 
            

    return UserInfo

def search_ExperimentDirectory(whichExperiment):

    sdTag = '/sd' + str(whichExperiment.Dataset.slicingInfo.slicingDim)
    def Search_ImageFolder(Dir, NucleusName):

        def splitNii(s):
            return s.split('.nii.gz')[0]

        def Classes_Local(Dir):
            class deformation:
                address = ''
                testWarp = ''
                testInverseWarp = ''
                testAffine = ''

            class temp:
                CropMask = ''
                Cropped = ''
                BiasCorrected = ''
                Deformation = deformation
                address = ''

            class tempLabel:
                address = ''
                Cropped = ''

            class label:
                LabelProcessed = ''
                LabelOriginal = ''
                Temp = tempLabel
                address = ''

            class newCropInfo:
                OriginalBoundingBox = ''
                PadSizeBackToOrig = ''

            class Files:
                ImageOriginal = ''
                ImageProcessed = ''
                Label = label
                Temp = temp
                address = Dir
                NewCropInfo = newCropInfo
                subjectName = ''

            return Files

        def Look_Inside_Label_SF(Files, NucleusName):
            Files.Label.Temp.address = mkDir(Files.Label.address + '/temp')
            A = next(os.walk(Files.Label.address))
            for s in A[2]:
                if NucleusName + '_PProcessed.nii.gz' in s: Files.Label.LabelProcessed = splitNii(s)
                if NucleusName + '.nii.gz' in s: Files.Label.LabelOriginal = splitNii(s)

            if Files.Label.LabelOriginal and not Files.Label.LabelProcessed:
                Files.Label.LabelProcessed = NucleusName + '_PProcessed'
                _, _, FullNames = NucleiSelection(ind=1)
                for name in FullNames: copyfile(Files.Label.address + '/' + name + '.nii.gz' , Files.Label.address + '/' + name + '_PProcessed.nii.gz')


            for s in A[1]:
                if 'temp' in s:
                    Files.Label.Temp.address = Files.Label.address + '/' + s

                    for d in os.listdir(Files.Label.Temp.address):
                        if '_Cropped.nii.gz' in d: Files.Label.Temp.Cropped = splitNii(d)

                    # Files.Label.Temp.Cropped = [ d.split('.nii.gz')[0] for d in os.listdir(Files.Label.Temp.address) if '_Cropped.nii.gz' in d]
                elif 'Label' in s: Files.Label.address = Dir + '/' + s

            return Files

        def Look_Inside_Temp_SF(Files):
            A = next(os.walk(Files.Temp.address))
            for s in A[2]:
                if 'CropMask.nii.gz' in s: Files.Temp.CropMask = splitNii(s)
                elif 'bias_corr.nii.gz' in s: Files.Temp.BiasCorrected = splitNii(s)
                elif 'bias_corr_Cropped.nii.gz' in s: Files.Temp.Cropped = splitNii(s)
                else: Files.Temp.origImage = splitNii(s)

            if 'deformation' in A[1]:
                Files.Temp.Deformation.address = Files.Temp.address + '/deformation'
                B = next(os.walk(Files.Temp.Deformation.address))
                for s in B[2]:
                    if 'testWarp.nii.gz' in s: Files.Temp.Deformation.testWarp = splitNii(s)
                    elif 'testInverseWarp.nii.gz' in s: Files.Temp.Deformation.testInverseWarp = splitNii(s)
                    elif 'testAffine.txt' in s: Files.Temp.Deformation.testAffine = splitNii(s)

            if not Files.Temp.Deformation.address: Files.Temp.Deformation.address = mkDir(Files.Temp.address + '/deformation')

            return Files

        def check_IfImageFolder(Files):
            A = next(os.walk(Files.address))
            for s in A[2]:
                if 'PProcessed.nii.gz' in s: Files.ImageProcessed = splitNii(s)
                if '.nii.gz' in s and 'PProcessed.nii.gz' not in s: Files.ImageOriginal = splitNii(s)

            if Files.ImageOriginal or Files.ImageProcessed:
                for s in A[1]:
                    if 'temp' in s: Files.Temp.address = mkDir(Dir + '/' + s)
                    elif 'Label' in s: Files.Label.address = Dir + '/' + s

                if Files.ImageOriginal and not Files.ImageProcessed:
                    Files.ImageProcessed = 'PProcessed'
                    copyfile(Dir + '/' + Files.ImageOriginal + '.nii.gz' , Dir + '/' + Files.ImageProcessed + '.nii.gz')

            if not Files.Temp.address: Files.Temp.address = mkDir(Dir + '/temp')

            return Files

        Files = Classes_Local(Dir)
        Files = check_IfImageFolder(Files)

        if Files.ImageOriginal or Files.ImageProcessed:
            if os.path.exists(Files.Label.address): Files = Look_Inside_Label_SF(Files, NucleusName)
            if os.path.exists(Files.Temp.address):  Files = Look_Inside_Temp_SF(Files)

        return Files

    def checkInputDirectory(Dir, NucleusName):
        class Input:
            address = os.path.abspath(Dir)
            Subjects = {}

        def LoopReadingData(Inputt, Dirr):
            SubjectsList = next(os.walk(Dirr))[1]

            if whichExperiment.Dataset.check_vimp_SubjectName: SubjectsList = [s for s in SubjectsList if 'vimp' in s]

            for s in SubjectsList:
                Inputt.Subjects[s] = Search_ImageFolder(Dirr + '/' + s , NucleusName)
                Inputt.Subjects[s].subjectName = s

            return Inputt

        Read = whichExperiment.Dataset.ReadTrain
        Input = LoopReadingData(Input, Dir)
        if Read.Main and os.path.exists( Dir + '/Main'): Input = LoopReadingData(Input, Dir + '/Main')
        if Read.ET   and os.path.exists( Dir + '/ET'  ): Input = LoopReadingData(Input, Dir + '/ET')            
        if Read.SRI  and os.path.exists( Dir + '/SRI' ): Input = LoopReadingData(Input, Dir + '/SRI')
        
        if Read.ReadAugments.Mode:
            DirAug = Dir + '/Augments/' + Read.ReadAugments.Tag 
            
            if Read.Main and os.path.exists( DirAug + '/Main' + sdTag):  Input = LoopReadingData( Input, DirAug + '/Main' + sdTag  )
            if Read.ET   and os.path.exists( DirAug + '/ET'   + sdTag ): Input = LoopReadingData( Input, DirAug + '/ET'   + sdTag  )
                
        return Input

    Exp_address = whichExperiment.Experiment.address
    SE      = whichExperiment.SubExperiment
    NucleusName = whichExperiment.Nucleus.name

    class train:
        address        = Exp_address + '/train'
        Model          = Exp_address + '/models/' + SE.name          + '/' + NucleusName  + sdTag
        Model_Thalamus = Exp_address + '/models/' + SE.name          + '/' + '1-THALAMUS' + sdTag
        Model_3T       = Exp_address + '/models/' + SE.name_Init_3T  + '/' + NucleusName  + sdTag
        Input   = checkInputDirectory(address, NucleusName)
    
    class test:
        address = Exp_address + '/test'
        Result  = Exp_address + '/results/' + SE.name + sdTag
        Input   = checkInputDirectory(address, NucleusName)

    class Directories:
        Train = train()
        Test  = test()

    return Directories()

def imShow(*args):
    _, axes = plt.subplots(1,len(args))
    for ax, im in enumerate(args):
        axes[ax].imshow(im,cmap='gray')

    # a = nib.viewers.OrthoSlicer3D(im,title='image')

    plt.show()

    return True

def mDice(msk1,msk2):
    intersection = msk1*msk2
    return intersection.sum()*2/(msk1.sum()+msk2.sum() + np.finfo(float).eps)

"""
def Loading_UserInfo(DirLoad, method):

    def loadReport(DirSave, name, method):

        def loadPickle(Dir):
            f = open(Dir,"wb")
            data = pickle.load(f)
            f.close()
            return data

        if 'pickle' in method:
            return loadPickle(DirSave + '/' + name + '.pkl')
        # elif 'mat' in method:
            # return mat4py.loadmat(DirSave + '/' + name + '.pkl')

    def dict2obj(d):
        if isinstance(d, list):
            d = [dict2obj(x) for x in d]
        if not isinstance(d, dict):
            return d
        class C(object):
            pass
        o = C()
        for k in d:
            o.__dict__[k] = dict2obj(d[k])
        return o

    UserInfo = loadReport(DirLoad, 'UserInfo', method)
    UserInfo = dict2obj( UserInfo )

    a = UserInfo['InputDimensions'].replace(',' ,'').split('[')[1].split(']')[0].split(' ')
    UserInfo['InputDimensions'] = [int(ai) for ai in a]
    return UserInfo
"""

def findBoundingBox(PreStageMask):
    objects = measure.regionprops(measure.label(PreStageMask))

    L = len(PreStageMask.shape)
    if len(objects) > 1:
        area = []
        for obj in objects: area = np.append(area, obj.area)

        Ix = np.argsort(area)
        bbox = objects[ Ix[-1] ].bbox

    else:
        bbox = objects[0].bbox

    BB = [ [bbox[d] , bbox[L + d] ] for d in range(L)]

    return BB

def Saving_UserInfo(DirSave, params):
                            
    # DirSave = '/array/ssd/msmajdi/experiments/keras/exp7_cascadeV1/models/sE11_Cascade_wRot7_6cnts_sd2/4-VA'
    User_Info = {            
        'num_Layers'     : int(params.WhichExperiment.HardParams.Model.num_Layers),
        'Trained_SRI'    : params.UserInfo['ReadTrain'].SRI,
        'Trained_ET'     : params.UserInfo['ReadTrain'].ET,
        'Trained_Main'   : params.UserInfo['ReadTrain'].Main,
        'Model_Method'   : params.UserInfo['Model_Method'],
        'FromThalamus'   : params.UserInfo['InitializeB'].FromThalamus,
        'FromOlderModel' : params.UserInfo['InitializeB'].FromOlderModel,
        'From_3T'        : params.UserInfo['InitializeB'].From_3T,
        'Learning_Rate'  : params.UserInfo['simulation'].Learning_Rate,
        'Normalizae'     : params.UserInfo['simulation'].NormalizaeMethod,
        'slicing_Dim'    : params.UserInfo['simulation'].slicingDim[0],
        'batch'          : int(params.UserInfo['simulation'].batch_size),
        'FeatureMaps'    : int(params.UserInfo['simulation'].FirstLayer_FeatureMap_Num),
        'Mult_Thalmaus'  : params.UserInfo['simulation'].Multiply_By_Thalmaus,
        'Weighted_Class' : params.UserInfo['simulation'].Weighted_Class_Mode,
        'Dropout'        : params.UserInfo['DropoutValue'],
        'gapDilation'    : int(params.UserInfo['gapDilation']),
        'ImClosePrediction' : params.UserInfo['simulation'].ImClosePrediction,
        'InputPadding_Mode' : params.UserInfo['InputPadding'].Automatic,
        'InputPadding_Dims' : [int(s) for s in params.WhichExperiment.HardParams.Model.InputDimensions],
    }

    with open(DirSave + '/UserInfo.json', "w") as j:
        j.write(json.dumps(User_Info))

    # with open(DirSave + '/UserInfo.json', "r") as j:
    #     data = json.load(j)