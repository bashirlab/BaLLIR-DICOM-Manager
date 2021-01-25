from tools.ReadScan import *
from tools.manage_dicom import *
from tools.shortcuts import *

from glob import glob
import numpy as np
import pydicom as dcm
import os
import cv2
from matplotlib import pyplot as plt





# split files by tag? --return multiple scans? -- different function for splitting files by series/some other tag.. 
# add patient position rounding function
# 


class ReadDicom(ReadScan):
    
    def __init__(self, filename, filter_tags = False, window_level = False, clip_vals = False, sort_by = False, decompress = True, flip_arr = False, fix_dicoms = False):
        
        # add decompress option... decompress self.scan, save self.scan with new PixelData and TransferSyntaxUID...? or other decompress() option?
        # have clip_val edit arr 
        # change PixelData to arr 
        
        
        """
        filename [string]: directory location of dicom files
        filter_tags [dictionary]: tag/value pairs, 'max' as value selects most frequent unique tag
        window_level[bool]: True conducts window/level operation based on WindowCenter/WindowWidth/RescaleSlope/RescaleIntercept tags or defaults
        clip_vals[list]: min and max values to clip pixel array (e.g., [-250, 200])
        sort_by[string]: dicom tag used to sort array (e.g., sort_by = 'SliceLocation')
        sort_by[dict]: dicom tag and indexused to sort array (e.g., sort_by = {'ImagePositionPatient': 2})
        decompress[bool]: set TransferSyntaxUID to LittleEndianExplicit, array as type int16
        """
        
        #add something to check for inconsistencies in dicom files...slice thickness, etc., 
        list_glob = glob(os.path.join(filename, '**/*.dcm'), recursive = True); list_glob.sort(); #list_glob.reverse()
        scan = [dcm.dcmread(file) for file in list_glob]
        if fix_dicoms: 
            scan = fixDicoms(scan)
        if clip_vals:
            scan = clipVals(scan, clip_vals)
        
        
        #edit so if not filter it reads the full files, otherwise it stops before pixel values, then reads pixel values after filtering
        if filter_tags:
            dict_tags, dict_max = check_tags(scan, filter_tags)
            self.dict_tags = dict_tags
            self.dict_max = dict_max
            for key, value in filter_tags.items():
                if value == 'max':
                    scan = [file for file in scan if getattr(file, key) == dict_max[key]]
                else:
                    scan = [file for file in scan if getattr(file, key) == value]
                
        if sort_by:
            if type(sort_by) == str:
                list_sort = [getattr(file, sort_by) for file in scan]
            elif type(sort_by) == dict:
                (tag, ind), = sort_by.items()
                list_sort = [getattr(file, tag)[ind] for file in scan]
            else:
                print('ERROR: [sort_by] enter either string or dict type as arg')
            scan = [x for _, x in sorted(zip(list_sort, scan))]
        
        if not flip_arr:
            arr = np.array([file.pixel_array for file in scan]); arr = np.swapaxes(arr, 0, 2); arr = np.flip(arr, 1); arr = np.flip(arr, 2)
        else:
            arr = np.array([file.pixel_array for file in scan]); arr = np.swapaxes(arr, 0, 2); arr = np.flip(arr, 1); #arr = np.flip(arr, 2)
            
        
        window_center, window_width, rescale_intercept, rescale_slope = super().getWinLevAttr_dcm(scan[0])
        if window_level:
            arr = super().winLev(arr, window_center, window_width, rescale_intercept, rescale_slope)
            
        type_arr = arr.dtype
        
#         if clip_vals:
            
#             arr = np.clip(arr, clip_vals[0], clip_vals[1]).astype(type_arr)

        self.root_file = filename
        self.root_type = 'DICOM'
        self.decompress = decompress
        #self.scan_type = 'MR', 'CT', etc.
        self.scan = scan
        self.arr = arr
        self.length = arr.shape[2]
        self.spacing = scan[0].PixelSpacing; self.spacing.append(scan[0].SliceThickness)
        self.range = [self.spacing[0] * self.arr.shape[0], self.spacing[1] * self.arr.shape[1], self.spacing[2] * self.arr.shape[2]]
        self.window_width = window_width
        self.window_center = window_center
        self.rescale_slope = rescale_slope
        self.rescale_intercept = rescale_intercept
        self.flip = flip_arr
        

        
    def orthoview(self, windowLevel = False):
        
        transverse = self.arr[..., int(self.arr.shape[2]/2)]
        transverse = cv2.resize(transverse, dsize = (int(self.range[1]), int(self.range[0])), interpolation = cv2.INTER_CUBIC); transverse = np.rot90(transverse)
        transverse = normalizeArr(transverse, [0, 1])
        sagittal = self.arr[int(self.arr.shape[0]/2), ...]
        sagittal = cv2.resize(sagittal, dsize = (int(self.range[2]), int(self.range[0])), interpolation = cv2.INTER_CUBIC); sagittal = np.rot90(sagittal); sagittal = np.flip(sagittal, 0)
        sagittal = normalizeArr(sagittal, [0, 1])
        coronal = self.arr[:, int(self.arr.shape[1]/2), :] 
        coronal = cv2.resize(coronal, dsize = (int(self.range[2]), int(self.range[1])), interpolation = cv2.INTER_CUBIC); coronal = np.rot90(coronal); coronal = np.flip(coronal, 0)
        coronal = normalizeArr(coronal, [0, 1])
        ims = [transverse, sagittal, coronal]
        
        plotRes([transverse, coronal, sagittal], mag = 1.0)
        
             
    def save_as(self, save_dir):
        
        buildDir(save_dir)
        
        if not self.flip:
            arr = np.swapaxes(self.arr, 0, 2); arr = np.flip(arr, 1); arr = np.flip(arr, 0); 
        else:
            print('ADD FIX')
        
        if self.decompress:
            self.scan = decompressDicoms(self.scan)
    
        for num, file in enumerate(self.scan):
#             file.PixelData = self.arr[num, ...].astype('int16').tobytes()     # update dicom files
            file.PixelData = arr[num, ...].astype('int16').tobytes()
            save_loc = os.path.join(save_dir, str(num).zfill(4) + '.dcm')
            buildDir(save_dir)
            file.save_as(save_loc)

        return
        