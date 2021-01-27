# standard imports 

import os
import numpy as np
import matplotlib.pyplot as plt
import shutil
import zipfile
import sys
from glob import glob
from tqdm import tqdm

from matplotlib.patches import Patch
from matplotlib.lines import Line2D


def unzipCheck(dir_unzip):
    
    list_zip = glob(os.path.join(dir_unzip, '**/*.zip'), recursive = True)
    list_unzip = [file for file in list_zip if not os.path.isdir(os.path.split(file)[0])]
    
    return list_zip, list_unzip



def normalizeArr(arr, norm_range = [0, 1]): 
    
    norm = (norm_range[1] - norm_range[0]) * ((arr - np.amin(arr))/(np.amax(arr) - np.amin(arr))) + norm_range[0]
    
    return norm



def printRange(arr):
    
    print('RANGE: ', np.amin(arr), ' : ', np.amax(arr))
    
    return



def plotRes(list_img, mag = 1, row_col = False, legend = False):
    
    '''
    list_img[list] = list of images to plot
    mag[int] = plot size
    row_col[list] = list of [row, col] for organization of plots
    legend[list] = nested list [[label1, color1], [label2, color2],...]
    '''
    
    if not row_col : row_col = [1, len(list_img)]
    fig = plt.figure(figsize = (15 * mag, 15 * mag))
    
    # add_subplot(nrows, ncols, index, **kwargs)
    for i in range(1, (1 + len(list_img))):
        ax = fig.add_subplot(row_col[0], row_col[1], i)
        if legend: 
            legend_elements = [Patch(facecolor = legend[i-1][1], edgecolor = legend[i-1][1], label = legend[i-1][0])]
            ax.legend(handles=legend_elements, loc='upper right', prop={'size': 15 * mag})

        plt.imshow((255*list_img[i - 1]).astype(np.uint8), cmap = 'gray')
    
    plt.show()
    


def normalizeArr(arr, norm_range = [0, 1]):  #fix so works with negative
    
    norm = (norm_range[1]*(arr - np.amin(arr))/np.ptp(arr)) 
    
    return norm



def removeMac(dir_mac):
    
    list_ds = glob(os.path.join(dir_mac, '**/*.DS_Store'), recursive = True)
    for file in list_ds: os.remove(file) 
        
    list_os = glob(os.path.join(dir_mac, '**/__MACOSX'), recursive = True)
    for file in list_os: shutil.rmtree(file) 
    
    return



# clean up a little so it does recursive stuff smarter -- descend into dir after unzipping
def unzipRec(file_zip, remove_zips = False, remove_mac = True): #add remove zip files option, add removeMac option
    
    if file_zip[-4:] == '.zip':
        with zipfile.ZipFile(file_zip, 'r') as zip_ref:
            zipto = file_zip.split('.zip')[0]
            while ' .' in zipto:
                zipto = '.'.join(zipto.split(' .')) 
            try:
                zip_ref.extractall(zipto)
            except:
                print('ERROR: unzip fail -- ', file_zip)
            for tail in os.listdir(zipto):
                dst = os.path.join(zipto, tail)
                while dst[-1] == ' ':
                    dst = dst[:-1]
                if not dst == os.path.join(zipto, tail):
                    print('ERROR: empty space on dir name -- ', zipto)
                    shutil.move(os.path.join(zipto, tail), src)
                    
        dir_zip = zipto
    elif os.path.isdir(file_zip):
        dir_zip = file_zip
    else:
        print('file_zip arg needs to be either .zip or a directory')
    
    list_error = []
    zips_remain = True
    while zips_remain:
        
        list_glob = glob(os.path.join(dir_zip, '**/*.zip'), recursive = True)
        list_unzipped = [file for file in list_glob if not os.path.exists(file.split('.zip')[0]) and not os.path.exists(''.join(file.split('.zip')[0].split(' ')))]
        
        for file_zip in list_unzipped:
            with zipfile.ZipFile(file_zip, 'r') as zip_ref:
                zipto = file_zip.split('.zip')[0]
                while ' .' in zipto:
                    zipto = '.'.join(zipto.split(' .')) 
                try:
                    zip_ref.extractall(zipto)
                except:
                    print('ERROR: unzip fail -- ', file_zip)
                    list_error.append(file_zip)
                    continue
                for tail in os.listdir(zipto):
                    dst = os.path.join(zipto, tail)
                    while dst[-1] == ' ':
                        dst = dst[:-1]
                    if not dst == os.path.join(zipto, tail):
                        print('ERROR: empty space on dir name -- ', zipto)
                        shutil.move(os.path.join(zipto, tail), src)
        list_glob = glob(os.path.join(dir_zip, '**/*.zip'), recursive = True)
        list_unzipped = [file for file in list_glob if not os.path.exists(file.split('.zip')[0]) and not os.path.exists(''.join(file.split('.zip')[0].split(' ')))]
        if len(list_unzipped) == 0 + len(list_error) : zips_remain = False 
            
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
