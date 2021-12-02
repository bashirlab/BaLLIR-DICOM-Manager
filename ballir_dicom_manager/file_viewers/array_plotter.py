

from matplotlib.patches import Patch
from matplotlib import pyplot as plt

class ArrayPlotter:
    
    zoom: int = 1
    legend_size: int = 12
    
#     def __init__(self)
        
    def add_legend(self, ax, legend):
        legend_elements = [Patch(facecolor = legend[j][1], edgecolor = legend[j][1], label = legend[j][0]) for j in range(len(legend))]
        return ax.legend(handles=legend_elements, loc='upper left', prop={'size':  self.legend_size * self.zoom})
        
    def plot_images(self, image_list, **kwargs):
        fig = plt.figure(figsize = (15 * self.zoom, 15 * self.zoom), dpi = 64)
        for i in range(1, (1 + len(image_list))):
            ax = fig.add_subplot(1, len(image_list), i)
            if 'legend' in kwargs: 
                ax = self.add_legend(ax, kwargs['legend'])
            plt.imshow(image_list[i - 1], cmap = 'gray')