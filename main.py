import os
import sys
import subprocess

sys.path.append(os.path.dirname(__file__))
import otherFuncs.smallFuncs as smallFuncs
from otherFuncs import datasets
import modelFuncs.choosingModel as choosingModel
import Parameters.UserInfo as UserInfo
import Parameters.paramFunc as paramFunc
import preprocess.applyPreprocess as applyPreprocess
from keras import backend as K
import nibabel as nib
import numpy as np
from nilearn import image as niImage
import shutil
from preprocess import uncrop

UserInfoB = smallFuncs.terminalEntries(UserInfo.__dict__)
UserInfoB['simulation'] = UserInfoB['simulation']()
K = smallFuncs.gpuSetting(UserInfoB['simulation'].GPU_Index)



def main(UserInfoB):
    def fuse_nuclei(Directory, mode='_PProcessed'):
        """ Saving all of the predicted nuclei into one nifti image

        Args:
            Directory (str): The path to all predicted nuclei
            mode (str, optional): Optional tag that can be added to the predicted nuclei names. Defaults to '_PProcessed'.
        """

        mask = []

        # Looping through all nuclei
        for cnt in (1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14):

            name = smallFuncs.Nuclei_Class(index=cnt).name
            dirr = Directory + '/' + name + mode + '.nii.gz'
            if os.path.isfile(dirr):
                if cnt == 1:
                    # loading thalamus mask for the purpose of using its affine matrices & header
                    assert os.path.isfile(dirr), 'Thalamus mask does not exist'
                    thalamus_mask = nib.load(dirr)

                else:
                    # saving the nuclei into one mask
                    msk = nib.load(dirr).get_data()
                    if mask == []:
                        # saving the first nucleus (2-AV)
                        mask = cnt * msk
                    else:
                        # saving the remaining nuclei, while randomly assigning a label from the labels 
                        # that exist in the overlapping area
                        mask_temp = mask.copy()
                        mask_temp[msk == 0] = 0
                        x = np.where(mask_temp > 0)
                        if x[0].shape[0] > 0:
                            fg = np.random.randn(x[0].shape[0])
                            fg1, fg2 = fg >= 0, fg < 0
                            mask[x[0][fg1], x[1][fg1], x[2][fg1]] = 0
                            msk[x[0][fg2], x[1][fg2], x[2][fg2]] = 0

                        mask += cnt * msk

        # Saving the final multi-label segmentaion mask as a nifti image
        smallFuncs.saveImage(mask, thalamus_mask.affine, thalamus_mask.header, Directory + '/AllLabels.nii.gz')

    def running_main(UserInfoB):
        """ Running the network on left and/or right thalamus

        Args:
            UserInfoB: User Inputs
        """

        def Run(UserInfoB):
            """ Loading the dataset & running the network on the assigned slicing orientation & nuclei

            Args:
                UserInfoB: User Inputs
            """

            params = paramFunc.Run(UserInfoB, terminal=True)
            print('\n', params.WhichExperiment.Nucleus.name, 'SD: ' + str(UserInfoB['simulation'].slicingDim),
                  'GPU: ' + str(UserInfoB['simulation'].GPU_Index), '\n')

            # Loading the dataset
            Data, params = datasets.loadDataset(params)

            # Running the training/testing network
            choosingModel.check_Run(params, Data)

            # clearing the gpu session
            # K.clear_session()

        def merge_results_and_apply_25D(UserInfoB):
            """ Merging the sagittal, Coronal, and axial networks prediction masks using 2.5D majority voting
            """

            params = paramFunc.Run(UserInfoB, terminal=True)
            smallFuncs.apply_MajorityVoting(params)

        def predict_thalamus_for_sd0(UserI):
            """ Due to the existense of both left and right thalamus in the cropped nifti image while lacking the
                manual labels for the right thalamus, during the sagittal network process, to predict the whole thalamus
                all 3D volumes will be sampled in the coronal direction instead of sagittal
            """

            # Predicting the whole thalamus in the coronal orientation
            UserI['simulation'].slicingDim = [2]
            UserI['simulation'].nucleus_Index = [1]
            UserI['simulation'].Use_Coronal_Thalamus_InSagittal = True
            Run(UserI)

            # Predicting the remaining of nuclei in the sagittal orientation
            UserI['simulation'].slicingDim = [0]
            UserI['simulation'].nucleus_Index = [2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
            Run(UserI)

        def predict_multi_thalamus(UserI):
            """ Running the two consecutive networks in the cascaded algorithm for axial & coronal orientations
            """

            # Running the 1st network of cascaded algorithm: Predicting whole thalamus 
            UserI['simulation'].nucleus_Index = [1]
            Run(UserI)

            # Running the 2nd network of cascaded algorithm: Predicting the remaiing of nuclei 
            # after cropping the input image & its nuclei using predicted whole thalamus bounding box
            UserI['simulation'].nucleus_Index = [2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
            Run(UserI)

        # Running the sagittal network
        UserInfoB['simulation'].FirstLayer_FeatureMap_Num = 40  # Number of feature maps in the first layer of Resnet
        UserInfoB['simulation'].slicingDim = [0]  # Sagittal Orientation
        UserInfoB['simulation'].nucleus_Index = [1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
        predict_thalamus_for_sd0(UserInfoB)

        # Running the axial network
        UserInfoB['simulation'].FirstLayer_FeatureMap_Num = 30  # Number of feature maps in the first layer of Resnet
        UserInfoB['simulation'].slicingDim = [1]  # Axial Orientation
        UserInfoB['simulation'].nucleus_Index = [1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
        predict_multi_thalamus(UserInfoB)

        # Running the coronal network
        UserInfoB['simulation'].FirstLayer_FeatureMap_Num = 20  # Number of feature maps in the first layer of Resnet
        UserInfoB['simulation'].slicingDim = [2]  # Coronal Orientation
        UserInfoB['simulation'].nucleus_Index = [1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
        # UserInfoB['simulation'].Use_Coronal_Thalamus_InSagittal = False
        predict_multi_thalamus(UserInfoB)

        merge_results_and_apply_25D(UserInfoB)

    def uncrop_output(subj='', thalamus_side='left'):

        input_address       = subj.address + f'/{thalamus_side}/2.5D_MV/AllLabels.nii.gz'
        crop_mask_address   = subj.address + '/temp/CropMask.nii.gz'
        cropped_input_image = subj.address + '/temp/' + subj.ImageOriginal + '_Cropped.nii.gz'

        # Checking to see if the CropMask exist. This file will be created if the cropping step of preprocessing is performed
        if os.path.isfile(crop_mask_address) and os.path.isfile(cropped_input_image):

            # re-orienting the outputs to their original space
            target_affine  = nib.load(cropped_input_image).affine
            target_shape   = nib.load(cropped_input_image).shape
            output_original_space_address = subj.address + f'/{thalamus_side}/2.5D_MV/AllLabels_original_space.nii.gz'

            im = niImage.resample_img(img=nib.load(input_address), target_affine=target_affine, target_shape=target_shape, interpolation='nearest')
            nib.save(im, output_original_space_address)


            # uncropping the re-oriented outputs
            output_full_size_address = subj.address + f'/{thalamus_side}/2.5D_MV/AllLabels_full_size.nii.gz'
            uncrop.uncrop_by_mask(input_image=output_original_space_address, output_image=output_full_size_address , full_mask=crop_mask_address)  

    def run_Left(UserInfoB):
        """ running the network on left thalamus """

        UserInfoB['thalamic_side'].active_side = 'left'
        running_main(UserInfoB)

        # Updating the parameters for left thalamus
        params = paramFunc.Run(UserInfoB, terminal=True)

        # Looping through subjects
        for subj in params.directories.Test.Input.Subjects.values():

            #  Saving the multi label nifti image consisting of all predicted labels from 2-AV to 14-MTT 
            fuse_nuclei(subj.address + '/left/2.5D_MV', mode='')

            # Uncropping the cropped fused output
            uncrop_output(subj=subj, thalamus_side='left')

    def run_Right(UserInfoB):
        """ running the network on right thalamus """

        def flip_inputs(params):
            print('Flip L-R the image & its nuclei')

            subjects = params.directories.Test.Input.Subjects.copy()
            code_address = params.WhichExperiment.Experiment.code_address + '/otherFuncs/flip_inputs.py'
            subjects.update(params.directories.Train.Input.Subjects)

            for subj in subjects.values():
                command = "cd {0};python {1} -i {0}/PProcessed.nii.gz -o {0}/PProcessed.nii.gz;".format(subj.address, code_address)
                subprocess.call(command, shell=True)

                command = "cd {0};mv {0}/PProcessed.nii.gz {0}/flipped_PProcessed.nii.gz;".format(subj.address)
                subprocess.call(command, shell=True)

        def unflip_inputs(params):
            print('Reverse Flip L-R the flipped image & its nuclei')

            subjects = params.directories.Test.Input.Subjects.copy()

            # Stacking train & test subjects
            subjects.update(params.directories.Train.Input.Subjects)

            # Address to the flipping python code
            code_address = params.WhichExperiment.Experiment.code_address + '/otherFuncs/flip_inputs.py'

            # Flipping back the nifti images back to their original space for both train & test data
            for subj in subjects.values():

                # Flipping back the nifti image to its original space
                command = "cd {0};python {1} -i {0}/flipped_PProcessed.nii.gz -o {0}/flipped_PProcessed.nii.gz;".format(subj.address, code_address)
                subprocess.call(command, shell=True)

                # re-naming the nifti image to its original name
                command = "cd {0};mv {0}/flipped_PProcessed.nii.gz {0}/PProcessed.nii.gz;".format(subj.address)
                subprocess.call(command, shell=True)

            # Flipping back the right thalamic nuclei predictions to their original space for only test data
            for subj in params.directories.Test.Input.Subjects.values():
                command = "cd {0};for n in right/*/*.nii.gz; do python {1} -i {0}/$n -o {0}/$n; done".format(subj.address, code_address)
                subprocess.call(command, shell=True)

        # Setting the active side to right thalamus. This is important to let the software know it shouldn't 
        # run training on these data and only use it for testing purposes. Also not to measure Dice (in case of the existense of manual label)
        UserInfoB['thalamic_side'].active_side = 'right'
        params = paramFunc.Run(UserInfoB, terminal=True)

        # Flipping the data
        flip_inputs(params)

        # Running the trained network on right thalamus
        running_main(UserInfoB)

        # Flipping the data back to its original orientation
        unflip_inputs(params)

        # Looping through subjects
        for subj in params.directories.Test.Input.Subjects.values():

            #  Saving the multi label nifti image consisting of all predicted labels from 2-AV to 14-MTT 
            fuse_nuclei(subj.address + '/right/2.5D_MV', mode='')

            # Uncropping the cropped fused output
            uncrop_output(subj=subj, thalamus_side='right') 

    def fuse_left_right_nuclei_together(UserInfoB):

        def fuse_func(output_name):

            # Function to load left or right fused thalamic nuclei prediction
            load_side = lambda thalamus_side: nib.load(subj.address + '/' + thalamus_side + '/2.5D_MV/' + output_name + '.nii.gz')

            # Loading the left and right fused thalamic nuclei predictions 
            left, right = load_side('left'), load_side('right')

            # Saving the final fused nifti image that contains all left and right nuclei
            smallFuncs.saveImage(Image=left.get_data() + right.get_data(), Affine=left.affine, Header=left.header,
                                outDirectory=subj.address + '/left/' + output_name + '_Left_and_Right.nii.gz')

        params = paramFunc.Run(UserInfoB, terminal=True)
        for subj in params.directories.Test.Input.Subjects.values():
            fuse_func('AllLabels')

    def moving_files_into_original_directory(UserInfoB):
        old_test_address = UserInfoB['experiment'].old_test_address   
        new_test_address = UserInfoB['experiment'].test_address + '/case_1'
        test_address     = UserInfoB['experiment'].test_address

        command = f"mv {new_test_address}/* {old_test_address}/"
        subprocess.call(command, shell=True)

        command = f"rm -r {test_address}"
        subprocess.call(command, shell=True)


    applyPreprocess.main(paramFunc.Run(UserInfoB, terminal=True))

    TS = UserInfoB['thalamic_side']()

    # Running the network on left thalamus
    if TS.left:  run_Left(UserInfoB)

    # Running the network on right thalamus
    if TS.right: run_Right(UserInfoB)

    # Merging the left & right predictions into one nifti file
    if TS.left and TS.right: fuse_left_right_nuclei_together(UserInfoB)

    # This portion will run if the input path to test files was a single nifti file.
    if UserInfoB['experiment'].test_path_is_nifti_file:
        moving_files_into_original_directory(UserInfoB)


if __name__ == '__main__':
    main(UserInfoB)



