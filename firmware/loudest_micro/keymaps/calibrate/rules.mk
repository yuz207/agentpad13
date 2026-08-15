# Bring-up calibration keymap. Same plain-QMK build as keymaps/default (no VIA,
# no Vial, no LTO) with ONE deliberate difference:
#
#   ENCODER_MAP_ENABLE is NOT set here, and that is load-bearing.
#
# keymaps/default/rules.mk sets ENCODER_MAP_ENABLE = yes, which routes encoder
# detents through action_exec() and the per-layer encoder_map[] instead of the
# encoder_update_kb()/encoder_update_user() callbacks (vial-qmk
# quantum/encoder.c:35-52). This keymap needs the callback, because it reports
# each detent as a typed "ENC:CW" / "ENC:CCW" line rather than emitting a
# keycode. With the map enabled, encoder_update_user() would never be called and
# the encoder half of the bring-up check would silently do nothing.
#
# Everything else - RGB matrix, joystick, raw HID, the shared keyboard-level
# code in loudest_micro.c - comes from keyboard.json and is identical to the
# default build. SEND_STRING_ENABLE defaults to yes
# (builddefs/generic_features.mk:18), which is what types the report.
