"""
RFID Reader Field Discovery
============================
Connects to an Impinj reader via LLRP (sllurp 3.x) and dumps EVERY field
from raw tag reports. No field assumptions. No filtering.

Purpose: discover exactly what data your reader provides so we stop
guessing and start building from facts.

Usage:
    python discover_reader_fields.py [--config path/to/config.yaml]
"""

import sys
import time
from pathlib import Path
from datetime import datetime, UTC
from collections import Counter

import yaml
from pydantic import BaseModel, ConfigDict, field_validator

from sllurp.llrp import LLRPReaderClient, LLRPReaderConfig


# ---------------------------------------------------------------------------
# Configuration (Single Responsibility: only config validation lives here)
# ---------------------------------------------------------------------------

class ReaderSettings(BaseModel):
    """Validates reader connection parameters from YAML."""

    model_config = ConfigDict(strict=True)

    host: str
    port: int = 5084
    duration: float = 10.0
    antennas: list[int] = [1, 2, 3, 4]
    tx_power: int = 0

    @field_validator("antennas")
    @classmethod
    def antennas_not_empty(cls, v: list[int]) -> list[int]:
        if not v:
            raise ValueError("At least one antenna required")
        return v


class DiscoveryConfig(BaseModel):
    """Top-level config wrapping reader settings + discovery params."""

    model_config = ConfigDict(strict=True)

    reader: ReaderSettings
    max_reports: int = 50


# ---------------------------------------------------------------------------
# Tag Report Collector (Single Responsibility: collect and display raw data)
# ---------------------------------------------------------------------------

class TagReportCollector:
    """
    Receives tag reports and prints ALL key-value pairs found.

    Open/Closed Principle: this class handles display. To change output
    format (e.g., JSON file, database), create a new collector class
    implementing the same callback interface — don't modify this one.
    """

    def __init__(self, max_reports: int = 0) -> None:
        # Interface Segregation: only exposes what callers need
        self._report_count: int = 0
        self._max_reports = max_reports
        # Track which fields we've seen across ALL reports
        self._field_registry: Counter[str] = Counter()
        self._done = False

    @property
    def is_done(self) -> bool:
        """Check if we've collected enough reports."""
        return self._done

    @property
    def report_count(self) -> int:
        return self._report_count

    def on_tag_report(self, reader: LLRPReaderClient, tags: list) -> None:
        """
        Callback invoked by sllurp for each tag report batch.

        Iterates ALL fields in the tag dict — never accesses a field
        by name. Whatever the reader sends, we print.
        """
        if self._done:
            return

        for tag in tags:
            self._report_count += 1

            print(f"\n{'=' * 65}")
            print(
                f"  Tag Report #{self._report_count}"
                f"  @  {datetime.now(UTC).strftime('%H:%M:%S.%f')[:-3]} UTC"
            )
            print(f"{'=' * 65}")

            # Core discovery: iterate ALL keys, assume nothing
            for key in sorted(tag.keys()):
                value = tag[key]
                self._field_registry[key] += 1
                # Format bytes as hex for readability (EPCs come as bytes)
                if isinstance(value, (bytes, bytearray)):
                    display = value.hex().upper()
                else:
                    display = repr(value)
                print(f"  {key:45s} : {display}")

            # Check if we've hit the limit
            if self._max_reports > 0 and self._report_count >= self._max_reports:
                self._done = True
                return

    def print_summary(self) -> None:
        """Print a summary of all unique fields discovered across all reports."""
        print(f"\n\n{'#' * 65}")
        print(f"  DISCOVERY SUMMARY")
        print(f"{'#' * 65}")
        print(f"  Total tag reports received : {self._report_count}")
        print(f"  Unique fields discovered   : {len(self._field_registry)}")
        print()

        if self._field_registry:
            print(f"  {'Field Name':45s}   Occurrences")
            print(f"  {'-' * 45}   {'-' * 11}")
            for field, count in sorted(self._field_registry.items()):
                print(f"  {field:45s}   {count}")
        else:
            print("  *** NO FIELDS RECEIVED ***")
            print("  Check: reader IP, antenna connections, tags in range")

        print(f"\n{'#' * 65}\n")


# ---------------------------------------------------------------------------
# Reader Connector (Dependency Inversion: depends on config + callback
# abstractions, not on hardcoded reader details)
# ---------------------------------------------------------------------------

class ReaderConnector:
    """
    Handles LLRP connection lifecycle.

    Dependency Injection: receives config and report handler externally.
    Liskov Substitution: any collector with an on_tag_report method works.
    """

    def __init__(
        self,
        settings: ReaderSettings,
        collector: TagReportCollector,
    ) -> None:
        self._settings = settings
        self._collector = collector
        self._client: LLRPReaderClient | None = None

    def _build_llrp_config(self) -> LLRPReaderConfig:
        """
        Build sllurp config with ALL selectors enabled.

        Strategy: enable every possible field. If the reader supports it,
        we see it. If not, it simply won't appear in the report.
        No harm in asking for everything.
        """
        config_dict = {
            "duration": self._settings.duration,
            "antennas": self._settings.antennas,
            "tx_power": self._settings.tx_power,
            "start_inventory": True,
            "report_every_n_tags": 1,
            "disconnect_when_done": True,

            # Enable ALL standard LLRP tag content selectors
            "tag_content_selector": {
                "EnableROSpecID": True,
                "EnableSpecIndex": True,
                "EnableInventoryParameterSpecID": True,
                "EnableAntennaID": True,
                "EnableChannelIndex": True,
                "EnablePeakRSSI": True,
                "EnableFirstSeenTimestamp": True,
                "EnableLastSeenTimestamp": True,
                "EnableTagSeenCount": True,
                "EnableAccessSpecID": True,
            },

            # Enable Impinj extensions — if the reader supports them,
            # we get phase/Doppler/RSSI. If not, they just won't appear.
            "impinj_extended_configuration": True,
            "impinj_tag_content_selector": {
                "EnableRFPhaseAngle": True,
                "EnablePeakRSSI": True,
                "EnableRFDopplerFrequency": True,
            },
        }
        return LLRPReaderConfig(config_dict)

    def run(self) -> None:
        """Connect to reader, collect reports, disconnect."""
        llrp_config = self._build_llrp_config()

        self._client = LLRPReaderClient(
            self._settings.host,
            self._settings.port,
            config=llrp_config,
        )

        # Register the collector's callback
        self._client.add_tag_report_callback(self._collector.on_tag_report)

        print(f"Connecting to {self._settings.host}:{self._settings.port} ...")
        print(f"Duration   : {self._settings.duration}s")
        print(f"Antennas   : {self._settings.antennas}")
        print(f"TX Power   : {self._settings.tx_power} (0=max)")
        print(f"Impinj ext : enabled (reader will ignore if unsupported)")
        print(f"\nWaiting for tag reports — place tags near antennas ...\n")

        try:
            # connect() starts a background thread for the reader loop
            self._client.connect()
        except Exception as exc:
            print(f"\nConnection FAILED: {exc}", file=sys.stderr)
            print(
                "Verify: reader IP, reader powered on, network reachable, "
                "no other client connected.",
                file=sys.stderr,
            )
            sys.exit(1)

        # Wait for duration or until max_reports reached
        deadline = time.monotonic() + self._settings.duration
        try:
            while time.monotonic() < deadline and not self._collector.is_done:
                time.sleep(0.2)
        except KeyboardInterrupt:
            print("\nInterrupted by user.")
        finally:
            self._disconnect()

    def _disconnect(self) -> None:
        """Safely disconnect from reader."""
        if self._client:
            try:
                self._client.disconnect()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Config Loader
# ---------------------------------------------------------------------------

def load_config(path: Path) -> DiscoveryConfig:
    """Load and validate YAML configuration."""
    if not path.exists():
        print(f"Config file not found: {path}", file=sys.stderr)
        print(
            "Copy discover_config.yaml and set your reader's IP.",
            file=sys.stderr,
        )
        sys.exit(1)

    with path.open() as f:
        raw = yaml.safe_load(f)

    return DiscoveryConfig.model_validate(raw)


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

def main() -> None:
    # Config lives next to the script — no CLI args needed
    script_dir = Path(__file__).resolve().parent
    config_path = script_dir / "config.yaml"

    config = load_config(config_path)

    # Dependency injection: wire components together at the composition root
    collector = TagReportCollector(max_reports=config.max_reports)
    connector = ReaderConnector(
        settings=config.reader,
        collector=collector,
    )

    connector.run()

    # Print what we discovered
    collector.print_summary()


if __name__ == "__main__":
    main()
