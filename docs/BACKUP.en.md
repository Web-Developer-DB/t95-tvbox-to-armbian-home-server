# Complete Armbian SD backup

[Deutsch](BACKUP.md) | **English**

This procedure creates a sector-exact backup of the **whole** Armbian SD card
and restores it to the same or an equally large replacement card. It preserves
bootloader, partition table, DTB, kernel, rootfs, accounts, and configuration.

> [!CAUTION]
> A full image can contain accounts, SSH configuration, Samba databases, logs,
> and other secrets. Treat it as private recovery material: do not upload it to
> GitHub, a public release, or an unencrypted cloud folder.

## Requirements

- The T95 is stable and can be shut down cleanly; remove the card only after
  `sudo poweroff` and full power-off.
- Use an Ubuntu/Debian PC with a card reader and a **different** storage device
  with enough free space.
- Run these commands in a Linux shell. WSL2 is appropriate only when the SD
  block device is reliably passed through as `/dev/sdX`; native Linux is
  recommended.
- A replacement card must have at least the source card's byte size from
  `lsblk`, not merely the same printed capacity.

## Create the backup

1. Identify the complete removable card—not a partition:

   ```bash
   lsblk -b -o NAME,SIZE,MODEL,SERIAL,TRAN,RM,TYPE,FSTYPE,MOUNTPOINTS
   export SD_DEVICE=/dev/sdX   # replace with the actual lsblk device
   ```

   Confirm `TYPE=disk`, `TRAN=usb`, `RM=1`, the expected byte size, and no
   mountpoints. Never reuse `/dev/sda` from an old example: device assignment
   can change and a wrong `if=` or `of=` can overwrite an internal drive.

2. Unmount all automatically mounted SD partitions; check their numbers first:

   ```bash
   sudo umount "${SD_DEVICE}1"
   sudo umount "${SD_DEVICE}2"
   ```

   “Not mounted” is harmless. Unmount additional partitions if present.

3. Install zstd once, choose a destination on another drive, and read/compress
   the complete card:

   ```bash
   sudo apt update
   sudo apt install -y zstd
   export BACKUP_DIR=/absolute/path/to/T95-Backups
   mkdir -p "$BACKUP_DIR"
   STAMP="$(date +%Y%m%d-%H%M%S)"
   IMAGE="$BACKUP_DIR/t95-armbian-full-$STAMP.img.zst"
   set -o pipefail
   sudo dd if="$SD_DEVICE" bs=16M iflag=fullblock status=progress \
     | zstd -T0 -6 --checksum -o "$IMAGE"
   ```

   `if=` deliberately reads the entire device. This does not write to the SD
   card or internal eMMC.

4. Verify and retain checksum, image, and source-card byte size together:

   ```bash
   zstd -t "$IMAGE"
   sha256sum "$IMAGE" | tee "$IMAGE.sha256"
   sha256sum -c "$IMAGE.sha256"
   ```

## Restore a card

Restoration overwrites the selected card entirely.

1. Insert the target card, run `lsblk` again, set `SD_DEVICE` again, confirm it
   is removable and at least as large as the source, then unmount its
   partitions.

2. Verify the archive before writing:

   ```bash
   export IMAGE=/absolute/path/to/t95-armbian-full-YYYYMMDD-HHMMSS.img.zst
   sha256sum -c "$IMAGE.sha256"
   zstd -t "$IMAGE"
   ```

3. Write only when both checks succeed:

   ```bash
   set -o pipefail
   zstd -dc "$IMAGE" \
     | sudo dd of="$SD_DEVICE" bs=16M conv=fsync status=progress
   sync
   sudo udevadm settle
   ```

   This writes the whole target card, including boot area and partition table;
   it does not access internal eMMC.

4. Re-read the layout and optionally check the Armbian root filesystem
   read-only after confirming the partition number:

   ```bash
   sudo partprobe "$SD_DEVICE"
   sudo udevadm settle
   lsblk -b -o NAME,SIZE,FSTYPE,LABEL,PARTUUID,MOUNTPOINTS "$SD_DEVICE"
   sudo e2fsck -fn "${SD_DEVICE}2"
   ```

Unmount partitions, remove the card safely, and insert it **only while the T95
is powered off**. Then capture UART and test DHCP/SSH.

## Recovery boundaries

- A full SD backup restores one point in time; it is not a substitute for
  regular, versioned data backups.
- A smaller or defective replacement card cannot hold the image.
- Backups can contain old Armbian credentials and configuration. Share a newly
  hardened, locally personalized release image instead.
- This procedure never reads or writes T95 Android eMMC.

See [`README.en.md`](../README.en.md) for the verified SD path,
[`RELEASE.en.md`](RELEASE.en.md) for release details, and
[`PUBLISHING.en.md`](PUBLISHING.en.md) for public secret checks.
