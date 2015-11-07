import cv2
import sys
import numpy as np


class ImageMerge:
    def __init__(self, in_img1, in_img2):
        self.img1 = cv2.imread(in_img1)
        self.img2 = cv2.imread(in_img2)
        self.im_out = None

        im_dims = self.img1.shape
        self.im_out_split = np.zeros((3, im_dims[0], im_dims[1]), np.uint8)

    def combine(self):

        img1_split = cv2.split(self.img1)
        img2_split = cv2.split(self.img2)

        for i in range(3):
            self.im_out_split[i] = np.min([img1_split[i], img2_split[i]], axis=0)

        self.im_out = cv2.merge(self.im_out_split)


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print 'syntax:\n python merge_images.py image1 image2, output'
        sys.exit(1)
    else:
        IM = ImageMerge(sys.argv[1], sys.argv[2])
        IM.combine()
        cv2.imwrite(sys.argv[3], IM.im_out)
