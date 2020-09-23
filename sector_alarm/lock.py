"""
"""
import logging

from homeassistant.components.lock import LockEntity
from homeassistant.const import (ATTR_CODE, STATE_LOCKED, STATE_UNKNOWN,
                                 STATE_UNLOCKED)

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

    locks = await sector_hub.get_locks()

    if locks is not None:
        async_add_entities(
            SectorAlarmLock(sector_hub, code, code_format, lock)
            for lock in locks)


class SectorAlarmLock(LockEntity):
    """Representation of a Sector Alarm lock."""

    def __init__(self, hub, code, code_format, serial):
        self._hub = hub
        self._serial = serial
        self._code = code
        self._code_format = code_format

    @property
    def name(self):
        """Return the serial of the lock."""
        return self._serial

    @property
    def state(self):
        """Return the state of the lock."""
        state = self._hub.lock_states[self._serial]

        if state == 'lock':
            return STATE_LOCKED
        elif state == 'unlock':
            return STATE_UNLOCKED

        return STATE_UNKNOWN

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