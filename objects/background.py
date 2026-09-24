"""Local, edge-connected uniform background removal; no model downloads."""
import cv2
import numpy as np


def remove_uniform_background(image, tolerance=35):
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGRA)
    elif image.shape[2] == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
    result = image.copy()
    rgb = result[:,:,:3].astype(np.float32)
    border = np.concatenate((rgb[0], rgb[-1], rgb[:,0], rgb[:,-1]))
    background = np.median(border,axis=0)
    candidate = (np.max(np.abs(rgb-background),axis=2) <= tolerance).astype(np.uint8)
    count,labels = cv2.connectedComponents(candidate,connectivity=4)
    edge_labels = np.unique(np.concatenate((labels[0],labels[-1],labels[:,0],labels[:,-1])))
    edge_labels = edge_labels[edge_labels != 0]
    result[:,:,3][np.isin(labels,edge_labels)] = 0
    return result
