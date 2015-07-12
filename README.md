btrbackup
=========

`btrbackup` is a simple script for performing regular backups using
the btrfs snapshots and then incrementally sending them to an external
drive.

`btrbackup` needs some setup before it is ready to work. You will need
to set the variables on top of the script to tell `btrbackup` various
things, for example where your local snapshot directory and the
external backup directory are.

- `DISK_UUID` is an UUID of a disk **on which you want your backups
  stored**
- `SNAPSHOT_DIR` is a directory **on a local disk** where you want
  your local temporary snapshots stored. `btrbackup` only keeps the
  last one of these.
- `BACKUP_DIR` is a directory **on an external disk** to which you
  want your snapshots sent.
- `MOUNT_SCRIPT` and `UMOUNT_SCRIPT` are paths to the scripts which
  are used to mount and umount the external backup disk.
- `MOUNT_USER` is the name of a user used to run the mount/umount
  scripts.

You will need to make the first snapshots manually as `btrbackup` only
does the incremental ones. The naming convention used is `@-$(date
+%s_%y.%m.%d)` and `@home-$(date +%s_%y.%m.%d)`. `btrbackup` assumes
you have no other snapshots which names start with these prefixes
(`@-` and `@home-` respectively).

What `btrbackup` does:

1. Create new local snapshots.
2. Mount the external drive.
3. Send the local snapshots incrementally to the external drive.
4. Remove the old local snapshots.
5. Unmount the external drive.

COPYRIGHT
---------

Copyright (C) 2015  Wojciech Siewierski

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
