#!/usr/bin/bash

function clean_obs_tmp_projects()
{
    prjs=$(osc -A tizen ls |grep home:xiaoqiang:gbs:itest-)
    local i=1
    for prj in $prjs
    do
        echo "#$i: delete $prj"
        osc -A tizen rdelete -rf -m "delete tmp project" $prj &
        let i++
    done
}
trap "echo Exit; exit 1" INT TERM
clean_obs_tmp_projects
wait
echo Done
