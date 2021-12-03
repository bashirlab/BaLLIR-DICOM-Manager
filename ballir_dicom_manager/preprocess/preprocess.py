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
        
    def __init__(self, DIR_RAW, add_subgroup = False, hounsfield: bool = False, value_clip = False, allow = []):
        self.RAW_DICOM_DIRS = self.dicom_finder.get_dicom_dirs(DIR_RAW)
        DIR_PREPROCESSED = "raw".join(DIR_RAW.split("raw")[:-1]) + "preprocessed" # join in case of 2nd "raw" dir somewhere in directory structure
        # option for images and labels?
        DIR_PRE_DICOM = self.get_preprocessed_dir(DIR_PREPROCESSED, image_type = 'dicom', add_subgroup = add_subgroup)
        DIR_PRE_NIFTI = self.get_preprocessed_dir(DIR_PREPROCESSED, image_type = 'nifti', add_subgroup = add_subgroup)
        self.DIRS = DirManager(
            DIR_PREPROCESSED = DIR_PREPROCESSED,
            DIR_PRE_DICOM = DIR_PRE_DICOM,
            DIR_PRE_NIFTI = DIR_PRE_NIFTI
        )
        self.hounsfield = hounsfield
        self.value_clip = value_clip
        self.allow = allow
        
    def get_preprocessed_dir(self, DIR_PREPROCESSED: pathlib.Path, image_type: str, add_subgroup) -> pathlib.Path:
        if add_subgroup:
            return os.path.join(DIR_PREPROCESSED, image_type, 'images', add_subgroup)
        else:
            return os.path.join(DIR_PREPROCESSED, image_type, 'images')
        
    def clean_dicom(self, raw_dicom_dir: pathlib.Path, clean_dicom_dir: pathlib.Path) -> None:
        raw = ReadDicom(raw_dicom_dir, hounsfield = self.hounsfield, value_clip = self.value_clip, allow = self.allow)
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
            
    def preview_preprocessed_dicom(self) -> None:
#         for clean_dicom_dir in get_dicom_dirs(self.DIR_PRE_DICOM):
        for clean_dicom_dir in glob(os.path.join(self.DIRS.DIR_PRE_DICOM, '*/')):
            clean_dicom = ReadDicom(clean_dicom_dir, allow = self.allow)
            clean_dicom.viewer.orthoview()
    
    def preview_preprocessed_nifti(self) -> None:
        for nifti_path in glob(os.path.join(self.DIRS.DIR_PRE_NIFTI, '*.nii.gz')):
            nifti_file = ReadNifti(nifti_path)
            nifti_file.viewer.orthoview()

    def preprocess(self, case_name_fn = False) -> None:
        for raw_dicom_dir in tqdm(self.RAW_DICOM_DIRS, desc = 'preprocessing...'):
            # try:
            case_name = self.get_case_name(raw_dicom_dir, case_name_fn)
            clean_dicom_dir = self.get_clean_dicom_dir(case_name)
            self.clean_dicom(raw_dicom_dir, clean_dicom_dir)
            self.write_nifti(clean_dicom_dir, case_name)        
            # except Exception as e:
            #     print(f'ERROR converting {raw_dicom_dir}: {e}')
            #     break


    # def verify_input_yesno(self, user_input: str) -> str:
    #     if user_input.lower() == 'y' or user_input.lower() == 'yes':
    #         return 'y'
    #     elif user_input.lower() == 'n' or user_input.lower() == 'no':
    #         return 'n'
    #     else:
    #         user_input = input('Please enter either "y" or "n"')
    #         self.verify_input(user_input)

    # def verify_input_list(self, user_input: str) -> list:
    #     if user_input == "":
    #         return [-250, 200]
    #     elif type(user_input) == list:
    #         if len(user_input) == 2:
    #             if type(user_input[0]) == int and type(user_input[1]) == int:
    #                 if user_input[1] > user_input[0]:
    #                     return user_input
    #                 else:
    #                     user_input = input('Make sure max is greater than min: [min, max]')
    #                     self.verify_input_list(user_input)
    #             else:
    #                 user_input = input('Please supply values as ints')
    #                 self.verify_input_list(user_input)
    #         else:
    #             user_input = input('Please supply only 2 values to list: [min, max]')
    #             self.verify_input_list(user_input)
    #     else:
    #         user_input = input('Please enter values as list: [min, max]')
    #         self.verify_input_list(user_input)

       
    # def check_modality(self):
    #     if 'CT' in [file.Modality.upper() for file in self.files]:
    #         user_input = self.verify_input_yesno(input('CT files found, clip data?: (y/n)'))
    #         if user_input == 'y':
    #             self.clip_range = self.verify_input_list(input(f'Enter value range as [min, max] or hit enter to supply default [-250, 200]'))
                

    #             self.clip_ct = True
    #     if not 'CT' in self.allow:
    #         self.check_modality(dicom_files)
            