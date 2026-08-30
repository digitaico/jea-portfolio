import sys
import logging
from datetime import datetime, timezone
from sllurp.llrp import LLRPReaderConfig, LLRPReaderClient

logging.getLogger('sllurp').setLevel(logging.ERROR)

READER_IP: str = '169.254.104.152'
READER_PORT: int = 5084
ANTENNAS = [1]

TIMESTAMP_FIELDS: frozenset[str] = frozenset({
    'FirstSeenTimestampUTC',
    'LastSeenTimestampUTC',
    'FirstSeenTimestampUptime',
    'LastSeenTimestampUptime',
})
EPC_FIELDS: frozenset[str] = frozenset({'EPC-96', 'EPC'})
HEX_FIELDS: frozenset[str] = frozenset({'C1G2CRC', 'C1G2PC', 'C1G2XPCW1', 'C1G2XPCW2'})


def _format_value(key: str, value: object) -> str:
    if value is None:
        return 'None'
    if key in EPC_FIELDS:
        return value.hex().upper() if isinstance(value, bytes) else str(value).upper()
    if key in TIMESTAMP_FIELDS:
        try:
            dt = datetime.fromtimestamp(int(value) / 1e6, tz=timezone.utc)
            return dt.strftime('%H:%M:%S.%f')[:-3] + ' UTC'
        except (TypeError, ValueError, OSError):
            return str(value)
    if key in HEX_FIELDS:
        try:
            return f'0x{int(value):04X}'
        except (TypeError, ValueError):
            return str(value)
    if key == 'ImpinjRFPhaseAngle':
        try:
            return f'{int(value) / 10:.1f}°'
        except (TypeError, ValueError):
            return str(value)
    if key == 'ImpinjRFDopplerFrequency':
        return f'{value} Hz'
    if key == 'PeakRSSI' or key == 'ImpinjPeakRSSI':
        return f'{value} dBm'
    if isinstance(value, bytes):
        return value.hex().upper()
    return str(value)


def _epc_from_report(report: dict) -> str:
    raw = report.get('EPC-96') or report.get('EPC')
    if raw is None:
        return 'UNKNOWN'
    return raw.hex().upper() if isinstance(raw, bytes) else str(raw).upper()


def handle_tags(reader: LLRPReaderClient, tag_reports: list[dict]) -> None:
    now = datetime.now()
    ts = f"{now.strftime('%H:%M:%S')}.{now.microsecond // 1000:03d}"

    for report in tag_reports:
        epc = _epc_from_report(report)
        lines: list[str] = [
            '─' * 50,
            f'[{ts}] EPC: {epc}',
        ]
        for key, value in sorted(report.items()):
            if key in EPC_FIELDS:
                continue
            formatted = _format_value(key, value)
            lines.append(f'  {key:<32}: {formatted}')

        sys.stdout.write('\n'.join(lines) + '\n')
        sys.stdout.flush()


def main() -> None:
    sys.stdout.write(f'Connecting to reader {READER_IP}:{READER_PORT} — capturing all fields...\n')
    sys.stdout.flush()

    config_args: dict = {
        'start_inventory': True,
        'reset_on_connect': True,
        'report_every_n_tags': 1,
        'tag_content_selector': {
            'EnableROSpecID': True,
            'EnableSpecIndex': True,
            'EnableInventoryParameterSpecID': True,
            'EnableAntennaID': True,
            'EnableChannelIndex': True,
            'EnablePeakRSSI': True,
            'EnableFirstSeenTimestamp': True,
            'EnableLastSeenTimestamp': True,
            'EnableTagSeenCount': True,
            'EnableAccessSpecID': True,
            'C1G2EPCMemorySelector': {
                'EnableCRC': True,
                'EnablePCBits': True,
                'EnableXPCBits': True,
            },
        },
    }

    config = LLRPReaderConfig(config_args)
    reader = LLRPReaderClient(READER_IP, READER_PORT, config)
    reader.add_tag_report_callback(handle_tags)
    reader.connect()

    sys.stdout.write('Live. Wave tags across the antenna...\n')
    sys.stdout.flush()

    try:
        reader.join(None)
    except (KeyboardInterrupt, SystemExit):
        sys.stdout.write('\nDisconnecting...\n')
        sys.stdout.flush()
    finally:
        reader.disconnect()


if __name__ == '__main__':
    main()
