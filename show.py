import os.path

from qtpy.QtWidgets import QApplication
from typhon import TyphonSuite, use_stylesheet
from ophyd.status import wait as status_wait

from laptop import lp

# Initialize signals
status_wait(lp.trigger())

# Create application
app = QApplication([])
use_stylesheet()
# Create TyphonSuite
ts = TyphonSuite.from_device(lp)
# Set our stylesheet
embedded = os.path.abspath('embedded_screen.ui')
detailed = os.path.abspath('detailed_screen.ui')

ts.setStyleSheet("""\
TyphonDeviceDisplay[device_class='laptop.Laptop'][display_type='0']
    {{qproperty-force_template: '{}';}}

TyphonDeviceDisplay[device_class='laptop.Laptop'][display_type='1']
    {{qproperty-force_template: '{}';}}
""".format(embedded, detailed))

# Start the show
ts.show()
app.exec_()
