// agentpad13 — referee for the protocol-v1 joystick-calibration commands
// (0x50 GET_JOYSTICK / 0x51 SET_CALIBRATION / 0x52 RESET_CALIBRATION) on
// rp2040js, against the REAL shipped UF2.
//
// Sibling of behavior.cjs, which referees the user-visible behavior of the same
// binaries and is deliberately never edited to accommodate this file. Contract
// under test: docs/PROTOCOL-V1-CONTRACT.md. Host counterpart:
// daemon/loudestd/protocol.py (agreement between the two is proven separately by
// firmware/tests/conformance/run_conformance.py, on the host, without hardware).
//
// WHY THIS EXISTS. The v1 redesign replaced a whole separate bring-up firmware
// with three raw-HID commands and one EEPROM block. Everything the owner will
// ever do to calibrate a joystick now rests on four claims:
//
//   1. the board reports its live ADC and its stored calibration truthfully;
//   2. it derives threshold = floor(60% of the smaller half-swing), exactly;
//   3. it rejects a bad calibration TOTALLY — nothing written, ever;
//   4. an accepted calibration SURVIVES A POWER CYCLE.
//
// Claim 4 is the one the whole design rests on and the one that is easiest to
// assume. It is proven here rather than assumed: the calibration is written,
// the emulated flash image is carried across a full MCU restart (new Simulator,
// SRAM zeroed, firmware re-entered at boot2), and the values are read back off
// the rebooted board.
//
// HOW THE GAMEPAD RESCALE IS READ. joystick_axes[] is QMK's runtime-mutable
// axis table (quantum/joystick.h declares it extern non-const; the definition
// generated from keyboard.json links into .data in SRAM). loudest_micro.c
// rewrites it on every calibration change so that the NATIVE HID gamepad mode
// gets the same calibration as the custom arrow/scroll modes. We do not
// hardcode its address: the array is LOCATED AT RUNTIME by searching SRAM for
// the two-record signature keyboard.json generates (GP26 / 0 / 512 / 1023 then
// GP27 / 0 / 512 / 1023), and the hit is then re-proven by watching those exact
// words change when a calibration is accepted.
//
// EMULATOR FIDELITY. Workarounds (a)-(e) are the ones behavior.cjs documents;
// (f) and (g) are additional and both live HERE, never in firmware:
//   (f) rp2040js never auto-clears ADC.CS.START_ONCE, which is self-clearing on
//       real silicon, so ChibiOS's read-modify-write of CS re-triggers a
//       conversion and every adcConvert() lags one sample behind. Switchable
//       with --no-adc-fix (that arm must FAIL, on the ADC-derived checks only).
//   (g) rp2040js models the flash as a read-only array: its SSI peripheral is a
//       stub that discards DR0 writes and always reports RXFLR 0, and IO_QSPI is
//       an UnimplementedPeripheral whose reads return 0xffffffff — which QMK's
//       wear-leveling driver reads as "flash access aborted", so every EEPROM
//       write silently does nothing. This harness attaches a small serial-NOR
//       model (WREN / page-program / sector- and block-erase / read-status) to
//       the SSI for the window in which the driver forces CS low by hand, so
//       writes land in the flash array the XIP read path already serves.
//       Switchable with --no-eeprom (that arm must FAIL, on persistence only).
//
// Usage:  node joystick.cjs [../prebuilt/agentpad13_reference.uf2] [--no-eeprom] [--no-adc-fix]
'use strict';

const fs = require('fs');
const path = require('path');

// Reuse the already-vendored emulator + bootrom from tests/emulator (no new
// install, no network). See firmware/sim/README.md for the one-time setup.
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
const EEPROM_MODEL = !args.includes('--no-eeprom'); // workaround (g)
const ADC_FIX = !args.includes('--no-adc-fix');     // workaround (f)
for (const a of args) {
  if (a.startsWith('--') && !['--no-eeprom', '--no-adc-fix'].includes(a)) {
    console.error(`unknown flag ${a} (expected --no-eeprom or --no-adc-fix)`);
    process.exit(2);
  }
}

// Contract constants — every one of these is a quotation from
// docs/PROTOCOL-V1-CONTRACT.md, not a value read back off the firmware.
const CMD_PING = 0x04;
const CMD_GET = 0x50;
const CMD_SET = 0x51;
const CMD_RESET = 0x52;
const MAGIC_L = 0x4c;
const MAGIC_D = 0x44;
const PROTO_VERSION = 1;
const ADC_MAX = 1023;
const PLACEHOLDER_REST = 512;
const PLACEHOLDER_THRESHOLD = 300;
const MIN_SWING = 100;
// Independent implementation of the contract's rounding rule. Deliberately
// written as floor(x * 60 / 100) rather than as the firmware's (x * 3) / 5 so
// that the two are not the same expression typed twice.
const threshold = (rest, lo, hi) => Math.floor((Math.min(rest - lo, hi - rest) * 60) / 100);

const PIO0_TXF0 = 0x50200010;

// ---------------------------------------------------------------- verdicts
let failures = 0;
let checks = 0;
function verdict(name, cond, detail = '') {
  checks++;
  if (!cond) failures++;
  console.log(`  [${cond ? 'ok' : 'FAIL'}] ${name}${cond || !detail ? '' : '  <- ' + detail}`);
}
function note(msg) { console.log(`  ..   ${msg}`); }

// ---------------------------------------------------------------- UF2
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

// ===========================================================================
// (g) serial-NOR flash model.
//
// QMK's RP2040 wear-leveling backing store (vial-qmk
// platforms/chibios/drivers/wear_leveling/wear_leveling_rp2040_flash.c) READS
// the store straight through XIP — which rp2040js already serves out of
// rp2040.flash — but WRITES it by bit-banging the SSI itself: it forces CS low
// through IO_QSPI's OUTOVER field, pushes command bytes into SSI DR0, and paces
// itself on SSI RXFLR. rp2040js models neither side, so without this the write
// is a no-op and "persistence" would be a claim, not a measurement.
//
// The model is deliberately confined to the window where CS is forced low by
// hand: boot2 and the XIP path drive the SSI with hardware chip-select and are
// left entirely to rp2040js's own stub, exactly as they are today.
// ===========================================================================
function installFlashModel(mcu) {
  const SSI_TXFLR = 0x20, SSI_RXFLR = 0x24, SSI_DR0 = 0x60;
  const QSPI_SS_CTRL = 0x0c;      // ioqspi_hw->io[1].ctrl (SS = chip select)
  const OUTOVER_LOW = 2, OUTOVER_HIGH = 3; // hardware/structs/ioqspi.h
  const stats = { programs: 0, erases: 0, bytes: 0 };

  // --- IO_QSPI: a plain register file. rp2040js ships an
  // UnimplementedPeripheral here, and its 0xffffffff reads make the driver's
  // flash_was_aborted() true, which aborts every flash loop early.
  const regs = new Uint32Array(0x1000 >> 2);
  let csLow = false, cmd = [], rx = [], wel = false;

  function endTransaction() {
    if (cmd.length) {
      const op = cmd[0];
      if (op === 0x06) {                       // WRITE ENABLE (latches WEL)
        wel = true;
      } else if (op === 0x02) {                // PAGE PROGRAM (already applied)
        if (cmd.length > 4) stats.programs++;
        wel = false;
      } else if ((op === 0x20 || op === 0x52 || op === 0xd8) && cmd.length >= 4) {
        const size = op === 0x20 ? 4096 : op === 0x52 ? 32768 : 65536;
        const addr = ((cmd[1] << 16) | (cmd[2] << 8) | cmd[3]) >>> 0;
        const base = addr & ~(size - 1);
        if (wel && base + size <= mcu.flash.length) {
          mcu.flash.fill(0xff, base, base + size);
          stats.erases++;
        }
        wel = false;
      } else if (op === 0xc7 || op === 0x60) { // CHIP ERASE — never expected here
        wel = false;
      }
    }
    cmd = [];
    rx = [];
  }

  mcu.peripherals[0x40018] = {
    readUint32(offset) { return regs[(offset & 0xfff) >> 2] >>> 0; },
    writeUint32(offset, value) {
      const o = offset & 0xfff;
      regs[o >> 2] = value >>> 0;
      if (o === QSPI_SS_CTRL) {
        const outover = (value >>> 8) & 0x3;
        // Both edges start a clean FIFO. Every put_get loop in the driver and in
        // the ROM lives entirely inside one CS state and reads back exactly as
        // many bytes as it wrote, so nothing in flight is ever discarded — but
        // boot2, re-run from RAM after each program, leaves bytes behind, and
        // without this they accumulate until a full FIFO starts DROPPING pushes
        // and the next put_get waits forever for a byte that will never arrive.
        // (Measured: exactly five EEPROM writes succeed, then boot hangs.)
        if (outover === OUTOVER_LOW && !csLow) { csLow = true; cmd = []; rx = []; }
        else if (outover === OUTOVER_HIGH && csLow) { csLow = false; endTransaction(); }
      }
    },
    writeUint32Atomic(offset, value, atomicType) {
      const o = offset & 0xfff;
      const cur = regs[o >> 2] >>> 0;
      const next = atomicType === 1 ? (cur ^ value) >>> 0
        : atomicType === 2 ? (cur | value) >>> 0
          : atomicType === 3 ? (cur & ~value) >>> 0
            : value >>> 0;
      this.writeUint32(o, next);
    },
  };

  // --- SSI: a 16-deep RX FIFO that always answers, plus command interpretation
  // while CS is forced low.
  //
  // The FIFO must answer UNCONDITIONALLY, not only inside a forced-CS window:
  // the bootrom's flash_exit_xip() clocks two 32-clock dummy bursts through the
  // same put_get loop with CS held HIGH, and that loop only ever exits when
  // RXFLR reports bytes or when flash_was_aborted() is true. rp2040js's stock
  // 0xffffffff on IO_QSPI is what made it exit today (permanently "aborted"),
  // so the moment IO_QSPI answers honestly the dummy burst must be answered
  // honestly too — otherwise boot hangs in ROM at 0x1784. Measured, not guessed.
  const ssi = mcu.peripherals[0x18000];
  const origRead = ssi.readUint32.bind(ssi);
  const origWrite = ssi.writeUint32.bind(ssi);
  ssi.readUint32 = (offset) => {
    if (offset === SSI_RXFLR) return rx.length;
    if (offset === SSI_TXFLR) return 0;
    if (offset === SSI_DR0) return rx.length ? rx.shift() : 0;
    return origRead(offset);
  };
  ssi.writeUint32 = (offset, value) => {
    if (offset !== SSI_DR0) { origWrite(offset, value); return; }
    const byte = value & 0xff;
    // The byte clocked back out while this one is clocked in. Only the status
    // registers carry meaning for this driver; everything else reads 0.
    let miso = 0x00;
    if (csLow) {
      cmd.push(byte);
      const op = cmd[0];
      if (cmd.length > 1) {
        if (op === 0x05) miso = 0x00;      // status-1: WIP clear, never busy
        else if (op === 0x35) miso = 0x02; // status-2: QE already set
      }
      if (op === 0x02 && cmd.length >= 5 && wel) {
        // Page program. NOR flash can only clear bits, so AND rather than
        // assign: programming onto un-erased bytes must not look like an erase.
        const addr = ((cmd[1] << 16) | (cmd[2] << 8) | cmd[3]) >>> 0;
        const at = addr + (cmd.length - 5);
        if (at < mcu.flash.length) { mcu.flash[at] &= byte; stats.bytes++; }
      }
    }
    rx.push(miso); // never capped: see the CS-edge comment above
  };
  return stats;
}

// ===========================================================================
// One emulated board. Instantiated twice: the power-cycle test builds a second
// Device seeded with the first one's flash image and nothing else.
// ===========================================================================
class Device {
  constructor(flashSeed) {
    this.sim = new Simulator();
    const mcu = this.sim.rp2040;
    this.mcu = mcu;
    mcu.loadBootrom(bootromB1); // also resets, which fills flash with 0xff
    mcu.logger = new ConsoleLogger(LogLevel.Error);
    this.blocks = loadUF2(UF2_PATH, mcu);
    if (flashSeed) mcu.flash.set(flashSeed); // a power cycle keeps the flash, not the SRAM

    this.flashStats = EEPROM_MODEL ? installFlashModel(mcu) : { programs: 0, erases: 0, bytes: 0 };

    { // (a) ADC FIFO_REG reads never re-evaluate the IRQ line -> interrupt storm.
      const adc = mcu.adc;
      const orig = adc.readUint32.bind(adc);
      adc.readUint32 = (o) => { const v = orig(o); if (o === 0x0c) adc.checkInterrupts(); return v; };
      if (ADC_FIX) { // (f) START_ONCE is self-clearing on silicon, not in rp2040js
        const origW = adc.writeUint32.bind(adc);
        adc.writeUint32 = (o, v) => { origW(o, v); if (o === 0x00) adc.cs &= ~(1 << 2); };
      }
      adc.channelValues[0] = PLACEHOLDER_REST * 4; // 12-bit; QMK reads 10-bit
      adc.channelValues[1] = PLACEHOLDER_REST * 4;
    }
    { // (b) DMA CHAN_ABORT reads are unimplemented -> ws2812 abort-poll spins.
      const dma = mcu.dma;
      const orig = dma.readUint32.bind(dma);
      dma.readUint32 = (o) => (o === 0x444 ? 0 : orig(o));
    }
    // (c) pull-ups are not folded into inputValue. GP0-GP15 idle high (switch to
    // GND); GP16 is the TTP223 output and idles LOW on this board (R10 straps
    // AHLB->GND = active-high), which is behavior.cjs's --touch=board model.
    for (let p = 0; p <= 15; p++) mcu.gpio[p].setInputValue(true);
    mcu.gpio[16].setInputValue(false);
    // (d) starting a DMA channel whose DREQ is already asserted never schedules.
    mcu.dma.channels.forEach((chan) => {
      const origStart = chan.start.bind(chan);
      chan.start = () => {
        origStart();
        if (chan.active && mcu.dma.dreq[chan.treq]) chan.scheduleTransfer();
      };
    });

    // --- USB host shim (same shape as behavior.cjs / tests/emulator/runner.cjs)
    this.descriptors = [];
    this.interfaces = [];
    this.armedReads = new Map();
    this.rawTxQueue = [];
    this.rawReports = [];
    this.configured = false;
    this.resetSeen = false;
    this.ep0Activity = 0;
    this.descriptorsSize = null;
    this.enumState = 'address';
    this.wallStart = Date.now();
    this.pioTick = 0;

    const usb = mcu.usbCtrl;
    this.usb = usb;
    usb.onUSBEnabled = () => usb.resetDevice();
    usb.onResetReceived = () => { this.resetSeen = true; };
    usb.onEndpointWrite = (ep, buf) => this.onEndpointWrite(ep, buf);
    usb.onEndpointRead = (ep, n) => {
      const raw = this.ifaceRaw();
      if (raw && ep === raw.outEp && this.rawTxQueue.length) usb.endpointReadDone(ep, this.rawTxQueue.shift());
      else this.armedReads.set(ep, n);
    };

    mcu.core.PC = 0x10000000; // start at boot2 in flash, as the rp2040js demos do
  }

  parseConfig() {
    const desc = this.descriptors;
    this.interfaces.length = 0;
    let i = 0, cur = null;
    while (i + 2 <= desc.length && desc[i] >= 2) {
      const len = desc[i], type = desc[i + 1];
      if (type === DescriptorType.Interface && len === 9) {
        cur = { number: desc[i + 2], cls: desc[i + 5], proto: desc[i + 7], inEp: -1, outEp: -1 };
        this.interfaces.push(cur);
      } else if (type === DescriptorType.Endpoint && len === 7 && cur) {
        const a = desc[i + 2];
        if (a & 0x80) cur.inEp = a & 0x0f; else cur.outEp = a & 0x0f;
      }
      i += len;
    }
  }
  ifaceKbd() { return this.interfaces.find((f) => f.cls === 3 && f.proto === 1); }
  ifaceRaw() { return this.interfaces.find((f) => f.cls === 3 && f.proto === 0 && f.outEp >= 0); }

  onEndpointWrite(ep, buf) {
    const usb = this.usb;
    if (ep === 0) {
      this.ep0Activity++;
      if (buf.length === 0) {
        if (this.enumState === 'address') { this.enumState = 'devdesc'; usb.sendSetupPacket(getDescriptorPacket(DescriptorType.Device, 18)); }
        else if (this.enumState === 'setconf') { this.enumState = 'done'; this.configured = true; this.parseConfig(); }
        return;
      }
      if (this.enumState === 'devdesc' && buf[1] === DescriptorType.Device) {
        this.enumState = 'confhdr'; usb.sendSetupPacket(getDescriptorPacket(DescriptorType.Configration, 9));
      } else if (this.enumState === 'confhdr' && buf.length === 9) {
        this.descriptorsSize = (buf[3] << 8) | buf[2];
        this.enumState = 'conffull'; usb.sendSetupPacket(getDescriptorPacket(DescriptorType.Configration, this.descriptorsSize));
      } else if (this.enumState === 'conffull') {
        this.descriptors.push(...buf); this.parseConfig();
        // Emulator quirk: continuation packets of a multi-packet control IN never
        // arrive, so the 91-byte config descriptor truncates at 64. The keyboard
        // and raw interfaces are complete inside that first packet.
        if (this.descriptors.length >= this.descriptorsSize || (this.ifaceKbd() && this.ifaceRaw())) {
          this.enumState = 'setconf'; usb.sendSetupPacket(setDeviceConfigurationPacket(1));
        }
      }
      return;
    }
    const raw = this.ifaceRaw();
    if (raw && ep === raw.inEp) this.rawReports.push(Buffer.from(buf));
  }

  run(us) {
    const CYCLE_NS = 1e9 / 125000000;
    const WALL_BUDGET_MS = 30 * 60 * 1000;
    const sim = this.sim, mcu = this.mcu;
    const target = sim.clock.nanos + us * 1000;
    while (sim.clock.nanos < target) {
      if (Date.now() - this.wallStart > WALL_BUDGET_MS) throw new Error('wall-clock budget exceeded');
      if (mcu.core.waiting) sim.clock.tick(Math.min(sim.clock.nanosToNextAlarm, target - sim.clock.nanos));
      else sim.clock.tick(mcu.core.executeInstruction() * CYCLE_NS);
      // (e) RPPIO.run() re-schedules via setTimeout, which never fires inside a
      //     synchronous loop; step the PIO from here instead.
      if ((++this.pioTick & 3) === 0) {
        if (!mcu.pio[0].stopped) mcu.pio[0].step();
        if (!mcu.pio[1].stopped) mcu.pio[1].step();
      }
    }
  }

  boot() {
    let addressAttempts = 0, lastActivity = 0;
    const usb = this.usb;
    for (let i = 0; i < 80 && !this.configured; i++) {
      this.run(100000);
      if (this.resetSeen && this.enumState === 'address' && this.ep0Activity === 0 && addressAttempts < 5) {
        addressAttempts++; usb.sendSetupPacket(setDeviceAddressPacket(1));
      } else if (!this.configured && this.ep0Activity > 0 && this.ep0Activity === lastActivity && i % 5 === 4) {
        if (this.enumState === 'devdesc') usb.sendSetupPacket(getDescriptorPacket(DescriptorType.Device, 18));
        else if (this.enumState === 'confhdr') usb.sendSetupPacket(getDescriptorPacket(DescriptorType.Configration, 9));
        else if (this.enumState === 'conffull') { this.descriptors.length = 0; usb.sendSetupPacket(getDescriptorPacket(DescriptorType.Configration, this.descriptorsSize)); }
        else if (this.enumState === 'setconf') usb.sendSetupPacket(setDeviceConfigurationPacket(1));
      }
      lastActivity = this.ep0Activity;
    }
    if (!this.configured) return false;
    for (const d of [0, 1, 2, 3, 8, 9, 10, 11]) this.mcu.dma.setDREQ(d);
    this.run(400000);
    return true;
  }

  sendRaw(frame) {
    const raw = this.ifaceRaw();
    if (raw && this.armedReads.has(raw.outEp)) {
      this.armedReads.delete(raw.outEp);
      this.usb.endpointReadDone(raw.outEp, frame);
    } else {
      this.rawTxQueue.push(frame);
    }
  }

  // Send one 32-byte frame and return the last raw-HID reply it produced, or
  // null if the board answered nothing (which is a legal outcome for a frame
  // the firmware must ignore).
  ask(bytes, us = 500000) {
    const before = this.rawReports.length;
    const frame = Buffer.alloc(32);
    (bytes instanceof Buffer ? bytes : Buffer.from(bytes)).copy(frame);
    this.sendRaw(frame);
    this.run(us);
    const got = this.rawReports.slice(before);
    return got.length ? got[got.length - 1] : null;
  }

  adc10(x, y, settle = 250000) {
    this.mcu.adc.channelValues[0] = x * 4;
    this.mcu.adc.channelValues[1] = y * 4;
    this.run(settle);
  }
}

// ---------------------------------------------------------------- helpers
const le16 = (v) => [v & 0xff, (v >> 8) & 0xff];
const rd16 = (b, at) => b[at] | (b[at + 1] << 8);
const setFrame = (rest_x, rest_y, min_x, max_x, min_y, max_y) =>
  [CMD_SET, ...le16(rest_x), ...le16(rest_y), ...le16(min_x), ...le16(max_x), ...le16(min_y), ...le16(max_y)];
const getFrame = (token) => [CMD_GET, token];

// Decode a 0x50 reply into the contract's field names, so every assertion below
// reads like the contract table rather than like byte arithmetic.
function decodeJoystick(b) {
  if (!b) return null;
  return {
    cmd: b[0], token: b[1], magic0: b[2], magic1: b[3],
    live_x: rd16(b, 4), live_y: rd16(b, 6), cal_state: b[8],
    rest_x: rd16(b, 9), rest_y: rd16(b, 11),
    min_x: rd16(b, 13), max_x: rd16(b, 15),
    min_y: rd16(b, 17), max_y: rd16(b, 19),
    threshold_x: rd16(b, 21), threshold_y: rd16(b, 23),
    padding: Array.from(b.subarray(25, 32)),
    hex: b.toString('hex'),
  };
}
const summarise = (j) => j
  ? `cal_state=${j.cal_state} rest=${j.rest_x},${j.rest_y} x=${j.min_x}..${j.max_x} y=${j.min_y}..${j.max_y} thr=${j.threshold_x},${j.threshold_y}`
  : 'no reply';

// Locate joystick_axes[] in SRAM by its generated content rather than by symbol
// address, so this harness stays correct across builds and keymaps. Layout:
// pin_t input_pin (4) + min_digit (2) + mid_digit (2) + max_digit (2) + pad (2).
const AXIS_STRIDE = 12;
function findJoystickAxes(mcu) {
  const s = mcu.sram;
  const dv = new DataView(s.buffer, s.byteOffset, s.byteLength);
  const rec = (o) => ({
    pin: dv.getUint32(o, true), min: dv.getUint16(o + 4, true),
    mid: dv.getUint16(o + 6, true), max: dv.getUint16(o + 8, true),
  });
  const hits = [];
  for (let o = 0; o + 2 * AXIS_STRIDE <= s.length; o += 4) {
    const a = rec(o);
    if (a.pin !== 26 || a.min !== 0 || a.mid !== PLACEHOLDER_REST || a.max !== ADC_MAX) continue;
    const b = rec(o + AXIS_STRIDE);
    if (b.pin !== 27 || b.min !== 0 || b.mid !== PLACEHOLDER_REST || b.max !== ADC_MAX) continue;
    hits.push(0x20000000 + o);
  }
  return hits;
}
function readAxes(mcu, base) {
  const out = [];
  for (let i = 0; i < 2; i++) {
    const o = base + i * AXIS_STRIDE;
    const w1 = mcu.readUint32(o + 4) >>> 0;
    const w2 = mcu.readUint32(o + 8) >>> 0;
    out.push({ min: w1 & 0xffff, mid: (w1 >>> 16) & 0xffff, max: w2 & 0xffff });
  }
  return out;
}
const axesText = (ax) => ax.map((a, i) => `[${i}] ${a.min}/${a.mid}/${a.max}`).join('  ');

// The wear-levelling backing store: the last 8 KiB of the 2 MiB image QMK
// builds for (vial-qmk platforms/chibios/drivers/wear_leveling/
// wear_leveling_rp2040_flash_config.h -> WEAR_LEVELING_RP2040_FLASH_BASE =
// PICO_FLASH_SIZE_BYTES - WEAR_LEVELING_BACKING_SIZE). Snapshotted whenever a
// frame must write NOTHING.
const EE_BASE = 0x200000 - 0x2000;
const EE_SIZE = 0x2000;
const eeSnapshot = (mcu) => Buffer.from(mcu.flash.subarray(EE_BASE, EE_BASE + EE_SIZE));
const eeChangedBytes = (a, b) => {
  let n = 0;
  for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) n++;
  return n;
};

// ================================================================ 0. boot
console.log(`agentpad13 joystick/protocol-v1 sim — ${path.basename(UF2_PATH)}`);
const dev = new Device(null);
console.log(`loaded ${dev.blocks} UF2 blocks`);
console.log(EEPROM_MODEL
  ? 'eeprom model: ON — SSI serial-NOR responder attached, EEPROM writes reach the flash image'
  : 'eeprom model: OFF — rp2040js stock, every EEPROM write is silently discarded (--no-eeprom)');
console.log(ADC_FIX
  ? 'adc fix: on — ADC.CS.START_ONCE cleared after each write, as real silicon does'
  : 'adc fix: OFF — conversions lag one sample, as stock rp2040js does (--no-adc-fix)');
console.log('');

console.log('0. boot + USB enumeration');
verdict('USB configured', dev.boot(), `state=${dev.enumState}`);
if (!dev.configured) { console.log('\nJOYSTICK SIM: FAIL (cannot proceed without USB)'); process.exit(1); }
note(`interfaces: ${dev.interfaces.map((f) => `#${f.number} cls${f.cls}/proto${f.proto} in${f.inEp}${f.outEp >= 0 ? '/out' + f.outEp : ''}`).join('  ')}`);

// ================================================================ 1. CAPS
console.log('\n1. CAPS (0x04 PING) — the version byte that says this board speaks v1');
{
  const caps = dev.ask([CMD_PING, 0x42]);
  verdict('PING answers', caps !== null, 'no reply');
  if (caps) {
    note(`CAPS: ${caps.toString('hex')}`);
    verdict('CAPS header 0x04/token/L/D',
      caps[0] === CMD_PING && caps[1] === 0x42 && caps[2] === MAGIC_L && caps[3] === MAGIC_D,
      caps.subarray(0, 4).toString('hex'));
    verdict(`CAPS protocol_version is ${PROTO_VERSION}`, caps[4] === PROTO_VERSION, `byte 4 = ${caps[4]}`);
    verdict('CAPS led_count 24, layer_count 8, features 0x1f (v0 fields unmoved)',
      caps[5] === 24 && caps[6] === 8 && caps[7] === 0x1f,
      `led=${caps[5]} layers=${caps[6]} feat=0x${caps[7].toString(16)}`);
  }
}

// ================================================================ 2. 0x50 framing
console.log('\n2. 0x50 GET_JOYSTICK on an UNCALIBRATED board — framing, live ADC, placeholders');
{
  dev.adc10(800, 200);
  const j = decodeJoystick(dev.ask(getFrame(0x37)));
  verdict('0x50 answers', j !== null, 'no reply');
  if (j) {
    note(`reply: ${j.hex}`);
    verdict('bytes 0..3 echo 0x50, the token, and the L/D magic',
      j.cmd === CMD_GET && j.token === 0x37 && j.magic0 === MAGIC_L && j.magic1 === MAGIC_D,
      `${j.cmd.toString(16)} ${j.token.toString(16)} ${j.magic0.toString(16)} ${j.magic1.toString(16)}`);
    verdict('live_x / live_y are the two ADC channels, not one channel twice',
      j.live_x === 800 && j.live_y === 200, `live_x=${j.live_x} live_y=${j.live_y} (injected 800/200)`);
    verdict('cal_state = 0 (uncalibrated)', j.cal_state === 0, `cal_state=${j.cal_state}`);
    verdict(`placeholders: rest ${PLACEHOLDER_REST}/${PLACEHOLDER_REST}, min 0/0, max ${ADC_MAX}/${ADC_MAX}`,
      j.rest_x === PLACEHOLDER_REST && j.rest_y === PLACEHOLDER_REST && j.min_x === 0 && j.max_x === ADC_MAX && j.min_y === 0 && j.max_y === ADC_MAX,
      summarise(j));
    verdict(`placeholder thresholds ${PLACEHOLDER_THRESHOLD}/${PLACEHOLDER_THRESHOLD}`,
      j.threshold_x === PLACEHOLDER_THRESHOLD && j.threshold_y === PLACEHOLDER_THRESHOLD,
      `${j.threshold_x}/${j.threshold_y}`);
    verdict('bytes 25..31 are zero padding', j.padding.every((v) => v === 0), j.padding.join(','));
  }
  // a second read with a different token and different ADC: the reply must track
  const j2 = (dev.adc10(123, 987), decodeJoystick(dev.ask(getFrame(0x99))));
  verdict('a second 0x50 echoes the NEW token and the NEW live values',
    j2 !== null && j2.token === 0x99 && j2.live_x === 123 && j2.live_y === 987,
    j2 ? `token=0x${j2.token.toString(16)} live=${j2.live_x},${j2.live_y}` : 'no reply');
}

// ================================================ 3. locate joystick_axes[]
console.log('\n3. the native HID gamepad axis table — located in SRAM by its content');
// Two records match the keyboard.json signature and BOTH should: joystick_axes[]
// itself, and js_axes_shipped[] — the copy loudest_micro.c snapshots at boot so
// 0x52 can restore the placeholders without a second copy of those numbers in C.
// Which is which is decided in section 6, by which one MOVES when a calibration
// is accepted. That is a stronger identification than any symbol address.
let CANDIDATES = [];
let AXES = null;
{
  CANDIDATES = findJoystickAxes(dev.mcu);
  verdict('the GP26/GP27 0-512-1023 axis signature is present in SRAM', CANDIDATES.length >= 1,
    'no axis table found — the joystick config never reached .data');
  for (const c of CANDIDATES) note(`candidate @0x${c.toString(16)} = ${axesText(readAxes(dev.mcu, c))}`);
}

// ================================================================ 4. rejections
console.log('\n4. 0x51 SET_CALIBRATION rejections — status 1, and NOTHING written');
{
  const cases = [
    // A well-formed frame carrying bad numbers MUST be answered with status 1.
    // Silence would be a different (and unspecified) behavior, so "no reply" is
    // a failure here, not a pass.
    ['a value above 1023 (max_x = 1500)', setFrame(500, 500, 200, 1500, 200, 800), false],
    ['rest_x >= max_x (rest 900, max 800)', setFrame(900, 500, 200, 800, 200, 800), false],
    ['min_y >= rest_y (min 600, rest 500)', setFrame(500, 500, 200, 800, 600, 800), false],
    ['half-swing 99 — one count below the contract minimum', setFrame(500, 500, 500 - (MIN_SWING - 1), 800, 200, 800), false],
    // A frame too short to contain the fields is the one case where silence is
    // an acceptable answer: the firmware must not read past the buffer, and
    // either ignoring it or rejecting it satisfies "nothing was written".
    ['a truncated frame: 0x51 with only 8 of its 13 payload bytes', Buffer.from([CMD_SET, ...le16(500), ...le16(500), ...le16(200), 0x00]), true],
  ];
  for (const [label, frame, silenceOk] of cases) {
    const before = eeSnapshot(dev.mcu);
    const r = dev.ask(frame);
    const rejected = r === null ? silenceOk : (r[0] === CMD_SET && r[1] === 1);
    verdict(`rejects ${label}`, rejected, r ? r.subarray(0, 2).toString('hex') : 'no reply');
    verdict(`  ...and wrote nothing to the EEPROM block`,
      eeChangedBytes(before, eeSnapshot(dev.mcu)) === 0,
      `${eeChangedBytes(before, eeSnapshot(dev.mcu))} byte(s) of the backing store changed`);
  }
  const j = decodeJoystick(dev.ask(getFrame(0x38)));
  verdict('after every rejection the board is still UNCALIBRATED, on the placeholders',
    j !== null && j.cal_state === 0 && j.threshold_x === PLACEHOLDER_THRESHOLD && j.threshold_y === PLACEHOLDER_THRESHOLD,
    summarise(j));
  const moved = CANDIDATES.filter((c) => {
    const ax = readAxes(dev.mcu, c);
    return !(ax[0].min === 0 && ax[0].mid === PLACEHOLDER_REST && ax[0].max === ADC_MAX &&
      ax[1].min === 0 && ax[1].mid === PLACEHOLDER_REST && ax[1].max === ADC_MAX);
  });
  verdict('a rejected calibration did not move the gamepad axes either', moved.length === 0,
    moved.map((c) => `0x${c.toString(16)} -> ${axesText(readAxes(dev.mcu, c))}`).join(' | '));
}

// ============================================ 5. the 99/100 boundary, from below
console.log(`\n5. the half-swing boundary — ${MIN_SWING - 1} rejects, ${MIN_SWING} accepts`);
const BOUNDARY = { rest_x: 500, rest_y: 520, min_x: 500 - MIN_SWING, max_x: 500 + MIN_SWING, min_y: 520 - MIN_SWING, max_y: 520 + MIN_SWING };
{
  const r = dev.ask(setFrame(BOUNDARY.rest_x, BOUNDARY.rest_y, BOUNDARY.min_x, BOUNDARY.max_x, BOUNDARY.min_y, BOUNDARY.max_y));
  verdict(`accepts a calibration whose half-swings are exactly ${MIN_SWING}`,
    r !== null && r[0] === CMD_SET && r[1] === 0, r ? r.subarray(0, 2).toString('hex') : 'no reply');
  const j = decodeJoystick(dev.ask(getFrame(0x3a)));
  const wantTx = threshold(BOUNDARY.rest_x, BOUNDARY.min_x, BOUNDARY.max_x);
  const wantTy = threshold(BOUNDARY.rest_y, BOUNDARY.min_y, BOUNDARY.max_y);
  verdict(`  ...and derives thresholds ${wantTx}/${wantTy} from it`,
    j !== null && j.cal_state === 1 && j.threshold_x === wantTx && j.threshold_y === wantTy, summarise(j));
  // Put it back so the acceptance section starts from a known-clean board.
  const z = dev.ask([CMD_RESET]);
  verdict('0x52 clears it again before the next section', z !== null && z[0] === CMD_RESET && z[1] === 0,
    z ? z.subarray(0, 2).toString('hex') : 'no reply');
}

// ================================================================ 6. acceptance
// x: rest 500, min 180, max 860 -> half-swings 320 / 360 -> smaller 320 -> 192
// y: rest 520, min 200, max 900 -> half-swings 320 / 380 -> smaller 320 -> 192
const CAL = { rest_x: 500, rest_y: 520, min_x: 180, max_x: 860, min_y: 200, max_y: 900 };
const WANT_TX = threshold(CAL.rest_x, CAL.min_x, CAL.max_x);
const WANT_TY = threshold(CAL.rest_y, CAL.min_y, CAL.max_y);
console.log('\n6. 0x51 accepted — stored verbatim, thresholds derived, gamepad rescaled');
{
  const eeBefore = eeSnapshot(dev.mcu);
  const r = dev.ask(setFrame(CAL.rest_x, CAL.rest_y, CAL.min_x, CAL.max_x, CAL.min_y, CAL.max_y), 900000);
  verdict('0x51 replies [0x51, 0] = accepted and written',
    r !== null && r[0] === CMD_SET && r[1] === 0, r ? r.subarray(0, 2).toString('hex') : 'no reply');
  const j = decodeJoystick(dev.ask(getFrame(0x39)));
  if (j) note(`reply: ${j.hex}`);
  verdict('0x50 now reports cal_state = 1', j !== null && j.cal_state === 1, summarise(j));
  verdict('0x50 hands back exactly the six values that were sent',
    j !== null && j.rest_x === CAL.rest_x && j.rest_y === CAL.rest_y && j.min_x === CAL.min_x && j.max_x === CAL.max_x && j.min_y === CAL.min_y && j.max_y === CAL.max_y,
    summarise(j));
  note(`contract: threshold = floor(60% of min(rest-min, max-rest)) = floor(60% of ${Math.min(CAL.rest_x - CAL.min_x, CAL.max_x - CAL.rest_x)}) = ${WANT_TX} (x), ${WANT_TY} (y)`);
  verdict(`thresholds are floor(60% of the smaller half-swing) = ${WANT_TX}/${WANT_TY}`,
    j !== null && j.threshold_x === WANT_TX && j.threshold_y === WANT_TY,
    j ? `${j.threshold_x}/${j.threshold_y}` : 'no reply');
  const rescaled = CANDIDATES.filter((c) => {
    const ax = readAxes(dev.mcu, c);
    return ax[0].min === CAL.min_x && ax[0].mid === CAL.rest_x && ax[0].max === CAL.max_x &&
      ax[1].min === CAL.min_y && ax[1].mid === CAL.rest_y && ax[1].max === CAL.max_y;
  });
  for (const c of CANDIDATES) note(`candidate @0x${c.toString(16)} after 0x51: ${axesText(readAxes(dev.mcu, c))}`);
  verdict('exactly one of the axis records was rescaled in SRAM to the stored calibration',
    rescaled.length === 1, `${rescaled.length} of ${CANDIDATES.length} candidate(s) hold the calibration`);
  if (rescaled.length === 1) {
    AXES = rescaled[0];
    note(`=> joystick_axes[] is @0x${AXES.toString(16)}; the record(s) that did not move are the shipped-placeholder snapshot 0x52 restores from`);
  }
  const stillPlaceholder = CANDIDATES.filter((c) => c !== AXES).every((c) => {
    const ax = readAxes(dev.mcu, c);
    return ax[0].mid === PLACEHOLDER_REST && ax[1].mid === PLACEHOLDER_REST && ax[0].max === ADC_MAX;
  });
  verdict('the shipped-placeholder snapshot was NOT overwritten by the calibration',
    CANDIDATES.length < 2 || stillPlaceholder, 'the snapshot moved too — 0x52 would have nothing to restore');
  const changed = eeChangedBytes(eeBefore, eeSnapshot(dev.mcu));
  note(`EEPROM backing store: ${changed} byte(s) changed, ${dev.flashStats.programs} page program(s), ${dev.flashStats.erases} erase(s)`);
  verdict('an ACCEPTED calibration did write to the EEPROM backing store', changed > 0,
    'the backing store is byte-identical — nothing was persisted');
}

// ================================================================ 7. power cycle
console.log('\n7. POWER CYCLE — the calibration must survive losing all SRAM');
{
  const image = dev.mcu.flash.slice(); // the flash chip is what a power cycle keeps
  const boot2 = new Device(image);
  const ok = boot2.boot();
  verdict('the rebooted board enumerates', ok, `state=${boot2.enumState}`);
  if (ok) {
    note('fresh Simulator: SRAM zeroed, core re-entered at boot2, only the flash image carried over');
    const j = decodeJoystick(boot2.ask(getFrame(0x5a)));
    if (j) note(`reply after reboot: ${j.hex}`);
    verdict('after the power cycle the board still reports cal_state = 1',
      j !== null && j.cal_state === 1, summarise(j));
    verdict('the six stored values survived the power cycle unchanged',
      j !== null && j.rest_x === CAL.rest_x && j.rest_y === CAL.rest_y && j.min_x === CAL.min_x && j.max_x === CAL.max_x && j.min_y === CAL.min_y && j.max_y === CAL.max_y,
      summarise(j));
    verdict(`the thresholds are re-derived to ${WANT_TX}/${WANT_TY} on the rebooted board`,
      j !== null && j.threshold_x === WANT_TX && j.threshold_y === WANT_TY,
      j ? `${j.threshold_x}/${j.threshold_y}` : 'no reply');
    // Same binary, so joystick_axes[] sits at the same SRAM address; what must
    // differ is its CONTENT, which the boot-time load rebuilt from the EEPROM.
    const ax = AXES === null ? null : readAxes(boot2.mcu, AXES);
    if (ax) note(`joystick_axes[] @0x${AXES.toString(16)} after reboot: ${axesText(ax)}`);
    verdict('the gamepad axes come up already calibrated after the power cycle',
      ax !== null &&
      ax[0].min === CAL.min_x && ax[0].mid === CAL.rest_x && ax[0].max === CAL.max_x &&
      ax[1].min === CAL.min_y && ax[1].mid === CAL.rest_y && ax[1].max === CAL.max_y,
      ax ? axesText(ax) : 'joystick_axes[] was never identified');
  }
}

// ================================================================ 8. 0x52
console.log('\n8. 0x52 RESET_CALIBRATION — back to the placeholders, with no reboot');
{
  const r = dev.ask([CMD_RESET], 900000);
  verdict('0x52 replies [0x52, 0x00]', r !== null && r[0] === CMD_RESET && r[1] === 0x00,
    r ? r.subarray(0, 2).toString('hex') : 'no reply');
  const j = decodeJoystick(dev.ask(getFrame(0x3b)));
  verdict('cal_state reverts to 0 immediately, without a reboot',
    j !== null && j.cal_state === 0, summarise(j));
  verdict(`the placeholders are back: rest ${PLACEHOLDER_REST}, span 0..${ADC_MAX}, threshold ${PLACEHOLDER_THRESHOLD}`,
    j !== null && j.rest_x === PLACEHOLDER_REST && j.rest_y === PLACEHOLDER_REST &&
    j.min_x === 0 && j.max_x === ADC_MAX && j.min_y === 0 && j.max_y === ADC_MAX &&
    j.threshold_x === PLACEHOLDER_THRESHOLD && j.threshold_y === PLACEHOLDER_THRESHOLD,
    summarise(j));
  if (AXES) {
    const ax = readAxes(dev.mcu, AXES);
    note(`joystick_axes[] after 0x52: ${axesText(ax)}`);
    verdict('the gamepad axes are restored to the keyboard.json placeholders 0/512/1023',
      ax[0].min === 0 && ax[0].mid === PLACEHOLDER_REST && ax[0].max === ADC_MAX &&
      ax[1].min === 0 && ax[1].mid === PLACEHOLDER_REST && ax[1].max === ADC_MAX,
      axesText(ax));
  }
  // And the wipe is persistent too: reboot once more and it must still be gone.
  const image = dev.mcu.flash.slice();
  const boot3 = new Device(image);
  if (boot3.boot()) {
    const j3 = decodeJoystick(boot3.ask(getFrame(0x5b)));
    verdict('the wipe survives a power cycle as well (the board stays uncalibrated)',
      j3 !== null && j3.cal_state === 0 && j3.threshold_x === PLACEHOLDER_THRESHOLD, summarise(j3));
  } else {
    verdict('the wipe survives a power cycle as well (the board stays uncalibrated)', false, 'reboot did not enumerate');
  }
}

// ================================================================ 9. v0 intact
console.log('\n9. v0 REGRESSION — the four v0 commands still answer exactly as before');
{
  const caps = dev.ask([CMD_PING, 0x11]);
  verdict('PING still answers a byte-exact CAPS after all of the above',
    caps !== null && caps.toString('hex') === `0411${MAGIC_L.toString(16)}${MAGIC_D.toString(16)}0118081f${'0'.repeat(48)}`,
    caps ? caps.toString('hex') : 'no reply');
  const before = dev.rawReports.length;
  dev.sendRaw(Buffer.concat([Buffer.from([0x03]), Buffer.alloc(31)])); // CLEAR
  dev.run(400000);
  verdict('CLEAR is still a silent command (no reply frame)', dev.rawReports.length === before,
    `${dev.rawReports.length - before} unexpected reply frame(s)`);
}

// ============================================ 10. SW14 on-board calibration
// The whole routine, driven end to end with NO host involvement: the board is
// told nothing but "the button is pressed" and "the stick is here". Everything
// else -- centring, the swing envelope, validation, derivation, the EEPROM
// write -- happens on the device.
//
// HOW SW14 IS PRESENTED. SW14 is the BOOTSEL button: it connects net BOOTSEL to
// GND and R6 (1k) ties BOOTSEL to QSPI_CS, so the firmware reads it by briefly
// overriding QSPI_CS to an input and sampling sio.gpio_hi_in bit 1. rp2040js
// models IO_QSPI as an UnimplementedPeripheral (rp2040.js:139), so the OEOVER
// override itself is a no-op here -- but gpio_hi_in IS modelled and reads
// mcu.qspi[n].inputValue (sio.js:119-126), which is exactly what the firmware
// samples. inputValue is `rawInputValue && inputEnable` (gpio-pin.js:122) and
// rp2040js leaves the QSPI pad's IE bit clear, so the pad must be enabled here
// before a button state can be presented at all.
//
// MEASURED, and load-bearing for every other section of this file: with IE
// clear, gpio_hi_in bit 1 reads 0 forever, which is "SW14 HELD" to an active-low
// read. Sections 0-9 above, and the whole of behavior.cjs, are nevertheless
// completely unaffected -- because the firmware refuses to arm until it has
// SEEN A RELEASE (selfcal_seen_release in loudest_micro.c). That guard is not a
// simulator accommodation: a board executing this firmware has ALWAYS seen SW14
// released, since holding SW14 at power-up enters the mask ROM instead of our
// code. The emulator simply never releases it, so the routine stays idle.
const SW14_QSPI_INDEX = 1;
const sw14 = {
  enable: (mcu) => { mcu.qspi[SW14_QSPI_INDEX].padValue |= 0x40; }, // PADS_QSPI IE
  press: (mcu) => mcu.qspi[SW14_QSPI_INDEX].setInputValue(false),   // pulled to GND via R6
  release: (mcu) => mcu.qspi[SW14_QSPI_INDEX].setInputValue(true),
};

// Instrument the QSPI_CS ctrl register so the interrupts-disabled window can be
// timed. rp2040.js:249-251 splits an address into atomicType = (addr & 0x3000)
// >> 12 and offset = addr & 0xfff, so the firmware's atomic SET alias arrives as
// (offset 0x00c, type 2) and its CLR alias as (offset 0x00c, type 3). 0x0c is
// io[1].ctrl (io[0]: status 0x00 / ctrl 0x04; io[1]: status 0x08 / ctrl 0x0c).
function watchSw14Window(mcu) {
  const stat = { windows: [] };
  let open = null;
  const p = mcu.peripherals[0x40018];
  // WRAP, NEVER REPLACE. installFlashModel() above has already put its own full
  // IO_QSPI register-file model at this key, and the ENTIRE EEPROM emulation
  // hangs off it: it watches OUTOVER (ctrl bits 8-9) on this same io[1].ctrl
  // register to detect the flash chip-select edges that frame every SPI
  // transaction. Assigning over its writeUint32Atomic silently destroys that,
  // and the failure is not a clean error -- the board enumerates and then hangs
  // on its first EEPROM access, because endTransaction() never runs and the SSI
  // FIFO fills until a put_get waits forever for a byte that never arrives.
  // That is exactly the hazard installFlashModel's own comment documents.
  // We only READ the value on its way past, so chain to the real handler.
  // (OEOVER is bits 12-13 and OUTOVER is bits 8-9, so the two observers look at
  // disjoint fields of the same register and cannot confuse each other.)
  const chain = p.writeUint32Atomic.bind(p);
  p.writeUint32Atomic = (off, val, type) => {
    if (off === 0x00c) {
      if (type === 2 && val === 0x2000) open = mcu.core.cycles;             // OEOVER := DISABLE
      else if (type === 3 && val === 0x3000 && open !== null) {             // OEOVER := NORMAL
        stat.windows.push(mcu.core.cycles - open);
        open = null;
      }
    }
    return chain(off, val, type);
  };
  return stat;
}

// Drive one complete on-board calibration. Every dwell is generously longer
// than the firmware constant it has to clear, because this harness must never
// depend on landing inside a timing window.
//   SELFCAL_ARM_MS 1000 | SELFCAL_CENTER_MS 2000 | SELFCAL_SWING_MS 10000
//   SELFCAL_POLL_MS 100 (SW14) | SELFCAL_SAMPLE_MS 10 (ADC)
function runSelfCal(dev, rest, sweep) {
  const mcu = dev.mcu;
  sw14.enable(mcu);
  sw14.release(mcu);
  dev.adc10(rest[0], rest[1], 400000); // let it SEE a release; park the stick at rest
  sw14.press(mcu);
  dev.run(1400000);                    // >= 1 s of held polls -> ARMED
  sw14.release(mcu);
  dev.run(300000);                     // ARMED waits for the release -> CENTER
  // CENTRE: hold dead still, so a 400 ms stability window has ZERO spread and
  // its mean is exactly `rest` -- which makes the stored value predictable to
  // the count, and therefore comparable byte-for-byte against the 0x51 path.
  dev.adc10(rest[0], rest[1], 2600000);
  // SWING: visit each extreme long enough for the 100 Hz sampler to catch it.
  for (const [x, y] of sweep) dev.adc10(x, y, 500000);
  // Run out the rest of the 10 s swing, the validation + EEPROM write, and the
  // result display, ending back in IDLE.
  dev.run(11000000);
}

console.log('\n10. SW14 ON-BOARD CALIBRATION — the whole routine, no host involved');
const SELF_SWEEP = [[CAL.min_x, CAL.rest_y], [CAL.max_x, CAL.rest_y], [CAL.rest_x, CAL.min_y], [CAL.rest_x, CAL.max_y]];
let selfEE = null;
{
  const self = new Device(null);
  const win = watchSw14Window(self.mcu);
  if (!self.boot()) {
    verdict('the on-board-calibration board enumerates', false, `state=${self.enumState}`);
  } else {
    const before = decodeJoystick(self.ask(getFrame(0x60)));
    verdict('it starts UNCALIBRATED (placeholders in force)',
      before !== null && before.cal_state === 0, summarise(before));
    const eeBefore = eeSnapshot(self.mcu);

    runSelfCal(self, [CAL.rest_x, CAL.rest_y], SELF_SWEEP);

    // --- the interrupts-disabled window of sw14_pressed(), measured on the
    // real instruction stream.
    //
    // EXPECT ~12021 CYCLES HERE, AND EXPECT THAT TO BE ~14% LOW. The
    // hardware-accurate figure is 14016 cycles == 112.1 us at 125 MHz, counted
    // by hand off the function's disassembly; this emulator reports 12021 ==
    // 96.2 us. The gap is entirely rp2040js's branch model and NOT a difference
    // in the firmware:
    //   * a taken branch costs `deltaCycles++` here, i.e. 2 cycles
    //     (cortex-m0-core.js:636 for Bcc, :648 for B)
    //   * real Cortex-M0+ takes 3 (1 + 2 for the pipeline refill)
    // The settle spin runs two taken branches per iteration, so rp2040js
    // under-counts by 2 cycles x 1000 iterations = 2000; the observed gap is
    // 1995, the missing 5 being the non-loop tail. Everything else agrees (base
    // 1/instruction, SRAM ldr/str +1, SIO +0, APB write +4).
    //
    // TRUST 112.1 us, not 96.2 us, for any argument about real hardware. Both
    // are far under the guard below, and both are ~3 orders of magnitude under
    // the flash-erase window this firmware already masks interrupts for on every
    // Vial keymap save (wear_leveling_rp2040_flash.c:185-203).
    if (win.windows.length) {
      const avg = win.windows.reduce((a, b) => a + b, 0) / win.windows.length;
      const lo = Math.min(...win.windows), hi = Math.max(...win.windows);
      note(`sw14_pressed() critical section: ${win.windows.length} samples, ` +
        `min=${lo} max=${hi} avg=${avg.toFixed(0)} cycles = ${(avg / 125).toFixed(1)} us at 125 MHz`);
      // Not a tight equality: this guards against a REGRESSION that balloons the
      // window (an added call, a longer spin), not against small model drift.
      verdict('the interrupts-disabled SW14 window stays under 200 us',
        hi / 125 < 200, `max ${(hi / 125).toFixed(1)} us`);
    } else {
      verdict('the SW14 read actually overrode QSPI_CS (OEOVER set then cleared)', false,
        'no OEOVER set/clear pair was ever observed — the button was never polled');
    }

    const j = decodeJoystick(self.ask(getFrame(0x61)));
    if (j) note(`after the routine: ${summarise(j)}`);
    verdict('the board calibrated ITSELF — cal_state is now 1', j !== null && j.cal_state === 1, summarise(j));
    verdict(`rest is the mean of the held-still window: ${CAL.rest_x}/${CAL.rest_y}`,
      j !== null && j.rest_x === CAL.rest_x && j.rest_y === CAL.rest_y, summarise(j));
    verdict(`the swing envelope was captured: x ${CAL.min_x}..${CAL.max_x}, y ${CAL.min_y}..${CAL.max_y}`,
      j !== null && j.min_x === CAL.min_x && j.max_x === CAL.max_x && j.min_y === CAL.min_y && j.max_y === CAL.max_y,
      summarise(j));
    verdict(`thresholds derived by the contract's floor(60%): ${WANT_TX}/${WANT_TY}`,
      j !== null && j.threshold_x === WANT_TX && j.threshold_y === WANT_TY,
      j ? `${j.threshold_x}/${j.threshold_y}` : 'no reply');
    const ax = AXES === null ? null : readAxes(self.mcu, AXES);
    if (ax) note(`joystick_axes[] after the on-board routine: ${axesText(ax)}`);
    verdict('the NATIVE HID gamepad was rescaled too, not just the custom modes',
      ax !== null &&
      ax[0].min === CAL.min_x && ax[0].mid === CAL.rest_x && ax[0].max === CAL.max_x &&
      ax[1].min === CAL.min_y && ax[1].mid === CAL.rest_y && ax[1].max === CAL.max_y,
      ax ? axesText(ax) : 'joystick_axes[] was never identified');
    selfEE = eeSnapshot(self.mcu);
    const changed = eeChangedBytes(eeBefore, selfEE);
    note(`EEPROM backing store: ${changed} byte(s) changed, ${self.flashStats.programs} page program(s)`);
    verdict('the on-board routine PERSISTED its result with no host and no daemon',
      changed > 0 && self.flashStats.programs > 0, `${changed} bytes, ${self.flashStats.programs} programs`);
  }
}

// ---- 10b. the whole point: one code path, not two -------------------------
console.log('\n10b. SW14 vs 0x51 — the same six numbers must produce the SAME BYTES');
{
  const host = new Device(null);
  if (!host.boot() || selfEE === null) {
    verdict('the 0x51 comparison board enumerates', false, 'cannot compare');
  } else {
    const r = host.ask(setFrame(CAL.rest_x, CAL.rest_y, CAL.min_x, CAL.max_x, CAL.min_y, CAL.max_y), 900000);
    verdict('0x51 with those same six values is accepted', r !== null && r[1] === 0,
      r ? `status=${r[1]}` : 'no reply');
    const hostEE = eeSnapshot(host.mcu);
    const diff = eeChangedBytes(selfEE, hostEE);
    note(`board-calibrated vs host-calibrated backing store: ${diff} differing byte(s) of ${EE_SIZE}`);
    // Both boards booted from an identical pristine image and performed exactly
    // one calibration write, so an identical write must leave an identical
    // store. This is what proves loudest_micro.c has ONE js_cal_store() and not
    // a second, drifting implementation behind the button.
    verdict('the EEPROM image is BYTE-IDENTICAL whether SW14 or 0x51 wrote it',
      diff === 0, `${diff} byte(s) differ`);
    const jh = decodeJoystick(host.ask(getFrame(0x62)));
    verdict('and both report identical stored values and thresholds',
      jh !== null && jh.rest_x === CAL.rest_x && jh.rest_y === CAL.rest_y &&
      jh.min_x === CAL.min_x && jh.max_x === CAL.max_x && jh.min_y === CAL.min_y && jh.max_y === CAL.max_y &&
      jh.threshold_x === WANT_TX && jh.threshold_y === WANT_TY, summarise(jh));
  }
}

// ---- 10c. a failed routine must write NOTHING -----------------------------
console.log('\n10c. A FAILED on-board run — total rejection, nothing written');
{
  const bad = new Device(null);
  if (!bad.boot()) {
    verdict('the failed-run board enumerates', false, `state=${bad.enumState}`);
  } else {
    const eeBefore = eeSnapshot(bad.mcu);
    const programsBefore = bad.flashStats.programs;
    // A stick that barely moves: +/-50 counts, under the contract's minimum
    // credible half-swing of 100. Everything else about the run is identical to
    // the successful one, so this isolates VALIDATION as the thing that rejects.
    const R = [CAL.rest_x, CAL.rest_y];
    runSelfCal(bad, R, [[R[0] - 50, R[1]], [R[0] + 50, R[1]], [R[0], R[1] - 50], [R[0], R[1] + 50]]);
    const j = decodeJoystick(bad.ask(getFrame(0x63)));
    if (j) note(`after the failed run: ${summarise(j)}`);
    verdict('the board is still UNCALIBRATED after a failed run', j !== null && j.cal_state === 0, summarise(j));
    verdict(`the placeholders are untouched (rest ${PLACEHOLDER_REST}, threshold ${PLACEHOLDER_THRESHOLD})`,
      j !== null && j.rest_x === PLACEHOLDER_REST && j.rest_y === PLACEHOLDER_REST &&
      j.threshold_x === PLACEHOLDER_THRESHOLD && j.threshold_y === PLACEHOLDER_THRESHOLD, summarise(j));
    const changed = eeChangedBytes(eeBefore, eeSnapshot(bad.mcu));
    note(`EEPROM backing store after the failed run: ${changed} byte(s) changed, ` +
      `${bad.flashStats.programs - programsBefore} page program(s)`);
    verdict('a REJECTED on-board calibration wrote NOTHING to the EEPROM at all',
      changed === 0 && bad.flashStats.programs === programsBefore,
      `${changed} bytes changed, ${bad.flashStats.programs - programsBefore} programs`);
  }
}

// ================================================================ done
console.log('');
console.log(`eeprom model: ${EEPROM_MODEL ? 'on' : 'OFF'}   adc fix: ${ADC_FIX ? 'on' : 'OFF'}   checks: ${checks}   failures: ${failures}`);
if (failures && EEPROM_MODEL && ADC_FIX) {
  console.log('NOTE: both emulator workarounds are ON, so a failure here is the firmware or');
  console.log('      this harness, not rp2040js. Re-run with --no-eeprom (persistence must');
  console.log('      then fail, and only persistence) or --no-adc-fix (the live-ADC checks');
  console.log('      must then fail) to confirm the harness still discriminates.');
}
if (!EEPROM_MODEL) {
  console.log('NOTE: --no-eeprom is the counterfactual arm. rp2040js stock discards every');
  console.log('      flash write, so an EEPROM-backed calibration cannot survive a power');
  console.log('      cycle. This arm MUST fail; if it passes, the persistence checks are');
  console.log('      not measuring persistence.');
}
console.log(failures === 0 ? 'JOYSTICK SIM: PASS' : 'JOYSTICK SIM: FAIL');
process.exit(failures === 0 ? 0 : 1); // explicit: the USB controller keeps the loop alive
