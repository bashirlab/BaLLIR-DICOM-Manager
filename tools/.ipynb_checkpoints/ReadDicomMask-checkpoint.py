from tools.ReadDicom import *


def index_empty(arr):

    for num_slice in range(arr.shape[2]):
        ind_mask = [ind for ind in range(arr.shape[2]) if np.amax(arr[..., ind]) > 0]
        ind_empty = [ind for ind in range(arr.shape[2]) if np.amax(arr[..., ind]) == 0 and ind > ind_mask[0] and ind < ind_mask[-1]]

    return ind_empty


def remove_empty(arr, ind_empty):
    
    for num_slice in range(arr.shape[2]-1, 0, -1):
        if num_slice in ind_empty: arr = np.delete(arr, num_slice, 2)
    #     arr_clean = [arr[..., num_slice] for num_slice in range(arr.shape[2]) if not num_slice]

    return arr


class ReadDicomMask(ReadDicom):
    
        
    def __init__(self, filename, filter_tags = False, clip_vals = False, sort_by = False, decompress = True, flip_arr = False, remove_empty = False, fix_dicoms_ = False):
        
        super().__init__(filename, filter_tags = filter_tags, clip_vals = False, sort_by = sort_by, decompress = decompress, flip_arr = flip_arr, fix_dicoms_ = fix_dicoms_)
        if remove_empty: self.arr = remove_empty(self.arr, index_empty(self.arr))
        
        # add decompress option... decompress self.scan, save self.scan with new PixelData and TransferSyntaxUID...? or other decompress() option?
        # have clip_val edit arr 
        # change PixelData to arr 
        
        # change bit tags etc?


        """
        filename [string]: directory location of dicom files
        filter_tags [dictionary]: tag/value pairs, 'max' as value selects most frequent unique tag
        window_level[bool]: True conducts window/level operation based on WindowCenter/WindowWidth/RescaleSlope/RescaleIntercept tags or defaults
        clip_vals[list]: min and max values to clip pixel array (e.g., [-250, 200])
        sort_by[string]: dicom tag used to sort array (e.g., sort_by = 'SliceLocation')
        sort_by[dict]: dicom tag and indexused to sort array (e.g., sort_by = {'ImagePositionPatient': 2})
        decompress[bool]: set TransferSyntaxUID to LittleEndianExplicit, array as type int16
        """
            
            
        