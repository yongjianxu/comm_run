#!/bin/bash
# cmd to get port lid
# ibv_devinfo  | grep port_lid


get_ib_perf() {
    local lids=("$@")  # Get all LIDs as an array

    # Get initial values for all metrics for all LIDs
    declare -A before_rcv before_xmit before_wait
    for lid in "${lids[@]}"; do
        before_data=$(perfquery -x $lid 1 | grep -E "PortRcvData|PortXmitData|PortXmitWait" | awk '{match($0, /[0-9]+/); print substr($0, RSTART, RLENGTH)}')
        before_xmit[$lid]=$(echo "$before_data" | head -n1)
        before_rcv[$lid]=$(echo "$before_data" | head -n2 | tail -n1)
        before_wait[$lid]=$(echo "$before_data" | tail -n1)
    done

    sleep 2

    # Get final values for all metrics for all LIDs
    declare -A after_rcv after_xmit after_wait
    for lid in "${lids[@]}"; do
        after_data=$(perfquery -x $lid 1 | grep -E "PortRcvData|PortXmitData|PortXmitWait" | awk '{match($0, /[0-9]+/); print substr($0, RSTART, RLENGTH)}')
        after_xmit[$lid]=$(echo "$after_data" | head -n1)
        after_rcv[$lid]=$(echo "$after_data" | head -n2 | tail -n1)
        after_wait[$lid]=$(echo "$after_data" | tail -n1)
    done

    # Calculate and display results for each LID
    for lid in "${lids[@]}"; do
        echo "LID $lid:"

        # Calculate and display Rx BW
        v=$((after_rcv[$lid]-before_rcv[$lid]))
        echo "  Rx BW: $((v*32/2000000000))"

        # Calculate and display Tx BW
        v=$((after_xmit[$lid]-before_xmit[$lid]))
        echo "  Tx BW: $((v*32/2000000000))"

        # Calculate and display Tx Wait
        v=$((after_wait[$lid]-before_wait[$lid]))
        echo "  Tx Wait:"
        congested=$((v*32/2000000000))
        echo "  congested bw: ${congested}"
        echo "---"
    done
}
# 149 is the lid.
get_ib_perf 148 114 90 48 208 177 265 227
