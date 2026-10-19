"""Real journals/locks with simulated devices, UDisks and Samba. No host effects."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import importlib.util
import io
import contextlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

LIB = Path(__file__).resolve().parents[1] / "lib"
sys.path.insert(0, str(LIB))
import t95_usb as usb


class FakeSystem(usb.System):
    def __init__(self, root, user):
        super().__init__(runner=self.stub_run, root=root)
        self.user = user
        self.calls, self.messages = [], []
        self.nodes = {}
        self.mount_list = [{"target": "/", "source": "/dev/mmcblk0p1", "maj:min": "179:1", "fstype": "ext4", "fsroot": "/"}]
        self.object_list = {}
        self.fail_inventory = self.fail_mounts = self.fail_guard = False
        self.fail_sync = self.fail_unmount = self.fail_power = self.fail_close = False
        self.on_unmount = None
        boot = self.path("/proc/sys/kernel/random/boot_id")
        boot.parent.mkdir(parents=True)
        boot.write_text("fixture-boot")
        self.path("/proc/swaps").write_text("Filename\tType\tSize\tUsed\tPriority\n")

    def stub_run(self, args, **kwargs):
        raise AssertionError(f"Unexpected external command in fixture: {args}")

    def add_disk(self, name="sda", seq="10", fs="ext4", label="DATA", parts=1, power=False, sibling=""):
        disk_number = f"8:{16 * (ord(name[-1]) - ord('a'))}"
        parent = {"name": "/dev/" + name, "type": "disk", "pkname": None, "maj:min": disk_number,
                  "tran": "usb", "fstype": fs if not parts else None, "label": label if not parts else None,
                  "uuid": "uuid-" + name if not parts else None, "children": []}
        self.nodes[parent["name"]] = parent
        sysdisk = self.path("/sys/class/block") / name
        sysdisk.mkdir(parents=True, exist_ok=True)
        (sysdisk / "diskseq").write_text(seq)
        drive = "/drives/" + name
        self.object_list[drive] = {"org.freedesktop.UDisks2.Drive": {"ConnectionBus": "usb", "CanPowerOff": power, "SiblingId": sibling}}
        items = []
        if parts:
            for index in range(1, parts + 1):
                item = {"name": "/dev/" + name + str(index), "type": "part", "pkname": parent["name"],
                        "maj:min": f"8:{int(disk_number.split(':')[1]) + index}", "tran": None,
                        "fstype": fs, "label": label if index == 1 else label + str(index),
                        "uuid": "uuid-" + name + str(index)}
                parent["children"].append(item)
                self.nodes[item["name"]] = item
                items.append(item)
        else:
            items.append(parent)
        for item in [parent, *parent["children"]]:
            self.object_list["/blocks/" + Path(item["name"]).name] = {"org.freedesktop.UDisks2.Block": {
                "DeviceNumber": os.makedev(*map(int, item["maj:min"].split(":"))), "Drive": drive,
                "HintIgnore": False, "HintAuto": True}}
        for item in items:
            target = self.user.base / Path(item["name"]).name
            target.mkdir(parents=True, exist_ok=True)
            self.mount_list.append({"target": str(target), "source": item["name"], "maj:min": item["maj:min"], "fstype": fs, "fsroot": "/"})
        return parent

    def inventory(self):
        if self.fail_inventory:
            raise usb.CommandError("lsblk failed")
        return deepcopy(self.nodes)

    def mounts(self):
        if self.fail_mounts:
            raise usb.CommandError("findmnt failed")
        return deepcopy(self.mount_list)

    def objects(self):
        return deepcopy(self.object_list)

    def activate_guard(self, disk):
        self.calls.append(("guard", disk.device))
        if not self.fail_guard:
            for interfaces in self.object_list.values():
                p = interfaces.get("org.freedesktop.UDisks2.Block", {})
                if p.get("Drive") == disk.drive:
                    p.update(HintIgnore=True, HintAuto=False)

    def wait_guard(self, disk, timeout=30):
        current = self.snapshot()
        current.verify(disk)
        blocks = [p for p in current.blocks.values() if p["Drive"] == disk.drive]
        if not blocks or any(not p["HintIgnore"] or p["HintAuto"] for p in blocks):
            raise usb.USBError("guard not confirmed")
        return current

    def sync(self, mount):
        self.calls.append(("sync", mount))
        if self.fail_sync:
            raise usb.CommandError("sync failed")

    def unmount(self, mount):
        self.calls.append(("unmount", mount))
        if self.fail_unmount:
            raise usb.CommandError("busy")
        self.mount_list = [m for m in self.mount_list if m["target"] != mount]
        if self.on_unmount:
            callback, self.on_unmount = self.on_unmount, None
            callback()

    def power_off(self, drive):
        self.calls.append(("power-off", drive))
        if self.fail_power:
            raise usb.USBError("unexpected power-off failure")
        diskname = drive.rsplit("/", 1)[1]
        disk = self.nodes["/dev/" + diskname]
        for item in [disk, *disk["children"]]:
            self.nodes.pop(item["name"], None)
            self.object_list.pop("/blocks/" + Path(item["name"]).name, None)
        self.object_list.pop(drive)
        return True

    def close_share(self, name):
        self.calls.append(("close-share", name))
        if self.fail_close:
            raise usb.CommandError("close-share failed")

    def permissions(self, user, path):
        return (True, not getattr(self, "read_only", False), True)

    def service(self, user, args, **kwargs):
        self.calls.append(("service", *args))
        return subprocess.CompletedProcess(args, 0, "active\n", "")

    def log(self, text):
        self.messages.append(text)


class FakeNet:
    def __init__(self):
        self.data = {}
        self.fail_query = self.fail_add = self.fail_delete = False
        self.calls = []

    def shares(self):
        if self.fail_query:
            raise usb.CommandError("Samba query failed")
        return dict(self.data)

    def reserved(self):
        return {"global", "t95-data"}

    def add(self, name, path):
        self.calls.append(("add", name, path))
        if self.fail_add:
            raise usb.CommandError("add failed")
        self.data[name] = path

    def delete(self, name):
        self.calls.append(("delete", name))
        if self.fail_delete:
            raise usb.CommandError("delete failed")
        self.data.pop(name, None)


class SambaRegistry:
    """Samba CLI boundary: info validates target directories; delete does not."""
    def __init__(self, system, user):
        self.system, self.user = system, user
        self.path = system.path('/var/lib/samba/usershares')
        self.path.mkdir(parents=True)
        for parent in ('/var', '/var/lib', '/var/lib/samba'):
            system.path(parent).chmod(0o755)
        self.path.chmod(0o1770)
        self.calls = []
        self.fail_delete = self.fail_config = False

    def write(self, name, path):
        record = self.path / name.lower()
        record.write_text(f'#VERSION 2\npath={path}\ncomment=T95 USB automatisch\n'
                          f'usershare_acl=S-1-5-21-123-1000:F\nguest_ok=n\nsharename={name}\n')
        record.chmod(0o644)

    def run(self, args, check=True, **kwargs):
        self.calls.append(args)
        output, error = '', ''
        if args[0] == 'testparm':
            if self.fail_config:
                raise usb.CommandError('testparm failed')
            output = '/var/lib/samba/usershares\n' if '--parameter-name=usershare path' in args else '[global]\n[T95-DATA]\n'
        elif args[:3] == ['net', 'usershare', 'add']:
            self.write(args[3], args[4])
        elif args[:3] == ['net', 'usershare', 'delete']:
            if self.fail_delete:
                raise usb.CommandError('delete failed')
            (self.path / args[3].lower()).unlink()
        elif args[:3] == ['net', 'usershare', 'info']:
            files = [self.path / args[3].lower()] if len(args) == 4 else sorted(self.path.iterdir())
            for record in files:
                fields = dict(line.split('=', 1) for line in record.read_text().splitlines()[1:])
                if not Path(fields['path']).is_dir():
                    error = f'info_fn: file {record} is not a well formed usershare file.\ninfo_fn: Error was Path is not a directory.'
                    break
                output += f"[{fields['sharename']}]\npath={fields['path']}\n\n"
        else:
            raise AssertionError(f'Unexpected Samba fixture command: {args}')
        if error and check:
            raise usb.CommandError(error)
        return subprocess.CompletedProcess(args, int(bool(error)), output, error)


class USBTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        home = self.root / "home/user"
        state = home / ".local/state/t95-usb-shares"
        state.mkdir(parents=True)
        self.user = usb.User("fixture-user", os.getuid(), os.getgid(), home, self.root / "media/user", state)
        runtime = self.root / "run/t95-usb"
        for part in ("", "locks", "guards", "operations"):
            (runtime / part).mkdir(parents=True, exist_ok=True)
            (runtime / part).chmod(0o755)
        (runtime / f"locks/shares-{self.user.uid}.lock").touch()
        self.runtime = usb.Runtime(self.user, runtime, os.getuid())
        self.system = FakeSystem(self.root, self.user)
        self.net = FakeNet()
        self.manager = usb.Manager(self.user, self.system, self.runtime, net=self.net)

    def tearDown(self):
        self.temp.cleanup()

    def ready(self, **kwargs):
        self.system.add_disk(**kwargs)
        self.manager.reconcile()
        return next(iter(self.net.data))

    def real_net(self):
        registry = SambaRegistry(self.system, self.user)
        self.system.run = registry.run
        self.manager.net = usb.Net(self.system, self.user)
        self.manager.net.owner = os.getuid()  # Temporary registry ownership, never host root paths.
        return registry

    def test_real_samba_registry_allows_cleanup_after_mount_directory_disappears(self):
        registry = self.real_net()
        self.system.add_disk(fs='exfat', label='Medion64')
        self.manager.reconcile()
        mount = self.system.mount_list[-1]['target']
        self.system.on_unmount = lambda: Path(mount).rmdir()
        self.manager.eject('Medion64')
        self.assertFalse(list(registry.path.iterdir()))
        self.assertFalse(list(self.user.state.glob('*.json')))
        self.assertEqual(self.runtime.operations()[-1]['phase'], 'ejected')
        self.assertTrue(self.runtime.guarded(self.system.snapshot().disk('/dev/sda')))

    def test_real_registry_resumes_failed_eject_with_missing_mount_directory(self):
        registry = self.real_net()
        self.system.add_disk(fs='exfat', label='Medion64')
        self.manager.reconcile()
        mount = self.system.mount_list[-1]['target']
        self.system.on_unmount = lambda: Path(mount).rmdir()
        registry.fail_delete = True
        with self.assertRaises(usb.USBError):
            self.manager.eject('Medion64')
        self.assertFalse(Path(mount).exists())
        self.assertEqual(self.runtime.operations()[-1]['phase'], 'failed')
        registry.fail_delete = False
        self.manager.eject('Medion64')
        self.assertEqual(self.runtime.operations()[-1]['phase'], 'ejected')
        self.assertFalse(list(registry.path.iterdir()))

    def test_real_registry_other_disk_can_publish_during_unmount_cleanup(self):
        registry = self.real_net()
        self.system.add_disk(label='DATA')
        self.manager.reconcile()
        target = self.system.mount_list[-1]['target']
        def hotplug():
            Path(target).rmdir()
            self.system.add_disk('sdb', '20', label='OTHER')
            self.manager.reconcile()
        self.system.on_unmount = hotplug
        self.manager.eject('DATA')
        self.assertEqual(set(self.manager.net.shares()), {'OTHER'})
        self.assertNotIn(('close-share', 'OTHER'), self.system.calls)
        self.assertEqual([p.name for p in registry.path.iterdir()], ['other'])

    def test_real_registry_missing_old_target_does_not_block_new_share(self):
        registry = self.real_net()
        registry.write('REMOVED', str(self.user.base / 'gone'))
        self.system.add_disk(label='NEW')
        self.manager.reconcile()
        self.assertEqual(set(self.manager.net.shares()), {'REMOVED', 'NEW'})
        queries = [c for c in registry.calls if c[:3] == ['net', 'usershare', 'info']]
        self.assertEqual(queries, [['net', 'usershare', 'info', 'NEW']])

    def test_status_keeps_device_and_operation_diagnostics_when_samba_query_fails(self):
        name = self.ready()
        disk = self.system.snapshot().disk('/dev/sda')
        self.runtime.operation(disk, 'failed', {name}, 'prior failure')
        self.net.fail_query = True
        with contextlib.redirect_stdout(io.StringIO()) as output:
            with self.assertRaises(usb.USBError):
                self.manager.status()
        self.assertIn('USB: /dev/sda', output.getvalue())
        self.assertIn('prior failure', output.getvalue())

    def test_real_registry_all_supported_filesystems_handle_removed_mountpoints(self):
        registry = self.real_net()
        for index, filesystem in enumerate(('ext4', 'exfat', 'vfat', 'ntfs', 'ntfs3'), 100):
            with self.subTest(filesystem=filesystem):
                self.system.nodes.clear()
                self.system.object_list.clear()
                self.system.add_disk(fs=filesystem, seq=str(index), label='DATA')
                self.manager.reconcile()
                mount = self.system.mount_list[-1]['target']
                self.system.on_unmount = lambda: Path(mount).rmdir()
                self.manager.eject('DATA')
                self.assertFalse(list(registry.path.iterdir()))
                self.assertEqual(self.runtime.operations()[-1]['phase'], 'ejected')

    def test_real_registry_all_partition_mount_directories_can_disappear(self):
        registry = self.real_net()
        self.system.add_disk(parts=2)
        self.manager.reconcile()
        normal = self.system.unmount
        def unmount(path):
            normal(path)
            Path(path).rmdir()
        self.system.unmount = unmount
        self.manager.eject('DATA')
        self.assertFalse(list(registry.path.iterdir()))
        self.assertEqual(len([c for c in self.system.calls if c[0] == 'unmount']), 2)

    def test_real_registry_missing_target_still_allows_confirmed_power_off(self):
        registry = self.real_net()
        self.system.add_disk(power=True)
        self.manager.reconcile()
        mount = self.system.mount_list[-1]['target']
        self.system.on_unmount = lambda: Path(mount).rmdir()
        self.manager.eject('DATA')
        self.assertFalse(list(registry.path.iterdir()))
        self.assertEqual(self.runtime.operations()[-1]['phase'], 'powered-off')

    def test_real_registry_read_failure_does_not_unmount_or_delete_state(self):
        registry = self.real_net()
        self.system.add_disk()
        self.manager.reconcile()
        registry.fail_config = True
        with self.assertRaises(usb.USBError):
            self.manager.eject('DATA')
        self.assertTrue(list(registry.path.iterdir()))
        self.assertTrue(list(self.user.state.glob('*.json')))
        self.assertFalse(any(c[0] == 'unmount' for c in self.system.calls))

    def test_real_registry_accepts_legacy_versions_without_target_directory(self):
        registry = self.real_net()
        for version in ('#VERSION 1', '#VERSION 2'):
            content = f'{version}\npath={self.user.base}/gone\ncomment=old\nusershare_acl=S-1-1-0:R\n'
            if version == '#VERSION 2':
                content += 'guest_ok=n\n'
            (registry.path / 'legacy').write_text(content)
            (registry.path / 'legacy').chmod(0o644)
            self.assertEqual(self.manager.net.shares(), {'legacy': str(self.user.base / 'gone')})

    def test_reconciliation_during_update_does_not_prevent_eject_resumption(self):
        registry = self.real_net()
        self.system.add_disk(label='Medion64')
        self.manager.reconcile()
        mount = self.system.mount_list[-1]['target']
        self.system.on_unmount = lambda: Path(mount).rmdir()
        registry.fail_delete = True
        with self.assertRaises(usb.USBError): self.manager.eject('Medion64')
        registry.fail_delete = False
        self.manager.reconcile()  # The installer's final step, with the drive still guarded/unmounted.
        self.assertFalse(list(registry.path.iterdir()))
        self.assertFalse(self.manager.state.read())
        self.manager.eject('Medion64')
        self.assertEqual(self.runtime.operations()[-1]['phase'], 'ejected')

    def test_real_registry_rejects_malformed_unsafe_and_incomplete_definitions(self):
        registry = self.real_net()
        registry.write('DATA', str(self.user.base / 'gone'))
        record = registry.path / 'data'
        original = record.read_text()
        cases = {
            'wrong name': original.replace('sharename=DATA', 'sharename=OTHER'),
            'relative path': original.replace(f'path={self.user.base}/gone', 'path=relative'),
            'invalid ACL': original.replace('S-1-5-21-123-1000:F', 'not-an-acl'),
            'incomplete': '#VERSION 2\npath=/gone\n',
            'unknown version': original.replace('#VERSION 2', '#VERSION 3'),
            'oversized': original + 'x' * 10241,
        }
        for description, content in cases.items():
            with self.subTest(description=description):
                record.write_text(content)
                with self.assertRaises(usb.CommandError): self.manager.net.shares()
        record.write_text(original)
        record.chmod(0o666)
        with self.assertRaises(usb.CommandError): self.manager.net.shares()
        record.unlink()
        record.symlink_to(self.root / 'outside')
        with self.assertRaises(usb.CommandError): self.manager.net.shares()
        record.unlink()
        os.mkfifo(record)
        with self.assertRaises(usb.CommandError): self.manager.net.shares()

    def test_real_registry_directory_links_and_unprotected_group_write_are_refused(self):
        registry = self.real_net()
        registry.path.chmod(0o770)
        with self.assertRaises(usb.CommandError): self.manager.net.shares()
        registry.path.rmdir()
        elsewhere = self.root / 'elsewhere'
        elsewhere.mkdir()
        registry.path.symlink_to(elsewhere)
        with self.assertRaises(usb.CommandError): self.manager.net.shares()

    def test_real_registry_ignores_samba_temporary_files_and_foreign_owners(self):
        registry = self.real_net()
        (registry.path / ':tmpABCDEF').write_text('not finished')
        registry.write('FOREIGN', str(self.user.base / 'other'))
        real_stat = usb.os.stat
        def foreign_stat(path, *args, **kwargs):
            result = real_stat(path, *args, **kwargs)
            return SimpleNamespace(st_uid=self.user.uid + 1) if path == 'foreign' else result
        with patch.object(usb.os, 'stat', side_effect=foreign_stat):
            self.assertEqual(self.manager.net.shares(), {})

    def test_real_registry_partial_failure_keeps_other_devices_visible_in_status(self):
        registry = self.real_net()
        self.system.add_disk()
        self.manager.reconcile()
        (registry.path / 'data').write_text('invalid')
        with contextlib.redirect_stdout(io.StringIO()) as output:
            with self.assertRaisesRegex(usb.USBError, 'Status unvollständig'):
                self.manager.status()
        self.assertIn('USB: /dev/sda', output.getvalue())
        self.assertIn('FEHLER:', output.getvalue())

    def test_supported_filesystems_are_published_and_ejected_without_global_stop(self):
        for fs in ("ext4", "exfat", "vfat", "ntfs", "ntfs3"):
            with self.subTest(fs=fs):
                self.system.nodes.clear()
                self.system.object_list.clear()
                self.net.data.clear()
                for p in self.user.state.iterdir(): p.unlink()
                for p in (self.runtime.path / "guards").iterdir(): p.unlink()
                self.system.mount_list = self.system.mount_list[:1]
                name = self.ready(fs=fs)
                self.manager.eject(name)
                self.assertFalse(self.net.data)
                self.assertFalse([m for m in self.system.mount_list if m["target"] != "/"])
                self.assertTrue(self.runtime.guarded(self.system.snapshot().disk("/dev/sda")))
                self.assertIn("Sicher ausgehängt", self.system.messages[-1])
                self.assertFalse(any(call[0] == "service" for call in self.system.calls))

    def test_other_devices_work_and_new_device_is_published_during_eject(self):
        name = self.ready()
        self.system.add_disk("sdb", "20", label="OTHER")
        self.manager.reconcile()
        before_b = self.net.data["OTHER"]
        def hotplug():
            self.system.add_disk("sdc", "30", label="NEW")
            self.manager.reconcile()
        self.system.on_unmount = hotplug
        self.manager.eject(name)
        self.assertEqual(self.net.data["OTHER"], before_b)
        self.assertIn("NEW", self.net.data)
        self.assertEqual(len([m for m in self.system.mount_list if m["target"] != "/"]), 2)
        self.assertNotIn(("close-share", "OTHER"), self.system.calls)

    def test_eject_reserves_names_when_new_device_has_the_same_label(self):
        name = self.ready(label="DATA")
        def hotplug():
            self.system.add_disk("sdb", "20", label="DATA")
            self.manager.reconcile()
        self.system.on_unmount = hotplug
        self.manager.eject(name)
        self.assertEqual(set(self.net.data), {"DATA-2"})
        self.assertNotIn(("close-share", "DATA-2"), self.system.calls)

    def test_power_off_removal_is_confirmed(self):
        name = self.ready(power=True)
        self.manager.eject(name)
        self.assertNotIn("/dev/sda", self.system.nodes)
        self.assertEqual(self.runtime.operations()[-1]["phase"], "powered-off")

    def test_sibling_drive_is_not_powered_off(self):
        name = self.ready(power=True, sibling="reader")
        self.system.add_disk("sdb", "20", label="OTHER", power=True, sibling="reader")
        self.manager.reconcile()
        self.manager.eject(name)
        self.assertFalse(any(c[0] == "power-off" for c in self.system.calls))
        self.assertIn("OTHER", self.net.data)

    def test_unexpected_power_error_is_not_reported_as_safe(self):
        name = self.ready(power=True)
        self.system.fail_power = True
        with self.assertRaisesRegex(usb.USBError, "power-off"):
            self.manager.eject(name)
        self.assertEqual(self.runtime.operations()[-1]["phase"], "failed")
        self.assertFalse(any("kann entfernt" in m or "Du kannst" in m for m in self.system.messages))

    def test_enumeration_mount_and_samba_query_errors_do_not_remove_anything(self):
        name = self.ready()
        for attribute, obj in (("fail_inventory", self.system), ("fail_mounts", self.system), ("fail_query", self.net)):
            with self.subTest(attribute=attribute):
                setattr(obj, attribute, True)
                with self.assertRaises(usb.USBError): self.manager.eject(name)
                setattr(obj, attribute, False)
                self.assertIn(name, self.net.data)
                self.assertFalse(any(c[0] == "unmount" for c in self.system.calls))

    def test_empty_samba_result_uses_valid_saved_mapping(self):
        name = self.ready()
        self.net.data.clear()
        self.manager.eject(name)
        self.assertEqual(self.runtime.operations()[-1]["phase"], "ejected")

    def test_guard_failure_stops_before_unmount(self):
        name = self.ready()
        self.system.fail_guard = True
        with self.assertRaisesRegex(usb.USBError, "guard"):
            self.manager.eject(name)
        self.assertIn(name, self.net.data)
        self.assertFalse(any(c[0] == "unmount" for c in self.system.calls))

    def test_busy_and_sync_errors_keep_share_and_allow_retry(self):
        name = self.ready()
        for attr in ("fail_close", "fail_sync", "fail_unmount"):
            setattr(self.system, attr, True)
            with self.assertRaises(usb.USBError): self.manager.eject(name)
            self.assertIn(name, self.net.data)
            setattr(self.system, attr, False)
        self.manager.eject(name)
        self.assertEqual(self.runtime.operations()[-1]["phase"], "ejected")

    def test_delete_failure_is_retryable_after_unmount(self):
        name = self.ready()
        self.net.fail_delete = True
        with self.assertRaises(usb.USBError): self.manager.eject(name)
        self.assertIn(name, self.net.data)
        self.net.fail_delete = False
        self.manager.eject(name)
        self.assertFalse(self.net.data)

    def test_all_partitions_and_all_their_shares_are_closed(self):
        name = self.ready(parts=2)
        names = set(self.net.data)
        self.manager.eject(name)
        self.assertEqual({c[1] for c in self.system.calls if c[0] == "close-share"}, names)
        self.assertEqual(len([c for c in self.system.calls if c[0] == "unmount"]), 2)
        self.assertFalse(self.net.data)

    def test_unpartitioned_disk(self):
        name = self.ready(parts=0)
        self.manager.eject(name)
        self.assertEqual(self.runtime.operations()[-1]["phase"], "ejected")

    def test_btrfs_source_suffix_and_nested_subvolumes(self):
        self.system.add_disk(fs="btrfs")
        fsdevices = self.system.path("/sys/fs/btrfs/uuid-sda1/devices")
        fsdevices.mkdir(parents=True)
        (fsdevices / "sda1").symlink_to(self.system.path("/sys/class/block/sda1"))
        self.system.path("/sys/class/block/sda1").mkdir()
        mount = self.system.mount_list[-1]
        mount["source"] += "[/@]"
        mount["maj:min"] = "0:99"
        nested = deepcopy(mount)
        nested["target"] += "/nested"
        nested["source"] = "/dev/sda1[/@nested]"
        Path(nested["target"]).mkdir()
        self.system.mount_list.append(nested)
        self.manager.reconcile()
        self.manager.eject(next(iter(self.net.data)))
        unmounts = [c[1] for c in self.system.calls if c[0] == "unmount"]
        self.assertEqual(unmounts[0], nested["target"])
        self.assertFalse(self.net.data)

    def test_ntfs_3g_anonymous_mount_device_number(self):
        self.system.add_disk(fs="ntfs")
        mount = self.system.mount_list[-1]
        mount.update(fstype="fuseblk", **{"maj:min": "0:88"})
        self.manager.reconcile()
        self.manager.eject(next(iter(self.net.data)))
        self.assertTrue(any(c[0] == "unmount" for c in self.system.calls))

    def test_foreign_mount_and_non_usb_are_rejected(self):
        name = self.ready()
        self.system.mount_list[-1]["target"] = "/srv/foreign"
        with self.assertRaises(usb.USBError): self.manager.eject(name)
        self.system.mount_list[-1]["target"] = next(iter(self.net.data.values()))
        self.system.object_list["/drives/sda"]["org.freedesktop.UDisks2.Drive"]["ConnectionBus"] = "sata"
        with self.assertRaises(usb.USBError): self.manager.eject(name)

    def test_mapper_and_swap_are_rejected(self):
        self.system.add_disk()
        self.system.nodes["/dev/sda1"]["type"] = "crypt"
        with self.assertRaises(usb.USBError): self.system.snapshot().disk("/dev/sda1")
        self.system.nodes["/dev/sda1"]["type"] = "part"
        self.system.nodes["/dev/sda1"]["fstype"] = "swap"
        with self.assertRaises(usb.USBError): self.system.snapshot().disk("/dev/sda1")

    def test_reused_device_name_cannot_resume_old_operation(self):
        name = self.ready()
        self.manager.eject(name)
        self.system.path("/sys/class/block/sda/diskseq").write_text("999")
        with self.assertRaises(usb.USBError): self.manager.eject(name)

    def test_replug_and_reboot_do_not_inherit_old_guard(self):
        name = self.ready()
        self.manager.eject(name)
        self.system.path("/sys/class/block/sda/diskseq").write_text("999")
        self.system.mount_list.append({"target": str(self.user.base / "sda1"), "source": "/dev/sda1", "maj:min": "8:1", "fstype": "ext4", "fsroot": "/"})
        self.manager.reconcile()
        self.assertIn(name, self.net.data)
        self.manager.eject(name)
        for p in (self.runtime.path / "guards").iterdir(): p.unlink()
        self.system.path("/proc/sys/kernel/random/boot_id").write_text("new-boot")
        self.assertFalse(self.runtime.guarded(self.system.snapshot().disk("/dev/sda")))

    def test_guard_survives_daemon_restart_and_repeated_events(self):
        name = self.ready()
        self.manager.eject(name)
        self.manager.reconcile()
        self.manager.reconcile()
        self.assertFalse(self.net.data)
        self.assertTrue(self.runtime.guarded(self.system.snapshot().disk("/dev/sda")))

    def test_duplicate_and_concurrent_unlabelled_mounts_are_unique(self):
        self.system.add_disk(label="")
        self.system.add_disk("sdb", "20", label="")
        with ThreadPoolExecutor(max_workers=2) as executor:
            list(executor.map(lambda _: self.manager.reconcile(), range(2)))
        self.assertEqual(set(self.net.data), {"Extern-USB-1", "Extern-USB-2"})
        self.assertEqual(len([c for c in self.net.calls if c[0] == "add"]), 2)

    def test_duplicate_labels_and_static_share_names_do_not_collide(self):
        self.system.add_disk(label="T95-DATA")
        self.system.add_disk("sdb", "20", label="T95-DATA")
        self.manager.reconcile()
        self.assertEqual(set(self.net.data), {"T95-DATA-2", "T95-DATA-3"})

    def test_same_disk_lock_is_exclusive_but_other_disk_is_independent(self):
        acquired = threading.Event()
        release = threading.Event()
        def hold():
            with self.runtime.lock("disk-10.lock", create=True, wait=0):
                acquired.set()
                release.wait(3)
        thread = threading.Thread(target=hold)
        thread.start()
        self.assertTrue(acquired.wait(2))
        try:
            with self.assertRaises(usb.USBError):
                with self.runtime.lock("disk-10.lock", create=True, wait=0): pass
            with self.runtime.lock("disk-20.lock", create=True, wait=0): pass
        finally:
            release.set()
            thread.join()

    def test_failed_publication_or_state_write_cannot_leave_false_success(self):
        self.system.add_disk()
        self.net.fail_add = True
        with self.assertRaises(usb.USBError): self.manager.reconcile()
        self.assertFalse(list(self.user.state.glob("*.json")))
        self.net.fail_add = False
        with patch.object(self.manager.state, "write", side_effect=OSError("disk full")):
            with self.assertRaises(OSError): self.manager.reconcile()
        self.assertFalse(self.net.data)

    def test_share_creation_with_failed_confirmation_is_rolled_back(self):
        self.system.add_disk()
        normal = self.net.add
        def partial_add(name, path):
            normal(name, path)
            raise usb.CommandError("confirmation query failed after add")
        with patch.object(self.net, "add", side_effect=partial_add):
            with self.assertRaises(usb.CommandError): self.manager.reconcile()
        self.assertFalse(self.net.data)
        self.assertFalse(list(self.user.state.glob("*.json")))

    def test_legacy_map_is_migrated_only_when_current_mapping_matches(self):
        self.system.add_disk()
        mount = self.system.mount_list[-1]["target"]
        self.net.data["OLD"] = mount
        old = self.user.state / "sda1.map"
        old.write_text(f"OLD\t{mount}\t/dev/sda1\tuuid-sda1\n")
        self.manager.reconcile()
        self.assertFalse(old.exists())
        self.assertEqual(self.manager.state.read()[0]["schema"], 1)
        self.assertEqual(set(self.net.data), {"OLD"})

    def test_query_failure_does_not_delete_stale_state(self):
        name = self.ready()
        self.system.mount_list = self.system.mount_list[:1]
        self.net.fail_query = True
        with self.assertRaises(usb.USBError): self.manager.reconcile()
        self.assertTrue(list(self.user.state.glob("*.json")))
        self.assertIn(name, self.net.data)

    def test_symlink_state_and_runtime_are_refused(self):
        outside = self.root / "outside"
        outside.write_text("untouched")
        (self.user.state / "evil.json").symlink_to(outside)
        with self.assertRaises(OSError): self.manager.state.read()
        self.assertEqual(outside.read_text(), "untouched")
        guard = self.runtime.path / "guards"
        guard.rmdir()
        guard.symlink_to(self.root)
        with self.assertRaises(usb.USBError): self.runtime.check()

    def test_diagnostics_are_read_only(self):
        self.ready()
        self.system.calls.clear()
        before = {p.name: p.read_bytes() for p in self.user.state.iterdir()}
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.manager.status()
        self.assertIn("Auswurfsperre=aus", output.getvalue())
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.user.state.iterdir()})
        self.assertTrue(all(c[0] == "service" and c[1] == "is-active" for c in self.system.calls))

    def test_actual_net_adapter_distinguishes_empty_and_failed_queries(self):
        registry = self.real_net()
        self.assertEqual(self.manager.net.shares(), {})
        registry.fail_config = True
        with self.assertRaises(usb.CommandError): self.manager.net.shares()

    def test_failed_first_query_uses_saved_mapping_then_requires_healthy_samba(self):
        name = self.ready()
        normal = self.net.shares
        count = [0]
        def query():
            count[0] += 1
            if count[0] == 1:
                raise usb.CommandError("transient query error")
            return normal()
        with patch.object(self.net, "shares", side_effect=query):
            self.manager.eject(name)
        self.assertEqual(self.runtime.operations()[-1]["phase"], "ejected")

    def test_repeated_reconciliation_does_not_rewrite_unchanged_state(self):
        self.ready()
        before = {p.name: (p.stat().st_ino, p.stat().st_mtime_ns) for p in self.user.state.iterdir()}
        messages = list(self.system.messages)
        self.manager.reconcile()
        after = {p.name: (p.stat().st_ino, p.stat().st_mtime_ns) for p in self.user.state.iterdir()}
        self.assertEqual(before, after)
        self.assertEqual(messages, self.system.messages)

    def test_invalid_eject_invocations_have_usage_exit_code(self):
        for arguments in ([], [""], ["--unknown"], ["one", "two"]):
            with self.subTest(arguments=arguments), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as result:
                    usb.main(["eject", *arguments])
                self.assertEqual(result.exception.code, 2)

    def test_real_empty_inventory_is_an_error(self):
        system = usb.System(runner=lambda args, **kwargs: subprocess.CompletedProcess(args, 0, '{"blockdevices": []}', ""))
        with self.assertRaisesRegex(usb.USBError, "leer"): system.inventory()

    def test_active_swap_file_blocks_eject_before_connections_are_closed(self):
        name = self.ready()
        mount = self.system.mount_list[-1]["target"]
        self.system.path("/proc/swaps").write_text("Filename Type Size Used Priority\n" + mount + "/swapfile file 1024 0 -2\n")
        with self.assertRaisesRegex(usb.USBError, "Swap"):
            self.manager.eject(name)
        self.assertFalse(any(c[0] in ("close-share", "unmount") for c in self.system.calls))

    def test_btrfs_member_on_another_drive_blocks_eject_of_its_ext4_partition(self):
        name = self.ready(parts=2)
        self.system.nodes["/dev/sda2"]["fstype"] = "btrfs"
        self.system.mount_list = [m for m in self.system.mount_list if m["source"] != "/dev/sda2"]
        devices = self.system.path("/sys/fs/btrfs/uuid-sda2/devices")
        devices.mkdir(parents=True)
        (devices / "sda2").symlink_to(self.system.path("/sys/class/block/sda2"))
        (devices / "sdb1").symlink_to(self.system.path("/sys/class/block/sdb1"))
        with self.assertRaisesRegex(usb.USBError, "mehrere physische"):
            self.manager.eject(name)

    def test_interrupted_and_partial_unmount_can_resume(self):
        name = self.ready(parts=2)
        def interrupted():
            raise KeyboardInterrupt()
        self.system.on_unmount = interrupted
        with self.assertRaises(KeyboardInterrupt): self.manager.eject(name)
        self.assertEqual(self.runtime.operations()[-1]["phase"], "failed")
        self.assertEqual(len(self.system.mount_list), 2)
        self.manager.eject(name)
        self.assertEqual(self.runtime.operations()[-1]["phase"], "ejected")

    def test_unmount_command_success_without_unmount_is_detected(self):
        name = self.ready()
        with patch.object(self.system, "unmount", return_value=None):
            with self.assertRaisesRegex(usb.USBError, "Mounts sind noch vorhanden"):
                self.manager.eject(name)
        self.assertIn(name, self.net.data)

    def test_device_disappearance_is_not_reported_as_success(self):
        name = self.ready()
        def disconnected(): self.system.nodes.clear()
        self.system.on_unmount = disconnected
        with self.assertRaises(usb.USBError): self.manager.eject(name)
        self.assertEqual(self.runtime.operations()[-1]["phase"], "failed")

    def test_stale_saved_path_cannot_select_a_replacement_device(self):
        name = self.ready()
        self.net.data.clear()
        self.system.path("/sys/class/block/sda/diskseq").write_text("999")
        with self.assertRaises(usb.USBError): self.manager.eject(name)
        self.assertFalse(any(c[0] == "unmount" for c in self.system.calls))

    def test_mount_rejected_by_kernel_does_not_create_a_share(self):
        self.system.add_disk(fs="ntfs")
        self.system.mount_list = self.system.mount_list[:1]
        self.manager.reconcile()
        self.assertFalse(self.net.data)
        with contextlib.redirect_stdout(io.StringIO()) as output: self.manager.status()
        self.assertIn("ntfs", output.getvalue())
        self.assertIn("Nicht eingehängt", output.getvalue())

    def test_readonly_and_ext4_permissions_are_reported_without_changing_data(self):
        self.ready()
        self.system.read_only = True
        with contextlib.redirect_stdout(io.StringIO()) as output: self.manager.status()
        self.assertIn("schreiben=False", output.getvalue())
        self.assertFalse(any(c[0] in ("sync", "unmount", "power-off") for c in self.system.calls))

    def test_real_guard_wait_checks_all_partitions_and_drive_jobs(self):
        self.system.add_disk(parts=2)
        disk = self.system.snapshot().disk("/dev/sda")
        self.system.activate_guard(disk)
        now = [0.0]
        def clock():
            now[0] += 0.2
            return now[0]
        self.system.object_list["/jobs/mount"] = {"org.freedesktop.UDisks2.Job": {"Objects": [disk.drive]}}
        with patch.object(usb.time, "monotonic", side_effect=clock), patch.object(usb.time, "sleep"):
            with self.assertRaises(usb.USBError): usb.System.wait_guard(self.system, disk, timeout=2)
        del self.system.object_list["/jobs/mount"]
        self.system.object_list.pop("/blocks/sda2")
        with patch.object(usb.time, "monotonic", side_effect=clock), patch.object(usb.time, "sleep"):
            with self.assertRaises(usb.USBError): usb.System.wait_guard(self.system, disk, timeout=2)

    def test_real_udisks_poweroff_distinguishes_not_supported(self):
        class DBusError(Exception):
            def get_dbus_name(self): return self.args[0]
        class Drive:
            def PowerOff(self, *args, **kwargs): raise DBusError("org.freedesktop.UDisks2.Error.NotSupported")
        system = usb.System()
        system._bus = SimpleNamespace(get_object=lambda *args: Drive())
        module = SimpleNamespace(DBusException=DBusError, Interface=lambda obj, iface: obj)
        with patch.dict(sys.modules, dbus=module):
            self.assertFalse(system.power_off("/drive"))
        class Broken(Drive):
            def PowerOff(self, *args, **kwargs): raise DBusError("org.freedesktop.UDisks2.Error.DeviceBusy")
        system._bus = SimpleNamespace(get_object=lambda *args: Broken())
        with patch.dict(sys.modules, dbus=module):
            with self.assertRaises(usb.USBError): system.power_off("/drive")


if __name__ == "__main__":
    unittest.main()
