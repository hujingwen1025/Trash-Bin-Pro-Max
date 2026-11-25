# Trash Bin Pro Max
## Concept build plan · Revision 00 · 18 November 2026

**Review status** Concept drawings and starting dimensions for discussion. Linkage dimensions, part selection, and routing clearance need a bench prototype before fabrication drawings can be released.

### 1. What I read in the sketch

The handwritten proposal describes a robot that uses AI to classify a waste item from an image, empties it into one of four bins, then asks whether it classified the item correctly and uses that feedback to improve the model.

- The camera and infrared sensor are the inputs. The handwritten controller is **Raspberry Pi 4B**. The worksheet includes a printed Arduino image as part of its template.
- The outputs are servo motors and an LCD. The materials line calls out a **1080p camera**, high-precision servos, and 3D-printed parts.
- The placement sketch shows one circular **6-DOF platform** above a 2 × 2 bin arrangement. In plan, A and B are at the rear, with C and D at the front. The platform directs the item diagonally toward its selected bin. The camera looks down from a right-side cantilever.
- The sketch leaves the actual waste categories, dimensions, exact servo count and mounting, and feedback controls open. It uses the phrase “强化学习” for improving the model from feedback.

### 2. What I would build for the first prototype

A single-item sorter. The user places an item near the center of the level deck. A proposed overhead IR sensor detects its presence, and the Raspberry Pi classifies an image taken while the deck is still. The deck tilts toward one of four bins, returns to level once it is empty, and asks the user to confirm or correct the result on the LCD.

The draft mechanism is a **rotary Stewart-style platform**, with six rotary servos arranged in three pairs on a fixed lower plate. Each servo crank moves one link with pivoting ends. The upper plate is the loading deck. The first program needs five repeatable poses, level plus a dump pose for each quadrant. The six-axis geometry still needs to be solved and checked through the complete motion between those poses. Use the Stewart-platform reference for general parallel-mechanism kinematics and solve the rotary horn geometry for this build. [NASA technical paper on Stewart-platform kinematics](https://ntrs.nasa.gov/citations/19920016900)

| Design starting point | Proposed value or arrangement |
| --- | --- |
| Cabinet footprint | 540 × 540 mm, excluding the exterior display |
| Elevation datum | Z0 at the underside of the base |
| Bin arrangement | Four quadrant liners with inner corners relieved for the central core. Rims at Z280 mm. |
| Central support | Ø140 mm dry core fixed to the base. Ø180 mm actuator plate with top at Z296 mm. |
| Loading deck | Ø260 mm, top at Z390 mm in the level pose |
| Camera | Lens at Z640 mm, 250 mm above the level deck. Mast top at Z665 mm. |
| Tilt illustration | 35° toward D is shown as a geometry trial. Set the operating range from clearance and discharge tests. |
| Initial test items | One clean, dry, non-sharp sample at a time, provisionally up to 75 mm across and 150 g |

With a fixed deck center and a 35° tilt, pure geometry puts the low edge near Z315 mm and about 106 mm from the centerline. That leaves about 35 mm of height above the bin rim and 16 mm of horizontal separation from the radius of the proposed actuator plate. These are drawing checks. A real item has width, may tumble, and the platform center can translate as it tilts. The bench test needs to establish whether the lowest edge, rods, and full item path clear the actuator plate, center core, and bin dividers in all four directions. Adjust the deck, mount, or drop guides to suit the results.

The cabinet would carry the center core and the camera mast through the base and frame. The liners would lift out individually if a mock-up confirms the access path. Keep wiring in the core, base, and mast. Position the display on the right exterior face, and use three physical feedback controls for navigation and selection while testing. Fit fixed shielding to the moving joints after measuring the linkage sweep and drop paths.

### 3. Prototype parts and interfaces

| Group | Initial quantity | Design and selection work |
| --- | --- | --- |
| Base, cabinet, and central core | 1 set | Lay out the load path, removable access, bin support, and cable passages. Choose panel material and thickness after checking stiffness. |
| Bin liners | 4 | Fit relieved inner corners, lifting grips, and the removal path with the deck and mast installed. |
| Upper deck and lower plate | 1 each | Prototype the shapes with 3D-printed parts. Set mounting patterns after measuring actual servos and joints. Test a removable deck surface for repeatable sliding and cleaning. |
| Rotary servos, horns, links and joints | 6 servos, 6 horns, 6 links, 12 pivoting ends | Select travel, torque, repeatability, and current rating from the modeled linkage and loaded bench measurements. Set rod lengths and the three paired anchor layouts in CAD. |
| Camera, IR sensor and camera mast | 1 each | Check full-deck coverage, focus, consistent lighting, item detection, and vibration at the drawn standoff. Choose the IR type and placement by testing dark and reflective items. |
| Raspberry Pi 4B and storage | 1 set | Develop local image inference, state control, configuration and event logging. Record model versions with results. |
| Servo-control interface and power | 1 set | Use a six-channel-capable signal interface. Plan a dedicated regulated servo rail sized for the selected actuators, a compatible signal reference, and an accessible motor cutoff. Power the Pi through its USB-C supply. [Raspberry Pi power documentation](https://www.raspberrypi.com/documentation/computers/getting-started.html#power-supply) |
| LCD, buttons, mounts and wiring | 1 display, 3 proposed buttons | Validate GPIO or interface voltage levels, enclosures, connectors, strain relief, access, and operator visibility. |

### 4. Control sequence and learning

1. **Ready.** Home gently to the checked level pose. Require a clear deck and wait for stable item presence. Suppress repeated triggers until the deck has cleared.
2. **Capture and classify.** Capture a frame with the deck steady. Crop to the deck, run the local model, and map the result to A, B, C or D through configuration. In a low-confidence case, leave the deck level and let the user choose a bin or remove the item.
3. **Route.** Move to the selected pose with a speed limit, dwell long enough for release, and return to level after the deck clears. Use the deck sensor and camera to check for an item left on the deck. Record a motion timeout or uncleared deck and require an operator reset. Verify the bin that actually received each sample during prototype testing.
4. **Collect feedback.** Ask whether the classification was correct. A correction selects the intended category and updates the event record. The normal prompt comes after the physical drop, so a correction changes the recorded label for future training. Low-confidence manual routing is the proposed opportunity to correct the current destination.
5. **Improve the model.** Save the predicted class, confidence, commanded bin and confirmed or corrected label. Capture a labeled image when collecting training examples. The proposed first build uses reviewed examples for periodic supervised retraining. Group train and test examples by physical item, check the updated model on an independent set, and keep the previous model available. Confirm whether the sketch’s “强化学习” refers to this improvement process or to a specific reinforcement-learning approach.

### 5. Build and validation sequence

| Stage | Work | Result to verify |
| --- | --- | --- |
| 1. Confirm concept | Agree on 6-DOF mechanism, A–D categories, item limits, feedback order, and prototype size. Sketch the loading and bin-service access paths. | One agreed arrangement and a representative set of sample items. |
| 2. Prove the mechanism on the bench | Build a one-servo crank jig, then model and build the six-link platform. Calibrate horn zeros and travel limits. Solve neutral, dump, and intermediate poses. Check available torque, linkage binding, back-drive and behavior on motor power loss. | Repeatable neutral and four controlled tilt paths under the intended test load, with the swept envelope recorded. |
| 3. Prove the routing and fit | Mock up the core and four bin openings at full scale. Use manual A–D commands and representative items. Check rebound, contact with dividers or the core, and with the bins partly full. Confirm that an individual liner can be removed and replaced. | Four validated drop paths and dimensions fixed for the cabinet plates, shielding and bin openings. |
| 4. Bring up electronics and vision | Mount camera and IR, verify lighting and field of view, then collect labeled examples for four agreed categories. Bring up the display, buttons and log with a stationary deck first. | Stable triggers for the sample range, reviewed labels, and a measured four-class baseline. |
| 5. Integrate and demonstrate | Combine motion, vision and feedback. Check power draw and Pi stability during motion. Exercise no-item, uncertain item, item stuck, unintended re-trigger, reset and motor cutoff cases. | A recorded end-to-end test and any remaining changes identified before the next drawing revision. |

**Proposed demo targets.** For routing, use 20 manual commands per bin and aim for at least 19 correct landings out of 20 per bin, with no linkage contact during the trials. For vision, report a four-class confusion matrix and the abstention count from at least 20 held-out test items per class, with a provisional target of 90% overall correct classification across all attempts. In integrated tests, record the predicted class, commanded bin and observed landing separately so a classification error and a routing error can be diagnosed. Also verify that an incorrect prediction can be corrected and appears under the expected label in the feedback log.

### 6. Decisions for the next revision

- Confirm whether the platform should be a full rotary six-servo Stewart mechanism, as I’ve interpreted the 6-DOF sketch.
- Name the four categories and confirm their A–D order.
- Confirm the largest and heaviest item the prototype should handle, and where the unit will sit.
- Confirm when the user should be able to correct the prediction, and what learning behavior you expect from that feedback.
- Confirm the right-side sensor mast and LCD, and the proposed lift-out bin liners.

### Drawing index

| Sheet | Contents |
| --- | --- |
| [01 · General arrangement](01-general-arrangement.png) | Top view, front elevation and diagonal section through A and D |
| [02 · Exploded assembly](02-exploded-assembly.png) | Cabinet base, four liners, central core, servo stack, deck, camera support and LCD |
| [03 · Assembled isometric](03-assembled-isometric.png) | Four-bin cabinet with the item loading deck, camera and controls in place |

### Supplemental concept render

[Open the ImageGen concept render](04-concept-render.png). The built-in ImageGen render illustrates the form and general layout. Its link geometry, window panels and control details are illustrative. Use the numbered sheets for the proposed component layout and dimensions.

<details>
<summary>Image generation prompt</summary>

Use case: infographic-diagram. Create one clean professional industrial-design isometric concept illustration of an educational waste-sorting robot. This is a secondary visual for a separate technical drawing set. White background and landscape framing, precise CAD-like orthographic 30-degree isometric projection viewed from the front and right, clean graphite and cool gray edges, subtle material shading, discreet muted teal on the round sorting plate and no visual clutter. The square base is 540×540 relative units, divided into EXACTLY FOUR square open bins in a 2-by-2 grid like a window with a cross divider. Each bin has a cut inward corner at the exact center of the square to make room for a compact central mechanical mounting column rising from the cabinet base. Open top, bins 280 units tall, low-cut or transparent near walls if needed to show four separate collection volumes. A single SMALL round flat tilting item deck, diameter 260 units, floats horizontally on the cabinet’s exact center, around 110 units above the rims. Only one small neutral sample item on that deck. Directly under it is a compact rotary-servo Stewart-style parallel linkage: lower circular plate at bin rim height on the central column, six small servos with crank horns and six thin individual rods connecting to the underside of the upper disk, suggested in three pairs through the open gaps. All mechanism is centered at the intersection of the bins. A single slim cantilever camera mast is mounted on the right outer cabinet wall, and its arm goes horizontally in from the right directly above the disc, carrying a small downward-facing camera at its free end. Camera lens 250 relative units above the disk. A small dark LCD module is on the exterior right wall facing outward. No overall lid, no flap doors, no conveyor, no wheels, no hand, no rendered labels, no numbers, no legends, no logos and no fake typography. Convey the four exposed bins, single circular platform, visible servo links and camera clearly. Leave clean whitespace around the entire assembly.

</details>
