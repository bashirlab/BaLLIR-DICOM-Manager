from tools.ReadDicom import *
from tools.ReadDicomMask import *
from tools.shortcuts import *
from tools.manage_dicom import *
from tools.ReadPair import *

import copy
import imageio
import matplotlib

class ReadPairNifti(ReadPair):
    
    def __init__(self, scan, mask, colors = ['#06b70c', '#2c2cc9', '#eaf915'], transparency = 0.3, preprocess_arr = False):
        
        
        self.scan = scan
        self.scan.arr = np.flip(np.flip(np.swapaxes(scan.get_fdata(), 0,1), 2), 0) # np.flip(np.swapaxes(self.scan.arr, 0,1), 0)
        if preprocess_arr:
            self.scan.arr = np.clip(self.scan.arr, np.mean(self.scan.arr)- (3*np.std(self.scan.arr)), np.mean(self.scan.arr) + (4*np.std(self.scan.arr)))
        self.scan.spacing = self.scan.header.get_zooms()
        self.scan.range = [self.scan.spacing[0] * self.scan.arr.shape[0], self.scan.spacing[1] * self.scan.arr.shape[1], self.scan.spacing[2] * self.scan.arr.shape[2]]
        self.mask = mask
        self.mask.arr = np.flip(np.flip(np.swapaxes(mask.get_fdata(), 0, 1), 2), 0)
            
#         rgb_colors = [tuple(int(color.strip('#')[i:i+2], 16) for i in (0, 2, 4)) for color in colors]
#         rgb = np.copy(self.scan.arr)
#         rgb = normalize_arr(rgb.astype('float64'), norm_range = [0, 255])
#         rgb = np.array([np.copy(rgb) for i in range(3)]) #build RGB
#         rgb_orig = np.copy(rgb)
#         for i in range(3): rgb[i,...][self.mask.arr > 0] *= (1-transparency)
#         for i in range(3): rgb[i,...][self.mask.arr > 0] += rgb_colors[1][i] * transparency #color in mask

        mask_vals = list(np.unique(mask.arr)); mask_vals.remove(0.0)
        if colors == 'random': colors = ["#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)]) for i in range(len(mask_vals))]                                           
        rgb_colors = [tuple(int(color.strip('#')[i:i+2], 16) for i in (0, 2, 4)) for color in colors]
        
        
        rgb = np.copy(self.scan.arr)
        rgb = normalize_arr(rgb.astype('float64'), norm_range = [0, 255])
        rgb = np.array([np.copy(rgb) for i in range(3)]) #build RGB
        rgb_orig = np.copy(rgb)
        for i in range(3): rgb[i,...][self.mask.arr > 0] *= (1-transparency)
        
        print(rgb.shape)
        for i in range(3):
            for mask_num, mask_val in enumerate(mask_vals):
                rgb[i,...][self.mask.arr == mask_val] = rgb_colors[mask_num][i] * transparency

#         if rotate: rgb = np.rot90(rgb, axes = (1,2)) 
#         if rotate: rgb_orig = np.rot90(rgb_orig, axes = (1,2)) 

        rgb_cat = np.concatenate((rgb_orig, rgb), axis = 2); rgb_cat = np.swapaxes(rgb_cat, 0, 3)
        
        self.rgb = rgb
        self.orig = rgb_orig
        self.cat = (rgb_cat).astype(np.uint8)
        self.colors = colors
        self.volume = f'{np.product(scan.header.get_zooms()) * ((np.sum(mask.get_fdata())/np.amax(mask.get_fdata()))/1000)} cm^3'