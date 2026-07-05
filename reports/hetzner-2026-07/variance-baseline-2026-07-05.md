# Run-to-Run Delta Report

**Run A**: reports/hetzner-2026-07/bench-hetzner-2026-07-04-sweep1.json  
**Run B**: reports/hetzner-2026-07/bench-hetzner-2026-07-05-sweep2.json  
**Cell threshold**: ±5%  

| Framework | Query | Metric | A | B | Δ% | |
|-----------|-------|--------|--:|--:|---:|--|
| actix-web-rest | F1 | rps | 10755.6 | 10798.8 | +0.4 |  |
| actix-web-rest | F1 | p50_ms | 3.6 | 3.6 | -1.4 |  |
| actix-web-rest | F1 | p99_ms | 5.8 | 5.9 | +1.5 |  |
| actix-web-rest | F2 | rps | 4808.5 | 4635.6 | -3.6 |  |
| actix-web-rest | F2 | p50_ms | 8.1 | 8.3 | +2.6 |  |
| actix-web-rest | F2 | p99_ms | 13.0 | 13.7 | +5.5 | ⚠ |
| actix-web-rest | M1 | rps | 2361.8 | 2475.6 | +4.8 |  |
| actix-web-rest | M1 | p50_ms | 16.3 | 15.7 | -3.6 |  |
| actix-web-rest | M1 | p99_ms | 31.6 | 22.9 | -27.7 | ⚠ |
| actix-web-rest | Q1 | rps | 1650.6 | 1647.0 | -0.2 |  |
| actix-web-rest | Q1 | p50_ms | 23.8 | 23.8 | +0.2 |  |
| actix-web-rest | Q1 | p99_ms | 30.0 | 30.1 | +0.5 |  |
| actix-web-rest | Q2 | rps | 11474.7 | 11352.0 | -1.1 |  |
| actix-web-rest | Q2 | p50_ms | 3.4 | 3.4 | -0.6 |  |
| actix-web-rest | Q2 | p99_ms | 5.3 | 5.6 | +6.5 | ⚠ |
| actix-web-rest | Q2b | rps | 4768.8 | 4734.3 | -0.7 |  |
| actix-web-rest | Q2b | p50_ms | 8.0 | 8.0 | -0.1 |  |
| actix-web-rest | Q2b | p99_ms | 13.7 | 14.2 | +4.3 |  |
| actix-web-rest | T1 | rps | 46.8 | 48.9 | +4.5 |  |
| actix-web-rest | T1 | p50_ms | 867.1 | 823.9 | -5.0 |  |
| actix-web-rest | T1 | p99_ms | 1035.5 | 971.4 | -6.2 | ⚠ |
| apollo-server | F1 | rps | 2871.8 | 2929.1 | +2.0 |  |
| apollo-server | F1 | p50_ms | 13.1 | 12.9 | -1.9 |  |
| apollo-server | F1 | p99_ms | 28.7 | 27.9 | -2.6 |  |
| apollo-server | F2 | rps | 1874.1 | 1897.6 | +1.3 |  |
| apollo-server | F2 | p50_ms | 19.6 | 19.3 | -1.3 |  |
| apollo-server | F2 | p99_ms | 44.3 | 43.3 | -2.2 |  |
| apollo-server | M1 | rps | 2520.4 | 2453.7 | -2.6 |  |
| apollo-server | M1 | p50_ms | 14.6 | 15.1 | +3.7 |  |
| apollo-server | M1 | p99_ms | 34.2 | 35.6 | +4.3 |  |
| apollo-server | Q1 | rps | 1581.3 | 1578.7 | -0.2 |  |
| apollo-server | Q1 | p50_ms | 24.6 | 24.9 | +1.3 |  |
| apollo-server | Q1 | p99_ms | 48.3 | 44.5 | -7.9 | ⚠ |
| apollo-server | Q2 | rps | 2907.3 | 2982.1 | +2.6 |  |
| apollo-server | Q2 | p50_ms | 13.0 | 12.7 | -2.4 |  |
| apollo-server | Q2 | p99_ms | 27.8 | 26.3 | -5.3 | ⚠ |
| apollo-server | Q2b | rps | 1955.6 | 1891.3 | -3.3 |  |
| apollo-server | Q2b | p50_ms | 19.0 | 19.6 | +2.7 |  |
| apollo-server | Q2b | p99_ms | 42.1 | 44.9 | +6.6 | ⚠ |
| apollo-server | T1 | rps | 1186.3 | 1180.8 | -0.5 |  |
| apollo-server | T1 | p50_ms | 30.8 | 31.0 | +0.7 |  |
| apollo-server | T1 | p99_ms | 59.9 | 60.6 | +1.1 |  |
| async-graphql | F1 | rps | 6589.1 | 6712.6 | +1.9 |  |
| async-graphql | F1 | p50_ms | 5.9 | 5.8 | -1.0 |  |
| async-graphql | F1 | p99_ms | 11.4 | 10.0 | -12.0 | ⚠ |
| async-graphql | F2 | rps | 5325.5 | 5244.7 | -1.5 |  |
| async-graphql | F2 | p50_ms | 6.9 | 7.2 | +3.2 |  |
| async-graphql | F2 | p99_ms | 16.3 | 15.9 | -2.0 |  |
| async-graphql | M1 | rps | 8534.3 | 7878.5 | -7.7 | ⚠ |
| async-graphql | M1 | p50_ms | 4.6 | 5.0 | +9.9 | ⚠ |
| async-graphql | M1 | p99_ms | 6.7 | 7.3 | +8.7 | ⚠ |
| async-graphql | MC1 | rps | 1259.5 | 1249.5 | -0.8 |  |
| async-graphql | MC1 | p50_ms | 23.1 | 23.5 | +1.8 |  |
| async-graphql | MC1 | p99_ms | 62.0 | 61.7 | -0.6 |  |
| async-graphql | Q1 | rps | 1412.8 | 1409.2 | -0.3 |  |
| async-graphql | Q1 | p50_ms | 17.1 | 17.3 | +0.8 |  |
| async-graphql | Q1 | p99_ms | 67.8 | 67.5 | -0.4 |  |
| async-graphql | Q2 | rps | 6212.2 | 5431.4 | -12.6 | ⚠ |
| async-graphql | Q2 | p50_ms | 6.1 | 6.8 | +11.3 | ⚠ |
| async-graphql | Q2 | p99_ms | 13.7 | 16.5 | +20.0 | ⚠ |
| async-graphql | Q2b | rps | 5543.9 | 5198.1 | -6.2 | ⚠ |
| async-graphql | Q2b | p50_ms | 6.6 | 7.2 | +9.2 | ⚠ |
| async-graphql | Q2b | p99_ms | 15.1 | 16.6 | +9.9 | ⚠ |
| async-graphql | Q3 | rps | 2251.3 | 2140.6 | -4.9 |  |
| async-graphql | Q3 | p50_ms | 16.6 | 17.7 | +6.6 | ⚠ |
| async-graphql | Q3 | p99_ms | 39.7 | 41.1 | +3.6 |  |
| async-graphql | T1 | rps | 4332.1 | 5110.6 | +18.0 | ⚠ |
| async-graphql | T1 | p50_ms | 8.9 | 7.6 | -15.5 | ⚠ |
| async-graphql | T1 | p99_ms | 16.8 | 14.0 | -16.7 | ⚠ |
| fraiseql-tv | C3 | rps | 9738.4 | 10134.7 | +4.1 |  |
| fraiseql-tv | C3 | p50_ms | 4.0 | 3.8 | -4.5 |  |
| fraiseql-tv | C3 | p99_ms | 6.2 | 6.1 | -1.9 |  |
| fraiseql-tv | F1 | rps | 8871.8 | 9174.9 | +3.4 |  |
| fraiseql-tv | F1 | p50_ms | 4.4 | 4.2 | -3.9 |  |
| fraiseql-tv | F1 | p99_ms | 6.9 | 6.7 | -2.3 |  |
| fraiseql-tv | F2 | rps | 7538.8 | 7730.1 | +2.5 |  |
| fraiseql-tv | F2 | p50_ms | 5.2 | 5.0 | -2.5 |  |
| fraiseql-tv | F2 | p99_ms | 8.1 | 7.9 | -2.2 |  |
| fraiseql-tv | F3 | rps | 8265.8 | 8149.4 | -1.4 |  |
| fraiseql-tv | F3 | p50_ms | 4.7 | 4.8 | +1.7 |  |
| fraiseql-tv | F3 | p99_ms | 7.4 | 7.5 | +1.1 |  |
| fraiseql-tv | HC3 | rps | 9848.1 | 9905.2 | +0.6 |  |
| fraiseql-tv | HC3 | p50_ms | 4.0 | 4.0 | -0.3 |  |
| fraiseql-tv | HC3 | p99_ms | 6.2 | 6.1 | -1.6 |  |
| fraiseql-tv | M1 | rps | 32.0 | 95.9 | +199.7 | ⚠ |
| fraiseql-tv | M1 | p50_ms | 41.3 | 206.5 | +399.8 | ⚠ |
| fraiseql-tv | M1 | p99_ms | 30002.0 | 3652.0 | -87.8 | ⚠ |
| fraiseql-tv | M1_APQ | rps | 31.6 | 102.8 | +225.3 | ⚠ |
| fraiseql-tv | M1_APQ | p50_ms | 48.2 | 202.8 | +320.8 | ⚠ |
| fraiseql-tv | M1_APQ | p99_ms | 30001.6 | 2623.9 | -91.3 | ⚠ |
| fraiseql-tv | M1d | rps | 43.5 | 8552.1 | +19560.0 | ⚠ |
| fraiseql-tv | M1d | p50_ms | 2.1 | 4.6 | +121.7 | ⚠ |
| fraiseql-tv | M1d | p99_ms | 13031.3 | 7.4 | -99.9 | ⚠ |
| fraiseql-tv | MC1 | rps | 32.1 | 102.6 | +219.6 | ⚠ |
| fraiseql-tv | MC1 | p50_ms | 49.1 | 206.4 | +320.2 | ⚠ |
| fraiseql-tv | MC1 | p99_ms | 29987.7 | 2584.0 | -91.4 | ⚠ |
| fraiseql-tv | Q1 | rps | 8541.6 | 8448.0 | -1.1 |  |
| fraiseql-tv | Q1 | p50_ms | 4.5 | 4.6 | +0.9 |  |
| fraiseql-tv | Q1 | p99_ms | 7.2 | 7.3 | +1.4 |  |
| fraiseql-tv | Q1_APQ | rps | 7687.7 | 7944.5 | +3.3 |  |
| fraiseql-tv | Q1_APQ | p50_ms | 5.1 | 4.9 | -3.1 |  |
| fraiseql-tv | Q1_APQ | p99_ms | 7.9 | 7.6 | -3.8 |  |
| fraiseql-tv | Q2 | rps | 9964.8 | 9565.2 | -4.0 |  |
| fraiseql-tv | Q2 | p50_ms | 3.9 | 4.1 | +4.9 |  |
| fraiseql-tv | Q2 | p99_ms | 6.2 | 6.4 | +3.4 |  |
| fraiseql-tv | Q2b | rps | 8359.7 | 8133.3 | -2.7 |  |
| fraiseql-tv | Q2b | p50_ms | 4.6 | 4.8 | +3.0 |  |
| fraiseql-tv | Q2b | p99_ms | 7.4 | 7.5 | +1.5 |  |
| fraiseql-tv | Q2b_APQ | rps | 7399.4 | 7959.2 | +7.6 | ⚠ |
| fraiseql-tv | Q2b_APQ | p50_ms | 5.3 | 4.9 | -7.8 | ⚠ |
| fraiseql-tv | Q2b_APQ | p99_ms | 8.2 | 7.7 | -6.8 | ⚠ |
| fraiseql-tv | Q3 | rps | 5860.7 | 4147.9 | -29.2 | ⚠ |
| fraiseql-tv | Q3 | p50_ms | 6.6 | 8.1 | +22.1 | ⚠ |
| fraiseql-tv | Q3 | p99_ms | 10.7 | 34.3 | +219.3 | ⚠ |
| fraiseql-tv | T1 | rps | 4857.5 | 4964.7 | +2.2 |  |
| fraiseql-tv | T1 | p50_ms | 7.9 | 7.7 | -2.0 |  |
| fraiseql-tv | T1 | p99_ms | 13.7 | 13.5 | -1.8 |  |
| fraiseql-tv-audit | M1 | rps | 101.5 | 99.0 | -2.5 |  |
| fraiseql-tv-audit | M1 | p50_ms | 196.6 | 175.8 | -10.6 | ⚠ |
| fraiseql-tv-audit | M1 | p99_ms | 2770.1 | 3197.8 | +15.4 | ⚠ |
| fraiseql-tv-cache | C3 | rps | 10042.2 | 10100.5 | +0.6 |  |
| fraiseql-tv-cache | C3 | p50_ms | 3.9 | 3.9 | -0.5 |  |
| fraiseql-tv-cache | C3 | p99_ms | 6.1 | 6.0 | -0.3 |  |
| fraiseql-tv-cache | F1 | rps | 8855.9 | 9081.0 | +2.5 |  |
| fraiseql-tv-cache | F1 | p50_ms | 4.4 | 4.3 | -2.5 |  |
| fraiseql-tv-cache | F1 | p99_ms | 6.9 | 6.7 | -1.9 |  |
| fraiseql-tv-cache | F2 | rps | 7625.1 | 7739.2 | +1.5 |  |
| fraiseql-tv-cache | F2 | p50_ms | 5.1 | 5.0 | -1.4 |  |
| fraiseql-tv-cache | F2 | p99_ms | 8.1 | 7.9 | -2.5 |  |
| fraiseql-tv-cache | F3 | rps | 7955.4 | 8311.1 | +4.5 |  |
| fraiseql-tv-cache | F3 | p50_ms | 4.9 | 4.7 | -5.1 | ⚠ |
| fraiseql-tv-cache | F3 | p99_ms | 7.5 | 7.3 | -3.1 |  |
| fraiseql-tv-cache | HC3 | rps | 10091.6 | 10040.5 | -0.5 |  |
| fraiseql-tv-cache | HC3 | p50_ms | 3.9 | 3.9 | +0.5 |  |
| fraiseql-tv-cache | HC3 | p99_ms | 6.1 | 6.0 | -0.2 |  |
| fraiseql-tv-cache | M1 | rps | 97.8 | 101.1 | +3.4 |  |
| fraiseql-tv-cache | M1 | p50_ms | 204.5 | 208.3 | +1.8 |  |
| fraiseql-tv-cache | M1 | p99_ms | 3241.3 | 2458.9 | -24.1 | ⚠ |
| fraiseql-tv-cache | M1_APQ | rps | 98.0 | 103.4 | +5.5 | ⚠ |
| fraiseql-tv-cache | M1_APQ | p50_ms | 201.0 | 212.0 | +5.5 | ⚠ |
| fraiseql-tv-cache | M1_APQ | p99_ms | 3358.2 | 2250.2 | -33.0 | ⚠ |
| fraiseql-tv-cache | MC1 | rps | 96.0 | 103.4 | +7.7 | ⚠ |
| fraiseql-tv-cache | MC1 | p50_ms | 204.6 | 209.3 | +2.3 |  |
| fraiseql-tv-cache | MC1 | p99_ms | 3938.1 | 2445.5 | -37.9 | ⚠ |
| fraiseql-tv-cache | Q1 | rps | 8242.0 | 8413.3 | +2.1 |  |
| fraiseql-tv-cache | Q1 | p50_ms | 4.7 | 4.6 | -2.5 |  |
| fraiseql-tv-cache | Q1 | p99_ms | 7.5 | 7.3 | -2.0 |  |
| fraiseql-tv-cache | Q1_APQ | rps | 7759.0 | 7963.6 | +2.6 |  |
| fraiseql-tv-cache | Q1_APQ | p50_ms | 5.1 | 4.9 | -2.8 |  |
| fraiseql-tv-cache | Q1_APQ | p99_ms | 7.7 | 7.5 | -2.5 |  |
| fraiseql-tv-cache | Q2 | rps | 9507.7 | 9567.0 | +0.6 |  |
| fraiseql-tv-cache | Q2 | p50_ms | 4.1 | 4.1 | -0.7 |  |
| fraiseql-tv-cache | Q2 | p99_ms | 6.4 | 6.5 | +0.5 |  |
| fraiseql-tv-cache | Q2b | rps | 7850.8 | 8138.6 | +3.7 |  |
| fraiseql-tv-cache | Q2b | p50_ms | 5.0 | 4.8 | -4.0 |  |
| fraiseql-tv-cache | Q2b | p99_ms | 7.8 | 7.5 | -3.6 |  |
| fraiseql-tv-cache | Q2b_APQ | rps | 7573.7 | 7789.5 | +2.8 |  |
| fraiseql-tv-cache | Q2b_APQ | p50_ms | 5.2 | 5.0 | -2.5 |  |
| fraiseql-tv-cache | Q2b_APQ | p99_ms | 8.0 | 7.7 | -3.1 |  |
| fraiseql-tv-cache | Q3 | rps | 4173.2 | 4157.9 | -0.4 |  |
| fraiseql-tv-cache | Q3 | p50_ms | 8.1 | 8.2 | +0.5 |  |
| fraiseql-tv-cache | Q3 | p99_ms | 34.3 | 33.7 | -1.6 |  |
| fraiseql-tv-cache | T1 | rps | 4799.4 | 4939.1 | +2.9 |  |
| fraiseql-tv-cache | T1 | p50_ms | 8.0 | 7.8 | -3.1 |  |
| fraiseql-tv-cache | T1 | p99_ms | 13.8 | 13.5 | -2.0 |  |
| fraiseql-v-cache | C3 | rps | 9533.2 | 9739.9 | +2.2 |  |
| fraiseql-v-cache | C3 | p50_ms | 4.1 | 4.0 | -2.0 |  |
| fraiseql-v-cache | C3 | p99_ms | 6.3 | 6.2 | -2.5 |  |
| fraiseql-v-cache | F1 | rps | 5759.3 | 5784.5 | +0.4 |  |
| fraiseql-v-cache | F1 | p50_ms | 5.4 | 5.5 | +0.7 |  |
| fraiseql-v-cache | F1 | p99_ms | 33.6 | 33.8 | +0.4 |  |
| fraiseql-v-cache | F2 | rps | 4295.6 | 4346.8 | +1.2 |  |
| fraiseql-v-cache | F2 | p50_ms | 6.9 | 6.7 | -2.6 |  |
| fraiseql-v-cache | F2 | p99_ms | 39.9 | 40.3 | +1.0 |  |
| fraiseql-v-cache | F3 | rps | 7663.2 | 7749.6 | +1.1 |  |
| fraiseql-v-cache | F3 | p50_ms | 5.1 | 5.0 | -1.4 |  |
| fraiseql-v-cache | F3 | p99_ms | 8.1 | 8.0 | -1.1 |  |
| fraiseql-v-cache | HC3 | rps | 9471.9 | 9681.7 | +2.2 |  |
| fraiseql-v-cache | HC3 | p50_ms | 4.1 | 4.0 | -2.2 |  |
| fraiseql-v-cache | HC3 | p99_ms | 6.3 | 6.2 | -1.7 |  |
| fraiseql-v-cache | M1 | rps | 95.9 | 101.8 | +6.2 | ⚠ |
| fraiseql-v-cache | M1 | p50_ms | 207.5 | 179.4 | -13.5 | ⚠ |
| fraiseql-v-cache | M1 | p99_ms | 3732.4 | 2483.9 | -33.4 | ⚠ |
| fraiseql-v-cache | M1_APQ | rps | 112.1 | 101.9 | -9.1 | ⚠ |
| fraiseql-v-cache | M1_APQ | p50_ms | 210.2 | 189.2 | -10.0 | ⚠ |
| fraiseql-v-cache | M1_APQ | p99_ms | 1902.9 | 2777.4 | +46.0 | ⚠ |
| fraiseql-v-cache | MC1 | rps | 102.0 | 99.7 | -2.3 |  |
| fraiseql-v-cache | MC1 | p50_ms | 213.4 | 196.9 | -7.8 | ⚠ |
| fraiseql-v-cache | MC1 | p99_ms | 2599.5 | 2982.8 | +14.7 | ⚠ |
| fraiseql-v-cache | Q1 | rps | 7886.2 | 7925.9 | +0.5 |  |
| fraiseql-v-cache | Q1 | p50_ms | 4.9 | 4.9 | -0.6 |  |
| fraiseql-v-cache | Q1 | p99_ms | 8.2 | 8.1 | -1.6 |  |
| fraiseql-v-cache | Q1_APQ | rps | 7297.5 | 7279.4 | -0.2 |  |
| fraiseql-v-cache | Q1_APQ | p50_ms | 5.3 | 5.4 | +0.7 |  |
| fraiseql-v-cache | Q1_APQ | p99_ms | 8.4 | 8.3 | -1.3 |  |
| fraiseql-v-cache | Q2 | rps | 6967.9 | 7056.8 | +1.3 |  |
| fraiseql-v-cache | Q2 | p50_ms | 4.9 | 5.0 | +1.4 |  |
| fraiseql-v-cache | Q2 | p99_ms | 25.7 | 25.5 | -0.6 |  |
| fraiseql-v-cache | Q2b | rps | 5002.4 | 5106.1 | +2.1 |  |
| fraiseql-v-cache | Q2b | p50_ms | 6.3 | 6.2 | -2.1 |  |
| fraiseql-v-cache | Q2b | p99_ms | 34.4 | 34.7 | +0.9 |  |
| fraiseql-v-cache | Q2b_APQ | rps | 4890.3 | 4914.1 | +0.5 |  |
| fraiseql-v-cache | Q2b_APQ | p50_ms | 6.5 | 6.5 | -0.5 |  |
| fraiseql-v-cache | Q2b_APQ | p99_ms | 34.7 | 34.2 | -1.5 |  |
| fraiseql-v-cache | Q3 | rps | 1471.6 | 1511.0 | +2.7 |  |
| fraiseql-v-cache | Q3 | p50_ms | 17.5 | 16.9 | -3.0 |  |
| fraiseql-v-cache | Q3 | p99_ms | 81.8 | 80.0 | -2.1 |  |
| fraiseql-v-cache | T1 | rps | 2523.9 | 2521.5 | -0.1 |  |
| fraiseql-v-cache | T1 | p50_ms | 11.2 | 11.2 | +0.1 |  |
| fraiseql-v-cache | T1 | p99_ms | 51.1 | 51.1 | -0.1 |  |
| fraiseql-v-nocache | C3 | rps | 9682.8 | 9750.6 | +0.7 |  |
| fraiseql-v-nocache | C3 | p50_ms | 4.0 | 4.0 | -1.0 |  |
| fraiseql-v-nocache | C3 | p99_ms | 6.2 | 6.2 | -0.5 |  |
| fraiseql-v-nocache | F1 | rps | 5773.8 | 5858.2 | +1.5 |  |
| fraiseql-v-nocache | F1 | p50_ms | 5.3 | 5.3 | -0.6 |  |
| fraiseql-v-nocache | F1 | p99_ms | 34.1 | 33.8 | -1.0 |  |
| fraiseql-v-nocache | F2 | rps | 4207.5 | 4319.8 | +2.7 |  |
| fraiseql-v-nocache | F2 | p50_ms | 7.0 | 6.8 | -3.8 |  |
| fraiseql-v-nocache | F2 | p99_ms | 41.0 | 40.5 | -1.0 |  |
| fraiseql-v-nocache | F3 | rps | 7478.9 | 7890.7 | +5.5 | ⚠ |
| fraiseql-v-nocache | F3 | p50_ms | 5.2 | 4.9 | -5.7 | ⚠ |
| fraiseql-v-nocache | F3 | p99_ms | 8.2 | 7.9 | -3.4 |  |
| fraiseql-v-nocache | HC3 | rps | 9730.7 | 9709.5 | -0.2 |  |
| fraiseql-v-nocache | HC3 | p50_ms | 4.0 | 4.0 | +0.5 |  |
| fraiseql-v-nocache | HC3 | p99_ms | 6.2 | 6.2 | -1.6 |  |
| fraiseql-v-nocache | M1 | rps | 97.4 | 98.2 | +0.8 |  |
| fraiseql-v-nocache | M1 | p50_ms | 200.1 | 183.8 | -8.2 | ⚠ |
| fraiseql-v-nocache | M1 | p99_ms | 2997.1 | 3989.9 | +33.1 | ⚠ |
| fraiseql-v-nocache | M1_APQ | rps | 99.2 | 101.2 | +2.0 |  |
| fraiseql-v-nocache | M1_APQ | p50_ms | 195.7 | 195.0 | -0.3 |  |
| fraiseql-v-nocache | M1_APQ | p99_ms | 3454.5 | 2961.7 | -14.3 | ⚠ |
| fraiseql-v-nocache | MC1 | rps | 96.6 | 98.3 | +1.8 |  |
| fraiseql-v-nocache | MC1 | p50_ms | 203.5 | 183.2 | -10.0 | ⚠ |
| fraiseql-v-nocache | MC1 | p99_ms | 3101.5 | 3618.6 | +16.7 | ⚠ |
| fraiseql-v-nocache | Q1 | rps | 7927.5 | 8044.5 | +1.5 |  |
| fraiseql-v-nocache | Q1 | p50_ms | 4.9 | 4.8 | -1.4 |  |
| fraiseql-v-nocache | Q1 | p99_ms | 8.0 | 7.9 | -1.5 |  |
| fraiseql-v-nocache | Q1_APQ | rps | 7005.4 | 7566.8 | +8.0 | ⚠ |
| fraiseql-v-nocache | Q1_APQ | p50_ms | 5.6 | 5.2 | -7.8 | ⚠ |
| fraiseql-v-nocache | Q1_APQ | p99_ms | 8.7 | 8.1 | -6.6 | ⚠ |
| fraiseql-v-nocache | Q2 | rps | 6990.3 | 7133.0 | +2.0 |  |
| fraiseql-v-nocache | Q2 | p50_ms | 4.9 | 4.9 | +0.0 |  |
| fraiseql-v-nocache | Q2 | p99_ms | 25.3 | 24.9 | -1.7 |  |
| fraiseql-v-nocache | Q2b | rps | 5022.5 | 5115.8 | +1.9 |  |
| fraiseql-v-nocache | Q2b | p50_ms | 6.3 | 6.2 | -2.2 |  |
| fraiseql-v-nocache | Q2b | p99_ms | 34.4 | 34.1 | -0.7 |  |
| fraiseql-v-nocache | Q2b_APQ | rps | 4595.8 | 4917.4 | +7.0 | ⚠ |
| fraiseql-v-nocache | Q2b_APQ | p50_ms | 6.8 | 6.4 | -5.3 | ⚠ |
| fraiseql-v-nocache | Q2b_APQ | p99_ms | 37.4 | 35.1 | -6.1 | ⚠ |
| fraiseql-v-nocache | Q3 | rps | 1499.7 | 1517.7 | +1.2 |  |
| fraiseql-v-nocache | Q3 | p50_ms | 16.8 | 16.7 | -0.7 |  |
| fraiseql-v-nocache | Q3 | p99_ms | 81.5 | 79.8 | -2.1 |  |
| fraiseql-v-nocache | T1 | rps | 2438.1 | 2528.9 | +3.7 |  |
| fraiseql-v-nocache | T1 | p50_ms | 12.0 | 11.3 | -6.4 | ⚠ |
| fraiseql-v-nocache | T1 | p99_ms | 51.3 | 50.9 | -0.8 |  |
| hasura | F1 | rps | 1324.9 | 1299.0 | -2.0 |  |
| hasura | F1 | p50_ms | 29.6 | 30.2 | +2.1 |  |
| hasura | F1 | p99_ms | 46.4 | 45.9 | -1.1 |  |
| hasura | F2 | rps | 1102.8 | 1102.4 | -0.0 |  |
| hasura | F2 | p50_ms | 35.4 | 35.5 | +0.3 |  |
| hasura | F2 | p99_ms | 53.8 | 52.2 | -3.1 |  |
| hasura | M1 | rps | 1493.9 | 1514.9 | +1.4 |  |
| hasura | M1 | p50_ms | 22.5 | 22.4 | -0.4 |  |
| hasura | M1 | p99_ms | 62.8 | 64.6 | +2.9 |  |
| hasura | MC1 | rps | 477.3 | 476.1 | -0.3 |  |
| hasura | MC1 | p50_ms | 83.5 | 83.8 | +0.4 |  |
| hasura | MC1 | p99_ms | 101.3 | 104.4 | +3.1 |  |
| hasura | Q1 | rps | 1623.7 | 1385.3 | -14.7 | ⚠ |
| hasura | Q1 | p50_ms | 26.8 | 28.6 | +6.7 | ⚠ |
| hasura | Q1 | p99_ms | 43.8 | 44.1 | +0.7 |  |
| hasura | Q2 | rps | 1490.6 | 1456.7 | -2.3 |  |
| hasura | Q2 | p50_ms | 26.3 | 27.1 | +3.1 |  |
| hasura | Q2 | p99_ms | 43.8 | 42.9 | -2.0 |  |
| hasura | Q2b | rps | 1234.0 | 1216.0 | -1.5 |  |
| hasura | Q2b | p50_ms | 31.8 | 32.5 | +2.1 |  |
| hasura | Q2b | p99_ms | 48.9 | 49.4 | +1.0 |  |
| hasura | Q3 | rps | 966.3 | 985.8 | +2.0 |  |
| hasura | Q3 | p50_ms | 40.6 | 39.9 | -1.6 |  |
| hasura | Q3 | p99_ms | 57.4 | 57.6 | +0.4 |  |
| hasura | T1 | rps | 814.0 | 794.7 | -2.4 |  |
| hasura | T1 | p50_ms | 48.5 | 50.8 | +4.7 |  |
| hasura | T1 | p99_ms | 71.0 | 72.1 | +1.5 |  |
| mercurius | F1 | rps | 4221.7 | 4465.6 | +5.8 | ⚠ |
| mercurius | F1 | p50_ms | 8.6 | 8.3 | -3.3 |  |
| mercurius | F1 | p99_ms | 21.2 | 18.9 | -10.9 | ⚠ |
| mercurius | F2 | rps | 2750.4 | 3158.1 | +14.8 | ⚠ |
| mercurius | F2 | p50_ms | 13.2 | 11.6 | -12.0 | ⚠ |
| mercurius | F2 | p99_ms | 30.5 | 25.7 | -15.8 | ⚠ |
| mercurius | M1 | rps | 3746.0 | 3868.5 | +3.3 |  |
| mercurius | M1 | p50_ms | 9.7 | 9.4 | -3.2 |  |
| mercurius | M1 | p99_ms | 24.4 | 24.8 | +1.6 |  |
| mercurius | MC1 | rps | 1351.7 | 1321.7 | -2.2 |  |
| mercurius | MC1 | p50_ms | 26.6 | 27.1 | +1.7 |  |
| mercurius | MC1 | p99_ms | 53.6 | 55.5 | +3.4 |  |
| mercurius | Q1 | rps | 1486.0 | 1489.3 | +0.2 |  |
| mercurius | Q1 | p50_ms | 17.9 | 17.7 | -1.1 |  |
| mercurius | Q1 | p99_ms | 74.7 | 74.1 | -0.8 |  |
| mercurius | Q2 | rps | 4643.3 | 4051.2 | -12.8 | ⚠ |
| mercurius | Q2 | p50_ms | 8.0 | 8.6 | +7.9 | ⚠ |
| mercurius | Q2 | p99_ms | 18.1 | 23.8 | +31.2 | ⚠ |
| mercurius | Q2b | rps | 2987.7 | 2967.7 | -0.7 |  |
| mercurius | Q2b | p50_ms | 12.1 | 12.3 | +1.0 |  |
| mercurius | Q2b | p99_ms | 28.2 | 28.1 | -0.1 |  |
| mercurius | T1 | rps | 1637.0 | 1673.3 | +2.2 |  |
| mercurius | T1 | p50_ms | 22.2 | 21.8 | -2.2 |  |
| mercurius | T1 | p99_ms | 44.8 | 44.0 | -1.8 |  |
| postgraphile | F1 | rps | 3038.3 | 3140.2 | +3.4 |  |
| postgraphile | F1 | p50_ms | 12.1 | 11.8 | -2.2 |  |
| postgraphile | F1 | p99_ms | 35.2 | 33.3 | -5.4 | ⚠ |
| postgraphile | F2 | rps | 2404.9 | 2427.2 | +0.9 |  |
| postgraphile | F2 | p50_ms | 15.2 | 15.0 | -1.4 |  |
| postgraphile | F2 | p99_ms | 42.5 | 40.6 | -4.4 |  |
| postgraphile | M1 | rps | 2929.4 | 2901.2 | -1.0 |  |
| postgraphile | M1 | p50_ms | 11.5 | 11.4 | -0.5 |  |
| postgraphile | M1 | p99_ms | 53.6 | 64.2 | +19.7 | ⚠ |
| postgraphile | MC1 | rps | 1269.1 | 1285.5 | +1.3 |  |
| postgraphile | MC1 | p50_ms | 26.5 | 26.2 | -1.2 |  |
| postgraphile | MC1 | p99_ms | 97.2 | 94.6 | -2.6 |  |
| postgraphile | Q1 | rps | 2926.2 | 2871.4 | -1.9 |  |
| postgraphile | Q1 | p50_ms | 12.6 | 12.8 | +1.7 |  |
| postgraphile | Q1 | p99_ms | 32.9 | 36.9 | +12.1 | ⚠ |
| postgraphile | Q2 | rps | 3168.7 | 3343.2 | +5.5 | ⚠ |
| postgraphile | Q2 | p50_ms | 11.5 | 10.9 | -4.5 |  |
| postgraphile | Q2 | p99_ms | 35.2 | 31.8 | -9.5 | ⚠ |
| postgraphile | Q2b | rps | 2537.1 | 2616.5 | +3.1 |  |
| postgraphile | Q2b | p50_ms | 14.6 | 14.1 | -3.6 |  |
| postgraphile | Q2b | p99_ms | 40.3 | 38.2 | -5.3 | ⚠ |
| postgraphile | Q3 | rps | 1468.6 | 1486.9 | +1.2 |  |
| postgraphile | Q3 | p50_ms | 24.2 | 23.8 | -1.4 |  |
| postgraphile | Q3 | p99_ms | 67.8 | 68.9 | +1.7 |  |
| postgraphile | T1 | rps | 2077.6 | 2166.5 | +4.3 |  |
| postgraphile | T1 | p50_ms | 17.4 | 16.5 | -5.3 | ⚠ |
| postgraphile | T1 | p99_ms | 59.3 | 62.3 | +5.2 | ⚠ |
| strawberry | F1 | rps | 1314.9 | 1318.7 | +0.3 |  |
| strawberry | F1 | p50_ms | 29.1 | 29.0 | -0.1 |  |
| strawberry | F1 | p99_ms | 60.8 | 60.2 | -1.1 |  |
| strawberry | F2 | rps | 961.8 | 971.0 | +1.0 |  |
| strawberry | F2 | p50_ms | 40.0 | 40.1 | +0.1 |  |
| strawberry | F2 | p99_ms | 74.0 | 70.8 | -4.3 |  |
| strawberry | M1 | rps | 1330.4 | 1329.0 | -0.1 |  |
| strawberry | M1 | p50_ms | 28.9 | 28.9 | -0.2 |  |
| strawberry | M1 | p99_ms | 59.1 | 61.4 | +4.0 |  |
| strawberry | Q1 | rps | 999.6 | 988.8 | -1.1 |  |
| strawberry | Q1 | p50_ms | 38.5 | 39.1 | +1.7 |  |
| strawberry | Q1 | p99_ms | 73.7 | 76.3 | +3.5 |  |
| strawberry | Q2 | rps | 1446.1 | 1423.0 | -1.6 |  |
| strawberry | Q2 | p50_ms | 28.5 | 27.0 | -5.2 | ⚠ |
| strawberry | Q2 | p99_ms | 61.8 | 56.6 | -8.5 | ⚠ |
| strawberry | Q2b | rps | 1029.6 | 1034.0 | +0.4 |  |
| strawberry | Q2b | p50_ms | 43.7 | 40.7 | -6.8 | ⚠ |
| strawberry | Q2b | p99_ms | 81.2 | 73.7 | -9.2 | ⚠ |
| strawberry | T1 | rps | 679.4 | 671.2 | -1.2 |  |
| strawberry | T1 | p50_ms | 64.0 | 65.8 | +2.8 |  |
| strawberry | T1 | p99_ms | 112.8 | 115.6 | +2.5 |  |

**Summary**: 92/354 cells flagged (26.0%) — gate limit 25% → **FAIL**
