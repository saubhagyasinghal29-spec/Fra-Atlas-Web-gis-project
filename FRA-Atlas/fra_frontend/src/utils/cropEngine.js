/**
 * Offline crop-recommendation engine.
 *
 * A faithful JavaScript port of the backend rule engine
 * (croprec/engine.py + water.py). Used ONLY as a fallback when the
 * FastAPI service at CROP_API_BASE is unreachable, so the page still works
 * offline. When the real API is up, its response is used verbatim and this
 * file is bypassed — the output shape is identical to POST /recommend.
 */
import { CROP_KB } from '../data/cropKnowledgeBase';

// --- water budget (mirrors water.py) ---------------------------------------
const EFFECTIVE_RAINFALL_FRACTION = 0.78;
const MAX_IRRIGATION_SUPPLEMENT_MM = 350.0;

function availableWater(rainfall_mm, irrigation_pct) {
  const effective_rain = rainfall_mm * EFFECTIVE_RAINFALL_FRACTION;
  const irrigation = (irrigation_pct / 100.0) * MAX_IRRIGATION_SUPPLEMENT_MM;
  return {
    total_mm: effective_rain + irrigation,
    effective_rain_mm: effective_rain,
    irrigation_mm: irrigation,
  };
}

// --- scoring config (mirrors engine.py) ------------------------------------
const GROUNDWATER_BASE_PENALTY = {
  'safe': 0.0,
  'semi-critical': 10.0,
  'critical': 25.0,
  'over-exploited': 40.0,
};
const INTENSITY_FACTOR = { low: 0.3, medium: 0.7, high: 1.0 };
const SOIL_GOOD_BONUS = 5.0;
const SOIL_POOR_PENALTY = -12.0;
const SEASON_MISMATCH_PENALTY = -50.0;
const TEMP_PENALTY_PER_DEGREE = 3.0;
const TEMP_PENALTY_CAP = 40.0;

const clamp = (v, lo = 0, hi = 100) => Math.max(lo, Math.min(hi, v));

function waterTarget(crop) {
  return (crop.water_mm[0] + crop.water_mm[1]) / 2;
}

function scoreCrop(cond, crop, avail) {
  const target = waterTarget(crop);
  const wm = target <= 0 ? 100 : clamp((avail.total_mm / target) * 100);
  const gw = GROUNDWATER_BASE_PENALTY[cond.groundwater] * INTENSITY_FACTOR[crop.intensity];
  const soilOk = crop.soils.includes(cond.soil);
  const soil = soilOk ? SOIL_GOOD_BONUS : SOIL_POOR_PENALTY;
  const seasonOk = crop.season === 'annual' || crop.season === cond.season;
  const season = seasonOk ? 0 : SEASON_MISMATCH_PENALTY;

  const [tmin, tmax] = crop.temp_c;
  const t = cond.temperature_c;
  let temp = 0;
  let tempOk = true;
  if (t < tmin || t > tmax) {
    tempOk = false;
    const degreesOutside = t < tmin ? tmin - t : t - tmax;
    temp = -Math.min(TEMP_PENALTY_CAP, TEMP_PENALTY_PER_DEGREE * degreesOutside);
  }

  const rule = clamp(wm - gw + soil + season + temp);

  // Build human-readable reasons (mirrors the backend's reasons array)
  const reasons = [
    {
      ok: wm >= 80,
      text: `Water need met (~${Math.round(target)} mm, ${Math.round(avail.total_mm)} mm available)`,
    },
  ];
  if (gw > 0) {
    reasons.push({
      ok: gw < 10,
      text: `Penalised -${Math.round(gw)}: ${crop.intensity}-water crop in ${cond.groundwater} block`,
    });
  } else {
    reasons.push({ ok: true, text: 'Groundwater is safe — no sustainability penalty' });
  }
  reasons.push({
    ok: soilOk,
    text: soilOk ? `Soil suits it (${cond.soil})` : `Soil not ideal (${cond.soil})`,
  });
  reasons.push({
    ok: seasonOk,
    text: seasonOk ? `Right season (${crop.season} crop)` : `Wrong season (${crop.season} crop)`,
  });
  reasons.push({
    ok: tempOk,
    text: tempOk
      ? `Temperature suits it (${tmin}-${tmax}C)`
      : `Temperature outside ideal band (${tmin}-${tmax}C)`,
  });

  return {
    crop: crop.name,
    final_score: Math.round(rule * 10) / 10,
    rule_score: Math.round(rule * 10) / 10,
    ml_score: null,
    season: crop.season,
    water_target_mm: target,
    reasons,
  };
}

/**
 * Local recommendation — same response shape as POST /recommend.
 * @param {object} cond { district, rainfall_mm, groundwater, irrigation_pct, soil, season, temperature_c }
 */
export function recommendLocal(cond) {
  const normalized = {
    ...cond,
    groundwater: cond.groundwater.trim().toLowerCase(),
    soil: cond.soil.trim().toLowerCase(),
    season: cond.season.trim().toLowerCase(),
  };
  const avail = availableWater(normalized.rainfall_mm, normalized.irrigation_pct);
  const recommendations = CROP_KB
    .map((crop) => scoreCrop(normalized, crop, avail))
    .sort((a, b) => b.final_score - a.final_score);

  return {
    district: cond.district,
    available_water_mm: Math.round(avail.total_mm * 10) / 10,
    effective_rain_mm: Math.round(avail.effective_rain_mm * 10) / 10,
    irrigation_mm: Math.round(avail.irrigation_mm * 10) / 10,
    used_ml: false,
    recommendations,
  };
}
