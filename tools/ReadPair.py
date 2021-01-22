from tools.ReadDicom import *
from tools.ReadDicomMask import *
import copy

#start using *args and **kwargs

#start as GT, expand to include QC image stuff with TP and FP measurements 

class ReadPair:
     
    def __init__(self, scan, mask, remove_empties = False, colors = ['#2c2cc9', '#06b70c', '#eaf915'], transparency = 0.7, rotate = True):
        
        self.scan = copy.deepcopy(scan)
        self.mask = copy.deepcopy(mask)
        
        if remove_empties:
            indEmpty = indexEmpty(self.mask.arr)
            self.mask.arr = removeEmpty(self.mask.arr, indEmpty)
            self.scan.arr = removeEmpty(self.scan.arr, indEmpty)
            
        rgb_colors = [tuple(int(color.strip('#')[i:i+2], 16) for i in (0, 2, 4)) for color in colors]
#         rgb_orig = np.copy(scan.arr).astype('float64')
#         rgb_orig = normalizeArr(rgb_orig, [0, 255])
        rgb_orig = np.copy(scan.arr)
        if rotate: rgb_orig = np.rot90(rgb_orig) 
        
        mask_seg = np.copy(masks)
        if rotate: mask_seg = np.rot90(mask_seg) 

        mask_r = np.copy(rgb_orig)
        mask_r[mask_seg>0] *= (1-transparency)
        mask_g = np.copy(mask_r)
        mask_b = np.copy(mask_r)

        mask_r[mask_seg>0] += rgb_colors[0][0] * transparency;  
        mask_g[mask_seg>0] += rgb_colors[0][1] * transparency; 
        mask_b[mask_seg>0] += rgb_colors[0][2] * transparency; 

        rgb_mask = grey2rgb([mask_r, mask_g, mask_b])
        rgb_orig = grey2rgb(rgb_orig) 
        rgb_cat = np.concatenate((rgb_orig, rgb_mask), axis = 2)
        rgb_cat /= 255
        rgb_cat = np.swapaxes(rgb_cat, 0, 3)

        self.arr = rgb_cat
        self.mask = rgb_mask
        self.orig = rgb_orig
        self.range = scan.range

           
        

        
        class DrawMasks(ReadDicom):  #add option for multiple masks compare (cat 3 wide, etc.)
    
    def __init__(self, scan, masks, colors = ['#2c2cc9', '#06b70c', '#eaf915'], transparency = 0.7, rotate = True):
        
        transparency = 1 - transparency
        rgb_colors = [tuple(int(color.strip('#')[i:i+2], 16) for i in (0, 2, 4)) for color in colors]
        rgb_orig = np.copy(scan.arr).astype('float64')
        if rotate: rgb_orig = np.rot90(rgb_orig) 
        rgb_orig = normalizeNumpy(rgb_orig, [0, 255])
        
            
        if len(masks)>1:                #remove if/else
            
            mask_seg = np.copy(masks[1].arr)
            if rotate: mask_seg = np.rot90(mask_seg) ; mask_seg = np.flip(mask_seg, 1)#tmpflip
            
            mask_gt = np.copy(masks[0].arr)
            if rotate: mask_gt = np.rot90(mask_gt) 
            
            full_mask = mask_gt + mask_seg
            full_mask[full_mask>0] = 1.0
            
            TP = mask_gt * mask_seg; TP[TP>0] = 1.0; TP[TP<0] = 0.0
            FP = mask_gt - mask_seg; FP[FP>0] = 1.0; FP[FP<0] = 0.0 #do something better in case of np.amax == 2 segs
            FN = mask_seg - mask_gt; FN[FN>0] = 1.0; FP[FP<0] = 0.0
            
            #DICE = (2*np.sum(TP))/((2*np.sum(TP)) + np.sum(FP) + np.sum(FN))
            DICE = (2*np.sum(TP))/(np.sum(mask_gt) + np.sum(mask_seg))
            
            mask_r = np.copy(rgb_orig)
            mask_r[full_mask>0] *= (1-transparency)
            mask_g = np.copy(mask_r)
            mask_b = np.copy(mask_r)
            
            mask_r[TP>0] += rgb_colors[1][0] * transparency;  
            mask_g[TP>0] += rgb_colors[1][1] * transparency; 
            mask_b[TP>0] += rgb_colors[1][2] * transparency; 
            
            mask_r[FP>0] += rgb_colors[0][0] * transparency;  
            mask_g[FP>0] += rgb_colors[0][1] * transparency; 
            mask_b[FP>0] += rgb_colors[0][2] * transparency; 
            
            mask_r[FN>0] += rgb_colors[2][0] * transparency;  
            mask_g[FN>0] += rgb_colors[2][1] * transparency; 
            mask_b[FN>0] += rgb_colors[2][2] * transparency; 
            
            self.TP = TP
            self.FP = FP
            self.FN = FN
            self.GT = mask_gt
            self.SEG = mask_seg
            self.DICE = DICE

        else:  
            
            mask_seg = np.copy(masks[0].arr)
            if rotate: mask_seg = np.rot90(mask_seg) 
            
            mask_r = np.copy(rgb_orig)
            print(mask_r.shape)
            mask_r[mask_seg>0] *= (1-transparency)
            mask_g = np.copy(mask_r)
            mask_b = np.copy(mask_r)

            mask_r[mask_seg>0] += rgb_colors[0][0] * transparency;  
            mask_g[mask_seg>0] += rgb_colors[0][1] * transparency; 
            mask_b[mask_seg>0] += rgb_colors[0][2] * transparency; 

        rgb_mask = grey2rgb([mask_r, mask_g, mask_b])
        rgb_orig = grey2rgb(rgb_orig) 
        rgb_cat = np.concatenate((rgb_orig, rgb_mask), axis = 2)
        rgb_cat /= 255
        rgb_cat = np.swapaxes(rgb_cat, 0, 3)

        self.arr = rgb_cat
        self.mask = rgb_mask
        self.orig = rgb_orig
        self.range = scan.range
        