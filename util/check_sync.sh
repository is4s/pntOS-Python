#!/usr/bin/env bash

set +xe
# Warning: This file expects to be run from the root level directory
# This script will determine if there are any conflicts when applying the patches
# and inform you if there is a desync issue
TEMP_DIR=$(mktemp -d)
DIFF_FILE=$(mktemp)
ret_val=0
cleanup() {
    rm "$DIFF_FILE" #2> /dev/null
    git worktree remove --force "$TEMP_DIR" #2>/dev/null || true
}

### Setup Test Environment
# Grab current changes
git diff > "$DIFF_FILE"
git diff --cached >> "$DIFF_FILE"

# Make worktree
git worktree add -d --quiet "$TEMP_DIR"

# Move to work tree
orig_dir=($PWD)
pushd "$TEMP_DIR" > /dev/null

# Apply patch if one exists
if [ -s $DIFF_FILE ]; then
    git apply "$DIFF_FILE"
    git add -u .
    git commit -m "trash commit"
fi

check_diff() {
    # Check diff
    git diff --exit-code --diff-filter=M
    if [ $? -ne 0 ]; then
        echo "Patch $1 did not account for all differences!"
        ret_val=1
    fi
    # Reset test environment
    git restore .
}

### Synchronization Check
check_sync() {
    local patch_file=$1
    # Test patch
    echo "Testing $patch_file"
    git apply "$patch_file"
    if [ $? -ne 0 ]; then
        echo "Patch $patch_file could not be applied cleanly. Please update the patch!"
        ret_val=1
    fi

    check_diff $patch_file

    # Test patch in reverse
    git apply --reverse "$patch_file"
    if [ $? -ne 0 ]; then
        echo "Patch $patch_file could not be applied cleanly in reverse. Please update the patch!"
        ret_val=1
    fi

    check_diff $patch_file
}

# Apply orchestration gps-velocity patch
check_sync $orig_dir"/util/orch_gps_vel.patch"
# Check sync between buscat controller plugin and standard controller plugin
check_sync $orig_dir"/util/controller_buscat.patch"
# Apply app gps-velocity patch
check_sync $orig_dir"/util/app_gps_vel.patch"
# Apply app add ROS patch
check_sync $orig_dir"/util/app_gps_ros.patch"
# Apply app gps-standard patch
check_sync $orig_dir"/util/app_gps_standard.patch"
# Apply app lcm-relay patch
check_sync $orig_dir"/util/app_lcm_relay.patch"
# Apply app lever_arm patch
check_sync $orig_dir"/util/app_gps_ins_leverarm.patch"
# Apply app bodyvel patch
check_sync $orig_dir"/util/app_gps_ins_bodyvel.patch"
# Apply app vsb patch
check_sync $orig_dir"/util/app_gps_ins_vsb.patch"
# Apply app outage patch
check_sync $orig_dir"/util/app_outage_sim.patch"

# Cleanup and return
popd > /dev/null
cleanup
# reverse `set +xe` call made at beginning of script
set -xe
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    return $ret_val
else
    exit $ret_val
fi
