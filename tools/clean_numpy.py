#standard imports
import numpy as np

#custom imports



def normalizeNumpy(arr, norm_range = [0, 1]):  #fix so works with negative
    
    norm = (norm_range[1]*(arr - np.amin(arr))/np.ptp(arr)) 
    
    return norm
