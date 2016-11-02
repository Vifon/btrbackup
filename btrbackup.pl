#!/usr/bin/env perl

use warnings;
use strict;
use 5.014;

use autodie;
use Carp;

use File::Glob qw(bsd_glob);
use File::Spec::Functions;
use Sys::Hostname;
use YAML::XS qw(LoadFile);


my $config = LoadFile('btrbackup.yml');

sub run {
    my $program = shift;
    my @arguments = @_;
    system($program, @arguments) == 0 or confess;
}

my $timestamp = `date +%y.%m.%d_%s`;
chomp $timestamp;

for my $disk (@{$config->{disks}}) {
    say "Mounting $disk->{uuid}...";
    run("sudo -u $disk->{mount_user} $disk->{mount_script}");

    my $backup_dir = catfile("$disk->{backup_dir}", hostname);

    for my $subvol (@{$disk->{subvols}}) {
        my $subvol_abs_prefix = catfile($disk->{snapshot_dir}, $subvol->{prefix});

        my @old_snapshots = bsd_glob("$subvol_abs_prefix*") or die "ERROR: No old snapshot!";
        my $last_snapshot = $old_snapshots[$#old_snapshots];

        my $new_snapshot = $subvol_abs_prefix . $timestamp;
        say "Creating a new snapshot of '$subvol->{mount}' at '$new_snapshot'...";
        run("btrfs", "subvolume", "snapshot", "-r",
            $subvol->{mount}, $new_snapshot);
        run("sync");

        say "Sending '$new_snapshot' to '$backup_dir'...";
        run("btrfs send -p '$last_snapshot' '$new_snapshot' | btrfs receive '$backup_dir'");

        say "Removing the old snapshot: '$last_snapshot'...";
        run("btrfs", "subvolume", "delete", $last_snapshot);
    }

    say "Unmounting $disk->{uuid}...";
    run("sudo -u $disk->{mount_user} $disk->{umount_script}");
}
