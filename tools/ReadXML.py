from tools.ReadDicom import *
from tools.shorcuts import *
from tools.manage_dicom import *

import copy

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
    
    
    