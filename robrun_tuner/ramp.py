"""Pure gamma-ramp math (platform independent, unit tested)."""

from dataclasses import dataclass, asdict

RAMP_SIZE = 256
MAX_VALUE = 65535


@dataclass
class Profile:
    gamma: float = 1.0       # >1 lifts shadows
    brightness: float = 0.0  # additive offset, -0.3..0.3
    contrast: float = 1.0    # 0.5..1.5

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**{k: float(data[k]) for k in ("gamma", "brightness", "contrast") if k in data})


PRESETS = {
    "Default": Profile(),
    "Dark areas / night": Profile(gamma=1.6, brightness=0.04, contrast=1.05),
    "Indoors / alleys": Profile(gamma=1.35, brightness=0.02, contrast=1.0),
    "Bright day (less glare)": Profile(gamma=0.9, brightness=-0.03, contrast=1.1),
}


def build_channel(profile: Profile) -> list[int]:
    """Return a monotonic 256-entry ramp of 16-bit values."""
    values = []
    prev = 0
    for i in range(RAMP_SIZE):
        x = i / (RAMP_SIZE - 1)
        y = x ** (1.0 / profile.gamma)
        y = (y - 0.5) * profile.contrast + 0.5 + profile.brightness
        y = min(1.0, max(0.0, y))
        v = max(prev, int(round(y * MAX_VALUE)))  # Windows rejects non-monotonic ramps
        values.append(v)
        prev = v
    return values


def build_ramp(profile: Profile) -> list[list[int]]:
    channel = build_channel(profile)
    return [channel, list(channel), list(channel)]
