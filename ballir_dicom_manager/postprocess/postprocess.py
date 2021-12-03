import pathlib
import os
import copy
import csv
from typing import List

import numpy as np
from glob import glob
from tqdm import tqdm
import pydicom as dcm

from ballir_dicom_manager.directory_manager import DirManager
from ballir_dicom_manager.file_readers.read_nifti import ReadNifti
from ballir_dicom_manager.file_readers.read_dicom import ReadDicom
from ballir_dicom_manager.file_readers.read_image_label_pair import ReadImageLabelPair
from ballir_dicom_manager.file_savers.save_measurements_to_csv import MeasurementSaver
from ballir_dicom_manager.file_savers.save_qc_images import QCSaver

# both this and preprocess image/label combo should inheret from image_label_reader
class PostProcess:

    qc_saver = QCSaver()
    measurements = MeasurementSaver()
    volume = {}
    
    def __init__(self, DIR_PRE_DICOM, DIR_PRE_NIFTI, DIR_INFERENCE, allow = []):
        DIR_POSTPROCESS = "postprocessed".join(DIR_INFERENCE.split("inference"))
        DIR_QC = os.path.join(DIR_POSTPROCESS, 'QC')
        DIR_MEASUREMENTS = os.path.join(DIR_POSTPROCESS, 'MEASUREMENTS')
        self.DIRS = DirManager(
            DIR_PRE_DICOM = DIR_PRE_DICOM,
            DIR_PRE_NIFTI = DIR_PRE_NIFTI,
            DIR_INFERENCE = DIR_INFERENCE,
            DIR_POSTPROCESS = DIR_POSTPROCESS,
            DIR_QC = DIR_QC,
            DIR_MEASUREMENTS = DIR_MEASUREMENTS
        )
        self.allow = allow
        
    def get_dicom_path(self, nifti_path: pathlib.Path) -> pathlib.Path:
        return os.path.join(self.DIRS.DIR_PRE_DICOM, os.path.basename(nifti_path).split('_0000.nii.gz')[0])
    
    def get_label_path(self, nifti_path: pathlib.Path) -> pathlib.Path:
        return os.path.join(self.DIRS.DIR_INFERENCE, ".nii.gz".join(os.path.basename(nifti_path).split("_0000.nii.gz")))
    
    def read_files(self, nifti_path: pathlib.Path):
        nifti_read_image = ReadNifti(nifti_path)
        nifti_read_label = ReadNifti(self.get_label_path(nifti_path))
        dicom_read_image = ReadDicom(self.get_dicom_path(nifti_path), allow = self.allow)
        dicom_read_label = copy.deepcopy(dicom_read_image)
        return nifti_read_image, nifti_read_label, dicom_read_image, dicom_read_label
   
    def copy_nifti_to_dicom(self, nifti_read: ReadNifti, dicom_read: ReadDicom) -> ReadDicom:
        nifti_pixel_array = np.rot90(nifti_read.files[0].get_fdata())
        return dicom_read.writer.write_array_volume_to_dicom(self, nifti_pixel_array, dicom_read.files)
        
    def postprocess(self) -> None:
        for nifti_path in tqdm(glob(os.path.join(self.DIRS.DIR_PRE_NIFTI, '*.nii.gz')), desc = 'postprocessing...'):
            nifti_image, nifti_label, dicom_image, dicom_label = self.read_files(nifti_path)
            dicom_image = self.copy_nifti_to_dicom(nifti_image, dicom_image)
            dicom_label = self.copy_nifti_to_dicom(nifti_label, dicom_label)
            dicom_image_write_dir = os.path.join(self.DIRS.DIR_POSTPROCESS, 'images', os.path.basename(nifti_path.split("_0000.nii.gz")[0]))
            dicom_image.writer.save_all(dicom_image.files, dicom_image_write_dir)
            dicom_label_write_dir = os.path.join(self.DIRS.DIR_POSTPROCESS, 'labels', os.path.basename(nifti_path.split("_0000.nii.gz")[0]))
            dicom_label.writer.save_all(dicom_label.files, dicom_label_write_dir)        

    def preview_postprocessed_dicom(self) -> None:
        for postprocessed_dir in glob(os.path.join(self.DIRS.DIR_POSTPROCESS, 'images', '*/')):
            print(os.path.basename(postprocessed_dir))
            image = ReadDicom(postprocessed_dir, allow = self.allow)
            label = ReadDicom("labels".join(postprocessed_dir.split("images")), allow = self.allow)
            pair = ReadImageLabelPair(image, label)
            pair.viewer.orthoview()

    def save_qc(self, orthoview: bool = True, **kwargs) -> None:
        for postprocessed_dir in tqdm(glob(os.path.join(self.DIRS.DIR_POSTPROCESS, 'images', '*/')), desc = f'writing QC images to {self.DIRS.DIR_QC}'):
            image = ReadDicom(postprocessed_dir, allow = self.allow)
            label = ReadDicom("labels".join(postprocessed_dir.split("images")), allow = self.allow)
            pair = ReadImageLabelPair(image, label) 
            self.qc_saver.save(os.path.join(self.DIRS.DIR_QC, os.path.basename(postprocessed_dir.strip('/'))), pair, orthoview = orthoview, **kwargs)

    def get_csv_path(self, csv_name: str) -> pathlib.Path:
        if csv_name:
            return os.path.join(self.DIRS.DIR_MEASUREMENTS, csv_name)
        else:
            return os.path.join(self.DIRS.DIR_MEASUREMENTS, 'volume_measurements.csv')

    def write_csv(self, csv_name: str) -> None:
        with open(self.get_csv_path(csv_name), 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=['case', 'volume cm^3'])
            writer.writeheader()
            for case, volume in self.volume.items():
                writer.writerow({'case': case, 'volume cm^3': volume})
    
    def calculate_volume(self, csv_name: str = False) -> None:
        for postprocessed_dir in tqdm(glob(os.path.join(self.DIRS.DIR_POSTPROCESS, 'images', '*/')), desc = 'calculating volume...'):
            image = ReadDicom(postprocessed_dir, allow = self.allow)
            label = ReadDicom("labels".join(postprocessed_dir.split("images")), allow = self.allow)
            pair = ReadImageLabelPair(image, label) 
            self.volume[os.path.basename(postprocessed_dir.strip('/'))] = pair.get_volume()/1000
        self.write_csv(csv_name)
        
    

