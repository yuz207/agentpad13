// agentpad13 - referee for the BRING-UP CALIBRATION firmware
// (firmware/prebuilt/loudest_micro_calibrate.uf2) on rp2040js.
//
// Sibling of behavior.cjs, which is the referee for the two SHIPPED builds and
// is deliberately never edited. This file is a NEW harness for a NEW artifact;
// behavior.cjs is untouched by it.
//
// WHAT IT PROVES. keymaps/calibrate turns the pad into a self-reporting
// calibration jig: it types its own measurements, and at step 4 it types the
// finished config lines the owner pastes back. Every one of those numbers is
// DERIVED - rest average, noise band, min/max sweep, per-axis inversion, the
// shared JS_CENTER, the re-derived JS_THRESHOLD, and the fires/NEVER-FIRES
// verdict against the SHIPPED JS_THRESHOLD 300. A derivation bug there would
// hand the owner a wrong config with total confidence, so every scenario below
// computes the whole expected report INDEPENDENTLY in JavaScript, from the
// values this harness injected, and asserts the typed text CHARACTER FOR
// CHARACTER against it. Nothing is compared against the firmware's own
// arithmetic.
//
// HOW THE TYPED STREAM IS READ. The calibrate keymap types with send_string(),
// which is ordinary HID key traffic on the boot-keyboard interface (cls 3 /
// proto 1) that behavior.cjs already decodes for the key sweep. Here each 8-byte
// report is diffed against the previous one; every newly-pressed usage is turned
// back into ASCII through the US layout table, with shift taken from the
// modifier byte of the same report. That reconstructs exactly what a text editor
// would have received.
//
// Usage:  node calibrate.cjs [../prebuilt/loudest_micro_calibrate.uf2]
'use strict';

const fs = require('fs');
const path = require('path');

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
const UF2_PATH = path.resolve(__dirname, args.find((a) => !a.startsWith('--')) ?? '../prebuilt/loudest_micro_calibrate.uf2');

// A/B arm, in the spirit of behavior.cjs's --touch: run with the ADC
// fidelity workaround (f) DISABLED. It must FAIL, and it must fail on the ADC
// numbers rather than on the prompts. A harness whose workaround cannot be
// switched off is a harness whose workaround cannot be audited.
const ADC_FIX = !args.includes('--no-adc-fix');

// GPIO map (keyboard.json matrix_pins.direct + loudest_micro.c).
const GP_SW1 = 12; // [0,0] step / capture
const GP_SW2 = 9;  // [0,1] restart
const GP_SW3 = 5;  // [0,2] live reading
const GP_SW4 = 2;  // [0,3] must stay a no-op
const GP_ENC_SW = 15; // [3,1] encoder push
const GP_TOUCH = 16;  // TTP223 OUT, injected at [3,2] by matrix_scan_kb()
const GP_ENC_A = 13;
const GP_ENC_B = 14;

// ---------------------------------------------------------------- verdicts
let failures = 0;
let checks = 0;
function verdict(name, cond, detail = '') {
  checks++;
  if (!cond) failures++;
  console.log(`  [${cond ? 'ok' : 'FAIL'}] ${name}${cond || !detail ? '' : '\n         <- ' + detail}`);
}
function note(msg) { console.log(`  ..   ${msg}`); }

// ---------------------------------------------------------------- device
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

// --- ASCII decode of the typed HID stream (US layout, which is what QMK's
//     send_string ascii_to_keycode_lut encodes).
const PUNCT = {
  0x28: ['\n', '\n'], 0x2b: ['\t', '\t'], 0x2c: [' ', ' '],
  0x2d: ['-', '_'], 0x2e: ['=', '+'], 0x2f: ['[', '{'], 0x30: [']', '}'],
  0x31: ['\\', '|'], 0x33: [';', ':'], 0x34: ["'", '"'], 0x35: ['`', '~'],
  0x36: [',', '<'], 0x37: ['.', '>'], 0x38: ['/', '?'],
};
const DIGITS = '1234567890';
const SHIFTED_DIGITS = '!@#$%^&*()';
function usageToAscii(usage, shift) {
  if (usage >= 0x04 && usage <= 0x1d) {
    const c = String.fromCharCode(97 + usage - 0x04);
    return shift ? c.toUpperCase() : c;
  }
  if (usage >= 0x1e && usage <= 0x27) {
    const i = usage - 0x1e;
    return shift ? SHIFTED_DIGITS[i] : DIGITS[i];
  }
  const e = PUNCT[usage];
  return e ? (shift ? e[1] : e[0]) : null;
}

function boot(label) {
  const sim = new Simulator();
  const mcu = sim.rp2040;
  mcu.loadBootrom(bootromB1);
  mcu.logger = new ConsoleLogger(LogLevel.Error);
  const blocks = loadUF2(UF2_PATH, mcu);

  const adcServiced = [];

  // --- rp2040js fidelity workarounds. All live HERE, never in firmware, and
  //     each is named at its site exactly as behavior.cjs does.
  { // (a) ADC FIFO_REG reads never re-evaluate the IRQ line -> interrupt storm.
    const adc = mcu.adc;
    const orig = adc.readUint32.bind(adc);
    adc.readUint32 = (o) => { const v = orig(o); if (o === 0x0c) adc.checkInterrupts(); return v; };
  }
  { // (f) NEW, and the reason this harness can trust an ADC number at all:
    //     rp2040js never auto-clears CS.START_ONCE (bit 2) after a conversion
    //     starts, but real RP2040 silicon does (RP2040 datasheet 4.9.5: the
    //     bit is self-clearing). ChibiOS's RP ADC LLD sets the channel with a
    //     READ-MODIFY-WRITE of CS (hal_adc_lld.c set_channel(), ADCv1), so on
    //     the unpatched emulator that RMW writes the stale START_ONCE back and
    //     kicks off a SECOND, unwanted conversion. The extra sample sits in the
    //     4-deep ADC FIFO and every adcConvert() then returns the PREVIOUS
    //     conversion's value - a strict one-conversion lag.
    //     Measured on the unpatched emulator, with the calibrate firmware:
    //       * alternating reads (analogReadPin(GP26); analogReadPin(GP27)) came
    //         back SWAPPED - inject ch0=800/ch1=200 and the board typed
    //         "live X=200 Y=800";
    //       * 16 consecutive reads of one pin averaged in one stale foreign
    //         sample - inject ch0=880/ch1=140 and the 16-sample average of GP26
    //         came back as 834, i.e. exactly (140 + 15*880 + 8) / 16.
    //     That second number is what identifies the fault as a pipeline lag
    //     rather than a channel mix-up, and it is why the lag CANNOT simply be
    //     cancelled by swapping the injection: its effect depends on the read
    //     pattern. Clearing the self-clearing bit removes the extra conversion
    //     and the lag with it, which section 0 below re-asserts on every run.
    if (ADC_FIX) {
      const adc = mcu.adc;
      const origWrite = adc.writeUint32.bind(adc);
      adc.writeUint32 = (o, v) => { origWrite(o, v); if (o === 0x00) adc.cs &= ~(1 << 2); };
    }
  }
  { // (b) DMA CHAN_ABORT reads are unimplemented -> ws2812 abort-poll spins.
    const dma = mcu.dma;
    const orig = dma.readUint32.bind(dma);
    dma.readUint32 = (o) => (o === 0x444 ? 0 : orig(o));
  }
  { // instrumentation: which ADC channels the emulator actually serviced.
    const adc = mcu.adc;
    const orig = adc.onADCRead;
    adc.onADCRead = (ch) => { adcServiced.push(ch); return orig(ch); };
    adc.channelValues[0] = 2048; // GP26 / ADC0 - joystick X (12-bit)
    adc.channelValues[1] = 2048; // GP27 / ADC1 - joystick Y (12-bit)
  }
  // (c) pull-ups are not folded into inputValue: the 13 switch lines and the
  //     encoder idle high (switch to GND); GP16 is the TTP223 output, which
  //     idles LOW on this board (R10 straps TOUCH_AHLB -> GND = active-high).
  //     Same model behavior.cjs calls "board truth".
  for (let p = 0; p <= 15; p++) mcu.gpio[p].setInputValue(true);
  mcu.gpio[GP_TOUCH].setInputValue(false);
  mcu.dma.channels.forEach((chan) => {
    const origStart = chan.start.bind(chan);
    chan.start = () => {
      origStart();
      // (d) starting a channel whose DREQ is already asserted never schedules.
      if (chan.active && mcu.dma.dreq[chan.treq]) chan.scheduleTransfer();
    };
  });

  // --- USB host shim (same shape as behavior.cjs; only the boot-keyboard
  //     interface matters here, because everything this firmware says it says
  //     as keystrokes).
  const usb = mcu.usbCtrl;
  let descriptorsSize = null, configured = false, resetSeen = false, ep0Activity = 0;
  let enumState = 'address';
  const descriptors = [], interfaces = [];
  const epLog = [];
  const epCounts = new Map(); // per-endpoint report counter, for the quiet detector
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
        if (descriptors.length >= descriptorsSize || (ifaceKbd() && ifaceRaw())) {
          enumState = 'setconf'; usb.sendSetupPacket(setDeviceConfigurationPacket(1));
        }
      }
      return;
    }
    epLog.push({ ep, bytes: Array.from(buf) });
    epCounts.set(ep, (epCounts.get(ep) ?? 0) + 1);
  };
  usb.onEndpointRead = () => {};

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

  mcu.core.PC = 0x10000000;
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
  if (!configured) {
    console.log(`  [FAIL] ${label}: USB never configured (state=${enumState})`);
    return null;
  }
  const KBD_EP = ifaceKbd().inEp;

  // --- typed-stream decoder
  let prevKeys = new Set();
  let pending = '';
  let cursor = 0;
  function pump() {
    for (; cursor < epLog.length; cursor++) {
      const e = epLog[cursor];
      if (e.ep !== KBD_EP || e.bytes.length < 8) continue;
      const shift = (e.bytes[0] & 0x22) !== 0;
      const keys = new Set(e.bytes.slice(2, 8).filter((k) => k !== 0));
      for (const k of keys) {
        if (!prevKeys.has(k)) {
          const c = usageToAscii(k, shift);
          if (c) pending += c;
        }
      }
      prevKeys = keys;
    }
  }
  function take() { pump(); const out = pending; pending = ''; return out; }
  function reportCount() { return epCounts.get(KBD_EP) ?? 0; }

  // Run until the device has finished talking. Two phases, and both are needed:
  //
  //   1. WAIT FOR IT TO START. A rest capture is 100 ADC samples 5 ms apart -
  //      more than half a second during which the firmware is deliberately
  //      silent. A naive "stop when it goes quiet" loop returns during that
  //      window and every later assertion reads the PREVIOUS step's text.
  //   2. WAIT FOR IT TO STOP, on the KEYBOARD endpoint only. QMK's joystick
  //      task pushes a HID gamepad report on a different endpoint whenever an
  //      axis value changes, so counting all endpoints would keep the detector
  //      awake (or asleep) for reasons that have nothing to do with typing.
  //
  // `waitFirstUs` is the budget for phase 1; pass a small one where the correct
  // answer is "it types nothing".
  function runUntilQuiet(maxUs = 60000000, quietUs = 300000, waitFirstUs = 2000000) {
    const SLICE = 20000;
    const startCount = reportCount();
    let elapsed = 0;
    while (elapsed < waitFirstUs && reportCount() === startCount) {
      run(SLICE);
      elapsed += SLICE;
    }
    let quiet = 0, last = reportCount();
    while (elapsed < maxUs) {
      run(SLICE);
      elapsed += SLICE;
      const now = reportCount();
      if (now !== last) { last = now; quiet = 0; } else { quiet += SLICE; }
      if (quiet >= quietUs) break;
    }
  }

  function press(gpio) {
    mcu.gpio[gpio].setInputValue(false); run(25000);
    mcu.gpio[gpio].setInputValue(true); run(25000);
  }
  function touch(down) { mcu.gpio[GP_TOUCH].setInputValue(down); run(60000); }
  function rotate(cw, detents) {
    // (A,B) walk. CW: 11 -> 01 -> 00 -> 10 -> 11 ; CCW is the reverse.
    const seq = [[0, 1], [0, 0], [1, 0], [1, 1]];
    const order = cw ? seq : seq.slice().reverse();
    for (let d = 0; d < detents; d++) {
      for (const [a, b] of order) {
        mcu.gpio[GP_ENC_A].setInputValue(!!a);
        mcu.gpio[GP_ENC_B].setInputValue(!!b);
        run(15000);
      }
    }
    run(120000);
  }
  // Inject a 10-bit pair. analogReadPin() returns sample >> 2 on this build
  // (12-bit ADC, ADC_RESOLUTION 10), so a 10-bit value v is injected as v*4 and
  // comes back as exactly v.
  function adc(x10, y10) {
    mcu.adc.channelValues[0] = x10 * 4;
    mcu.adc.channelValues[1] = y10 * 4;
  }

  return { sim, mcu, blocks, run, runUntilQuiet, press, touch, rotate, adc, take, reportCount, adcServiced };
}

// ---------------------------------------------------------------- expectations
// Independent JavaScript implementation of the derivation rules. Nothing here
// reads or mirrors the firmware's C arithmetic; it is written from the spec:
//   inverted_y = (y_up  > y_rest)   because loudest_micro.c fires UP on
//                                   y < JS_CENTER - JS_THRESHOLD
//   inverted_x = (x_right < x_rest) because it fires RIGHT on
//                                   x > JS_CENTER + JS_THRESHOLD
//   C = round((x_rest + y_rest) / 2)          (one JS_CENTER serves both axes)
//   T = floor(0.60 * smallest half-swing)     (40% of travel left in reserve)
//   shipped verdict uses the SHIPPED constants 512/300 and the SHIPPED strict
//   comparisons: a direction fires only below 212 or above 812.
const SHIPPED_CENTER = 512;
const SHIPPED_THRESHOLD = 300;
const firesLow = (v) => v < SHIPPED_CENTER - SHIPPED_THRESHOLD;
const firesHigh = (v) => v > SHIPPED_CENTER + SHIPPED_THRESHOLD;

function expectedReport(m) {
  const invX = m.xRight < m.xRest;
  const invY = m.yUp > m.yRest;
  const swings = [m.xRest - m.xMin, m.xMax - m.xRest, m.yRest - m.yMin, m.yMax - m.yRest];
  const smallest = Math.min(...swings);
  const C = Math.round((m.xRest + m.yRest) / 2);
  const T = Math.floor((smallest * 60) / 100);
  const worstNoise = Math.max(m.xNoise, m.yNoise);
  const skew = Math.abs(m.xRest - m.yRest);

  let s = '';
  s += 'agentpad13 cal v1 | REPORT\n';
  s += `X: min=${m.xMin} rest=${m.xRest} max=${m.xMax}  inverted=${invX ? 'YES' : 'NO'}\n`;
  s += `Y: min=${m.yMin} rest=${m.yRest} max=${m.yMax}  inverted=${invY ? 'YES' : 'NO'}\n`;
  if (smallest < 100) {
    s += `WARNING: SWING TOO SMALL - check JS1 / restart with SW2 (smallest half-swing ${smallest}, want 100+)\n`;
  }
  if (T <= 3 * worstNoise) {
    s += `WARNING: THRESHOLD INSIDE NOISE - derived JS_THRESHOLD ${T} is not more than 3x the rest noise +/-${worstNoise}\n`;
  }
  if (skew > 30) {
    s += `WARNING: X and Y rest differ by ${skew} counts (limit 30) - loudest_micro.c shares ONE JS_CENTER for both axes\n`;
  }
  const v = (fire) => (fire ? 'fires' : 'NEVER FIRES');
  s += 'shipped JS_THRESHOLD 300 verdict (fires only below 212 or above 812): ' +
    `X- ${v(firesLow(m.xMin))} X+ ${v(firesHigh(m.xMax))} ` +
    `Y- ${v(firesLow(m.yMin))} Y+ ${v(firesHigh(m.yMax))}\n`;
  s += '--- apply to firmware/loudest_micro/keyboard.json (joystick.axes): ---\n';
  // POLARITY-NOTE.md "The one-line fix": an inverted axis is corrected by
  // swapping low and high. The board is expected to have applied it already.
  const xLow = invX ? m.xMax : m.xMin, xHigh = invX ? m.xMin : m.xMax;
  const yLow = invY ? m.yMax : m.yMin, yHigh = invY ? m.yMin : m.yMax;
  s += `"x": {"input_pin": "GP26", "low": ${xLow}, "rest": ${m.xRest}, "high": ${xHigh}},\n`;
  s += `"y": {"input_pin": "GP27", "low": ${yLow}, "rest": ${m.yRest}, "high": ${yHigh}}\n`;
  s += '--- apply to firmware/loudest_micro/loudest_micro.c: ---\n';
  s += `#define JS_CENTER ${C}\n`;
  s += `#define JS_THRESHOLD ${T}\n`;
  s += 'note: if an axis shows inverted=YES the arrow/scroll comparisons in\n';
  s += 'loudest_micro.c must be mirrored for that axis too - POLARITY-NOTE.md\n';
  return { text: s, C, T, invX, invY, smallest };
}

function diffText(want, got) {
  const w = want.split('\n'), g = got.split('\n');
  for (let i = 0; i < Math.max(w.length, g.length); i++) {
    if (w[i] !== g[i]) return `line ${i + 1}\n            want: ${JSON.stringify(w[i])}\n            got : ${JSON.stringify(g[i])}`;
  }
  return '';
}

// ---------------------------------------------------------------- scenarios
// A scenario drives the four-press guided flow. `restA` is held for the whole
// 500 ms rest window unless `restB` is given, in which case the injection is
// stepped part-way through the window: the rest AVERAGE (first 16 samples,
// ~80 ms) still sees only restA, while the noise band widens to |restB - restA|.
function runGuidedFlow(dev, plan) {
  const seen = { x: [], y: [] }; // every value injected while the sweep is live
  const inject = (x, y, track) => { dev.adc(x, y); if (track) { seen.x.push(x); seen.y.push(y); } };

  // 1. rest
  inject(plan.restA[0], plan.restA[1], false);
  dev.run(200000);
  const bootReports = dev.reportCount();
  dev.press(GP_SW1);
  seen.x.push(plan.restA[0]); seen.y.push(plan.restA[1]);
  if (plan.restB) {
    dev.run(250000); // past sample 16 (~80 ms), still inside the 500 ms window
    inject(plan.restB[0], plan.restB[1], true);
  }
  dev.runUntilQuiet();
  const restText = dev.take();

  // 2. up
  inject(plan.up[0], plan.up[1], true);
  dev.run(60000);
  dev.press(GP_SW1);
  dev.runUntilQuiet();
  const upText = dev.take();

  // 3. right
  inject(plan.right[0], plan.right[1], true);
  dev.run(60000);
  dev.press(GP_SW1);
  dev.runUntilQuiet();
  const rightText = dev.take();

  // 4. roll the outer edge, then report
  for (const [x, y] of plan.roll) {
    inject(x, y, true);
    dev.run(60000);
  }
  inject(plan.restA[0], plan.restA[1], true); // hand comes back to center
  dev.run(60000);
  dev.press(GP_SW1);
  dev.runUntilQuiet();
  const reportText = dev.take();

  // Measurements as THIS harness knows them, from its own injections only.
  const restWindow = plan.restB ? [plan.restA, plan.restB] : [plan.restA];
  const m = {
    xRest: plan.restA[0],
    yRest: plan.restA[1],
    xNoise: Math.max(...restWindow.map((p) => Math.abs(p[0] - plan.restA[0]))),
    yNoise: Math.max(...restWindow.map((p) => Math.abs(p[1] - plan.restA[1]))),
    yUp: plan.up[1],
    xRight: plan.right[0],
    xMin: Math.min(...seen.x), xMax: Math.max(...seen.x),
    yMin: Math.min(...seen.y), yMax: Math.max(...seen.y),
  };
  return { bootReports, restText, upText, rightText, reportText, m };
}

function scenarioGuided(title, plan, extra) {
  console.log(`\n${title}`);
  const dev = boot(title);
  if (!dev) { failures++; checks++; return; }
  const r = runGuidedFlow(dev, plan);
  const exp = expectedReport(r.m);

  verdict('the board types NOTHING until the first SW1 press', r.bootReports === 0,
    `${r.bootReports} keyboard report(s) before any key was pressed`);

  const wantRest = `agentpad13 cal v1 | rest X=${r.m.xRest} Y=${r.m.yRest} noise X=+/-${r.m.xNoise} Y=+/-${r.m.yNoise}\n` +
    'step 2/4: HOLD stick UP (away from you, toward the encoder edge), then press SW1\n';
  verdict('press 1 types the rest average, the measured noise band and the step-2 prompt',
    r.restText === wantRest, diffText(wantRest, r.restText));

  const wantUp = `Y up sample: ${r.m.yUp}\nstep 3/4: HOLD stick RIGHT, then press SW1\n`;
  verdict('press 2 types the Y-up sample and the step-3 prompt', r.upText === wantUp, diffText(wantUp, r.upText));

  const wantRight = `X right sample: ${r.m.xRight}\nstep 4/4: slowly roll the stick around its full outer edge twice, then press SW1\n`;
  verdict('press 3 types the X-right sample and the step-4 prompt', r.rightText === wantRight, diffText(wantRight, r.rightText));

  verdict('press 4 types the full report, character for character, incl. derived JS_CENTER/JS_THRESHOLD and the copy-paste config',
    r.reportText === exp.text, diffText(exp.text, r.reportText));
  note(`independently derived: JS_CENTER=${exp.C} JS_THRESHOLD=${exp.T} (smallest half-swing ${exp.smallest}) invX=${exp.invX ? 'YES' : 'NO'} invY=${exp.invY ? 'YES' : 'NO'}`);
  note(`ADC channels the emulator serviced: [${[...new Set(dev.adcServiced)].join(',')}] over ${dev.adcServiced.length} conversions`);

  if (extra) extra(r, exp, dev);
}

// ================================================================ 0. harness self-check
console.log(`agentpad13 calibration sim — ${path.basename(UF2_PATH)}`);
console.log(ADC_FIX
  ? 'ADC model: rp2040js CS.START_ONCE patched to self-clear (real-silicon behavior)'
  : 'ADC model: rp2040js AS-IS — CS.START_ONCE never clears, so every conversion lags by one. MUST FAIL.');
{
  console.log('\n0. harness self-check — the ADC injection must survive both read patterns');
  const dev = boot('self-check');
  if (!dev) { failures++; checks++; }
  else {
    note(`loaded ${dev.blocks} UF2 blocks`);
    // Alternating reads: cal_live() does analogReadPin(GP26) then (GP27).
    dev.adc(800, 200);
    dev.run(200000);
    const silentBefore = dev.reportCount();
    dev.press(GP_SW3);
    dev.runUntilQuiet();
    const live1 = dev.take();
    verdict('nothing is typed at boot (no editor is focused when the board is plugged in)',
      silentBefore === 0, `${silentBefore} report(s)`);
    verdict('SW3 live line reports the injected pair in the right order (X=GP26/ADC0, Y=GP27/ADC1)',
      live1 === 'live X=800 Y=200\n', JSON.stringify(live1));
    dev.adc(123, 987);
    dev.run(100000);
    dev.press(GP_SW3);
    dev.runUntilQuiet();
    const live2 = dev.take();
    verdict('a second, different pair reads back exactly (both channels move independently)',
      live2 === 'live X=123 Y=987\n', JSON.stringify(live2));
    verdict('the emulator serviced BOTH ADC channels', new Set(dev.adcServiced).size === 2,
      `channels=[${[...new Set(dev.adcServiced)].join(',')}]`);
    note('16-consecutive-read pattern (cal_avg) is proven by the Y-up / X-right assertions below:');
    note('an uncorrected one-conversion lag shows up there as a foreign 1/16 contamination.');
  }
}

// ================================================================ 1. nominal
scenarioGuided(
  '1. NOMINAL — both axes sensed the right way round, healthy swing, real noise band',
  {
    restA: [507, 514],
    restB: [509, 512],            // dithers the rest window -> noise X +/-2, Y +/-2
    up: [507, 180],               // UP decreases Y  => inverted=NO
    right: [850, 514],            // RIGHT increases X => inverted=NO
    roll: [[180, 514], [850, 514], [507, 180], [507, 850]],
  });

// ================================================================ 2. inverted Y
scenarioGuided(
  '2. INVERTED Y — pushing up RAISES the Y reading; the typed JSON must swap Y low/high and leave X alone',
  {
    restA: [507, 514],
    up: [507, 850],               // UP increases Y => inverted=YES
    right: [850, 514],            // X unchanged from scenario 1
    roll: [[180, 514], [850, 514], [507, 180], [507, 850]],
  },
  (r, exp) => {
    verdict('Y is flagged inverted and X is not', exp.invY === true && exp.invX === false,
      `invX=${exp.invX} invY=${exp.invY}`);
    verdict('the typed Y config line has low/high SWAPPED (low=max, high=min)',
      r.reportText.includes(`"y": {"input_pin": "GP27", "low": ${r.m.yMax}, "rest": ${r.m.yRest}, "high": ${r.m.yMin}}`),
      r.reportText.split('\n').find((l) => l.startsWith('"y"')));
    verdict('the typed X config line is untouched (low=min, high=max)',
      r.reportText.includes(`"x": {"input_pin": "GP26", "low": ${r.m.xMin}, "rest": ${r.m.xRest}, "high": ${r.m.xMax}},`),
      r.reportText.split('\n').find((l) => l.startsWith('"x"')));
  });

// ================================================================ 3. reduced swing
scenarioGuided(
  '3. REDUCED SWING — a stick that only reaches 250..780 kills arrows and scroll on the SHIPPED firmware',
  {
    restA: [507, 514],
    up: [507, 250],
    right: [780, 514],
    roll: [[250, 514], [780, 514], [507, 250], [507, 780]],
  },
  (r, exp) => {
    const line = r.reportText.split('\n').find((l) => l.startsWith('shipped JS_THRESHOLD'));
    verdict('all four directions are reported NEVER FIRES against the shipped JS_THRESHOLD 300',
      line === 'shipped JS_THRESHOLD 300 verdict (fires only below 212 or above 812): X- NEVER FIRES X+ NEVER FIRES Y- NEVER FIRES Y+ NEVER FIRES',
      JSON.stringify(line));
    // 507-250=257, 780-507=273, 514-250=264, 780-514=266 -> smallest 257
    verdict('JS_THRESHOLD is re-derived from the SMALL swing, not from the shipped 300',
      exp.smallest === 257 && exp.T === 154 && exp.T < SHIPPED_THRESHOLD,
      `smallest=${exp.smallest} T=${exp.T}`);
    verdict('the re-derived threshold would actually fire every direction on this stick',
      507 - exp.T > 250 && 507 + exp.T < 780 && 514 - exp.T > 250 && 514 + exp.T < 780,
      `T=${exp.T}`);
  });

// ================================================================ 4. touch + encoder + restart + live
{
  console.log('\n4. TOUCH + ENCODER + RESTART + LIVE — the non-joystick half of bring-up');
  const dev = boot('scenario 4');
  if (!dev) { failures++; checks++; }
  else {
    dev.adc(507, 514);
    dev.run(200000);
    const bootReports = dev.reportCount();
    verdict('still silent at boot', bootReports === 0, `${bootReports} report(s)`);

    // touch: press and release, in that order (this is the TTP223 fix on real
    // silicon - GP16 idles LOW and goes HIGH while touched).
    dev.touch(true); dev.runUntilQuiet();
    const tDown = dev.take();
    dev.touch(false); dev.runUntilQuiet();
    const tUp = dev.take();
    verdict('touching the pad types TOUCH:DOWN (and nothing else)', tDown === 'TOUCH:DOWN\n', JSON.stringify(tDown));
    verdict('lifting off types TOUCH:UP', tUp === 'TOUCH:UP\n', JSON.stringify(tUp));

    dev.rotate(true, 2); dev.runUntilQuiet();
    const cw = dev.take();
    dev.rotate(false, 2); dev.runUntilQuiet();
    const ccw = dev.take();
    verdict('rotating the encoder one way types ENC:CW', /^(ENC:CW\n)+$/.test(cw), JSON.stringify(cw));
    verdict('rotating the other way types ENC:CCW', /^(ENC:CCW\n)+$/.test(ccw), JSON.stringify(ccw));

    dev.press(GP_ENC_SW); dev.runUntilQuiet();
    const encPress = dev.take();
    verdict('pressing the encoder types ENC:PRESS', encPress === 'ENC:PRESS\n', JSON.stringify(encPress));

    // "types nothing" is the correct answer here, so give phase 1 a short budget
    dev.press(GP_SW4); dev.runUntilQuiet(2000000, 300000, 400000);
    const sw4 = dev.take();
    verdict('an unassigned switch (SW4) types nothing at all', sw4 === '', JSON.stringify(sw4));

    // start a capture, abandon it mid-flow, restart, and prove the restart is clean
    dev.adc(400, 400);
    dev.press(GP_SW1); dev.runUntilQuiet();
    const firstRest = dev.take();
    verdict('a first capture runs with the first pair', firstRest.startsWith('agentpad13 cal v1 | rest X=400 Y=400 noise X=+/-0 Y=+/-0\n'),
      JSON.stringify(firstRest));

    dev.adc(900, 100); // move the stick far away mid-capture, as a fumbled run would
    dev.run(200000);
    dev.press(GP_SW2); dev.runUntilQuiet();
    const restarted = dev.take();
    verdict('SW2 types the restart prompt', restarted === 'restarted: center the stick, press SW1\n', JSON.stringify(restarted));

    dev.adc(511, 515);
    dev.run(100000);
    dev.press(GP_SW1); dev.runUntilQuiet();
    const secondRest = dev.take();
    const wantSecond = 'agentpad13 cal v1 | rest X=511 Y=515 noise X=+/-0 Y=+/-0\n' +
      'step 2/4: HOLD stick UP (away from you, toward the encoder edge), then press SW1\n';
    verdict('the restarted capture is CLEAN — step 1 again, with no memory of the abandoned run',
      secondRest === wantSecond, diffText(wantSecond, secondRest));

    dev.adc(321, 654);
    dev.run(100000);
    dev.press(GP_SW3); dev.runUntilQuiet();
    const live = dev.take();
    verdict('SW3 still gives a live reading mid-flow, matching the injected pair',
      live === 'live X=321 Y=654\n', JSON.stringify(live));

    dev.touch(true); dev.runUntilQuiet();
    dev.touch(false); dev.runUntilQuiet();
    const tAgain = dev.take();
    verdict('touch still reports mid-flow, both edges, in order',
      tAgain === 'TOUCH:DOWN\nTOUCH:UP\n', JSON.stringify(tAgain));
  }
}

// ================================================================ done
console.log('');
console.log(`adc fix: ${ADC_FIX ? 'on' : 'OFF'}   checks: ${checks}   failures: ${failures}`);
if (failures && ADC_FIX) {
  console.log('NOTE: re-run with --no-adc-fix to see the same binary fail on the ADC numbers');
  console.log('      only (prompts intact). If BOTH arms fail the same way, the fault is in');
  console.log('      the firmware or this harness, not in the emulator workaround.');
}
console.log(failures === 0 ? 'CALIBRATE SIM: PASS' : 'CALIBRATE SIM: FAIL');
process.exit(failures === 0 ? 0 : 1); // explicit: the USB controller keeps the loop alive
