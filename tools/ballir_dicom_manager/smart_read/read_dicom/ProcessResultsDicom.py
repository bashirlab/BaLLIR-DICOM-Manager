from tools.ReadScan import *
from tools.ReadDicom import *
from tools.ReadPairNifti import *
from tools.manage_dicom import *
from tools.shortcuts import *
from tools.manage_dicom import *

from ast import literal_eval
from copy import deepcopy
import xmltodict
from skimage.draw import polygon
from scipy import interpolate
from scipy.ndimage import binary_erosion


class ProcessResultsDicom(ReadPair):
    
    def __init__(self, scan, mask_gt, mask_alg, colors = ['#06b70c', '#2c2cc9', '#eaf915'], transparency = 0.3, outline = False, legend_size = False, _middle_slice = False, preprocess_arr = False):
        
        '''
        
        '''
        
        super().__init__(scan = scan, mask = mask_gt, colors = colors, transparency = transparency)
            
        self.mask_alg = mask_alg
            
#         self.mask_alg.arr = np.flip(np.flip(np.swapaxes(mask_alg.get_fdata(), 0, 1), 2), 0)
        
        if _middle_slice:
            middle_slice, range_mask = get_middle_slices(self.mask.arr, axis = 2, num_slices = _middle_slice)
            self.scan.arr = self.scan.arr[..., middle_slice]
            self.mask.arr = self.mask.arr[..., middle_slice]
            self.mask_alg.arr = self.mask_alg.arr[..., middle_slice]
            if _middle_slice == 1:
                self.scan.arr = self.scan.arr[...,np.newaxis]#np.concatenate([self.scan.arr,self.scan.arr], axis = )
                self.mask.arr = self.mask.arr[...,np.newaxis]
                self.mask_alg.arr = self.mask_alg.arr[...,np.newaxis]
                
        
            
        
        self.legend_size = legend_size
        if preprocess_arr:
            self.scan.arr = np.clip(self.scan.arr, np.mean(self.scan.arr)- (3*np.std(self.scan.arr)), np.mean(self.scan.arr) + (4*np.std(self.scan.arr)))
        
        if outline:     
            mask_gt_erode = np.copy(self.mask.arr)
            for arr_slice in range(self.mask.arr.shape[2]):
                mask_gt_erode[..., arr_slice] = binary_erosion(self.mask.arr[..., arr_slice], structure = np.ones((outline, outline)))
            self.mask.arr = self.mask.arr - mask_gt_erode
            
            mask_alg_erode = np.copy(self.mask_alg.arr)
            for arr_slice in range(self.mask_alg.arr.shape[2]):
                mask_alg_erode[..., arr_slice] = binary_erosion(self.mask_alg.arr[..., arr_slice], structure = np.ones((outline, outline)))
            self.mask_alg.arr = self.mask_alg.arr - mask_alg_erode
            
            
        rgb_colors = [tuple(int(color.strip('#')[i:i+2], 16) for i in (0, 2, 4)) for color in colors]
        rgb = np.copy(self.scan.arr)
        rgb = normalize_arr(rgb.astype('float64'), norm_range = [0, 255])
        rgb = np.array([np.copy(rgb) for i in range(3)]) #build RGB
        rgb_orig = np.copy(rgb)
        
        # OVERLAP GROUND TRUTH AND SEGMENTATION
        true_positive = self.mask.arr * self.mask_alg.arr; true_positive[true_positive < 0] = 0; true_positive[true_positive > 0] = 1
        self.true_positive = true_positive
        # ALGORITHM SEGMENTATION ONLY
        false_positive = self.mask_alg.arr - self.mask.arr; false_positive[false_positive < 0] = 0; false_positive[false_positive > 0] = 1
        self.false_positive = false_positive
        # ALGORITHM MISSES
        false_negative = self.mask.arr - self.mask_alg.arr; false_negative[false_negative < 0] = 0; false_negative[false_negative > 0] = 1
        self.false_negative = false_negative
        mask_all =  self.false_negative + self.true_positive + self.false_positive; false_negative[false_negative < 0] = 0; true_positive[true_positive > 0] = 1
        self.mask_all = mask_all; mask_all[mask_all < 0] = 0#; mask_all[mask_all > 0] = 1
        
        
        mask1 = np.copy(self.mask_alg.arr)
        mask1[mask1 < 0] = 0; mask1[mask1 > 1] = 1
        mask2 = np.copy(self.mask.arr)
        mask2[mask2 < 0] = 0; mask2[mask2 > 1] = 1
        self.dice_score = float('{0:.4f}'.format(round(2*np.sum(self.true_positive)/(np.sum(mask1) + np.sum(mask2)), 4)))
        self.iou = float('{0:.4f}'.format(round(np.sum(self.true_positive)/np.sum(self.mask_all), 4)))
        
        for i in range(3): rgb[i,...][mask_all > 0] *= (1-transparency)
        for num_mask, sub_mask in enumerate([self.true_positive, self.false_negative, self.false_positive]):
            for i in range(3): rgb[i,...][sub_mask > 0] += rgb_colors[num_mask][i] * transparency #color in mask
                
    #         if rotate: rgb = np.rot90(rgb, axes = (1,2)) 
    #         if rotate: rgb_orig = np.rot90(rgb_orig, axes = (1,2)) 

        rgb_cat = np.concatenate((rgb_orig, rgb), axis = 2); rgb_cat = np.swapaxes(rgb_cat, 0, 3)

        self.rgb = rgb
        self.orig = rgb_orig
        self.cat = (rgb_cat).astype(np.uint8)
        
        

    