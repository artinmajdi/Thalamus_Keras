# import os, sys
# sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import numpy as np
from random import shuffle
from scipy.misc import imrotate
import nibabel as nib
from preprocess import BashCallingFunctionsA
from otherFuncs import smallFuncs
import os


def funcRotating(Image , angle):

    for i in range(Image.shape[2]):
        Image[...,i] = imrotate(Image[...,i],angle)

    return Image

def funcShifting(Image , shift):

    Image = np.roll(Image,shift[0],axis=0)
    Image = np.roll(Image,shift[1],axis=1)

    return Image

def indexFunc(L,AugmentLength, ind):

    if AugmentLength > L:
        AugmentLength = L-1

    rang = range(L)
    rang = np.delete(rang,rang.index(ind))
    shuffle(rang)
    rang = rang[:AugmentLength]
    return rang

def LinearFunc(params, mode):

    Subjects = params.directories.Train.Input.Subjects
    SubjectNames = list(Subjects.keys())
    L = len(SubjectNames)

    for imInd in range(31,L):
        nameSubject = SubjectNames[imInd]
        subject  = Subjects[nameSubject]

        # lst = indexFunc(L, AugLen, imInd)
        for AugIx in range(params.preprocess.Augment.LinearAugmentLength):
            print('image',imInd,'/',L,'augment',AugIx,'/',params.preprocess.Augment.LinearAugmentLength)

            im = nib.load(subject.address + '/' + subject.ImageProcessed + '.nii.gz')  # 'Cropped' for cropped image
            Image  = im.get_data()
            Header = im.header
            Affine = im.affine

            angle = np.random.random_integers(-2,2)
            shift = [ np.random.random_integers(-10,10) , np.random.random_integers(-10,10)]


            nameSubject2 = nameSubject + '_Aug' + str(AugIx)
            if params.preprocess.Augment.Rotation:
                Image = funcRotating(Image , angle)
                nameSubject2 = nameSubject2 + '_Rot_' + str(angle) 

            if params.preprocess.Augment.Shift:
                Image = funcShifting(Image , shift)
                nameSubject2 = nameSubject2 + '_shift_' + str(shift[0]) + '-' + str(shift[1])

            outDirectoryImage = smallFuncs.mkDir( params.directories.Train.Input.address + '/' + nameSubject2)
            outDirectoryMask = smallFuncs.mkDir( params.directories.Train.Input.address + '/' + nameSubject2 + '/Labels')


            outDirectoryImage2 = outDirectoryImage + '/' + subject.ImageProcessed + '.nii.gz'
            smallFuncs.saveImage(Image , Affine , Header , outDirectoryImage2)
            # smallFuncs.copyfile(outDirectoryImage2 , outDirectoryImage  + '/' + subject.ImageProcessed.split('_PProcessed')[0] + '.nii.gz')


            #! applying the augmentation on CropMask
            Dir_CropMask_In = subject.Temp.address + '/' + subject.Temp.CropMask + '.nii.gz'

            smallFuncs.mkDir(outDirectoryImage + '/temp/')
            Dir_CropMask_Out = outDirectoryImage + '/temp/' + subject.Temp.CropMask + '.nii.gz'
            if os.path.isfile(Dir_CropMask_In):

                CropMask = nib.load(Dir_CropMask_In).get_data() 
                if params.preprocess.Augment.Rotation: CropMask = funcRotating(CropMask , angle)
                if params.preprocess.Augment.Shift:    CropMask = funcShifting(CropMask , shift)
                smallFuncs.saveImage( np.float32(CropMask > 0.5) , Affine , Header , Dir_CropMask_Out)

            for ind in params.WhichExperiment.Nucleus.FullIndexes:
                NucleusName, _ = smallFuncs.NucleiSelection(ind , params.WhichExperiment.Nucleus.Organ)

                Mask   = nib.load(subject.Label.address + '/' + NucleusName + '_PProcessed.nii.gz').get_data() # 'Cropped' for cropped image

                if params.preprocess.Augment.Rotation: Mask = funcRotating(Mask , angle)
                if params.preprocess.Augment.Shift:    Mask = funcShifting(Mask , shift)

                outDirectoryMask2  = outDirectoryMask  + '/' + NucleusName + '_PProcessed.nii.gz'
                smallFuncs.saveImage( np.float32(Mask > 0.5) , Affine , Header , outDirectoryMask2)
                # smallFuncs.copyfile(outDirectoryMask2 , outDirectoryMask  + '/' + NucleusName + '.nii.gz')

def NonLinearFunc(Input, Augment, mode):

    Subjects = Input.Subjects
    SubjectNames = list(Subjects.keys())
    L = len(SubjectNames)

    for imInd in range(L):
        nameSubject = SubjectNames[imInd]
        subject  = Subjects[nameSubject]

        lst = indexFunc(L, Augment.NonLinearAugmentLength, imInd)

        AugIx = 0
        for augInd in lst:
            AugIx = AugIx + 1
            print('image',imInd,'/',L,'augment',AugIx,'/',len(lst))

            nameSubjectRef = SubjectNames[augInd]
            subjectRef = Subjects[nameSubjectRef]

            # Image     = subject.address    + '/' + subject.ImageProcessed + '.nii.gz'
            # Reference = subjectRef.address + '/' + subjectRef.ImageProcessed + '.nii.gz'

            # Mask      = subject.Label.address    + '/' + subject.Label.LabelProcessed + '.nii.gz'
            # Reference = subjectRef.Label.address + '/' + subjectRef.Label.LabelProcessed + '.nii.gz'

            outputAddress = smallFuncs.mkDir( Input.address + '/' + nameSubject + '_Aug' + str(AugIx) + '_Ref_' + nameSubjectRef )

            BashCallingFunctionsA.Bash_AugmentNonLinear(subject , subjectRef , outputAddress)

# TODO fix "LinearFunc" & "NonLinearFunc" function to count for situations when we only want to apply the function on one case
def main_augment(params , Flag, mode):

    if 'experiment' in mode:
        if params.preprocess.Augment.Mode and (params.preprocess.Augment.Rotation or params.preprocess.Augment.Shift) and (Flag == 'Linear'):
            LinearFunc(params, mode)

        elif params.preprocess.Augment.Mode and params.preprocess.Augment.NonRigidWarp and (Flag == 'NonLinear'):
            NonLinearFunc(params.directories.Train.Input , params.preprocess.Augment, mode)

    else:
        # if 'Linear' in Flag: LinearFunc(params, mode)
        # if 'NonLinear' in Flag: NonLinearFunc(params.directories.Train.Input , params.preprocess.Augment, mode)
        print('')