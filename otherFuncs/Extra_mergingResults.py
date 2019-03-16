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
# NucleiIndexes = UserInfoB['nucleus_Index']
_, NucleiIndexes , _ = smallFuncs.NucleiSelection(ind=1)

def savingHistory_AsExcel(params):

        Dir = (params.directories.Train.Model).split('/subExp')[0]

        # _, FullIndexes, namesNulcei = smallFuncs.NucleiSelection(1)
        # namesNulcei = smallFuncs.AllNucleiNames(FullIndexes)
        n_epochsMax = 300

        List_subExperiments = [a for a in os.listdir(Dir) if 'subExp' in a]
        writer = pd.ExcelWriter((params.directories.Test.Result).split('/subExp')[0] + '/All_LossAccForEpochs.xlsx', engine='xlsxwriter')
        for IxNu in tuple(NucleiIndexes) + tuple([1.1,1.2]):
                nucleus, _ , _ = smallFuncs.NucleiSelection(IxNu)
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
                                print('failed')

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

                # _, FullIndexes, _ = smallFuncs.NucleiSelection(1)
                # names = np.append(['subjects'], smallFuncs.AllNucleiNames(FullIndexes))
                names = list(np.zeros(17))
                names[0] = 'subjects'
                # for ind in NucleiIndexes:
                #         if ind != 4567: names[ind], _ , _ = smallFuncs.NucleiSelection(ind)

                for subject in subF:
                        Dir_subject = Dir + '/' + subject
                        a = os.listdir(Dir_subject)
                        a = [i for i in a if 'Dice_' in i]

                        Dice_Single = list(np.zeros(17))
                        Dice_Single[0] = subject
                        # for n in a:


                        for ix in tuple(NucleiIndexes) + tuple([1.1,1.2]):
                                if ix in range(16):
                                        ind = ix                                 
                                elif ix == 1.1:
                                        ind = 15
                                elif ix == 1.2:
                                        ind = 16

                                names[ind], _ , _ = smallFuncs.NucleiSelection(ix)
                                if os.path.isfile(Dir_subject + '/Dice_' + names[ind]+'.txt'):
                                        b = np.loadtxt(Dir_subject + '/Dice_' + names[ind]+'.txt')
                                        Dice_Single[int(b[0])] = b[1]

                                        
                        Dice_Test.append(Dice_Single)

                df = pd.DataFrame(data=Dice_Test, columns=names)
                df.to_csv(Dir + '/Dices.csv', index=False)

                return df

        writer = pd.ExcelWriter(Dir + '/All_Dice.xlsx', engine='xlsxwriter')
        List_subExperiments = [a for a in os.listdir(Dir) if 'subExp' in a]
        for subExperiment in List_subExperiments:
                try:
                        df = mergingDiceValues_ForOneSubExperiment(Dir + '/' + subExperiment)
                        if len(subExperiment) > 31: subExperiment = subExperiment[:31]
                        df.to_excel(writer, sheet_name=subExperiment)
                except:
                        print(subExperiment,'failed')
        writer.close()


mergingDiceValues((params.directories.Test.Result).split('/subExp')[0])

savingHistory_AsExcel(params)

# A = UserInfoB['slicingDim'] if isinstance(UserInfoB['slicingDim'] , list) else [UserInfoB['slicingDim']]

# for UserInfoB['slicingDim'] in A: