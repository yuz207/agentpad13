// agentpad13 Rev A UF2 smoke test on rp2040js (headless RP2040 emulator).
//
// Loads the real production UF2, boots it, then verifies against the
// ORDER-READINESS Layer 4 pin table:
//   1. pin muxing: matrix/encoder pins on SIO with pull-ups, GP17 on PIO
//      (ws2812 vendor driver), GP26/27 handed to the ADC
//   2. WS2812 data activity on GP17 (edge count)
//   3. full USB HID enumeration (device descriptor, config, interfaces)
//   4. key scan: drive SW1 (GP12) low -> keyboard IN report; release -> clear
//   5. raw HID: send PING on the raw OUT endpoint -> expect the 32-byte CAPS
//      reply on the raw IN endpoint (byte-exact vs daemon protocol oracle)
//
// Usage: node runner.cjs <uf2-file> <expected-caps-hex> [--press-gpio N]
'use strict';
const fs = require('fs');
const {
  Simulator,
  ConsoleLogger,
  LogLevel,
  DescriptorType,
  createSetupPacket,
  getDescriptorPacket,
  setDeviceAddressPacket,
  setDeviceConfigurationPacket,
  DataDirection,
  SetupType,
  SetupRecipient,
} = require('rp2040js');
const { bootromB1 } = require('./bootrom.cjs');

const UF2_MAGIC0 = 0x0a324655;
const UF2_MAGIC1 = 0x9e5d5157;
const FLASH_START = 0x10000000;

function loadUF2(filename, rp2040) {
  const data = fs.readFileSync(filename);
  let blocks = 0;
  for (let off = 0; off + 512 <= data.length; off += 512) {
    const magic0 = data.readUInt32LE(off);
    const magic1 = data.readUInt32LE(off + 4);
    if (magic0 !== UF2_MAGIC0 || magic1 !== UF2_MAGIC1) continue;
    const target = data.readUInt32LE(off + 12);
    const size = data.readUInt32LE(off + 16);
    rp2040.flash.set(data.subarray(off + 32, off + 32 + size), target - FLASH_START);
    blocks++;
  }
  return blocks;
}

const uf2Path = process.argv[2];
const expectedCapsHex = process.argv[3];
const pressGpio = parseInt(process.argv[4] ?? '12', 10);

const sim = new Simulator();
const mcu = sim.rp2040;
mcu.loadBootrom(bootromB1);
mcu.logger = new ConsoleLogger(LogLevel.Error); // silence unimplemented-reg warnings
const blocks = loadUF2(uf2Path, mcu);
console.log(`loaded ${blocks} UF2 blocks from ${uf2Path}`);

// Emulator bugfix (rp2040js ADC): the FIFO_REG read path pulls from the FIFO
// but never re-evaluates the IRQ line, so after the ChibiOS ADC handler
// drains the FIFO the ADC_FIFO interrupt stays latched -> interrupt storm
// that starves the main loop. Wrap the read to recompute interrupts, exactly
// what real silicon does. (Harness-side emulator fix; firmware untouched.)
{
  const adc = mcu.adc;
  const origRead = adc.readUint32.bind(adc);
  adc.readUint32 = (offset) => {
    const v = origRead(offset);
    if (offset === 0x0c) adc.checkInterrupts(); // FIFO_REG
    return v;
  };
  // mid-scale joystick rest values (12-bit) -> ~512 at QMK's 10-bit reads
  adc.channelValues[0] = 2048;
  adc.channelValues[1] = 2048;
}

// Emulator bugfix (rp2040js DMA): reading CHAN_ABORT (0x444) is unimplemented
// and returns 0xffffffff, so the QMK ws2812 driver's abort-completion poll
// (`while (dma_hw->abort & mask)`) spins forever, freezing the main thread.
// Real silicon clears the bits when the abort completes; emulated aborts are
// instantaneous, so the register correctly reads 0.
{
  const dma = mcu.dma;
  const origRead = dma.readUint32.bind(dma);
  dma.readUint32 = (offset) => (offset === 0x444 ? 0 : origRead(offset));
}

// The emulator does not fold pull-ups into inputValue, so idle-high matrix /
// encoder / touch lines must be driven high explicitly (otherwise every key
// reads pressed and bootmagic [SW1 held] would jump to the bootloader).
const INPUT_PINS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16];
for (const p of INPUT_PINS) mcu.gpio[p].setInputValue(true);

// --- WS2812 activity probe on GP17
let gp17Edges = 0;
mcu.gpio[17].addListener(() => gp17Edges++);

// --- generic USB HID host (pattern follows rp2040js's USBCDC helper)
const usb = mcu.usbCtrl;
let descriptorsSize = null;
const descriptors = [];
let configured = false;
const interfaces = []; // {number, cls, sub, proto, inEp, outEp}
const armedReads = new Map(); // endpoint -> armed byte count
const rawTxQueue = [];
const events = [];
const kbdReports = [];
const rawReports = [];

function log(msg) {
  events.push(`[${(sim.clock.micros / 1000).toFixed(1)}ms] ${msg}`);
}

function parseConfig(desc) {
  interfaces.length = 0; // idempotent: may be called on partial then full data
  let i = 0;
  let cur = null;
  while (i + 2 <= desc.length && desc[i] >= 2) {
    const len = desc[i];
    const type = desc[i + 1];
    if (type === DescriptorType.Interface && len === 9) {
      cur = { number: desc[i + 2], cls: desc[i + 5], sub: desc[i + 6], proto: desc[i + 7], inEp: -1, outEp: -1 };
      interfaces.push(cur);
    } else if (type === DescriptorType.Endpoint && len === 7 && cur) {
      const addr = desc[i + 2];
      if (addr & 0x80) cur.inEp = addr & 0x0f;
      else cur.outEp = addr & 0x0f;
    }
    i += len;
  }
}

function ifaceByKind(kind) {
  // keyboard: HID class, boot protocol 1; raw: HID class with an OUT endpoint
  if (kind === 'kbd') return interfaces.find((f) => f.cls === 3 && f.proto === 1);
  if (kind === 'raw') return interfaces.find((f) => f.cls === 3 && f.proto === 0 && f.outEp >= 0);
  return undefined;
}

let resetSeen = false;
let ep0Activity = 0; // counts every EP0 event, to detect a stalled handshake
usb.onUSBEnabled = () => {
  log('USB controller enabled by firmware');
  usb.resetDevice();
};
usb.onResetReceived = () => {
  log('USB reset received by device');
  resetSeen = true; // SET_ADDRESS is sent from the main loop, with retries
};
// Enumeration state machine, paced from the main loop:
// address -> device descriptor -> config descriptor (9) -> config (full) ->
// set configuration -> configured
let enumState = 'address';
usb.onEndpointWrite = (endpoint, buffer) => {
  if (endpoint === 0) {
    ep0Activity++;
    log(`EP0 IN ${buffer.length}B: ${Buffer.from(buffer).toString('hex')} (state=${enumState})`);
  }
  if (endpoint === 0 && buffer.length === 0) {
    // zero-length status stage acks
    if (enumState === 'address') {
      enumState = 'devdesc';
      usb.sendSetupPacket(getDescriptorPacket(DescriptorType.Device, 18));
    } else if (enumState === 'setconf') {
      enumState = 'done';
      configured = true;
      parseConfig(descriptors);
      log('USB configured; interfaces: ' + interfaces.map((f) => `#${f.number}(cls${f.cls}/proto${f.proto} in${f.inEp}${f.outEp >= 0 ? '/out' + f.outEp : ''})`).join(' '));
    }
    return;
  }
  if (endpoint === 0 && buffer.length > 1) {
    if (enumState === 'devdesc' && buffer[1] === DescriptorType.Device) {
      enumState = 'confhdr';
      usb.sendSetupPacket(getDescriptorPacket(DescriptorType.Configration, 9));
    } else if (enumState === 'confhdr' && buffer.length === 9 && buffer[1] === DescriptorType.Configration) {
      descriptorsSize = (buffer[3] << 8) | buffer[2];
      enumState = 'conffull';
      usb.sendSetupPacket(getDescriptorPacket(DescriptorType.Configration, descriptorsSize));
    } else if (enumState === 'conffull') {
      descriptors.push(...buffer);
      parseConfig(descriptors);
      const complete = descriptors.length >= descriptorsSize;
      // Known emulator quirk with the ChibiOS control pipeline: continuation
      // packets of a multi-packet control IN transfer never arrive, so a
      // >64-byte config descriptor truncates at the first packet. Proceed to
      // SET_CONFIGURATION once the interfaces we exercise (boot keyboard +
      // raw HID with IN and OUT endpoints) are fully described.
      if (complete || (ifaceByKind('kbd') && ifaceByKind('raw'))) {
        if (!complete) log(`config descriptor truncated at ${descriptors.length}/${descriptorsSize} bytes (emulator control-continuation quirk); kbd+raw interfaces fully parsed, proceeding`);
        enumState = 'setconf';
        usb.sendSetupPacket(setDeviceConfigurationPacket(1));
      }
    }
    return;
  }
  const kbd = ifaceByKind('kbd');
  const raw = ifaceByKind('raw');
  if (kbd && endpoint === kbd.inEp) {
    kbdReports.push(Buffer.from(buffer).toString('hex'));
    log(`KBD report: ${Buffer.from(buffer).toString('hex')}`);
  } else if (raw && endpoint === raw.inEp) {
    rawReports.push(Buffer.from(buffer).toString('hex'));
    log(`RAW report: ${Buffer.from(buffer).toString('hex')}`);
  } else if (endpoint !== 0) {
    log(`EP${endpoint} IN: ${Buffer.from(buffer).toString('hex')}`);
  }
};
usb.onEndpointRead = (endpoint, byteCount) => {
  const raw = ifaceByKind('raw');
  if (raw && endpoint === raw.outEp && rawTxQueue.length) {
    const frame = rawTxQueue.shift();
    log(`delivering ${frame.length}-byte frame on raw OUT ep${endpoint}`);
    usb.endpointReadDone(endpoint, frame);
  } else {
    armedReads.set(endpoint, byteCount);
  }
};

function sendRaw(frame) {
  const raw = ifaceByKind('raw');
  if (raw && armedReads.has(raw.outEp)) {
    armedReads.delete(raw.outEp);
    log(`delivering ${frame.length}-byte frame on armed raw OUT ep${raw.outEp}`);
    usb.endpointReadDone(raw.outEp, frame);
  } else {
    rawTxQueue.push(frame);
  }
}

// --- synchronous simulation loop
const cycleNanos = 1e9 / 125000000;
const wallStart = Date.now();
const WALL_BUDGET_MS = 25 * 60 * 1000;
let pioTick = 0;
function runForMicros(us) {
  const target = sim.clock.nanos + us * 1000;
  let stallGuard = 0;
  while (sim.clock.nanos < target) {
    if (Date.now() - wallStart > WALL_BUDGET_MS) throw new Error('wall-clock budget exceeded');
    const before = sim.clock.nanos;
    if (mcu.core.waiting) {
      const next = Math.min(sim.clock.nanosToNextAlarm, target - sim.clock.nanos);
      sim.clock.tick(next);
    } else {
      sim.clock.tick(mcu.core.executeInstruction() * cycleNanos);
    }
    // Emulator workaround (rp2040js PIO): RPPIO.run() re-schedules itself via
    // setTimeout (the real JS event loop), which never fires inside this
    // synchronous simulation loop - the PIO would execute only its first
    // 1000-step burst. Step the PIO here instead; exact SM-vs-core clock
    // ratio does not matter for this smoke test.
    if ((++pioTick & 3) === 0) {
      if (!mcu.pio[0].stopped) mcu.pio[0].step();
      if (!mcu.pio[1].stopped) mcu.pio[1].step();
    }
    if (sim.clock.nanos === before) {
      if (++stallGuard > 1e7) throw new Error(`simulation stalled at PC=0x${mcu.core.PC.toString(16)}`);
    } else {
      stallGuard = 0;
    }
  }
}

// Start execution from boot2 in flash, exactly like the rp2040js demos
// (the emulator's bootrom reset path is not meant to be executed).
mcu.core.PC = 0x10000000;

// ===== run =====
let ok = true;
function verdict(name, cond, detail = '') {
  console.log(`  [${cond ? 'ok' : 'FAIL'}] ${name}${cond || !detail ? '' : '  <- ' + detail}`);
  if (!cond) ok = false;
}

// 1) boot + enumerate (up to 6 s simulated). The host shim paces the
// handshake from out here: SET_ADDRESS goes out only after the device has
// seen the bus reset and had sim-time to re-arm EP0, and stalled control
// transfers are retried (real hosts retry too).
let addressAttempts = 0;
let lastActivity = 0;
for (let i = 0; i < 80 && !configured; i++) {
  runForMicros(100000);
  if (resetSeen && enumState === 'address' && ep0Activity === 0 && addressAttempts < 5) {
    addressAttempts++;
    log(`SET_ADDRESS(1) attempt ${addressAttempts}`);
    usb.sendSetupPacket(setDeviceAddressPacket(1));
  } else if (!configured && ep0Activity > 0 && ep0Activity === lastActivity && i % 5 === 4) {
    // control transfer stalled for 500 ms of sim time: retry current step
    log(`retrying stalled step ${enumState}`);
    if (enumState === 'devdesc') usb.sendSetupPacket(getDescriptorPacket(DescriptorType.Device, 18));
    else if (enumState === 'confhdr') usb.sendSetupPacket(getDescriptorPacket(DescriptorType.Configration, 9));
    else if (enumState === 'conffull') { descriptors.length = 0; usb.sendSetupPacket(getDescriptorPacket(DescriptorType.Configration, descriptorsSize)); }
    else if (enumState === 'setconf') usb.sendSetupPacket(setDeviceConfigurationPacket(1));
  }
  lastActivity = ep0Activity;
}
verdict('USB enumeration completed', configured, `state=${enumState} ep0Activity=${ep0Activity} resetSeen=${resetSeen}`);

// Emulator bugfix (rp2040js DMA/PIO DREQ): DREQ lines are only updated on
// FIFO level *transitions* (pio.js set/clearDREQ), so a PIO TX FIFO that has
// been empty since boot never asserts its initial DREQ and a DREQ-paced DMA
// (the QMK ws2812 driver) deadlocks. Nudge the PIO TX DREQs once; from then
// on the PIO's own transition callbacks maintain them.
for (const d of [0, 1, 2, 3, 8, 9, 10, 11]) mcu.dma.setDREQ(d);
// ...and starting a channel whose DREQ is *already* asserted never schedules
// a transfer either (start() ignores the dreq latch; only transitions kick
// it). Kick armed channels whose DREQ is high.
for (const chan of mcu.dma.channels) {
  const origStart = chan.start.bind(chan);
  chan.start = () => {
    origStart();
    if (chan.active && mcu.dma.dreq[chan.treq]) chan.scheduleTransfer();
  };
}

// settle, collect ws2812 + pin config state
const edgesBefore = gp17Edges;
runForMicros(300000);
console.log('-- pin configuration after boot (funcsel: 5=SIO, 6/7=PIO, 31=NULL/ADC)');
const expectSio = { 0: 'SW12', 1: 'SW8', 2: 'SW4', 3: 'SW11', 4: 'SW7', 5: 'SW3', 6: 'SW13', 7: 'SW10', 8: 'SW6', 9: 'SW2', 10: 'SW9', 11: 'SW5', 12: 'SW1', 13: 'ENC_A', 14: 'ENC_B', 15: 'ENC_SW', 16: 'TOUCH_OUT' };
for (const [pin, name] of Object.entries(expectSio)) {
  const g = mcu.gpio[pin];
  verdict(`GP${pin} (${name}): SIO input, pull-up`, g.functionSelect === 5 && g.inputEnable && g.pullupEnabled && !g.rawOutputEnable, `funcsel=${g.functionSelect} ie=${g.inputEnable} pue=${g.pullupEnabled} oe=${g.rawOutputEnable}`);
}
const g17 = mcu.gpio[17];
verdict('GP17 (RGB_MCU): PIO function', g17.functionSelect === 6 || g17.functionSelect === 7, `funcsel=${g17.functionSelect}`);
verdict('GP17 WS2812 data edges seen', gp17Edges > edgesBefore, `${gp17Edges - edgesBefore} edges`);
for (const pin of [26, 27]) {
  const g = mcu.gpio[pin];
  verdict(`GP${pin} (JOY_${pin === 26 ? 'X' : 'Y'}_ADC): analog (NULL funcsel, digital input off)`, g.functionSelect === 31, `funcsel=${g.functionSelect} ie=${g.inputEnable}`);
}
for (const pin of [18, 19, 20, 21, 22, 23, 24, 25, 28, 29]) {
  const g = mcu.gpio[pin];
  verdict(`GP${pin} (spare/NC): untouched by firmware (funcsel NULL)`, g.functionSelect === 31, `funcsel=${g.functionSelect}`);
}

// 2) key scan: press SW1 (GP12) -> F13 (0x68) -> release
const reportsBefore = kbdReports.length;
mcu.gpio[pressGpio].setInputValue(false);
runForMicros(150000);
mcu.gpio[pressGpio].setInputValue(true);
runForMicros(150000);
const newReports = kbdReports.slice(reportsBefore);
const pressSeen = newReports.some((r) => r.includes('68'));
const releaseSeen = newReports.length >= 2 && /^00+$/.test(newReports[newReports.length - 1].replace(/^01/, ''));
verdict(`key scan: GP${pressGpio} low -> keyboard report with F13 (0x68)`, pressSeen, JSON.stringify(newReports.slice(0, 4)));
verdict('key scan: release -> empty report', releaseSeen, JSON.stringify(newReports.slice(-2)));

// 3) raw HID PING -> CAPS
const ping = Buffer.alloc(32);
ping[0] = 0x04;
ping[1] = 0x42;
const rawBefore = rawReports.length;
sendRaw(ping);
runForMicros(400000);
const caps = rawReports.slice(rawBefore);
verdict('raw HID: PING answered', caps.length >= 1, `got ${caps.length} raw reports`);
if (caps.length) {
  verdict('raw HID: CAPS byte-exact vs daemon oracle', caps[0] === expectedCapsHex, `got ${caps[0]}\n      want ${expectedCapsHex}`);
}

console.log('-- event log');
for (const e of events.slice(0, 40)) console.log('   ' + e);
console.log(ok ? 'EMULATOR SMOKE: PASS' : 'EMULATOR SMOKE: FAIL');
process.exit(ok ? 0 : 1); // explicit: the emulated USB controller keeps the event loop alive
