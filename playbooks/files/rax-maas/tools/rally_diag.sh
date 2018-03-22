#!/bin/bash

###outputs all the Rally projects and IDs
echo -e '\n##################################################################\n'
echo 'Rally IDs and Projects:'
tput setaf 2; mysql keystone -e "select id,name from project where name like 'rally%'"; tput sgr0
echo -e '\n##################################################################\n'

###checks for instances by rally, whether in-progress or stuck
echo '...Checking for INSTANCES spawned by Rally...'
tput setaf 1; for PROJECT in `mysql keystone -BNe "select id from project where name like 'rally%'"`; do mysql nova -e "select uuid,display_name,vm_state,task_state,host,launched_at,project_id from instances where project_id='$PROJECT' and deleted=0" ; done; tput sgr0
echo -e '\n##################################################################\n'

###checks for images by rally, whether in-progress or stuck
echo '...Checking for IMAGES created by Rally...'
tput setaf 1; for PROJECT in `mysql keystone -BNe "select id from project where name like 'rally%'"`; do mysql glance -e "select id,name,status,created_at,owner from images where owner='$PROJECT' and deleted=0"; done; tput sgr0
echo -e '\n##################################################################\n'

###checks for volumes created by rally
echo '...Checking for VOLUMES created by Rally...'
tput setaf 1; for PROJECT in `mysql keystone -BNe "select id from project where name like 'rally%'"`; do mysql cinder -e "select id,display_name,host,status,attach_status,created_at,project_id from volumes where project_id='$PROJECT' and deleted=0"; done; tput sgr0
echo -e '\n##################################################################\n'

###checks for neutron ports
echo '...Checking for PORTS created by Rally...'
tput setaf 1; for PROJECT in `mysql keystone -BNe "select id from project where name like 'rally%'"`; do mysql neutron -e "select id,name,status,device_owner from ports where device_owner='$PROJECT'"; done; tput sgr0
echo -e '\n##################################################################\n'

###checks for neutron secgroups
echo '...Checking for SECURITY GROUPS created by Rally...'
tput setaf 1; for PROJECT in `mysql keystone -BNe "select id from project where name like 'rally%'"`; do mysql neutron -e "select id,name,project_id from securitygroups where project_id='$PROJECT' and name like '%rally%'"; done; tput sgr0
echo -e '\n##################################################################\n'

###checks for swift containers
echo '...Checking for SWIFT CONTAINERS created by Rally...'
tput setaf 1; PROJECT=`mysql keystone -BNe "select id from project where name='rally_swift'"`; source openrc; swift list --lh --os-project-id $PROJECT; tput sgr0
echo -e '\n################################################################################'

###echos an explanation
echo '###     If there is RED output and the "created_at" date is >5 min old,      ###'
echo '###       Rally operation may have failed and requires investigation.        ###'
echo '###         Once investigation is complete, clean-up the scenario,           ###'
echo '###              replacing <scenario_name> with project name:                ###'
echo '###              "rm -rf /var/lock/maas_rally/<scenario_name>"               ###'
echo '###                                                                          ###'
echo '###                           !!EXCEPTIONS!!                                 ###'
echo '###        Security Groups dont have dates; delete if no instances           ###'
echo '###                           !!EXCEPTIONS!!                                 ###'
echo '################################################################################'
