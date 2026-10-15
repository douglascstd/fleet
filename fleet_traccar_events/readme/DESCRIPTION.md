This module is an add-on for the Fleet application in Odoo. It extends
`fleet_traccar_integration` to synchronize the Traccar geofences and events
into Odoo:

- **Geofences** (`traccar.geofence`): the geofences defined in Traccar,
  with their name, description, area, calendar and attributes. They can be
  synchronized on demand or from a server action.
- **Events** (`traccar.event`): the events reported by Traccar (alarm,
  geofence enter/exit, device status, etc.), with their type, date, device
  and vehicle, related geofence and telemetry point, message and raw data.
- Events are deduplicated by Traccar ID and relinked to the corresponding
  device/geofence/telemetry records when they are available later.
