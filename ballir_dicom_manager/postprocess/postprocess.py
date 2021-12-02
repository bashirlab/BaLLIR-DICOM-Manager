import pathlib
import os
import copy

import numpy as np
from glob import glob
from tqdm import tqdm
import pydicom as dcm

from ballir_dicom_manager.directory_manager import DirManager
from ballir_dicom_manager.file_readers.read_nifti import ReadNifti
from ballir_dicom_manager.file_readers.read_dicom import ReadDicom
from ballir_dicom_manager.file_readers.read_image_label_pair import ReadImageLabelPair

class PostProcess:
    
    def __init__(self, DIR_PRE_DICOM, DIR_PRE_NIFTI, DIR_INFERENCE, allow = []):
        DIR_POSTPROCESS = "postprocessed".join(DIR_INFERENCE.split("inference"))
        self.DIRS = DirManager(
            DIR_PRE_DICOM = DIR_PRE_DICOM,
            DIR_PRE_NIFTI = DIR_PRE_NIFTI,
            DIR_INFERENCE = DIR_INFERENCE,
            DIR_POSTPROCESS = DIR_POSTPROCESS
        )
        self.allow = allow
        
    def get_dicom_path(self, nifti_path: pathlib.Path) -> pathlib.Path:
        return os.path.join(self.DIRS.DIR_PRE_DICOM, os.path.basename(nifti_path).split('_0000.nii.gz')[0])
    
    def get_label_path(self, nifti_path: pathlib.Path) -> pathlib.Path:
        return os.path.join(self.DIRS.DIR_INFERENCE, ".nii.gz".join(os.path.basename(nifti_path).split("_0000.nii.gz")))
    
    def read_files(self, nifti_path: pathlib.Path):
        nifti_image = ReadNifti(nifti_path)
        nifti_label = ReadNifti(self.get_label_path(nifti_path))
        dicom_image = ReadImageLabelPair(self.get_dicom_path(nifti_path), allow = self.allow)
        dicom_label = copy.deepcopy(dicom_image)
        return nifti_image, nifti_label, dicom_image, dicom_label
    
    def decompress_dicom(self, dicom_file: dcm.dataset.Dataset) -> dcm.dataset.Dataset:
        dicom_file.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2"
        dicom_file.file_meta.is_little_endian = True
        dicom_file.file_meta.is_implicit_VR = True
        return dicom_file
    
    def copy_nifti_to_dicom(self, nifti_file: ReadNifti, dicom_file: ReadDicom) -> ReadDicom:
        nifti_array = nifti_file.files[0].get_fdata()
        for num, dcm_file in enumerate(dicom_file.files):
            dcm_file = self.decompress_dicom(dcm_file)
            dcm_file.PixelData = np.rot90(nifti_array[..., num]).astype('uint16').tobytes()
        return dicom_file
        
    def postprocess(self) -> None:
        for nifti_path in tqdm(glob(os.path.join(self.DIRS.DIR_PRE_NIFTI, '*.nii.gz')), desc = 'postprocessing...'):
            nifti_image, nifti_label, dicom_image, dicom_label = self.read_files(nifti_path)
            dicom_image = self.copy_nifti_to_dicom(nifti_image, dicom_image)
            dicom_label = self.copy_nifti_to_dicom(nifti_label, dicom_label)
            dicom_image_write_dir = os.path.join(self.DIRS.DIR_POSTPROCESS, 'images', os.path.basename(nifti_path.split("_0000.nii.gz")[0]))
            dicom_image.writer.save_all(dicom_image.files, dicom_image_write_dir)
            dicom_label_write_dir = os.path.join(self.DIRS.DIR_POSTPROCESS, 'labels', os.path.basename(nifti_path.split("_0000.nii.gz")[0]))
            dicom_label.writer.save_all(dicom_label.files, dicom_label_write_dir)
