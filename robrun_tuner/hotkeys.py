"""Global hotkeys (Windows RegisterHotKey) delivered through a queue for Tk."""

import ctypes
import ctypes.wintypes
import queue
import threading

WM_HOTKEY = 0x0312
VK_F9, VK_F10 = 0x78, 0x79
HOTKEYS = {1: ("toggle", VK_F9), 2: ("reset", VK_F10)}


def start(events: "queue.Queue[str]") -> threading.Thread:
    def loop():
        user32 = ctypes.windll.user32
        for hk_id, (_, vk) in HOTKEYS.items():
            if not user32.RegisterHotKey(None, hk_id, 0, vk):
                events.put(f"error:F{vk - 0x6F} is already in use by another program")
        msg = ctypes.wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            if msg.message == WM_HOTKEY and msg.wParam in HOTKEYS:
                events.put(HOTKEYS[msg.wParam][0])

    t = threading.Thread(target=loop, daemon=True)
    t.start()
    return t
