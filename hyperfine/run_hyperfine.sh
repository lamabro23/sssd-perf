#!/bin/bash

check_opt() {
    if ! [[ $1 =~ $2 ]]; then
        echo "Invalid argument '$1', for option '-$3'!" >&2
        echo "$4"
        exit 1
    fi
}

while getopts "r:p:o:s:" opt; do
    case "${opt}" in
        r)
            check_opt $OPTARG "^[2-9][0-9]*$" "$opt" "The number of runs has to be at least 2"
            runs="$OPTARG";;
        p)
            check_opt $OPTARG "^.*@.*\..*" "$opt" "The correct format of parameter is '^.*@.*\..*'"
            params+="$OPTARG,";;
        o)
            check_opt $OPTARG "^.*\.json$" "$opt" "The output should be a json file"
            output="$OPTARG";;
        s)
            check_opt $OPTARG "^(/[a-zA-Z]+)*/?sss_cache" "$opt" "This does not point to a valid sss_cache binary"
            sss_cache="$OPTARG -E";;
        \?)
            exit 1;;
    esac
done

cmd="sudo hyperfine -i"

build_cmd() {
    if ! [ -z "$1" ]; then
        $1+=$2
    fi
}

if ! [ -z "$runs" ]; then
    cmd+=" -r $runs"
fi

if ! [ -z "$sss_cache" ]; then
    cmd+=" --prepare '$sss_cache'"
fi

if ! [ -z "$params" ]; then
    cmd+=" --parameter-list user ${params::-1}"
else
    echo "The '-p' parameter is required" >&2; exit 1
fi

if ! [ -z "$output" ]; then
    if ! [ -d "json" ]; then
        mkdir json
    fi
    cmd+=" --export-json json/$output"
fi

cmd+=" 'id {user}'"

eval $cmd
