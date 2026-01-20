#!/usr/bin/env python3

import asyncio
import logging
import signal
import sys
from typing import Optional

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

from config import ConfigManager
from api import StreamboxSettingsInterface

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StreamboxSettingsDaemon:
    def __init__(self):
        self.loop = None
        self.bus: Optional[dbus.SystemBus] = None
        self.config_manager: Optional[ConfigManager] = None
        self.api_interface: Optional[StreamboxSettingsInterface] = None
        self._running = False
        self.glib_loop = None

    def initialize(self):
        logger.info("Initializing Streambox Settings daemon")
        
        try:
            DBusGMainLoop(set_as_default=True)
            self.bus = dbus.SystemBus()
            logger.info("System bus acquired")
            
            self.config_manager = ConfigManager()
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            self.loop.run_until_complete(self.config_manager.initialize())
            logger.info("Config manager initialized")
            
            self.api_interface = StreamboxSettingsInterface(self.config_manager, self.bus)
            self.loop.run_until_complete(self.api_interface._async_init())
            logger.info("API interface initialized")
            
            self.bus_name = dbus.service.BusName(
                "org.cockpit.StreamboxSettings",
                bus=self.bus,
                allow_replacement=True
            )
            self.bus_name.fallback = True
            
            logger.info("D-Bus interface published successfully: org.cockpit.StreamboxSettings")
            
        except Exception as e:
            logger.error(f"Failed to initialize daemon: {e}", exc_info=True)
            raise

    def shutdown(self):
        logger.info("Shutting down Streambox Settings daemon")
        self._running = False
        
        if self.api_interface:
            self.api_interface.cleanup()
        
        if self.config_manager and self.loop:
            self.loop.run_until_complete(self.config_manager.cleanup())

    def setup_signal_handlers(self):
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}")
            self.shutdown()
            if self.glib_loop:
                self.glib_loop.quit()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGHUP, signal_handler)

    def run(self):
        try:
            self.initialize()
            self._running = True
            self.setup_signal_handlers()
            
            logger.info("Streambox Settings daemon started")
            
            self.glib_loop = GLib.MainLoop()
            self.glib_loop.run()
            
        except Exception as e:
            logger.error(f"Daemon error: {e}", exc_info=True)
            sys.exit(1)


def main():
    daemon = StreamboxSettingsDaemon()
    daemon.run()


if __name__ == "__main__":
    main()
