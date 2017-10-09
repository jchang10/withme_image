from PIL import Image, ImageEnhance
import numpy as np
import colorsys

def rgb_to_hsv(rgb):
    # Translated from source of colorsys.rgb_to_hsv
    # r,g,b should be a numpy arrays with values between 0 and 255
    # rgb_to_hsv returns an array of floats between 0.0 and 1.0.
    rgb = rgb.astype('float')
    hsv = np.zeros_like(rgb)
    # in case an RGBA array was passed, just copy the A channel
    hsv[..., 3:] = rgb[..., 3:]
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    maxc = np.max(rgb[..., :3], axis=-1)
    minc = np.min(rgb[..., :3], axis=-1)
    hsv[..., 2] = maxc
    mask = maxc != minc
    hsv[mask, 1] = (maxc - minc)[mask] / maxc[mask]
    rc = np.zeros_like(r)
    gc = np.zeros_like(g)
    bc = np.zeros_like(b)
    rc[mask] = (maxc - r)[mask] / (maxc - minc)[mask]
    gc[mask] = (maxc - g)[mask] / (maxc - minc)[mask]
    bc[mask] = (maxc - b)[mask] / (maxc - minc)[mask]
    hsv[..., 0] = np.select(
        [r == maxc, g == maxc], [bc - gc, 2.0 + rc - bc], default=4.0 + gc - rc)
    hsv[..., 0] = (hsv[..., 0] / 6.0) % 1.0
    return hsv

def hsv_to_rgb(hsv):
    # Translated from source of colorsys.hsv_to_rgb
    # h,s should be a numpy arrays with values between 0.0 and 1.0
    # v should be a numpy array with values between 0.0 and 255.0
    # hsv_to_rgb returns an array of uints between 0 and 255.
    rgb = np.empty_like(hsv)
    rgb[..., 3:] = hsv[..., 3:]
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    i = (h * 6.0).astype('uint8')
    f = (h * 6.0) - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    i = i % 6
    conditions = [s == 0.0, i == 1, i == 2, i == 3, i == 4, i == 5]
    rgb[..., 0] = np.select(conditions, [v, q, p, p, t, v], default=v)
    rgb[..., 1] = np.select(conditions, [v, v, v, q, p, p], default=t)
    rgb[..., 2] = np.select(conditions, [v, p, t, v, v, q], default=p)
    return rgb.astype('uint8')

def shift_hue(arr,hout):
    hsv=rgb_to_hsv(arr)
    hsv[...,0]=hout
    rgb=hsv_to_rgb(hsv)
    return rgb

def rotate_hue(arr,hout):
    hsv=rgb_to_hsv(arr)
    hsv[...,0] = (hsv[...,0] + (hout/360)) % 1
    rgb=hsv_to_rgb(hsv)
    return rgb

def adjust_hsv_hue(hsv, val):
    hsv[...,0] = (hsv[...,0] + (val/360)) % 1
    return hsv

def adjust_hsv_sat(hsv, val):
    hsv[...,1] = (hsv[...,1] * val) % 1
    return hsv

def adjust_hsv_val(hsv, val):
    hsv[...,2] *= val
    hsv[...,2] = hsv[...,2].clip(0, 255)
    return hsv

def img_to_hsv(img):
    arr = np.array(np.asarray(img).astype('float'))
    hsv = rgb_to_hsv(arr)
    return hsv

def hsv_to_img(hsv):
    rgb = hsv_to_rgb(hsv)
    return Image.fromarray(rgb, 'RGBA')

def _rotate_hue(arr,hout):
    hsv=rgb_to_hsv(arr)
    hsv[...,0] = (hsv[...,0] + (hout/360)) % 1
    rgb=hsv_to_rgb(hsv)
    return rgb

def new_rotate_hue(image, hue):
    """
    Colorize PIL image `original` with the given
    `hue` (hue within 0-360); returns another PIL image.
    """
    img = image.convert('RGBA')
    arr = np.array(np.asarray(img).astype('float'))
    new_img = Image.fromarray(_rotate_hue(arr, hue).astype('uint8'), 'RGBA')

    return new_img

def new_grayscale(image):
    newim = Image.new('LA', image.size)
    newim.paste(image, (0,0), image)
    newim = newim.convert('RGBA')
    return newim

def new_hair_color(image, color):
    newim = None
    if color == 'black':
        newim = new_grayscale(image)
        newim = ImageEnhance.Brightness(newim).enhance(0.5)
    elif color == 'blonde':
        # hsv = img_to_hsv(image)
        # hsv = adjust_hsv_hue(hsv, 23)
        # hsv = adjust_hsv_val(hsv, 1.2)
        # newim = hsv_to_img(hsv)
        newim = new_rotate_hue(image, 20)
        newim = ImageEnhance.Brightness(newim).enhance(1.6)
    elif color == 'darkbrown':
        newim = ImageEnhance.Brightness(image).enhance(0.6)
    elif color == 'white':
        newim = new_grayscale(image)
        newim = ImageEnhance.Brightness(newim).enhance(1.5)
    return newim


#enhancer = ImageEnhance.Brightness(im)
#%bbenhancer.enhance(0.5).show()

im, hsv, newim = (None,)*3

def test1():
    global im, hsv, newim
    im = Image.open('test.jpg')
    newim = colorize(im, 350)
    im = Image.open('items/hairs/hair0.png')
    hsv = img_to_hsv(im)
    
