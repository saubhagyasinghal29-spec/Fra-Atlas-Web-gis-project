// Crop knowledge base — mirrors backend data/crops.yaml
// Used as offline fallback when the FastAPI /recommend service is unreachable.
export const CROP_KB = [
  {
    "name": "Rice",
    "season": "kharif",
    "water_mm": [
      1200,
      1800
    ],
    "intensity": "high",
    "temp_c": [
      20,
      37
    ],
    "soils": [
      "clay",
      "clay loam"
    ]
  },
  {
    "name": "Wheat",
    "season": "rabi",
    "water_mm": [
      450,
      650
    ],
    "intensity": "medium",
    "temp_c": [
      10,
      25
    ],
    "soils": [
      "loam",
      "clay loam",
      "sandy loam"
    ]
  },
  {
    "name": "Maize",
    "season": "kharif",
    "water_mm": [
      500,
      800
    ],
    "intensity": "medium",
    "temp_c": [
      18,
      32
    ],
    "soils": [
      "loam",
      "sandy loam",
      "clay loam"
    ]
  },
  {
    "name": "Pearl millet (Bajra)",
    "season": "kharif",
    "water_mm": [
      350,
      500
    ],
    "intensity": "low",
    "temp_c": [
      25,
      35
    ],
    "soils": [
      "sandy",
      "sandy loam",
      "loam"
    ]
  },
  {
    "name": "Sorghum (Jowar)",
    "season": "kharif",
    "water_mm": [
      450,
      650
    ],
    "intensity": "low",
    "temp_c": [
      24,
      35
    ],
    "soils": [
      "loam",
      "sandy loam",
      "clay loam"
    ]
  },
  {
    "name": "Finger millet (Ragi)",
    "season": "kharif",
    "water_mm": [
      400,
      600
    ],
    "intensity": "low",
    "temp_c": [
      20,
      32
    ],
    "soils": [
      "loam",
      "sandy loam",
      "clay loam"
    ]
  },
  {
    "name": "Mustard",
    "season": "rabi",
    "water_mm": [
      250,
      400
    ],
    "intensity": "low",
    "temp_c": [
      10,
      25
    ],
    "soils": [
      "sandy loam",
      "loam",
      "sandy"
    ]
  },
  {
    "name": "Chickpea (Gram)",
    "season": "rabi",
    "water_mm": [
      300,
      400
    ],
    "intensity": "low",
    "temp_c": [
      15,
      28
    ],
    "soils": [
      "sandy loam",
      "loam"
    ]
  },
  {
    "name": "Barley",
    "season": "rabi",
    "water_mm": [
      350,
      500
    ],
    "intensity": "low",
    "temp_c": [
      12,
      25
    ],
    "soils": [
      "sandy loam",
      "loam"
    ]
  },
  {
    "name": "Lentil (Masoor)",
    "season": "rabi",
    "water_mm": [
      300,
      420
    ],
    "intensity": "low",
    "temp_c": [
      15,
      28
    ],
    "soils": [
      "loam",
      "clay loam"
    ]
  },
  {
    "name": "Cotton",
    "season": "kharif",
    "water_mm": [
      700,
      1300
    ],
    "intensity": "high",
    "temp_c": [
      21,
      35
    ],
    "soils": [
      "clay loam",
      "loam"
    ]
  },
  {
    "name": "Sugarcane",
    "season": "annual",
    "water_mm": [
      1500,
      2500
    ],
    "intensity": "high",
    "temp_c": [
      20,
      38
    ],
    "soils": [
      "loam",
      "clay loam"
    ]
  },
  {
    "name": "Groundnut",
    "season": "kharif",
    "water_mm": [
      500,
      700
    ],
    "intensity": "medium",
    "temp_c": [
      22,
      33
    ],
    "soils": [
      "sandy loam",
      "sandy",
      "loam"
    ]
  },
  {
    "name": "Soybean",
    "season": "kharif",
    "water_mm": [
      450,
      700
    ],
    "intensity": "medium",
    "temp_c": [
      20,
      32
    ],
    "soils": [
      "loam",
      "clay loam"
    ]
  },
  {
    "name": "Pigeon pea (Arhar)",
    "season": "kharif",
    "water_mm": [
      600,
      1000
    ],
    "intensity": "medium",
    "temp_c": [
      20,
      35
    ],
    "soils": [
      "loam",
      "sandy loam",
      "clay loam"
    ]
  },
  {
    "name": "Jute",
    "season": "kharif",
    "water_mm": [
      1200,
      1500
    ],
    "intensity": "high",
    "temp_c": [
      24,
      37
    ],
    "soils": [
      "loam",
      "clay loam"
    ]
  },
  {
    "name": "Potato",
    "season": "rabi",
    "water_mm": [
      500,
      700
    ],
    "intensity": "medium",
    "temp_c": [
      15,
      25
    ],
    "soils": [
      "sandy loam",
      "loam"
    ]
  },
  {
    "name": "Sunflower",
    "season": "rabi",
    "water_mm": [
      400,
      600
    ],
    "intensity": "medium",
    "temp_c": [
      18,
      30
    ],
    "soils": [
      "loam",
      "sandy loam"
    ]
  }
];
