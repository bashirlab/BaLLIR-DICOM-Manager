from tools.ReadDicom import *
from tools.ReadDicomMask import *
from tools.shortcuts import *
from tools.manage_dicom import *
import copy
import imageio
import matplotlib


# start using *args and **kwargs
# start as GT, expand to include QC image stuff with TP and FP measurements 
# log errors, instances of slice_removal, etc.

#orthoview and save_as redundant



# SAVE QC numpy array as PNG in DIRECTORY

def save_rgb(rgb, dir_save):
    
    build_dir(dir_save)

    for i in range(rgb.shape[0]):
        loc_save = os.path.join(dir_save, str(i)+'.png')
        imageio.imwrite(loc_save, rgb[i,...])
    
    return


class ReadPair:
     
    def __init__(self, scan, mask, remove_empties = False, colors = ['#06b70c', '#2c2cc9', '#eaf915'], transparency = 0.3, rotate = True, sync_attributes = False, round_attributes = False, sync_slices = False):
        """
        
        sync_attributes[list]: list of attributes to copy from scan to mask 
        round_attributes[dict]: round attributes (keys) to decimal place (values)
        sync_slices[dict]: attribute and attribute's indices to set equal to first slice e.g. -- {'ImagePositionPatient': [0,1]}
        """
        self.scan = copy.deepcopy(scan)
        self.mask = copy.deepcopy(mask)
        
        if remove_empties:
            ind_empty = index_empty(self.mask.arr)
            if len(ind_empty) > 0:
                print('indEmpty: ', ind_empty)
                self.mask.arr = remove_empty(self.mask.arr, ind_empty)
                self.mask.scan = [file for num_file, file in enumerate(self.mask.scan) if num_file not in ind_empty]
                self.scan.arr = remove_empty(self.scan.arr, ind_empty)
                self.scan.scan = [file for num_file, file in enumerate(self.scan.scan) if num_file not in ind_empty]
               
                # fix ERROR: -- ConversionValidationError: SLICE_INCREMENT_INCONSISTENT
                slice_steps, slice_steps_unq, slice_locs, slice_locs_unq = step_sizes(self.scan.scan)
                print('slice steps 2: ', slice_steps_unq)
                self.scan.scan = reset_slices(self.scan.scan, slice_steps, slice_steps_unq)
                self.mask.scan = reset_slices(self.mask.scan, slice_steps, slice_steps_unq)
                
        if sync_attributes:
            for attr in sync_attributes:
                for num, file in enumerate(self.scan.scan):
                    setattr(self.mask.scan[num], attr, getattr(self.scan.scan[num], attr))
        if round_attributes:
            for key_attr, value_round in round_attributes.items():
                for num, file in enumerate(self.scan.scan):
                    attr_rounded_scan = [round(cur_attr, value_round) for cur_attr in getattr(self.scan.scan[num], key_attr)]
                    setattr(self.scan.scan[num], key_attr, attr_rounded_scan)
                    attr_rounded_mask = [round(cur_attr, value_round) for cur_attr in getattr(self.mask.scan[num], key_attr)]
                    setattr(self.mask.scan[num], key_attr, attr_rounded_mask)
        if sync_slices:
            for key_attr, value_ind in sync_slices.items():
                const_attr = getattr(self.scan.scan[0], key_attr)
                for num, file in enumerate(self.scan.scan):
                    tmp_attr = getattr(file, key_attr)
                    for ind in value_ind:                        
                        tmp_attr[ind] = const_attr[ind]
                    setattr(self.scan.scan[num], key_attr, tmp_attr)
                const_attr = getattr(self.mask.scan[0], key_attr)
                for num, file in enumerate(self.mask.scan):
                    tmp_attr = getattr(file, key_attr)
                    for ind in value_ind:                        
                        tmp_attr[ind] = const_attr[ind]
                    setattr(self.mask.scan[num], key_attr, tmp_attr)
                    
        
            
        rgb_colors = [tuple(int(color.strip('#')[i:i+2], 16) for i in (0, 2, 4)) for color in colors]
        rgb = np.copy(self.scan.arr)
        rgb = normalize_arr(rgb.astype('float64'), norm_range = [0, 255])
        rgb = np.array([np.copy(rgb) for i in range(3)]) #build RGB
        rgb_orig = np.copy(rgb)
        for i in range(3): rgb[i,...][self.mask.arr > 0] *= (1-transparency)
        for i in range(3): rgb[i,...][self.mask.arr > 0] += rgb_colors[1][i] * transparency #color in mask
        if rotate: rgb = np.rot90(rgb, axes = (1,2)) 
        if rotate: rgb_orig = np.rot90(rgb_orig, axes = (1,2)) 

        rgb_cat = np.concatenate((rgb_orig, rgb), axis = 2); rgb_cat = np.swapaxes(rgb_cat, 0, 3)
        
        self.rgb = rgb
        self.orig = rgb_orig
        self.cat = (rgb_cat).astype(np.uint8)
        self.colors = colors
        
        
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

        legend_ = [['Ground Truth'], [self.colors[1]]]#[['TP: Overlap', 'FN: Ground Truth', 'FP: Segmentation Mask'], res_nib.colors]
#         [['Ground Truth'], [self.colors[1]]
        plot_res(list_img = [transverse, coronal, sagittal], mag = 1.0, row_col = [3, 1], legend = legend_)
        
    

    def save_as(self, loc_save, cat = True, ext = '.png', label = 'Ground Truth'):
        
        if cat:
            
            build_dir(os.path.split(loc_save)[0])
            transverse = np.copy(self.transverse)
            transverse = cv2.resize(transverse, dsize = (1024, int(1024 * (self.transverse.shape[0]/self.transverse.shape[1]))), interpolation = cv2.INTER_CUBIC); 
            transverse = normalize_arr(transverse, [0, 255]).astype(np.uint8)
            coronal = np.copy(self.coronal); 
            coronal = cv2.resize(coronal, dsize = (1024, int(1024 * (self.coronal.shape[0]/self.coronal.shape[1]))), interpolation = cv2.INTER_CUBIC); 
            coronal = normalize_arr(coronal, [0, 255]).astype(np.uint8)
            sagittal = np.copy(self.sagittal); 
            sagittal = cv2.resize(sagittal, dsize = (1024, int(1024 * (self.sagittal.shape[0]/self.sagittal.shape[1]))), interpolation = cv2.INTER_CUBIC); 
            sagittal = normalize_arr(sagittal, [0, 255]).astype(np.uint8)
            cat = np.concatenate ((transverse, coronal, sagittal), axis = 0)
            
            figsize = (16,(int(1024 * (self.transverse.shape[0]/self.transverse.shape[1])) +   int(1024 * (self.coronal.shape[0]/self.coronal.shape[1])) + int(1024 * (self.sagittal.shape[0]/self.sagittal.shape[1])))/64)
            plt.figure(num=None, figsize=figsize, dpi= 64, facecolor='w', edgecolor='k') # figsize=(16, 24)
            legend_elements = [Patch(facecolor = self.colors[0], edgecolor = self.colors[0], label = label)]
            plt.legend(handles=legend_elements, loc='upper right', prop={'size': 25})
            plt.tight_layout()
            plt.imshow(cat)
            plt.tick_params(left=False,
                            bottom=False,
                            labelleft=False,
                            labelbottom=False)
            plt.savefig(loc_save)
            plt.close()
            
        else:
            
            build_dir(loc_save)
            for slice_num in range(self.cat.shape[0]):
                plt.figure(num=None, figsize= (16, 8), dpi= 64, facecolor='w', edgecolor='k') # figsize=(16, 24)
                legend_elements = [Patch(facecolor = self.colors[0], edgecolor = self.colors[0], label = label)]
                plt.legend(handles=legend_elements, loc='upper right', prop={'size': 25})
                plt.tight_layout()
                plt.imshow(self.cat[slice_num, ...])
                plt.tick_params(left=False,
                                bottom=False,
                                labelleft=False,
                                labelbottom=False)
                loc_slice = os.path.join(loc_save, str(slice_num).zfill(4) + ext)
                plt.savefig(loc_slice)
                plt.close()

        return
    

