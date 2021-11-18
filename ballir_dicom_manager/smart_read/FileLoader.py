from abc import ABC, abstractmethod
import os

from glob import glob
from natsort import natsorted

from ballir_dicom_manager.exception_handling import ArgErrorType


class FileLoader(ABC):
    """Load medical imaging data file."""

    def __init__(self, target_path):
        self.files = self.load_all_files(target_path)
        pass

    
    def return_file_paths(self) -> list:
        try:
            if isinstance(self.target_path, str) and os.path.isdir(self.target_path):
                # target directory
                file_paths = glob(os.path.join(self.target_path, '**/*'), recursive = True)
                file_paths  = [file for file in file_paths if not os.path.isdir(file)] 
                return natsorted(file_paths)
            elif isinstance(self.target_path, str) and not os.path.isdir(self.target_path):
                # single target file
                return [self.target_path]
            elif isinstance(self.target_path, list):
                # list of target files
                return natsorted(self.target_path)
            else:
                raise ArgErrorType(f'MUST ENTER self.target_path VARIABLE OF STRING TYPE (directory) or LIST TYPE (full paths), not {type(self.target_path)}')
        except ArgErrorType as e:
            print(e)

    @abstractmethod
    def load_file(self, file_path):
        """try/except block to read individual files."""

    def load_all_files(self, target_path) -> list:
        file_paths: list = self.return_file_paths(target_path)
        return [self.load_file(file) for file in file_paths]