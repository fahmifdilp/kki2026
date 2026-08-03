from dataclasses import dataclass

@dataclass
class GuideResult:
    status: str
    target: tuple[int, int] | None
    color: tuple[int, int, int]

class NavigationGuide:
    def __init__(self, smoothing: float = .35):
        self.smoothing = smoothing
        self._target = None

    def calculate(self, red, green) -> GuideResult:
        if red and green:
            raw = ((red["center_x"] + green["center_x"]) // 2, (red["center_y"] + green["center_y"]) // 2)
            status, color = "Koridor Terdeteksi", (70, 220, 100)
        elif red or green:
            item = red or green
            raw = (item["center_x"], item["center_y"])
            status, color = "Panduan Terbatas", (0, 210, 255)
        else:
            self._target = None
            return GuideResult("Target Tidak Terdeteksi", None, (50, 50, 230))
        if self._target:
            a = self.smoothing
            raw = (int(a * raw[0] + (1-a) * self._target[0]), int(a * raw[1] + (1-a) * self._target[1]))
        self._target = raw
        return GuideResult(status, raw, color)
