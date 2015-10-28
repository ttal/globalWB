import wx
import cv2
import copy
import numpy as np

video_feed = False
global_rect = None
global_transform_matrix = None
projection_detect = False
global_frame = None
fine_tune_draw = False
fine_tune_calc = False


class ShowCapture(wx.Panel):
    def __init__(self, parent, capture, fps=4, control_frame=True):
        wx.Panel.__init__(self, parent)

        self.parent = parent
        self.control_frame = control_frame
        self.capture = capture
        ret, self.frame = self.capture.read()
        self.height, self.width = self.frame.shape[:2]
        self.parent.SetSize((self.width, self.height))
        self.coords = []
        self.count = 0

        self.circle_positions = [[50, 50], [self.width-50, 50],
                                 [self.width-50, self.height-50], [50, self.height-50]]

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
                self.frame = np.zeros((self.width, self.height, 3), np.int8)
                self.frame[:] = 255

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
        global projection_detect
        global global_frame
        global fine_tune_draw
        global fine_tune_calc

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
                    self.remove_background()

                    if fine_tune_calc:
                        self.find_offsets()

                        fine_tune_calc = False

                    if fine_tune_draw:
                        self.draw_circles()
                        self.count += 1

                        if self.count > 2:
                            fine_tune_draw = False
                            fine_tune_calc = True
                else:
                    self.frame = np.ones((self.width, self.height, 3), np.uint8) * 255
                    projection_detect = True

                global_frame = self.frame

            self.bmp.CopyFromBuffer(self.frame)
            self.Refresh()

    def ToggleCalibrate(self, event):
        global video_feed
        global fine_tune_draw
        global global_transform_matrix

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
        global global_transform_matrix

        if global_transform_matrix is None:
            if global_rect is not None:
                dst = np.array([[0, 0],
                                [self.width, 0],
                                [self.width, self.height],
                                [0, self.height]], dtype='float32')
                global_transform_matrix = cv2.getPerspectiveTransform(global_rect, dst)

        self.frame = cv2.warpPerspective(self.frame, global_transform_matrix, (self.width, self.height))

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

    def find_offsets(self, max_offset=10.0):
        global global_transform_matrix

        gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, 15, 51, 51)
        edged = cv2.Canny(gray, 20, 100)
        _, contours, _ = cv2.findContours(edged.copy(), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_TC89_L1)

        coords = []
        for i in range(len(contours)):
            moments = cv2.moments(contours[i])
            if moments['m00'] != 0 and moments['m00'] != 0:
                x_cen, y_cen = moments['m10']/moments['m00'], moments['m01']/moments['m00']
                nearest_circle = self.closest_node((x_cen, y_cen), self.circle_positions)
                x_offset = np.abs(self.circle_positions[nearest_circle][0] - x_cen)
                y_offset = np.abs(self.circle_positions[nearest_circle][1] - y_cen)
                if x_offset <= max_offset and y_offset <= max_offset:
                    coords.append((x_cen, y_cen))

        rect = self.order_points(np.array(coords))
        transform_matrix = cv2.getPerspectiveTransform(rect, np.array(self.circle_positions, dtype='float32'))
        global_transform_matrix = np.dot(transform_matrix, global_transform_matrix)

    def closest_node(self, node, nodes):
        nodes = np.asarray(nodes)
        deltas = nodes - node
        dist_2 = np.einsum('ij,ij->i', deltas, deltas)

        return np.argmin(dist_2)


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
