from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN

class PanelConnection:
    def __init__(self, panel, unique_id, model):
        self.unique_id = unique_id
        self.model = model
        self.panel = panel
        self.on_connect = []
        panel.connection_status_observer.attach(self.on_connection_status_change)

    def on_connection_status_change(self):
        if not self.panel.connection_status():
            return
        for on_connect_handler in self.on_connect:
            on_connect_handler()
        self.on_connect.clear()

    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            name=f"Bosch {self.model}",
            manufacturer="Bosch Security Systems",
            model=self.model,
            sw_version=self.panel.firmware_version,
        )

    async def disconnect(self):
        self.panel.connection_status_observer.detach(self.on_connection_status_change)
        await self.panel.disconnect()
