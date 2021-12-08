from typing import List
import pathlib

import numpy as np
import pydicom as dcm

from ballir_dicom_manager.file_readers.read_dicom import ReadDicom
from ballir_dicom_manager.file_viewers.rgb_viewer import RGBViewer


class ReadImageLabelPair(ReadDicom):
        
    def __init__(self, dicom_image, dicom_label, transparency: float = 0.3, allow = []):
        self.dicom_image = self.get_file(dicom_image, allow)
        self.dicom_label = self.get_file(dicom_label, allow)
        self.transparency = transparency
        assert dicom_image.spacing == dicom_label.spacing, f'image and label spacing is inconsistent {dicom_image.spacing}:{dicom_label.spacing}'
        self.arr = self.build_rgb_overlay()
        self.viewer = RGBViewer(self.arr, self.dicom_label.arr, dicom_image.spacing)

    def get_file(self, path_or_file, allow) -> dcm.dataset.Dataset:
        if isinstance(path_or_file, pathlib.Path):
            return ReadDicom(path_or_file, allow) 
        else: #elif isinstance(path_or_file, dcm.dataset.Dataset):
            return path_or_file
        
    def get_label_values(self) -> List[int]:
        assert np.amin(self.dicom_label.arr) >= 0, 'negative values present in mask'
        return np.unique(self.dicom_label.arr[self.dicom_label.arr > 0])
    
    def normalize_image(self, grayscale_array: np.array) -> np.array:
        normalized_array = (grayscale_array - np.amin(grayscale_array))/(np.amax(grayscale_array) - np.amin(grayscale_array))
        normalized_array *= 255
        normalized_array = normalized_array.astype('uint8')
        return normalized_array
        
    def convert_grayscale_to_rgb(self, grayscale_array: np.array) -> np.array:
        return np.array([np.copy(self.normalize_image(grayscale_array)) for i in range(3)])
    
    def dampen_mask_regions(self, rgb_array: np.array) -> np.array:
        for i in range(3): 
            rgb_array[i,...][self.dicom_label.arr > 0] = rgb_array[i,...][self.dicom_label.arr > 0] -rgb_array[i,...][self.dicom_label.arr > 0]*self.transparency
        return rgb_array
    
    def get_color_tuples(self, colors = ('#06b70c', '#2c2cc9', '#eaf915')) -> List[tuple]:
        return [tuple(int(color.strip('#')[i:i+2], 16) for i in (0, 2, 4)) for color in colors]

    def color_in_labels(self, rgb_array: np.array) -> np.array:
        for i in range(3):
            for num, label_value in enumerate(self.get_label_values()):
                rgb_array[i,...][self.dicom_label.arr == label_value] = rgb_array[i,...][self.dicom_label.arr == label_value] + (self.get_color_tuples()[num][i]*self.transparency)
        return rgb_array
        
    def build_rgb_overlay(self) -> np.array:
        rgb_array = self.convert_grayscale_to_rgb(self.dicom_image.arr)
        rgb_array = self.dampen_mask_regions(rgb_array)
        rgb_array = self.color_in_labels(rgb_array)
        rgb_array = np.swapaxes(rgb_array, 0, -1)
        return rgb_array

    def get_voxel_size(self, dicom_file: dcm.dataset.Dataset) -> float:
        return np.product(dicom_file.PixelSpacing[:2]) * dicom_file.SpacingBetweenSlices

    def get_volume(self) -> float:
        return sum([self.get_voxel_size(image)*np.sum(label.pixel_array) for image, label in zip(self.dicom_image.files, self.dicom_label.files)])

    
        

# separate out into volume_calculator class?



#     def validate_mask(self):
#         return
    
#     def check_for_missing_slices(self, mask: dcm.dataset.Dataset) -> list:
        
    
#     def remove_empty_slices(self): # if preprocessing, do this before slice position reset... 
#         for image_slice, label_slice in zip(dicom_image.files, dicom_label.files):
#             if np.amax(label_slice.pixel_array) == 0:
#                 #do something
#                 return
        
    
    # assert empty slices...
    # remove empty slices 
    # select single mask value/ combine mask values