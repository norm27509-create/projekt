import unittest

from robrun_tuner.ramp import MAX_VALUE, PRESETS, Profile, build_channel, build_ramp


class RampTests(unittest.TestCase):
    def test_default_is_identity(self):
        ch = build_channel(Profile())
        self.assertEqual(ch[0], 0)
        self.assertEqual(ch[-1], MAX_VALUE)
        self.assertEqual(ch[128], round(128 / 255 * MAX_VALUE))

    def test_presets_are_monotonic_and_in_range(self):
        for name, p in PRESETS.items():
            ch = build_channel(p)
            self.assertEqual(len(ch), 256, name)
            self.assertTrue(all(0 <= v <= MAX_VALUE for v in ch), name)
            self.assertTrue(all(a <= b for a, b in zip(ch, ch[1:])), name)

    def test_higher_gamma_lifts_shadows(self):
        self.assertGreater(build_channel(Profile(gamma=1.6))[40], build_channel(Profile())[40])

    def test_extremes_clamp(self):
        ch = build_channel(Profile(gamma=2.5, brightness=0.3, contrast=1.5))
        self.assertTrue(all(0 <= v <= MAX_VALUE for v in ch))
        self.assertEqual(len(build_ramp(Profile())), 3)

    def test_profile_roundtrip(self):
        p = Profile(1.2, 0.05, 0.9)
        self.assertEqual(Profile.from_dict(p.to_dict()), p)


if __name__ == "__main__":
    unittest.main()
