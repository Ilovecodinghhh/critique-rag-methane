## 5-7. Remaining Parameters (Appendix)

### Interhemispheric Exchange Time (τ_ex)



```
Parameter Name: Interhemispheric Exchange Time (τ_ex)
Current Value: 1.0 year (fixed, no uncertainty)
Literature Value: ~1.0 year nominal (Turner2017PNAS [2]), but Naus2019ACP [1, 4, 13] demonstrates that τ_ex is NOT fixed — it is species-dependent, time-varying, and exhibits significant trends and interannual variability. For CH₄ specifically, Naus et al. (2019) derive k_IH (the interhemispheric exchange rate, i.e., 1/τ_ex) from TM5 3-D simulations and find: (a) a positive trend of +0.35 ± 0.05% yr⁻¹ (p = 0.00) in k_IH for CH₄ over the simulation period; (b) notable interannual variability driven by meteorology; (c) substantial species-dependence (MCF shows dramatically different behavior including a minimum in 2000–2005). The nominal value of 1.0 yr is broadly consistent with Turner et al. (2017) who state "Interhemispheric exchange time is 1 y" in their two-box model schematic, but this is a simplification.
Status: OUTDATED
Reason for Change: 
1. **Time-dependence**: Naus2019ACP [13] explicitly shows that k_IH for CH₄ has a statistically significant positive trend (+0.35 ± 0.05% yr⁻¹), meaning τ_ex is decreasing over time. Over the model's 1999–2022 period, this amounts to a ~8% cumulative change — not negligible for a parameter that directly controls the NH-SH gradient and hence hemisphere-specific source attribution.

2. **Interannual variability**: Naus2019ACP [13] shows year-to-year fluctuations in k_IH driven by meteorological variability (confirmed by the near-zero variability found when annually repeating meteorology was used). Using a fixed value ignores this variability, which propagates into errors in the NH-SH emission partitioning.

3. **Species-dependence**: The effective τ_ex depends on the spatial distribution of sources and sinks of the species in question. For CH₄, with its strong NH source bias (the model itself uses FF 85/15, Mic 65/35 NH/SH splits), the effective exchange rate differs from that of an inert tracer like SF₆. Naus2019ACP [13] shows SF₆ has a different trend (+0.50 ± 0.01% yr⁻¹) than CH₄ (+0.35 ± 0.05% yr⁻¹).

4. **Systematic biases in two-box models**: Naus2019ACP [1] found that "substantial systematic biases exist in the interhemispheric mixing ratio gradients that are input to two-box model inversions" and that the absolute magnitude of derived global mean OH (and by extension CH₄ emissions) was affected by ~10% when bias corrections were applied. The interhemispheric exchange parameterization is one of the key sources of these biases.

5. **No uncertainty propagation**: The current model uses τ_ex = 1.0 yr as a fixed constant with zero uncertainty. Given that Naus et al. show meaningful variability and trends, this artificially suppresses uncertainty in the hemisphere-specific source estimates.

Suggested Action:
(a) **Minimum change**: Replace the fixed τ_ex = 1.0 yr with a time-varying parameterization that includes the trend identified by Naus2019ACP. Based on their CH₄-specific k_IH trend of +0.35% yr⁻¹:
   τ_ex(t) = τ_ex_ref / [1 + 0.0035 × (t − t_ref)]
   where τ_ex_ref ≈ 1.0 yr at t_ref ≈ 2000 (the approximate midpoint of the Naus et al. analysis period). This gives τ_ex(1999) ≈ 1.004 yr, τ_ex(2010) ≈ 0.966 yr, τ_ex(2022) ≈ 0.925 yr.

(b) **Better change**: Include τ_ex in the Monte Carlo sampling. Sample from a distribution such as:
   τ_ex(t) ~ Normal(μ = 1.0 / [1 + 0.0035 × (t − 2000)], σ = 0.05 yr)
   The σ = 0.05 yr (~5%) accounts for interannual meteorological variability shown in Naus2019ACP Figure 2 and the species-dependence uncertainty.

(c) **Best change (if feasible)**: Use year-specific k_IH values derived from a 3-D CTM simulation (as Naus et al. did with TM5), or at minimum use the Naus et al. CH₄-specific k_IH time series if it can be obtained from their supplementary data.

(d) **Structural consideration**: Naus2019ACP [1] found ~10% impact on absolute OH magnitude from bias corrections. Consider whether the NH/SH CH₄ gradient (currently linearly interpolated 80→100 ppb) is consistent with the chosen τ_ex — these are not independent parameters. The gradient should be observationally constrained and τ_ex should be consistent with it given the emission split.

Confidence: HIGH
The Naus2019ACP paper directly addresses this exact parameter for CH₄ in a two-box model framework, using a state-of-the-art 3-D CTM (TM5) to derive the effective exchange rate. The finding of time-dependence and species-dependence is robust (statistically significant trend, confirmed by sensitivity tests with fixed meteorology). Turner2017PNAS confirms the nominal ~1 yr value but does not address its variability.

Validation Test:
1. **Sensitivity experiment**: Run the full Monte Carlo ensemble three times:
   (a) τ_ex = 1.0 yr fixed (current);
   (b) τ_ex(t) with −0.35% yr⁻¹ trend (Naus2019ACP);
   (c) τ_ex sampled from Normal(μ(t), σ=0.05 yr).
   Compare: (i) NH vs SH source partitioning (BB, FF, Mic); (ii) posterior uncertainty envelopes; (iii) the implied NH-SH CH₄ gradient vs observations. If the NH-SH gradient in case (b) better matches NOAA surface observations than case (a), this validates the trend.

2. **Consistency check**: Verify that the model's NH-SH CH₄ gradient (80→100 ppb) is self-consistent with τ_ex and the prescribed NH/SH emission ratios. Compute the steady-state gradient implied by the emission split and τ_ex:
   ΔCH₄ ≈ (S_NH − S_SH) × τ_ex / (2 × M_atm_hemisphere)
   If this doesn't match 80–100 ppb, either τ_ex or the emission ratios need adjustment.

3. **Impact on isotope budgets**: The NH-SH isotopic offsets (currently ±1.5‰ for δD) are coupled to τ_ex. Check whether varying τ_ex changes the implied δD NH-SH offset and whether the result is more or less consistent with any available hemisphere-specific δD observations.
```

---

### NH/SH Emission Ratios



```
Parameter Name: NH/SH Emission Ratios — Fossil Fuel (FF)
Current Value: NH 85% / SH 15%
Literature Value: Feinberg2018JGR provides EDGAR-based hemispheric emission fractions showing NH fossil fuel subcategories (coal ~10% of NH total, gas ~20% of NH total) versus SH (coal ~2%, gas ~4%), consistent with heavily NH-dominated fossil fuel emissions. Saunois2016ESSD Figure 3 shows fossil fuel emission spatial distribution overwhelmingly concentrated in NH (Russia, Middle East, China, North America). He2026Science reports oil/gas emission decreases 2019–2024 but does not provide explicit NH/SH split. No paper in the provided context gives a single explicit "85/15" ratio, but the spatial distributions in Saunois2016ESSD and the fractional breakdowns in Feinberg2018JGR are broadly consistent with ~83–88% NH. Chen2006JGR notes coal emissions are "dominated by Northern Hemispheric sources." Basu2022ACP attributes fossil changes primarily to "northern extratropics."
Status: CONFIRMED
Reason for Change: The 85/15 split is well-supported by the spatial distribution of fossil fuel infrastructure. EDGAR-based inventories consistently show >80% of fossil CH₄ in the NH. However, the ratio should not be treated as time-invariant: He2026Science documents shifting oil/gas patterns 2019–2024, and growing SH fossil activity (e.g., Australian coal, South American oil/gas) could push the SH fraction slightly higher over time. Feinberg2018JGR's Table shows coal at 10% NH vs 2% SH and gas at 20% NH vs 4% SH, which when combined with other fossil subcategories yields roughly 83–87% NH depending on year and inventory version.
Suggested Action: Retain 85/15 as central estimate. Consider implementing a ±3% uncertainty on the NH fraction (i.e., NH_FF ~ U[0.82, 0.88]) in the Monte Carlo sampling to propagate this structural uncertainty. If time-varying EDGAR v8 data are available per hemisphere, replace the fixed ratio with year-specific values.
Confidence: HIGH
Validation Test: Run sensitivity experiments with NH_FF = 0.80 and NH_FF = 0.90 and examine the impact on inferred FF emissions and δ¹³C source signatures in each hemisphere. The NH/SH CH₄ gradient (80–100 ppb) should be compared against the model-predicted gradient under each ratio to check consistency.
```

```
Parameter Name: NH/SH Emission Ratios — Microbial (Mic)
Current Value: NH 65% / SH 35%
Literature Value: Feinberg2018JGR shows wetlands (M-WET) at NH 21% of NH total vs SH 55% of SH total, indicating wetlands are SH-dominated relative to total emissions. However, ruminants (M-COW) are NH 21% vs SH 16%, and rice is predominantly NH. Saunois2016ESSD Figure 3 shows wetland emissions concentrated in tropical regions spanning both hemispheres (Amazon, Congo, Southeast Asia) with significant boreal NH wetlands. Basu2022ACP finds the "largest contribution to the global increase in microbial emissions between the two periods comes from the tropics." He2026Science identifies East Africa and South America (straddling equator but largely SH) as most responsible for 2019–2024 emission increases, with livestock and waste increases offsetting oil/gas decreases. Nisbet2023GBC notes marked growth in "southern outer tropics around 2018 (e.g., Pantanal wetland)" and tropical dominance of methane growth. Saunois2025ESSD is referenced but the provided excerpt does not give explicit NH/SH microbial splits.
Status: POTENTIALLY OUTDATED
Reason for Change: The 65/35 split aggregates wetlands, ruminants, rice, landfills/waste, and termites. While rice and some ruminant emissions are NH-dominated, tropical and SH wetlands are enormous. The Feinberg2018JGR data suggest wetlands alone could be ~40–55% SH when weighted by total hemispheric emissions. He2026Science's finding that East Africa and South America drove 2019–2024 increases suggests the SH microbial fraction may be growing over time. A fixed 65/35 may underestimate SH microbial contributions, particularly for recent years (post-2015). The aggregate ratio depends critically on how tropical emissions near the equator (0–10°S) are partitioned — many "tropical" sources (Amazon, Congo) straddle the meteorological equator but are geographically SH. If the ITCZ position is used rather than the geographic equator, the NH fraction could be somewhat higher.
Suggested Action: (1) Decompose microbial into sub-categories with separate NH/SH ratios: wetlands ~55/45 to 50/50, ruminants ~70/30, rice ~85/15, waste ~65/35, termites ~45/55, then compute the aggregate ratio from bottom-up inventories year by year. (2) As a simpler fix, shift to NH 60% / SH 40% (±5%) to better reflect the growing tropical/SH microbial contribution documented in He2026Science and Nisbet2023GBC. (3) Implement time-varying microbial NH/SH ratios if CT-CH₄ posteriors provide this information.
Confidence: MEDIUM
Validation Test: (1) Run the two-hemisphere model with Mic NH/SH = 60/40 vs 65/35 vs 55/45 and compare predicted NH–SH δ¹³C gradients against observations (the NH should be isotopically heavier due to more fossil fuel; shifting more microbial to SH should lighten SH δ¹³C). (2) Compare predicted interhemispheric CH₄ gradient against observed 80–100 ppb gradient — a higher SH microbial fraction would reduce the gradient, providing a constraint. (3) Check whether the model can reproduce the post-2007 δ¹³C decline documented in Nisbet2023GBC and Basu2022ACP under different NH/SH microbial splits.
```

```
Parameter Name: NH/SH Emission Ratios — Biomass Burning (BB)
Current Value: NH 55% / SH 45%
Literature Value: Feinberg2018JGR Table shows BB (M-BB) at NH 2% of NH total vs SH 6% of SH total, indicating BB is relatively more important in the SH. Saunois2016ESSD Figure 3 shows biomass burning emissions concentrated in tropical Africa (both hemispheres), South America (SH), and Southeast Asia (NH), with substantial SH contribution. Turner2017PNAS notes "evidence from the satellite record of CO pointing to a decrease in Southern Hemispheric biomass burning since 2001" and finds SH isotopically heavy sources (such as BB) may have decreased. Acquah2025ACP reports "strong increase in the biomass burning emissions" in the SH in their EMIS-02 scenario. Fujita2025JGR uses BB scaling factors but does not provide explicit NH/SH splits. No paper in the context provides a definitive single NH/SH BB ratio.
Status: POTENTIALLY OUTDATED
Reason for Change: The 55/45 NH/SH split for BB appears to overweight the NH. Most major biomass burning regions are in the tropics and SH: African savanna burning (a large fraction south of equator), South American deforestation fires (Amazon, Cerrado), and Australian fires. NH BB sources include boreal fires (Canada, Siberia) and some Southeast Asian burning. GFED-based analyses typically show ~35–45% NH and ~55–65% SH for fire-related CH₄ emissions, though this varies enormously year to year (e.g., 2019–2020 Australian fires, 2023 Canadian fires). The Feinberg2018JGR fractions (2% NH vs 6% SH of respective hemispheric totals) suggest BB is proportionally much more important in the SH. Turner2017PNAS's finding of decreasing SH BB could shift the ratio toward NH in recent years, but the baseline should likely be closer to 45/55 or even 40/60 (NH/SH). The current 55/45 may reflect an older EDGAR distribution that included biofuel burning (more NH-weighted) alongside open biomass burning.
Suggested Action: (1) Reverse the ratio to NH 40–45% / SH 55–60% based on GFED5 open fire distributions, or at minimum use 50/50. (2) Make the ratio time-varying using annual GFED5 data, as BB has enormous interannual variability (e.g., El Niño years shift burning toward tropical SH). (3) Separate biofuel (NH-dominated) from open biomass burning (SH-dominated) if the model's BB category includes both. (4) Sample the NH fraction as U[0.35, 0.55] in Monte Carlo to capture interannual variability.
Confidence: MEDIUM
Validation Test: (1) Compare model-predicted SH δ¹³C with observations under BB NH/SH = 55/45 vs 45/55 — BB is isotopically heavy (~−22‰), so shifting more BB to SH should make SH δ¹³C heavier, which can be checked against the observed NH–SH δ¹³C gradient. (2) Correlate year-to-year changes in the GFED5-derived NH/SH BB ratio with observed interannual variability in the interhemispheric δ¹³C gradient. (3) Use CO observations (which co-vary with BB) as an independent constraint on the hemispheric BB distribution, following the approach noted in Turner2017PNAS.
```

```
Parameter Name: NH/SH Emission Ratios — Aggregate structural treatment
Current Value: Fixed ratios applied uniformly across all years (FF 85/15, Mic 65/35, BB 55/45)
Literature Value: He2026Science documents significant interannual variability in emission patterns 2019–2024, with "global emissions increased from 571 Tg per year in 2019 to 601 Tg per year in 2021 and back to 575 Tg per year in 2024" and identifies East Africa and South America as key growth regions. Nisbet2023GBC Figure 13 shows the methane growth rate varies dramatically by latitude band and year, with tropical dominance shifting between NH and SH tropics. Basu2022ACP shows source-specific emissions varying by latitude band over time. Turner2017PNAS uses a two-box model with time-varying hemispheric source isotopic compositions.
Status: OUTDATED (structural issue)
Reason for Change: Using fixed NH/SH ratios ignores well-documented interannual variability in the spatial distribution of emissions. ENSO cycles shift wetland and fire emissions between hemispheres. Secular trends (e.g., growth of SH livestock, decline of NH coal mining in some regions, growth of SH fossil fuel extraction) alter the ratios over the 1999–2022 study period. He2026Science's finding that emission trends reversed between 2019–2021 and 2022–2024 underscores that fixed ratios are inadequate for capturing recent dynamics.
Suggested Action: (1) Replace fixed ratios with time-varying ratios derived from annual EDGAR (for FF), GFED5 (for BB), and CT-CH₄ or wetland model ensembles (for Mic). (2) If annual data are unavailable, at minimum implement decadal shifts (e.g., 2000–2009 vs 2010–2022) and sample the ratios with appropriate uncertainty in the Monte Carlo. (3) Add the NH/SH ratio uncertainty to the Monte Carlo sampling: for each iteration, draw NH_FF ~ U[0.82, 0.88], NH_Mic ~ U[0.55, 0.70], NH_BB ~ U[0.35, 0.55].
Confidence: HIGH
Validation Test: (1) Run the two-hemisphere model with fixed vs time-varying NH/SH ratios and compare the residuals in the NH and SH mass balance equations — time-varying ratios should reduce systematic residuals. (2) Compare the model's predicted NH–SH CH₄ concentration gradient against NOAA observations for each year; fixed ratios may produce a gradient that drifts from observations. (3) Perform a leave-one-year-out cross-validation: fit the model on all years except one, predict the left-out year's NH and SH concentrations and isotope values, and compare RMSE between fixed and time-varying ratio versions.
```

**Summary Assessment:**

The FF 85/15 ratio is well-supported and can be retained with minor uncertainty sampling. The Mic 65/35 ratio is likely slightly too NH-heavy given growing evidence of tropical/SH microbial emission importance (He2026Science, Nisbet2023GBC, Basu2022ACP) — a shift toward 60/40 is recommended. The BB 55/45 ratio appears to be in the wrong direction relative to GFED-based fire distributions, which typically show SH-dominated open biomass burning — reversal to ~45/55 is recommended. Most critically, all three ratios should be treated as uncertain parameters in the Monte Carlo framework and ideally made time-varying, as the provided literature documents substantial interannual and decadal shifts in the spatial distribution of methane sources.

**Key limitation of this review:** The provided research context does not include Saunois et al. (2020) — the cited source for the current ratios — nor does it include GFED5 documentation or detailed EDGAR v8 hemispheric breakdowns. A definitive quantitative update would require those primary sources. The recommendations above are based on indirect evidence from the 20 papers provided.

---

### NH/SH Lifetime Ratio



```
Parameter Name: NH/SH Lifetime Ratio (CH₄ lifetime asymmetry between hemispheres)
Current Value: NH: 0.95×τ_global, SH: 1.05×τ_global (i.e., NH/SH lifetime ratio = 0.905)
Current Source: "Prather 2012, Lawrence 2001 approximation"

Literature Value: 
The research context does not provide a single, directly quoted NH/SH CH₄ lifetime ratio, but the parameter is tightly coupled to the NH/SH OH ratio, which is extensively discussed. The key constraint is:

- Patra et al. (2014) [Patra2014Nature]: NH/SH OH ratio = 0.98 ± 0.12 (observation-based, from CH₃CCl₃ gradients, 2004–2011). This implies near-parity in hemispheric OH, and therefore near-parity in CH₄ lifetime (NH/SH lifetime ratio ≈ 1.0, or perhaps ~0.98–1.02 given other sink asymmetries).

- Zhang et al. (2021) [Zhang2021NatComm]: Posterior NH/SH OH ratio = 1.02 ± 0.05, compared to prior of 1.16 and ACCMIP ensemble mean of 1.28 ± 0.10. This is "more consistent with the observation-based estimate of 0.97 ± 0.12 (Patra et al., 2014)."

- Naik et al. (2013) [Naik2013ACP]: ACCMIP models simulate NH/SH OH ratios of 1.13–1.42 for present-day, but these are acknowledged to be biased high relative to observations, partly due to low CO biases in the NH.

- Zhao et al. (2023) [Zhao2023ACP]: Observation-constrained OH fields reduce model NH/SH OH ratios from 1.35→1.24 (CESM1) and 1.26→1.15 (GEOSCCM), still higher than MCF-based estimates of ~1.0.

- Lelieveld et al. (2016) [Lelieveld2016ACP]: Air-mass-weighted NH/SH OH ratio = 1.20–1.25 in their model; correcting for ITCZ position reduces this to ~1.13. Including the lower stratosphere brings it to near-parity (~1.02–1.05).

- Bousquet et al. (2005) [Bousquet2005ACP]: Optimized NH/SH OH ratio = 0.85 (i.e., more OH in SH), though this is an outlier relative to more recent estimates.

- Lawrence et al. (2001) [Lawrence2001ACP]: Model-based, shows >60% of CH₄ oxidation occurs in the tropical lower troposphere; NH/SH asymmetry in oxidation is driven primarily by extratropical differences.

- Naus et al. (2019) [Naus2019ACP]: Found "significant deviations in the magnitude and time-dependence" of two-box model parameters relative to 3-D simulations, including exposure to OH, cautioning that simple NH/SH parameterizations can be systematically biased.

Converting OH ratio to lifetime ratio: Since τ_CH₄ ∝ 1/[OH] (to first order, for the OH sink which dominates), an NH/SH OH ratio of ~1.0 implies an NH/SH CH₄ lifetime ratio of ~1.0 as well. However, the CH₄ lifetime also depends on CH₄ abundance (higher in NH), temperature (affecting rate constant k_CH₄+OH), and non-OH sinks (soil, Cl, stratosphere). The current model's NH/SH lifetime ratio of 0.905 implies an effective NH/SH OH ratio of ~1.10, which sits between the observation-based estimates (~0.97–1.02) and the uncorrected model estimates (~1.13–1.42).

Status: OUTDATED

Reason for Change:
The current parameterization (NH lifetime = 0.95×τ, SH = 1.05×τ, giving NH/SH ratio = 0.905) implies substantially more OH in the NH than the SH (effective OH ratio ~1.10). This is inconsistent with the most robust observation-based constraints:

1. Patra et al. (2014) find NH/SH OH ≈ 0.98 ± 0.12 from CH₃CCl₃, the gold-standard tracer for hemispheric OH.
2. Zhang et al. (2021) find a posterior NH/SH OH ratio of 1.02 ± 0.05 from a full inversion.
3. Multiple studies (Naik2013ACP, Zhao2023ACP, Lelieveld2016ACP) acknowledge that chemistry-climate models systematically overestimate the NH/SH OH asymmetry, partly due to NH CO underestimation.

The current value appears to derive from older model-based estimates (Lawrence 2001 gives model OH distributions with NH>SH, and Prather 2012 provides a total lifetime framework). However, the observation-based literature has converged toward near-hemispheric parity in OH, which would imply a much smaller lifetime asymmetry.

Physically, the remaining lifetime asymmetry should account for:
(a) The temperature-dependent rate constant k_CH₄+OH: NH troposphere is slightly cooler on average than SH tropics-weighted mean, which would slightly increase NH lifetime.
(b) Higher CH₄ burden in NH means more CH₄ per unit OH, but this is already captured in the mass balance.
(c) Non-OH sinks: soil uptake is larger in NH (more land area), Cl is debated, stratospheric loss is roughly symmetric. These partially offset each other.

A reasonable estimate: if NH/SH OH ratio ≈ 1.0 (observation-based), then the NH/SH lifetime ratio for OH loss alone is also ~1.0. Including the slight NH enhancement of soil sink and possibly Cl, the effective NH lifetime might be ~0.98×τ_global and SH ~1.02×τ_global, rather than the current 0.95/1.05.

Suggested Action:
Replace the current fixed 0.95/1.05 split with a parameterization informed by observation-based OH constraints:

Option A (Recommended): 
  NH: τ_NH = 0.98 × τ_global (± 0.03)
  SH: τ_SH = 1.02 × τ_global (± 0.03)
  This corresponds to an effective NH/SH OH ratio of ~1.04, consistent with Zhang et al. (2021) posterior of 1.02 ± 0.05 plus a small additional asymmetry from non-OH sinks.

Option B (Monte Carlo sampling):
  Sample the NH/SH OH ratio from N(1.02, 0.05²) following Zhang et al. (2021), then compute:
    τ_NH = τ_global × 2 / (1 + R_OH)
    τ_SH = τ_global × 2·R_OH / (1 + R_OH)
  where R_OH = [OH]_NH / [OH]_SH, and additionally apply small corrections for hemispheric differences in non-OH sinks (soil: NH gets ~0.5% shorter lifetime; Cl: uncertain).

Option C (If retaining simplicity):
  At minimum, narrow the asymmetry to NH: 0.99×τ, SH: 1.01×τ, which is more consistent with Patra et al. (2014).

Note: Naus et al. (2019) caution that two-box model parameters derived from 3-D simulations show "significant deviations" and time-dependence, so any fixed ratio is an approximation. The uncertainty on this parameter should be explicitly sampled in the Monte Carlo framework.

Confidence: MEDIUM-HIGH

The direction of the correction (toward less asymmetry) is robust across multiple independent studies using different methods (CH₃CCl₃ inversions, satellite-constrained OH fields, full atmospheric inversions). However, the exact value remains uncertain because:
- Models and observations still disagree on the sign and magnitude of the NH/SH OH asymmetry
- The ITCZ position complicates the definition of "hemispheric" (Lelieveld2016ACP, Lawrence2001ACP)
- Naus et al. (2019) show that 3-D-derived two-box parameters are time-dependent and species-dependent
- The non-OH sink contributions to hemispheric lifetime asymmetry are not well constrained in the provided literature

Validation Test:
1. **MCF consistency test**: Run the two-hemisphere model with CH₃CCl₃ as a passive tracer using the same OH fields implied by the lifetime parameterization. Compare the predicted NH-SH CH₃CCl₃ gradient against AGAGE/NOAA observations for 2004–2011 (the period used by Patra et al. 2014). The current 0.95/1.05 split should produce too large an interhemispheric MCF gradient (too much OH in NH), while the corrected 0.98/1.02 should better match observations.

2. **Sensitivity sweep**: Run the full dual-isotope Monte Carlo with NH/SH lifetime ratios spanning 0.90/1.10 to 1.00/1.00 in steps of 0.02. Examine:
   (a) Impact on NH vs SH source partitioning (BB, FF, Mic)
   (b) Impact on the interhemispheric CH₄ gradient (should match observed 80–100 ppb NH-SH difference)
   (c) Impact on isotopic gradients (δ¹³C and δD NH-SH offsets)
   
3. **Cross-check with Turner et al. (2017)**: Their two-box model (Fig. 3, middle panel) shows the NH/SH OH ratio time series. Compare the implied lifetime ratio from their most likely solution against the model's fixed parameterization.

4. **Isotopic sensitivity**: The NH/SH lifetime ratio affects the bulk KIE differently in each hemisphere. Test whether the corrected ratio changes the inferred source-weighted isotopic signatures and whether this improves or degrades agreement with observed δ¹³C and δD NH-SH offsets.
```

---

