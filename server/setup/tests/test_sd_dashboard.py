"""Exercise the login module with controlled sysfs and journal responses."""
import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import time
import unittest


MODULE = Path(__file__).resolve().parents[2] / "ssh-dashboard/95-sd-card-stats"
BOOT_ID = Path("/proc/sys/kernel/random/boot_id").read_text().strip().replace("-", "")
SD_DETECTION = ["mmc3: new ultra high speed SDR104 SDXC card at address 59b4",
                "mmcblk0: mmc3:59b4 SN128 119 GiB"]


class SDDashboardTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.fixture = Path(directory.name)
        self.env = {
            "PATH": f"{self.fixture}:{os.defpath}", "LC_ALL": "C", "T95_FIXTURE": directory.name,
            "T95_BOOT_ID": BOOT_ID, "T95_ROOT_PARTITION": "mmcblk0p1",
        }
        card = self.fixture / "mmc7:0001"
        card.mkdir()
        (card / "type").write_text("SD\n")
        self.command("findmnt", '''
            case " $* " in
                *" --raw "*) printf '179:1\\n' ;;
                *) printf '179:1  \\n' ;;
            esac
        ''')
        self.command("readlink", '''
            case "$3" in
                /sys/dev/block/179:1) echo "$T95_FIXTURE/mmcblk0/$T95_ROOT_PARTITION" ;;
                /sys/block/mmcblk0) echo "$T95_FIXTURE/mmcblk0" ;;
                /sys/block/mmcblk0/device) echo "$T95_FIXTURE/mmc7:0001" ;;
                *) exit 1 ;;
            esac
        ''')
        self.command("df", 'echo "/dev/mmcblk0p1 117G 10G 107G 9% /"')
        self.command("journalctl", '''
            case " $* " in
                *" --boot=$T95_BOOT_ID "*) boot=current ;;
                *" --boot=$T95_BOOT_ID-1 "*) boot=previous ;;
                *) exit 2 ;;
            esac
            printf '%s\\n' "$boot" >> "$T95_FIXTURE/calls"
            cat "$T95_FIXTURE/$boot" || exit 1
            if [ "$T95_DENY" = "$boot" ]; then
                echo 'Hint: You are currently not seeing messages from the system.' >&2
            fi
            if [ "$T95_HANG" = "$boot" ]; then
                trap '' TERM
                sleep 10
            fi
        ''')

    def command(self, name, script):
        command = self.fixture / name
        command.write_text("#!/bin/sh\n" + textwrap.dedent(script) + "\n")
        command.chmod(0o755)

    def journal(self, boot, messages):
        (self.fixture / boot).write_text("".join(
            f"2026-11-09T11:00:{second:02d}+01:00 kernel: {message}\n"
            for second, message in enumerate(messages)))

    def login(self):
        result = subprocess.run(["/bin/bash", str(MODULE)], env=self.env, capture_output=True,
                                text=True, check=True, timeout=4)
        self.assertEqual(result.stderr, "")
        self.assertIn("Laufwerksübersicht", result.stdout)
        return result.stdout

    def test_current_and_previous_use_their_own_host_and_count_once_per_message(self):
        self.journal("current", [
            "mmc7: Timeout waiting for hardware interrupt",
            "mmc7: CRC error",
            "mmcblk0: error -84 transferring data",
            "blk_update_request: I/O error, dev mmcblk0, sector 123",
            "Buffer I/O error on dev mmcblk0p1, logical block 0",
            "critical medium error, dev mmcblk0, sector 321",
            "mmcblk0: recovery failed!",
            "EXT4-fs error (device mmcblk0p1): I/O error reading directory block",
            "mmc3: Timeout waiting for hardware interrupt",
            "mmc7: maximum timeout value is 1s",
            "Buffer I/O error on dev sda1, logical block 0",
            "Buffer I/O error on dev mmcblk01, logical block 0",
            "I/O error, dev mmcblk2, sector 123",
            "EXT4-fs error (device mmcblk2p1): error reading directory block",
            "EXT4-fs (mmcblk0p1): mounted filesystem with opts: errors=remount-ro",
            "Buffer I/O error, logical block 0",
        ])
        self.journal("previous", ["mmc3: error -110 whilst initialising SD card", *SD_DETECTION,
                                  "mmc7: CRC error"])
        output = self.login()
        self.assertIn("CRITICAL: 7 detected (last 2026-11-09T11:00:06+01:00)", output)
        self.assertIn("CRITICAL: 1 detected (last 2026-11-09T11:00:07+01:00)", output)
        self.assertIn("WARNING: 1 detected (last 2026-11-09T11:00:00+01:00)", output)
        self.assertEqual(output.count("0 detected"), 1)
        self.assertNotIn("sector 123", output)
        self.assertEqual((self.fixture / "calls").read_text().splitlines(), ["current", "previous"])

    def test_clean_boots_report_zero_in_german(self):
        self.env.pop("LC_ALL")
        self.env["LANG"] = "de_DE.UTF-8"
        self.journal("current", ["EXT4-fs (mmcblk0p1): mounted filesystem"])
        self.journal("previous", SD_DETECTION)
        output = self.login()
        self.assertIn("Aktueller Start", output)
        self.assertIn("Voriger Journalstart", output)
        self.assertEqual(output.count("0 erkannt"), 4)

    def test_current_requires_root_partition_and_sd_type(self):
        self.journal("current", ["mmcblk0: error -110"])
        self.journal("previous", SD_DETECTION)
        self.env["T95_ROOT_PARTITION"] = "mmcblk01"
        self.assertIn("Current boot: Check unavailable", self.login())
        self.env["T95_ROOT_PARTITION"] = "mmcblk0p1"
        (self.fixture / "mmc7:0001/type").write_text("MMC\n")
        self.assertIn("Current boot: Check unavailable", self.login())

    def test_historical_mapping_requires_unambiguous_sd_detection(self):
        self.journal("current", ["Kernel initialized"])
        for previous in (["mmcblk0: error -110"],
                         ["mmc3: new high speed MMC card at address 59b4", SD_DETECTION[1]],
                         [*SD_DETECTION, "mmcblk0: mmc7:0001 OTHER 119 GiB"],
                         [*SD_DETECTION, "mmc3: new SDHC card at address 0001"]):
            with self.subTest(previous=previous):
                self.journal("previous", previous)
                self.assertIn("Previous journal boot: Check unavailable", self.login())

    def test_empty_missing_and_partially_readable_journals_are_unavailable(self):
        self.journal("current", [])
        output = self.login()
        self.assertIn("Current boot: Check unavailable", output)
        self.assertIn("Previous journal boot: Check unavailable", output)
        self.assertNotIn("0 detected", output)
        self.journal("current", ["mmcblk0: error -110"])
        self.env["T95_DENY"] = "current"
        output = self.login()
        self.assertIn("Current boot: Check unavailable", output)
        self.assertNotIn("1 detected", output)

    def test_partial_output_on_timeout_is_discarded_and_previous_boot_still_runs(self):
        self.journal("current", ["I/O error, dev mmcblk0, sector 123"])
        self.journal("previous", SD_DETECTION)
        self.env["T95_HANG"] = "current"
        started = time.monotonic()
        output = self.login()
        self.assertLess(time.monotonic() - started, 3)
        self.assertIn("Current boot: Check unavailable", output)
        self.assertEqual(output.count("0 detected"), 2)
        self.assertNotIn("CRITICAL", output)
