# Current Box Model: Dual-Isotope (δ¹³C + δD) Monte Carlo Mass Balance

## Overview
A global methane (CH₄) source partitioning model that uses two stable isotope systems (δ¹³C-CH₄ and δD-CH₄) to separate total emissions into three categories: **Biomass Burning (BB)**, **Fossil Fuel (FF)**, and **Microbial (Mic)**.

## Model Versions

### v2.0 — One-Box Upgraded (`upgraded_box_model.py`)
- Global one-box atmosphere
- 3×3 linear system: mass balance + δ¹³C + δD → solve for BB, FF, Mic simultaneously
- 1000 Monte Carlo iterations with KIE sampling
- Time-varying lifetime τ(t)
- Direct matrix inversion (`np.linalg.solve`)

### v3.0 — Two-Hemisphere (`two_hemisphere_box_model.py`)
- NH/SH two-box with interhemispheric exchange (τ_ex = 1.0 yr)
- Per-hemisphere mass balance and isotope budgets
- Bounded least-squares solver (`scipy.optimize.lsq_linear`) with non-negativity
- NH-specific and SH-specific sink fractions and lifetimes
- NH/SH emission ratios: FF 85/15, Mic 65/35, BB 55/45

### v3.1 — Optimized 3×3 (`v3.1_optimized_3x3.py`)
### v3.2 — BB Fixed 2×2 (`v3.2_bb_fixed_2x2.py`)
### v3.3 — δD Comparison (`v3.3_dD_comparison.py`)
### v4.0 — Mic vs Non-Mic (`v4.0_mic_vs_nonmic.py`)

## Governing Equations

### One-Box Mass Balance (v2.0)
For year j, total source:
```
S_total(j) = [CH₄](j+1)·PT − [CH₄](j)·PT + [CH₄](j)·PT / τ(j)
```
where PT = 2.815 (ppb → Tg conversion), τ(j) is time-varying lifetime.

### Isotope Mass Balance
For heavy-isotope fraction f (either ¹³C or D):
```
f_source(j) · S_total(j) = n(j+1) − n(j) + n(j) · α / τ(j)
```
where n(j) = f_atm(j) · [CH₄](j) · PT, and α = 1/KIE_bulk.

### 3×3 Linear System (v2.0, v3.0)
```
[1        1        1      ] [BB ]   [S_total        ]
[f13_BB   f13_FF   f13_Mic] [FF ] = [S_total·f13_src]
[fD_BB    fD_FF    fD_Mic ] [Mic]   [S_total·fD_src ]
```

### Two-Hemisphere (v3.0)
Per hemisphere h ∈ {NH, SH}:
```
S_h = M_h(t+1) − M_h(t) + M_h(t)/τ_h − (M_other(t) − M_h(t))/τ_ex
```
Isotopic exchange terms couple the hemispheres:
```
f_src_h · S_h = d(f·M)_h/dt + (f·M)_h · α_h/τ_h − exchange_isotopic
```

## Current Parameter Values

### Kinetic Isotope Effects (KIE)
| Parameter | Distribution | Range/Value | Source |
|-----------|-------------|-------------|--------|
| OH_KIE_13C | Uniform | 1.0039 – 1.0054 | Saueressig 2001 – Cantrell 1990 |
| OH_KIE_D | Uniform | 1.294 – 1.327 | Saueressig 2001 – Whitehill-Joelson |
| Cl_KIE_13C | Normal | 1.066 ± 0.002 | Saueressig 1995 |
| Cl_KIE_D | Normal | 1.52 ± 0.02 | Saueressig 2001 |
| Strat_KIE_13C | Fixed | 1.003 | Lassey 2007 |
| Strat_KIE_D | Fixed | 1.179 | Dyonisius 2020; Beck 2018 |
| Soil_KIE_13C | Fixed | 1.0201 | Avg of Snover & Quay; Tyler; Reeburgh |
| Soil_KIE_D | Fixed | 1.083 | Snover & Quay 2000 |

### Sink Fractions (Global)
| Sink | Fraction |
|------|----------|
| OH | 0.835 |
| Cl | 0.035 |
| Stratosphere | 0.07 |
| Soil | 0.06 |

### Sink Fractions (Hemisphere-Specific, v3.0)
| Sink | NH | SH |
|------|-----|-----|
| OH | 0.825 | 0.850 |
| Cl | 0.040 | 0.028 |
| Strat | 0.070 | 0.070 |
| Soil | 0.065 | 0.052 |

### Time-Varying Lifetime
```
τ(t) = 9.0 − 0.017 × (t − 2010)
```
- τ(1999) = 9.19 yr, τ(2010) = 9.00 yr, τ(2022) = 8.80 yr
- NH: τ × 0.95; SH: τ × 1.05
- **NOTE**: This is a LINEAR PARAMETERIZATION, not actual data from He et al. (2026)

### Source Isotopic Signatures
| Source | δ¹³C (‰) | δD (‰) | Notes |
|--------|-----------|---------|-------|
| Fossil Fuel | Time-varying (~−44) | Time-varying (~−186) | From EDGAR8 MC sampling |
| Microbial | ~−62 (time-varying) | ~−299 (time-varying) | From CT-CH4 posterior fractions |
| Biomass Burning | ~−22 (time-varying) | ~−217 (time-varying) | From GFED5/C3-C4 distributions |
| mic_dd_U (uncertainty) | — | **Fixed at 7‰** | Should be data-derived |

### Interhemispheric Exchange (v3.0)
- τ_ex = 1.0 year
- NH/SH CH₄ gradient: linearly interpolated 80→100 ppb (1999→2022)
- δD NH-SH offset: ±1.5‰ (approximation)

### Emission Ratios (v3.0)
| Source | NH fraction | SH fraction |
|--------|-------------|-------------|
| FF | 0.85 | 0.15 |
| Mic | 0.65 | 0.35 |
| BB | 0.55 | 0.45 |

## Known Issues & Data Gaps

1. **OH KIE temperature**: Model uses lab temperature (296K) range. Tropospheric mean ~270K gives OH_KIE_D ≈ 1.315, significantly higher.
2. **Lifetime is simulated**: Linear parameterization approximates He et al. (2026). Actual year-by-year values needed.
3. **mic_dd_U = 7‰ hardcoded**: Should be derived from EMID database (Menoud 2022).
4. **δD 1999–2004 padded**: Repeating 2005 value. Real observations needed.
5. **3×3 ill-conditioning**: δD end-members too close for FF/BB separation. v3.2 and v4.0 address this.
6. **NH/SH δD gradient approximated**: Only ±1.5‰ offset from global, not observed.
7. **No Bayesian MCMC**: Direct matrix solve, not proper posterior sampling.
8. **No 5-year smoothing**: Ben (Riddell-Young 2025) applies smoothing; we don't.
9. **Strat and Soil KIEs fixed**: Literature suggests some uncertainty.
10. **No CH₄-OH feedback**: Perturbation lifetime not distinguished from total lifetime.

## Comparison to Previous Versions
- **v1.0 (original by Yufan Bao)**: Fixed KIEs, fixed lifetime, no quality monitoring, 4 copy-pasted scenario loops
- **v2.0**: Added KIE sampling, quality monitoring, time-varying τ
- **v3.0**: Added two-hemisphere structure, bounded solver
- **v3.2**: Switched to BB-fixed 2×2 approach (following Riddell-Young 2025)
- **v4.0**: Mic vs Non-Mic formulation using δD for microbial separation only

## Input Data Sources
- CH₄ concentrations: NOAA GML Annual Means
- δ¹³C: ch4c13_nh_sh_mean.xlsx (NH/SH specific)
- δD: GlobMean_dD_iterations_UmezawaCal_noBUDS.xlsx (global only)
- Source signatures: Pre-computed MC iterations from Riddell-Young 2025 pipeline
- CarbonTracker: CT-CH₄ posterior emissions for BB prior
- EDGAR: v8 fossil fuel emissions for FF signature weighting
