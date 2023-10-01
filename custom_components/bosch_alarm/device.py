from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN

def device_info_from_panel(panel):
    return DeviceInfo(
        identifiers={(DOMAIN, panel.serial_number or panel.model)},
        name=f"Bosch {panel.model}",
        manufacturer="Bosch Security Systems",
        model=panel.model,
        sw_version=panel.firmware_version,
    )
