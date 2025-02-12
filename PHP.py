def predictVirusHost(scriptPath,bacteriaKmerDir,bacteriaKmerName,outFileDir,dicVirusSeqLength):
    import pandas as pd
    import numpy  as np
    import joblib
    import heapq
    
    modelFullLength = joblib.load(scriptPath+'/model/FullLength/FullLength.m')
    model10k = joblib.load(scriptPath+'/model/10k/10k.m')
    model5k = joblib.load(scriptPath+'/model/5k/5k.m')
    model3k = joblib.load(scriptPath+'/model/3k/3k.m')
    model1k = joblib.load(scriptPath+'/model/1k/1k.m')
    ###
    hostAll = pd.read_csv(bacteriaKmerDir + bacteriaKmerName, sep=',', header=None, index_col=0).astype('float32')  # 全部的细菌基因组kmer
    listHostName = hostAll._stat_axis.values.tolist()  # 得到测试的宿主的名字列表
    print('bacteriaNum', len(listHostName))
    fileOut = open(outFileDir + bacteriaKmerName + '_Prediction_Maxhost.tsv', 'w')
    fileOut.write( 'queryVirus\tscore\t_maxScoreHost\n')
    fileOutAll = open(outFileDir + bacteriaKmerName + '_Prediction_Allhost.csv','w')
    fileOutAll.write('host')
    for eachHost in listHostName:
        fileOutAll.write(','+str(eachHost))
    fileOutAll.write('\n')
    
    testVirusAll = pd.read_csv(outFileDir+'virusKmer', sep=',', header=None, index_col=0)
    testList = testVirusAll._stat_axis.values.tolist()
    n = 0
    for eachVirus in testList:
        n+=1
        print('Counting score\t',eachVirus,str(n)+'/'+str(len(testList)))
        length = int(dicVirusSeqLength[eachVirus])
        if length >12500:
            model = modelFullLength
        elif length>7500 and length<=12500:
            model = model10k
        elif length>4000 and length<=7500:
            model = model5k
        elif length>2000 and length<=4000:
            model = model3k
        elif length>4 and length<=2000:
            model = model1k
        else:
            continue
        
        virusParameter = testVirusAll.loc[eachVirus]
        temp1 = hostAll.sub((virusParameter), axis=1)
        temp2 = temp1.sub((temp1), axis=1)
        dataVirusMinusAllHost = temp2.sub((temp1))
        
        pre = model.score_samples(dataVirusMinusAllHost)
        LIST = list(zip(listHostName,pre))
        maxScoreList = sorted(LIST,key=lambda x:float(x[1]),reverse=True)[:30]
        
        for eachHostName,eachScore in maxScoreList:
            if eachScore == maxScoreList[0][1]:
                fileOut.write( str(eachVirus) +'\t' + str(eachScore) + '\t' + str(eachHostName)  + '\n')
        
        #outputAll
        tempMax = 0.0
        fileOutAll.write(eachVirus)
        for i in range(0,len(pre)):
            fileOutAll.write(','+str(pre[i]))
        fileOutAll.write('\n')
    fileOut.close()
    fileOutAll.close()


def main():
    import pandas as pd
    import numpy  as np
    import countKmer
    import datetime,os,sys,getopt

    
    ###default setting
    virusFastaFileDir = ''
    outFileDir = './exampleOutput/'
    bacteriaKmerDir = ''
    bacteriaKmerName = ''
    scriptPath = sys.path[0]+'/'
    print(scriptPath)
    
    opts, args = getopt.getopt(sys.argv[1:], "hv:o:d:n:",["help","virusFastaFileDir=","outFileDir=","bacteriaKmerDir=","bacteriaKmerName="])
    for op, value in opts:
        if   op == "--virusFastaFileDir" or op == "-v":
            virusFastaFileDir = value+'/'
        elif op == "--outFileDir"  or op == "-o":
            outFileDir = value+'/'
        elif op == "--bacteriaKmerDir"  or op == "-d":
            bacteriaKmerDir = value+'/'
        elif op == "--bacteriaKmerName"  or op == "-n":
            bacteriaKmerName = value
        elif op == "--help" or op == "-h":
            print('Step 1: calculate the *k*-mer frequency of the host\n')
            print('    python3 countKmer.py --fastaFileDir  ./exampleHostGenome --kmerFileDir ./exampleOutput --kmerName HostKmer  --coreNum -1\n')
            print('Or use the simplify command\n')
            print('    python3 countKmer.py -f ./exampleHostGenome -d ./exampleOutput -n HostKmer -c -1\n')
            print('--fastaFileDir or -f: The fasta file of prokaryotic genome sequences, one genome per file.')
            print('--kmerFileDir or -d: The path of prokaryotic *k*-mer file.')
            print('--kmerName or -n: The name of prokaryotic *k*-mer file.\n')
            print('--coreNum or -c: The number of cores used in *k*-mer calculation. -1 represents the use of all cores\n')
            print('K-mer file of 60,105 prokaryotic genomes is saved in current folder and named hostKmer_60105_kmer4.tar.gz')
            print('Users can directly use the *k*-mer file to run the step 2 after decompression')
            print('The taxonomy information of the 60,105 genomes is saved in /interactionTable/MARGE_PAIR_TAX.xls')

            print('\n\n-------------------------------------------------\n\n')
            print('Step 2: predict the infection relationship between the virus and the host\n')
            print('    python3 PHP.py --virusFastaFileDir ./exampleVirusGenome  --outFileDir ./exampleOutput  --bacteriaKmerDir ./exampleOutput  --bacteriaKmerName HostKmer\n')
            print('Or use the simplify command\n')
            print('    python3 PHP.py -v ./exampleVirusGenome  -o ./exampleOutput  -d ./exampleOutput  -n HostKmer\n')
            print('--virusFastaFileDir or -v: The fasta file of query virus sequences, one virus genome per file.')
            print('--outFileDir or -o: The path of temp files and result files.')
            print('--bacteriaKmerDir or -d: The path of prokaryotic *k*-mer file.')
            print('--bacteriaKmerName or -n: The name of prokaryotic *k*-mer file.')
            return

    if not os.path.exists(outFileDir):
        os.mkdir(outFileDir)
    if (not os.path.exists(virusFastaFileDir)) or virusFastaFileDir == '':
        print('please input a correct virusFastaFileDir.\ndone.')
        return
    if (not os.path.exists(bacteriaKmerDir)) or bacteriaKmerDir == '':
        print('please input a correct bacteriaKmerDir.\ndone.')
        return
    if (not os.path.exists(bacteriaKmerDir+bacteriaKmerName)) or bacteriaKmerName == '':
        print(bacteriaKmerName+' is not exist in '+bacteriaKmerDir+'.\ndone.')
        return


    dicVirusSeqLength = countKmer.getKmer(virusFastaFileDir,outFileDir,'virusKmer',-1)
    predictVirusHost(scriptPath,bacteriaKmerDir,bacteriaKmerName,outFileDir,dicVirusSeqLength)


if __name__ == '__main__':
    main()
    #python3 countKmer.py --fastaFileDir  ./exampleHostGenome --kmerFileDir ./exampleOutput --kmerName HostKmer --coreNum -1
    #python3 countKmer.py -f  ./exampleHostGenome -d ./exampleOutput -n HostKmer -c -1
    
    
    #python3 PHP.py --virusFastaFileDir ./exampleVirusGenome  --outFileDir ./exampleOutput  --bacteriaKmerDir ./exampleOutput  --bacteriaKmerName HostKmer
    #python3 PHP.py -v ./exampleVirusGenome  -o ./exampleOutput  -d ./exampleOutput  -n HostKmer
    
    
    
    
    
    
    
    

