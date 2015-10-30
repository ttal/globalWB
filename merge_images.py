import cv2
import sys
import numpy as np


class ImageMerge:
    def __init__(self, in_img1, in_img2):
        img1 = cv2.imread(in_img1, cv2.CV_LOAD_IMAGE_UNCHANGED)
        img2 = cv2.imread(in_img2, cv2.CV_LOAD_IMAGE_UNCHANGED)

        self.img1_split = cv2.split(img1)
        self.img2_split = cv2.split(img2)

        im_dims = self.img1_split[0].shape
        self.im_out_split = np.zeros((4, im_dims[0], im_dims[1]), np.uint8)
        self.im_out = None

    def combine(self):
        w_alpha1_only = (self.img1_split[3] == 255) & (self.img2_split[3] != 255)
        w_alpha2_only = (self.img1_split[3] != 255) & (self.img2_split[3] == 255)
        w_alpha_both = (self.img1_split[3] == 255) & (self.img2_split[3] == 255)
        w_alpha_either = (self.img1_split[3] == 255) | (self.img2_split[3] == 255)

        for i in range(3):
            self.im_out_split[i][w_alpha1_only] = self.img1_split[i][w_alpha1_only]
            self.im_out_split[i][w_alpha2_only] = self.img2_split[i][w_alpha2_only]
            self.im_out_split[i][w_alpha_both] = np.average([self.img1_split[i][w_alpha_both],
                                                             self.img2_split[i][w_alpha_both]], axis=0)
        self.im_out_split[3][w_alpha_either] = 255

        self.im_out = cv2.merge(self.im_out_split, 4)


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print 'syntax:\n python merge_images.py image1 image2, output'
        sys.exit(1)
    else:
        IM = ImageMerge(sys.argv[1], sys.argv[2])
        IM.combine()
        cv2.imwrite(sys.argv[3], IM.im_out)
