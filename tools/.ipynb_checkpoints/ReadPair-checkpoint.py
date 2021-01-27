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

def saveRGB(rgb, dir_save):
    
    buildDir(dir_save)

    for i in range(rgb.shape[0]):
        loc_save = os.path.join(dir_save, str(i)+'.png')
        imageio.imwrite(loc_save, rgb[i,...])
    
    return


class ReadPair:
     
    def __init__(self, scan, mask, remove_empties = False, colors = ['#2c2cc9', '#06b70c', '#eaf915'], transparency = 0.3, rotate = True):
        
        self.scan = copy.deepcopy(scan)
        self.mask = copy.deepcopy(mask)
        
        if remove_empties:
            indEmpty = indexEmpty(self.mask.arr)
            if len(indEmpty) > 0:
                print('indEmpty: ', indEmpty)
                self.mask.arr = removeEmpty(self.mask.arr, indEmpty)
                self.mask.scan = [file for num_file, file in enumerate(self.mask.scan) if num_file not in indEmpty]
                self.scan.arr = removeEmpty(self.scan.arr, indEmpty)
                self.scan.scan = [file for num_file, file in enumerate(self.scan.scan) if num_file not in indEmpty]
               
                # fix ERROR: -- ConversionValidationError: SLICE_INCREMENT_INCONSISTENT
                slice_steps, slice_steps_unq, slice_locs, slice_locs_unq = stepSizes(self.scan.scan)
                print('slice steps 2: ', slice_steps_unq)
                self.scan.scan = resetSlices(self.scan.scan, slice_steps, slice_steps_unq)
                self.mask.scan = resetSlices(self.mask.scan, slice_steps, slice_steps_unq)

            
        rgb_colors = [tuple(int(color.strip('#')[i:i+2], 16) for i in (0, 2, 4)) for color in colors]
        rgb = np.copy(self.scan.arr)
        rgb = normalizeArr(rgb.astype('float64'), norm_range = [0, 255])
        rgb = np.array([np.copy(rgb) for i in range(3)]) #build RGB
        rgb_orig = np.copy(rgb)
        for i in range(3): rgb[i,...][self.mask.arr > 0] *= (1-transparency)
        for i in range(3): rgb[i,...][self.mask.arr > 0] += rgb_colors[0][i] * transparency #color in mask
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
        transverse = normalizeArr(transverse, [0, 1])

        #CORONAL
        coronal_scan = np.copy(self.orig[:, int(self.orig.shape[1]/2), :, :])
        coronal_rgb = np.copy(self.rgb[:, int(self.orig.shape[1]/2), :, :])
        coronal_scan = np.swapaxes(coronal_scan, 0, 2)
        coronal_rgb = np.swapaxes(coronal_rgb, 0, 2)
        coronal = np.concatenate((coronal_scan, coronal_rgb), axis = 1)
        coronal = cv2.resize(coronal, dsize = (int(2 * self.scan.range[0]), int(self.scan.range[2])), interpolation = cv2.INTER_CUBIC)
        coronal = normalizeArr(coronal, [0,1])

        #SAGITTAL 
        sagittal_scan = np.copy(self.orig[:, :, int(self.orig.shape[2]/2), :])
        sagittal_rgb = np.copy(self.rgb[:, :, int(self.orig.shape[2]/2), :])
        sagittal_scan = np.swapaxes(sagittal_scan, 0, 2); sagittal_scan = np.flip(sagittal_scan, 1) 
        sagittal_rgb = np.swapaxes(sagittal_rgb, 0, 2); sagittal_rgb = np.flip(sagittal_rgb, 1)
        sagittal = np.concatenate((sagittal_scan, sagittal_rgb), axis = 1)
        sagittal = cv2.resize(sagittal, dsize = (int(2 * self.scan.range[1]), int(self.scan.range[2])), interpolation = cv2.INTER_CUBIC)
        sagittal = normalizeArr(sagittal, [0,1])
        
        self.transverse = transverse
        self.coronal = coronal
        self.sagittal = sagittal

        plotRes(list_img = [transverse, coronal, sagittal], mag = 1.0, row_col = [3, 1], legend = [['Ground Truth', self.colors[0]],['Ground Truth', self.colors[0]],['Ground Truth', self.colors[0]]])
        
    

    def save_as(self, loc_save, cat = True, ext = '.png', label = 'Ground Truth'):
        
        if cat:
            
            buildDir(os.path.split(loc_save)[0])
            transverse = np.copy(self.transverse)
            transverse = cv2.resize(transverse, dsize = (1024, int(1024 * (self.transverse.shape[0]/self.transverse.shape[1]))), interpolation = cv2.INTER_CUBIC); 
            transverse = normalizeArr(transverse, [0, 255]).astype(np.uint8)
            coronal = np.copy(self.coronal); 
            coronal = cv2.resize(coronal, dsize = (1024, int(1024 * (self.coronal.shape[0]/self.coronal.shape[1]))), interpolation = cv2.INTER_CUBIC); 
            coronal = normalizeArr(coronal, [0, 255]).astype(np.uint8)
            sagittal = np.copy(self.sagittal); 
            sagittal = cv2.resize(sagittal, dsize = (1024, int(1024 * (self.sagittal.shape[0]/self.sagittal.shape[1]))), interpolation = cv2.INTER_CUBIC); 
            sagittal = normalizeArr(sagittal, [0, 255]).astype(np.uint8)
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
            
            buildDir(loc_save)
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
    

