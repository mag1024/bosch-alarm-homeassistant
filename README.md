## Upstreamed!

As of Home Assistant _2025.6_, this integration is part of Home Assistant.
This repository will no longer be updated. All users are encouraged to update to the build-in version.

### Home Assistant integration for Bosch Alarm Panels, using the _Mode 2_ API.

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)
[![Stable](https://img.shields.io/github/v/release/mag1024/bosch-alarm-homeassistant)](https://github.com/mag1024/bosch-alarm-homeassistant/releases/latest)

![Screenshot 2023-11-18 at 01 10 27](https://github.com/mag1024/bosch-alarm-homeassistant/assets/787978/022c331d-6a11-4796-b773-fc19c5bee32b)

Supported panels:
 * _Solution 2000/3000/4000_
 * B Series: _B3512/B4512/B5512/B6512_
 * G Series: _B8512G/B9512G_
 * _AMAX 2100/3000/4000_
 * _D7412GV4/D9412GV4_ [^1]

[^1]: Firmware 2.0+

Based on the [bosch-alarm-mode2](https://github.com/mag1024/bosch-alarm-mode2) library, which uses subscriptions/push updates for panels that support it.

### Provided entities
- [AlarmControlPanel](https://developers.home-assistant.io/docs/core/entity/alarm-control-panel/) for each configured area, with the ability to issue arm/disarm commands.
  This entity reports state (*disarmed*, *armed_away*, etc), and contains custom attributes *ready_to_arm* (*no*|*home*|*away*), and a *faulted_points* counter.
- [BinarySensor](https://developers.home-assistant.io/docs/core/entity/binary-sensor) for each configured alarm point.
- [Sensor](https://developers.home-assistant.io/docs/core/entity/sensor/) entities for the panel's current faults, and the panel's history.
  The history itself is stored on a `history` attribute, as there is a limit to how much text a sensor can store in its state.
- [Switch](https://developers.home-assistant.io/docs/core/entity/switch) for each configured output. Note that for some panels, only outputs with the type set to "remote output" can be controlled via _Mode 2_ API.
- [Lock](https://developers.home-assistant.io/docs/core/entity/lock) for each configured "door" (_Solution 4000_, _B Series_ and _G Series_ panels only).
- A custom Service, called `set_date_time`, that can be used to set the time and date on the panel.

### Authentication
The primary means of authentication for the _Mode 2_ API is the _Automation_ passcode. It needs to be at least 10 characters long, and it is different from the _User_ code -- a shorter numeric pin used to arm/disarm the panel.
The integration will prompt for the required passcodes, which depend on the panel type.

| Panel | Code |
| --- | --- |
| Solution | User [^2] |
| B Series | Automation |
| G Series | Automation |
| AMAX | Both |

[^2]: The user needs to have the "master code functions" authority if you wish to interact with history events.

⚠️ Since the _Mode 2_ automation user has "superuser" priviledges, it bypasses the regularly-configured alarm pin: you will _not_ be prompted for a _User_ code when arming/disaming through the integration.
The integration also supports (optionally) setting a Home Assistant-local pin to protect these operations -- it does not need to match any of the codes configured on the panel. 

### Installation

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=mag1024&repository=bosch-alarm-homeassistant&category=integration)
