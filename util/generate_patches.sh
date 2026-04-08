#!/usr/bin/env bash

# Warning: This file expects to be run from the root level directory
# Generates .patch files for apps and tutorial orchestration plugins
tutorial_plugins_folder="pntos-cobra/src/pntos/cobra/tutorial_plugins/"
standard_plugins_folder="pntos-cobra/src/pntos/cobra/standard_plugins/"
advanced_plugins_folder="pntos-cobra/src/pntos/cobra/advanced_plugins/"

git diff --no-index apps/tutorial/pos_ins.py apps/tutorial/pos_vel_ins.py > util/app_pos_vel.patch
git diff --no-index apps/tutorial/pos_ins.py apps/standard/pos_ins.py > util/app_pos_standard.patch
git diff --no-index apps/standard/pos_ins.py apps/standard/lcm_relay.py > util/app_lcm_relay.patch
git diff --no-index apps/standard/pos_ins.py apps/standard/pos_ins_leverarm.py > util/app_pos_ins_leverarm.patch
git diff --no-index apps/standard/pos_ins.py apps/standard/pos_ins_bodyvel.py > util/app_pos_ins_bodyvel.patch
git diff --no-index apps/standard/pos_ins.py apps/advanced/pos_ins_ros.py > util/app_pos_ros.patch
git diff --no-index $tutorial_plugins_folder"TutorialPosOrchestrationPlugin.py" $tutorial_plugins_folder"TutorialPosVelOrchestrationPlugin.py" > util/orch_pos_vel.patch
git diff --no-index apps/standard/pos_ins.py apps/standard/pos_vel_ins.py > util/app_pos_vel_standard.patch
git diff --no-index apps/standard/pos_vel_ins.py apps/standard/posvel_ins.py > util/app_posvel_standard.patch
git diff --no-index apps/standard/pos_ins.py apps/standard/outage_sim.py > util/app_outage_sim.patch
git diff --no-index apps/standard/pos_ins.py apps/standard/pos_ins_vsb.py > util/app_pos_ins_vsb.patch
git diff --no-index $standard_plugins_folder/controller/StandardControllerPlugin.py $advanced_plugins_folder/buscat/BuscatControllerPlugin.py > util/controller_buscat.patch
git diff --no-index apps/standard/pos_ins.py apps/standard/direction_to_points.py > util/app_direction_to_points.patch
