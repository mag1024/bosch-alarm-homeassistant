from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN

def device_info_from_panel(data):
    panel = data.panel
    return DeviceInfo(
        identifiers={(DOMAIN, data.unique_id)},
        name=f"Bosch {data.model}",
        manufacturer="Bosch Security Systems",
        model=panel.model,
        sw_version=panel.firmware_version,
    )

class BoschPanel:
    def __init__(self, panel, unique_id, model):
        self.unique_id = unique_id
        self.model = model
        self.panel = panel
        self._initialised = False
        self._entity_setups = []
        panel.connection_status_observer.attach(self.setup)

    def register_entity_setup(self, setup):
        self._entity_setups.append(setup)

    def setup(self):
        if not self.panel.connection_status() or self._initialised:
            return
        # We only want to setup entities once
        self._initialised = True
        for setup in self._entity_setups:
            setup()

    async def disconnect(self):
        self.panel.connection_status_observer.detach(self.setup)
        await self.panel.disconnect()
