#!/usr/bin/env python3
"""Generate the Loudest Micro Rev A flat KiCad-9 schematic + project.

Every value traces to docs/open-agent-macropad-spec.md sec 3/4,
research/03-electrical-pcb-dossier.md, the RP2040 minimal design guide, or the
0xCB-Helios cross-check (datasheet-fact pinouts only; CC-BY-SA, checking ref).
DRAFT - pending human review. Footprints for switches/sockets/LEDs/encoder/
joystick are recorded as fields to be bound at layout (marbastlib etc.).
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kschem import Schematic, PITCH

OUTDIR = sys.argv[1] if len(sys.argv) > 1 else "."

s = Schematic(project="loudest-micro", paper="A1")

# ---------------------------------------------------------------- footprints
FP = dict(
    R="Resistor_SMD:R_0402_1005Metric",
    C="Capacitor_SMD:C_0402_1005Metric",
    C0805="Capacitor_SMD:C_0805_2012Metric",
    RP2040="Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm",
    FLASH="Package_SO:SOIC-8_5.23x5.23mm_P1.27mm",
    LDO="Package_TO_SOT_SMD:SOT-23-5",
    SOT236="Package_TO_SOT_SMD:SOT-23-6",
    XTAL="Crystal:Crystal_SMD_Abracon_ABM8-4Pin_3.2x2.5mm",
    USBC="Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
    FUSE="Fuse:Fuse_1812_4532Metric",
    SOD323="Diode_SMD:D_SOD-323",
    ENC="Rotary_Encoder:RotaryEncoder_Alps_EC11E-Switch_Vertical_H20mm  # TBD bind at layout",
    JOY="loudest:Joystick_PSP_Slider  # TBD Phase-1 part select",
    KEY="marbastlib-mx:SW_MX_HS_Combined_pre-mirrored  # TBD bind at layout",
    LEDK="marbastlib:LED_SK6812MINI-E_ReverseMount  # TBD bind at layout",
    LEDS="marbastlib:LED_SK6812-SIDE_4020  # TBD bind at layout",
    TACT="Button_Switch_SMD:SW_SPST_PTS645  # generic tact",
    HDR="Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical",
    TP="TestPoint:TestPoint_Pad_D1.5mm",
)

# ---------------------------------------------------------------- symbol defs
def P(n, name, t):
    return (str(n), name, t)

s.define_symbol("Device:R", [P(1, "~", "passive"), P(2, "~", "passive")])
s.define_symbol("Device:C", [P(1, "~", "passive"), P(2, "~", "passive")])
s.define_symbol("Device:Crystal_GND24",
                [P(1, "1", "passive"), P(2, "2", "passive"),
                 P(3, "3", "passive"), P(4, "4", "passive")])
s.define_symbol("Device:Fuse_PTC", [P(1, "1", "passive"), P(2, "2", "power_out")])
s.define_symbol("Diode:TVS", [P(1, "A", "passive"), P(2, "K", "passive")])
s.define_symbol("Switch:SW_Push", [P(1, "1", "passive"), P(2, "2", "passive")])
s.define_symbol("Switch:RotaryEncoder_EC11",
                [P("A", "A", "passive"), P("B", "B", "passive"),
                 P("C", "C", "passive"), P("S1", "S1", "passive"),
                 P("S2", "S2", "passive")])
s.define_symbol("LED:SK6812",
                [P(1, "VDD", "power_in"), P(2, "DOUT", "output"),
                 P(3, "VSS", "power_in"), P(4, "DIN", "input")])
s.define_symbol("Joystick:PSP_Slider",
                [P(1, "XA", "passive"), P(2, "XW", "passive"), P(3, "XB", "passive"),
                 P(4, "YA", "passive"), P(5, "YW", "passive"), P(6, "YB", "passive")])
s.define_symbol("Connector:TestPoint", [P(1, "1", "passive")])
s.define_symbol("Connector:Conn_1x08",
                [P(n, str(n), "passive") for n in range(1, 9)])

# power symbols
for net in ["GND", "+3V3", "+5V", "+1V1", "VBUS"]:
    s.define_power_symbol(net)
s.define_power_symbol("PWR_FLAG", etype="power_out")

# RP2040 QFN-56 (pin map verified vs KiCad-official symbol via 0xCB-Helios)
RP_PINS = [
    P(1,"IOVDD","power_in"),   P(2,"GPIO0","bidirectional"),  P(3,"GPIO1","bidirectional"),
    P(4,"GPIO2","bidirectional"),P(5,"GPIO3","bidirectional"),P(6,"GPIO4","bidirectional"),
    P(7,"GPIO5","bidirectional"),P(8,"GPIO6","bidirectional"),P(9,"GPIO7","bidirectional"),
    P(10,"IOVDD","power_in"),   P(11,"GPIO8","bidirectional"), P(12,"GPIO9","bidirectional"),
    P(13,"GPIO10","bidirectional"),P(14,"GPIO11","bidirectional"),P(15,"GPIO12","bidirectional"),
    P(16,"GPIO13","bidirectional"),P(17,"GPIO14","bidirectional"),P(18,"GPIO15","bidirectional"),
    P(19,"TESTEN","input"),     P(20,"XIN","input"),           P(21,"XOUT","output"),
    P(22,"IOVDD","power_in"),   P(23,"DVDD","power_in"),       P(24,"SWCLK","bidirectional"),
    P(25,"SWDIO","bidirectional"),P(26,"RUN","input"),         P(27,"GPIO16","bidirectional"),
    P(28,"GPIO17","bidirectional"),P(29,"GPIO18","bidirectional"),P(30,"GPIO19","bidirectional"),
    P(31,"GPIO20","bidirectional"),P(32,"GPIO21","bidirectional"),P(33,"IOVDD","power_in"),
    P(34,"GPIO22","bidirectional"),P(35,"GPIO23","bidirectional"),P(36,"GPIO24","bidirectional"),
    P(37,"GPIO25","bidirectional"),P(38,"GPIO26_ADC0","bidirectional"),P(39,"GPIO27_ADC1","bidirectional"),
    P(40,"GPIO28_ADC2","bidirectional"),P(41,"GPIO29_ADC3","bidirectional"),P(42,"IOVDD","power_in"),
    P(43,"ADC_AVDD","power_in"),P(44,"VREG_VIN","power_in"),   P(45,"VREG_VOUT","power_out"),
    P(46,"USB_DM","bidirectional"),P(47,"USB_DP","bidirectional"),P(48,"USB_VDD","power_in"),
    P(49,"IOVDD","power_in"),   P(50,"DVDD","power_in"),       P(51,"QSPI_SD3","bidirectional"),
    P(52,"QSPI_SCLK","output"), P(53,"QSPI_SD0","bidirectional"),P(54,"QSPI_SD2","bidirectional"),
    P(55,"QSPI_SD1","bidirectional"),P(56,"QSPI_SS_N","output"),P(57,"GND","power_in"),
]
s.define_symbol("MCU:RP2040", RP_PINS)

s.define_symbol("Memory:W25Q128JVS",
    [P(1,"~CS","input"),P(2,"DO_IO1","bidirectional"),P(3,"~WP_IO2","bidirectional"),
     P(4,"GND","power_in"),P(5,"DI_IO0","bidirectional"),P(6,"CLK","input"),
     P(7,"~HOLD_IO3","bidirectional"),P(8,"VCC","power_in")])
s.define_symbol("Regulator:AP2112K-3.3",
    [P(1,"VIN","power_in"),P(2,"GND","power_in"),P(3,"EN","input"),
     P(4,"NC","no_connect"),P(5,"VOUT","power_out")])
s.define_symbol("ESD:USBLC6-2SC6",
    [P(1,"IO1","bidirectional"),P(2,"GND","power_in"),P(3,"IO2","bidirectional"),
     P(4,"IO2","bidirectional"),P(5,"VBUS","power_in"),P(6,"IO1","bidirectional")])
s.define_symbol("Logic:SN74LVC1T45",
    [P(1,"VCCA","power_in"),P(2,"GND","power_in"),P(3,"A","bidirectional"),
     P(4,"B","bidirectional"),P(5,"DIR","input"),P(6,"VCCB","power_in")])
s.define_symbol("Touch:TTP223",
    [P(1,"Q","output"),P(2,"VSS","power_in"),P(3,"I","input"),
     P(4,"AHLB","input"),P(5,"VDD","power_in"),P(6,"TOG","input")])
# USB-C HRO TYPE-C-31-M-12 (pads verified vs KiCad footprint)
s.define_symbol("Connector:USB_C_HRO",
    [P("A1","GND","passive"),P("A4","VBUS","power_out"),P("A5","CC1","passive"),
     P("A6","DP1","passive"),P("A7","DN1","passive"),P("A8","SBU1","passive"),
     P("A9","VBUS","passive"),P("A12","GND","passive"),
     P("B1","GND","passive"),P("B4","VBUS","passive"),P("B5","CC2","passive"),
     P("B6","DP2","passive"),P("B7","DN2","passive"),P("B8","SBU2","passive"),
     P("B9","VBUS","passive"),P("B12","GND","passive"),P("S1","SHIELD","passive")])

# ---------------------------------------------------------------- placement
COLW = 150.0
cursors = {}
def put(col, ref, lib, val, pinmap, **kw):
    x = 40.0 + col * COLW
    y = cursors.get(col, 45.0)
    s.place(ref, lib, val, x, y, pinmap, **kw)
    nrows = max(len(pinmap), 1)
    # advance by symbol height estimate (half the pins per side) + gap
    rows = (len([1 for _ in pinmap]) + 1) // 2
    cursors[col] = y + rows * PITCH + 22.0
    return x, y

# ===== Block 1: RP2040 core =====
put(0, "U1", "MCU:RP2040", "RP2040", {
    1:"+3V3",10:"+3V3",22:"+3V3",33:"+3V3",42:"+3V3",49:"+3V3",
    23:"+1V1",50:"+1V1",19:"GND",57:"GND",
    20:"XIN",21:"XOUT",24:"SWCLK",25:"SWDIO",26:"RUN",
    43:"+3V3",44:"+3V3",45:"+1V1",46:"DM",47:"DP",48:"+3V3",
    51:"QSPI_SD3",52:"QSPI_CLK",53:"QSPI_SD0",54:"QSPI_SD2",55:"QSPI_SD1",56:"QSPI_CS",
    2:"SW1",3:"SW2",4:"SW3",5:"SW4",6:"SW5",7:"SW6",8:"SW7",9:"SW8",
    11:"SW9",12:"SW10",13:"SW11",14:"SW12",15:"SW13",
    16:"ENC_A",17:"ENC_B",18:"ENC_SW",27:"TOUCH_OUT",28:"RGB_MCU",
    29:"SDA",30:"SCL",31:"GP20",32:"GP21",
    34:"NC",35:"NC",36:"NC",37:"NC",41:"NC",
    38:"JOY_X_ADC",39:"JOY_Y_ADC",40:"GP28",
}, footprint=FP["RP2040"], mpn="RP2040", lcsc="C2040", jlc="Extended",
   descr="Dual Cortex-M0+ MCU, QFN-56 (RPi minimal design)")

# RP2040 decoupling (col 1): 6x IOVDD 100n, 2x DVDD 100n, ADC_AVDD, USB_VDD, 2x VREG 1u
dec = []
for i in range(1, 7):  dec.append((f"C{i}", "100n", "+3V3"))     # IOVDD
dec.append(("C7","100n","+1V1")); dec.append(("C8","100n","+1V1"))  # DVDD
dec.append(("C9","100n","+3V3"))    # ADC_AVDD (pin43)
dec.append(("C10","100n","+3V3"))   # USB_VDD (pin48)
for ref,val,rail in dec:
    put(1, ref, "Device:C", val, {1:rail,2:"GND"}, footprint=FP["C"],
        mpn="CL05B104KO5NNNC", lcsc="C1525", jlc="Basic", descr="MLCC 0402")
put(1, "C11", "Device:C", "1u", {1:"+3V3",2:"GND"}, footprint=FP["C"],
    mpn="CL05A105KA5NNNC", lcsc="C52923", jlc="Basic", descr="VREG_VIN decoupling")
put(1, "C12", "Device:C", "1u", {1:"+1V1",2:"GND"}, footprint=FP["C"],
    mpn="CL05A105KA5NNNC", lcsc="C52923", jlc="Basic", descr="VREG_VOUT decoupling")

# ===== Block 2: Flash + crystal + boot (col 2) =====
put(2, "U2", "Memory:W25Q128JVS", "W25Q128JVSIQ", {
    1:"QSPI_CS",2:"QSPI_SD1",3:"QSPI_SD2",4:"GND",
    5:"QSPI_SD0",6:"QSPI_CLK",7:"QSPI_SD3",8:"+3V3"},
    footprint=FP["FLASH"], mpn="W25Q128JVSIQ", lcsc="C97521", jlc="Extended",
    descr="16 MB QSPI flash")
put(2, "C13", "Device:C", "100n", {1:"+3V3",2:"GND"}, footprint=FP["C"],
    mpn="CL05B104KO5NNNC", lcsc="C1525", jlc="Basic", descr="flash decoupling")
put(2, "R6", "Device:R", "1k", {1:"QSPI_CS",2:"BOOTSEL"}, footprint=FP["R"],
    mpn="0402WGF1001TCE", lcsc="C11702", jlc="Basic", descr="BOOTSEL series")
put(2, "SW14", "Switch:SW_Push", "BOOT", {1:"BOOTSEL",2:"GND"}, footprint=FP["TACT"],
    mpn="TS-1187A", lcsc="C318884", jlc="Basic", descr="BOOTSEL tact")
put(2, "Y1", "Device:Crystal_GND24", "12MHz ABM8-272-T3",
    {1:"XIN",3:"XOUT_XTAL",2:"GND",4:"GND"}, footprint=FP["XTAL"],
    mpn="ABM8-272-T3", lcsc="C20625731", jlc="Extended",
    descr="12 MHz 10pF crystal (RPi guide)")
put(2, "R5", "Device:R", "1k", {1:"XOUT",2:"XOUT_XTAL"}, footprint=FP["R"],
    mpn="0402WGF1001TCE", lcsc="C11702", jlc="Basic", descr="XOUT series (RPi guide)")
put(2, "C18", "Device:C", "15p", {1:"XIN",2:"GND"}, footprint=FP["C"],
    mpn="CL05C150JB5NNNC", lcsc="C1548", jlc="Basic", descr="crystal load cap")
put(2, "C19", "Device:C", "15p", {1:"XOUT_XTAL",2:"GND"}, footprint=FP["C"],
    mpn="CL05C150JB5NNNC", lcsc="C1548", jlc="Basic", descr="crystal load cap")

# ===== Block 3: Power / USB-C front end (col 3) =====
put(3, "J1", "Connector:USB_C_HRO", "USB-C", {
    "A1":"GND","A12":"GND","B1":"GND","B12":"GND","S1":"GND",
    "A4":"VBUS","A9":"VBUS","B4":"VBUS","B9":"VBUS",
    "A5":"CC1","B5":"CC2",
    "A6":"PORT_DP","B6":"PORT_DP","A7":"PORT_DM","B7":"PORT_DM",
    "A8":"NC","B8":"NC"}, footprint=FP["USBC"],
    mpn="TYPE-C-31-M-12", lcsc="C165948", jlc="Extended", descr="USB-C 2.0 receptacle")
put(3, "R1", "Device:R", "5.1k", {1:"CC1",2:"GND"}, footprint=FP["R"],
    mpn="0402WGF5101TCE", lcsc="C25905", jlc="Basic", descr="CC1 pulldown (own pin)")
put(3, "R2", "Device:R", "5.1k", {1:"CC2",2:"GND"}, footprint=FP["R"],
    mpn="0402WGF5101TCE", lcsc="C25905", jlc="Basic", descr="CC2 pulldown (own pin)")
put(3, "F1", "Device:Fuse_PTC", "500mA", {1:"VBUS",2:"+5V"}, footprint=FP["FUSE"],
    mpn="MF-MSMF050-2", lcsc="C17313", jlc="Extended", descr="PTC polyfuse 500mA hold")
put(3, "U4", "ESD:USBLC6-2SC6", "USBLC6-2SC6", {
    6:"PORT_DP",1:"USB_DP",4:"PORT_DM",3:"USB_DM",5:"+5V",2:"GND"},
    footprint=FP["SOT236"], mpn="USBLC6-2SC6", lcsc="C7519", jlc="Extended",
    descr="USB ESD array")
put(3, "R3", "Device:R", "27", {1:"USB_DP",2:"DP"}, footprint=FP["R"],
    mpn="0402WGF270JTCE", lcsc="C25100", jlc="Basic", descr="D+ series")
put(3, "R4", "Device:R", "27", {1:"USB_DM",2:"DM"}, footprint=FP["R"],
    mpn="0402WGF270JTCE", lcsc="C25100", jlc="Basic", descr="D- series")
put(3, "D1", "Diode:TVS", "SD05C", {1:"GND",2:"+5V"}, footprint=FP["SOD323"],
    mpn="SD05C", lcsc="C907858", jlc="Extended", dnp=True, descr="VBUS TVS (optional, DNP)")
put(3, "U3", "Regulator:AP2112K-3.3", "AP2112K-3.3", {
    1:"+5V",2:"GND",3:"+5V",4:"NC",5:"+3V3"}, footprint=FP["LDO"],
    mpn="AP2112K-3.3TRG1", lcsc="C51118", jlc="Extended", descr="3.3V 600mA LDO")
put(3, "C14", "Device:C", "1u", {1:"+5V",2:"GND"}, footprint=FP["C"],
    mpn="CL05A105KA5NNNC", lcsc="C52923", jlc="Basic", descr="LDO Cin")
put(3, "C15", "Device:C", "1u", {1:"+3V3",2:"GND"}, footprint=FP["C"],
    mpn="CL05A105KA5NNNC", lcsc="C52923", jlc="Basic", descr="LDO Cout")
put(3, "C16", "Device:C", "10u", {1:"+5V",2:"GND"}, footprint=FP["C0805"],
    mpn="CL21A106KOQNNNE", lcsc="C15850", jlc="Basic", descr="+5V bulk")
put(3, "C17", "Device:C", "10u", {1:"+3V3",2:"GND"}, footprint=FP["C0805"],
    mpn="CL21A106KOQNNNE", lcsc="C15850", jlc="Basic", descr="+3V3 bulk")

# ===== Block 4: RUN/SWD/expansion (col 4) =====
put(4, "R7", "Device:R", "10k", {1:"+3V3",2:"RUN"}, footprint=FP["R"],
    mpn="0402WGF1002TCE", lcsc="C25744", jlc="Basic", descr="RUN pull-up")
put(4, "SW15", "Switch:SW_Push", "RESET", {1:"RUN",2:"GND"}, footprint=FP["TACT"],
    mpn="TS-1187A", lcsc="C318884", jlc="Basic", descr="RESET tact")
put(4, "TP1", "Connector:TestPoint", "SWCLK", {1:"SWCLK"}, footprint=FP["TP"],
    mpn="TestPad", lcsc="", jlc="n/a", descr="SWD test pad")
put(4, "TP2", "Connector:TestPoint", "SWDIO", {1:"SWDIO"}, footprint=FP["TP"],
    mpn="TestPad", lcsc="", jlc="n/a", descr="SWD test pad")
put(4, "TP3", "Connector:TestPoint", "3V3", {1:"+3V3"}, footprint=FP["TP"],
    mpn="TestPad", lcsc="", jlc="n/a", descr="power test pad")
put(4, "TP4", "Connector:TestPoint", "GND", {1:"GND"}, footprint=FP["TP"],
    mpn="TestPad", lcsc="", jlc="n/a", descr="ground test pad")
put(4, "R8", "Device:R", "4.7k", {1:"+3V3",2:"SDA"}, footprint=FP["R"],
    mpn="0402WGF4701TCE", lcsc="C25900", jlc="Basic", descr="I2C SDA pull-up")
put(4, "R9", "Device:R", "4.7k", {1:"+3V3",2:"SCL"}, footprint=FP["R"],
    mpn="0402WGF4701TCE", lcsc="C25900", jlc="Basic", descr="I2C SCL pull-up")
put(4, "J2", "Connector:Conn_1x08", "EXPANSION", {
    1:"+3V3",2:"GND",3:"SDA",4:"SCL",5:"GP20",6:"GP21",7:"GP28",8:"+5V"},
    footprint=FP["HDR"], mpn="PinHeader_1x08", lcsc="", jlc="n/a",
    descr="I2C(GP18/19)+3V3+GND+spares GP20/21/GP28+5V")

# ===== Block 5: switches SW1..SW13 (col 5) =====
for k in range(1, 14):
    put(5, f"SW{k}", "Switch:SW_Push", "MX_Hotswap", {1:f"SW{k}",2:"GND"},
        footprint=FP["KEY"], mpn="Kailh_CPG151101S11", lcsc="C2803348",
        jlc="Standard-Only(back)", descr=f"direct-pin key {k} (GP{k-1}), MX hotswap")

# ===== Block 6: encoder / touch / joystick / shifter (col 6) =====
put(6, "RE1", "Switch:RotaryEncoder_EC11", "EC11", {
    "A":"ENC_A","B":"ENC_B","C":"GND","S1":"ENC_SW","S2":"GND"},
    footprint=FP["ENC"], mpn="PEC11R-4215F-S0024", lcsc="C143790",
    jlc="n/a(hand-solder)", descr="rotary encoder + push (A/B=GP13/14, SW=GP15)")
put(6, "U6", "Touch:TTP223", "TTP223", {
    1:"TOUCH_OUT",2:"GND",3:"TOUCH_PAD",4:"TOUCH_AHLB",5:"+3V3",6:"GND"},
    footprint=FP["SOT236"], mpn="TTP223-BA6", lcsc="C80757", jlc="Extended",
    descr="cap touch (OUT->GP16, TOG=GND direct mode)")
put(6, "C22", "Device:C", "100n", {1:"+3V3",2:"GND"}, footprint=FP["C"],
    mpn="CL05B104KO5NNNC", lcsc="C1525", jlc="Basic", descr="TTP223 decoupling")
put(6, "R10", "Device:R", "0R", {1:"TOUCH_AHLB",2:"GND"}, footprint=FP["R"],
    mpn="0402WGF0000TCE", lcsc="C17168", jlc="Basic",
    descr="AHLB strap=GND (active-high); move to +3V3 for active-low")
put(6, "TP5", "Connector:TestPoint", "TOUCHPAD", {1:"TOUCH_PAD"}, footprint=FP["TP"],
    mpn="CopperPour", lcsc="", jlc="n/a", descr="14x14 sensing copper pour")
put(6, "C25", "Device:C", "DNP", {1:"TOUCH_PAD",2:"GND"}, footprint=FP["C"],
    mpn="C_0402", lcsc="", jlc="Basic", dnp=True, descr="touch sensitivity cap (DNP, tune 0-50pF)")
put(6, "JS1", "Joystick:PSP_Slider", "PSP-Slider", {
    1:"+3V3",2:"JOY_X",3:"GND",4:"+3V3",5:"JOY_Y",6:"GND"},
    footprint=FP["JOY"], mpn="Adafruit-444_or_clone", lcsc="", jlc="n/a(hand-solder)",
    descr="2-axis planar joystick (Phase-1 select)")
put(6, "R11", "Device:R", "1k", {1:"JOY_X",2:"JOY_X_ADC"}, footprint=FP["R"],
    mpn="0402WGF1001TCE", lcsc="C11702", jlc="Basic", descr="joystick X RC series")
put(6, "R12", "Device:R", "1k", {1:"JOY_Y",2:"JOY_Y_ADC"}, footprint=FP["R"],
    mpn="0402WGF1001TCE", lcsc="C11702", jlc="Basic", descr="joystick Y RC series")
put(6, "C23", "Device:C", "100n", {1:"JOY_X_ADC",2:"GND"}, footprint=FP["C"],
    mpn="CL05B104KO5NNNC", lcsc="C1525", jlc="Basic", descr="joystick X RC cap")
put(6, "C24", "Device:C", "100n", {1:"JOY_Y_ADC",2:"GND"}, footprint=FP["C"],
    mpn="CL05B104KO5NNNC", lcsc="C1525", jlc="Basic", descr="joystick Y RC cap")

# ===== Block 7: level shifter (col 7) =====
put(7, "U5", "Logic:SN74LVC1T45", "SN74LVC1T45", {
    1:"+3V3",2:"GND",3:"RGB_MCU",4:"RGB_D00",5:"+3V3",6:"+5V"},
    footprint=FP["SOT236"], mpn="SN74LVC1T45DBVR", lcsc="C7843", jlc="Extended",
    descr="1-bit level shifter (A=3V3 GP17, B=5V LEDs, DIR=A->B)")
put(7, "C20", "Device:C", "100n", {1:"+3V3",2:"GND"}, footprint=FP["C"],
    mpn="CL05B104KO5NNNC", lcsc="C1525", jlc="Basic", descr="shifter VCCA decoupling")
put(7, "C21", "Device:C", "100n", {1:"+5V",2:"GND"}, footprint=FP["C"],
    mpn="CL05B104KO5NNNC", lcsc="C1525", jlc="Basic", descr="shifter VCCB decoupling")

# ===== Block 8: LED chain (cols 8..) 13 MINI-E + 1 indicator + 10 SIDE =====
# chain nets: RGB_D00 (shifter B -> LED1 DIN), RGB_Dk = LEDk.DOUT -> LED(k+1).DIN
NLED = 24
for k in range(1, NLED + 1):
    din = f"RGB_D{k-1:02d}"
    dout = f"RGB_D{k:02d}" if k < NLED else "NC"
    if k <= 14:
        fp, mpn, lcsc, val, role = FP["LEDK"], "SK6812MINI-E", "C5149201", "SK6812MINI-E", ("per-key" if k <= 13 else "layer-indicator")
        jlc = "Standard-Only"
    else:
        fp, mpn, lcsc, val, role = FP["LEDS"], "SK6812-SIDE-A", "C_TBD_verify", "SK6812-SIDE", "underglow"
        jlc = "Standard/Extended-verify"
    col = 8 + (k - 1) // 12
    put(col, f"LED{k}", "LED:SK6812", val, {1:"+5V",4:din,2:dout,3:"GND"},
        footprint=fp, mpn=mpn, lcsc=lcsc, jlc=jlc, descr=f"RGB {role} idx{k-1}")
    put(col, f"C{25+k}", "Device:C", "100n", {1:"+5V",2:"GND"}, footprint=FP["C"],
        mpn="CL05B104KO5NNNC", lcsc="C1525", jlc="Basic", descr=f"LED{k} decoupling")

# ---------------------------------------------------------------- power flags
s.add_pwr_flag("GND", 20.0, 20.0)
s.add_pwr_flag("VBUS", 30.0, 20.0)
s.note("Loudest Micro Rev A - DRAFT flat schematic (auto-generated). "
       "Connectivity is by net-name labels; footprints bound at layout.", 20.0, 10.0)

# ---------------------------------------------------------------- write files
os.makedirs(OUTDIR, exist_ok=True)
sch_path = os.path.join(OUTDIR, "loudest-micro.kicad_sch")
open(sch_path, "w").write(s.dumps())
print("wrote", sch_path)

pro = {
  "board": {"design_settings": {"rules": {}}, "layer_presets": [], "viewports": []},
  "boards": [],
  "cvpcb": {"equivalence_files": []},
  "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
  "meta": {"filename": "loudest-micro.kicad_pro", "version": 1},
  "net_settings": {"classes": [{"name": "Default", "clearance": 0.2,
      "track_width": 0.25, "via_diameter": 0.6, "via_drill": 0.3}]},
  "pcbnew": {"last_paths": {}, "page_layout_descr_file": ""},
  "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
  "sheets": [[s.root_uuid, "Root"]],
  "text_variables": {}
}
pro_path = os.path.join(OUTDIR, "loudest-micro.kicad_pro")
open(pro_path, "w").write(json.dumps(pro, indent=2))
print("wrote", pro_path)
