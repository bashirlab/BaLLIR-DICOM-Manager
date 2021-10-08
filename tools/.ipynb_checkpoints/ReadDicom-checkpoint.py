from tools.ReadScan import *
from tools.manage_dicom import *
from tools.shortcuts import *

from glob import glob
import numpy as np
import pydicom as dcm
import os
import cv2
from matplotlib import pyplot as plt



def closest(lst, K):
    return lst[min(range(len(lst)), key = lambda i: abs(lst[i]-K))]


def flatten(t):
    return [item for sublist in t for item in sublist]

# split files by tag? --return multiple scans? -- different function for splitting files by series/some other tag.. 
# add patient position rounding function
# 


class ReadDicom(ReadScan):
    
    def __init__(self, filename, filter_tags = False, window_level = False, hounsfield_units = False, clip_vals = False, sort_by = False, decompress = True, flip_arr = False, fix_dicoms_ = False, reverse_ = False, remove_duplicates = False, slice_locs = False):
        
        # add decompress option... decompress self.scan, save self.scan with new PixelData and TransferSyntaxUID...? or other decompress() option?
        # have clip_val edit arr 
        # change PixelData to arr 
        
        
        """
        filename [string]: directory location of dicom files
        filename [list]: list of full paths to dicom files
        filter_tags [dictionary]: tag/value pairs, 'max' as value selects most frequent unique tag
        window_level[bool]: True conducts window/level operation based on WindowCenter/WindowWidth/RescaleSlope/RescaleIntercept tags or defaults
        clip_vals[list]: min and max values to clip pixel array (e.g., [-250, 200])
        sort_by[string]: dicom tag used to sort array (e.g., sort_by = 'SliceLocation')
        sort_by[dict]: dicom tag and indexused to sort array (e.g., sort_by = {'ImagePositionPatient': 2})
        decompress[bool]: set TransferSyntaxUID to LittleEndianExplicit, array as type int16
        slice_locs[list]: will load in slices with closest SliceLocation to list items
        """
        
        #add something to check for inconsistencies in dicom files...slice thickness, etc., 
        if isinstance(filename, str):
            list_glob = glob(os.path.join(filename, '**/*.dcm'), recursive = True); list_glob.sort(); #list_glob.reverse()
        elif isinstance(filename, list):
            list_glob = filename.copy()
        else:
            print(f'MUST ENTER filename VARIABLE OF STRING TYPE (directory) or LIST TYPE (full paths), not {type(filename)}')
        
        if reverse_: list_glob.reverse()
        scan = [dcm.dcmread(file) for file in list_glob]
        
        print(len(scan))
        print(len(slice_locs))
        if slice_locs:
            scan_locs = [file.SliceLocation for file in scan]
            scan = [scan[scan_locs.index(closest(scan_locs, loc))] for loc in slice_locs]
        print(len(scan))
                
        if remove_duplicates:
            dict_series = {}
            dict_thickness = {}

            for scan_slice in scan:
                if not scan_slice.SeriesNumber in dict_series.keys():
                    dict_series[scan_slice.SeriesNumber] = [float(scan_slice.ImagePositionPatient[-1])]
                else:
                    dict_series[scan_slice.SeriesNumber].append(float(scan_slice.ImagePositionPatient[-1]))
                dict_thickness[scan_slice.SeriesNumber] = float(scan_slice.SliceThickness)
            if len(set(dict_thickness.values()))>1: print(f'INCONSISTENT SLICE THICKNESS: {set(dict_thickness.values())}')

            dict_range = {}
            for series, z_positions in dict_series.items():
                dict_range[series] = [np.amin(z_positions),np.amax(z_positions)]
            dict_range = dict(sorted(dict_range.items(), key=lambda item: item[1]))

            for key_num in range(1, len(dict_range.keys())):
                midway_point = np.mean( [dict_range[list(dict_range.keys())[key_num-1]][1], dict_range[list(dict_range.keys())[key_num]][0]]) + 1
#                 midway_point = closest(flatten(dict_range.values()), midway_point)
                dict_range[list(dict_range.keys())[key_num-1]][1] = midway_point + (0.5*scan[0].SliceThickness) - 1 
                dict_range[list(dict_range.keys())[key_num]][0] = midway_point - (0.5*scan[0].SliceThickness) + 1
#             print(dict_range)

#             scan = [file for file in scan if file.ImagePositionPatient[-1] >= dict_range[file.SeriesNumber][0] and file.ImagePositionPatient[-1] < dict_range[file.SeriesNumber][1]]
            scan = [file for file in scan if file.ImagePositionPatient[-1] >= dict_range[file.SeriesNumber][0] and file.ImagePositionPatient[-1] < dict_range[file.SeriesNumber][1]]


        
        if sort_by:
            try:
                if type(sort_by) == str:
                    list_sort = [getattr(file, sort_by) for file in scan]
                elif type(sort_by) == dict:
                    (tag, ind), = sort_by.items()
                    list_sort = [getattr(file, tag)[ind] for file in scan]
                else:
                    print('ERROR: [sort_by] enter either string or dict type as arg')
                scan = [x for (y,x) in sorted(zip(list_sort,scan), key=lambda pair: pair[0])]
            except Exception as e:
                print(f'ERROR sorting: {e}')
                
        if remove_duplicates:
            scan_fix = [scan[0]]
            for file_num in range(1,len(scan)):
                if abs(scan[file_num].ImagePositionPatient[2] - scan[file_num-1].ImagePositionPatient[2]) > (0.5*scan[0].SliceThickness):
                    scan_fix.append(scan[file_num])
            scan = scan_fix.copy()

        
        #edit so if not filter it reads the full files, otherwise it stops before pixel values, then reads pixel values after filtering
        if filter_tags:
            dict_tags, dict_max = check_tags(scan, filter_tags)
            self.dict_tags = dict_tags
            print(f'dict tags: {dict_tags}')
            self.dict_max = dict_max
            print(f'dict max: {dict_max}')
            for key, value in filter_tags.items():
                if value == 'max':
                    scan = [file for file in scan if getattr(file, key) == dict_max[key]]
                elif value == 'highest':
                    vals = [float(val.split('--')[-1]) for val in dict_tags.keys() if val.split('--')[0] == key]
#                     vals = [float(val.split('--')[-1]) for val in self.dict_tags.keys()]
                    scan = [file for file in scan if getattr(file, key) == max(vals)]
                else:
                    scan = [file for file in scan if getattr(file, key) == value]
        if fix_dicoms_: 
            scan = fix_dicoms(scan)
            
        
        # check for inconsistent shape size:
        arr_shapes = [file.pixel_array.shape for file in scan]
        unq_arr_shapes = list(set(arr_shapes))
        if len(unq_arr_shapes)>1: 
            print(f'INCONSISTENT ARRAYS')
            for arr_shape in unq_arr_shapes: print(f'\t{arr_shape}: {arr_shapes.count(arr_shape)}')
        
        # load pixel_array as numpy array
        arr = np.array([file.pixel_array for file in scan])
        arr = np.swapaxes(arr, 0, 2); arr = np.flip(arr, 1)
            
        if not flip_arr: arr = np.flip(arr, 2)    

        window_center, window_width, rescale_intercept, rescale_slope = super().getWinLevAttr_dcm(scan[0])
        if window_level:
            arr = super().winLev(arr, window_center, window_width, rescale_intercept, rescale_slope)

        if hounsfield_units:
            arr = hounsfield(arr, rescale_slope, rescale_intercept)
        
        if clip_vals:
            arr = clip_arr_vals(arr, clip_vals)
        
        type_arr = arr.dtype
        

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
        transverse = normalize_arr(transverse, [0, 1])
        sagittal = self.arr[int(self.arr.shape[0]/2), ...]
        sagittal = cv2.resize(sagittal, dsize = (int(self.range[2]), int(self.range[0])), interpolation = cv2.INTER_CUBIC); sagittal = np.rot90(sagittal); sagittal = np.flip(sagittal, 0)
        sagittal = normalize_arr(sagittal, [0, 1])
        coronal = self.arr[:, int(self.arr.shape[1]/2), :] 
        coronal = cv2.resize(coronal, dsize = (int(self.range[2]), int(self.range[1])), interpolation = cv2.INTER_CUBIC); coronal = np.rot90(coronal); coronal = np.flip(coronal, 0)
        coronal = normalize_arr(coronal, [0, 1])
        ims = [transverse, sagittal, coronal]
        
        plot_res([transverse, coronal, sagittal], mag = 1.0)
        
             
    def save_as(self, save_dir):
        
        build_dir(save_dir)
        
        if not self.flip:
            arr = np.swapaxes(self.arr, 0, 2); arr = np.flip(arr, 1); arr = np.flip(arr, 0); 
        else:
            arr = np.swapaxes(self.arr, 0, 2); arr = np.flip(arr, 1); arr = np.flip(arr, 0); 
            print('ADD FIX')
        
        if self.decompress:
            self.scan = decompress_dicoms(self.scan)
    
        for num, file in enumerate(self.scan):
#             file.PixelData = self.arr[num, ...].astype('int16').tobytes()     # update dicom files
            file.PixelData = arr[num, ...].astype('int16').tobytes()
            save_loc = os.path.join(save_dir, str(num).zfill(4) + '.dcm')
            build_dir(save_dir)
            file.save_as(save_loc)

        return