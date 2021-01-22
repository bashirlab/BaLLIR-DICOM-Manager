from tools.ReadDicom import *
from tools.shorcuts import *
from tools.manage_dicom import *

import copy

# -- CONVERT XML to NUMPY

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
        ind, x, y = getROIcoords(roi)
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
    
    return file_npy, flipCheck


# -- convert XML to DICOM

def xml2dicom(file_xml, template_dcm = False, dir_save = False, file_save = True, z_reversed = False, step_size = False):
    
    file_npy = xml2numpy(file_xml, file_save = False, z_reversed = z_reversed)
    file_npy = file_npy.astype('uint16')
    file_dcm = []
    
    if  file_save and dir_save:
        buildDIR(dir_save)
      
    for num_slice in range(file_npy.shape[2]):
        
        slice_dcm = buildDCM()
#         slice_dcm = copy.deepcopy(template_dcm)#buildDCM()
        slice_dcm.file_meta.TransferSyntaxUID = '1.2.840.10008.1.2.1'
        slice_dcm.Rows = file_npy.shape[0]
        slice_dcm.Columns = file_npy.shape[1]
        slice_dcm.InstanceNumber = num_slice
        slice_dcm.PixelSpacing = template_dcm.PixelSpacing
        slice_dcm.ImagePositionPatient[0] = template_dcm.ImagePositionPatient[0]
        slice_dcm.ImagePositionPatient[1] = template_dcm.ImagePositionPatient[1]
        slice_dcm.ImageOrientationPatient = [1, 0, 0, 0, 1, 0] #template_dcm.ImageOrientationPatient
        
        if template_dcm and step_size:
#             slice_dcm = copy.deepcopy(template_dcm)
            slice_dcm.ImagePositionPatient[2] = float(template_dcm.ImagePositionPatient[2] + (num_slice*step_size))
            slice_dcm.SliceThickness = template_dcm.SliceThickness
        else:
            print('ERROR: no template provided')
            slice_dcm.ImagePositionPatient[2] = -float(num_slice)
            slice_dcm.SliceThickness = 5.0
            
        
        slice_dcm.PixelData = file_npy[..., num_slice].tobytes()#np.ascontiguousarray(file_npy[..., num_slice])
        file_dcm.append(slice_dcm)
        
#         if not template_dcm:
#             slice_dcm['PixelData'].VR = 'OW'
            
#         file_dcm.append(slice_dcm)
        
        if file_save:
            if not dir_save:
                print('DICOM SAVE DIRECTORY NOT PROVIDED')
            else:
                loc_save = os.path.join(dir_save, str(num_slice).zfill(4) + '.dcm')
                slice_dcm.save_as(loc_save)
    
    return file_dcm



class ReadXML(ReadDicom):
    
    def __init__(self, file_xml, template = False):
        
        if template:
            scan = [copy.deepcopy(file) for file in template]
            scan =decompressDicoms(scan)
        else:
            scan = [newDicom() for file in range(len(xml..something...))]
         
        # do this with super init??
    self.root_file = file_xml
    self.root_type = 'XML'
    #self.scan_type = 'MR', 'CT', etc.
    self.scan = scan
    self.arr = arr
    self.length = arr.shape[2]
    self.spacing = scan[0].PixelSpacing; self.spacing.append(scan[0].SliceThickness)
    self.range = [self.spacing[0] * self.arr.shape[0], self.spacing[1] * self.arr.shape[1], self.spacing[2] * self.arr.shape[2]]
    self.window_width = window_width
    self.window_center = window_center
    self.rescale_slope = rescale_slope
    self.rescale_intercept = rescale_intercept
    
    
    