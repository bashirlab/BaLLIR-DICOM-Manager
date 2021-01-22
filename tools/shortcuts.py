# standard imports 

import os
import numpy as np
import matplotlib.pyplot as plt
import shutil
import zipfile
import sys

# custom imports


def normalizeArr(arr, norm_range = [0, 1]):  #fix so works with negative
    
    norm = (norm_range[1]*(arr - np.amin(arr))/np.ptp(arr)) 
    
    return norm



def removeMac(dir_mac):
    
    list_ds = glob(os.path.join(dir_mac, '**/*.DS_Store'), recursive = True)
    for file in list_ds: os.remove(file) 
        
    list_os = glob(os.path.join(dir_mac, '**/__MACOSX'), recursive = True)
    for file in list_os: shutil.rmtree(file) 
    
    return



def unzipRec(dir_zip, remove_zips = False, remove_mac = True): #add remove zip files option, add removeMac option
    
    zips_remain = True
    while zips_remain:
        
        list_glob = glob(os.path.join(dir_test, '**/*.zip'), recursive = True)
        list_unzipped = [file for file in list_glob if not os.path.exists(file.split('.zip')[0])]
        
        for file_zip in list_unzipped:
            with zipfile.ZipFile(file_zip, 'r') as zip_ref:
                zip_ref.extractall(file_zip.split('.zip')[0])
          
        list_glob = glob(os.path.join(dir_test, '**/*.zip'), recursive = True)
        list_unzipped = [file for file in list_glob if not os.path.exists(file.split('.zip')[0])]
        if len(list_unzipped) == 0 : zips_remain = False 
            
    if remove_mac: removeMac(dir_zip)
    
    return



def buildDir(dir_check, overwrite = False):
    
    if overwrite and os.path.exists(dir_check):
        shutil.rmtree(dir_check)
    
    if not os.path.exists(dir_check):
        os.makedirs(dir_check, exist_ok = True)
#     else:
#         print(dir_check, 'ERROR: directory exists, set overwrite arg to True')
        
    return




def histo(arr, bins = 10, threshold = False, title = False):
    #arr
    #bins
    #threshold = [min, max]
    #title
    # -- add min, max for X and Y axis
    
    vect = np.ndarray.flatten(arr)
    
    if threshold:
        vect = vect[vect>threshold[0]]; vect = vect[vect<threshold[1]]
    if not title:
        title = "histogram"
    plt.hist(vect, bins = bins)
    plt.title(title) 
    plt.show()
    
    return

def unq(list_full):
    
    list_unq = set(list_full)
    list_unq = list(list_unq)
    
    return list_unq

def head(list_inp, len_head = 5):
    
    print(*list_inp[:len_head], sep = '\n')
    
    return

def addLib():
    
    
    
    return
