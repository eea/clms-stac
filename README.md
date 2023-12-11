# clms-stac
This repository contains example STAC collections and items of CLMS **Corine Land Cover** and **Vegetation Phenology and Productivity** products with **product schemas** for validation and maintanence.

```
.
├── stacs
│   ├── corine-land-cover
│   │   ├── clc2018_clc2018_v2018_20_raster100m
│   │   │   └── clc2018_clc2018_v2018_20_raster100m.json (STAC item)
│   │   └── corine-land-cover-raster.json (STAC collection)
│   ├── vegetation-phenology-and-productivity
│   │   ├── VPP_2022_S2_T40KCC-010m_V105_s2_TPROD
│   │   │   └── VPP_2022_S2_T40KCC-010m_V105_s2_TPROD.json (STAC item)
│   │   └── vegetation-phenology-and-productivity.json (STAC collection)
│   └── clms_catalog.json (STAC catalog)
└── schema
    ├── eea-extension
    │   └── schema.json (self-defined extension schema)
    └── products
        ├── clc.json (Corine Land Cover collection and items schema)
        ├── core.json (croe schema of CLMS products)
        └── vpp.json (Vegetation Phenology and Productivity collection and items schema)
```
