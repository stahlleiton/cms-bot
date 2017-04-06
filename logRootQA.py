#!/usr/bin/env python

from os import listdir
from os.path import isfile, join
import os
import subprocess
import sys

def getFiles(d,ending):
    return [os.path.join(dp, f) for dp, dn, filenames in os.walk(d) for f in filenames if os.path.splitext(f)[1] == '.'+ending]
#    return  [ f for f in listdir(d) if isfile(join(d,f)) ]

def getCommonFiles(d1,d2,ending):
    l1=getFiles(d1,ending)
    l2=getFiles(d2,ending)
    common=[]
    for l in l1:
        lT=l[len(d1):]
        if 'step' not in lT or 'runall' in lT or 'dasquery' in lT: continue
        if d2+lT in l2:
            common.append(lT)
    return common

def checkLines(l1,l2):
    lines=0
    for l in open(l2):
        lines=lines+1
    for l in open(l1):
        lines=lines-1
    if lines>0:
        print "You added "+str(lines)+" to "+l2
    if lines<0:
        print "You removed "+str(-1*lines)+" to "+l2
        
    return lines

def filteredLines(f):
    retval={}
    for l in open(f):
        sl=l.strip()
        if 'P       Y      T    H   H  III  A   A' in l:continue
        # look for and remove timestamps
        if '-' in l and ':' in l:
            sp=l.strip().split()
            
            ds=[]
            for i in range(0,len(sp)-1):
                if sp[i].count('-')==2 and sp[i+1].count(':')==2 and '-20' in sp[i]: 
                    ds.append(sp[i]) #its a date
                    ds.append(sp[i+1]) #its a date
            if len(ds)!=0:
                sp2=l.strip().split(' ')
                sp3=[]
                for i in range(0,len(sp2)):
                    if sp2[i] not in ds:
                        sp3.append(sp2[i])
                sl=' '.join(sp3)
        retval[sl]=1
    return retval

def getRelevantDiff(l1,l2,maxInFile=20):
    nPrintTot=0
    filt1=filteredLines(l1)
    filt2=filteredLines(l2)

    keys1=filt1.keys()
    keys2=filt2.keys()
    newIn1=[]
    newIn2=[]
    for k in keys1:
        if k not in filt2:
            newIn1.append(k)
    for k in keys2:
        if k not in filt1:
            newIn2.append(k)

    if len(newIn1)>0 or len(newIn2)>0:
        print ''
        print len(newIn1),'Lines only in',l1
        nPrint=0
        for l in newIn1: 
            nPrint=nPrint+1
            if nPrint>maxInFile: break
            print '  ',l
        nPrintTot=nPrint
        print len(newIn2),'Lines only in',l2
        nPrint=0
        for l in newIn2: 
            nPrint=nPrint+1
            if nPrint>maxInFile: break
            print '  ',l
        nPrintTot=nPrintTot+nPrint
    return nPrintTot

import subprocess as sub

def runCommand(c):
    p=sub.Popen(c,stdout=sub.PIPE,stderr=sub.PIPE)
    output=p.communicate()
    return output

def checkEventContent(r1,r2):
    retVal=True

    output1=runCommand(['ls','-l',r1])
    output2=runCommand(['ls','-l',r2])
    s1=output1[0].split()[4]
    s2=output2[0].split()[4]
    if abs(float(s2)-float(s1))>0.1*float(s1):
        print "Big output file size change?",s1,s2
        retVal=False

    output1=runCommand(['edmEventSize','-v',r1])
    output2=runCommand(['edmEventSize','-v',r2])

    if 'contains no' in output1[1] and 'contains no' in output2[1]:
        w=1
    else:
        sp=output1[0].split('\n')
        p1=[]
        for p in sp:
            if len(p.split())>0:
                p1.append(p.split()[0])
        sp=output2[0].split('\n')
        p2=[]
        for p in sp:
            if len(p.split())>0:
                p2.append(p.split()[0])

        common=[]    
        for p in p1:
            if p in p2: common.append(p)
        if len(common)!=len(p1) or len(common)!=len(p2):
            print 'Change in products found in',r1
            for p in p1:
                if p not in common: print '    Product missing '+p
            for p in p2:
                if p not in common: print '    Product added '+p
            retVal=False    
    return retVal

def summaryJR(jrDir):
    nDiff=0
    print jrDir
    dirs=[]
    for root, dirs, files in os.walk(jrDir):
        break

    for d in dirs:
        diffs=getFiles(root+'/'+d,'png')
        if len(diffs)>0:
            print 'JR results differ',len(diffs),d
            nDiff=nDiff+len(diffs)
    return nDiff

def parseNum(s):
    return int(s[1:-1].split('/')[0])
    

def summaryComp(compDir):
    print compDir
    files=[]
    for root, dirs, files in os.walk(compDir):
        break
    comps=[]
    for f in files:
        if 'log' in f[-3:]:
            comps.append(root+'/'+f)

    results=[0,0,0,0,0,0,0]

    for comp in comps:
        loc=[0,0,0,0,0,0]
        for l in open(comp):
            if '- summary of' in l: loc[0]=int(l.split()[3])
            if 'o Failiures:' in l: loc[1]=parseNum(l.split()[3])
            if 'o Nulls:' in l: loc[2]=parseNum(l.split()[3])
            if 'o Successes:' in l: loc[3]=parseNum(l.split()[3])
            if 'o Skipped:' in l: loc[4]=parseNum(l.split()[3])
            if 'o Missing objects:' in l: loc[5]=int(l.split()[3])
        print 'Histogram comparison details',comp,loc
        for i in range(0,5):
            results[i]=results[i]+loc[i]
        results[6]=results[6]+1
    return results


##########################################
#
#
#
qaIssues=False

#https://cmssdt.cern.ch/SDT/jenkins-artifacts/baseLineComparisons/CMSSW_9_0_X_2017-03-22-1100+18042/18957/validateJR/
baseDir='../170322/orig'
testDir='../170322/new'
jrDir='../170322/jrlogs/validateJR'
compDir='../170322/compDir'

if len(sys.argv)==5:
    baseDir=sys.argv[1]
    testDir=sys.argv[2]
    jrDir=sys.argv[3]
    compDir=sys.argv[4]

if baseDir[-1]=='/':
    baseDir=baseDir[:-1]
if testDir[-1]=='/':
    testDir=testDir[:-1]
if jrDir[-1]=='/':
    jrDir=jrDir[:-1]
if compDir[-1]=='/':
    compDir=jrDir[:-1]

commonLogs=getCommonFiles(baseDir,testDir,'log')

#### check the printouts
lines=0
lChanges=False
nLog=0
nPrintTot=0
stopPrint=0
for l in commonLogs:
    lCount=checkLines(baseDir+l,testDir+l)
    lines=lines+lCount
    if lChanges!=0:
        lChanges=True
    if nPrintTot<1000:
        nprint=getRelevantDiff(baseDir+l,testDir+l)
        nPrintTot=nPrintTot+nprint
    else:
        if stopPrint==0:
            print 'Skipping further diff comparisons. Too many diffs'
            stopPrint=1
    nLog=nLog+1    

if lines >0 :
    print "SUMMARY You potentially added "+str(lines)+" lines to the logs" 
else:
    print "SUMMARY No significant changes to the logs found"
if lChanges:
    qaIssues=True
print '\n'
#### compare edmEventSize on each to look for new missing candidates
commonRoots=getCommonFiles(baseDir,testDir,'root')
sameEvts=True
nRoot=0
for r in commonRoots:
    if '50' in r or '25' in r:
        sameEvts=sameEvts and checkEventContent(baseDir+r,testDir+r)
        nRoot=nRoot+1
if not sameEvts:
    qaIssues=True
    print 'SUMMARY ROOTFileChecks: Some differences in event products or their sizes found'

print '\n'
# now check the JR comparisons for differences
nDiff=summaryJR(jrDir)
print 'SUMMARY Reco comparison results:',nDiff,'differences found in the comparisons' 
print '\n'

compSummary=summaryComp(compDir)
print 'SUMMARY DQMHistoTests: Total files compared:',compSummary[6]
print 'SUMMARY DQMHistoTests: Total histograms compared:',compSummary[0]
print 'SUMMARY DQMHistoTests: Total failures:',compSummary[1]
print 'SUMMARY DQMHistoTests: Total nulls:',compSummary[2]
print 'SUMMARY DQMHistoTests: Total successes:',compSummary[3]
print 'SUMMARY DQMHistoTests: Total skipped:',compSummary[4]
print 'SUMMARY DQMHistoTests: Total Missing objects:',compSummary[5]


#### conclude
print "SUMMARY Checked",nLog,"log files,",nRoot,"edm output root files,",compSummary[6],"DQM output files"
if not qaIssues:
    print "No potential problems in log/root QA checks!"
