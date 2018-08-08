#!/bin/bash

###outputs all the Rally projects and IDs
echo -e '\n##################################################################\n'
echo 'Rally IDs and Projects:'
tput setaf 2; mysql keystone -e "select id,name from project where name like 'rally%'"; tput sgr0
echo -e '\n##################################################################\n'

###checks for instances by rally, whether in-progress or stuck
echo '...Checking for INSTANCES spawned by Rally...'
tput setaf 1
mysql --table <<EOF
SELECT uuid,
       display_name,
       vm_state,
       task_state,
       host,
       launched_at,
       project_id
FROM   nova.instances
WHERE  project_id IN (SELECT id
                      FROM   keystone.project
                      WHERE  NAME LIKE 'rally%')
       AND deleted = 0;
EOF
tput sgr0
echo -e '\n##################################################################\n'

###checks for images by rally, whether in-progress or stuck
echo '...Checking for IMAGES created by Rally...'
tput setaf 1
mysql --table <<EOF
SELECT id,
       NAME,
       status,
       created_at,
       owner
FROM   glance.images
WHERE  owner IN (SELECT id
                 FROM   keystone.project
                 WHERE  NAME LIKE 'rally%')
       AND deleted = 0;
EOF
tput sgr0
echo -e '\n##################################################################\n'

###checks for volumes created by rally
echo '...Checking for VOLUMES created by Rally...'
tput setaf 1
mysql --table <<EOF
SELECT id,
       display_name,
       host,
       status,
       attach_status,
       created_at,
       project_id
FROM   cinder.volumes
WHERE  project_id IN (SELECT id
                      FROM   keystone.project
                      WHERE  NAME LIKE 'rally%')
       AND deleted = 0;
EOF
tput sgr0
echo -e '\n##################################################################\n'

###checks for neutron ports
echo '...Checking for PORTS created by Rally...'
tput setaf 1
mysql --table <<EOF
SELECT ports.id,
       ports.name,
       ports.status,
       ports.device_owner,
       standardattributes.created_at,
       standardattributes.updated_at,
       standardattributes.description
FROM   neutron.ports
       LEFT JOIN neutron.standardattributes
              ON ports.standard_attr_id = standardattributes.id
WHERE  ports.project_id IN (SELECT id
                            FROM   keystone.project
                            WHERE  name LIKE 'rally%')
       AND ports.device_owner != 'network:dhcp'
       AND standardattributes.updated_at < NOW() - interval 5 minute;
EOF
tput sgr0
echo -e '\n##################################################################\n'

###checks for neutron secgroups
echo '...Checking for SECURITY GROUPS created by Rally...'
tput setaf 1
mysql --table <<EOF
SELECT id,
       NAME,
       project_id
FROM   neutron.securitygroups
WHERE  project_id IN (SELECT id
                      FROM   keystone.project
                      WHERE  NAME LIKE 'rally%')
       AND NAME LIKE '%rally%';
EOF
tput sgr0
echo -e '\n##################################################################\n'

###checks for swift containers
echo '...Checking for SWIFT CONTAINERS created by Rally...'
tput setaf 1
PROJECT=`mysql keystone -BNe "select id from project where name='rally_swift'"`
source openrc
swift list --lh --os-project-id $PROJECT
tput sgr0
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
