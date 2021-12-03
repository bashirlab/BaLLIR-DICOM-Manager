from typing import List, Tuple

from ballir_dicom_manager.file_viewers.array_viewer import ArrayViewer

import cv2
import scipy
import numpy as np

class RGBViewer(ArrayViewer):
    
    def __init__(self, overlay: np.array, label: np.array, spacing):
        self.arr = overlay
        self.label = label
        self.spacing = spacing
        self.center_of_mass = self.get_center_of_mass()
#         super().__init__(arr, spacing)
    
    def get_transverse(self, arr: np.array, resize_dims: List[float]) -> np.array:
        transverse =  np.flip(np.rot90(arr[int(self.center_of_mass[2]), ...], axes = (1, 0)), 1)
        return self.resize_rgb(transverse, resize_dims = resize_dims, resize_idx = (1,0))
    
    def get_sagittal(self, arr: np.array, resize_dims: List[float]) -> np.array:
        sagittal = np.flip(np.rot90(arr[:, int(self.center_of_mass[0]), ...], k = 2, axes = (2,0)), 1)
        return self.resize_rgb(sagittal, resize_dims = resize_dims, resize_idx = (1,2))
    
    def get_coronal(self, arr: np.array, resize_dims: List[float]) -> np.array:
        coronal = np.rot90(arr[:, :, int(self.center_of_mass[1]), :], k = 2, axes = (2,0))
        return self.resize_rgb(coronal, resize_dims = resize_dims, resize_idx = (0,2))
    
    def get_center_of_mass(self) -> Tuple[float]:
        return scipy.ndimage.center_of_mass(self.label)
    
    def resize_rgb(self, arr: np.array, resize_dims: Tuple[float], resize_idx: Tuple[int]) -> np.array:
        resized_rgb = np.zeros([resize_dims[resize_idx[1]], resize_dims[resize_idx[0]], 3])
        for channel in range(3):
            resized_rgb[..., channel] = cv2.resize(arr[..., channel], dsize = (resize_dims[resize_idx[0]], resize_dims[resize_idx[1]]), interpolation = cv2.INTER_CUBIC)
        return resized_rgb.astype('uint8')
    
    def get_resize_dimensions(self):
        resize_dims = np.multiply(list(reversed(self.arr.shape[:-1])), self.spacing)
        return [int(dim) for dim in resize_dims]