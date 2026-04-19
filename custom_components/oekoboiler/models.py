from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


def default_indicator_map() -> dict[str, bool]:
    return {
        "off": False,
        "htg": False,
        "def": False,
        "warm": False,
        "highTemp": False,
    }


@dataclass
class FrameQuality:
    status: str = "unknown"
    confidence: Optional[float] = None
    frame: Optional[int] = None

    def as_dict(self) -> dict[str, str | float | int | None]:
        return {
            "status": self.status,
            "confidence": self.confidence,
            "frame": self.frame,
        }


def default_quality_map() -> dict[str, FrameQuality]:
    return {
        "time": FrameQuality(),
        "set_temperature": FrameQuality(),
        "water_temperature": FrameQuality(),
        "mode": FrameQuality(),
        "state": FrameQuality(),
        "level": FrameQuality(),
    }


@dataclass
class AlignmentResult:
    raw_shift_x: int = 0
    raw_shift_y: int = 0
    shift_x: int = 0
    shift_y: int = 0
    error: Optional[float] = None
    frame: Optional[int] = None

    def as_dict(self) -> dict[str, float | int | None]:
        return {
            "raw_shift_x": self.raw_shift_x,
            "raw_shift_y": self.raw_shift_y,
            "shift_x": self.shift_x,
            "shift_y": self.shift_y,
            "error": self.error,
            "frame": self.frame,
        }


@dataclass
class ParsedFrame:
    time: Optional[str] = ""
    set_temperature: Optional[int] = 0
    water_temperature: Optional[int] = 0
    mode: Optional[str] = ""
    state: Optional[str] = ""
    level: float = 0.0
    indicator: dict[str, bool] = field(default_factory=default_indicator_map)
    quality: dict[str, FrameQuality] = field(default_factory=default_quality_map)
    alignment: AlignmentResult = field(default_factory=AlignmentResult)

    def clone(self) -> ParsedFrame:
        return ParsedFrame(
            time=self.time,
            set_temperature=self.set_temperature,
            water_temperature=self.water_temperature,
            mode=self.mode,
            state=self.state,
            level=self.level,
            indicator=dict(self.indicator),
            quality={
                key: FrameQuality(value.status, value.confidence, value.frame)
                for key, value in self.quality.items()
            },
            alignment=AlignmentResult(
                raw_shift_x=self.alignment.raw_shift_x,
                raw_shift_y=self.alignment.raw_shift_y,
                shift_x=self.alignment.shift_x,
                shift_y=self.alignment.shift_y,
                error=self.alignment.error,
                frame=self.alignment.frame,
            ),
        )

    def set_quality(self, key: str, status: str, frame: int, confidence: Optional[float] = None) -> None:
        self.quality[key] = FrameQuality(
            status=status,
            confidence=round(confidence, 3) if confidence is not None else None,
            frame=frame,
        )

    def set_failed_quality(self, key: str, frame: int, confidence: Optional[float] = None) -> None:
        previous_status = self.quality.get(key, FrameQuality()).status
        status = "stale" if previous_status == "ok" else "unknown"
        self.set_quality(key, status, frame, confidence)

    def get_quality_dict(self, key: str) -> dict[str, str | float | int | None]:
        return self.quality.get(key, FrameQuality()).as_dict()

    def get_alignment_dict(self) -> dict[str, float | int | None]:
        return self.alignment.as_dict()