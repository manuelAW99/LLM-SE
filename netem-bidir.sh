#!/bin/bash

DEV="wlp2s0"  
IFB="ifb0"

setup_ifb() {
  modprobe ifb 2>/dev/null
  ip link add $IFB type ifb 2>/dev/null
  ip link set $IFB up

  tc qdisc add dev $DEV ingress 2>/dev/null
  tc filter add dev $DEV parent ffff: protocol ip u32 \
    match u32 0 0 action mirred egress redirect dev $IFB 2>/dev/null
}

clear_tc() {
  tc qdisc del dev $DEV root 2>/dev/null
  tc qdisc del dev $DEV ingress 2>/dev/null
  tc qdisc del dev $IFB root 2>/dev/null
}

good() {
  clear_tc
  setup_ifb

#  tc qdisc add dev $DEV root netem delay 20ms loss 0.1%
#  tc qdisc add dev $IFB root netem delay 20ms loss 0.1%

  echo "🟢 GOOD signal"
}

medium() {
  clear_tc
  setup_ifb

  tc qdisc add dev $DEV root netem \
    delay 80ms 20ms distribution normal loss 10% 30%

  tc qdisc add dev $IFB root netem \
    delay 80ms 20ms distribution normal loss 20% 30%

  echo "🟡 MEDIUM signal"
}

bad() {
  clear_tc
  setup_ifb

  tc qdisc add dev $DEV root netem \
    delay 150ms 40ms distribution normal loss 15% 30%

  tc qdisc add dev $IFB root netem \
    delay 150ms 40ms distribution normal loss 40% 30%

  echo "🔴 BAD signal"
}

off() {
  clear_tc
  ip link del $IFB 2>/dev/null
  echo "⚪ NETEM OFF"
}

case "$1" in
  good) good ;;
  medium) medium ;;
  bad) bad ;;
  off) off ;;
  *)
    echo "Usage: $0 {good|medium|bad|off}"
    exit 1
    ;;
esac

