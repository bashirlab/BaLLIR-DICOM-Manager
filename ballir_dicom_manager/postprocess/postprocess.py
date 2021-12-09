import pathlib
import os
import copy
import csv
from typing import List, Dict

import numpy as np
from glob import glob
from tqdm import tqdm
import pydicom as dcm

from ballir_dicom_manager.directory_manager import DirManager
from ballir_dicom_manager.file_readers.read_nifti import ReadNifti
from ballir_dicom_manager.file_readers.read_dicom import ReadDicom, ReadRawDicom
from ballir_dicom_manager.file_readers.read_image_label_pair import ReadImageLabelPair
from ballir_dicom_manager.file_writers.save_measurements_to_csv import MeasurementSaver
from ballir_dicom_manager.file_writers.save_qc_images import QCSaver

# both this and preprocess image/label combo should inheret from image_label_reader
class PostProcess:

    qc_saver = QCSaver()
    measurements = MeasurementSaver()
    volume = {}
    
    def __init__(self, DIR_PRE_DICOM, DIR_PRE_NIFTI, DIR_INFERENCE, allow = []):
        self.verify_inference_complete(DIR_PRE_NIFTI, DIR_INFERENCE, allow)
        DIR_POSTPROCESS = "postprocessed".join(DIR_INFERENCE.split("inference"))
        DIR_QC = os.path.join(DIR_POSTPROCESS, 'QC')
        DIR_MEASUREMENTS = os.path.join(DIR_POSTPROCESS, 'MEASUREMENTS')
        self.DIRS = DirManager(
            DIR_PRE_DICOM = DIR_PRE_DICOM,
            DIR_PRE_NIFTI = DIR_PRE_NIFTI,
            DIR_INFERENCE = DIR_INFERENCE,
            DIR_POSTPROCESS = DIR_POSTPROCESS,
            DIR_QC = DIR_QC,
            DIR_MEASUREMENTS = DIR_MEASUREMENTS,
        )
        self.allow = allow

    def verify_inference_complete(self, DIR_PRE_NIFTI: pathlib.Path, DIR_INFERENCE: pathlib.Path, allow) -> None:
        preprocessed_paths = set(os.path.basename(case).split('_0000.nii.gz')[0] for case in glob(os.path.join(DIR_PRE_NIFTI, '*.nii.gz')))
        inference_paths = set(os.path.basename(case).split('.nii.gz')[0] for case in glob(os.path.join(DIR_INFERENCE, '*.nii.gz')))
        missing_inference_files = preprocessed_paths.difference(inference_paths)
        if not 'missing_inference' in allow:
            assert len(missing_inference_files) == 0, f'{len(missing_inference_files)} preprocessed files in {DIR_PRE_NIFTI} are not accounted for in {DIR_INFERENCE}: {missing_inference_files}, continue inference or pass "missing_inference" in allow list'
        
    def get_dicom_path(self, nifti_path: pathlib.Path) -> pathlib.Path:
        return os.path.join(self.DIRS.DIR_PRE_DICOM, os.path.basename(nifti_path).split('_0000.nii.gz')[0])
    
    def get_label_path(self, nifti_path: pathlib.Path) -> pathlib.Path:
        return os.path.join(self.DIRS.DIR_INFERENCE, ".nii.gz".join(os.path.basename(nifti_path).split("_0000.nii.gz")))
    
    def read_files(self, nifti_path: pathlib.Path):
        nifti_read_image = ReadNifti(nifti_path)
        nifti_read_label = ReadNifti(self.get_label_path(nifti_path))
        dicom_read_image = ReadRawDicom(self.get_dicom_path(nifti_path), allow = self.allow)
        dicom_read_label = copy.deepcopy(dicom_read_image)
        return nifti_read_image, nifti_read_label, dicom_read_image, dicom_read_label
   
    def copy_nifti_to_dicom(self, nifti_read: ReadNifti, dicom_read: ReadDicom) -> ReadDicom:
        '''Copy pixel data from segmentation output NIFTI file to original (raw path) DICOM meta data.'''
        nifti_pixel_array = (nifti_read.files[0].get_fdata())
        dicom_read.files = dicom_read.writer.write_array_volume_to_dicom(nifti_pixel_array, dicom_read.files)
        return dicom_read
        
    def postprocess(self) -> None:
        for nifti_path in tqdm(glob(os.path.join(self.DIRS.DIR_PRE_NIFTI, '*.nii.gz')), desc = 'postprocessing...'):
            nifti_image, nifti_label, dicom_image, dicom_label = self.read_files(nifti_path)
            dicom_image = self.copy_nifti_to_dicom(nifti_image, dicom_image)
            dicom_label = self.copy_nifti_to_dicom(nifti_label, dicom_label)
            dicom_image_write_dir = os.path.join(self.DIRS.DIR_POSTPROCESS, 'images', os.path.basename(nifti_path.split("_0000.nii.gz")[0]))
            dicom_image.writer.save_all(dicom_image.files, dicom_image_write_dir)
            dicom_label_write_dir = os.path.join(self.DIRS.DIR_POSTPROCESS, 'labels', os.path.basename(nifti_path.split("_0000.nii.gz")[0]))
            dicom_label.writer.save_all(dicom_label.files, dicom_label_write_dir)

    def preview_postprocessed_dicom(self, **kwargs) -> None:
        '''Display segmentation mask overlay of postprocessed DICOM data as RGB.'''
        for postprocessed_dir in tqdm(glob(os.path.join(self.DIRS.DIR_POSTPROCESS, 'images', '*/')), desc = 'generating previews of postprocessed DICOM data...'):
            case_kwargs = copy.deepcopy(kwargs)
            if 'legend' in case_kwargs: case_kwargs['legend'].append([os.path.basename(postprocessed_dir.rstrip('/')), '#808080'])
            image = ReadDicom(postprocessed_dir, allow = self.allow)
            label = ReadDicom("labels".join(postprocessed_dir.split("images")), allow = self.allow)
            pair = ReadImageLabelPair(image, label, **kwargs)
            pair.viewer.orthoview(**case_kwargs)

    def save_qc(self, orthoview: bool = True, **kwargs) -> None:
        '''Save QC images with RGB overlay of segmentation masks.'''
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

    def write_csv(self, csv_name: str, volume: dict, label_key: Dict[str, int]) -> None:
        '''Write volume measurements as csv file.'''
        fieldnames = ['case'] + list(label_key.keys()) #[f'{label_name} volume (cm^3)' for label_name in list(label_key.keys())]
        with open(self.get_csv_path(csv_name), 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for case, label_volume_key in self.volume.items():
                writer.writerow({'case': case, **label_volume_key})
                # case_volumes = {}
                # for label_name, label_volume in label_volume_key.items():

                #     writer.writerow({'case': case, 'volume cm^3': volume})

    def calculate_volume_for_all_labels(self, pair: ReadImageLabelPair, label_key: Dict[str, int]) -> Dict[str, int]:
        return {label_name: pair.get_volume(read_dicom_label = pair.read_dicom_label, label_value = label_value)/1000 for label_name, label_value in label_key.items()}

    def calculate_volume(self, csv_name: str = False, label_key: Dict[str, int] = {'Segmentation Mask': 1}) -> None:
        '''
        Calculate volume as cm^3 for all patients. e.g., label_values = {liver: 1, tumor: 2}.
        Builds nested dict with {case_name: {liver: 1500cm^3, tumor: 300cm^3}}....
        '''
        for postprocessed_dir in tqdm(glob(os.path.join(self.DIRS.DIR_POSTPROCESS, 'images', '*/')), desc = 'calculating volume...'):
            read_dicom_image = ReadDicom(postprocessed_dir, allow = self.allow)
            read_dicom_label = ReadDicom("labels".join(postprocessed_dir.split("images")), allow = self.allow)
            pair = ReadImageLabelPair(read_dicom_image, read_dicom_label) 
            self.volume[os.path.basename(postprocessed_dir.strip('/'))] = self.calculate_volume_for_all_labels(pair = pair, label_key = label_key)
        self.write_csv(csv_name = csv_name, volume = self.volume, label_key = label_key)
        
    

