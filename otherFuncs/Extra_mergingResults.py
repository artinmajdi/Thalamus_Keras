import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import numpy as np
import pandas as pd
import otherFuncs.smallFuncs as smallFuncs
import Parameters.UserInfo as UserInfo
import Parameters.paramFunc as paramFunc
import pickle 

UserInfoB = smallFuncs.terminalEntries(UserInfo=UserInfo.__dict__)
params = paramFunc.Run(UserInfoB)
# NucleiIndexes = UserInfoB['simulation'].nucleus_Index
_, NucleiIndexes , _ = smallFuncs.NucleiSelection(ind=1)

def savingHistory_AsExcel(params):

        Dir = params.WhichExperiment.Experiment.address + '/models'

        # _, FullIndexes, namesNulcei = smallFuncs.NucleiSelection(1)
        # namesNulcei = smallFuncs.AllNucleiNames(FullIndexes)
        n_epochsMax = 300

        List_subExperiments = [a for a in os.listdir(Dir) if ('subExp' in a) or ('sE' in a) ]
        writer = pd.ExcelWriter(  params.WhichExperiment.Experiment.address + '/results/All_LossAccForEpochs.xlsx', engine='xlsxwriter')
        for IxNu in tuple(NucleiIndexes) + tuple([1.1,1.2]):                
                nucleus, _ , _ = smallFuncs.NucleiSelection(IxNu)
                print('Learning Curves: ', nucleus)
                # dir_save = smallFuncs.mkDir((params.directories.Test.Result).split('/subExp')[0] + '/Train_Output')
                AllNucleusInfo = []
                ind = -1
                for subExperiment in List_subExperiments:
                        try:
                                subDir = Dir + '/' + subExperiment + '/' + nucleus
                                if os.path.exists(subDir):
                                        ind = ind + 1
                                        a  = open(subDir + '/hist_history.pkl' , 'rb')
                                        history = pickle.load(a)
                                        a.close()
                                        keys = list(history.keys())
                                        
                                        nucleusInfo = np.zeros((n_epochsMax,len(keys)+2))
                                        for ix, key in enumerate(keys):
                                                A = history[key]                                        
                                                nucleusInfo[:len(A),ix+2] = np.transpose(A)

                                        if ind == 0:
                                                nucleusInfo[:len(A),0] = np.array(range(len(A)))
                                                AllNucleusInfo = nucleusInfo
                                                FullNamesLA = np.append(['Epochs', subExperiment],  keys )
                                        else:
                                                AllNucleusInfo = np.concatenate((AllNucleusInfo, nucleusInfo) , axis=1)
                                                namesLA = np.append(['', subExperiment],  keys )
                                                FullNamesLA = np.append(FullNamesLA, namesLA)

                                        # df = pd.DataFrame(data=nucleusInfo, columns=np.append(['Epochs', subExperiment],  keys ))
                                        # df.to_csv(subDir + '/history.csv', index=False)
                        except:
                                print('failed',nucleus)

                if len(AllNucleusInfo) != 0:
                        df = pd.DataFrame(data=AllNucleusInfo, columns=FullNamesLA)
                        # df.to_csv(Dir + '/history_AllSubExperiments_' + nucleus + '.csv', index=False)                        
                        df.to_excel(writer, sheet_name=nucleus)
        writer.close()

def mergingDiceValues(Dir):
        
        def mergingDiceValues_ForOneSubExperiment(Dir):
                subF = os.listdir(Dir)
                subF = [a for a in subF if 'vimp' in a]
                subF.sort()
                Dice_Test = []

                names = list(np.zeros(18))
                names[0] = 'subjects'

                for subject in subF:
                        Dir_subject = Dir + '/' + subject
                        a = os.listdir(Dir_subject)
                        a = [i for i in a if 'Dice_' in i]

                        Dice_Single = list(np.zeros(18))
                        Dice_Single[0] = subject


                        for ix in tuple(NucleiIndexes) + tuple([1.1,1.2,1.3]):
                                if ix in range(16):
                                        ind = ix                                 
                                elif ix == 1.1:
                                        ind = 15
                                elif ix == 1.2:
                                        ind = 16
                                elif ix == 1.3:
                                        ind = 17                                        

                                names[ind], _ , _ = smallFuncs.NucleiSelection(ix)
                                if os.path.isfile(Dir_subject + '/Dice_' + names[ind]+'.txt'):
                                        b = np.loadtxt(Dir_subject + '/Dice_' + names[ind]+'.txt')
                                        Dice_Single[ind] = b[1]

                                        
                        Dice_Test.append(Dice_Single)

                df = pd.DataFrame(data=Dice_Test, columns=names)
                df.to_csv(Dir + '/Dices.csv', index=False)

                return df

        writer = pd.ExcelWriter(Dir + '/All_Dice.xlsx', engine='xlsxwriter')
        List_subExperiments = [a for a in os.listdir(Dir) if ('subExp' in a) or ('sE' in a)]
        for ixSE, subExperiment in enumerate(List_subExperiments):
                try:
                        print('Dices: ', str(ixSE) + '/' + str(len(List_subExperiments)), subExperiment)
                        df = mergingDiceValues_ForOneSubExperiment(Dir + '/' + subExperiment)
                        if len(subExperiment) > 31: subExperiment = subExperiment[:31]
                        df.to_excel(writer, sheet_name=subExperiment)
                except:
                        print(subExperiment,'failed')
        writer.close()


mergingDiceValues(params.WhichExperiment.Experiment.address + '/results')

savingHistory_AsExcel(params)

os.system('bash /array/ssd/msmajdi/code/thalamus/keras/bashCodes/zip_Bash')