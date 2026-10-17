# Complete Armbian SD backup

[Deutsch](BACKUP.md) | **English**

**Optional recovery path:** you can reinstall the base system at any time
using the [installation guide](INSTALLATION.en.md). A full SD backup saves
having to recreate your accounts, settings, and services, and preserves SD
files at the time of backup. A fresh installation overwrites the selected SD;
keep any personal files you want to retain separately.

This procedure backs up the **entire** Armbian SD card: bootloader, partition
table, hardware description (DTB), kernel, system, accounts, and configuration.
It excludes data on separate USB drives or internal eMMC storage.
Keep all PC steps in the same terminal window so selected paths remain available.

> [!CAUTION]
> A backup can contain passwords, SSH settings, Samba databases, and other
> secrets. Keep it private and encrypted when stored in a cloud folder.
> Restoring overwrites the entire selected target card.

[Back to installation](INSTALLATION.en.md#6-back-up-the-base-system) · [Help](TROUBLESHOOTING.en.md)

## Requirements

- Shut down the T95 before removing its SD card.
- Use a Linux PC with a USB card reader and a **different** destination drive.
- Reserve at least the entire SD card's size as free backup space. Compression
  may save space, but already compressed data may remain close to raw size.
- The replacement card must have at least the original card's size **in bytes**,
  not merely the same advertised capacity.
- Use native Linux, or WSL2 with reliable USB block-device access as `/dev/sdX`.

<a id="create-the-backup"></a>

## 1. Shut down the box

**On the T95, normal SSH user with `sudo`:**

```bash
sudo poweroff
```

Wait until the box is fully off, then move its SD to the PC's USB card reader.

## 2. Identify the source card

**On the Linux PC, normal user:**

```bash
lsblk -b -o NAME,SIZE,MODEL,SERIAL,TRAN,RM,TYPE,FSTYPE,MOUNTPOINTS
```

Choose the **whole card**, not a partition. Check `TYPE=disk`, `TRAN=usb`,
`RM=1`, and the expected size. Record its byte size with the backup.
`/dev/sdX` below is a placeholder: replace it with the actual device from your list.

> [!WARNING]
> Device names can change every time a card is inserted. A wrong `if=` or `of=`
> can overwrite an internal drive. Never reuse a device name without checking it.

**On the Linux PC, normal user; adapt the placeholder first:**

```bash
export SD_DEVICE=/dev/sdX
```

## 3. Unmount partitions

Release `v1.0.1` has one ext4 partition. Check your card's layout first.

**On the Linux PC, normal user with `sudo`:**

```bash
sudo umount "${SD_DEVICE}1"
```

“Not mounted” is harmless. Unmount additional partitions if your actual card has any.

## 4. Create the compressed backup

**On the Linux PC, normal user with `sudo`; install zstd once:**

```bash
sudo apt update
sudo apt install -y zstd
```

Set `BACKUP_DIR` to a real folder on the **other** destination drive.
Replace the example path before running this block.

**On the Linux PC, normal user:**

```bash
export BACKUP_DIR=/absolute/path/to/T95-Backups
mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
IMAGE="$BACKUP_DIR/t95-armbian-full-$STAMP.img.zst"
```

**On the Linux PC, normal user; `sudo` reads the card:**

```bash
set -o pipefail
sudo dd if="$SD_DEVICE" bs=16M iflag=fullblock status=progress \
  | zstd -T0 -6 --check -o "$IMAGE"
```

This reads the entire SD card without writing to it or to T95 eMMC.
It may take a long time. Stop here if the command reports an error.

## 5. Verify and retain the backup

**On the Linux PC, normal user:**

```bash
zstd -t "$IMAGE"
```

Create a checksum containing the filename without its original directory:

**On the Linux PC, normal user:**

```bash
(
  cd -- "$(dirname -- "$IMAGE")" || exit 1
  sha256sum -- "$(basename -- "$IMAGE")" > "$(basename -- "$IMAGE").sha256" &&
    sha256sum -c -- "$(basename -- "$IMAGE").sha256"
)
```

Both checks must succeed: no zstd error, and a checksum result ending in `OK`.
Keep the image, matching `.sha256` file, and original card's byte size together.
Copy this complete backup set to a second protected drive.

## Restore a card

Restoration erases the selected target card. Follow these steps only to replace
an SD card or restore a saved system state.

### 1. Check the target card

**On the Linux PC, normal user; replace `/dev/sdX` with the newly checked device:**

```bash
lsblk -b -o NAME,SIZE,MODEL,SERIAL,TRAN,RM,TYPE,FSTYPE,MOUNTPOINTS
export SD_DEVICE=/dev/sdX
```

Confirm a removable USB disk at least as large in bytes as the original.
Check partition numbers and unmount all automatically mounted partitions.

**On the Linux PC, normal user with `sudo`:**

```bash
sudo umount "${SD_DEVICE}1"
```

### 2. Verify the selected archive

Replace the example with the actual archive path. Its matching checksum file
must be beside it as `FILENAME.img.zst.sha256`.

**On the Linux PC, normal user:**

```bash
export IMAGE=/absolute/path/to/t95-armbian-full-YYYYMMDD-HHMMSS.img.zst
```

**On the Linux PC, normal user; run this entire verification block:**

```bash
T95_BACKUP_VERIFIED=
T95_BACKUP_SHA256=
if [[ -f "$IMAGE" && -f "$IMAGE.sha256" ]] &&
   read -r T95_BACKUP_SHA256 _ < "$IMAGE.sha256" &&
   [[ "$T95_BACKUP_SHA256" =~ ^[[:xdigit:]]{64}$ ]] &&
   printf '%s  %s\n' "$T95_BACKUP_SHA256" "$IMAGE" | sha256sum -c - &&
   zstd -t -- "$IMAGE"; then
  T95_BACKUP_VERIFIED="$IMAGE"
  printf '%s\n' 'OK: Selected archive verified. Writing is permitted.'
else
  printf '%s\n' 'STOP: Archive or checksum is missing, invalid, or does not match. Do not write.' >&2
  false
fi
```

**Success:** `OK: Selected archive verified. Writing is permitted.`
For `STOP`, stay here and check the paths, archive, and checksum.
This always verifies the **selected archive**, including when an older checksum
file records its original absolute path. The old path is not used to select a file.
Keep the same PC window open. Repeat this step after changing `IMAGE` or opening
another terminal window.

### 3. Write the complete image

**On the Linux PC, normal user; `sudo` writes the checked target card:**

```bash
if [[ -n "${T95_BACKUP_VERIFIED:-}" && "$T95_BACKUP_VERIFIED" == "$IMAGE" ]]; then
  set -o pipefail
  if zstd -dc -- "$IMAGE" \
      | sudo dd of="$SD_DEVICE" bs=16M conv=fsync status=progress; then
    sync && sudo udevadm settle
  else
    printf '%s\n' 'STOP: Writing failed. Do not use the card; check the error.' >&2
    false
  fi
else
  printf '%s\n' 'STOP: Successfully verify the selected archive in step 2 first.' >&2
  false
fi
```

**Success:** writing completes without errors. For any error, stop and use
[troubleshooting](TROUBLESHOOTING.en.md). This writes the whole target card,
including boot area and partition table. T95 eMMC is not accessed.

### 4. Check layout and use the card

**On the Linux PC, normal user with `sudo`:**

```bash
sudo partprobe "$SD_DEVICE"
sudo udevadm settle
lsblk -b -o NAME,SIZE,FSTYPE,LABEL,PARTUUID,MOUNTPOINTS "$SD_DEVICE"
```

Confirm the actual layout and that the partition is unmounted. This release
has one ext4 partition, `${SD_DEVICE}1`.

**On the Linux PC, normal user with `sudo`:**

```bash
sudo e2fsck -fn "${SD_DEVICE}1"
```

This checks layout and filesystem; it is not a full byte-for-byte comparison.
Unmount any auto-mounted partitions, remove the card safely, and insert it only
while the T95 is off. Check DHCP and SSH using
[installation](INSTALLATION.en.md#3-boot-the-box-and-find-its-network-address).
UART is an additional diagnostic option for boot problems.

## Recovery boundaries

- The backup restores one point in time; separately back up changing data regularly.
- A smaller or defective replacement card cannot hold the image.
- Backups contain personal accounts and configuration. For sharing, use the
  public release and let each user personalize it locally.
- This procedure never reads or writes Android eMMC.

[Daily use](DAILY_USE.en.md) · [Release details](RELEASE.en.md)
