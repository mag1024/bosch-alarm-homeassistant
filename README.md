### Home Assistant integration using the [bosch-alarm-mode2](https://github.com/mag1024/bosch-alarm-mode2) library.

![Screenshot 2023-11-18 at 01 10 27](https://github.com/mag1024/bosch-alarm-homeassistant/assets/787978/022c331d-6a11-4796-b773-fc19c5bee32b)

### This integration provides
- An [AlarmControlPanel](https://developers.home-assistant.io/docs/core/entity/alarm-control-panel/)
entity for each configured area, with the ability to issue arm/disarm commands
(note, that since the mode2 automation user has "superuser" priviledges, this bypasses the regularly
configured alarm pin). The entity reports state (*disarmed*, *armed_away*, etc), and
contains custom attributes *ready_to_arm* (*no*|*home*|*away*), and a *faulted_points* counter.

- A [BinarySensor](https://developers.home-assistant.io/docs/core/entity/binary-sensor) entity for each configured alarm point.

- A [Sensor](https://developers.home-assistant.io/docs/core/entity/sensor/) entity for the panel's history. The history itself is stored on a `history` attribute, as there is a limit to how much text a sensor can store in its state.

- A [Switch](https://developers.home-assistant.io/docs/core/entity/switch) entity for the each configured output. Note that for the solution 2000/3000, only outputs with the type set to "remote output" will show here, as these are the only ones that can be controlled via mode 2.

### Installation

1. [Install](https://hacs.xyz/docs/setup/download/) the Home Assistant Community Store (HACS): 
2. Use [Custom Repositories](https://hacs.xyz/docs/faq/custom_repositories/) to add the URL of this github repository (select category `Integration`)
3. Search for _Bosch Alarm_ in HACS, install it, and restart Home Assistant
4. Search for _Bosch Alarm_ in Home Assistant -> Settings -> Integrations -> Add Integration, and install it
