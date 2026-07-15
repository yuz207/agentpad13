# Case — Phase 3 (build123d via cad-khana)

Runs in parallel with PCB fab. Consumes: PCB STEP/DXF export, mount-hole coordinates, component heights.

## Architecture (spec §3.8 as amended, `research/04` dimensional bible)
- **Unibody top shell with integrated plate** (D3): 1.5 mm clip shelf in a 3.0–3.5 mm web, per-switch relief pockets, 13.9 mm cutouts (coupon-calibrated), printed deck-face-down; + flat bottom lid on M3 heat-set inserts (⌀4.0–4.25 pilot). FR4-plate sandwich remains the zero-redesign fallback.
- Two SKUs, one CAD: frosted-translucent PETG shell (whole-body glow) / black PETG + perimeter diffuser channel (≥3 mm LED-to-diffuser or add frost).
- Bottom lid: steel weight pocket (~60×40×3), PORON 2 mm sheet with socket cutouts, SJ5303/5302 bumpons, reserved 50×34×6 battery cavity (wireless fork).
- Stack-up numbers: plate-top→PCB 5.0 mm; sockets hang 1.85 mm below PCB → ≥2.2 mm relief (3.5–4.0 with foam); USB cutout per research/04 §1E; touch window ~1.2 mm; encoder = EC11 20 mm-class shaft, PCB-mount, no nut torque on printed top.
- Elephant-foot chamfers (0.3–0.5 mm × 45°) on every bed-side edge + slicer EFC.

## Discipline
Tolerance coupons FIRST (20-min prints): switch-cutout ladder, insert-hole ladder, USB aperture, encoder/joystick openings, touch-window thickness. Then the 4-hour full print. Use `khana check` (cad-khana skill) for interference/clearance assertions against the PCB STEP.
