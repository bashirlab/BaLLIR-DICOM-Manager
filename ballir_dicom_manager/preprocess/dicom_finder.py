import os
import pathlib
from typing import List

from glob import glob
from tqdm import tqdm
import pydicom as dcm

class DicomFinder:

    def attempt_dicom_read(self, possible_dicom_path: pathlib.Path):
        try:
            with open(possible_dicom_path, 'rb') as fp:
                dcm.filereader.read_preamble(fp, False)  
            return possible_dicom_path
        except dcm.errors.InvalidDicomError:
            pass

    def get_dicom_paths(self, target_directory: pathlib.Path) -> List[pathlib.Path]:
        """Return all DICOM file paths"""
        possible_dicom_paths =  glob(os.path.join(target_directory, '**/*'), recursive = True)
        possible_dicom_paths = [dicom_path for dicom_path in possible_dicom_paths if os.path.isfile(dicom_path)]
        return [dicom_path for dicom_path in tqdm(possible_dicom_paths, desc = 'locating all DICOM containing directories...') if self.attempt_dicom_read(dicom_path)]

    def get_dicom_dirs(self, target_directory: pathlib.Path) -> List[pathlib.Path]:
        """Return all subdirectories containing DICOM files."""
        dicom_paths = self.get_dicom_paths(target_directory)
        dicom_dirs = [os.path.dirname(dicom_path) for dicom_path in dicom_paths]
        dicom_dirs = list(set(dicom_dirs))
        print(f'found {len(dicom_dirs)} DICOM containins directories in {target_directory}')
        print(*dicom_dirs[:10], sep = '\n')
        return dicom_dirs