# Run-to-Run Delta Report

**Run A**: reports/hetzner-2026-07/bench-hetzner-2026-07-05-sweep2.json  
**Run B**: reports/hetzner-2026-07/bench-hetzner-2026-07-05-sweep3.json  
**Cell threshold**: ±5%  

| Framework | Query | Metric | A | B | Δ% | |
|-----------|-------|--------|--:|--:|---:|--|
| actix-web-rest | F1 | rps | 10798.8 | 11328.0 | +4.9 |  |
| actix-web-rest | F1 | p50_ms | 3.6 | 3.5 | -3.9 |  |
| actix-web-rest | F1 | p99_ms | 5.9 | 5.2 | -11.3 | ⚠ |
| actix-web-rest | F2 | rps | 4635.6 | 4913.4 | +6.0 | ⚠ |
| actix-web-rest | F2 | p50_ms | 8.3 | 8.0 | -3.4 |  |
| actix-web-rest | F2 | p99_ms | 13.7 | 11.4 | -16.8 | ⚠ |
| actix-web-rest | M1 | rps | 2475.6 | 2465.4 | -0.4 |  |
| actix-web-rest | M1 | p50_ms | 15.7 | 15.8 | +0.8 |  |
| actix-web-rest | M1 | p99_ms | 22.9 | 20.9 | -8.7 | ⚠ |
| actix-web-rest | Q1 | rps | 1647.0 | 1628.5 | -1.1 |  |
| actix-web-rest | Q1 | p50_ms | 23.8 | 23.9 | +0.3 |  |
| actix-web-rest | Q1 | p99_ms | 30.1 | 31.2 | +3.6 |  |
| actix-web-rest | Q2 | rps | 11352.0 | 11584.9 | +2.1 |  |
| actix-web-rest | Q2 | p50_ms | 3.4 | 3.4 | -0.3 |  |
| actix-web-rest | Q2 | p99_ms | 5.6 | 5.2 | -6.6 | ⚠ |
| actix-web-rest | Q2b | rps | 4734.3 | 4929.2 | +4.1 |  |
| actix-web-rest | Q2b | p50_ms | 8.0 | 7.8 | -2.5 |  |
| actix-web-rest | Q2b | p99_ms | 14.2 | 13.0 | -8.8 | ⚠ |
| actix-web-rest | T1 | rps | 48.9 | 47.3 | -3.3 |  |
| actix-web-rest | T1 | p50_ms | 823.9 | 859.1 | +4.3 |  |
| actix-web-rest | T1 | p99_ms | 971.4 | 989.9 | +1.9 |  |
| apollo-server | F1 | rps | 2929.1 | 2837.8 | -3.1 |  |
| apollo-server | F1 | p50_ms | 12.9 | 13.3 | +3.2 |  |
| apollo-server | F1 | p99_ms | 27.9 | 28.9 | +3.5 |  |
| apollo-server | F2 | rps | 1897.6 | 1868.3 | -1.5 |  |
| apollo-server | F2 | p50_ms | 19.3 | 19.5 | +0.8 |  |
| apollo-server | F2 | p99_ms | 43.3 | 45.0 | +3.9 |  |
| apollo-server | M1 | rps | 2453.7 | 2512.1 | +2.4 |  |
| apollo-server | M1 | p50_ms | 15.1 | 14.6 | -3.4 |  |
| apollo-server | M1 | p99_ms | 35.6 | 33.9 | -5.0 |  |
| apollo-server | Q1 | rps | 1578.7 | 1574.9 | -0.2 |  |
| apollo-server | Q1 | p50_ms | 24.9 | 24.7 | -0.8 |  |
| apollo-server | Q1 | p99_ms | 44.5 | 47.2 | +6.1 | ⚠ |
| apollo-server | Q2 | rps | 2982.1 | 2992.0 | +0.3 |  |
| apollo-server | Q2 | p50_ms | 12.7 | 12.6 | -0.8 |  |
| apollo-server | Q2 | p99_ms | 26.3 | 26.9 | +2.1 |  |
| apollo-server | Q2b | rps | 1891.3 | 1930.1 | +2.1 |  |
| apollo-server | Q2b | p50_ms | 19.6 | 19.2 | -1.9 |  |
| apollo-server | Q2b | p99_ms | 44.9 | 41.9 | -6.8 | ⚠ |
| apollo-server | T1 | rps | 1180.8 | 1185.7 | +0.4 |  |
| apollo-server | T1 | p50_ms | 31.0 | 31.0 | +0.1 |  |
| apollo-server | T1 | p99_ms | 60.6 | 58.6 | -3.3 |  |
| async-graphql | F1 | rps | 6712.6 | 6290.8 | -6.3 | ⚠ |
| async-graphql | F1 | p50_ms | 5.8 | 6.0 | +3.1 |  |
| async-graphql | F1 | p99_ms | 10.0 | 13.7 | +36.5 | ⚠ |
| async-graphql | F2 | rps | 5244.7 | 5339.3 | +1.8 |  |
| async-graphql | F2 | p50_ms | 7.2 | 7.0 | -2.2 |  |
| async-graphql | F2 | p99_ms | 15.9 | 15.8 | -0.8 |  |
| async-graphql | M1 | rps | 7878.5 | 8319.9 | +5.6 | ⚠ |
| async-graphql | M1 | p50_ms | 5.0 | 4.7 | -6.6 | ⚠ |
| async-graphql | M1 | p99_ms | 7.3 | 7.0 | -3.7 |  |
| async-graphql | MC1 | rps | 1249.5 | 1241.2 | -0.7 |  |
| async-graphql | MC1 | p50_ms | 23.5 | 23.4 | -0.5 |  |
| async-graphql | MC1 | p99_ms | 61.7 | 62.4 | +1.2 |  |
| async-graphql | Q1 | rps | 1409.2 | 1404.5 | -0.3 |  |
| async-graphql | Q1 | p50_ms | 17.3 | 17.2 | -0.2 |  |
| async-graphql | Q1 | p99_ms | 67.5 | 68.0 | +0.7 |  |
| async-graphql | Q2 | rps | 5431.4 | 6040.1 | +11.2 | ⚠ |
| async-graphql | Q2 | p50_ms | 6.8 | 6.1 | -10.9 | ⚠ |
| async-graphql | Q2 | p99_ms | 16.5 | 15.2 | -7.6 | ⚠ |
| async-graphql | Q2b | rps | 5198.1 | 5586.7 | +7.5 | ⚠ |
| async-graphql | Q2b | p50_ms | 7.2 | 6.6 | -8.9 | ⚠ |
| async-graphql | Q2b | p99_ms | 16.6 | 15.3 | -7.3 | ⚠ |
| async-graphql | Q3 | rps | 2140.6 | 2241.2 | +4.7 |  |
| async-graphql | Q3 | p50_ms | 17.7 | 16.9 | -4.1 |  |
| async-graphql | Q3 | p99_ms | 41.1 | 38.9 | -5.4 | ⚠ |
| async-graphql | T1 | rps | 5110.6 | 4856.5 | -5.0 |  |
| async-graphql | T1 | p50_ms | 7.6 | 8.0 | +5.8 | ⚠ |
| async-graphql | T1 | p99_ms | 14.0 | 14.8 | +5.5 | ⚠ |
| fraiseql-tv | C3 | rps | 10134.7 | 9856.7 | -2.7 |  |
| fraiseql-tv | C3 | p50_ms | 3.8 | 4.0 | +3.4 |  |
| fraiseql-tv | C3 | p99_ms | 6.1 | 6.1 | +0.7 |  |
| fraiseql-tv | F1 | rps | 9174.9 | 9021.7 | -1.7 |  |
| fraiseql-tv | F1 | p50_ms | 4.2 | 4.3 | +1.9 |  |
| fraiseql-tv | F1 | p99_ms | 6.7 | 6.8 | +1.6 |  |
| fraiseql-tv | F2 | rps | 7730.1 | 7350.3 | -4.9 |  |
| fraiseql-tv | F2 | p50_ms | 5.0 | 5.3 | +5.9 | ⚠ |
| fraiseql-tv | F2 | p99_ms | 7.9 | 8.2 | +3.3 |  |
| fraiseql-tv | F3 | rps | 8149.4 | 7779.4 | -4.5 |  |
| fraiseql-tv | F3 | p50_ms | 4.8 | 5.0 | +5.2 | ⚠ |
| fraiseql-tv | F3 | p99_ms | 7.5 | 7.8 | +3.7 |  |
| fraiseql-tv | HC3 | rps | 9905.2 | 9887.5 | -0.2 |  |
| fraiseql-tv | HC3 | p50_ms | 4.0 | 4.0 | +0.0 |  |
| fraiseql-tv | HC3 | p99_ms | 6.1 | 6.1 | +0.8 |  |
| fraiseql-tv | M1 | rps | 95.9 | 98.8 | +3.0 |  |
| fraiseql-tv | M1 | p50_ms | 206.5 | 203.4 | -1.5 |  |
| fraiseql-tv | M1 | p99_ms | 3652.0 | 2476.0 | -32.2 | ⚠ |
| fraiseql-tv | M1_APQ | rps | 102.8 | 105.4 | +2.5 |  |
| fraiseql-tv | M1_APQ | p50_ms | 202.8 | 193.3 | -4.7 |  |
| fraiseql-tv | M1_APQ | p99_ms | 2623.9 | 2127.1 | -18.9 | ⚠ |
| fraiseql-tv | M1d | rps | 8552.1 | 8641.9 | +1.1 |  |
| fraiseql-tv | M1d | p50_ms | 4.6 | 4.5 | -0.9 |  |
| fraiseql-tv | M1d | p99_ms | 7.4 | 7.2 | -2.0 |  |
| fraiseql-tv | MC1 | rps | 102.6 | 101.8 | -0.8 |  |
| fraiseql-tv | MC1 | p50_ms | 206.4 | 198.3 | -3.9 |  |
| fraiseql-tv | MC1 | p99_ms | 2584.0 | 2511.6 | -2.8 |  |
| fraiseql-tv | Q1 | rps | 8448.0 | 8182.3 | -3.1 |  |
| fraiseql-tv | Q1 | p50_ms | 4.6 | 4.7 | +3.1 |  |
| fraiseql-tv | Q1 | p99_ms | 7.3 | 7.6 | +3.8 |  |
| fraiseql-tv | Q1_APQ | rps | 7944.5 | 7947.4 | +0.0 |  |
| fraiseql-tv | Q1_APQ | p50_ms | 4.9 | 4.9 | +0.0 |  |
| fraiseql-tv | Q1_APQ | p99_ms | 7.6 | 7.6 | +0.1 |  |
| fraiseql-tv | Q2 | rps | 9565.2 | 9298.1 | -2.8 |  |
| fraiseql-tv | Q2 | p50_ms | 4.1 | 4.2 | +3.2 |  |
| fraiseql-tv | Q2 | p99_ms | 6.4 | 6.5 | +2.4 |  |
| fraiseql-tv | Q2b | rps | 8133.3 | 7905.6 | -2.8 |  |
| fraiseql-tv | Q2b | p50_ms | 4.8 | 4.9 | +2.9 |  |
| fraiseql-tv | Q2b | p99_ms | 7.5 | 7.8 | +3.3 |  |
| fraiseql-tv | Q2b_APQ | rps | 7959.2 | 7902.8 | -0.7 |  |
| fraiseql-tv | Q2b_APQ | p50_ms | 4.9 | 4.9 | +1.0 |  |
| fraiseql-tv | Q2b_APQ | p99_ms | 7.7 | 7.7 | +0.1 |  |
| fraiseql-tv | Q3 | rps | 4147.9 | 4080.4 | -1.6 |  |
| fraiseql-tv | Q3 | p50_ms | 8.1 | 8.4 | +3.5 |  |
| fraiseql-tv | Q3 | p99_ms | 34.3 | 33.8 | -1.5 |  |
| fraiseql-tv | T1 | rps | 4964.7 | 4857.2 | -2.2 |  |
| fraiseql-tv | T1 | p50_ms | 7.7 | 7.9 | +2.2 |  |
| fraiseql-tv | T1 | p99_ms | 13.5 | 13.7 | +1.6 |  |
| fraiseql-tv-audit | M1 | rps | 99.0 | 99.3 | +0.3 |  |
| fraiseql-tv-audit | M1 | p50_ms | 175.8 | 183.8 | +4.6 |  |
| fraiseql-tv-audit | M1 | p99_ms | 3197.8 | 3015.8 | -5.7 | ⚠ |
| fraiseql-tv-cache | C3 | rps | 10100.5 | 10078.2 | -0.2 |  |
| fraiseql-tv-cache | C3 | p50_ms | 3.9 | 3.9 | +0.3 |  |
| fraiseql-tv-cache | C3 | p99_ms | 6.0 | 6.0 | -0.5 |  |
| fraiseql-tv-cache | F1 | rps | 9081.0 | 9233.9 | +1.7 |  |
| fraiseql-tv-cache | F1 | p50_ms | 4.3 | 4.2 | -2.1 |  |
| fraiseql-tv-cache | F1 | p99_ms | 6.7 | 6.7 | -0.6 |  |
| fraiseql-tv-cache | F2 | rps | 7739.2 | 7512.6 | -2.9 |  |
| fraiseql-tv-cache | F2 | p50_ms | 5.0 | 5.2 | +4.2 |  |
| fraiseql-tv-cache | F2 | p99_ms | 7.9 | 8.0 | +1.4 |  |
| fraiseql-tv-cache | F3 | rps | 8311.1 | 8186.5 | -1.5 |  |
| fraiseql-tv-cache | F3 | p50_ms | 4.7 | 4.8 | +1.9 |  |
| fraiseql-tv-cache | F3 | p99_ms | 7.3 | 7.4 | +1.1 |  |
| fraiseql-tv-cache | HC3 | rps | 10040.5 | 9909.1 | -1.3 |  |
| fraiseql-tv-cache | HC3 | p50_ms | 3.9 | 4.0 | +1.8 |  |
| fraiseql-tv-cache | HC3 | p99_ms | 6.0 | 6.1 | +0.5 |  |
| fraiseql-tv-cache | M1 | rps | 101.1 | 107.9 | +6.7 | ⚠ |
| fraiseql-tv-cache | M1 | p50_ms | 208.3 | 218.8 | +5.0 | ⚠ |
| fraiseql-tv-cache | M1 | p99_ms | 2458.9 | 2054.2 | -16.5 | ⚠ |
| fraiseql-tv-cache | M1_APQ | rps | 103.4 | 102.9 | -0.5 |  |
| fraiseql-tv-cache | M1_APQ | p50_ms | 212.0 | 228.7 | +7.9 | ⚠ |
| fraiseql-tv-cache | M1_APQ | p99_ms | 2250.2 | 2022.8 | -10.1 | ⚠ |
| fraiseql-tv-cache | MC1 | rps | 103.4 | 102.3 | -1.1 |  |
| fraiseql-tv-cache | MC1 | p50_ms | 209.3 | 210.3 | +0.5 |  |
| fraiseql-tv-cache | MC1 | p99_ms | 2445.5 | 2482.5 | +1.5 |  |
| fraiseql-tv-cache | Q1 | rps | 8413.3 | 8414.9 | +0.0 |  |
| fraiseql-tv-cache | Q1 | p50_ms | 4.6 | 4.6 | +0.2 |  |
| fraiseql-tv-cache | Q1 | p99_ms | 7.3 | 7.3 | -0.3 |  |
| fraiseql-tv-cache | Q1_APQ | rps | 7963.6 | 7760.2 | -2.6 |  |
| fraiseql-tv-cache | Q1_APQ | p50_ms | 4.9 | 5.0 | +2.0 |  |
| fraiseql-tv-cache | Q1_APQ | p99_ms | 7.5 | 7.8 | +4.1 |  |
| fraiseql-tv-cache | Q2 | rps | 9567.0 | 9799.6 | +2.4 |  |
| fraiseql-tv-cache | Q2 | p50_ms | 4.1 | 4.0 | -2.7 |  |
| fraiseql-tv-cache | Q2 | p99_ms | 6.5 | 6.3 | -2.3 |  |
| fraiseql-tv-cache | Q2b | rps | 8138.6 | 8056.0 | -1.0 |  |
| fraiseql-tv-cache | Q2b | p50_ms | 4.8 | 4.9 | +1.7 |  |
| fraiseql-tv-cache | Q2b | p99_ms | 7.5 | 7.6 | +0.1 |  |
| fraiseql-tv-cache | Q2b_APQ | rps | 7789.5 | 7600.2 | -2.4 |  |
| fraiseql-tv-cache | Q2b_APQ | p50_ms | 5.0 | 5.2 | +2.4 |  |
| fraiseql-tv-cache | Q2b_APQ | p99_ms | 7.7 | 7.9 | +2.2 |  |
| fraiseql-tv-cache | Q3 | rps | 4157.9 | 4155.5 | -0.1 |  |
| fraiseql-tv-cache | Q3 | p50_ms | 8.2 | 8.2 | +0.9 |  |
| fraiseql-tv-cache | Q3 | p99_ms | 33.7 | 33.5 | -0.6 |  |
| fraiseql-tv-cache | T1 | rps | 4939.1 | 4860.9 | -1.6 |  |
| fraiseql-tv-cache | T1 | p50_ms | 7.8 | 7.9 | +1.5 |  |
| fraiseql-tv-cache | T1 | p99_ms | 13.5 | 13.8 | +1.9 |  |
| fraiseql-v-cache | C3 | rps | 9739.9 | 9534.5 | -2.1 |  |
| fraiseql-v-cache | C3 | p50_ms | 4.0 | 4.1 | +2.2 |  |
| fraiseql-v-cache | C3 | p99_ms | 6.2 | 6.3 | +1.5 |  |
| fraiseql-v-cache | F1 | rps | 5784.5 | 5745.2 | -0.7 |  |
| fraiseql-v-cache | F1 | p50_ms | 5.5 | 5.4 | -1.6 |  |
| fraiseql-v-cache | F1 | p99_ms | 33.8 | 34.2 | +1.2 |  |
| fraiseql-v-cache | F2 | rps | 4346.8 | 4294.0 | -1.2 |  |
| fraiseql-v-cache | F2 | p50_ms | 6.7 | 6.8 | +0.9 |  |
| fraiseql-v-cache | F2 | p99_ms | 40.3 | 40.8 | +1.2 |  |
| fraiseql-v-cache | F3 | rps | 7749.6 | 7736.8 | -0.2 |  |
| fraiseql-v-cache | F3 | p50_ms | 5.0 | 5.0 | +0.4 |  |
| fraiseql-v-cache | F3 | p99_ms | 8.0 | 8.1 | +1.0 |  |
| fraiseql-v-cache | HC3 | rps | 9681.7 | 9674.0 | -0.1 |  |
| fraiseql-v-cache | HC3 | p50_ms | 4.0 | 4.0 | -0.2 |  |
| fraiseql-v-cache | HC3 | p99_ms | 6.2 | 6.2 | +0.0 |  |
| fraiseql-v-cache | M1 | rps | 101.8 | 102.1 | +0.3 |  |
| fraiseql-v-cache | M1 | p50_ms | 179.4 | 199.5 | +11.2 | ⚠ |
| fraiseql-v-cache | M1 | p99_ms | 2483.9 | 2615.3 | +5.3 | ⚠ |
| fraiseql-v-cache | M1_APQ | rps | 101.9 | 99.8 | -2.1 |  |
| fraiseql-v-cache | M1_APQ | p50_ms | 189.2 | 187.3 | -1.0 |  |
| fraiseql-v-cache | M1_APQ | p99_ms | 2777.4 | 2732.0 | -1.6 |  |
| fraiseql-v-cache | MC1 | rps | 99.7 | 99.1 | -0.6 |  |
| fraiseql-v-cache | MC1 | p50_ms | 196.9 | 195.4 | -0.7 |  |
| fraiseql-v-cache | MC1 | p99_ms | 2982.8 | 3143.0 | +5.4 | ⚠ |
| fraiseql-v-cache | Q1 | rps | 7925.9 | 7945.5 | +0.2 |  |
| fraiseql-v-cache | Q1 | p50_ms | 4.9 | 4.9 | -0.2 |  |
| fraiseql-v-cache | Q1 | p99_ms | 8.1 | 8.0 | -0.9 |  |
| fraiseql-v-cache | Q1_APQ | rps | 7279.4 | 7370.1 | +1.2 |  |
| fraiseql-v-cache | Q1_APQ | p50_ms | 5.4 | 5.3 | -2.0 |  |
| fraiseql-v-cache | Q1_APQ | p99_ms | 8.3 | 8.4 | +1.2 |  |
| fraiseql-v-cache | Q2 | rps | 7056.8 | 7050.8 | -0.1 |  |
| fraiseql-v-cache | Q2 | p50_ms | 5.0 | 4.8 | -3.4 |  |
| fraiseql-v-cache | Q2 | p99_ms | 25.5 | 26.6 | +4.3 |  |
| fraiseql-v-cache | Q2b | rps | 5106.1 | 5069.2 | -0.7 |  |
| fraiseql-v-cache | Q2b | p50_ms | 6.2 | 6.3 | +2.8 |  |
| fraiseql-v-cache | Q2b | p99_ms | 34.7 | 33.8 | -2.7 |  |
| fraiseql-v-cache | Q2b_APQ | rps | 4914.1 | 4875.7 | -0.8 |  |
| fraiseql-v-cache | Q2b_APQ | p50_ms | 6.5 | 6.7 | +2.3 |  |
| fraiseql-v-cache | Q2b_APQ | p99_ms | 34.2 | 34.2 | +0.1 |  |
| fraiseql-v-cache | Q3 | rps | 1511.0 | 1512.4 | +0.1 |  |
| fraiseql-v-cache | Q3 | p50_ms | 16.9 | 16.9 | -0.4 |  |
| fraiseql-v-cache | Q3 | p99_ms | 80.0 | 80.6 | +0.7 |  |
| fraiseql-v-cache | T1 | rps | 2521.5 | 2498.4 | -0.9 |  |
| fraiseql-v-cache | T1 | p50_ms | 11.2 | 11.2 | +0.1 |  |
| fraiseql-v-cache | T1 | p99_ms | 51.1 | 51.9 | +1.6 |  |
| fraiseql-v-nocache | C3 | rps | 9750.6 | 9587.5 | -1.7 |  |
| fraiseql-v-nocache | C3 | p50_ms | 4.0 | 4.1 | +2.0 |  |
| fraiseql-v-nocache | C3 | p99_ms | 6.2 | 6.2 | +0.5 |  |
| fraiseql-v-nocache | F1 | rps | 5858.2 | 5819.1 | -0.7 |  |
| fraiseql-v-nocache | F1 | p50_ms | 5.3 | 5.4 | +2.7 |  |
| fraiseql-v-nocache | F1 | p99_ms | 33.8 | 32.9 | -2.6 |  |
| fraiseql-v-nocache | F2 | rps | 4319.8 | 4307.6 | -0.3 |  |
| fraiseql-v-nocache | F2 | p50_ms | 6.8 | 6.8 | +0.7 |  |
| fraiseql-v-nocache | F2 | p99_ms | 40.5 | 40.5 | -0.2 |  |
| fraiseql-v-nocache | F3 | rps | 7890.7 | 7677.3 | -2.7 |  |
| fraiseql-v-nocache | F3 | p50_ms | 4.9 | 5.1 | +3.0 |  |
| fraiseql-v-nocache | F3 | p99_ms | 7.9 | 8.1 | +1.9 |  |
| fraiseql-v-nocache | HC3 | rps | 9709.5 | 9634.5 | -0.8 |  |
| fraiseql-v-nocache | HC3 | p50_ms | 4.0 | 4.1 | +0.5 |  |
| fraiseql-v-nocache | HC3 | p99_ms | 6.2 | 6.2 | +1.5 |  |
| fraiseql-v-nocache | M1 | rps | 98.2 | 100.1 | +1.9 |  |
| fraiseql-v-nocache | M1 | p50_ms | 183.8 | 197.8 | +7.6 | ⚠ |
| fraiseql-v-nocache | M1 | p99_ms | 3989.9 | 2709.3 | -32.1 | ⚠ |
| fraiseql-v-nocache | M1_APQ | rps | 101.2 | 103.4 | +2.2 |  |
| fraiseql-v-nocache | M1_APQ | p50_ms | 195.0 | 200.2 | +2.6 |  |
| fraiseql-v-nocache | M1_APQ | p99_ms | 2961.7 | 2513.2 | -15.1 | ⚠ |
| fraiseql-v-nocache | MC1 | rps | 98.3 | 103.3 | +5.1 | ⚠ |
| fraiseql-v-nocache | MC1 | p50_ms | 183.2 | 195.0 | +6.4 | ⚠ |
| fraiseql-v-nocache | MC1 | p99_ms | 3618.6 | 2394.3 | -33.8 | ⚠ |
| fraiseql-v-nocache | Q1 | rps | 8044.5 | 8004.8 | -0.5 |  |
| fraiseql-v-nocache | Q1 | p50_ms | 4.8 | 4.8 | +0.2 |  |
| fraiseql-v-nocache | Q1 | p99_ms | 7.9 | 7.9 | +0.6 |  |
| fraiseql-v-nocache | Q1_APQ | rps | 7566.8 | 7238.3 | -4.3 |  |
| fraiseql-v-nocache | Q1_APQ | p50_ms | 5.2 | 5.4 | +4.4 |  |
| fraiseql-v-nocache | Q1_APQ | p99_ms | 8.1 | 8.5 | +5.2 | ⚠ |
| fraiseql-v-nocache | Q2 | rps | 7133.0 | 7057.6 | -1.1 |  |
| fraiseql-v-nocache | Q2 | p50_ms | 4.9 | 4.8 | -0.8 |  |
| fraiseql-v-nocache | Q2 | p99_ms | 24.9 | 25.4 | +2.0 |  |
| fraiseql-v-nocache | Q2b | rps | 5115.8 | 5061.2 | -1.1 |  |
| fraiseql-v-nocache | Q2b | p50_ms | 6.2 | 6.3 | +1.0 |  |
| fraiseql-v-nocache | Q2b | p99_ms | 34.1 | 34.2 | +0.3 |  |
| fraiseql-v-nocache | Q2b_APQ | rps | 4917.4 | 4849.1 | -1.4 |  |
| fraiseql-v-nocache | Q2b_APQ | p50_ms | 6.4 | 6.5 | +1.4 |  |
| fraiseql-v-nocache | Q2b_APQ | p99_ms | 35.1 | 35.5 | +1.1 |  |
| fraiseql-v-nocache | Q3 | rps | 1517.7 | 1510.7 | -0.5 |  |
| fraiseql-v-nocache | Q3 | p50_ms | 16.7 | 16.9 | +1.0 |  |
| fraiseql-v-nocache | Q3 | p99_ms | 79.8 | 79.8 | +0.0 |  |
| fraiseql-v-nocache | T1 | rps | 2528.9 | 2490.2 | -1.5 |  |
| fraiseql-v-nocache | T1 | p50_ms | 11.3 | 11.5 | +2.0 |  |
| fraiseql-v-nocache | T1 | p99_ms | 50.9 | 50.9 | +0.1 |  |
| hasura | F1 | rps | 1299.0 | 1332.5 | +2.6 |  |
| hasura | F1 | p50_ms | 30.2 | 29.4 | -2.6 |  |
| hasura | F1 | p99_ms | 45.9 | 46.0 | +0.2 |  |
| hasura | F2 | rps | 1102.4 | 1084.1 | -1.7 |  |
| hasura | F2 | p50_ms | 35.5 | 36.0 | +1.3 |  |
| hasura | F2 | p99_ms | 52.2 | 54.5 | +4.5 |  |
| hasura | M1 | rps | 1514.9 | 1553.2 | +2.5 |  |
| hasura | M1 | p50_ms | 22.4 | 22.3 | -0.4 |  |
| hasura | M1 | p99_ms | 64.6 | 58.9 | -8.8 | ⚠ |
| hasura | MC1 | rps | 476.1 | 486.0 | +2.1 |  |
| hasura | MC1 | p50_ms | 83.8 | 81.9 | -2.3 |  |
| hasura | MC1 | p99_ms | 104.4 | 99.8 | -4.5 |  |
| hasura | Q1 | rps | 1385.3 | 1491.4 | +7.7 | ⚠ |
| hasura | Q1 | p50_ms | 28.6 | 27.6 | -3.4 |  |
| hasura | Q1 | p99_ms | 44.1 | 44.8 | +1.6 |  |
| hasura | Q2 | rps | 1456.7 | 1600.4 | +9.9 | ⚠ |
| hasura | Q2 | p50_ms | 27.1 | 25.5 | -5.8 | ⚠ |
| hasura | Q2 | p99_ms | 42.9 | 40.7 | -5.1 | ⚠ |
| hasura | Q2b | rps | 1216.0 | 1233.1 | +1.4 |  |
| hasura | Q2b | p50_ms | 32.5 | 31.7 | -2.2 |  |
| hasura | Q2b | p99_ms | 49.4 | 49.6 | +0.4 |  |
| hasura | Q3 | rps | 985.8 | 1029.1 | +4.4 |  |
| hasura | Q3 | p50_ms | 39.9 | 38.8 | -2.8 |  |
| hasura | Q3 | p99_ms | 57.6 | 56.3 | -2.2 |  |
| hasura | T1 | rps | 794.7 | 897.3 | +12.9 | ⚠ |
| hasura | T1 | p50_ms | 50.8 | 43.0 | -15.3 | ⚠ |
| hasura | T1 | p99_ms | 72.1 | 66.9 | -7.3 | ⚠ |
| mercurius | F1 | rps | 4465.6 | 4250.6 | -4.8 |  |
| mercurius | F1 | p50_ms | 8.3 | 8.5 | +2.9 |  |
| mercurius | F1 | p99_ms | 18.9 | 21.2 | +12.2 | ⚠ |
| mercurius | F2 | rps | 3158.1 | 3372.5 | +6.8 | ⚠ |
| mercurius | F2 | p50_ms | 11.6 | 11.2 | -3.9 |  |
| mercurius | F2 | p99_ms | 25.7 | 22.5 | -12.4 | ⚠ |
| mercurius | M1 | rps | 3868.5 | 3954.1 | +2.2 |  |
| mercurius | M1 | p50_ms | 9.4 | 9.5 | +1.1 |  |
| mercurius | M1 | p99_ms | 24.8 | 21.0 | -15.4 | ⚠ |
| mercurius | MC1 | rps | 1321.7 | 1318.6 | -0.2 |  |
| mercurius | MC1 | p50_ms | 27.1 | 27.3 | +0.7 |  |
| mercurius | MC1 | p99_ms | 55.5 | 55.4 | -0.1 |  |
| mercurius | Q1 | rps | 1489.3 | 1473.5 | -1.1 |  |
| mercurius | Q1 | p50_ms | 17.7 | 17.8 | +0.9 |  |
| mercurius | Q1 | p99_ms | 74.1 | 74.6 | +0.7 |  |
| mercurius | Q2 | rps | 4051.2 | 4719.5 | +16.5 | ⚠ |
| mercurius | Q2 | p50_ms | 8.6 | 8.0 | -7.3 | ⚠ |
| mercurius | Q2 | p99_ms | 23.8 | 17.1 | -27.8 | ⚠ |
| mercurius | Q2b | rps | 2967.7 | 2926.8 | -1.4 |  |
| mercurius | Q2b | p50_ms | 12.3 | 12.4 | +1.5 |  |
| mercurius | Q2b | p99_ms | 28.1 | 28.7 | +1.9 |  |
| mercurius | T1 | rps | 1673.3 | 1642.7 | -1.8 |  |
| mercurius | T1 | p50_ms | 21.8 | 22.3 | +2.3 |  |
| mercurius | T1 | p99_ms | 44.0 | 44.2 | +0.5 |  |
| postgraphile | F1 | rps | 3140.2 | 3171.3 | +1.0 |  |
| postgraphile | F1 | p50_ms | 11.8 | 11.6 | -1.4 |  |
| postgraphile | F1 | p99_ms | 33.3 | 32.2 | -3.4 |  |
| postgraphile | F2 | rps | 2427.2 | 2340.3 | -3.6 |  |
| postgraphile | F2 | p50_ms | 15.0 | 15.5 | +3.3 |  |
| postgraphile | F2 | p99_ms | 40.6 | 42.8 | +5.5 | ⚠ |
| postgraphile | M1 | rps | 2901.2 | 2908.8 | +0.3 |  |
| postgraphile | M1 | p50_ms | 11.4 | 11.7 | +2.2 |  |
| postgraphile | M1 | p99_ms | 64.2 | 49.6 | -22.8 | ⚠ |
| postgraphile | MC1 | rps | 1285.5 | 1282.6 | -0.2 |  |
| postgraphile | MC1 | p50_ms | 26.2 | 26.3 | +0.4 |  |
| postgraphile | MC1 | p99_ms | 94.6 | 93.7 | -1.0 |  |
| postgraphile | Q1 | rps | 2871.4 | 2814.5 | -2.0 |  |
| postgraphile | Q1 | p50_ms | 12.8 | 13.2 | +2.6 |  |
| postgraphile | Q1 | p99_ms | 36.9 | 35.8 | -2.8 |  |
| postgraphile | Q2 | rps | 3343.2 | 3470.9 | +3.8 |  |
| postgraphile | Q2 | p50_ms | 10.9 | 10.7 | -2.7 |  |
| postgraphile | Q2 | p99_ms | 31.8 | 29.2 | -8.1 | ⚠ |
| postgraphile | Q2b | rps | 2616.5 | 2602.7 | -0.5 |  |
| postgraphile | Q2b | p50_ms | 14.1 | 14.3 | +1.2 |  |
| postgraphile | Q2b | p99_ms | 38.2 | 38.0 | -0.3 |  |
| postgraphile | Q3 | rps | 1486.9 | 1450.1 | -2.5 |  |
| postgraphile | Q3 | p50_ms | 23.8 | 24.7 | +3.5 |  |
| postgraphile | Q3 | p99_ms | 68.9 | 67.3 | -2.4 |  |
| postgraphile | T1 | rps | 2166.5 | 2121.7 | -2.1 |  |
| postgraphile | T1 | p50_ms | 16.5 | 16.9 | +2.2 |  |
| postgraphile | T1 | p99_ms | 62.3 | 66.3 | +6.4 | ⚠ |
| strawberry | F1 | rps | 1318.7 | 1309.1 | -0.7 |  |
| strawberry | F1 | p50_ms | 29.0 | 29.3 | +0.8 |  |
| strawberry | F1 | p99_ms | 60.2 | 60.2 | +0.1 |  |
| strawberry | F2 | rps | 971.0 | 962.6 | -0.9 |  |
| strawberry | F2 | p50_ms | 40.1 | 40.3 | +0.6 |  |
| strawberry | F2 | p99_ms | 70.8 | 75.9 | +7.3 | ⚠ |
| strawberry | M1 | rps | 1329.0 | 1322.0 | -0.5 |  |
| strawberry | M1 | p50_ms | 28.9 | 29.0 | +0.5 |  |
| strawberry | M1 | p99_ms | 61.4 | 60.6 | -1.3 |  |
| strawberry | Q1 | rps | 988.8 | 990.7 | +0.2 |  |
| strawberry | Q1 | p50_ms | 39.1 | 38.9 | -0.6 |  |
| strawberry | Q1 | p99_ms | 76.3 | 76.4 | +0.0 |  |
| strawberry | Q2 | rps | 1423.0 | 1423.6 | +0.0 |  |
| strawberry | Q2 | p50_ms | 27.0 | 26.8 | -0.7 |  |
| strawberry | Q2 | p99_ms | 56.6 | 59.1 | +4.5 |  |
| strawberry | Q2b | rps | 1034.0 | 1029.7 | -0.4 |  |
| strawberry | Q2b | p50_ms | 40.7 | 40.7 | +0.0 |  |
| strawberry | Q2b | p99_ms | 73.7 | 74.6 | +1.2 |  |
| strawberry | T1 | rps | 671.2 | 668.7 | -0.4 |  |
| strawberry | T1 | p50_ms | 65.8 | 57.5 | -12.6 | ⚠ |
| strawberry | T1 | p99_ms | 115.6 | 99.8 | -13.7 | ⚠ |

**Summary**: 63/354 cells flagged (17.8%) — gate limit 25% → **PASS**
