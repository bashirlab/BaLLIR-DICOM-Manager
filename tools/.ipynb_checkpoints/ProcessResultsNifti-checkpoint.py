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



class ProcessResultsNifti(ReadPairNifti):
    
    def __init__(self, scan, mask, ground_truth, colors = ['#06b70c', '#2c2cc9', '#eaf915'], transparency = 0.3, outline = False, legend_size = False):
        
        super().__init__(scan = scan, mask = mask, colors = colors, transparency = transparency)
        
        self.ground_truth = ground_truth
        self.ground_truth.arr = np.flip(np.flip(np.swapaxes(ground_truth.get_fdata(), 0, 1), 2), 0)
        self.legend_size = legend_size
        
        if outline:     
            mask_erode = np.copy(mask.arr)
            for arr_slice in range(mask.arr.shape[2]):
                mask_erode[..., arr_slice] = scipy.ndimage.binary_erosion(mask.arr[..., arr_slice], structure = np.ones((outline, outline)))
            mask.arr = mask.arr - mask_erode
            
            gt_erode = np.copy(self.ground_truth.arr)
            for arr_slice in range(self.ground_truth.arr.shape[2]):
                gt_erode[..., arr_slice] = scipy.ndimage.binary_erosion(self.ground_truth.arr[..., arr_slice], structure = np.ones((outline, outline)))
            self.ground_truth.arr = self.ground_truth.arr - gt_erode
            
            
        rgb_colors = [tuple(int(color.strip('#')[i:i+2], 16) for i in (0, 2, 4)) for color in colors]
        rgb = np.copy(self.scan.arr)
        rgb = normalize_arr(rgb.astype('float64'), norm_range = [0, 255])
        rgb = np.array([np.copy(rgb) for i in range(3)]) #build RGB
        rgb_orig = np.copy(rgb)
        
        
        true_positive = self.ground_truth.arr * self.mask.arr; true_positive[true_positive < 0] = 0; true_positive[true_positive > 0] = 1
        self.true_positive = true_positive
        false_positive = self.mask.arr - self.ground_truth.arr; false_positive[false_positive < 0] = 0; false_positive[false_positive > 0] = 1
        self.false_positive = false_positive
        false_negative = self.ground_truth.arr - self.mask.arr; false_negative[false_negative < 0] = 0; false_negative[false_negative > 0] = 1
        self.false_negative = false_negative
        mask_all =  self.false_negative + self.true_positive + self.false_positive; false_negative[false_negative < 0] = 0; true_positive[true_positive > 0] = 1
        self.mask_all = mask_all; mask_all[mask_all < 0] = 0; mask_all[mask_all > 0] = 1
        
        self.dice_score = float('{0:.4f}'.format(round(np.sum(self.true_positive)/np.sum(self.mask_all), 4)))
        
        for i in range(3): rgb[i,...][mask_all > 0] *= (1-transparency)
        for num_mask, sub_mask in enumerate([self.true_positive, self.false_negative, self.false_positive]):
            for i in range(3): rgb[i,...][sub_mask > 0] += rgb_colors[num_mask][i] * transparency #color in mask
                
    #         if rotate: rgb = np.rot90(rgb, axes = (1,2)) 
    #         if rotate: rgb_orig = np.rot90(rgb_orig, axes = (1,2)) 

        rgb_cat = np.concatenate((rgb_orig, rgb), axis = 2); rgb_cat = np.swapaxes(rgb_cat, 0, 3)

        self.rgb = rgb
        self.orig = rgb_orig
        self.cat = (rgb_cat).astype(np.uint8)
        
        
    def orthoview(self):
        
        #TRANSVERSE
        transverse_scan = np.copy(self.orig[..., int(self.orig.shape[-1]/2)])
        transverse_rgb = np.copy(self.rgb[..., int(self.orig.shape[-1]/2)])
        transverse_scan = np.swapaxes(transverse_scan, 0, 2); transverse_scan = np.rot90(transverse_scan, axes = (1,0)); transverse_scan = np.flip(transverse_scan, 1)
        transverse_rgb = np.swapaxes(transverse_rgb, 0, 2); transverse_rgb = np.rot90(transverse_rgb, axes = (1,0)); transverse_rgb = np.flip(transverse_rgb, 1)
        transverse = np.concatenate((transverse_scan, transverse_rgb), axis = 1)
        transverse = normalize_arr(transverse, [0, 1])

        #CORONAL
        coronal_scan = np.copy(self.orig[:, int(self.orig.shape[1]/2), :, :])
        coronal_rgb = np.copy(self.rgb[:, int(self.orig.shape[1]/2), :, :])
        coronal_scan = np.swapaxes(coronal_scan, 0, 2)
        coronal_rgb = np.swapaxes(coronal_rgb, 0, 2)
        coronal = np.concatenate((coronal_scan, coronal_rgb), axis = 1)
        coronal = cv2.resize(coronal, dsize = (int(2 * self.scan.range[0]), int(self.scan.range[2])), interpolation = cv2.INTER_CUBIC)
        coronal = normalize_arr(coronal, [0,1])

        #SAGITTAL 
        sagittal_scan = np.copy(self.orig[:, :, int(self.orig.shape[2]/2), :])
        sagittal_rgb = np.copy(self.rgb[:, :, int(self.orig.shape[2]/2), :])
        sagittal_scan = np.swapaxes(sagittal_scan, 0, 2); sagittal_scan = np.flip(sagittal_scan, 1) 
        sagittal_rgb = np.swapaxes(sagittal_rgb, 0, 2); sagittal_rgb = np.flip(sagittal_rgb, 1)
        sagittal = np.concatenate((sagittal_scan, sagittal_rgb), axis = 1)
        sagittal = cv2.resize(sagittal, dsize = (int(2 * self.scan.range[1]), int(self.scan.range[2])), interpolation = cv2.INTER_CUBIC)
        sagittal = normalize_arr(sagittal, [0,1])
        
        self.transverse = transverse
        self.coronal = coronal
        self.sagittal = sagittal

#         plot_res(list_img = [transverse, coronal, sagittal], mag = 1.0, row_col = [3, 1], legend = [['Ground Truth', self.colors[0]],['Ground Truth', self.colors[0]],['Ground Truth', self.colors[0]]])
        if self.legend_size:
            legend_ = [['TP: Overlap', 'FN: Ground Truth', 'FP: Segmentation Mask'], res_nib.colors]
        else: 
            legend_ = False
        plot_res(list_img = [transverse, coronal, sagittal], mag = 1.0, row_col = [3, 1], legend = legend_, legend_size = self.legend_size)



    