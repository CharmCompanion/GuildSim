"""SD setup helper for Pico W and desktop fallback."""


def mount_sd():
    """Mount SD card on Pico W, or provide local ./sd fallback on desktop."""
    try:
        import machine  # type: ignore
        import sdcard  # type: ignore
        import os

        spi = machine.SPI(
            0,
            sck=machine.Pin(18),
            mosi=machine.Pin(19),
            miso=machine.Pin(16),
        )

        # Some LCD hats consume GP17 for display CS, so try a fallback CS pin.
        for cs_pin in (17, 22):
            try:
                sd = sdcard.SDCard(spi, machine.Pin(cs_pin))
                os.mount(sd, "/sd")
                print("SD Card Mounted at /sd (CS=GP{})".format(cs_pin))
                return "/sd"
            except Exception:
                pass

        raise RuntimeError("SD mount failed on CS pins GP17 and GP22")
    except Exception as exc:
        # Desktop/Thonny fallback path.
        try:
            import os

            path = "sd"
            if path not in os.listdir("."):
                os.mkdir(path)
            print("SD fallback active at ./sd ({})".format(exc))
            return path
        except Exception:
            print("SD setup failed. Continuing without mounted storage.")
            return None
