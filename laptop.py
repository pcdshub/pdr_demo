import time

import cv2
import face_recognition
from ophyd import Device, Component as Cpt, Signal
from ophyd.sim import NullStatus, FakeEpicsSignalRO


obama_image = face_recognition.load_image_file("obama.jpg")
obama_face_encoding = face_recognition.face_encodings(obama_image)[0]


class Laptop(Device):
    """Laptop Web Camera Ophyd Device"""
    # Raw Image
    faces = Cpt(FakeEpicsSignalRO, 'faces', kind='hinted')
    presidents = Cpt(FakeEpicsSignalRO, 'presidents', kind='normal')
    # ROI
    y = Cpt(Signal, kind='config', value=0)
    h = Cpt(Signal, kind='config', value=0)
    image = Cpt(FakeEpicsSignalRO, 'image', kind='omitted')

    def trigger(self):
        self.log.info("Taking new image from %r", self.name)
        super().trigger()
        # Capture image
        self.log.debug("Opening camera ...")
        self._cam = cv2.VideoCapture(0)
        time.sleep(0.5)
        self.log.debug("Reading image ...")
        _, frame = self._cam.read()
        self.log.debug("Releasing camera ...")
        self._cam.release()
        # Store information image in signal
        self.image.sim_put(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
        # Color convert
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Resize image and convert to RGB
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        self.log.debug("Searching for faces ...")
        face_locations = face_recognition.face_locations(small_frame)
        # Find facial matches
        face_encodings = face_recognition.face_encodings(small_frame,
                                                         face_locations)
        presidents = 0
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces([obama_face_encoding],
                                                     face_encoding)
            if any(matches):
                presidents += 1
        # Store face matches
        self.faces.sim_put(len(face_locations))
        self.presidents.sim_put(presidents)
        self.log.info("Finished taking image, found %r faces %r "
                      "of whom are presidents",
                      self.faces.get(),
                      self.presidents.get())
        return NullStatus()


lp = Laptop(name='teddy_laptop')
