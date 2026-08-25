import cv2, numpy as np
im = cv2.imread('ref/gun_pose3.png')
h,w = im.shape[:2]
print('shape', im.shape)
# sample background corners
for name,(y0,y1,x0,x1) in {'TR':(0,12,w-40,w),'TL':(0,8,0,20),'BR':(h-12,h,w-40,w)}.items():
    patch = im[y0:y1,x0:x1].reshape(-1,3)
    print(name, 'mean BGR', patch.mean(0).round(1), 'std', patch.std(0).round(1))
