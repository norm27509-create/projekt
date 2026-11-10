"""Windows display gamma control via GDI. Never touches the game process."""

import ctypes
import sys

from .ramp import RAMP_SIZE

IS_WINDOWS = sys.platform == "win32"
RampArray = (ctypes.c_ushort * RAMP_SIZE) * 3


class Display:
    def __init__(self):
        self.original = None
        if IS_WINDOWS:
            self.original = self._get()

    def _get(self):
        ramp = RampArray()
        user32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32
        hdc = user32.GetDC(None)
        try:
            ok = gdi32.GetDeviceGammaRamp(hdc, ctypes.byref(ramp))
        finally:
            user32.ReleaseDC(None, hdc)
        return ramp if ok else None

    def _set(self, ramp) -> bool:
        user32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32
        hdc = user32.GetDC(None)
        try:
            return bool(gdi32.SetDeviceGammaRamp(hdc, ctypes.byref(ramp)))
        finally:
            user32.ReleaseDC(None, hdc)

    def apply(self, ramp_lists) -> bool:
        if not IS_WINDOWS:
            return False
        ramp = RampArray()
        for c in range(3):
            for i in range(RAMP_SIZE):
                ramp[c][i] = ramp_lists[c][i]
        return self._set(ramp)

    def restore(self) -> bool:
        if not IS_WINDOWS or self.original is None:
            return False
        return self._set(self.original)
