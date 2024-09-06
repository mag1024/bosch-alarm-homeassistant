### Home Assistant integration for Bosch Alarm Panels, using the _Mode 2_ API.

![Screenshot 2023-11-18 at 01 10 27](https://github.com/mag1024/bosch-alarm-homeassistant/assets/787978/022c331d-6a11-4796-b773-fc19c5bee32b)

Supported panels:
 * _Solution 2000/3000/4000_
 * _B4512/B5512_
 * _B8512G/B9512G_
 * _AMAX 2100/3000/4000_
 * _D7412GV4/D9412GV4_.

Based on the [bosch-alarm-mode2](https://github.com/mag1024/bosch-alarm-mode2) library, which uses subscriptions/push updates for panels that support it.

### Provided entities
- [AlarmControlPanel](https://developers.home-assistant.io/docs/core/entity/alarm-control-panel/) for each configured area, with the ability to issue arm/disarm commands.
  Warning: since the _Mode 2_ automation user has "superuser" priviledges, this bypasses the regularly-configured alarm pin.
  These entities report state (*disarmed*, *armed_away*, etc), and contain custom attributes *ready_to_arm* (*no*|*home*|*away*), and a *faulted_points* counter.
- [BinarySensor](https://developers.home-assistant.io/docs/core/entity/binary-sensor) for each configured alarm point.
- [Sensor](https://developers.home-assistant.io/docs/core/entity/sensor/) entities for the panel's current faults, and the panel's history.
  The history itself is stored on a `history` attribute, as there is a limit to how much text a sensor can store in its state.
- [Switch](https://developers.home-assistant.io/docs/core/entity/switch) for each configured output. Note that for some panels, only outputs with the type set to "remote output" can be controlled via _Mode 2_ API.
- [Lock](https://developers.home-assistant.io/docs/core/entity/lock) for each configured "door" (_Solution 4000, B4512, B5512, B8512G, B9512G_ only).
- A custom Service, called `set_date_time`, that can be used to set the time and date on the panel.

### Installation

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=mag1024&repository=bosch-alarm-homeassistant&category=integration)
