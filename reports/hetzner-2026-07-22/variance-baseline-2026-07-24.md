# Run-to-Run Delta Report

**Run A**: reports/hetzner-2026-07/bench-hetzner-2026-07-24-sweep3.json  
**Run B**: reports/hetzner-2026-07/bench-hetzner-2026-07-24-sweep4.json  
**Cell threshold**: ±5%  

| Framework | Query | Metric | A | B | Δ% | |
|-----------|-------|--------|--:|--:|---:|--|
| actix-web-rest | C3 | rps | 18619.4 | 18019.2 | -3.2 |  |
| actix-web-rest | C3 | p50_ms | 2.1 | 2.2 | +3.3 |  |
| actix-web-rest | C3 | p99_ms | 2.7 | 2.9 | +6.2 | ⚠ |
| actix-web-rest | F1 | rps | 13307.6 | 12920.5 | -2.9 |  |
| actix-web-rest | F1 | p50_ms | 2.9 | 3.1 | +4.1 |  |
| actix-web-rest | F1 | p99_ms | 3.8 | 3.9 | +0.3 |  |
| actix-web-rest | F2 | rps | 4776.1 | 4718.8 | -1.2 |  |
| actix-web-rest | F2 | p50_ms | 8.3 | 8.4 | +1.2 |  |
| actix-web-rest | F2 | p99_ms | 9.9 | 9.9 | +0.3 |  |
| actix-web-rest | F3 | rps | 1615.7 | 1609.7 | -0.4 |  |
| actix-web-rest | F3 | p50_ms | 24.3 | 24.4 | +0.2 |  |
| actix-web-rest | F3 | p99_ms | 30.1 | 31.1 | +3.1 |  |
| actix-web-rest | HC3 | rps | 18495.4 | 17922.0 | -3.1 |  |
| actix-web-rest | HC3 | p50_ms | 2.1 | 2.2 | +3.3 |  |
| actix-web-rest | HC3 | p99_ms | 2.9 | 2.9 | +2.8 |  |
| actix-web-rest | M1 | rps | 5291.2 | 4997.0 | -5.6 | ⚠ |
| actix-web-rest | M1 | p50_ms | 7.5 | 7.9 | +5.9 | ⚠ |
| actix-web-rest | M1 | p99_ms | 10.4 | 10.9 | +4.7 |  |
| actix-web-rest | MC1 | rps | 1353.4 | 1349.7 | -0.3 |  |
| actix-web-rest | MC1 | p50_ms | 28.9 | 28.9 | +0.0 |  |
| actix-web-rest | MC1 | p99_ms | 35.7 | 35.9 | +0.7 |  |
| actix-web-rest | Q1 | rps | 1675.0 | 1678.9 | +0.2 |  |
| actix-web-rest | Q1 | p50_ms | 23.4 | 23.4 | -0.2 |  |
| actix-web-rest | Q1 | p99_ms | 29.4 | 29.2 | -0.8 |  |
| actix-web-rest | Q2 | rps | 14068.6 | 13188.8 | -6.3 | ⚠ |
| actix-web-rest | Q2 | p50_ms | 2.8 | 3.0 | +6.0 | ⚠ |
| actix-web-rest | Q2 | p99_ms | 3.7 | 4.0 | +7.6 | ⚠ |
| actix-web-rest | Q2b | rps | 4944.0 | 4816.3 | -2.6 |  |
| actix-web-rest | Q2b | p50_ms | 8.1 | 8.3 | +2.7 |  |
| actix-web-rest | Q2b | p99_ms | 9.5 | 9.7 | +1.9 |  |
| actix-web-rest | Q3 | rps | 4300.9 | 4240.5 | -1.4 |  |
| actix-web-rest | Q3 | p50_ms | 9.2 | 9.4 | +1.7 |  |
| actix-web-rest | Q3 | p99_ms | 11.0 | 11.1 | +0.9 |  |
| actix-web-rest | T1 | rps | 3301.8 | 3287.6 | -0.4 |  |
| actix-web-rest | T1 | p50_ms | 12.0 | 12.1 | +0.5 |  |
| actix-web-rest | T1 | p99_ms | 14.1 | 14.2 | +0.7 |  |
| apollo-server | C3 | rps | 4111.6 | 4353.1 | +5.9 | ⚠ |
| apollo-server | C3 | p50_ms | 9.4 | 8.9 | -6.2 | ⚠ |
| apollo-server | C3 | p99_ms | 16.8 | 16.4 | -2.7 |  |
| apollo-server | F1 | rps | 3102.1 | 2993.4 | -3.5 |  |
| apollo-server | F1 | p50_ms | 12.6 | 13.0 | +3.8 |  |
| apollo-server | F1 | p99_ms | 21.7 | 22.2 | +2.5 |  |
| apollo-server | F2 | rps | 2236.9 | 2202.0 | -1.6 |  |
| apollo-server | F2 | p50_ms | 17.2 | 17.5 | +2.0 |  |
| apollo-server | F2 | p99_ms | 31.7 | 31.6 | -0.3 |  |
| apollo-server | F3 | rps | 1567.9 | 1567.9 | +0.0 |  |
| apollo-server | F3 | p50_ms | 24.6 | 24.6 | +0.2 |  |
| apollo-server | F3 | p99_ms | 50.1 | 49.7 | -0.8 |  |
| apollo-server | HC3 | rps | 4260.7 | 4263.8 | +0.1 |  |
| apollo-server | HC3 | p50_ms | 9.0 | 9.0 | +0.0 |  |
| apollo-server | HC3 | p99_ms | 16.5 | 16.5 | +0.2 |  |
| apollo-server | M1 | rps | 2749.7 | 2837.8 | +3.2 |  |
| apollo-server | M1 | p50_ms | 13.8 | 13.3 | -3.3 |  |
| apollo-server | M1 | p99_ms | 24.4 | 23.9 | -2.1 |  |
| apollo-server | M1_APQ | rps | 2749.8 | 2876.7 | +4.6 |  |
| apollo-server | M1_APQ | p50_ms | 13.8 | 13.1 | -4.9 |  |
| apollo-server | M1_APQ | p99_ms | 24.2 | 23.3 | -3.9 |  |
| apollo-server | MC1 | rps | 1072.5 | 1063.3 | -0.9 |  |
| apollo-server | MC1 | p50_ms | 36.9 | 37.3 | +1.3 |  |
| apollo-server | MC1 | p99_ms | 54.8 | 54.4 | -0.6 |  |
| apollo-server | Q1 | rps | 1566.3 | 1566.4 | +0.0 |  |
| apollo-server | Q1 | p50_ms | 24.5 | 24.6 | +0.4 |  |
| apollo-server | Q1 | p99_ms | 51.2 | 50.5 | -1.5 |  |
| apollo-server | Q1_APQ | rps | 1577.7 | 1575.8 | -0.1 |  |
| apollo-server | Q1_APQ | p50_ms | 24.5 | 24.7 | +0.9 |  |
| apollo-server | Q1_APQ | p99_ms | 50.2 | 49.0 | -2.3 |  |
| apollo-server | Q2 | rps | 3162.3 | 3128.7 | -1.1 |  |
| apollo-server | Q2 | p50_ms | 12.3 | 12.5 | +1.3 |  |
| apollo-server | Q2 | p99_ms | 21.3 | 21.3 | +0.1 |  |
| apollo-server | Q2b | rps | 2194.2 | 2212.5 | +0.8 |  |
| apollo-server | Q2b | p50_ms | 17.6 | 17.5 | -0.7 |  |
| apollo-server | Q2b | p99_ms | 31.8 | 31.5 | -0.9 |  |
| apollo-server | Q2b_APQ | rps | 2244.6 | 2183.4 | -2.7 |  |
| apollo-server | Q2b_APQ | p50_ms | 17.1 | 17.7 | +3.5 |  |
| apollo-server | Q2b_APQ | p99_ms | 31.7 | 31.8 | +0.5 |  |
| apollo-server | Q3 | rps | 783.9 | 776.4 | -1.0 |  |
| apollo-server | Q3 | p50_ms | 50.6 | 51.0 | +0.9 |  |
| apollo-server | Q3 | p99_ms | 69.1 | 70.3 | +1.7 |  |
| apollo-server | T1 | rps | 1460.8 | 1438.9 | -1.5 |  |
| apollo-server | T1 | p50_ms | 26.2 | 26.6 | +1.6 |  |
| apollo-server | T1 | p99_ms | 39.7 | 39.6 | -0.2 |  |
| fraiseql-tv | C3 | rps | 11696.7 | 11581.0 | -1.0 |  |
| fraiseql-tv | C3 | p50_ms | 3.4 | 3.4 | +1.2 |  |
| fraiseql-tv | C3 | p99_ms | 4.8 | 4.8 | -0.2 |  |
| fraiseql-tv | F1 | rps | 10574.7 | 10526.6 | -0.5 |  |
| fraiseql-tv | F1 | p50_ms | 3.8 | 3.8 | +0.3 |  |
| fraiseql-tv | F1 | p99_ms | 5.4 | 5.4 | +0.4 |  |
| fraiseql-tv | F2 | rps | 8852.0 | 8856.1 | +0.0 |  |
| fraiseql-tv | F2 | p50_ms | 4.5 | 4.5 | -0.2 |  |
| fraiseql-tv | F2 | p99_ms | 6.3 | 6.3 | -0.2 |  |
| fraiseql-tv | F3 | rps | 9467.7 | 9494.9 | +0.3 |  |
| fraiseql-tv | F3 | p50_ms | 4.2 | 4.2 | -0.5 |  |
| fraiseql-tv | F3 | p99_ms | 5.9 | 5.9 | -0.2 |  |
| fraiseql-tv | HC3 | rps | 11593.5 | 11639.7 | +0.4 |  |
| fraiseql-tv | HC3 | p50_ms | 3.4 | 3.4 | -0.3 |  |
| fraiseql-tv | HC3 | p99_ms | 4.8 | 4.8 | -0.8 |  |
| fraiseql-tv | M1 | rps | 1117.4 | 1116.2 | -0.1 |  |
| fraiseql-tv | M1 | p50_ms | 20.3 | 20.0 | -1.5 |  |
| fraiseql-tv | M1 | p99_ms | 187.2 | 197.0 | +5.2 | ⚠ |
| fraiseql-tv | M1_APQ | rps | 1100.2 | 1104.9 | +0.4 |  |
| fraiseql-tv | M1_APQ | p50_ms | 21.1 | 20.3 | -3.6 |  |
| fraiseql-tv | M1_APQ | p99_ms | 181.8 | 200.6 | +10.3 | ⚠ |
| fraiseql-tv | M1d | rps | 10016.3 | 10188.5 | +1.7 |  |
| fraiseql-tv | M1d | p50_ms | 4.0 | 3.9 | -1.8 |  |
| fraiseql-tv | M1d | p99_ms | 5.9 | 5.8 | -1.5 |  |
| fraiseql-tv | MC1 | rps | 1084.8 | 1111.3 | +2.4 |  |
| fraiseql-tv | MC1 | p50_ms | 21.0 | 20.8 | -1.2 |  |
| fraiseql-tv | MC1 | p99_ms | 196.0 | 186.9 | -4.6 |  |
| fraiseql-tv | Q1 | rps | 9759.6 | 9719.3 | -0.4 |  |
| fraiseql-tv | Q1 | p50_ms | 4.1 | 4.1 | +0.5 |  |
| fraiseql-tv | Q1 | p99_ms | 5.8 | 5.8 | +0.0 |  |
| fraiseql-tv | Q1_APQ | rps | 9393.2 | 9302.9 | -1.0 |  |
| fraiseql-tv | Q1_APQ | p50_ms | 4.2 | 4.3 | +0.9 |  |
| fraiseql-tv | Q1_APQ | p99_ms | 5.9 | 5.9 | +0.7 |  |
| fraiseql-tv | Q2 | rps | 11100.5 | 11110.3 | +0.1 |  |
| fraiseql-tv | Q2 | p50_ms | 3.6 | 3.6 | +0.0 |  |
| fraiseql-tv | Q2 | p99_ms | 5.2 | 5.2 | +0.2 |  |
| fraiseql-tv | Q2b | rps | 9233.0 | 9229.1 | -0.0 |  |
| fraiseql-tv | Q2b | p50_ms | 4.3 | 4.3 | +0.0 |  |
| fraiseql-tv | Q2b | p99_ms | 6.1 | 6.1 | +0.2 |  |
| fraiseql-tv | Q2b_APQ | rps | 9011.9 | 9169.5 | +1.7 |  |
| fraiseql-tv | Q2b_APQ | p50_ms | 4.4 | 4.3 | -1.8 |  |
| fraiseql-tv | Q2b_APQ | p99_ms | 6.1 | 6.0 | -1.5 |  |
| fraiseql-tv | Q3 | rps | 7257.7 | 7219.6 | -0.5 |  |
| fraiseql-tv | Q3 | p50_ms | 5.5 | 5.5 | +0.7 |  |
| fraiseql-tv | Q3 | p99_ms | 7.8 | 7.8 | +0.4 |  |
| fraiseql-tv | T1 | rps | 5800.9 | 5819.1 | +0.3 |  |
| fraiseql-tv | T1 | p50_ms | 6.8 | 6.8 | -0.1 |  |
| fraiseql-tv | T1 | p99_ms | 9.9 | 9.8 | -0.8 |  |
| fraiseql-tv-audit | M1 | rps | 1060.9 | 1070.4 | +0.9 |  |
| fraiseql-tv-audit | M1 | p50_ms | 21.6 | 21.5 | -0.6 |  |
| fraiseql-tv-audit | M1 | p99_ms | 194.8 | 196.2 | +0.7 |  |
| fraiseql-tv-cache | C3 | rps | 11724.8 | 11652.7 | -0.6 |  |
| fraiseql-tv-cache | C3 | p50_ms | 3.4 | 3.4 | +0.6 |  |
| fraiseql-tv-cache | C3 | p99_ms | 4.8 | 4.8 | +0.8 |  |
| fraiseql-tv-cache | F1 | rps | 10557.0 | 10874.6 | +3.0 |  |
| fraiseql-tv-cache | F1 | p50_ms | 3.8 | 3.6 | -2.9 |  |
| fraiseql-tv-cache | F1 | p99_ms | 5.4 | 5.2 | -3.7 |  |
| fraiseql-tv-cache | F2 | rps | 8830.9 | 9020.2 | +2.1 |  |
| fraiseql-tv-cache | F2 | p50_ms | 4.5 | 4.4 | -2.2 |  |
| fraiseql-tv-cache | F2 | p99_ms | 6.3 | 6.2 | -2.8 |  |
| fraiseql-tv-cache | F3 | rps | 9476.2 | 9483.3 | +0.1 |  |
| fraiseql-tv-cache | F3 | p50_ms | 4.2 | 4.2 | +0.7 |  |
| fraiseql-tv-cache | F3 | p99_ms | 5.9 | 5.9 | +0.7 |  |
| fraiseql-tv-cache | HC3 | rps | 11659.6 | 11655.0 | -0.0 |  |
| fraiseql-tv-cache | HC3 | p50_ms | 3.4 | 3.4 | +0.0 |  |
| fraiseql-tv-cache | HC3 | p99_ms | 4.8 | 4.8 | -0.8 |  |
| fraiseql-tv-cache | M1 | rps | 1076.6 | 1114.4 | +3.5 |  |
| fraiseql-tv-cache | M1 | p50_ms | 21.2 | 20.4 | -3.6 |  |
| fraiseql-tv-cache | M1 | p99_ms | 193.2 | 189.4 | -1.9 |  |
| fraiseql-tv-cache | M1_APQ | rps | 1099.8 | 1106.8 | +0.6 |  |
| fraiseql-tv-cache | M1_APQ | p50_ms | 20.6 | 20.3 | -1.5 |  |
| fraiseql-tv-cache | M1_APQ | p99_ms | 191.8 | 197.2 | +2.8 |  |
| fraiseql-tv-cache | M1d | rps | 10213.4 | 10213.5 | +0.0 |  |
| fraiseql-tv-cache | M1d | p50_ms | 3.9 | 3.9 | +0.3 |  |
| fraiseql-tv-cache | M1d | p99_ms | 5.8 | 5.8 | -0.7 |  |
| fraiseql-tv-cache | MC1 | rps | 1085.2 | 1097.2 | +1.1 |  |
| fraiseql-tv-cache | MC1 | p50_ms | 20.9 | 20.7 | -1.1 |  |
| fraiseql-tv-cache | MC1 | p99_ms | 198.6 | 198.7 | +0.0 |  |
| fraiseql-tv-cache | Q1 | rps | 9872.8 | 9806.7 | -0.7 |  |
| fraiseql-tv-cache | Q1 | p50_ms | 4.0 | 4.0 | +0.7 |  |
| fraiseql-tv-cache | Q1 | p99_ms | 5.7 | 5.8 | +0.9 |  |
| fraiseql-tv-cache | Q1_APQ | rps | 9205.8 | 9334.7 | +1.4 |  |
| fraiseql-tv-cache | Q1_APQ | p50_ms | 4.3 | 4.3 | -1.6 |  |
| fraiseql-tv-cache | Q1_APQ | p99_ms | 6.0 | 6.0 | -0.3 |  |
| fraiseql-tv-cache | Q2 | rps | 11262.5 | 11190.6 | -0.6 |  |
| fraiseql-tv-cache | Q2 | p50_ms | 3.5 | 3.5 | +0.3 |  |
| fraiseql-tv-cache | Q2 | p99_ms | 5.1 | 5.1 | +0.6 |  |
| fraiseql-tv-cache | Q2b | rps | 9295.7 | 9394.6 | +1.1 |  |
| fraiseql-tv-cache | Q2b | p50_ms | 4.3 | 4.2 | -1.2 |  |
| fraiseql-tv-cache | Q2b | p99_ms | 6.1 | 6.0 | -1.5 |  |
| fraiseql-tv-cache | Q2b_APQ | rps | 9028.4 | 9084.7 | +0.6 |  |
| fraiseql-tv-cache | Q2b_APQ | p50_ms | 4.4 | 4.4 | -0.7 |  |
| fraiseql-tv-cache | Q2b_APQ | p99_ms | 6.2 | 6.1 | -0.7 |  |
| fraiseql-tv-cache | Q3 | rps | 7366.2 | 7189.0 | -2.4 |  |
| fraiseql-tv-cache | Q3 | p50_ms | 5.4 | 5.5 | +1.5 |  |
| fraiseql-tv-cache | Q3 | p99_ms | 7.7 | 7.9 | +3.0 |  |
| fraiseql-tv-cache | T1 | rps | 5810.2 | 5779.1 | -0.5 |  |
| fraiseql-tv-cache | T1 | p50_ms | 6.8 | 6.8 | +0.4 |  |
| fraiseql-tv-cache | T1 | p99_ms | 9.9 | 9.9 | +0.6 |  |
| fraiseql-v-cache | C3 | rps | 11235.4 | 11228.5 | -0.1 |  |
| fraiseql-v-cache | C3 | p50_ms | 3.5 | 3.5 | +0.3 |  |
| fraiseql-v-cache | C3 | p99_ms | 4.9 | 5.0 | +0.8 |  |
| fraiseql-v-cache | F1 | rps | 6725.0 | 6773.1 | +0.7 |  |
| fraiseql-v-cache | F1 | p50_ms | 4.7 | 4.7 | +1.1 |  |
| fraiseql-v-cache | F1 | p99_ms | 30.0 | 29.3 | -2.2 |  |
| fraiseql-v-cache | F2 | rps | 5173.8 | 5186.0 | +0.2 |  |
| fraiseql-v-cache | F2 | p50_ms | 5.9 | 5.9 | -0.3 |  |
| fraiseql-v-cache | F2 | p99_ms | 34.5 | 34.3 | -0.5 |  |
| fraiseql-v-cache | F3 | rps | 8722.6 | 8624.0 | -1.1 |  |
| fraiseql-v-cache | F3 | p50_ms | 4.6 | 4.6 | +1.1 |  |
| fraiseql-v-cache | F3 | p99_ms | 6.5 | 6.6 | +0.8 |  |
| fraiseql-v-cache | HC3 | rps | 11301.9 | 11313.4 | +0.1 |  |
| fraiseql-v-cache | HC3 | p50_ms | 3.5 | 3.5 | +0.0 |  |
| fraiseql-v-cache | HC3 | p99_ms | 4.9 | 4.9 | +0.0 |  |
| fraiseql-v-cache | M1 | rps | 1111.4 | 1101.2 | -0.9 |  |
| fraiseql-v-cache | M1 | p50_ms | 20.8 | 20.5 | -1.2 |  |
| fraiseql-v-cache | M1 | p99_ms | 188.3 | 191.8 | +1.9 |  |
| fraiseql-v-cache | M1_APQ | rps | 1103.4 | 1090.5 | -1.2 |  |
| fraiseql-v-cache | M1_APQ | p50_ms | 20.4 | 21.1 | +3.4 |  |
| fraiseql-v-cache | M1_APQ | p99_ms | 194.5 | 190.6 | -2.0 |  |
| fraiseql-v-cache | MC1 | rps | 1090.3 | 1093.9 | +0.3 |  |
| fraiseql-v-cache | MC1 | p50_ms | 20.8 | 21.0 | +1.3 |  |
| fraiseql-v-cache | MC1 | p99_ms | 197.5 | 192.1 | -2.7 |  |
| fraiseql-v-cache | Q1 | rps | 8833.3 | 8943.4 | +1.2 |  |
| fraiseql-v-cache | Q1 | p50_ms | 4.5 | 4.4 | -1.3 |  |
| fraiseql-v-cache | Q1 | p99_ms | 6.6 | 6.7 | +1.4 |  |
| fraiseql-v-cache | Q1_APQ | rps | 8464.9 | 8430.2 | -0.4 |  |
| fraiseql-v-cache | Q1_APQ | p50_ms | 4.7 | 4.7 | +0.2 |  |
| fraiseql-v-cache | Q1_APQ | p99_ms | 6.7 | 6.7 | +0.1 |  |
| fraiseql-v-cache | Q2 | rps | 7410.2 | 7455.1 | +0.6 |  |
| fraiseql-v-cache | Q2 | p50_ms | 4.5 | 4.4 | -0.9 |  |
| fraiseql-v-cache | Q2 | p99_ms | 25.8 | 26.1 | +1.2 |  |
| fraiseql-v-cache | Q2b | rps | 5322.3 | 5375.3 | +1.0 |  |
| fraiseql-v-cache | Q2b | p50_ms | 5.8 | 5.8 | -1.0 |  |
| fraiseql-v-cache | Q2b | p99_ms | 33.5 | 33.5 | -0.0 |  |
| fraiseql-v-cache | Q2b_APQ | rps | 5116.5 | 5169.5 | +1.0 |  |
| fraiseql-v-cache | Q2b_APQ | p50_ms | 5.9 | 6.0 | +0.2 |  |
| fraiseql-v-cache | Q2b_APQ | p99_ms | 35.1 | 33.9 | -3.5 |  |
| fraiseql-v-cache | Q3 | rps | 3399.3 | 3434.4 | +1.0 |  |
| fraiseql-v-cache | Q3 | p50_ms | 8.6 | 8.5 | -0.6 |  |
| fraiseql-v-cache | Q3 | p99_ms | 43.1 | 42.5 | -1.3 |  |
| fraiseql-v-cache | T1 | rps | 3336.9 | 3370.6 | +1.0 |  |
| fraiseql-v-cache | T1 | p50_ms | 9.3 | 9.4 | +0.9 |  |
| fraiseql-v-cache | T1 | p99_ms | 38.7 | 36.9 | -4.9 |  |
| fraiseql-v-nocache | C3 | rps | 11293.4 | 11314.6 | +0.2 |  |
| fraiseql-v-nocache | C3 | p50_ms | 3.5 | 3.5 | +0.0 |  |
| fraiseql-v-nocache | C3 | p99_ms | 4.9 | 4.9 | +0.4 |  |
| fraiseql-v-nocache | F1 | rps | 6901.1 | 6932.1 | +0.4 |  |
| fraiseql-v-nocache | F1 | p50_ms | 4.7 | 4.7 | -1.5 |  |
| fraiseql-v-nocache | F1 | p99_ms | 27.9 | 28.9 | +3.5 |  |
| fraiseql-v-nocache | F2 | rps | 5183.5 | 5229.6 | +0.9 |  |
| fraiseql-v-nocache | F2 | p50_ms | 6.0 | 5.8 | -2.2 |  |
| fraiseql-v-nocache | F2 | p99_ms | 34.2 | 34.9 | +2.1 |  |
| fraiseql-v-nocache | F3 | rps | 8476.7 | 8833.7 | +4.2 |  |
| fraiseql-v-nocache | F3 | p50_ms | 4.7 | 4.5 | -3.8 |  |
| fraiseql-v-nocache | F3 | p99_ms | 6.7 | 6.5 | -3.9 |  |
| fraiseql-v-nocache | HC3 | rps | 11350.4 | 11338.2 | -0.1 |  |
| fraiseql-v-nocache | HC3 | p50_ms | 3.5 | 3.5 | +0.3 |  |
| fraiseql-v-nocache | HC3 | p99_ms | 4.9 | 4.9 | +0.0 |  |
| fraiseql-v-nocache | M1 | rps | 1123.3 | 1081.8 | -3.7 |  |
| fraiseql-v-nocache | M1 | p50_ms | 20.2 | 21.0 | +4.0 |  |
| fraiseql-v-nocache | M1 | p99_ms | 194.0 | 198.1 | +2.1 |  |
| fraiseql-v-nocache | M1_APQ | rps | 1097.8 | 1106.4 | +0.8 |  |
| fraiseql-v-nocache | M1_APQ | p50_ms | 20.2 | 20.8 | +2.9 |  |
| fraiseql-v-nocache | M1_APQ | p99_ms | 198.3 | 190.7 | -3.9 |  |
| fraiseql-v-nocache | MC1 | rps | 1106.1 | 1082.3 | -2.2 |  |
| fraiseql-v-nocache | MC1 | p50_ms | 20.5 | 20.9 | +2.0 |  |
| fraiseql-v-nocache | MC1 | p99_ms | 189.3 | 198.7 | +4.9 |  |
| fraiseql-v-nocache | Q1 | rps | 8866.1 | 8940.7 | +0.8 |  |
| fraiseql-v-nocache | Q1 | p50_ms | 4.4 | 4.4 | -0.7 |  |
| fraiseql-v-nocache | Q1 | p99_ms | 7.0 | 7.0 | -0.1 |  |
| fraiseql-v-nocache | Q1_APQ | rps | 8371.5 | 8522.6 | +1.8 |  |
| fraiseql-v-nocache | Q1_APQ | p50_ms | 4.8 | 4.7 | -1.9 |  |
| fraiseql-v-nocache | Q1_APQ | p99_ms | 6.8 | 6.7 | -1.3 |  |
| fraiseql-v-nocache | Q2 | rps | 7426.5 | 7491.7 | +0.9 |  |
| fraiseql-v-nocache | Q2 | p50_ms | 4.5 | 4.5 | -0.7 |  |
| fraiseql-v-nocache | Q2 | p99_ms | 25.8 | 25.1 | -2.8 |  |
| fraiseql-v-nocache | Q2b | rps | 5304.2 | 5392.5 | +1.7 |  |
| fraiseql-v-nocache | Q2b | p50_ms | 5.8 | 5.7 | -2.2 |  |
| fraiseql-v-nocache | Q2b | p99_ms | 33.6 | 33.2 | -1.1 |  |
| fraiseql-v-nocache | Q2b_APQ | rps | 5091.4 | 5231.8 | +2.8 |  |
| fraiseql-v-nocache | Q2b_APQ | p50_ms | 6.0 | 5.9 | -2.6 |  |
| fraiseql-v-nocache | Q2b_APQ | p99_ms | 34.6 | 34.3 | -1.0 |  |
| fraiseql-v-nocache | Q3 | rps | 3412.1 | 3447.9 | +1.0 |  |
| fraiseql-v-nocache | Q3 | p50_ms | 8.5 | 8.5 | -0.7 |  |
| fraiseql-v-nocache | Q3 | p99_ms | 43.1 | 42.3 | -1.8 |  |
| fraiseql-v-nocache | T1 | rps | 3346.2 | 3464.4 | +3.5 |  |
| fraiseql-v-nocache | T1 | p50_ms | 9.4 | 9.2 | -2.3 |  |
| fraiseql-v-nocache | T1 | p99_ms | 38.1 | 36.3 | -5.0 |  |
| hasura | C3 | rps | 3464.9 | 3473.4 | +0.2 |  |
| hasura | C3 | p50_ms | 11.1 | 11.1 | -0.4 |  |
| hasura | C3 | p99_ms | 20.4 | 19.9 | -2.3 |  |
| hasura | F1 | rps | 3461.7 | 3502.5 | +1.2 |  |
| hasura | F1 | p50_ms | 11.1 | 11.0 | -0.6 |  |
| hasura | F1 | p99_ms | 20.3 | 20.0 | -1.7 |  |
| hasura | F2 | rps | 2882.1 | 2908.3 | +0.9 |  |
| hasura | F2 | p50_ms | 13.3 | 13.1 | -1.0 |  |
| hasura | F2 | p99_ms | 22.6 | 23.0 | +1.8 |  |
| hasura | F3 | rps | 3609.1 | 3673.5 | +1.8 |  |
| hasura | F3 | p50_ms | 10.7 | 10.6 | -1.1 |  |
| hasura | F3 | p99_ms | 19.7 | 19.9 | +0.9 |  |
| hasura | HC3 | rps | 3484.8 | 3489.9 | +0.1 |  |
| hasura | HC3 | p50_ms | 11.0 | 11.0 | -0.5 |  |
| hasura | HC3 | p99_ms | 19.6 | 20.0 | +2.1 |  |
| hasura | M1 | rps | 1957.8 | 1980.9 | +1.2 |  |
| hasura | M1 | p50_ms | 19.3 | 19.1 | -0.9 |  |
| hasura | M1 | p99_ms | 31.6 | 30.7 | -2.8 |  |
| hasura | MC1 | rps | 1200.4 | 1215.6 | +1.3 |  |
| hasura | MC1 | p50_ms | 32.2 | 32.0 | -0.7 |  |
| hasura | MC1 | p99_ms | 48.1 | 44.2 | -8.2 | ⚠ |
| hasura | Q1 | rps | 3636.3 | 3638.2 | +0.1 |  |
| hasura | Q1 | p50_ms | 10.6 | 10.6 | +0.1 |  |
| hasura | Q1 | p99_ms | 19.5 | 19.2 | -1.5 |  |
| hasura | Q2 | rps | 3885.9 | 3924.2 | +1.0 |  |
| hasura | Q2 | p50_ms | 9.9 | 9.8 | -1.5 |  |
| hasura | Q2 | p99_ms | 18.9 | 18.2 | -3.9 |  |
| hasura | Q2b | rps | 3190.5 | 3227.1 | +1.1 |  |
| hasura | Q2b | p50_ms | 12.0 | 11.8 | -1.3 |  |
| hasura | Q2b | p99_ms | 21.1 | 20.9 | -1.0 |  |
| hasura | Q3 | rps | 2620.6 | 2614.0 | -0.3 |  |
| hasura | Q3 | p50_ms | 14.7 | 14.7 | +0.2 |  |
| hasura | Q3 | p99_ms | 23.9 | 23.8 | -0.2 |  |
| hasura | T1 | rps | 2160.8 | 2179.2 | +0.9 |  |
| hasura | T1 | p50_ms | 17.6 | 17.4 | -1.7 |  |
| hasura | T1 | p99_ms | 30.6 | 27.8 | -9.0 | ⚠ |
| mercurius | C3 | rps | 7314.4 | 7443.8 | +1.8 |  |
| mercurius | C3 | p50_ms | 5.2 | 5.1 | -1.5 |  |
| mercurius | C3 | p99_ms | 10.8 | 10.6 | -1.5 |  |
| mercurius | F1 | rps | 4759.3 | 4601.9 | -3.3 |  |
| mercurius | F1 | p50_ms | 8.1 | 8.4 | +3.7 |  |
| mercurius | F1 | p99_ms | 14.9 | 15.1 | +1.1 |  |
| mercurius | F2 | rps | 3391.7 | 3279.9 | -3.3 |  |
| mercurius | F2 | p50_ms | 11.3 | 11.7 | +3.3 |  |
| mercurius | F2 | p99_ms | 20.3 | 21.2 | +4.5 |  |
| mercurius | F3 | rps | 1461.0 | 1452.2 | -0.6 |  |
| mercurius | F3 | p50_ms | 17.8 | 18.4 | +3.3 |  |
| mercurius | F3 | p99_ms | 76.8 | 76.8 | +0.0 |  |
| mercurius | HC3 | rps | 7217.7 | 7464.6 | +3.4 |  |
| mercurius | HC3 | p50_ms | 5.3 | 5.1 | -3.0 |  |
| mercurius | HC3 | p99_ms | 10.8 | 10.6 | -1.9 |  |
| mercurius | M1 | rps | 4364.3 | 4466.0 | +2.3 |  |
| mercurius | M1 | p50_ms | 8.8 | 8.6 | -1.8 |  |
| mercurius | M1 | p99_ms | 16.6 | 16.3 | -1.7 |  |
| mercurius | M1_APQ | rps | 4328.3 | 4377.0 | +1.1 |  |
| mercurius | M1_APQ | p50_ms | 8.9 | 8.8 | -0.9 |  |
| mercurius | M1_APQ | p99_ms | 16.3 | 16.3 | -0.4 |  |
| mercurius | MC1 | rps | 1341.0 | 1348.2 | +0.5 |  |
| mercurius | MC1 | p50_ms | 27.3 | 26.8 | -2.0 |  |
| mercurius | MC1 | p99_ms | 53.9 | 53.9 | +0.0 |  |
| mercurius | Q1 | rps | 1449.9 | 1460.3 | +0.7 |  |
| mercurius | Q1 | p50_ms | 18.0 | 17.6 | -2.0 |  |
| mercurius | Q1 | p99_ms | 77.0 | 76.4 | -0.8 |  |
| mercurius | Q1_APQ | rps | 1457.8 | 1460.2 | +0.2 |  |
| mercurius | Q1_APQ | p50_ms | 18.2 | 18.0 | -1.1 |  |
| mercurius | Q1_APQ | p99_ms | 75.0 | 75.8 | +1.0 |  |
| mercurius | Q2 | rps | 4874.7 | 4870.3 | -0.1 |  |
| mercurius | Q2 | p50_ms | 7.9 | 7.9 | +0.1 |  |
| mercurius | Q2 | p99_ms | 14.8 | 14.8 | -0.5 |  |
| mercurius | Q2b | rps | 3486.5 | 3470.0 | -0.5 |  |
| mercurius | Q2b | p50_ms | 11.0 | 11.0 | +0.5 |  |
| mercurius | Q2b | p99_ms | 19.9 | 20.0 | +0.3 |  |
| mercurius | Q2b_APQ | rps | 3391.0 | 3424.0 | +1.0 |  |
| mercurius | Q2b_APQ | p50_ms | 11.3 | 11.2 | -1.1 |  |
| mercurius | Q2b_APQ | p99_ms | 20.5 | 20.3 | -0.9 |  |
| mercurius | Q3 | rps | 1032.6 | 1034.3 | +0.2 |  |
| mercurius | Q3 | p50_ms | 38.6 | 38.5 | -0.2 |  |
| mercurius | Q3 | p99_ms | 53.4 | 52.8 | -1.0 |  |
| mercurius | T1 | rps | 1972.4 | 2008.9 | +1.9 |  |
| mercurius | T1 | p50_ms | 19.4 | 19.0 | -1.9 |  |
| mercurius | T1 | p99_ms | 30.1 | 29.5 | -1.9 |  |
| postgraphile | C3 | rps | 4062.0 | 4401.4 | +8.4 | ⚠ |
| postgraphile | C3 | p50_ms | 9.5 | 8.8 | -7.7 | ⚠ |
| postgraphile | C3 | p99_ms | 18.3 | 17.1 | -6.7 | ⚠ |
| postgraphile | F1 | rps | 3780.6 | 3501.1 | -7.4 | ⚠ |
| postgraphile | F1 | p50_ms | 10.2 | 11.0 | +8.8 | ⚠ |
| postgraphile | F1 | p99_ms | 20.4 | 20.5 | +0.7 |  |
| postgraphile | F2 | rps | 2825.7 | 2862.9 | +1.3 |  |
| postgraphile | F2 | p50_ms | 13.6 | 13.4 | -1.6 |  |
| postgraphile | F2 | p99_ms | 25.9 | 25.9 | +0.1 |  |
| postgraphile | F3 | rps | 3373.6 | 3333.3 | -1.2 |  |
| postgraphile | F3 | p50_ms | 11.4 | 11.6 | +1.1 |  |
| postgraphile | F3 | p99_ms | 22.4 | 22.1 | -1.5 |  |
| postgraphile | HC3 | rps | 4214.6 | 4478.7 | +6.3 | ⚠ |
| postgraphile | HC3 | p50_ms | 9.1 | 8.6 | -5.7 | ⚠ |
| postgraphile | HC3 | p99_ms | 17.7 | 16.9 | -4.5 |  |
| postgraphile | M1 | rps | 3502.9 | 3455.5 | -1.4 |  |
| postgraphile | M1 | p50_ms | 10.6 | 10.6 | -0.1 |  |
| postgraphile | M1 | p99_ms | 21.6 | 22.3 | +3.3 |  |
| postgraphile | MC1 | rps | 1430.9 | 1543.4 | +7.9 | ⚠ |
| postgraphile | MC1 | p50_ms | 26.3 | 24.6 | -6.5 | ⚠ |
| postgraphile | MC1 | p99_ms | 49.8 | 45.6 | -8.4 | ⚠ |
| postgraphile | Q1 | rps | 3419.4 | 3261.6 | -4.6 |  |
| postgraphile | Q1 | p50_ms | 11.3 | 11.8 | +5.0 |  |
| postgraphile | Q1 | p99_ms | 21.6 | 22.2 | +3.1 |  |
| postgraphile | Q2 | rps | 3865.3 | 4029.4 | +4.2 |  |
| postgraphile | Q2 | p50_ms | 9.9 | 9.5 | -4.2 |  |
| postgraphile | Q2 | p99_ms | 19.4 | 18.9 | -2.8 |  |
| postgraphile | Q2b | rps | 2981.7 | 2967.0 | -0.5 |  |
| postgraphile | Q2b | p50_ms | 12.9 | 13.1 | +1.2 |  |
| postgraphile | Q2b | p99_ms | 24.1 | 23.4 | -2.9 |  |
| postgraphile | Q3 | rps | 1751.0 | 1896.4 | +8.3 | ⚠ |
| postgraphile | Q3 | p50_ms | 22.1 | 20.3 | -8.2 | ⚠ |
| postgraphile | Q3 | p99_ms | 39.2 | 36.4 | -7.1 | ⚠ |
| postgraphile | T1 | rps | 2459.0 | 2558.3 | +4.0 |  |
| postgraphile | T1 | p50_ms | 15.6 | 14.9 | -4.0 |  |
| postgraphile | T1 | p99_ms | 30.5 | 30.0 | -1.4 |  |
| strawberry | C3 | rps | 1575.4 | 1617.4 | +2.7 |  |
| strawberry | C3 | p50_ms | 23.6 | 23.7 | +0.4 |  |
| strawberry | C3 | p99_ms | 61.4 | 58.7 | -4.4 |  |
| strawberry | F1 | rps | 1269.9 | 1284.9 | +1.2 |  |
| strawberry | F1 | p50_ms | 30.1 | 29.9 | -0.8 |  |
| strawberry | F1 | p99_ms | 68.5 | 64.0 | -6.5 | ⚠ |
| strawberry | F2 | rps | 941.1 | 937.4 | -0.4 |  |
| strawberry | F2 | p50_ms | 40.6 | 40.9 | +0.6 |  |
| strawberry | F2 | p99_ms | 81.1 | 77.0 | -5.0 | ⚠ |
| strawberry | F3 | rps | 969.4 | 991.8 | +2.3 |  |
| strawberry | F3 | p50_ms | 17.4 | 38.9 | +123.8 | ⚠ |
| strawberry | F3 | p99_ms | 112.1 | 76.8 | -31.4 | ⚠ |
| strawberry | HC3 | rps | 1569.1 | 1639.0 | +4.5 |  |
| strawberry | HC3 | p50_ms | 10.2 | 22.9 | +123.6 | ⚠ |
| strawberry | HC3 | p99_ms | 78.6 | 54.4 | -30.8 | ⚠ |
| strawberry | M1 | rps | 1316.2 | 1319.7 | +0.3 |  |
| strawberry | M1 | p50_ms | 29.0 | 29.1 | +0.4 |  |
| strawberry | M1 | p99_ms | 70.3 | 63.9 | -9.2 | ⚠ |
| strawberry | MC1 | rps | 563.0 | 578.0 | +2.7 |  |
| strawberry | MC1 | p50_ms | 85.4 | 74.5 | -12.8 | ⚠ |
| strawberry | MC1 | p99_ms | 149.0 | 140.8 | -5.5 | ⚠ |
| strawberry | Q1 | rps | 990.2 | 1000.5 | +1.0 |  |
| strawberry | Q1 | p50_ms | 39.0 | 41.6 | +6.8 | ⚠ |
| strawberry | Q1 | p99_ms | 76.8 | 86.1 | +12.2 | ⚠ |
| strawberry | Q2 | rps | 1400.9 | 1400.8 | -0.0 |  |
| strawberry | Q2 | p50_ms | 27.5 | 27.6 | +0.4 |  |
| strawberry | Q2 | p99_ms | 61.8 | 58.3 | -5.6 | ⚠ |
| strawberry | Q2b | rps | 1009.4 | 1019.7 | +1.0 |  |
| strawberry | Q2b | p50_ms | 38.1 | 37.6 | -1.3 |  |
| strawberry | Q2b | p99_ms | 75.5 | 70.3 | -6.8 | ⚠ |
| strawberry | Q3 | rps | 529.9 | 543.3 | +2.5 |  |
| strawberry | Q3 | p50_ms | 81.5 | 70.9 | -13.0 | ⚠ |
| strawberry | Q3 | p99_ms | 141.4 | 116.1 | -17.9 | ⚠ |
| strawberry | T1 | rps | 667.6 | 676.5 | +1.3 |  |
| strawberry | T1 | p50_ms | 60.7 | 57.0 | -6.0 | ⚠ |
| strawberry | T1 | p99_ms | 112.9 | 97.6 | -13.6 | ⚠ |

**Summary**: 42/423 cells flagged (9.9%) — gate limit 25% → **PASS**
