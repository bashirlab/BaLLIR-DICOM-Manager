# standard imports 

import os
import numpy as np
import matplotlib.pyplot as plt
import shutil

# custom imports



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
