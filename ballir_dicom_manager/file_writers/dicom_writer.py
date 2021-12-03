import os
from typing import List

import numpy as np
import pydicom as dcm

class DicomWriter:
    
    def __init__(self):
        return        
    
    def save_all(self, dicom_files, destination_dir: str):
        if not os.path.exists(destination_dir): 
            os.makedirs(destination_dir)            
        for num, dicom_file in enumerate(dicom_files):
            dicom_file.save_as(os.path.join(destination_dir, f'{str(num).zfill(4)}.dcm')) 

    def decompress_dicom(self, dicom_file: dcm.dataset.Dataset) -> dcm.dataset.Dataset:
        dicom_file.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2"
        dicom_file.file_meta.is_little_endian = True
        dicom_file.file_meta.is_implicit_VR = True
        return dicom_file

    def write_array_to_dicom(self, pixel_array: np.array, dicom_file: dcm.dataset.Dataset) -> dcm.dataset.Dataset:
        dicom_file = self.decompress_dicom(dicom_file)
        dicom_file.PixelData = pixel_array.astype('uint16').tobytes()
        return dicom_file

    def write_array_volume_to_dicom(self, pixel_array_volume: np.array, dicom_files: List[dcm.dataset.Dataset]) -> List[dcm.dataset.Dataset]:
        for num, dicom_file in enumerate(dicom_files):
            dicom_file = self.write_array_to_dicom(pixel_array_volume[num, ...], dicom_file)
        return dicom_files