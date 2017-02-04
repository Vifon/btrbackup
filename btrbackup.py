#!/usr/bin/env python3

import argparse
import glob
import logging
import subprocess
import time
import yaml

class CannotSend(Exception): pass

def mount_targets(targets):
    """Mount the target devices."""
    run_target_scripts(
        targets,
        message="Mounting %s...",
        config_key='mount_script')

def umount_targets(targets):
    """Unmount the target devices."""
    run_target_scripts(
        targets,
        message="Unmounting %s...",
        config_key='umount_script')

def run_target_scripts(targets, message, config_key):
    """Run a script stored in the config on each target."""
    for name, target in targets.items():
        logging.getLogger('btrbackup').info(message, name)
        command = target[config_key]
        if 'sudo' in target:
            command = ["sudo", "-u", target['sudo']] + [command]
        subprocess.check_call(" ".join(command), shell=True)

def backup_subvols(subvols, targets, timestamp):
    """Create the new snapshots and send them to targets."""
    subvols_with_snapshots = prepare_snapshots(subvols, timestamp)
    create_snapshots(subvols_with_snapshots)
    send_snapshots(subvols_with_snapshots, targets)

# Note: `subvols' is being mutated. Do not use afterwards.
def prepare_snapshots(subvols, timestamp):
    """Add the old and new snapshot paths to the subvolume dict read from
    config.

    """
    return list(
        filter(
            None,
            map(
                lambda subvol:
                    prepare_snapshot(subvol, timestamp),
                subvols)))

# Note: `subvol' is being mutated. Do not use afterwards.
def prepare_snapshot(subvol, timestamp):
    """Get the last snapshot path and generate the name of the new
    snapshot. Add them to the subvolume dict read from the config.

    """
    snapshots = sorted(glob.iglob(glob.escape(subvol['snapshots']) + "*"))
    new_snapshot = subvol['snapshots'] + timestamp
    if len(snapshots) < 1:
        subvol['old_snapshot'] = None
        subvol['new_snapshot'] = new_snapshot
        return subvol

    if len(snapshots) > 1:
        logging.getLogger('btrbackup').warning("Ambiguous old snapshot list for %s:", subvol['mount'])
        for old_snapshot in snapshots:
            logging.getLogger('btrbackup').warning(" - %s", old_snapshot)

    old_snapshot = snapshots.pop()
    subvol['old_snapshot'] = old_snapshot
    subvol['new_snapshot'] = new_snapshot
    return subvol

def create_snapshots(subvols):
    """Create a snapshot for each subvolume."""
    for subvol in subvols:
        create_snapshot(subvol)

def create_snapshot(subvol):
    """Create a new read-only snapshot."""
    subprocess.check_call(
        ["btrfs", "subvolume", "snapshot", "-r",
         subvol['mount'],
         subvol['new_snapshot']])

def send_snapshots(subvols, targets):
    """Send each taken snapshot to appropriate targets."""
    for subvol in subvols:
        send_snapshot(subvol, targets)

def send_snapshot(subvol, targets):
    """Send the snapshot the specified targets"""
    for target_key in subvol['targets']:
        logging.getLogger('btrbackup').info("Sending %s to %s...", subvol['mount'], target_key)
        if subvol['old_snapshot']:
            send_cmd = ["btrfs", "send", "-p",
                        subvol['old_snapshot'],
                        subvol['new_snapshot']]
        else:
            send_cmd = ["btrfs", "send", subvol['new_snapshot']]
        recv_cmd = ["btrfs", "receive",
                    targets[target_key]['path']]
        logging.getLogger('btrbackup').debug("Send cmd: %s", send_cmd)
        logging.getLogger('btrbackup').debug("Recv cmd: %s", recv_cmd)
        send = subprocess.Popen(send_cmd, stdout=subprocess.PIPE)
        recv = subprocess.Popen(recv_cmd, stdin=send.stdout)
        if recv.wait() != 0:
            logging.getLogger('btrbackup').error(
                "Failed to send %s to %s. Aborting...",
                subvol['mount'],
                target_key)
            raise CannotSend

def main(argv=None):
    logging.basicConfig(level=logging.INFO)

    timestamp = time.strftime("%F_%s")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'config',
        type=argparse.FileType('r'),
        help="Path to the configuration file. Default: ./btrbackup.yml",
        default="btrbackup.yml",
        nargs='?')
    args = parser.parse_args()

    config = yaml.load(args.config)
    args.config.close()

    mount_targets(config['targets'])
    try:
        backup_subvols(config['subvols'], config['targets'], timestamp)
    finally:
        umount_targets(config['targets'])

if __name__ == '__main__':
    from sys import argv
    main(argv)
