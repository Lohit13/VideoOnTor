from PIL import Image
import math
from skimage import img_as_float
from skimage.measure import compare_mse as mse

def rmsdiff(im1, im2):
	i1 = Image.open(im1)
	i2 = Image.open(im2)
	return math.sqrt(mse(img_as_float(i1), img_as_float(i2)))