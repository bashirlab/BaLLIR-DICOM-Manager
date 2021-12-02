import pathlib
import os

import dicom2nifti
from tqdm import tqdm
from glob import glob

from ballir_dicom_manager.directory_manager import DirManager
from ballir_dicom_manager.file_readers.read_dicom import ReadDicom
from ballir_dicom_manager.file_readers.read_nifti import ReadNifti
from ballir_dicom_manager.preprocess.dicom_finder import DicomFinder

class PreProcess:

    dicom_finder = DicomFinder()
        
    def __init__(self, DIR_RAW, add_subgroup = False, allow = []):
        RAW_DICOM_DIRS = self.dicom_finder.return_dicom_dirs(DIR_RAW)
        DIR_PREPROCESSED = "raw".join(DIR_RAW.split("raw")[:-1]) + "preprocessed" # join in case of 2nd "raw" dir somewhere in directory structure
        # option for images and labels?
        DIR_PRE_DICOM = self.get_preprocessed_dir(image_type = 'dicom', add_subgroup = add_subgroup)
        DIR_PRE_NIFTI = self.get_preprocessed_dir(image_type = 'nifti', add_subgroup = add_subgroup)
        self.DIRS = DirManager(
            DIR_PREPROCESSED = DIR_PREPROCESSED,
            DIR_PRE_DICOM = DIR_PRE_DICOM,
            DIR_PRE_NIFTI = DIR_PRE_NIFTI
        )
        self.allow = allow
        
        
    def get_preprocessed_dir(self, image_type: str, add_subgroup) -> pathlib.Path:
        if add_subgroup:
            return os.path.join(self.DIRS.DIR_PREPROCESSED, image_type, 'images', add_subgroup)
        else:
            return os.path.join(self.DIRS.DIR_PREPROCESSED, image_type, 'images')
        
    def clean_dicom(self, raw_dicom_dir: pathlib.Path, clean_dicom_dir: pathlib.Path) -> None:
        raw = ReadDicom(raw_dicom_dir, self.allow)
        raw.prep_for_nifti()
        raw.writer.save_all(raw.files, clean_dicom_dir)
    
    def get_clean_dicom_dir(self, case_name) -> pathlib.Path:
        return os.path.join(self.DIRS.DIR_PRE_DICOM, case_name)
        
    def get_case_name(self, raw_dicom_dir, case_name_fn) -> str:
        if not case_name_fn:
            return os.path.basename(raw_dicom_dir)
        else:
            return case_name_fn(raw_dicom_dir)
        
    def write_nifti(self, clean_dicom_dir: pathlib.Path, case_name: str) -> None:
        nifti_write_path = os.path.join(self.DIRS.DIR_PRE_NIFTI, f'{case_name}_0000.nii.gz')
        dicom2nifti.dicom_series_to_nifti(clean_dicom_dir, nifti_write_path)
        
    def preprocess(self, case_name_fn = False) -> None:
        for raw_dicom_dir in tqdm(self.RAW_DICOM_DIRS, desc = f'preprocessing...'):
            try:
                case_name = self.get_case_name(raw_dicom_dir, case_name_fn)
                clean_dicom_dir = self.get_clean_dicom_dir(case_name)
                self.clean_dicom(raw_dicom_dir, clean_dicom_dir)
                self.write_nifti(clean_dicom_dir, case_name)        
            except Exception as e:
                print(f'ERROR converting {raw_dicom_dir}: {e}')
                break
            
    def preview_preprocessed_dicom(self) -> None:
#         for clean_dicom_dir in return_dicom_dirs(self.DIR_PRE_DICOM):
        for clean_dicom_dir in glob(os.path.join(self.DIRS.DIR_PRE_DICOM, '*/')):
            clean_dicom = ReadDicom(clean_dicom_dir, self.allow)
            clean_dicom.viewer.orthoview()
    
    def preview_preprocessed_nifti(self) -> None:
        for nifti_path in glob(os.path.join(self.DIRS.DIR_PRE_NIFTI, '*.nii.gz')):
            nifti_file = ReadNifti(nifti_path)
            nifti_file.viewer.orthoview()
            