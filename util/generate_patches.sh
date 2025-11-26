#!/usr/bin/env bash

# Warning: This file expects to be run from the root level directory
# Generates .patch files for apps and tutorial orchestration plugins
orch_path="pntos-cobra/src/pntos/cobra/tutorial_plugins/"

git diff --no-index apps/tutorial/gps_ins.py apps/tutorial/gps_vel_ins.py > util/app_gps_vel.patch
git diff --no-index apps/tutorial/gps_ins.py apps/standard/gps_ins.py > util/app_gps_standard.patch
git diff --no-index apps/standard/gps_ins.py apps/standard/lcm_relay.py > util/app_lcm_relay.patch
git diff --no-index apps/standard/gps_ins.py apps/standard/gps_ins_leverarm.py > util/app_gps_ins_leverarm.patch
git diff --no-index apps/standard/gps_ins.py apps/standard/gps_ins_bodyvel.py > util/app_gps_ins_bodyvel.patch
git diff --no-index apps/standard/gps_ins.py apps/advanced/gps_ins_ros.py > util/app_gps_ros.patch
git diff --no-index $orch_path"TutorialGpsOrchestrationPlugin.py" $orch_path"TutorialGpsVelOrchestrationPlugin.py" > util/orch_gps_vel.patch
git diff --no-index apps/standard/gps_ins.py apps/standard/gps_vel_ins.py > util/app_gps_vel_standard.patch
git diff --no-index apps/standard/gps_vel_ins.py apps/standard/posvel_ins.py > util/app_posvel_standard.patch
git diff --no-index apps/standard/gps_ins.py apps/standard/gps_ins_baro.py > util/app_gps_ins_baro.patch
git diff --no-index apps/standard/gps_ins.py apps/standard/gps_ins_vsb.py > util/app_gps_ins_vsb.patch
