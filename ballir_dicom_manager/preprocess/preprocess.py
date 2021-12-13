import pathlib
import os
import logging
from datetime import datetime

import numpy as np
import dicom2nifti
from tqdm import tqdm
from glob import glob

from ballir_dicom_manager.directory_manager import DirManager
from ballir_dicom_manager.file_readers.read_dicom import ReadDicom
from ballir_dicom_manager.file_readers.read_nifti import ReadNifti
from ballir_dicom_manager.preprocess.dicom_finder import DicomFinder

log = logging.getLogger(__name__)


class PreProcess:

    dicom_finder = DicomFinder()

    def __init__(self, DIR_RAW, add_subgroup=False, value_clip=False, allow=[]):
        self.RAW_DICOM_DIRS = self.dicom_finder.get_dicom_dirs(DIR_RAW)
        DIR_PREPROCESSED = (
            "raw".join(DIR_RAW.split("raw")[:-1]) + "preprocessed"
        )  # join in case of 2nd "raw" dir somewhere in directory structure
        # option for images and labels?
        self.configure_logger(DIR_PREPROCESSED, add_subgroup)
        DIR_PRE_DICOM = self.get_preprocessed_dir(
            DIR_PREPROCESSED, image_type="dicom", add_subgroup=add_subgroup
        )
        DIR_PRE_NIFTI = self.get_preprocessed_dir(
            DIR_PREPROCESSED, image_type="nifti", add_subgroup=add_subgroup
        )
        self.DIRS = DirManager(
            DIR_RAW=DIR_RAW,
            DIR_PREPROCESSED=DIR_PREPROCESSED,
            DIR_PRE_DICOM=DIR_PRE_DICOM,
            DIR_PRE_NIFTI=DIR_PRE_NIFTI,
        )
        self.value_clip = value_clip
        self.allow = allow

    def configure_logger(self, log_directory: pathlib.Path, add_subgroup) -> None:
        log_date = datetime.now()
        log_date = "_".join(
            [
                str(log_date.year),
                str(log_date.month),
                str(log_date.day),
                str(log_date.hour),
                str(log_date.minute),
            ]
        )
        if add_subgroup:
            log_date = "_".join([add_subgroup, log_date])
        # set up log config
        logging.basicConfig(
            filename=os.path.join(
                log_directory,
                f"preprocess_{log_date}.log",
            ),
            level=logging.INFO,
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def get_preprocessed_dir(
        self, DIR_PREPROCESSED: pathlib.Path, image_type: str, add_subgroup
    ) -> pathlib.Path:
        if add_subgroup:
            return os.path.join(DIR_PREPROCESSED, image_type, "images", add_subgroup)
        else:
            return os.path.join(DIR_PREPROCESSED, image_type, "images")

    def clean_dicom(
        self, raw_dicom_dir: pathlib.Path, clean_dicom_dir: pathlib.Path
    ) -> None:
        raw = ReadDicom(raw_dicom_dir, value_clip=self.value_clip, allow=self.allow)
        raw.prep_for_nifti(raw.files)
        raw.writer.save_all(raw.files, clean_dicom_dir)
        log.info(f"{raw_dicom_dir} preprocessed as DICOM to {clean_dicom_dir}")

    def get_clean_dicom_dir(self, case_name) -> pathlib.Path:
        return os.path.join(self.DIRS.DIR_PRE_DICOM, case_name)

    def get_case_name(self, raw_dicom_dir, case_name_fn) -> str:
        if not case_name_fn:
            return os.path.basename(raw_dicom_dir)
        else:
            return case_name_fn(raw_dicom_dir)

    def write_nifti(self, clean_dicom_dir: pathlib.Path, case_name: str) -> None:
        nifti_write_path = os.path.join(
            self.DIRS.DIR_PRE_NIFTI, f"{case_name}_0000.nii.gz"
        )
        dicom2nifti.dicom_series_to_nifti(clean_dicom_dir, nifti_write_path)
        log.info(f"{clean_dicom_dir} preprocessed as NIFTI to {nifti_write_path}")

    def build_legend(self, dicom_dir: pathlib.Path, pixel_array: np.array, **kwargs):
        if "legend" in kwargs and not kwargs["legend"]:
            return kwargs
        if not "legend_size" in kwargs:
            kwargs["legend_size"] = 12
        if not "legend" in kwargs:
            kwargs["legend"] = [
                [
                    f"{os.path.basename(dicom_dir)}: {np.amin(pixel_array)}:{np.amax(pixel_array)}",
                    "#808080",
                ]
            ]
            return kwargs
        return kwargs

    def preview_raw_dicom(self, value_clip=False, **kwargs) -> None:
        """Generate orthoview previews of original/raw DICOM files."""
        for raw_dicom_dir in tqdm(
            glob(os.path.join(self.DIRS.DIR_RAW, "*/")),
            desc="generating previews of raw data...",
        ):
            raw_dicom = ReadDicom(
                raw_dicom_dir, allow=self.allow, value_clip=value_clip
            )
            raw_dicom.viewer.orthoview(
                **self.build_legend(raw_dicom_dir, raw_dicom.arr, **kwargs)
            )

    def preview_preprocessed_dicom(self, value_clip=False, **kwargs) -> None:
        """Generate orthoview previews of preprocessed DICOM files."""
        for clean_dicom_dir in tqdm(
            glob(os.path.join(self.DIRS.DIR_PRE_DICOM, "*/")),
            desc="generating previews of preprocessed DICOM data...",
        ):
            clean_dicom = ReadDicom(
                clean_dicom_dir, allow=self.allow, value_clip=value_clip
            )
            clean_dicom.viewer.orthoview(
                **self.build_legend(clean_dicom_dir, clean_dicom.arr, **kwargs)
            )

    def preview_preprocessed_nifti(self, value_clip=False, **kwargs) -> None:
        """Generate orthoview previews of preprocessed NIFTI files."""
        for nifti_path in tqdm(
            glob(os.path.join(self.DIRS.DIR_PRE_NIFTI, "*.nii.gz")),
            desc="generating previews of preprocessed NIFTI data...",
        ):
            nifti_file = ReadNifti(nifti_path, value_clip=value_clip)
            nifti_file.viewer.orthoview(
                **self.build_legend(nifti_path, nifti_file.arr, **kwargs)
            )

    def preprocess(self, case_name_fn=False) -> None:
        for raw_dicom_dir in tqdm(self.RAW_DICOM_DIRS, desc="preprocessing..."):
            # try:
            print(f"case: {raw_dicom_dir}")
            case_name = self.get_case_name(raw_dicom_dir, case_name_fn)
            clean_dicom_dir = self.get_clean_dicom_dir(case_name)
            self.clean_dicom(raw_dicom_dir, clean_dicom_dir)
            self.write_nifti(clean_dicom_dir, case_name)
            # except Exception as e:
            #     log.exception(e)
            #     print(f'ERROR converting {raw_dicom_dir}: {e}')


if __name__ == "__main__":
    main()
