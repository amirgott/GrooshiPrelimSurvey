# Response Segmentation

Status: Planned

Used by: `/process-issues` skill (step 3b.4). Also the researcher's tracing reference for why a category was assigned.

---

## Step 1 — Derive before classifying

| Derivation | Formula |
|------------|---------|
| `age_youngest` | min of all `1.1_kid_age_*` values |
| `age_oldest` | max of all `1.1_kid_age_*` values |
| `kids_under_10` | count of `1.1_kid_age_*` < 10 |
| `tension_max` | max(`2.2_emotional_tension`, `2.2_org_difficulty`) |
| `tension_type` | `"emotional"` if `2.2_emotional_tension` > `2.2_org_difficulty`; `"organizational"` if reverse; `"balanced"` if equal |
| `friction_area_count` | count of selected `3.1_areas` values |
| `friction_quality_min` | min of quality scores for selected areas |
| `friction_quality_avg` | avg of quality scores for selected areas (1 decimal) |

If step 3 was skipped (safety routing): treat `friction_area_count` as 0 and all quality scores as N/A — do not interpret absence of friction areas as low-conflict.

---

## Step 2 — Evaluate segments

Evaluate each segment independently. Assign the best-fit **primary** segment; assign a **second** only when evidence is clearly split. Maximum two segments in output.

Segments marked **[exclusive]** block all others if assigned. Segments marked **[combinable]** are typically secondary.

---

### Safety-critical / Coercive Control `[exclusive]`

Respondent does not feel safe communicating with the other parent — threats, aggression, or coercive control patterns present. Step 3 is skipped; read need signal only. Assign no other segment.

| | |
|-|-|
| **Decisive** | `2.1_safety` == `"לא"` (respondent does not feel safe) |
| **Supporting** | `2.3_legal` == `"כן"` · `2.3_legal_type` includes `"גט"` or `"משמורת"` |
| **Notes** | Step 3 absent — do not read zero friction areas as low-conflict. Read step 4 need signal and `2.1_safety_detail` only. Assign no other segment. |

---

### High-conflict / Court-adjacent

Active legal proceedings combined with very poor communication and high tension. The dynamic is adversarial, not merely difficult — conflict has entered institutional channels.

| | |
|-|-|
| **Decisive** | `2.3_legal` == `"כן"` AND `2.2_comm_quality` ≤ 2 AND `tension_max` ≥ 3 |
| **Supporting** | `friction_quality_min` == 1 · `2.3_legal_type` includes `"משמורת"` · `tension_type` == `"emotional"` · `3_tasks_not_done` == `"כן"` |
| **Notes** | `2.3_legal_type` == `"מזונות"` alone (no custody/property dispute) does not trigger this segment — route to Financially-stressed instead. `age_oldest` ≥ 15 + `"משמורת"` strengthens read. |

---

### Angry Associates

Moderate-to-high conflict without active litigation. Communication is poor and tension elevated, but the situation has not escalated to court.

| | |
|-|-|
| **Decisive** | `2.2_comm_quality` ≤ 2 AND `tension_max` in 2–3 AND `2.3_legal` != `"כן"` |
| **Supporting** | `friction_area_count` ≥ 2 · `3_decisions_friction` or `3_schedule_friction` elevated · `tension_type` == `"emotional"` · `3_tasks_not_done` == `"כן"` |
| **Notes** | If `2.3_legal` == `"כן"` but `tension_max` < 3, still consider this segment over High-conflict. |

---

### Cooperative Colleagues

Good communication and low tension despite real operational friction. Logistics are hard because of coordination volume with young kids, not because of interpersonal conflict.

| | |
|-|-|
| **Decisive** | `2.2_comm_quality` ≥ 3 AND `tension_max` ≤ 2 AND `friction_area_count` ≥ 1 AND `kids_under_10` ≥ 1 |
| **Supporting** | Friction in `"שגרה ומטלות"` or `"שינויי לו"ז"` · `tension_type` == `"organizational"` · `3_tasks_not_done` == `"כן"` despite decent comm |
| **Notes** | Defining pattern: logistics friction despite cooperation — friction is structural, not conflictual. `kids_under_10` ≥ 1 required; absence of young kids shifts to Boundary-first. |

---

### Boundary-first / Parallel Parents

Low conflict achieved by minimizing contact surfaces. Few friction areas because they have structurally reduced interaction — not because co-parenting is inherently smooth.

| | |
|-|-|
| **Decisive** | `2.2_comm_quality` in 2–3 AND `tension_max` ≤ 2 AND `friction_area_count` ≤ 1 |
| **Supporting** | `1.1_custody` == `"משמורת מלאה שלי"` · few areas selected despite moderate tension |
| **Notes** | Distinguish from Cooperative Colleagues by low `friction_area_count` — they've minimized contact surfaces by design. Non-custodial respondent (`1.1_custody` == `"משמורת מלאה של ההורה האחר"`): expect financial friction without logistics friction; weight Financially-stressed or High-conflict accordingly. |

---

### Financially-stressed `[combinable]`

Financial management and expense transparency are the dominant friction source. Frequently overlaps with other conflict segments as a secondary dimension.

| | |
|-|-|
| **Decisive** | `3.1_areas` includes `"ניהול כספים והוצאות"` AND `3_finances_quality` ≤ 2 |
| **Supporting** | `2.3_legal_type` includes `"מזונות"` · `4_barriers` contains financial language · `tension_type` == `"organizational"` · `1.1_custody` == `"משמורת מלאה של ההורה האחר"` (non-custodial) |
| **Notes** | Frequently combines with Angry Associates or High-conflict. Assign as secondary when another segment is primary and financial friction is present. |

---

### Complex-care Coordinators `[combinable]`

Medical, therapeutic, or special-needs coordination adds a layer of complexity beyond ordinary logistics. Often present alongside another primary segment.

| | |
|-|-|
| **Decisive** | `3.1_areas` includes `"בריאות וצרכים מיוחדים"` AND `3_special_quality` ≤ 2 |
| **Supporting** | Age mix (some `< 10`, some `≥ 10`) · `2.2_org_difficulty` elevated · `friction_area_count` ≥ 2 |
| **Notes** | Age mix amplifies this read even without an explicit special-needs flag. Assign alongside primary segment. |

---

### Distance / Relocation `[combinable]`

Geographic separation structurally amplifies logistics and scheduling friction regardless of conflict level. Lowers thresholds for other segment criteria.

| | |
|-|-|
| **Decisive** | `1.1_distance` == `"עיר אחרת"` or `"חו"ל"` |
| **Supporting** | `3.1_areas` includes `"שינויי לו"ז"` · `2.2_org_difficulty` elevated · high `friction_area_count` despite moderate emotional tension |
| **Notes** | Distance amplifies all friction readings — lower thresholds for other segment criteria by 1 scale point when present. Usually secondary; assign as primary only when distance is the dominant stated pain. |

---

### Blended-family / New Partners `[combinable]`

New romantic partners on either side introduce schedule complexity and decision-making friction beyond the original co-parenting dynamic. Almost always secondary.

| | |
|-|-|
| **Decisive** | `1.2_new_partner` != `"לאף אחד"` |
| **Supporting** | Friction concentrated in `"שינויי לו"ז"` or `"קבלת החלטות"` |
| **Notes** | Almost always secondary. New partner status also amplifies schedule and decision friction interpretation in any other segment, even when Blended-family is not assigned. |

---

## Step 3 — Apply modifiers

Modifiers are listed alongside the segment(s) in the output. Multiple modifiers can apply simultaneously.

| Modifier | Signal | Classification impact |
|----------|--------|----------------------|
| **Get-Trapped** | `1.2_religious_divorce` == `"בתהליך"` or `"עיגון"` | Overlays segments 3, 6, 8; adds legal-emotional dimension independent of civil proceedings |
| **Newly Separated** | `1.1_time_since_sep` == `"עד שנה"` | All scores provisional — co-parenting pattern not yet stable; treat need signal cautiously |
| **Still Separating** | `1.1_time_since_sep` == `"עדיין פרודים"` | No stable arrangement yet; friction and need signals are pre-arrangement baseline, not ongoing patterns |
| **Young kids** | `kids_under_10` ≥ 1 | Logistics friction structural — lower bar for Cooperative Colleagues; שגרה friction less diagnostic of conflict |
| **Older kids only** | `age_youngest` ≥ 13 | Logistics friction expected to decrease; reduce weight of שגרה ומטלות; elevate weight of קבלת החלטות |

---

## Step 4 — Post-classification coherence checks

| Pattern | Trigger | Action |
|---------|---------|--------|
| WTP without friction | `4_wtp` == `"כן"` but `friction_area_count` == 0 and `tension_max` ≤ 1 | Add coherence warning |
| Many areas, low tension | `friction_area_count` ≥ 3 but `tension_max` ≤ 1 | Confirms Cooperative Colleagues even if quality scores are poor |
| Tension asymmetry — emotional | `tension_type` == `"emotional"` with low `friction_area_count` | Consider Angry Associates even if fewer areas selected |
| Tension asymmetry — organizational | `tension_type` == `"organizational"` with high `friction_area_count` | Strengthens logistically-overwhelmed read within the primary segment |
| Segment–score mismatch | Primary segment implies high conflict but `friction_quality_avg` > 2.5, or vice versa | Add coherence warning |
