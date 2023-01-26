import os.path
import sys
from shutil import which
from unittest import TestCase, skipUnless

import pexpect

DATADIR = os.path.join(os.path.dirname(__file__), 'data')
KEYA_VDO = os.path.join(DATADIR, 'samplea.vdo')
KEYB_VDO = os.path.join(DATADIR, 'sampleb.vdo')


@skipUnless(which("vncev"), reason="requires https://github.com/LibVNC/libvncserver")
class TestSendEvents(TestCase):

    def setUp(self):
        cmd = 'vncev -rfbport 5933 -rfbwait 1000'
        self.server = pexpect.spawn(cmd, logfile=sys.stdout.buffer, timeout=2)

    def tearDown(self):
        self.server.terminate(force=True)

    def assertKeyDown(self, key):
        down = rf'^.*down:\s+\({key:#x}\)\r'
        self.server.expect(down)

    def assertKeyUp(self, key):
        up = rf'^.*up:\s+\({key:#x}\)\r'
        self.server.expect(up)

    def assertMouse(self, x, y, buttonmask):
        output = f'^.*Ptr: mouse button mask {buttonmask:#x} at {x},{y}'
        self.server.expect(output)

    def assertDisconnect(self):
        disco = 'Client 127.0.0.1 gone'
        self.server.expect(disco)

    def run_vncdo(self, commands):
        cmd = 'vncdo -v -s :33 ' + commands
        vnc = pexpect.spawn(cmd, logfile=sys.stdout.buffer, timeout=5)
        retval = vnc.wait()
        assert retval == 0, retval

    def test_key_alpha(self):
        self.run_vncdo('key z')
        self.assertKeyDown(ord('z'))
        self.assertKeyUp(ord('z'))
        self.assertDisconnect()

    def test_key_ctrl_a(self):
        self.run_vncdo('key ctrl-a')
        self.assertKeyDown(int(0xffe3))
        self.assertKeyDown(ord('a'))
        self.assertKeyUp(int(0xffe3))
        self.assertKeyUp(ord('a'))
        self.assertDisconnect()

    def test_type(self):
        string = 'abcdefghij'
        self.run_vncdo('type %s' % string)
        for key in string:
            self.assertKeyDown(ord(key))
            self.assertKeyUp(ord(key))
        self.assertDisconnect()

    def test_mouse_move(self):
        # vncev only prints click events, but will include the position
        self.run_vncdo('move 10 20 click 1')
        self.assertMouse(10, 20, 0x1)
        self.assertDisconnect()

    def test_mouse_click_button_two(self):
        self.run_vncdo('click 2')
        self.assertMouse(0, 0, 0x2)
        self.assertDisconnect()

    def test_read_files(self):
        self.run_vncdo(f'key x {KEYA_VDO} key y {KEYB_VDO}')
        for key in 'xayb':
            self.assertKeyDown(ord(key))
            self.assertKeyUp(ord(key))
