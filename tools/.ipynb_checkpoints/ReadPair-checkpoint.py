from tools.ReadDicom import *
from tools.ReadDicomMask import *
from tools.shortcuts import *
from tools.manage_dicom import *
import copy
import imageio
import matplotlib
import cv2


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
     
    def __init__(self, scan, mask, remove_empties = False, colors = ['#06b70c', '#2c2cc9', '#eaf915'], transparency = 0.3, rotate = True, sync_attributes = False, round_attributes = False, sync_slices = False, outline_mask = False, preprocess_arr = False):
        """
        
        sync_attributes[list]: list of attributes to copy from scan to mask 
        round_attributes[dict]: round attributes (keys) to decimal place (values)
        sync_slices[dict]: attribute and attribute's indices to set equal to first slice e.g. -- {'ImagePositionPatient': [0,1]}
        """
        self.scan = copy.deepcopy(scan)
        self.mask = copy.deepcopy(mask)
        
        if preprocess_arr:
            self.scan.arr = np.clip(self.scan.arr, np.mean(self.scan.arr)- (3*np.std(self.scan.arr)), np.mean(self.scan.arr) + (4*np.std(self.scan.arr)))
        
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
                    
        mask_vals = list(np.unique(mask.arr)); mask_vals.remove(0.0)
#         if isinstance(rgb_colors, list) and len(rgb_colors) < len(mask_vals):
#                 print(f'too few colors supplied for mask with {len(mask_vals)} values, padding with random colors')
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
#         for mask_val in mask_vals:
#             rgb[self.mask.arr == mask_val] 
#         for rgb_color in range(len(rgb_colors)):
#             for i in range(3): rgb[i,...][self.mask.arr > 0] += rgb_colors[1][i] * transparency #color in mask
# #             for i in range(3): rgb[i,...][self.mask.arr > 0] += rgb_colors[1][i] * transparency #color in mask
            
            
        if rotate: rgb = np.rot90(rgb, axes = (1,2)) 
        if rotate: rgb_orig = np.rot90(rgb_orig, axes = (1,2)) 

        rgb_cat = np.concatenate((rgb_orig, rgb), axis = 2); rgb_cat = np.swapaxes(rgb_cat, 0, 3)
        
        self.rgb = rgb
        self.orig = rgb_orig
        self.cat = (rgb_cat).astype(np.uint8)
        self.colors = colors
#         self.volume = np.product(scan[0].pixel_spacing()) * (np.sum(mask)/np.amax(mask))  --double check, also check for slice consistency in tag values
        
    def orthoview(self, legend_ = [['Ground Truth'], [0]], middle_slice = False, silence = False, concatenate = True):
            
        #TRANSVERSE
        slicenum_transverse, range_mask = get_middle_slices(self.mask.arr, axis = 2, num_slices = 1)
        transverse_scan = np.copy(self.orig[..., slicenum_transverse[0]])
        transverse_rgb = np.copy(self.rgb[..., slicenum_transverse[0]])
        transverse_scan = np.swapaxes(transverse_scan, 0, 2); transverse_scan = np.rot90(transverse_scan, axes = (1,0)); transverse_scan = np.flip(transverse_scan, 1)
        transverse_rgb = np.swapaxes(transverse_rgb, 0, 2); transverse_rgb = np.rot90(transverse_rgb, axes = (1,0)); transverse_rgb = np.flip(transverse_rgb, 1)
        if concatenate: transverse = np.concatenate((transverse_scan, transverse_rgb), axis = 1)
        transverse = normalize_arr(transverse, [0, 1])

        #CORONAL
        slicenum_coronal, range_mask = get_middle_slices(self.mask.arr, axis = 0, num_slices = 1)
        coronal_scan = np.copy(self.orig[:, slicenum_coronal[0], :, :])
        coronal_rgb = np.copy(self.rgb[:, slicenum_coronal[0], :, :])
        coronal_scan = np.swapaxes(coronal_scan, 0, 2)
        coronal_rgb = np.swapaxes(coronal_rgb, 0, 2)
        if concatenate: coronal = np.concatenate((coronal_scan, coronal_rgb), axis = 1)
        coronal = cv2.resize(coronal, dsize = (int(2 * self.scan.range[0]), int(self.scan.range[2])), interpolation = cv2.INTER_CUBIC)
        coronal = normalize_arr(coronal, [0,1])

        #SAGITTAL 
        slicenum_sagittal, range_mask = get_middle_slices(self.mask.arr, axis = 1, num_slices = 1)
        sagittal_scan = np.copy(self.orig[:, :, slicenum_sagittal[0], :])
        sagittal_rgb = np.copy(self.rgb[:, :, slicenum_sagittal[0], :])
        sagittal_scan = np.swapaxes(sagittal_scan, 0, 2); sagittal_scan = np.flip(sagittal_scan, 1) 
        sagittal_rgb = np.swapaxes(sagittal_rgb, 0, 2); sagittal_rgb = np.flip(sagittal_rgb, 1)
        if concatenate: sagittal = np.concatenate((sagittal_scan, sagittal_rgb), axis = 1)
        sagittal = cv2.resize(sagittal, dsize = (int(2 * self.scan.range[1]), int(self.scan.range[2])), interpolation = cv2.INTER_CUBIC)
        sagittal = normalize_arr(sagittal, [0,1])
        
        self.transverse = transverse
        self.coronal = coronal
        self.sagittal = sagittal

        if legend_:
            legend_colors = [self.colors[ind] for ind in legend_[1]]
            
        if not silence: plot_res(list_img = [transverse, coronal, sagittal], mag = 1.0, row_col = [3, 1], legend = [legend_[0], legend_colors])
        
    

    def save_as(self, loc_save, cat = True, ext = '.png', legend_ = [['Ground Truth'], [1]], legend_size = False):
        
        self.orthoview(silence = True)
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
            cat_single = np.concatenate ((transverse, coronal, sagittal), axis = 0)#/255
            self.cat_single = cat_single
            
            if legend_:
                legend_colors = [self.colors[ind] for ind in legend_[1]]
                if not legend_size:
                    legend_size = 25
            fig_size = (16,(int(1024 * (self.transverse.shape[0]/self.transverse.shape[1])) +   int(1024 * (self.coronal.shape[0]/self.coronal.shape[1])) + int(1024 * (self.sagittal.shape[0]/self.sagittal.shape[1])))/64)
            plot_res(list_img = [cat_single], mag = 1.0, row_col = [1, 1], legend = [legend_[0], legend_colors], legend_size = legend_size, axis = False, tight = True, fig_size = fig_size, loc_save = loc_save, close = True)
            
        else:
            
            build_dir(loc_save)
            for slice_num in range(self.cat.shape[0]):
                plt.figure(num=None, figsize= (16, 8), dpi= 64, facecolor='w', edgecolor='k') # figsize=(16, 24)
#                 legend_elements = [Patch(facecolor = self.colors[0], edgecolor = self.colors[0], label = label)]
                if legend_:
                    legend_elements = [Patch(facecolor = self.colors[i], edgecolor = self.colors[i], label = legend_[0][i]) for i in range(len(legend_[0]))]
                    plt.legend(handles=legend_elements, loc='upper left', prop={'size': 25})
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
    

