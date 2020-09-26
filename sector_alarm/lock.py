"""
"""
import datetime
import logging

from homeassistant.components.lock import LockEntity, ATTR_CHANGED_BY
from homeassistant.const import (ATTR_CODE, STATE_LOCKED, STATE_UNKNOWN,
                                 STATE_UNLOCKED, ATTR_FRIENDLY_NAME)

import custom_components.sector_alarm as sector_alarm

DEPENDENCIES = ['sector_alarm']

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass,
                               config,
                               async_add_entities,
                               discovery_info=None):

    sector_hub = hass.data[sector_alarm.DATA_SA]
    code = discovery_info[sector_alarm.CONF_CODE]
    code_format = discovery_info[sector_alarm.CONF_CODE_FORMAT]

    locks = await sector_hub._async_sector.get_status()
    locks = locks['Locks']

    if locks:
        async_add_entities(
            SectorAlarmLock(sector_hub, code, code_format, lock.get("Serial"), lock.get("Label"))
            for lock in locks)


class SectorAlarmLock(LockEntity):
    """Representation of a Sector Alarm lock."""

    def __init__(self, hub, code, code_format, serial, name=None):
        self._hub = hub
        self._serial = serial
        self._code = code
        self._code_format = code_format
        self._name = name

    @property
    def name(self):
        """Return the serial of the lock."""
        return self._name or self._serial

    @property
    def state(self):
        """Return the state of the lock."""
        state = self._hub.lock_states[self._serial]["state"]

        if state == 'lock':
            return STATE_LOCKED
        elif state == 'unlock':
            return STATE_UNLOCKED

        return STATE_UNKNOWN

    @property
    def changed_by(self):
        return self._hub.lock_states[self._serial].get("changed_by")

    @property
    def last_changed(self):
        timestamp_str = self._hub.lock_states[self._serial].get("last_changed")
        if timestamp_str:
            return datetime.datetime.fromtimestamp(int(timestamp_str.lstrip("/Date(").rstrip(")/"))/1_000)
        return None

    @property
    def available(self):
        """Return True if entity is available."""
        return True

    @property
    def code_format(self):
        """Return the required six digit code."""
        return self._code_format

    async def async_update(self):
        update = self._hub.update()
        if update:
            await update

    def _validate_code(self, code):
        """Validate given code."""
        check = self._code is None or code == self._code
        if not check:
            _LOGGER.warning("Invalid code given")
        return check

    @property
    def state_attributes(self):
        """Return the state attributes."""
        return {ATTR_CHANGED_BY: self.changed_by,
                "last_changed": self.last_changed,
                "lock_id": self._serial,
                }

    @property
    def is_locked(self):
        """Return true if lock is locked."""
        state = self._hub.lock_states[self._serial]
        return state == STATE_LOCKED

    async def async_unlock(self, **kwargs):
        """Send unlock command."""
        state = self._hub.lock_states[self._serial]
        if state == STATE_UNLOCKED:
            return

        await self._hub.unlock(self._serial, code=self._code)

    async def async_lock(self, **kwargs):
        """Send lock command."""
        state = self._hub.lock_states[self._serial]
        if state == STATE_LOCKED:
            return

        await self._hub.lock(self._serial, code=self._code)