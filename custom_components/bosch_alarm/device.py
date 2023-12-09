from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN

def device_info_from_panel(panel):
    return DeviceInfo(
        identifiers={(DOMAIN, panel.serial_number)},
        name=f"Bosch {panel.model}",
        manufacturer="Bosch Security Systems",
        model=panel.model,
        sw_version=panel.firmware_version,
    )

class BoschPanel:
    def __init__(self, panel):
        self.panel = panel
        self._initialised = False
        self._entity_setups = []
        panel.connection_status_observer.attach(self.setup)

    def register_entity_setup(self, initializer):
        self._entity_setups.append(initializer)

    def setup(self):
        if not self.panel.connection_status() or self._initialised:
            return
        self._initialised = True
        for initializer in self._entity_setups:
            initializer()

    async def disconnect(self):
        self.panel.connection_status_observer.detach(self.setup)
        await self.panel.disconnect()
