#!/bin/bash

# Warning: This file expects to be run from the root level directory
# Generates .patch files for fusion_gps_ins <=> fusion_gps_vel_ins and
# SimpleGpsOrchestrationPlugin <=> SimpleGpsVelOrchestrationPlugin
orch_path="pntos-cobra/src/pntos/cobra/orchestration_plugins/"

git diff --no-index apps/fusion_gps_ins.py apps/fusion_gps_vel_ins.py > util/app_gps_vel.patch
git diff --no-index $orch_path"SimpleGpsOrchestrationPlugin.py" $orch_path"SimpleGpsVelOrchestrationPlugin.py" > util/orch_gps_vel.patch
