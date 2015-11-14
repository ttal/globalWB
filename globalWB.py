import wx
import cv2
import numpy as np
import file_transfers

video_feed, projection_detect, fine_tune_draw, fine_tune_calc, use_merged = False, False, False, False, False
global_rect, global_frame, global_transform_matrix = None, None, None
camera_matrix, distortion_coeffs, new_camera_matrix = None, None, None
post_image = False


class ShowCapture(wx.Panel):
    def __init__(self, parent, capture, fps=4, control_frame=True,
                 chessboard_img='chessboard.png', cb_corners=(9, 6),
                 screen_capture_file_name='gwb_screen_capture.png', merged_file_name='merged.png'):
        wx.Panel.__init__(self, parent)

        self.parent = parent
        self.control_frame = control_frame
        self.capture = capture
        ret, self.frame = self.capture.read()
        self.height, self.width = self.frame.shape[:2]
        self.parent.SetSize((self.width, self.height))
        self.coords = []
        self.count = 0

        self.screen_capture_file_name = screen_capture_file_name
        self.merged_file_name = merged_file_name
        self.sft = file_transfers.FileTransfers(self.screen_capture_file_name, self.merged_file_name)

        if not control_frame:
            self.chessboard_img = cv2.resize(cv2.imread(chessboard_img), (self.width, self.height))
            self.cb_corners = cb_corners
            self.obj_points = np.zeros((self.cb_corners[1] * self.cb_corners[0], 3), np.float32)
            self.obj_points[:,:2] = np.mgrid[0:cb_corners[0], 0:cb_corners[1]].T.reshape(-1, 2)
            self.criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

        if self.control_frame:
            self.calibrate = wx.ToggleButton(self, 1, 'calibrate')
            self.calibrate.SetValue(True)
            self.save_frame = wx.Button(self, 2, 'save to file', (380, -1))

            self.detect_screen()
            self.frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)

        else:
            if video_feed:
                self.frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)

            else:
                self.frame = np.ones((self.width, self.height, 3), np.uint8) * 255

        self.bmp = wx.BitmapFromBuffer(self.width, self.height, self.frame)

        self.timer = wx.Timer(self)
        self.timer.Start(1000. / fps)

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_TIMER, self.NextFrame)

        if self.control_frame:
            self.Bind(wx.EVT_TOGGLEBUTTON, self.ToggleCalibrate, id=1)
            self.Bind(wx.EVT_BUTTON, self.SaveToFile, id=2)

    def OnPaint(self, event):
        dc = wx.BufferedPaintDC(self)
        dc.DrawBitmap(self.bmp, 0, 0)

    def NextFrame(self, event):
        global projection_detect, global_frame, fine_tune_draw, fine_tune_calc, use_merged, post_image

        ret, self.frame = self.capture.read()
        if ret:
            if self.control_frame:
                if self.calibrate.GetValue():
                    self.detect_screen()
                    self.frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
                else:
                    self.frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)

            else:
                if video_feed:

                    if projection_detect:
                        self.detect_screen(draw_contours=False)
                        projection_detect = False
                    self.expand_image()

                    if not fine_tune_calc:
                        self.remove_background()

                    if fine_tune_calc:
                        self.find_chessboard_distortions()
                        self.frame = np.ones((self.width, self.height, 3), np.uint8) * 255

                        fine_tune_calc = False

                    if fine_tune_draw:
                        self.frame = self.chessboard_img.copy()
                        #cv2.imwrite('cb_project.png', self.frame)
                        self.count += 1

                        if self.count > 3:
                            fine_tune_draw = False
                            fine_tune_calc = True
                            post_image = True
                            #self.frame = np.ones((self.width, self.height, 3), np.uint8) * 255

                    if post_image:
                        cv2.imwrite(self.screen_capture_file_name, self.frame)
                        self.sft.post_file()
                        use_merged = True
                    #if use_merged:
                        self.sft.get_file()
                        self.frame = cv2.imread(self.merged_file_name)

                else:
                    self.frame = np.ones((self.width, self.height, 3), np.uint8) * 255
                    projection_detect = True

                global_frame = self.frame
                cv2.imwrite(self.screen_capture_file_name, self.frame)

            self.bmp.CopyFromBuffer(self.frame)
            self.Refresh()

    def ToggleCalibrate(self, event):
        global video_feed, fine_tune_draw, global_transform_matrix

        if self.calibrate.GetValue():
            video_feed = False
            global_transform_matrix = None
        else:
            video_feed = True
            fine_tune_draw = True
            self.count = 0

    def SaveToFile(self, event):
        global global_frame
        cv2.imwrite('gwb_frame.png', cv2.cvtColor(global_frame, cv2.COLOR_BGR2RGB))

    def detect_screen(self, blur_pars=(21, 17, 17), draw_contours=True):
        gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, *blur_pars)
        edged = cv2.Canny(gray, 30, 200)

        (_, contours, _) = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
        screen_contour = []

        for c in contours:
            # approximate the contour
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)

            if len(approx) == 4:
                screen_contour = approx
                break

        if len(screen_contour):
            global global_rect

            coords = np.array([[i[0][0], i[0][1]] for i in screen_contour])
            if draw_contours:
                cv2.drawContours(self.frame, [screen_contour], -1, (0, 0, 255), 3)

            global_rect = self.order_points(coords)

    def order_points(self, coords):
        rect = np.zeros((4, 2), dtype="float32")

        s = coords.sum(axis=1)
        diff = np.diff(coords, axis=1)

        rect[0] = coords[np.argmin(s)]
        rect[2] = coords[np.argmax(s)]
        rect[1] = coords[np.argmin(diff)]
        rect[3] = coords[np.argmax(diff)]

        return rect

    def expand_image(self):
        global global_transform_matrix, new_camera_matrix, camera_matrix, distortion_coeffs

        if global_transform_matrix is None:
            if global_rect is not None:
                dst = np.array([[0, 0],
                                [self.width, 0],
                                [self.width, self.height],
                                [0, self.height]], dtype='float32')
                global_transform_matrix = cv2.getPerspectiveTransform(global_rect, dst)

        if new_camera_matrix is not None:
            self.frame = cv2.undistort(self.frame, camera_matrix, distortion_coeffs, None, new_camera_matrix)

        self.frame = cv2.warpPerspective(self.frame, global_transform_matrix, (self.width, self.height), flags=cv2.INTER_CUBIC)

    def remove_background(self, power_factor=1.0, stdev_factor=1.5, gauss_kernel=51):
        (B, G, R) = cv2.split(self.frame.astype('float32'))

        gB = cv2.GaussianBlur(B, (gauss_kernel, gauss_kernel), 0)
        gG = cv2.GaussianBlur(G, (gauss_kernel, gauss_kernel), 0)
        gR = cv2.GaussianBlur(R, (gauss_kernel, gauss_kernel), 0)
        removed = cv2.merge((R/gR, G/gG, B/gB))

        removed_stdev = np.std(removed)
        if removed_stdev == removed_stdev:
            removed = (removed - stdev_factor * np.std(removed)) ** power_factor

        w_saturated = removed >= 1.0
        if np.sum(w_saturated):
            removed[w_saturated] = 1.0
        removed = (removed * 255.).astype('uint8')

        self.frame = removed

    def draw_circles(self, circle_radius=15):
        single_channel = np.ones((self.height, self.width), np.uint8) * 255

        for cp in self.circle_positions:
            cv2.circle(single_channel, (cp[0], cp[1]), circle_radius, [0, 0, 0], -1)

        self.frame = cv2.merge((single_channel, single_channel, single_channel))

    def find_chessboard_distortions(self):
        global new_camera_matrix, camera_matrix, distortion_coeffs

        #cv2.imwrite('cb_read.png', self.frame)
        gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)

        _, corners = cv2.findChessboardCorners(gray, self.cb_corners, flags=cv2.CALIB_CB_ADAPTIVE_THRESH)
        corners_sub_pix = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), self.criteria)

        _, camera_matrix, distortion_coeffs, _, _ = cv2.calibrateCamera([self.obj_points], [corners_sub_pix],
                                                                        gray.shape[::-1], None, None)
        new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(camera_matrix, distortion_coeffs,
                                                               (self.width, self.height), 1, (self.width, self.height))


class MainLoop:
    def __init__(self):
        app = wx.App()

        # create and show window to be projected
        projection_display = wx.Display(1)
        projection_geometry = projection_display.GetGeometry()
        projection_frame = wx.Frame(None)
        projection_frame.SetPosition((projection_geometry[0], projection_geometry[1]))
        projection_frame.SetSize((projection_geometry[2], projection_geometry[3]))

        projection_capture = cv2.VideoCapture(0)
        projection_capture.set(cv2.CAP_PROP_FRAME_WIDTH, projection_geometry[2])
        projection_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, projection_geometry[3])
        blank = ShowCapture(projection_frame, projection_capture, control_frame=False)
        projection_frame.Show()
        projection_frame.ShowFullScreen(True)

        # create and show control window
        control_frame = wx.Frame(None)
        control_frame.SetSize((480, 360))

        control_capture = cv2.VideoCapture(0)
        control_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
        control_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
        cap = ShowCapture(control_frame, control_capture)
        control_frame.Show()

        app.MainLoop()

if __name__ == '__main__':
    x = MainLoop()
