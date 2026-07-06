export const RISK_COLORS = {
  Critical:  '#C0392B',
  Moderate:  '#E67E22',
  Good:      '#82B543',
  Excellent: '#1A7A3C',
};

export const RISK_BG = {
  Critical:  '#FDECEA',
  Moderate:  '#FEF5E7',
  Good:      '#EEF5E6',
  Excellent: '#E8F5EE',
};

export const RISK_ICONS = {
  Critical:  '🔴',
  Moderate:  '🟠',
  Good:      '🟡',
  Excellent: '🟢',
};

export const FOCUSED_STATES = ['Madhya Pradesh', 'Tripura', 'Odisha', 'Telangana'];

export const ALL_STATES = [
  'Madhya Pradesh','Tripura','Odisha','Telangana','Chhattisgarh',
  'Jharkhand','Maharashtra','Meghalaya','Arunachal Pradesh',
  'Uttarakhand','Assam','Nagaland','Gujarat','Rajasthan',
  'Himachal Pradesh','Kerala',
];

export const DISTRICT_COORDS = {
  'Kondagaon':[19.59,81.66],'West Garo Hills':[25.57,90.47],'Chamoli':[30.40,79.32],
  'Dhalai':[24.07,92.16],'Dahod':[22.83,74.25],'East Garo Hills':[25.62,90.90],
  'Rayagada':[19.17,83.42],'Chandrapur':[19.96,79.30],'Adilabad':[19.66,78.53],
  'Banswara':[23.55,74.44],'Dantewada':[18.90,81.35],'Lahaul and Spiti':[32.57,77.60],
  'Koraput':[18.81,82.71],'Idukki':[9.85,76.97],'Pithoragarh':[29.58,80.22],
  'Udaipur':[24.58,73.69],'Dindori':[22.94,81.07],'Jhabua':[22.77,74.59],
  'Kokrajhar':[26.39,90.27],'Simdega':[22.62,84.51],'Nandurbar':[21.37,74.24],
  'Gadchiroli':[20.10,80.00],'The Dangs':[20.75,73.70],'Mandla':[22.60,80.37],
  'Balaghat':[21.83,80.19],'Tuensang':[26.27,94.82],'Malkangiri':[18.33,81.89],
  'Kinnaur':[31.59,78.45],'Dima Hasao':[25.13,93.00],'Kandhamal':[20.09,84.23],
  'Sukma':[18.37,81.66],'Changlang':[27.13,95.78],'Gumla':[23.04,84.54],
  'Komaram Bheem':[19.47,79.60],'Mayurbhanj':[21.94,86.73],'Nabarangpur':[19.23,82.55],
  'Khunti':[23.07,85.28],'West Singhbhum':[22.70,85.83],'Latehar':[23.74,84.50],
  'Tirap':[27.03,95.53],'Longding':[27.40,95.14],'Mon':[26.73,95.00],
  'Karbi Anglong':[26.00,93.50],'Almora':[29.60,79.65],'Narmada':[21.87,73.77],
  'Alirajpur':[22.19,74.36],'Narayanpur':[19.73,81.23],'Kanker':[20.27,81.50],
  'Bastar':[19.10,81.95],'Lohardaga':[23.43,84.68],'Gondia':[21.45,80.20],
  'Sundargarh':[22.12,84.03],'Keonjhar':[21.62,85.58],'Mancherial':[18.87,79.45],
};

export const STATE_CENTERS = {
  'Madhya Pradesh':[23.5,78.5],'Odisha':[20.5,84.5],'Telangana':[18.0,79.5],
  'Tripura':[23.9,91.9],'Chhattisgarh':[21.0,81.5],'Jharkhand':[23.5,85.5],
  'Maharashtra':[19.7,76.5],'Meghalaya':[25.5,91.4],'Arunachal Pradesh':[27.0,93.6],
  'Nagaland':[26.2,94.5],'Assam':[26.2,92.9],'Uttarakhand':[30.0,79.3],
  'Gujarat':[22.3,72.6],'Rajasthan':[24.5,74.5],'Himachal Pradesh':[31.5,77.2],
  'Kerala':[10.5,76.5],
};

export const CSS_SCHEMES = [
  { id:'pmkisan', icon:'🌾', name:'PM-KISAN', ministry:'Agriculture', desc:'Direct income support ₹6,000/year to FRA patta holder families.', rights:['ifr','all'], tag:'Agriculture' },
  { id:'jjm', icon:'💧', name:'Jal Jeevan Mission', ministry:'Jal Shakti', desc:'Tap water connections to forest villages with FRA recognition.', rights:['all'], tag:'Water' },
  { id:'mgnrega', icon:'🔨', name:'MGNREGA', ministry:'Rural Development', desc:'100-day wage employment; forest protection converges with FRA CFR mandate.', rights:['all'], tag:'Employment' },
  { id:'pmayg', icon:'🏠', name:'PMAY-G', ministry:'Rural Development', desc:'Pucca house assistance — IFR patta satisfies land ownership requirement.', rights:['ifr','all'], tag:'Housing' },
  { id:'saubhagya', icon:'⚡', name:'SAUBHAGYA', ministry:'Power', desc:'Free electricity connections in unelectrified forest areas.', rights:['all'], tag:'Energy' },
  { id:'vanbandhu', icon:'🌿', name:'Van Bandhu Kalyan Yojana', ministry:'Tribal Affairs', desc:'Primary tribal welfare scheme for CFR-recognized communities.', rights:['cfr','all'], tag:'Tribal Welfare' },
  { id:'soilhealth', icon:'🧪', name:'Soil Health Card Scheme', ministry:'Agriculture', desc:'Soil testing for IFR forest fringe farmlands.', rights:['ifr','all'], tag:'Agriculture' },
  { id:'pmfby', icon:'🛡️', name:'PM Fasal Bima Yojana', ministry:'Agriculture', desc:'Crop insurance — FRA patta serves as proof of cultivated land.', rights:['ifr','all'], tag:'Insurance' },
  { id:'eklavya', icon:'📚', name:'Eklavya Model Schools', ministry:'Tribal Affairs', desc:'Residential schools for ST students in CFR/CR-recognized villages.', rights:['cfr','cr','all'], tag:'Education' },
];

// ─── Fire Forecast ──────────────────────────────────────────────
export const FIRE_RISK_COLORS = {
  High:   '#D7263D',
  Medium: '#F46036',
  Low:    '#2E933C',
};
export const FIRE_RISK_BG = {
  High:   '#FBE7EA',
  Medium: '#FDEDE6',
  Low:    '#E7F3E9',
};
// Model evaluation scores (from ROC / PR curves)
export const FIRE_MODELS = [
  { name: 'LSTM',         roc: 0.70, pr: 0.67, best: true },
  { name: 'RandomForest', roc: 0.69, pr: 0.65, best: false },
  { name: 'Ensemble',     roc: 0.68, pr: 0.65, best: false },
  { name: 'XGBoost',      roc: 0.67, pr: 0.64, best: false },
];
// Fire-driver importance (Random Forest)
export const FIRE_DRIVERS = [
  { feature: 'Land Surface Temp (LST)', importance: 0.239 },
  { feature: 'Day of Year',             importance: 0.214 },
  { feature: 'NDVI (vegetation)',       importance: 0.198 },
  { feature: 'Month',                   importance: 0.135 },
  { feature: 'Rainfall',                importance: 0.092 },
  { feature: 'Wind Speed',              importance: 0.069 },
  { feature: 'Forest Cover',            importance: 0.053 },
];

// ─── Crop Recommender ───────────────────────────────────────────
export const CROP_API_BASE = 'http://127.0.0.1:8000';

export const GROUNDWATER_COLORS = {
  'safe':           '#1D9E75',
  'semi-critical':  '#BA7517',
  'critical':       '#D85A30',
  'over-exploited': '#A32D2D',
};

// Demo districts (from the crop recommender's web prototype)
export const CROP_DISTRICTS = [
  { district:'Hisar (Haryana)',    lat:29.15, lng:75.72, rainfall_mm:450,  groundwater:'critical',       irrigation_pct:55, soil:'sandy loam', season:'rabi',   temperature_c:22 },
  { district:'Ludhiana (Punjab)',  lat:30.90, lng:75.85, rainfall_mm:700,  groundwater:'over-exploited', irrigation_pct:98, soil:'loam',       season:'kharif', temperature_c:31 },
  { district:'Barmer (Rajasthan)', lat:25.75, lng:71.40, rainfall_mm:270,  groundwater:'semi-critical',  irrigation_pct:20, soil:'sandy',      season:'kharif', temperature_c:33 },
  { district:'Bardhaman (W.B.)',   lat:23.25, lng:87.85, rainfall_mm:1400, groundwater:'safe',           irrigation_pct:70, soil:'clay loam',  season:'kharif', temperature_c:29 },
  { district:'Tumkur (Karnataka)', lat:13.34, lng:77.10, rainfall_mm:600,  groundwater:'critical',       irrigation_pct:35, soil:'loam',       season:'kharif', temperature_c:26 },
  { district:'Dindori (M.P.)',     lat:22.94, lng:81.07, rainfall_mm:1250, groundwater:'safe',           irrigation_pct:30, soil:'clay loam',  season:'kharif', temperature_c:27 },
  { district:'Adilabad (Telangana)',lat:19.66,lng:78.53, rainfall_mm:1000, groundwater:'semi-critical',  irrigation_pct:40, soil:'clay',       season:'kharif', temperature_c:29 },
];

export const SOIL_TYPES = ['sandy','sandy loam','loam','clay loam','clay'];
export const GROUNDWATER_LEVELS = ['safe','semi-critical','critical','over-exploited'];
export const SEASONS = ['rabi','kharif','zaid','annual'];
