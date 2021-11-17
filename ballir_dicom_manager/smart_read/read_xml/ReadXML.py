from tools.ReadScan import *
from tools.ReadDicom import *
from tools.manage_dicom import *
from tools.shortcuts import *
from tools.manage_dicom import *

from ast import literal_eval
from copy import deepcopy
import xmltodict
from skimage.draw import polygon
from scipy import interpolate

# -- CONVERT XML to NUMPY


def get_roi_coords(roi):

    # get index of ROI
    ind = int(roi['integer'][1])
    # get coordinate data of ROI
    x = roi['array']['dict']['array'][1]['string']
    # convert string coordinates to tuples
    coords = [literal_eval(coord) for coord in x]
    # parse out x and y and make closed loop
    x = [i[0] for i in coords] + [coords[0][0]]
    y = [i[1] for i in coords] + [coords[0][1]]
    # apply parametric spline interpolation
    tck, _ = interpolate.splprep([x,y], s=0, per=True)
    x, y = interpolate.splev(np.linspace(0,1,500), tck)
    
    
    return ind, x, y


def xml2numpy(file_xml, loc_save = False, file_save = False, z_reversed = False):
    
    with open(file_xml, 'r') as f: 
        xml_data = xmltodict.parse(f.read())
    
    roi_list = xml_data['plist']['dict']['array']['dict']
    
    if float(roi_list[0]['array']['dict']['string'][0].split('(')[-1].split(')')[0].split(',')[2]) > float(roi_list[1]['array']['dict']['string'][0].split('(')[-1].split(')')[0].split(',')[2]):
        z_reversed = True
    else:
        z_reversed = False
    
    file_npy = np.zeros((int(roi_list[0]['integer'][0]), int(roi_list[0]['integer'][3]), int(roi_list[0]['integer'][2])))
    
    for roi in roi_list:
        ind, x, y = get_roi_coords(roi)
        rr, cc = polygon(y, x)
        
        if z_reversed:
            file_npy[rr, cc, int(roi['integer'][1])] = 1.0
        else:
            file_npy[rr, cc, int(file_npy.shape[2] -1 - int(roi['integer'][1]))] = 1.0
        
    if file_save:
        if not loc_save:
            print('NUMPY SAVE LOCATION NOT PROVIDED')
        else:
            np.save(loc_save, file_save)
    
    return file_npy


# -- convert XML to DICOM

def xml2dicom(file_xml, template = False, z_reversed = False):
#         if file_save and dir_save:
#         buildDIR(dir_save)
    
    arr_mask = xml2numpy(file_xml)

    if template: 
        files_dicom = [decompress_dicom(deepcopy(file)) for file in template]
        for file_dicom in files_dicom:
            file_dicom.RescaleSlope = 1.0
            file_dicom.RescaleIntercept = 0.0
    else:
        files_dicom = [new_dicom(arr_mask[..., i]) for i in range(arr_mask.shape[2])]
        for num, file in enumerate(files_dicom):
            file.ImagePositionPatient = [0, 0, num]
            file.SliceLocation = num
            file.InstanceNumber = num
    
    for num, file in enumerate(files_dicom):
        file.PixelData = arr_mask[..., num].astype('int16').tobytes()
        file = reset_dicom(file)
        file.Rows = arr_mask.shape[1]
        file.Columns = arr_mask.shape[1]
    
    return files_dicom



class ReadXML(ReadDicom):
    
    def __init__(self, file_xml, template = False, filter_tags = False, sort_by = False, flip_arr = False, fix_dicoms = False):
        
        
        #add something to check for inconsistencies in dicom files...slice thickness, etc., 
        scan = xml2dicom(file_xml, template = template)
        if fix_dicoms: 
            scan = fix_dicoms(scan, template = template)
        
        #edit so if not filter it reads the full files, otherwise it stops before pixel values, then reads pixel values after filtering
        if filter_tags:
            dict_tags, dict_max = check_tags(scan, filter_tags)
            self.dict_tags = dict_tags
            self.dict_max = dict_max
            for key, value in filter_tags.items():
                if value == 'max':
                    scan = [file for file in scan if getattr(file, key) == dict_max[key]]
                else:
                    scan = [file for file in scan if getattr(file, key) == value]
                
        if sort_by:
            if type(sort_by) == str:
                list_sort = [getattr(file, sort_by) for file in scan]
            elif type(sort_by) == dict:
                (tag, ind), = sort_by.items()
                list_sort = [getattr(file, tag)[ind] for file in scan]
            else:
                print('ERROR: [sort_by] enter either string or dict type as arg')
            scan = [x for _, x in sorted(zip(list_sort, scan))]
        
        arr = np.array([file.pixel_array for file in scan]); arr = np.swapaxes(arr, 0, 2); arr = np.flip(arr, 1)
        if not flip_arr: arr = np.flip(arr, 2)
        
        type_arr = arr.dtype
        
        self.scan = scan
        self.root_file = file_xml
        self.root_type = 'XML'
        #self.scan_type = 'MR', 'CT', etc.
        self.arr = arr
        self.length = arr.shape[2]
        self.spacing = scan[0].PixelSpacing; self.spacing.append(scan[0].SliceThickness)
        self.range = [self.spacing[0] * self.arr.shape[0], self.spacing[1] * self.arr.shape[1], self.spacing[2] * self.arr.shape[2]]
        self.flip = flip_arr
        self.decompress = False
        
      

        
    
    
    