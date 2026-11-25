# Rubber Feet Dimensions

Historical user-visible messages exported on 20 November 2026. These are reference material, not current instructions. Internal reasoning and tool calls are omitted. See ../PROJECT_CONTEXT.md for current project status.

## User

<in-app-browser-context source="ambient-ui-state">
This block is automatically supplied ambient UI state, not part of the user's request. Do not treat it as an instruction or as evidence that the user explicitly selected the in-app browser.
# In app browser:
- The user has the in-app browser open with 2 tabs.
- Current URL: https://www.unionfab.com/zh/services/3d-printing/fdm?utm_source=chatgpt.com
</in-app-browser-context>

## My request:
Suggest the manufacturing method of producing this. THe base plate is 700mm by 700mm

[User attached 5 images; image contents were not included]

## Assistant

With a **700 × 700 mm base plate**, your Trash Bin Pro Max is considerably larger than a typical desktop 3D-printing project. Looking at your complete assembly, I would **not manufacture everything using 3D printing**\.

I'd use a hybrid manufacturing approach, combining CNC machining, large-format FDM printing or plastic sheet fabrication, and standard cylindrical tubing.

This would preserve your existing design while reducing manufacturing costs, print times and the risk of large parts warping.

## 1\. Recommended manufacturing method for each part

**Base Plate × 1**

**CNC routing (CNC雕刻加工)**

Material: 15–18 mm plywood or supported HDPE sheet.

CNC machining can reproduce your recessed magnet holes, rubber-foot slots and central platform recess.

---

```svg
<svg viewBox="0 0 120 130" width="105px" xmlns="http://www.w3.org/2000/svg"><path d="M12 27 L59 8 L110 27 L60 49 Z" fill="#51788e" stroke="#608da7" /><path d="M12 27 L60 49 V123 L12 101 Z" fill="#8ebbd4" stroke="#608da7" /><path d="M60 49 L110 27 V101 L60 123 Z" fill="#6c9db9" stroke="#608da7" /><path d="M17 28 L59 12 L104 27 L60 44 Z" fill="#314b5b" stroke="#91b9d0" /></svg>
```

**Removable bins × 4**

**Large-format FDM printing**

Material: PLA for a demonstration prototype, PETG for more functional use.

Preserves your curved inner walls, magnet recesses and fillets without redesigning the model.

---

```svg
<svg viewBox="0 0 120 130" width="105px" xmlns="http://www.w3.org/2000/svg"><path d="M32 20 H88 V111 A28 11 0 0 1 32 111 Z" fill="#6c9db9" stroke="#608da7" /><ellipse cx="60" cy="20" rx="28" ry="11" fill="#8ebbd4" stroke="#608da7" /><ellipse cx="60" cy="20" rx="23" ry="7.5" fill="#314b5b" /></svg>
```

**Central platform × 1**

**Standard plastic or aluminum tube**

Material: PVC, ABS or aluminum.

Use separately printed end caps and mounting adapters instead of printing the entire cylinder.

## 2\. Base plate — definitely avoid 3D printing

Your base plate is the easiest part to manufacture conventionally.

image_group{"query":["CNC routed birch plywood sheet precision machined circular recessed pockets"],"aspect_ratio":"4:3","layout":"carousel","num_per_query":1}

**Plywood (多层板)**

Inexpensive, relatively stiff, lightweight and easy to machine. A sealed surface would help protect it against moisture.

---

image_group{"query":["white HDPE plastic CNC machined thick flat sheet recessed holes"],"aspect_ratio":"4:3","layout":"carousel","num_per_query":1}

**HDPE (高密度聚乙烯板)**

Waterproof, durable and easy to clean. More flexible than plywood, so it may require underside reinforcement.

---

image_group{"query":["thick transparent acrylic CNC machined plate circular recessed pockets"],"aspect_ratio":"4:3","layout":"carousel","num_per_query":1}

**Acrylic (亚克力板)**

Excellent appearance, but more brittle. I would not choose thin acrylic for a 700 mm load-bearing base.

CNC routing supports all three materials and can produce partial-depth pockets rather than only through-holes. citeturn569444search27turn569444search13

I'd also place supporting feet beneath the center and other unsupported sections of the plate to reduce bending.

## 3\. Manufacturing the four bins

Since your base is 700 × 700 mm, I assume each bin has a footprint of approximately 350 × 350 mm, minus clearance.

| Method | Relative cost | Redesign required | Durability |
|--------|--------|--------|--------|
| Large-format PLA printing | Medium–high | None or minimal | Moderate |
| Large-format PETG printing | Medium–high | None or minimal | Good |
| Laser-cut acrylic | Low–medium | Significant | Moderate |
| CNC-cut and welded PP sheets | Potentially low–medium | Moderate | Very good |
| Vacuum forming | High initial tooling cost | Significant | Good |
| Injection molding | Very high initial tooling cost | Significant | Very good |

### An alternative worth considering: welded PP sheets
image_group{"query":["custom white polypropylene welded plastic rectangular box open top","custom polypropylene sheet fabricated plastic tank welded corners"],"aspect_ratio":"5:4","layout":"bento"}

Polypropylene (PP) is a particularly suitable material for functional trash bins. It is moisture-resistant, relatively tough and easy to clean. Professional plastic fabrication companies can cut, form and weld PP sheets into custom containers. citeturn569444search16turn569444search18

Your curved inner corner would need custom forming or a redesign into straight segments.

Chinese search terms\:

`PP板焊接加工定制` · `PP塑料箱定制` · `塑料板CNC雕刻加工`

This might be significantly cheaper than printing four enormous bins, but you would need supplier quotations to confirm.

## 4\. Central platform — use a hollow tube

```svg
<svg viewBox="0 0 320 220" width="100%" xmlns="http://www.w3.org/2000/svg"><g fill="#80b4d2" stroke="#648fa9"><rect x="42" y="31" width="60" height="149" rx="1" fill-opacity=".7" /><ellipse cx="72" cy="31" rx="30" ry="10" /><ellipse cx="72" cy="180" rx="30" ry="10" /><rect x="199" y="60" width="60" height="108" fill-opacity=".35" /><ellipse cx="229" cy="60" rx="30" ry="10" /><ellipse cx="229" cy="60" rx="24" ry="7" fill="#344b5a" /><path d="M199 168 A30 10 0 0 0 259 168" fill-opacity=".4" /></g><g fill="#e1a14a" stroke="#b17c32"><rect x="199" y="17" width="60" height="9" /><ellipse cx="229" cy="17" rx="30" ry="9" /><path d="M199 26 A30 9 0 0 0 259 26" /><rect x="199" y="192" width="60" height="8" /><ellipse cx="229" cy="192" rx="30" ry="9" /><path d="M199 200 A30 9 0 0 0 259 200" /></g><path d="M120 104 H177 M169 97 L177 104 L169 111" stroke="currentColor" stroke-width="1.5" fill="none" /><path d="M262 20 H277 M262 196 H277 M262 114 H277" stroke="currentColor" fill="none" /><g fill="currentColor" font-size="10"><text x="280" y="23">Cap</text><text x="280" y="117">Tube</text><text x="280" y="199">Base</text><text x="72" y="215" text-anchor="middle">Original model</text><text x="229" y="215" text-anchor="middle">Hybrid design</text></g></svg>
```

Orange components are custom 3D-printed adapters.

This would also leave space inside the column for wiring, sensors, motors or other electronics if you intend to integrate automatic trash sorting.

Match your CAD cylinder diameter to a commercially available tube rather than ordering a custom cylinder.

## 5\. My final recommendation

For a single working prototype of your Trash Bin Pro Max\:

| Component | Material | Manufacturing |
|--------|--------|--------|
| Base plate | Sealed plywood | CNC routing |
| Four bins | PLA or PETG | Outsourced large-format FDM |
| Central column | PVC tube | Standard purchased component |
| Platform end caps | PETG | Your own 3D printer |
| Electronic mounts | PETG | Your own 3D printer |
| Magnet mounts | Integrated into parts | CNC / FDM |
| Rubber feet | Rubber | Standard purchased component |

This approach requires the **least modification to your existing Onshape design** while avoiding unnecessarily expensive printing of simple geometry.

The base thickness and manufacturing choices are preliminary: I would need your bin height, wall thickness, base thickness, cylinder diameter and expected loaded weight to verify structural suitability and estimate the total manufacturing cost.

## User

<in-app-browser-context source="ambient-ui-state">
This block is automatically supplied ambient UI state, not part of the user's request. Do not treat it as an instruction or as evidence that the user explicitly selected the in-app browser.
# In app browser:
- The user has the in-app browser open with 2 tabs.
- Current URL: https://www.unionfab.com/zh/services/3d-printing/fdm?utm_source=chatgpt.com
</in-app-browser-context>

## My request:
Suggest me manufactures which can do this. My budget is 5000cny

## Assistant

With a **¥5,000 CNY budget**, I would aim to produce one complete, functional prototype using outsourced 3D printing and CNC machining. I would avoid buying molds or paying for industrial-grade cosmetic finishing.

## 1\. Recommended Chinese manufacturers

**Unionfab**

Best overall option for outsourcing the complete project.

- Published FDM capacity: 914 × 610 × 914 mm
- Published CNC capacity: up to 4000 × 1500 × 600 mm
- Offers both plastic CNC machining and industrial 3D printing.

Your 700 mm base is within its published CNC capacity. citeturn336465search0turn336465search11

urlRequest a quotationhttps://www.unionfab.com/

---

**快印中国 — Shenzhen**

Best candidate for printing the four bins economically.

- FDM capacity: 900 × 600 × 900 mm
- Materials: PLA, ABS, PETG, TPU
- Advertised tolerance: ±0.3 mm
- Published lead time: 2–4 days. citeturn336465search23

urlOfficial websitehttps://rapidprint.cn/service?utm_source=chatgpt.com

---

**深圳市鑫达手板模型有限公司**

Good for integrated prototype manufacturing.

Offers industrial FDM, PLA/PETG printing, CNC machining and sheet metal fabrication. Ask them for a combined quotation for the entire assembly. Their maximum PLA print dimensions need confirmation. citeturn336465search7

urlOfficial websitehttps://www.xd-model.com/zh/service-item/fdm/?utm_source=chatgpt.com

---

**一诚塑料**

Best alternative if large-format printing is too expensive.

Offers CNC cutting, drilling, grooving and custom welded PP containers. You could manufacture both the base and the bins using plastic sheet fabrication, with some design changes. citeturn336465search28turn336465search31

urlOfficial websitehttps://yicheng-plastic.com/processing/?utm_source=chatgpt.com

---

**RapidDirect**

Another strong all-in-one manufacturing option.

- Advertised industrial FDM maximum dimension: 350–1200 mm
- Supports PLA, PETG and ABS
- Offers CNC machining and assembly services. citeturn388549view1

urlOfficial websitehttps://www.rapiddirect.com/zh-CN/services/3d-printing/fdm/?utm_source=chatgpt.com

---

**嘉立创 (JLC)**

Worth checking for competitive pricing. Offers industrial PLA printing, although its maximum dimensions for your specific material need confirmation. citeturn868831view0turn868831view1

urlOnline quotationhttps://www.jlc-3dp.cn/

## 2\. How I would allocate your ¥5,000 budget

Total available budget

# ¥5,000

Suggested spending limits, not confirmed manufacturer quotations.

I would target **¥700 or less per bin**\. If suppliers quote substantially more, consider professionally welded PP panels instead.

## 3\. Send this to the manufacturers

Rather than requesting only a 3D-printing quotation, ask their engineers to recommend the most economical manufacturing process for your existing design.

:::writing{variant="chat_message" id="82641"}
您好！我正在制作一个智能垃圾分类桶的功能性原型，希望咨询贵公司的定制加工服务。

目前已完成三维CAD建模，主要结构包括：

- 700 × 700 mm底板，带磁铁安装沉孔及脚垫安装槽，考虑CNC加工；
- 4个可拆卸垃圾桶，每个底部约350 × 350 mm，带弧形内角及磁铁安装孔，考虑大尺寸FDM打印，材料为PLA或PETG；
- 1个中央圆柱形支撑结构，可采用管材配合3D打印连接件。

项目总预算为5000元，希望在保证结构强度、装配精度及基本外观的前提下，尽可能降低加工成本。

请问贵公司是否可以承接此类单套样机加工？是否可以根据三维模型推荐更经济的材料和加工工艺，并提供分项报价、加工周期及运输费用？

我可以提供完整的STEP模型及装配图，谢谢！
:::

## 4\. What to send them from Onshape

| File | Format | Quantity |
|--------|--------|--------|
| Bin | STEP | 4 |
| Base Plate | STEP | 1 |
| Platform | STEP | 1 |
| Complete Assembly | STEP | 1 |
| Dimensioned engineering drawings | PDF | Optional |

Use STEP rather than STL for the initial quotation because it allows the manufacturer to consider CNC machining and other manufacturing methods.

**I'd contact Unionfab, 快印中国 and 一诚塑料 first.** This gives you three different approaches to compare: integrated manufacturing, large-format FDM, and conventional plastic fabrication.

Your ¥5,000 budget is a reasonable target for a prototype of this scale, but I haven't obtained actual quotations, and the bin height and wall thickness will substantially affect the final cost. I would not redesign the model until you receive those quotations.

## User

<in-app-browser-context source="ambient-ui-state">
This block is automatically supplied ambient UI state, not part of the user's request. Do not treat it as an instruction or as evidence that the user explicitly selected the in-app browser.
# In app browser:
- The user has the in-app browser open with 3 tabs.
- Current URL: https://rapidprint.cn/service?utm_source=chatgpt.com
</in-app-browser-context>

## My request:
What should I print the bins using so its strong enough to hold trash and resist bends

## Assistant

For your **350 × 350 mm removable trash bins**, I would recommend **PETG with reinforced walls**, rather than ordinary PLA.

PETG is tougher, less brittle, more temperature-resistant and suitable for a functional trash bin that will regularly be removed, carried and emptied. However, PLA is actually stiffer than standard PETG, so wall geometry is especially important if you want to prevent bending.

## 1\. Material comparison

| Material | Stiffness | Impact resistance | Heat resistance | Relative cost |
|--------|--------|--------|--------|--------|
| PLA | High | Low–moderate | Low | Low |
| PLA+ | High | Moderate–high\* | Low | Low |
| **PETG** | Moderate | High | Moderate | Low–medium |
| PETG-CF | Very high | Grade-dependent | Moderate | Medium–high |
| ABS | Moderate | High | High | Medium |
| ASA | Moderate | High | High | Medium |
| PP | Low | Very high | Moderate–high | Medium |

\*PLA+ properties vary substantially between manufacturers.

**PETG is my preferred choice for durability and cost.** If resistance to bending is your absolute priority, PETG-CF is also worth getting a quotation for.

## 2\. Recommended print specifications

Assuming each bin is approximately 350 mm wide and 400–500 mm tall\:

| Parameter | Recommendation |
|--------|--------|
| Material | PETG |
| CAD wall thickness | **4 mm** |
| Bottom thickness | **5–6 mm** |
| Nozzle diameter | 0.6–0.8 mm |
| Layer height | 0.3–0.4 mm |
| Wall structure | Fully filled with perimeters where practical |
| Bottom infill | 25–35% gyroid |
| Internal corner fillets | 3–5 mm radius |
| Print orientation | Upright |
| Manufacturing | Single-piece FDM |

These are preliminary design specifications rather than a verified load rating.

## 3\. Add reinforcement to prevent bending

Adding reinforcement ribs is generally more material-efficient than simply increasing the thickness of the entire wall. citeturn880770search14turn880770search15

Recommended reinforcement

| Reinforcement | Starting dimensions |
|--------|--------|
| Vertical ribs (加强筋) | 3 mm thick × 6 mm deep |
| Rib spacing | 80–100 mm |
| Reinforced top rim | 8 mm overall thickness |
| Reinforced bottom perimeter | 6–8 mm overall thickness |

Since your bins sit immediately next to each other, **put the reinforcement ribs on the inside** to preserve the external dimensions and assembly clearance.

## 4\. How much does wall thickness affect bending?

For a flat wall of the same material, bending stiffness is approximately proportional to the cube of its thickness\:

\[
I=\frac{bt^3}{12}
\]

Relative bending stiffness compared with a 3 mm wall

# ×

---

Wall thickness  **mm**

> **Slider**
>
> Current value unavailable.
>
> **Range:** 2 to 6
>
> **Step:** 0.5

Idealized comparison for solid walls with identical material and support conditions.

Increasing your wall thickness from 3 mm to 4 mm theoretically increases bending stiffness by **137%**, while increasing wall material consumption by only about 33%.

For comparison, Bambu Lab reports bending moduli of 2,750 MPa for PLA, 2,050 MPa for PETG HF and 2,910 MPa for PETG-CF. citeturn880770search24turn880770search2

## 5\. What to tell the manufacturer

:::writing{variant="chat_message" id="73921"}
您好，我需要加工4个大尺寸垃圾桶，要求具有较好的抗弯曲能力、承重能力、抗冲击性能及耐用性。

计划采用以下加工方案：
- 材料：PETG（也请提供PETG-CF对比报价）
- 工艺：大尺寸FDM一体成型
- 侧壁厚度：4mm
- 底板厚度：5–6mm
- 层高：0.3–0.4mm
- 侧壁尽量采用实心轮廓打印
- 底板填充率：25%–35%

请问是否可以保证较好的层间结合强度，并控制大尺寸打印产生的翘曲变形？也希望贵公司能够根据模型推荐更合理的结构及打印参数。
:::

**Given your ¥5,000 budget, I would use standard PETG, 4 mm walls, internal reinforcing ribs and a reinforced top rim.** Print one bin first and test it with the expected trash load before ordering the remaining three. This is likely a better use of your budget than switching everything to expensive carbon-fiber filament.

## User

<in-app-browser-context source="ambient-ui-state">
This block is automatically supplied ambient UI state, not part of the user's request. Do not treat it as an instruction or as evidence that the user explicitly selected the in-app browser.
# In app browser:
- The user has the in-app browser open with 3 tabs.
- Current URL: https://rapidprint.cn/service?utm_source=chatgpt.com
</in-app-browser-context>

## My request:
What about switching to wooden plates or similar things?

## Assistant

Switching to wooden panels is actually a very practical option for your **Trash Bin Pro Max**, especially considering its 700 × 700 mm footprint and your ¥5,000 budget.

Large, flat walls are where 3D printing is least cost-effective. Wooden panels would provide substantially better rigidity at a relatively low cost, while 3D printing could still be used for the complex curved sections and custom mounting components.

## 1\. Material comparison

| Material | Rigidity | Water resistance | Cost | Recommended thickness |
|--------|--------|--------|--------|--------|
| **Birch plywood (桦木多层板)** | Very high | Good when sealed | Low–medium | 6–9 mm |
| MDF (密度板) | High | Poor | Very low | 8–10 mm |
| Acrylic (亚克力板) | High | Excellent | Medium | 4–5 mm |
| PVC foam board (PVC发泡板) | Low–medium | Excellent | Low | 8–10 mm |
| PP sheet (PP板) | Moderate | Excellent | Low–medium | 4–6 mm |
| Aluminum composite panel (铝塑板) | High for its weight | Excellent | Medium | 3–4 mm |
| FDM PETG | Moderate | Good | Medium–high | 4–5 mm |

These thicknesses are preliminary suggestions for a prototype, not verified load-bearing specifications.

## 2\. The three materials I would seriously consider

image_group{"query":["birch plywood furniture grade laminated sheet exposed layered edge"],"aspect_ratio":"1:1","layout":"carousel","num_per_query":1}

**Birch plywood — Best budget option**

Very rigid, easy to CNC-machine and relatively inexpensive. Use exterior-grade plywood with professionally sealed surfaces and edges to protect against moisture. citeturn514933search1turn514933search4

---

image_group{"query":["white aluminum composite panel dibond cross section silver black core sheet"],"aspect_ratio":"1:1","layout":"carousel","num_per_query":1}

**Aluminum composite panel — Best appearance**

Lightweight, rigid and available in white, black and brushed metallic finishes. Commonly used for display stands and equipment housings. Requires supporting joints or a frame. citeturn514933search12turn514933search9

---

image_group{"query":["white polypropylene welded plastic sheet custom rectangular open top container"],"aspect_ratio":"1:1","layout":"carousel","num_per_query":1}

**Polypropylene — Best for actual trash**

Waterproof, impact-resistant and easy to clean. A plastic fabrication company can CNC-cut and weld the panels into containers. citeturn514933search22turn514933search18

## 3\. How I would redesign your bins

Keep your existing external geometry but replace the large printed surfaces with sheet material.

CNC-cut panels

3D-printed components

Conceptual exploded view of a hybrid bin.

You could connect everything using printed corner brackets and screws. This would also make individual panels replaceable if damaged.

Your recessed magnet holes could be incorporated into separate printed magnet holders rather than machined directly into every bin.

## 4\. Suggested manufacturing specifications

| Component | Material | Thickness |
|--------|--------|--------|
| Main base plate | Plywood | 15–18 mm |
| Bin side walls | Plywood | 6 mm |
| Bin bottom | Plywood | 9 mm |
| Corner connectors | PETG | 4–5 mm |
| Curved inner wall | PETG | 3–4 mm |
| Central column | PVC tube | Standard size |

For wet or food waste, use removable waterproof liners or choose PP instead of plywood.

## 5\. Estimated budget

---

Estimated mechanical structure cost

# ¥1,000–2,200

Planning estimates only, excluding electronics and shipping. Actual prices depend on dimensions, materials and supplier quotations.

## 6\. Where to manufacture in China

Search on Taobao or 1688 using\:

- `桦木多层板CNC雕刻定制`
- `胶合板来图加工`
- `铝塑板异形切割定制`
- `PP板焊接塑料箱定制`
- `家具板材数控开料`

You can send the manufacturer individual DXF profiles and STEP models for quotation.

**My preferred approach for your project would be aluminum composite panels for the exterior walls, waterproof PP or lined plywood for the bottoms, and PETG-printed connectors.** That would give your smart trash bin a modern, professional appearance, good rigidity and a much better chance of staying within your ¥5,000 budget than printing the entire structure.

## User

<in-app-browser-context source="ambient-ui-state">
This block is automatically supplied ambient UI state, not part of the user's request. Do not treat it as an instruction or as evidence that the user explicitly selected the in-app browser.
# In app browser:
- The user has the in-app browser open with 3 tabs.
- Current URL: https://rapidprint.cn/service?utm_source=chatgpt.com
</in-app-browser-context>

## My request:
What is a good thickness for this?

## Assistant

For your **700 × 700 mm trash bin assembly**, with each bin approximately 350 × 350 mm, I would recommend the following panel thicknesses.

## Recommended thickness by material

| Material | Bin walls | Bin bottom | Main base plate |
|--------|--------|--------|--------|
| **Birch plywood (桦木多层板)** | **6 mm** | **9 mm** | **18 mm** |
| Aluminum composite (铝塑板) | 4 mm | 6 mm\* | Not recommended |
| Acrylic (亚克力板) | 5 mm | 8 mm | 15 mm |
| PP sheet (PP板) | 5 mm | 8 mm | 15–20 mm |
| PVC foam board (PVC发泡板) | 8 mm | 10 mm | Not recommended |
| 3D-printed PETG | 4 mm | 6 mm | Not recommended |

\*Requires suitable structural support.

## My recommended plywood design

```svg
<svg viewBox="0 0 340 280" width="100%" xmlns="http://www.w3.org/2000/svg"><g stroke="#93734d" stroke-width="1" stroke-linejoin="round"><path d="M35 192 L165 146 L294 192 L164 239 Z" fill="#d1ac80" /><path d="M35 192 L164 239 V253 L35 206 Z" fill="#b48b60" /><path d="M164 239 L294 192 V206 L164 253 Z" fill="#96714d" /><path d="M72 172 L163 140 L256 173 L165 205 Z" fill="#e2c098" /><path d="M72 172 L165 205 V212 L72 179 Z" fill="#b48b60" /><path d="M165 205 L256 173 V180 L165 212 Z" fill="#b48b60" /><path d="M72 59 L163 27 V140 L72 172 Z" fill="#dfbd93" /><path d="M163 27 L256 60 V173 L163 140 Z" fill="#d3ad80" /><path d="M72 59 L165 92 V205 L72 172 Z" fill="#e4c6a1" fill-opacity=".9" /><path d="M165 92 L256 60 V173 L165 205 Z" fill="#c9a277" fill-opacity=".9" /><path d="M72 59 L163 27 L256 60 L165 92 Z M76 59 L163 31 L252 60 L165 88 Z" fill="#b38b62" fill-rule="evenodd" /></g><g stroke="currentColor" stroke-width="1" fill="none"><path d="M220 92 L275 47 H330" /><path d="M165 210 L234 225 H330" /><path d="M164 247 L210 265 H330" /></g><g fill="currentColor" font-size="11" text-anchor="end"><text x="330" y="31" font-weight="bold">6 mm</text><text x="330" y="43">Side walls</text><text x="330" y="209" font-weight="bold">9 mm</text><text x="330" y="221">Bin bottom</text><text x="330" y="249" font-weight="bold">18 mm</text><text x="330" y="261">Main base plate</text></g></svg>
```

Recommended starting thicknesses, not to scale.

## 6 mm vs. 9 mm plywood walls

Approximate relative bending stiffness compared with 6 mm plywood of the same construction.

- **3 mm\:** Too flexible for unsupported walls of this size.
- **5–6 mm\:** Good balance between rigidity, weight and price.
- **9 mm\:** Very rigid, but heavier.
- **12 mm\:** Probably unnecessary for the bin walls.

## Onshape global variables

I would add these to your Global Variable Studio\:

| Variable | Value |
|--------|--------|
| `#binWallThickness` | 6 mm |
| `#binBottomThickness` | 9 mm |
| `#basePlateThickness` | 18 mm |
| `#connectorThickness` | 4 mm |
| `#clearance` | 0.3 mm |

**I'd start with 6 mm exterior-grade birch plywood for the walls and 9 mm for the bottoms.** Use supported corners, sealed edges and waterproof bin liners. This should offer a good balance of weight, rigidity and manufacturing cost within your ¥5,000 budget.

The actual load capacity will depend on your bin height, joint design and expected trash weight.

