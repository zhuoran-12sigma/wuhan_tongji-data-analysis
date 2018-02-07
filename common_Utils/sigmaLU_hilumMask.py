import nibabel as nib
import numpy as np

class SigmaLU_HilumMask(object):
    '''
    This is the SigmaLU_HilumMask class to get the parameters of hilum location
    Author Siqi Qin
    '''
    def __init__(self, file):
        '''
        :param file: input lungmask.nii
        '''
        self._mask_file = nib.load(file)
        self._shape = self._mask_file.shape
        self._img = self._mask_file.get_data()

    def getHilumCoord(self):
        '''
        Get the start and end point of hilum in x, y, z directions, referring to weiwei's Matlab code
        :return hilum_coord: coordinates, self._mask_file.affine: affine matrix from patient to RAS
        '''
        slice = self._shape[2]

        mask2D = []
        for s in range(slice):
            x, y = np.where(self._img[:, :, s] > 0)
            for i in range(x.shape[0]):
                mask2D.append([x[i], y[i], s])

        mask2D = np.asarray(mask2D)
        hilum_coord = {}
        x_min, y_min, z_min = np.min(mask2D, 0)
        x_max, y_max, z_max = np.max(mask2D, 0)
        x_min_hilum = x_min + (x_max - x_min) / 4.0
        x_max_hilum = x_max - (x_max - x_min) / 4.0
        hilum_coord['x_min'] = x_min_hilum
        hilum_coord['x_max'] = x_max_hilum
        hilum_coord['y_min'] = y_min
        hilum_coord['y_max'] = y_max
        hilum_coord['z_min'] = z_min
        hilum_coord['z_max'] = z_max

        return hilum_coord, self._mask_file.affine

if __name__ == '__main__':
    path = 'Z:\\Data02\\Results\\Lung_Cancer\\JSPH\\result_th0.36_20170821\\JSPH_1069884_Z1_500MM_Si_B70f.intermediate.lungMaskU8.nii'
    test = HilumMask(path)
    print(test.getHilumCoord())