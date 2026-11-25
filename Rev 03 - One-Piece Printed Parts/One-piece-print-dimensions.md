# Trash Bin Pro Max
## One-piece 3D-printed parts · Rev 03

The cabinet stays **760 × 760 mm**, or **785 × 760 × 1,225 mm** including the right-side display housing and camera mast. The existing **760 × 760 × 35 mm** base is the non-printed component. The part numbers follow Rev 02. Each row describes one complete printable body per unit shown. The stationary pedestal retains its three original parts. The mechanism between the pedestal and deck is deferred.

All dimensions are nominal in **mm**. The coordinate origin is the center of the base, with +X toward the LCD, +Y toward the rear, and Z0 at the floor. Base top Z55, liner bottom Z115, liner floor Z120, rim Z500, pedestal top Z630, level deck top Z750, camera lens Z1190 and mast top Z1225.

### Printer fit

The Bambu H2D specification gives **325 × 320 × 325** for single-nozzle printing. Bambu separately lists **350 × 320 × 325** as the total reach of both nozzles. The statuses below use the single-nozzle volume. **Fits** means the nominal bounding box fits in the stated orientation. **Check angled** means the intended print orientation exceeds that volume and a rotated setup, supports and clearance would need checking in the slicer. **Larger printer** means the part geometry exceeds the single-nozzle volume in any orientation. [Bambu H2D technical specifications](https://cdn1.bambulab.com/documentation/h2d/en/H2D_Laser_Full_Combo_20250305.pdf)

For the listed flat-wall and upright-mast orientations, the minimum bounding envelope across the print jobs is **760 × 445 × 1,170**, before adding room for brims or supports. The cabinet panels, liners, and mast remain full-size single pieces.

### 1. Cabinet and rails

| Part | Qty | One-piece dimensions | Printed form | H2D |
| --- | ---: | --- | --- | --- |
| P04 Foot | 4 | 50 × 50 × 20 | TPU foot cup, R4 plan corners, 4 bottom and 4 perimeter wall. Four 4-thick web arms forming a cross up to the open face. | Fits flat |
| P05 Front/rear access panel | 2 | 760 × 445 × 18 | Ribbed shell with six integral through-bolt bosses. | Larger printer |
| P06 Fixed left wall | 1 | 724 × 445 × 18 | Ribbed shell with end receivers for both access panels. | Larger printer |
| P07 Fixed right half-wall | 2 | 350 × 445 × 18 each | Ribbed shell with a receiver at the outside end. The original two half-walls flank the lower mast. | Larger printer |
| P08 Front/rear/left divider | 3 | 266 × 445 × 24 each | Hollow box web with smooth liner-facing sides. | Check angled |
| P09 Right divider | 1 | 244 × 445 × 24 | Hollow box web, ends at X340 against the lower mast. | Check angled |
| P10 Liner slide rail | 8 | 320 × 30 × 60 each | Open-bottom skid with 5-thick top, 4-thick side/end walls and four 4-thick cross webs. | Fits laid flat, rotated about 25° for brim room |

**P05–P07 shell profile.** The liner-facing skin is 4 thick. On the opposite face, the perimeter return and orthogonal web ribs are 3.2 thick and rise 14 from the skin, for 18 total. Starting at the lower-left corner, put ribs along U = 75, 150, 225, … and V = 75, 150, 225, … within the shell. Omit any rib center less than 25 from the far edge on its axis. Blend ribs into the skin with R2 roots. Fill around each bolt or insert with an integrated local boss.

**P08–P09 divider profile.** Each face is 3 thick, with 18 between the faces. Apply 3-thick internal vertical cross webs at 35, 95, 155 and 215 from the inner end and 3-thick end walls. The top closes with a 45° internal taper under a 3-thick top cap. Leave the bottom cells open between attachment bosses. The nominal upright print is 445 high.

**Installation coordinates.** P05 inner faces are at Y = ±362. P06 inner face is X−362. P07 inner faces are X+362 and run Y = −362 to −12 and +12 to +362. The four 24-thick dividers are centered on the cabinet axes and start 96 from the center. P08 ends at 362 from center and P09 ends at X340. All panels start at Z55 and end at Z500. Foot centers remain at all four combinations of X = ±330 and Y = ±330. Rail webs are centered 40, 120, 200 and 280 from one end. Rail stations are absolute X spans 120–150 and 270–300 and absolute Y span 30–350 in each quadrant. The rail tops are Z115.

**Mounting features.**

- Front and rear P05 panels each retain six Ø5.5 through holes at local U = 9, 380 and 751 from one end, and V = 90 and 355 above the bottom. Put each hole through a Ø16 solid boss, full 18 deep. Countersink the exterior for the flush M5 head. Use the Rev 02 M5 × 45 connector bolts and M5 Ø8 × 12 barrel nuts. P06 receives a bolt at each end, P07 at its outboard end, and the front/rear P08 on its outboard end. At each receiving end, place a solid **30 long × 24 tall** end block at both fastener heights, full part thickness. The bolt channel is Ø5.5 × 30 from the end, on mid-thickness. The Ø8 barrel socket center is 20 from that end, at its bolt height, to a depth of 15 in the 18 walls or 18 in the 24 divider.
- Plinth mounting points on the fixed side walls are X = ±371, Y = ±60, ±180 and ±300. Divider mounts are on the two center axes at ±145, ±225 and ±305. Use integrated, full-depth bottom pads **22 long × 20 high** centered on each point, with an M5 insert axis vertically from below. The prior Ø5.5 base clearance holes align with these pads. M5 × 50 screws have 15 nominal available above the base, so keep a clear screw passage beyond the insert as needed. Set printed pocket geometry to the selected M5 heat-set insert and use a test coupon for fit.
- The two LCD housing attachment points are on the right half-walls at Y = ±40, Z320. Add a **Ø16 full-depth boss** centered at each point for the shell screws.

### 2. Full-size liner

| Part | Qty | One-piece dimensions | Printed form | H2D |
| --- | ---: | --- | --- | --- |
| P11 Complete liner | 4 | 346 × 346 × 385 outside | Monolithic chamfered tub with 5 floor, 3 walls, reinforced rim and two molded pull ledges. The former wall sheets and pull straps are built into this body. | Larger printer |

- Outside floor/rim polygon in local U,V is **(107, 0), (346, 0), (346, 346), (0, 346), (0, 107)**. The 107 × 107 corner relief is 45°. For rear-right bin B the local origin is cabinet (14, 14). Rotate the same liner by 90° increments for the other positions. Its outer chamfer stays at least 95.46 radially from the cabinet center.
- The bottom is 5 thick and the five vertical side walls are 3 thick measured normal to each side. Put R5 fillets on the inside floor-to-wall edges. The straight-wall inside width and length are **340**, and usable floor-to-rim depth is **380**.
- Thicken the top 8 of the rim inward from 3 to **6** at its top, using a 45° ramp for the first 3 and a straight 5-high band above. This gives a **334 × 334** nominal straight-wall rim opening before the chamfer.
- Mold a pull ledge on the inside of each of the two full-length outside walls. Each is 80 long, centered at station 173 along its wall, with a 12 inward projection and a 12-high 45° underside. In local height, the ledge starts at 350 and reaches full projection at 362. The minimum span at a ledge is 328 in its direction. The shell walls stay within the 346 outside box.
- Print upright with the bottom on the bed. The 350-wide cabinet bay gives 2 per side before dimensional variation. The liner slides out horizontally after removing the appropriate P05 panel.

### 3. Stationary pedestal and deck

| Part | Qty | One-piece dimensions | Printed form | H2D |
| --- | ---: | --- | --- | --- |
| P16 Bottom flange | 1 | Ø186 × 32 total | 8 flange plus a Ø137.4 × 24 raised locating ring, ID105. | Fits flange-down |
| P17 Pedestal tube | 1 | Ø150 OD × 557 long | Ø138 bore, 6 wall, four internal ribs. | Larger printer |
| P18 Top cap | 1 | Ø190 × 34 total | 10 solid top plus a Ø137.4 × 24 downward locating ring, ID105. | Fits top-face-down |
| P19 Loading deck | 1 | Ø380 × 10 | Flat 4-thick loading face, 4-thick perimeter wall, and underside rib grid 6 deep. | Check angled. The Ø380 face exceeds the flat bed. |

**Pedestal.** The base flange remains at Z55–63, tube at Z63–620, and cap at Z620–630. The two locating rings enter the ends of the tube by 24, with a nominal 0.30 radial gap. The four tube ribs are 4 thick × 6 radial depth, at angles 45°, 135°, 225°, 315°, and stop 25 short of both ends to clear the rings. Ramp their first and last 6 to and from full depth. P16 keeps four Ø6.6 through holes in the 8-thick flange on **Ø170 PCD**, on the 45° diagonals. Connect each tube end to its ring with four radial Ø4.5 through holes centered 12 from the tube end at 0°, 90°, 180°, 270°. Match those locations to M4 insert pockets on the rings. Check actual insert dimensions and flange flatness before assembly. P18 reserves the full Ø190 top as the future mechanism interface.

**Deck.** The 4-thick solid face and 6-deep underside ribs make the 10 total. Put 3.2-thick ribs along the X and Y axes and at ±60 and ±120 in both directions. Trim them to the inside of the perimeter wall at radius 186. Use a 2 × 45° upper edge bevel. Keep the face smooth and the future mounting interface blank. Its eventual level top is Z750.

### 4. Mast, camera arm and electronics mounts

| Part | Qty | One-piece dimensions | Printed form | H2D |
| --- | ---: | --- | --- | --- |
| P20 Camera mast | 1 | 1,170 high × 50 in X × 50 in Y maximum | Closed-section post with 40 × 24 lower stem and 50 × 50 upper box. | Larger printer |
| P21 Camera arm | 1 | 372 long × 50 wide × 32 high maximum | Open-bottom stiffened beam with a raised camera end and integral locating tongue. | Fits bed-diagonally with top face down |
| P22 Camera gusset | 2 | 145 × 100 × 8 right triangle | 4-thick web plus 4-deep ribs and integral bolt bosses. | Fits flat |
| P23 Camera cradle | 1 | 60 × 44 × 4 | 3-thick tray with 1-high edge lip and two underside arm fixings. | Fits flat |
| P24 LCD shell | 1 | 140 × 80 × 22 | 3-thick sides and back, integrated four Ø8 screw posts. | Fits back-down |
| P25 LCD cover | 1 | 140 × 80 × 6 overall | 3 visible thickness plus a 3-high internal locating skirt. | Fits front-down |
| P26 Pi carrier | 1 | 110 × 90 × 11 overall | 3-thick tray plus four integral 8-high standoffs. | Fits flat |
| P27 IR saddle | 1 | 45 × 30 × 6 overall | 3-thick seat and 3-high edge flanges. | Fits flat |

**Mast.** At Z55–500 use X340–380, Y = ±12 and 5-thick walls. Close the bottom 18 for the two vertical M5 mounting inserts on X360, Y = ±6, at the old base hole locations. Over Z500–560, taper the section to X330–380, Y = ±25. Maintain this 50 × 50 upper box and 5-thick walls from Z560–1225. Form the arm seat as an open-top pocket from **X330–340.4**, Y = ±20.3 and Z1206.7–1225. Keep the mast outer face at X380. The upper section widens inward and sideways above the bin rim. Dry-fit and bond the lower stem to the two P07 edges and the P09 end over Z55–500 with a process tested on the printed material.

**Arm.** The top is Z1225 across X−32 to +340. The 50-wide main beam is 32 deep from X45–330. The 50-wide camera end is 18 deep from X−32 to +31. Ramp the underside at 45° between X31 and X45. The tongue at X330–340 is 40 wide and 18 deep, flush with the top. Use a 4-thick top skin, 4-thick side walls and 4-thick transverse ribs at X60, 110, 160, 210, 260 and 315. Provide solid local pads behind the camera and IR saddle fixings. Add full-depth, 14-wide transverse bolt webs at X265 and X305 and drill the Ø5.5 holes across the width. The camera end rises to an underside at Z1207 to retain space for the lens.

**Gussets.** Fit one on each Y face of the upper mast and beam. Use a local origin at X225, Z1225, with U along +X and V down. Profile vertices are **(0, 0), (145, 0), (145, 100)**. Four Ø5.5 through holes are at **(40, 9), (80, 9), (135, 35), (135, 75)**. Use Ø14 bosses full depth around the holes, 4-thick stiffening ribs along all three edges and M5 × 80 bolts with washers and locking nuts. Match those bolt centers in the beam and post. Form solid transverse bridges across the post bore at Z1150 and Z1190, each 14 wide in X and 14 high at the hole, with 45° lead-ins underneath from the sidewalls. Drill their holes across the width after printing. Clear the nuts and check the mast's deflection with the camera installed.

**Camera and IR adapters.** Center the camera cradle at X0, Y0, with two Ø4.5 mounting centers on X = ±22, Y0. Its 2-thick shallow lip runs along the two long sides, leaving each end open for wiring. Set the lens to Z1190 with the final camera mounted. Center the IR saddle at X90, Y0 with two Ø4.5 mounting holes at X78 and X102, Y0, and put 2-thick flanges along the long sides. Provide corresponding base-facing attachment pads in the arm. Transfer sensor screw and cable openings to the printed blanks once actual hardware is available.

**LCD.** Position the shell at X380–402, centered at Y0, Z320. Relative to the shell center in the face plane, put two Ø4.5 wall-mount holes through the back at **(±40, 0)** and four Ø8 posts at **(±61, ±31)**. Tap M3 to depth 8 into the posts from the open face. Internal box before posts is 134 × 74 × 19. Cut a **10 wide × 6 deep** slot back from the front edge of the bottom wall on center. The cover adds 3 externally, to X405. Its locating skirt is 133.4 × 73.4 outside, 1.5 thick and 3 high, with a 12-wide gap on the bottom center at the cable slot. Cover holes are four Ø3.4 through on the post centers, countersunk Ø6.5 to keep M3 screw heads flush. Its display opening follows the final LCD model.

**Pi carrier.** The four standoffs are Ø8 × 8 high, centered at **(±29, ±24.5)** on the 58 × 49 board pattern. Use an M2.5 pilot suitable for the actual fastening method. Two Ø4.5 mounting holes through the tray are at **(±47, +36)**. Center the tray at cabinet X−210, Y−215 under liner C, with its 110 dimension along cabinet Y. [Raspberry Pi 4 Model B mechanical drawing](https://pip-assets.raspberrypi.com/categories/545-raspberry-pi-4-model-b/documents/RP-008341-DS-1-raspberry-pi-4-datasheet.pdf)

### Print and assembly checks

Use PETG as the initial rigid-part material and TPU for the feet. Fasteners, heat-set inserts and electronics are purchased hardware. The 0.30-per-side slip allowances at the socket and display skirt are starting values. Print mating coupons before committing to the large pieces and check the liner width after cooling. Verify rigidity of the tall mast and fixed pedestal under their intended loads. The drawings are dimension inputs for CAD and prototyping. [Prusa PETG guide](https://help.prusa3d.com/article/petg_2059) · [Prusa guidance on modeling tolerances](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135)

### Dimensioned drawings

- [01 · Printed cabinet and rails](01-printed-cabinet.png)
- [02 · One-piece liner and molded grips](02-one-piece-liner.png)
- [03 · Flanged pedestal and ribbed deck](03-pedestal-and-ribbed-deck.png)
- [04 · Camera mast, arm and gussets](04-mast-and-arm.png)
- [05 · Electronics housings and mounts](05-electronics-mounts.png)
