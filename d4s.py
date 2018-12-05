def get_d4sigma(array, pix_size):
    ''' (d4s_x, s4s_y, centr_x, centr_y) = get_d4sigma(array, pix_size)
    
    returns the d4sigma as well as the centroids for X and Y
    array:    2D numpy array with data
    pix_size:   pixel size; square pixels are assumed
    important: background is zero on average!!!   '''
    
    import numpy as np
    
    array = array-np.min(array)
    f_y, f_x = array.shape
    
    #(uses 'D4sigma or second moment width' from wikipedia
    #get centroids
    x = np.linspace(1, f_x, f_x)
    y = np.linspace(1, f_y, f_y)
    x, y = np.meshgrid(x, y)
    total_sum = np.sum(array)
    centr_nom_x = np.sum(array * x)
    centr_nom_y = np.sum(array * y)
    centroid_x = centr_nom_x / total_sum
    centroid_y = centr_nom_y / total_sum

    #determine D4sigma values
    d4s_nom_x = np.sum(array * np.power(((x) - centroid_x), 2))
    d4s_nom_y = np.sum(array * np.power(((y) - centroid_y), 2))
    d4s_x = 4*np.power(d4s_nom_x / total_sum, 0.5) * pix_size
    d4s_y = 4*np.power(d4s_nom_y / total_sum, 0.5) * pix_size

    return (d4s_x, d4s_y, centroid_x, centroid_y)
