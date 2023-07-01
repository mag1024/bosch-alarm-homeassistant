Home Assistant integration using the bosch-alarm-mode2 library.

This integration provides
- An [AlarmControlPanel](https://developers.home-assistant.io/docs/core/entity/alarm-control-panel/)
entity for each configured area, with the ability to issue arm/disarm commands
(note, that since the mode2 automation user has "superuser" priviledges, this bypasses the regularly
configured alarm pin). The entity reports state (*disarmed*, *armed_away*, etc), and
contains custom attributes *ready_to_arm* (*no*|*home*|*away*), and a *faulted_points* counter.

- A [BinarySensor](https://developers.home-assistant.io/docs/core/entity/binary-sensor) entity for each configured alarm point.

- A [Sensor](https://developers.home-assistant.io/docs/core/entity/sensor/) entity for the panel's history. The history itself is stored on a `history` attribute, as there is a limit to how much text a sensor can store in its state.