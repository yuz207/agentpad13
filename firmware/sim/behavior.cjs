// agentpad13 — behavioral simulation of the shipped UF2 on rp2040js.
//
// This is the *behavior* layer that sits above firmware/tests/emulator/runner.cjs
// (which proves boot, pin muxing, USB enumeration, one key, and raw-HID PING).
// Here we answer the owner's four pre-hardware questions:
//
//   Q1 "do presses register"        -> every one of the 13 switches is driven
//                                      low in turn and the resulting USB report
//                                      is checked against the default keymap.
//   Q2 "do LEDs trigger"            -> the ws2812 DMA source buffer is located
//                                      at runtime and read back per frame.
//   Q3 "are they individually
//       addressable"                -> all 24 chain positions are painted with
//                                      a unique color over raw HID SET_KEY and
//                                      read back byte-exact, one at a time.
//   Q4 "does the firmware work"     -> encoder, capacitive touch -> layer move,
//                                      layer-indicator hue, and the analog
//                                      joystick -> HID gamepad path.
//
// HOW THE LED READBACK WORKS (and why it is trustworthy):
//   QMK's RP2040 "vendor" ws2812 driver hands the pixel array to a DMA channel
//   that feeds PIO0's TX FIFO (PIO0_BASE+TXF0 = 0x50200010). We do not hardcode
//   the buffer address: we watch every DMA channel start, and the lowest read
//   address of whichever channel targets TXF0 *is* the pixel buffer. Each entry
//   is one uint32 holding GRB in bits 31:8 (the SM runs autopull with
//   PULL_THRESH=24, MSB first), which we assert structurally (low byte == 0).
//   So we are reading the exact words the PIO shifts onto GP17 — one hop short
//   of the wire.
//
// WHAT THIS CANNOT DO — read firmware/sim/README.md before trusting a PASS.
// In particular WS2812 bit timing, ADC electrical behavior, and the joystick's
// axis IDENTITY are NOT validated here; the emulator is not cycle-faithful and
// rp2040js has a confirmed ADC channel-select masking bug (README §"Untrusted").
//
// Usage:  node behavior.cjs [../prebuilt/agentpad13_reference.uf2]
'use strict';

const fs = require('fs');
const path = require('path');

// Reuse the already-vendored emulator + bootrom from tests/emulator (no new
// install, no network). See README.md for the one-time setup there.
const EMU = path.resolve(__dirname, '../tests/emulator');
let R, bootromB1;
try {
  R = require(path.join(EMU, 'node_modules/rp2040js'));
  ({ bootromB1 } = require(path.join(EMU, 'bootrom.cjs')));
} catch (e) {
  console.error('SETUP INCOMPLETE: ' + e.message);
  console.error('Run this first:  cd firmware/tests/emulator && ./get-bootrom.sh && npm install');
  process.exit(2);
}
const {
  Simulator, ConsoleLogger, LogLevel, DescriptorType,
  getDescriptorPacket, setDeviceAddressPacket, setDeviceConfigurationPacket,
} = R;

const args = process.argv.slice(2);
const UF2_PATH = path.resolve(__dirname, args.find((a) => !a.startsWith('--')) ?? '../prebuilt/agentpad13_reference.uf2');
const PIO0_TXF0 = 0x50200010;
const LED_COUNT = 24;

// --- TOUCH POLARITY MODEL -------------------------------------------------
// This is the single most important knob in this harness. The default models
// the board and must pass; the counterfactual recreates the pre-fix assumption
// and must fail only the touch checks.
//
//   'board'    (DEFAULT — what the v5 PCB actually does)
//              R10 (0R) ties TOUCH_AHLB -> GND. On a TTP223,
//              AHLB low selects ACTIVE-HIGH output: Q idles LOW and drives HIGH
//              while touched. So GP16 rests LOW.
//
//   'firmware' (legacy flag name — the old, wrong firmware assumption)
//              "idle high, touched low" — GP16 rests HIGH. Current firmware
//              does not make this assumption; this is the negative-control arm.
//
// GP16 is intentionally outside QMK's direct matrix and is polled active-high
// by loudest_micro.c, so 'board' passes and 'firmware' fails four checks.
const TOUCH_MODEL = (args.find((a) => a.startsWith('--touch=')) ?? '--touch=board').split('=')[1];
if (!['board', 'firmware'].includes(TOUCH_MODEL)) {
  console.error(`unknown --touch=${TOUCH_MODEL} (expected 'board' or 'firmware')`);
  process.exit(2);
}
const TOUCH_IDLE_LEVEL = TOUCH_MODEL === 'board' ? false : true; // false = LOW
const touchDown = () => mcu.gpio[16].setInputValue(!TOUCH_IDLE_LEVEL);
const touchUp = () => mcu.gpio[16].setInputValue(TOUCH_IDLE_LEVEL);

// --- ENCODER DIRECTION MODEL ----------------------------------------------
// Second A/B, identical in shape and purpose to --touch above, added
// 2026-08-15. A quadrature walk on GP13/GP14 has no intrinsic handedness: which
// walk is a PHYSICALLY CLOCKWISE detent depends on which EC11 terminal landed on
// ENC_A and which on ENC_B — a board fact, exactly like the AHLB strap. This
// harness used to hard-code one answer (the seq[] order below == clockwise),
// which was an assumption about the v5 board, not a measurement of it.
//
//   'board'    (DEFAULT — measured on fabricated v5_6; unchanged in v5_8)
//              Measured on the owner's populated board, 2026-08-15: turning the
//              knob clockwise on the PRE-FLIP firmware produced volume-DOWN. So
//              on this board a physically-clockwise detent is the REVERSED walk,
//              and the firmware now carries ENCODER_DIRECTION_FLIP
//              (config.h) so that CW is volume UP again.
//
//   'firmware' (the pre-flip assumption, and what this file asserted before
//              2026-08-15) — a physically-clockwise detent is the forward walk.
//              It describes no board that exists; it is the counterfactual arm.
//
// Both models assert the SAME behavior — CW must give KC_VOLU, CCW must give
// KC_VOLD. Only the GPIO walk that stands for "clockwise" changes, which is the
// one thing the board decides. Nothing about the keymap is relaxed.
const ENCODER_MODEL = (args.find((a) => a.startsWith('--encoder=')) ?? '--encoder=board').split('=')[1];
if (!['board', 'firmware'].includes(ENCODER_MODEL)) {
  console.error(`unknown --encoder=${ENCODER_MODEL} (expected 'board' or 'firmware')`);
  process.exit(2);
}
// true = the seq[] order in rotate() is a clockwise detent on this board.
const ENCODER_CW_IS_FORWARD_WALK = ENCODER_MODEL === 'firmware';

// ---------------------------------------------------------------- verdicts
let failures = 0;
let checks = 0;
function verdict(name, cond, detail = '') {
  checks++;
  if (!cond) failures++;
  console.log(`  [${cond ? 'ok' : 'FAIL'}] ${name}${cond || !detail ? '' : '  <- ' + detail}`);
}
function note(msg) { console.log(`  ..   ${msg}`); }

// ---------------------------------------------------------------- boot
function loadUF2(file, rp2040) {
  const data = fs.readFileSync(file);
  let blocks = 0;
  for (let off = 0; off + 512 <= data.length; off += 512) {
    if (data.readUInt32LE(off) !== 0x0a324655 || data.readUInt32LE(off + 4) !== 0x9e5d5157) continue;
    const target = data.readUInt32LE(off + 12);
    const size = data.readUInt32LE(off + 16);
    rp2040.flash.set(data.subarray(off + 32, off + 32 + size), target - 0x10000000);
    blocks++;
  }
  return blocks;
}

const sim = new Simulator();
const mcu = sim.rp2040;
mcu.loadBootrom(bootromB1);
mcu.logger = new ConsoleLogger(LogLevel.Error);
console.log(`agentpad13 behavioral sim — ${path.basename(UF2_PATH)}`);
console.log(`loaded ${loadUF2(UF2_PATH, mcu)} UF2 blocks`);
console.log(TOUCH_MODEL === 'board'
  ? 'touch model: BOARD TRUTH — TTP223 AHLB->GND (R10) = active-high, GP16 idles LOW'
  : 'touch model: FIRMWARE ASSUMPTION — config.h:21 "idle high, touched low", GP16 idles HIGH');
console.log(ENCODER_MODEL === 'board'
  ? 'encoder model: BOARD TRUTH — v5_6 A/B landing measured 2026-08-15, CW = the reversed GP13/GP14 walk'
  : 'encoder model: PRE-FLIP ASSUMPTION — CW = the forward GP13/GP14 walk (no ENCODER_DIRECTION_FLIP)');
console.log('');

// --- rp2040js fidelity workarounds. Identical in intent to the four documented
// in tests/emulator/runner.cjs; all live here in the harness, never in firmware.
{ // (a) ADC FIFO_REG reads never re-evaluate the IRQ line -> interrupt storm.
  const adc = mcu.adc;
  const orig = adc.readUint32.bind(adc);
  adc.readUint32 = (o) => { const v = orig(o); if (o === 0x0c) adc.checkInterrupts(); return v; };
  adc.channelValues[0] = 2048; // GP26 / ADC0 — joystick X at rest (12-bit mid)
  adc.channelValues[1] = 2048; // GP27 / ADC1 — joystick Y at rest
}
{ // (b) DMA CHAN_ABORT reads are unimplemented -> ws2812 abort-poll spins.
  const dma = mcu.dma;
  const orig = dma.readUint32.bind(dma);
  dma.readUint32 = (o) => (o === 0x444 ? 0 : orig(o));
}
// (c) pull-ups are not folded into inputValue: drive every idle-high line high,
//     otherwise every key reads pressed (and bootmagic would jump to the ROM).
// GP0-GP15 are switches/encoder and genuinely idle high (switch to GND).
// GP16 is the TTP223 output — its idle level is the whole question, so it is
// set from the polarity model rather than assumed.
for (let p = 0; p <= 15; p++) mcu.gpio[p].setInputValue(true);
mcu.gpio[16].setInputValue(TOUCH_IDLE_LEVEL);

// --- locate the ws2812 pixel buffer by watching the DMA channel that feeds PIO0
let ledBase = null;
mcu.dma.channels.forEach((chan) => {
  const origStart = chan.start.bind(chan);
  chan.start = () => {
    if ((chan.writeAddr >>> 0) === PIO0_TXF0) {
      const a = chan.readAddr >>> 0;
      if (ledBase === null || a < ledBase) ledBase = a;
    }
    origStart();
    // (d) starting a channel whose DREQ is already asserted never schedules.
    if (chan.active && mcu.dma.dreq[chan.treq]) chan.scheduleTransfer();
  };
});
function readLeds() {
  const out = [];
  for (let i = 0; i < LED_COUNT; i++) {
    const w = mcu.readUint32(ledBase + i * 4) >>> 0;
    out.push({ g: (w >>> 24) & 0xff, r: (w >>> 16) & 0xff, b: (w >>> 8) & 0xff, lo: w & 0xff });
  }
  return out;
}
const rgb = (c) => `${c.r},${c.g},${c.b}`;

// ---------------------------------------------------------------- USB host shim
const usb = mcu.usbCtrl;
let descriptorsSize = null, configured = false, resetSeen = false, ep0Activity = 0;
let enumState = 'address';
const descriptors = [], interfaces = [], armedReads = new Map(), rawTxQueue = [];
const epLog = []; // every device->host report on a non-control endpoint

function parseConfig(desc) {
  interfaces.length = 0;
  let i = 0, cur = null;
  while (i + 2 <= desc.length && desc[i] >= 2) {
    const len = desc[i], type = desc[i + 1];
    if (type === DescriptorType.Interface && len === 9) {
      cur = { number: desc[i + 2], cls: desc[i + 5], proto: desc[i + 7], inEp: -1, outEp: -1 };
      interfaces.push(cur);
    } else if (type === DescriptorType.Endpoint && len === 7 && cur) {
      const a = desc[i + 2];
      if (a & 0x80) cur.inEp = a & 0x0f; else cur.outEp = a & 0x0f;
    }
    i += len;
  }
}
const ifaceKbd = () => interfaces.find((f) => f.cls === 3 && f.proto === 1);
const ifaceRaw = () => interfaces.find((f) => f.cls === 3 && f.proto === 0 && f.outEp >= 0);

usb.onUSBEnabled = () => usb.resetDevice();
usb.onResetReceived = () => { resetSeen = true; };
usb.onEndpointWrite = (ep, buf) => {
  if (ep === 0) {
    ep0Activity++;
    if (buf.length === 0) {
      if (enumState === 'address') { enumState = 'devdesc'; usb.sendSetupPacket(getDescriptorPacket(DescriptorType.Device, 18)); }
      else if (enumState === 'setconf') { enumState = 'done'; configured = true; parseConfig(descriptors); }
      return;
    }
    if (enumState === 'devdesc' && buf[1] === DescriptorType.Device) {
      enumState = 'confhdr'; usb.sendSetupPacket(getDescriptorPacket(DescriptorType.Configration, 9));
    } else if (enumState === 'confhdr' && buf.length === 9) {
      descriptorsSize = (buf[3] << 8) | buf[2];
      enumState = 'conffull'; usb.sendSetupPacket(getDescriptorPacket(DescriptorType.Configration, descriptorsSize));
    } else if (enumState === 'conffull') {
      descriptors.push(...buf); parseConfig(descriptors);
      // Emulator quirk: continuation packets of a multi-packet control IN never
      // arrive, so the 91-byte config descriptor truncates at 64. The keyboard
      // and raw interfaces are complete in that first packet; the third
      // (shared: NKRO/consumer/joystick) interface is not — we identify its
      // endpoint from observed traffic instead of from the descriptor.
      if (descriptors.length >= descriptorsSize || (ifaceKbd() && ifaceRaw())) {
        enumState = 'setconf'; usb.sendSetupPacket(setDeviceConfigurationPacket(1));
      }
    }
    return;
  }
  epLog.push({ t: sim.clock.micros, ep, hex: Buffer.from(buf).toString('hex'), bytes: Array.from(buf) });
};
usb.onEndpointRead = (ep, n) => {
  const raw = ifaceRaw();
  if (raw && ep === raw.outEp && rawTxQueue.length) usb.endpointReadDone(ep, rawTxQueue.shift());
  else armedReads.set(ep, n);
};
function sendRaw(frame) {
  const raw = ifaceRaw();
  if (raw && armedReads.has(raw.outEp)) { armedReads.delete(raw.outEp); usb.endpointReadDone(raw.outEp, frame); }
  else rawTxQueue.push(frame);
}
const cmd = (...bytes) => { const f = Buffer.alloc(32); bytes.forEach((b, i) => { f[i] = b; }); return f; };
const SET_KEY = (i, r, g, b, fx = 0) => cmd(0x01, i, r, g, b, fx);
const CLEAR = () => cmd(0x03);

// ---------------------------------------------------------------- clock
const CYCLE_NS = 1e9 / 125000000;
const WALL_BUDGET_MS = 30 * 60 * 1000;
const wallStart = Date.now();
let pioTick = 0;
function run(us) {
  const target = sim.clock.nanos + us * 1000;
  while (sim.clock.nanos < target) {
    if (Date.now() - wallStart > WALL_BUDGET_MS) throw new Error('wall-clock budget exceeded');
    if (mcu.core.waiting) sim.clock.tick(Math.min(sim.clock.nanosToNextAlarm, target - sim.clock.nanos));
    else sim.clock.tick(mcu.core.executeInstruction() * CYCLE_NS);
    // (e) RPPIO.run() re-schedules via setTimeout, which never fires inside a
    //     synchronous loop; step the PIO from here instead.
    if ((++pioTick & 3) === 0) {
      if (!mcu.pio[0].stopped) mcu.pio[0].step();
      if (!mcu.pio[1].stopped) mcu.pio[1].step();
    }
  }
}

// ================================================================ 0. boot
mcu.core.PC = 0x10000000; // start at boot2 in flash, as the rp2040js demos do
console.log('0. boot + USB enumeration');
let addressAttempts = 0, lastActivity = 0;
for (let i = 0; i < 80 && !configured; i++) {
  run(100000);
  if (resetSeen && enumState === 'address' && ep0Activity === 0 && addressAttempts < 5) {
    addressAttempts++; usb.sendSetupPacket(setDeviceAddressPacket(1));
  } else if (!configured && ep0Activity > 0 && ep0Activity === lastActivity && i % 5 === 4) {
    if (enumState === 'devdesc') usb.sendSetupPacket(getDescriptorPacket(DescriptorType.Device, 18));
    else if (enumState === 'confhdr') usb.sendSetupPacket(getDescriptorPacket(DescriptorType.Configration, 9));
    else if (enumState === 'conffull') { descriptors.length = 0; usb.sendSetupPacket(getDescriptorPacket(DescriptorType.Configration, descriptorsSize)); }
    else if (enumState === 'setconf') usb.sendSetupPacket(setDeviceConfigurationPacket(1));
  }
  lastActivity = ep0Activity;
}
verdict('USB configured', configured, `state=${enumState}`);
if (!configured) { console.log('\nBEHAVIOR SIM: FAIL (cannot proceed without USB)'); process.exit(1); }
note(`interfaces: ${interfaces.map((f) => `#${f.number} cls${f.cls}/proto${f.proto} in${f.inEp}${f.outEp >= 0 ? '/out' + f.outEp : ''}`).join('  ')}`);
for (const d of [0, 1, 2, 3, 8, 9, 10, 11]) mcu.dma.setDREQ(d);
run(300000);
verdict('ws2812 DMA source buffer located', ledBase !== null, 'no DMA channel ever targeted PIO0 TXF0');
if (ledBase === null) { console.log('\nBEHAVIOR SIM: FAIL'); process.exit(1); }
note(`pixel buffer @ 0x${ledBase.toString(16)} (${LED_COUNT} x uint32, GRB in bits 31:8)`);
{
  const l = readLeds();
  verdict('pixel words carry GRB<<8 (low byte always 0)', l.every((c) => c.lo === 0),
    l.map((c) => c.lo).join(','));
}
const KBD_EP = ifaceKbd().inEp;

// ============================================ 0b. what layer did we boot into?
// Nothing has touched raw HID yet, so loudest_status[] is all-zero and chain
// index 13 is showing the layer indicator: hsv(h = layer*32, s = 255, v).
// Layer 0 -> hue 0 -> pure red. Any other layer is NOT pure red.
// This is where a stuck [3,2] (the layer-cycle key) shows itself immediately.
const failBeforeTouch = failures; // sections 0b-0d are the touch-polarity-bearing ones
console.log('\n0b. boot layer — the layer indicator must say layer 0 (BASE)');
{
  const ind = readLeds()[13];
  const isLayer0 = ind.r > 0 && ind.g === 0 && ind.b === 0;
  note(`layer indicator (chain 13) at boot: ${rgb(ind)}`);
  verdict('device booted into layer 0 (indicator is pure red, hue 0)', isLayer0, rgb(ind));
  if (!isLayer0) {
    console.log('  !!   DIAGNOSIS: the indicator is not hue 0, so a layer move already fired.');
    console.log('  !!   GP16 (TTP223 OUT) rests LOW on the fabricated board (R10: TOUCH_AHLB->GND,');
    console.log('  !!   AHLB low = active-HIGH output). QMK reads direct pins as LOW=pressed and this');
    console.log('  !!   tree never defines MATRIX_INPUT_PRESSED_STATE, so matrix [3,2] is held from');
    console.log('  !!   power-on. [3,2] is TO(L_CTRL) on layer 0, so the pad boots into layer 1 and');
    console.log('  !!   the whole layer-0 keymap is unreachable. firmware/loudest_micro/config.h:21');
    console.log('  !!   and keyboard.json:32 both claim the strap is active-low; the board disagrees.');
  }
}

// ===================================== 0c. blast radius of a stuck layer key
// One probe, at whatever layer the device actually booted into: SW1 must be
// KC_F13. If [3,2] is stuck the pad is on L_CTRL, where SW1 is JS_MODE — a
// custom keycode that emits no USB report at all.
console.log('\n0c. blast radius — SW1 at the as-booted layer must still be KC_F13');
{
  const from = epLog.length;
  mcu.gpio[12].setInputValue(false); run(110000);
  mcu.gpio[12].setInputValue(true); run(110000);
  const rep = epLog.slice(from).filter((e) => e.ep === KBD_EP);
  const ok = rep.some((e) => e.bytes.slice(2).includes(0x68));
  verdict('SW1 emits KC_F13 (0x68) from the as-booted layer', ok,
    rep.map((e) => e.hex).join(' ') || 'no keyboard report at all');
  if (!ok) {
    console.log('  !!   The layer-0 keymap is unreachable: every one of the 12 macro keys, and the');
    console.log('  !!   2U hero key, resolves against L_CTRL instead (RGB/media/JS_MODE), and the');
    console.log('  !!   encoder maps to RGB_MOD rather than volume.');
  }
}

// ===================================== 0d. touch polarity, before anything else
// Run before the key sweep: on L_CTRL the sweep would press RGB_TOG (SW3) and
// blank the chain, destroying the layer-indicator signal this test reads.
console.log('\n0d. touch polarity — the layer must advance ON TOUCH, not on release');
{
  const before = readLeds()[13];
  const from = epLog.length;
  touchDown(); run(250000);
  const during = readLeds()[13];
  touchUp(); run(500000);
  const after = readLeds()[13];
  note(`layer indicator: rest ${rgb(before)} -> touched ${rgb(during)} -> released ${rgb(after)}`);
  const movedOnTouch = rgb(during) !== rgb(before);
  const movedOnRelease = rgb(after) !== rgb(during);
  verdict('the layer advances while the pad is TOUCHED', movedOnTouch,
    `still ${rgb(before)} while touched`);
  verdict('the layer does NOT advance again when the finger LIFTS', !movedOnRelease,
    `touched ${rgb(during)} -> released ${rgb(after)}`);
  verdict('touch sends no USB key report (TO() is a layer move)',
    epLog.slice(from).length === 0, epLog.slice(from).map((e) => `EP${e.ep}:${e.hex}`).join(' '));
  if (!movedOnTouch && movedOnRelease) {
    console.log('  !!   DIAGNOSIS: the layer moved on finger LIFT — the inverted-polarity signature.');
    console.log('  !!   Under the board strap, "touching" RELEASES a key QMK already thinks is held,');
    console.log('  !!   and lifting off presses it. Every touch action is off by one edge.');
  }
}
const failAfterTouch = failures;
// Normalise to layer 0 so the remaining sections test what they say they test.
// SET_LAYER(0) is claimed by the keyboard in both the default and vial builds.
sendRaw(cmd(0x02, 0x00));
run(400000);

// ================================================================ 1. LEDs individually addressable
console.log('\n1. LED chain — 24 positions, one unique color each (raw HID SET_KEY)');
const want = [];
for (let i = 0; i < LED_COUNT; i++) {
  const c = { r: 10 + i * 3, g: 100 - i * 2, b: 200 - i * 5 };
  want.push(c);
  sendRaw(SET_KEY(i, c.r, c.g, c.b, 0));
}
run(2000000);
{
  const got = readLeds();
  const wrong = [];
  for (let i = 0; i < LED_COUNT; i++) {
    if (want[i].r !== got[i].r || want[i].g !== got[i].g || want[i].b !== got[i].b) {
      wrong.push(`[${i}] want ${rgb(want[i])} got ${rgb(got[i])}`);
    }
  }
  verdict(`all ${LED_COUNT} chain positions independently addressable`, wrong.length === 0, wrong.join(' | '));
  note(`0-12 per-key: ${got.slice(0, 13).map(rgb).join('  ')}`);
  note(`13 indicator: ${rgb(got[13])}`);
  note(`14-23 underglow: ${got.slice(14).map(rgb).join('  ')}`);
}
// Prove isolation: repaint exactly one LED, nothing else may move.
{
  const before = readLeds();
  sendRaw(SET_KEY(9, 0xfe, 0x02, 0x7f, 0));
  run(400000);
  const after = readLeds();
  const moved = [];
  for (let i = 0; i < LED_COUNT; i++) if (rgb(before[i]) !== rgb(after[i])) moved.push(i);
  verdict('repainting LED 9 alone moves only LED 9', moved.length === 1 && moved[0] === 9, `moved: [${moved}]`);
  verdict('LED 9 took the exact requested color 254,2,127', rgb(after[9]) === '254,2,127', rgb(after[9]));
}

// ================================================================ 2. CLEAR
console.log('\n2. CLEAR releases the chain back to the on-device animation');
sendRaw(CLEAR());
run(600000);
{
  const got = readLeds();
  const stillHostColored = [];
  for (let i = 0; i < LED_COUNT; i++) if (rgb(got[i]) === rgb(want[i])) stillHostColored.push(i);
  verdict('no LED is still holding its host-set color', stillHostColored.length === 0, `[${stillHostColored}]`);
  verdict('chain is live (some LED is lit by the local animation)', got.some((c) => c.r || c.g || c.b));
  note(`layer-0 indicator (chain 13): ${rgb(got[13])}`);
  verdict('layer-0 indicator is pure red (hue 0 = layer 0)', got[13].r > 0 && got[13].g === 0 && got[13].b === 0, rgb(got[13]));
}

// ================================================================ 3. full 13-switch sweep
console.log('\n3. every switch — GPIO low -> the keycode the default keymap assigns');
// keyboard.json direct matrix, keymaps/default layer 0 (L_BASE).
const SWITCHES = [
  { gpio: 12, name: 'SW1  [0,0]', usage: 0x68, key: 'KC_F13' },
  { gpio: 9, name: 'SW2  [0,1]', usage: 0x69, key: 'KC_F14' },
  { gpio: 5, name: 'SW3  [0,2]', usage: 0x6a, key: 'KC_F15' },
  { gpio: 2, name: 'SW4  [0,3]', usage: 0x6b, key: 'KC_F16' },
  { gpio: 11, name: 'SW5  [1,0]', usage: 0x6c, key: 'KC_F17' },
  { gpio: 8, name: 'SW6  [1,1]', usage: 0x6d, key: 'KC_F18' },
  { gpio: 4, name: 'SW7  [1,2]', usage: 0x6e, key: 'KC_F19' },
  { gpio: 1, name: 'SW8  [1,3]', usage: 0x6f, key: 'KC_F20' },
  { gpio: 10, name: 'SW9  [2,0]', usage: 0x70, key: 'KC_F21' },
  { gpio: 7, name: 'SW10 [2,1]', usage: 0x71, key: 'KC_F22' },
  { gpio: 3, name: 'SW11 [2,2]', usage: 0x72, key: 'KC_F23' },
  { gpio: 0, name: 'SW12 [2,3]', usage: 0x73, key: 'KC_F24' },
];
const CONSUMER = [
  { gpio: 6, name: 'SW13 [3,0] 2U hero', usage: 0x00cd, key: 'KC_MPLY' },
  { gpio: 15, name: 'ENC_SW [3,1] push', usage: 0x00e2, key: 'KC_MUTE' },
];
for (const s of SWITCHES) {
  const from = epLog.length;
  mcu.gpio[s.gpio].setInputValue(false); run(110000);
  mcu.gpio[s.gpio].setInputValue(true); run(110000);
  const rep = epLog.slice(from).filter((e) => e.ep === KBD_EP);
  const hex = s.usage.toString(16).padStart(2, '0');
  const pressed = rep.some((e) => e.bytes.slice(2).includes(s.usage));
  const released = rep.length >= 2 && rep[rep.length - 1].bytes.every((b) => b === 0);
  verdict(`GP${String(s.gpio).padStart(2)} ${s.name} -> ${s.key} (0x${hex}) then release`,
    pressed && released, rep.map((e) => e.hex).join(' '));
}
for (const s of CONSUMER) {
  const from = epLog.length;
  mcu.gpio[s.gpio].setInputValue(false); run(110000);
  mcu.gpio[s.gpio].setInputValue(true); run(110000);
  const rep = epLog.slice(from).filter((e) => e.ep !== KBD_EP);
  const lo = s.usage & 0xff, hi = (s.usage >> 8) & 0xff;
  const seen = rep.some((e) => e.bytes.some((b, i) => b === lo && e.bytes[i + 1] === hi));
  verdict(`GP${String(s.gpio).padStart(2)} ${s.name} -> ${s.key} (consumer 0x${s.usage.toString(16)})`,
    seen, rep.map((e) => `EP${e.ep}:${e.hex}`).join(' ') || 'no report');
}

// ================================================================ 4. encoder
const failBeforeEncoder = failures;
console.log('\n4. EC11 encoder — quadrature on GP13/GP14, layer 0 maps to volume');
function rotate(cw, detents) {
  // (A,B) walk: 11 -> 01 -> 00 -> 10 -> 11, and its reverse. WHICH of the two is
  // a physically-clockwise detent is a property of the A/B landing on the board,
  // so it comes from the --encoder model rather than being assumed here.
  const seq = [[0, 1], [0, 0], [1, 0], [1, 1]];
  const forwardWalk = cw === ENCODER_CW_IS_FORWARD_WALK;
  const order = forwardWalk ? seq : seq.slice().reverse();
  for (let d = 0; d < detents; d++) {
    for (const [a, b] of order) {
      mcu.gpio[13].setInputValue(!!a);
      mcu.gpio[14].setInputValue(!!b);
      run(15000);
    }
  }
  run(200000);
}
for (const [dir, cw, usage, key] of [['CW', true, 0x00e9, 'KC_VOLU'], ['CCW', false, 0x00ea, 'KC_VOLD']]) {
  const from = epLog.length;
  rotate(cw, 3);
  const rep = epLog.slice(from);
  const lo = usage & 0xff, hi = (usage >> 8) & 0xff;
  const seen = rep.some((e) => e.bytes.some((b, i) => b === lo && e.bytes[i + 1] === hi));
  verdict(`rotate ${dir} -> ${key} (consumer 0x${usage.toString(16)})`, seen,
    rep.map((e) => `EP${e.ep}:${e.hex}`).join(' ') || 'no report');
}

const failAfterEncoder = failures;

// ================================================================ 5. joystick
console.log('\n5. analog joystick — ADC injection -> HID gamepad report (report id 0x07)');
const adcReads = [];
{ const a = mcu.adc; const orig = a.onADCRead; a.onADCRead = (ch) => { adcReads.push(ch); return orig(ch); }; }
function joystick(x12, y12, label) {
  const from = epLog.length;
  mcu.adc.channelValues[0] = x12; // GP26 / ADC0, declared as axis "x"
  mcu.adc.channelValues[1] = y12; // GP27 / ADC1, declared as axis "y"
  run(700000);
  const rep = epLog.slice(from).filter((e) => e.bytes[0] === 0x07);
  if (!rep.length) return { label, axes: null, hex: '(none)' };
  const b = rep[rep.length - 1].bytes;
  const s16 = (i) => { const v = b[i] | (b[i + 1] << 8); return v >= 0x8000 ? v - 0x10000 : v; };
  return { label, axes: [s16(1), s16(3)], hex: rep[rep.length - 1].hex };
}
const jRest = joystick(2048, 2048, 'rest');
const jA = joystick(4000, 100, 'ADC0 high / ADC1 low');
const jB = joystick(100, 4000, 'ADC0 low / ADC1 high');
for (const j of [jRest, jA, jB]) note(`${j.label.padEnd(22)} report ${j.hex}  axes=${j.axes ? j.axes.join(',') : 'n/a'}`);
verdict('joystick emits HID gamepad reports at all', jA.axes !== null && jB.axes !== null);
if (jA.axes && jB.axes) {
  // 12-bit 4000 -> QMK reads 10-bit 1000 -> (1000-512)/511*511 = +488
  // 12-bit  100 -> QMK reads 10-bit   25 -> (25-512)/512*512   = -487
  const big = (v) => Math.abs(v) > 400;
  verdict('both axes swing to near full scale on a full ADC sweep',
    big(jA.axes[0]) && big(jA.axes[1]) && big(jB.axes[0]) && big(jB.axes[1]),
    `A=${jA.axes} B=${jB.axes}`);
  verdict('the two axes move independently (swapping the ADC inputs flips both signs)',
    Math.sign(jA.axes[0]) === -Math.sign(jB.axes[0]) && Math.sign(jA.axes[1]) === -Math.sign(jB.axes[1]),
    `A=${jA.axes} B=${jB.axes}`);
  note(`ADC channels the emulator serviced: [${[...new Set(adcReads)].join(',')}] — see README "Untrusted":`);
  note('axis IDENTITY (which report slot is X) is NOT decided by this run.');
}

// ================================================================ done
console.log('');
console.log(`touch model: ${TOUCH_MODEL}   encoder model: ${ENCODER_MODEL}   checks: ${checks}   failures: ${failures}`);
if (failAfterTouch > failBeforeTouch && TOUCH_MODEL === 'board') {
  console.log('NOTE: --touch=board models the PCB as fabricated (R10: TOUCH_AHLB->GND).');
  console.log('      Re-run with --touch=firmware to see the same binary pass under the');
  console.log('      polarity config.h:21 assumes — that isolates the fault to the strap,');
  console.log('      not to the keymap or the LED/USB paths.');
}
if (failAfterEncoder > failBeforeEncoder && ENCODER_MODEL === 'board') {
  console.log('NOTE: --encoder=board models the EC11 A/B landing measured on the assembled');
  console.log('      v5_6 on 2026-08-15. Re-run with --encoder=firmware to see the same');
  console.log('      binary under the pre-flip assumption — that isolates the fault to the');
  console.log('      A/B landing (config.h ENCODER_DIRECTION_FLIP), not to the keymap.');
}
console.log(failures === 0 ? 'BEHAVIOR SIM: PASS' : 'BEHAVIOR SIM: FAIL');
process.exit(failures === 0 ? 0 : 1); // explicit: the USB controller keeps the loop alive
