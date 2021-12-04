import pathlib
from typing import List

import numpy as np
import pydicom as dcm

from ballir_dicom_manager.file_viewers.array_viewer import ArrayViewer
from ballir_dicom_manager.file_readers.read_image_volume import ReadImageVolume
from ballir_dicom_manager.file_loaders.dicom_loader import DicomLoader
from ballir_dicom_manager.file_writers.dicom_writer import DicomWriter
from ballir_dicom_manager.preprocess.dicom_tag_parser import DicomSorter, DicomTagParser
from ballir_dicom_manager.preprocess.dicom_validator import DicomVolumeValidator
from ballir_dicom_manager.preprocess.fix_dicom_for_nifti import FixDicomForNifti

class ReadDicom(ReadImageVolume):
    
    loader = DicomLoader()
    sorter = DicomSorter()
    writer = DicomWriter()
    nifti_fixer = FixDicomForNifti(fill_missing_with_adjacent = False)
    
    def __init__(self, target_path: pathlib.Path, value_clip = False, allow: list = []):
        super().__init__(target_path)  

        self.value_clip = value_clip
        self.files = self.sorter.sort_dicom_files(self.files)
        
        self.validator = DicomVolumeValidator(allow)
        self.validator.validate(self.files)
        
        self.parser = DicomTagParser(allow)
        self.spacing = self.parser.get_dicom_spacing(self.files)
        
        self.set_arr()

#     def get_window_level_attributes(self, dicom_file: dcm.dataset.Dataset):
#         window_level_attributes = {'WindowWidth': 400.0, 'WindowCenter': 50.0, 'RescaleIntercept': 0.0, 'RescaleSlope': 1.0}
#         for tag in window_level_attributes.keys():
#             if hasattr(dicom_file, tag): setattr(window_level_attributes, getattr(dicom_file, tag))  
#         window_level_attributes['lower_limit'] = window_level_attributes['WindowCenter'] - window_level_attributes['WindowWidth']/2 
#         window_level_attributes['upper_limit'] = window_level_attributes['WindowCenter'] - window_level_attributes['WindowWidth']/2 
#         return window_level_attributes

#     def apply_window_level(self, dicom_files: List[dcm.dataset.Dataset]):
#         window_level_attributes = self.get_window_level_attributes(dicom_files[0]) # check all for consistency?
#         lower_limit = window_level_attributes['WindowCenter']
        
#     def winLev(self, arr, wc, ww, ri, rs):

#         lower_limit = wc - (ww/2)
#         upper_limit = wc + (ww/2)

#         hounsfield_img = (arr*rs) + ri
#         clipped_img = np.clip(hounsfield_img, lower_limit, upper_limit)
#         windowLevel = (clipped_img/ww) - (lower_limit/ww)

#         return windowLevel
    
    
#     def getWinLevAttr_dcm(self, tmp_dcm):

#         attr = {'WindowCenter': 50.0, 'WindowWidth': 400.0, 'RescaleIntercept': 0.0, 'RescaleSlope': 1.0}

#         for key, value in attr.items():
#             if hasattr(tmp_dcm, key):
#                 try:
#                     attr[key] = float(getattr(tmp_dcm, key))
#                 except:
#                     attr[key] = float(getattr(tmp_dcm, key)[0])
# #             else:
# #                 print('MISSING: ', key)

#         wc, ww, ri, rs = attr.values()
#         return wc, ww, ri, rs

    def convert_to_hounsfield(self):
        self.arr += np.int16(self.files[0].RescaleIntercept)
        self.arr *= np.int16(self.files[0].RescaleSlope)

    def convert_from_hounsfield(self): 
        self.arr = self.arr/np.int16(self.files[0].RescaleSlope)
        self.arr -= np.int16(self.files[0].RescaleIntercept)
        
    def set_arr(self) -> None:
        self.arr = np.array([file.pixel_array for file in self.files])
        if self.value_clip: 
            self.convert_to_hounsfield()
            self.arr = np.clip(self.arr, self.value_clip[0], self.value_clip[1])
            self.convert_from_hounsfield()
            self.writer.write_array_volume_to_dicom(self.arr, self.files)
        
        # if self.window_level:
        #     self.arr, self.files = self.apply_window_level(self.arr, self.files)
        self.arr = np.swapaxes(self.arr, 0, 2)
        self.viewer = ArrayViewer(self.arr, self.spacing)    
        
    def prep_for_nifti(self) -> None:
        self.files = self.nifti_fixer.validate_for_nifti(self.files)
        self.set_arr()

    