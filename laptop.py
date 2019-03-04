import time
import threading

import cv2
import face_recognition
from ophyd import Device, Component as Cpt, Signal
from ophyd.sim import FakeEpicsSignalRO
from ophyd.status import DeviceStatus

import happi

obama_image = face_recognition.load_image_file("obama.jpg")
obama_face_encoding = face_recognition.face_encodings(obama_image)[0]


class Laptop(Device):
    """Laptop Web Camera Ophyd Device"""
    # Raw Image
    image = Cpt(FakeEpicsSignalRO, 'image', kind='omitted')
    # ROI
    y = Cpt(Signal, kind='config', value=0)
    h = Cpt(Signal, kind='config', value=0)
    # Interpreted Data
    faces = Cpt(FakeEpicsSignalRO, 'faces', kind='hinted')
    presidents = Cpt(FakeEpicsSignalRO, 'presidents', kind='normal')

    def take_image(self, status):
        """Trigger Laptop camera to take a new image and process"""
        try:
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
            # Reframe image
            y = int(self.y.get() or 0)
            h = int(self.h.get() or frame.shape[0] - y)
            # Store information image in signal
            if y < 0 or h < 0 or y + h > frame.shape[0]:
                raise ValueError(f"Invalid ROI ({y}, {y+h}) for image of height "
                                 f"{frame.shape[0]}")

            frame = frame[round(y):round(y+h), :, :]
            self.image.sim_put(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
            self.image._run_subs(sub_type=self.image.SUB_VALUE, value=self.image.value)
            # Color convert
            small_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
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
        except:
            self.log.exception("Unable to capture image!")
            status._finished(success=False)
        else:
            status._finished(success=True)

    def trigger(self):
        status = DeviceStatus(self)
        self._thread = threading.Thread(target=self.take_image,
                                        args=[status])
        self._thread.start()
        return status


laptop_md = happi.Device(prefix='Empty', name='teddy_laptop',
                         beamline='TST', args=[],
                         device_class='laptop.Laptop')

lp = happi.from_container(laptop_md)
