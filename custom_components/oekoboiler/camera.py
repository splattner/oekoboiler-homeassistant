from __future__ import annotations

import logging
import io
from typing import Callable, Union
import collections

from PIL import Image, ImageDraw, UnidentifiedImageError

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import HomeAssistantError


from homeassistant.components.image_processing import (
    CONF_CONFIDENCE,
    PLATFORM_SCHEMA,
    ImageProcessingEntity,
)

from homeassistant.helpers.typing import ConfigType, HomeAssistantType

from .const import (
    DOMAIN,
    DATA_OEKOBOILER_CLIENT,
)

from. import OekoboilerEntity


_LOGGER = logging.getLogger(__name__)

DEFAULT_CONTENT_TYPE: Final = "image/jpeg"


async def async_setup_entry(
    hass: HomeAssistantType, 
    entry: ConfigEntry, 
    async_add_entities: Callable
) -> None:

    pass

    devices: dict = []

    oekoboiler = hass.data[DOMAIN][entry.entry_id][DATA_OEKOBOILER_CLIENT]

    # Mode Sensor
    devices.append(OekoboilerCameraEntity(
                hass=hass,
                oekoboiler=oekoboiler,
                entry=entry,
            )
    )


    async_add_entities(device for device in devices)



class OekoboilerCameraEntity(OekoboilerEntity, Camera):
    def __init__(
        self,
        hass: HomeAssistantType,
        oekoboiler,
        entry,
        *args,
        **kwargs,
    ):
        self._hass: HomeAssistantType = hass

        self.stream: Stream | None = None
        self.stream_options: dict[str, str] = {}
        self.content_type: str = DEFAULT_CONTENT_TYPE
        self.access_tokens: collections.deque = collections.deque([], 2)
        self._create_stream_lock: asyncio.Lock | None = None
        self._rtsp_to_webrtc = False


        super().__init__(oekoboiler=oekoboiler, entry=entry, *args, **kwargs)


    @property
    def name(self) -> str:
        return f"Oekoboiler Display processed image"

    @property
    def unique_id(self) -> str:
        return f"oekoboiler_processed_image"

    @property
    def available(self) -> bool:
        return True

    @property
    def device_info(self) -> dict:
        """Return information about the device."""
        return {
            "identifiers": {(DOMAIN, "oekoboiler")},
            "name": "Oekoboiler",
            "model": "OekoBoiler",
            "manufacturer": "Oekoswiss Supply AG",
        }

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return bytes of camera image."""


        camera = self.hass.components.camera
        cameraImage = None

        try:
            cameraImage = await camera.async_get_image(
                self._camera_entity, timeout=self._timeout
            )


        except HomeAssistantError as err:
            _LOGGER.error("Error on receive image from entity: %s", err)
            return


        oekoboilerDisplayImage = Image.open(io.BytesIO(bytearray(cameraImage.content))).convert("RGB")
        w, h = oekoboilerDisplayImage.size

        _LOGGER.debug("Image captured from camera for processing in Oekoboiler Component. Image Size: w={}, h={}".format(w,h))

        processedImage = self._oekoboiler.imageByteArray