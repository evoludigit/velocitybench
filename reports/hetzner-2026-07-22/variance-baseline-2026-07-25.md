# Run-to-Run Delta Report

**Run A**: reports/hetzner-2026-07/bench-hetzner-2026-07-25-sweep3.json  
**Run B**: reports/hetzner-2026-07/bench-hetzner-2026-07-25-sweep4.json  
**Cell threshold**: ±5%  

| Framework | Query | Metric | A | B | Δ% | |
|-----------|-------|--------|--:|--:|---:|--|
| actix-web-rest | C3 | rps | 16160.2 | 16150.6 | -0.1 |  |
| actix-web-rest | C3 | p50_ms | 2.4 | 2.4 | -0.8 |  |
| actix-web-rest | C3 | p99_ms | 3.4 | 3.8 | +13.6 | ⚠ |
| actix-web-rest | F1 | rps | 12048.9 | 11995.0 | -0.4 |  |
| actix-web-rest | F1 | p50_ms | 3.2 | 3.2 | -0.6 |  |
| actix-web-rest | F1 | p99_ms | 5.7 | 6.1 | +7.8 | ⚠ |
| actix-web-rest | F2 | rps | 6775.0 | 6543.3 | -3.4 |  |
| actix-web-rest | F2 | p50_ms | 5.8 | 6.0 | +2.9 |  |
| actix-web-rest | F2 | p99_ms | 7.8 | 8.0 | +2.7 |  |
| actix-web-rest | F3 | rps | 1612.6 | 1626.0 | +0.8 |  |
| actix-web-rest | F3 | p50_ms | 24.1 | 24.0 | -0.4 |  |
| actix-web-rest | F3 | p99_ms | 31.3 | 30.9 | -1.1 |  |
| actix-web-rest | HC3 | rps | 16289.0 | 16112.2 | -1.1 |  |
| actix-web-rest | HC3 | p50_ms | 2.4 | 2.4 | +0.0 |  |
| actix-web-rest | HC3 | p99_ms | 3.4 | 3.7 | +9.7 | ⚠ |
| actix-web-rest | M1 | rps | 3548.3 | 2820.8 | -20.5 | ⚠ |
| actix-web-rest | M1 | p50_ms | 11.0 | 14.3 | +30.4 | ⚠ |
| actix-web-rest | M1 | p99_ms | 15.8 | 18.1 | +14.7 | ⚠ |
| actix-web-rest | MC1 | rps | 1284.4 | 1277.6 | -0.5 |  |
| actix-web-rest | MC1 | p50_ms | 29.8 | 30.2 | +1.4 |  |
| actix-web-rest | MC1 | p99_ms | 40.9 | 39.3 | -4.0 |  |
| actix-web-rest | Q1 | rps | 1662.5 | 1655.6 | -0.4 |  |
| actix-web-rest | Q1 | p50_ms | 23.3 | 23.6 | +1.5 |  |
| actix-web-rest | Q1 | p99_ms | 31.5 | 30.3 | -3.8 |  |
| actix-web-rest | Q2 | rps | 12717.5 | 12219.1 | -3.9 |  |
| actix-web-rest | Q2 | p50_ms | 3.1 | 3.1 | +1.9 |  |
| actix-web-rest | Q2 | p99_ms | 4.3 | 5.8 | +36.4 | ⚠ |
| actix-web-rest | Q2b | rps | 4977.7 | 5123.0 | +2.9 |  |
| actix-web-rest | Q2b | p50_ms | 7.8 | 7.7 | -0.9 |  |
| actix-web-rest | Q2b | p99_ms | 13.3 | 11.5 | -13.6 | ⚠ |
| actix-web-rest | Q3 | rps | 4217.5 | 4299.3 | +1.9 |  |
| actix-web-rest | Q3 | p50_ms | 9.4 | 9.2 | -1.7 |  |
| actix-web-rest | Q3 | p99_ms | 12.8 | 11.0 | -13.8 | ⚠ |
| actix-web-rest | T1 | rps | 3153.4 | 3167.1 | +0.4 |  |
| actix-web-rest | T1 | p50_ms | 12.7 | 12.6 | -0.5 |  |
| actix-web-rest | T1 | p99_ms | 18.0 | 16.2 | -9.6 | ⚠ |
| apollo-server | C3 | rps | 3904.0 | 3730.0 | -4.5 |  |
| apollo-server | C3 | p50_ms | 9.8 | 10.1 | +3.2 |  |
| apollo-server | C3 | p99_ms | 19.4 | 21.4 | +10.7 | ⚠ |
| apollo-server | F1 | rps | 2897.9 | 2912.8 | +0.5 |  |
| apollo-server | F1 | p50_ms | 13.3 | 13.0 | -2.1 |  |
| apollo-server | F1 | p99_ms | 25.2 | 27.8 | +10.4 | ⚠ |
| apollo-server | F2 | rps | 1902.0 | 1905.6 | +0.2 |  |
| apollo-server | F2 | p50_ms | 19.6 | 19.5 | -0.8 |  |
| apollo-server | F2 | p99_ms | 40.8 | 42.0 | +2.9 |  |
| apollo-server | F3 | rps | 1558.5 | 1572.7 | +0.9 |  |
| apollo-server | F3 | p50_ms | 24.8 | 24.4 | -1.6 |  |
| apollo-server | F3 | p99_ms | 50.0 | 50.5 | +1.1 |  |
| apollo-server | HC3 | rps | 3959.7 | 3851.9 | -2.7 |  |
| apollo-server | HC3 | p50_ms | 9.6 | 9.6 | +0.1 |  |
| apollo-server | HC3 | p99_ms | 18.8 | 21.8 | +15.6 | ⚠ |
| apollo-server | M1 | rps | 2541.1 | 2543.5 | +0.1 |  |
| apollo-server | M1 | p50_ms | 14.8 | 14.6 | -1.2 |  |
| apollo-server | M1 | p99_ms | 32.3 | 33.4 | +3.3 |  |
| apollo-server | M1_APQ | rps | 2588.9 | 2666.6 | +3.0 |  |
| apollo-server | M1_APQ | p50_ms | 14.7 | 14.1 | -3.5 |  |
| apollo-server | M1_APQ | p99_ms | 31.5 | 31.3 | -0.6 |  |
| apollo-server | MC1 | rps | 1060.5 | 1047.0 | -1.3 |  |
| apollo-server | MC1 | p50_ms | 37.2 | 37.8 | +1.5 |  |
| apollo-server | MC1 | p99_ms | 55.4 | 55.2 | -0.4 |  |
| apollo-server | Q1 | rps | 1552.2 | 1570.6 | +1.2 |  |
| apollo-server | Q1 | p50_ms | 24.8 | 24.6 | -0.8 |  |
| apollo-server | Q1 | p99_ms | 50.5 | 49.7 | -1.7 |  |
| apollo-server | Q1_APQ | rps | 1557.0 | 1577.6 | +1.3 |  |
| apollo-server | Q1_APQ | p50_ms | 24.8 | 24.8 | -0.2 |  |
| apollo-server | Q1_APQ | p99_ms | 50.2 | 48.4 | -3.7 |  |
| apollo-server | Q2 | rps | 2896.1 | 3015.5 | +4.1 |  |
| apollo-server | Q2 | p50_ms | 13.1 | 12.7 | -2.5 |  |
| apollo-server | Q2 | p99_ms | 28.0 | 25.2 | -9.9 | ⚠ |
| apollo-server | Q2b | rps | 1867.4 | 1934.1 | +3.6 |  |
| apollo-server | Q2b | p50_ms | 19.9 | 19.5 | -2.3 |  |
| apollo-server | Q2b | p99_ms | 42.4 | 39.5 | -7.0 | ⚠ |
| apollo-server | Q2b_APQ | rps | 1976.2 | 1987.6 | +0.6 |  |
| apollo-server | Q2b_APQ | p50_ms | 19.0 | 18.8 | -0.9 |  |
| apollo-server | Q2b_APQ | p99_ms | 38.2 | 41.1 | +7.7 | ⚠ |
| apollo-server | Q3 | rps | 643.0 | 654.9 | +1.9 |  |
| apollo-server | Q3 | p50_ms | 61.0 | 60.1 | -1.5 |  |
| apollo-server | Q3 | p99_ms | 95.0 | 95.4 | +0.4 |  |
| apollo-server | T1 | rps | 1203.8 | 1196.5 | -0.6 |  |
| apollo-server | T1 | p50_ms | 30.4 | 30.9 | +1.7 |  |
| apollo-server | T1 | p99_ms | 58.6 | 57.4 | -2.1 |  |
| async-graphql | C3 | rps | 16088.8 | 15638.8 | -2.8 |  |
| async-graphql | C3 | p50_ms | 2.4 | 2.5 | +4.9 |  |
| async-graphql | C3 | p99_ms | 3.9 | 4.1 | +6.7 | ⚠ |
| async-graphql | F1 | rps | 9523.6 | 9368.7 | -1.6 |  |
| async-graphql | F1 | p50_ms | 4.2 | 4.3 | +2.7 |  |
| async-graphql | F1 | p99_ms | 5.8 | 7.1 | +22.3 | ⚠ |
| async-graphql | F2 | rps | 6061.2 | 6175.9 | +1.9 |  |
| async-graphql | F2 | p50_ms | 6.2 | 6.2 | -0.3 |  |
| async-graphql | F2 | p99_ms | 14.4 | 13.1 | -8.7 | ⚠ |
| async-graphql | F3 | rps | 1400.6 | 1400.1 | -0.0 |  |
| async-graphql | F3 | p50_ms | 17.5 | 17.6 | +0.2 |  |
| async-graphql | F3 | p99_ms | 67.2 | 67.1 | -0.1 |  |
| async-graphql | HC3 | rps | 16065.6 | 15818.3 | -1.5 |  |
| async-graphql | HC3 | p50_ms | 2.4 | 2.5 | +3.3 |  |
| async-graphql | HC3 | p99_ms | 3.8 | 4.0 | +5.3 | ⚠ |
| async-graphql | M1 | rps | 9537.8 | 9293.2 | -2.6 |  |
| async-graphql | M1 | p50_ms | 4.1 | 4.3 | +3.9 |  |
| async-graphql | M1 | p99_ms | 5.5 | 5.8 | +5.4 | ⚠ |
| async-graphql | M1_APQ | rps | 10477.9 | 9974.3 | -4.8 |  |
| async-graphql | M1_APQ | p50_ms | 3.8 | 4.0 | +5.8 | ⚠ |
| async-graphql | M1_APQ | p99_ms | 5.1 | 5.5 | +7.8 | ⚠ |
| async-graphql | MC1 | rps | 1254.6 | 1250.0 | -0.4 |  |
| async-graphql | MC1 | p50_ms | 23.0 | 23.0 | +0.3 |  |
| async-graphql | MC1 | p99_ms | 62.3 | 62.0 | -0.4 |  |
| async-graphql | Q1 | rps | 1402.3 | 1390.1 | -0.9 |  |
| async-graphql | Q1 | p50_ms | 17.4 | 17.6 | +1.0 |  |
| async-graphql | Q1 | p99_ms | 67.3 | 67.2 | -0.1 |  |
| async-graphql | Q1_APQ | rps | 1397.8 | 1398.2 | +0.0 |  |
| async-graphql | Q1_APQ | p50_ms | 17.4 | 17.5 | +0.8 |  |
| async-graphql | Q1_APQ | p99_ms | 67.4 | 67.2 | -0.3 |  |
| async-graphql | Q2 | rps | 8257.6 | 8837.0 | +7.0 | ⚠ |
| async-graphql | Q2 | p50_ms | 4.7 | 4.5 | -4.7 |  |
| async-graphql | Q2 | p99_ms | 8.5 | 7.2 | -15.3 | ⚠ |
| async-graphql | Q2b | rps | 6106.4 | 6115.1 | +0.1 |  |
| async-graphql | Q2b | p50_ms | 6.2 | 6.2 | +0.8 |  |
| async-graphql | Q2b | p99_ms | 14.3 | 13.5 | -5.6 | ⚠ |
| async-graphql | Q2b_APQ | rps | 6322.9 | 6324.8 | +0.0 |  |
| async-graphql | Q2b_APQ | p50_ms | 6.1 | 6.0 | -0.2 |  |
| async-graphql | Q2b_APQ | p99_ms | 13.0 | 12.9 | -1.3 |  |
| async-graphql | Q3 | rps | 2694.9 | 2461.4 | -8.7 | ⚠ |
| async-graphql | Q3 | p50_ms | 13.9 | 15.1 | +8.5 | ⚠ |
| async-graphql | Q3 | p99_ms | 33.4 | 36.5 | +9.3 | ⚠ |
| async-graphql | T1 | rps | 5578.9 | 4882.8 | -12.5 | ⚠ |
| async-graphql | T1 | p50_ms | 6.7 | 7.5 | +11.3 | ⚠ |
| async-graphql | T1 | p99_ms | 14.0 | 16.0 | +14.3 | ⚠ |
| fraiseql-tv | C3 | rps | 11635.4 | 11466.6 | -1.5 |  |
| fraiseql-tv | C3 | p50_ms | 3.4 | 3.5 | +1.8 |  |
| fraiseql-tv | C3 | p99_ms | 4.8 | 4.8 | +1.0 |  |
| fraiseql-tv | F1 | rps | 10419.3 | 10367.1 | -0.5 |  |
| fraiseql-tv | F1 | p50_ms | 3.8 | 3.8 | +0.5 |  |
| fraiseql-tv | F1 | p99_ms | 5.5 | 5.5 | +0.0 |  |
| fraiseql-tv | F2 | rps | 8774.7 | 8725.7 | -0.6 |  |
| fraiseql-tv | F2 | p50_ms | 4.5 | 4.6 | +0.7 |  |
| fraiseql-tv | F2 | p99_ms | 6.4 | 6.4 | +0.6 |  |
| fraiseql-tv | F3 | rps | 9446.3 | 9477.1 | +0.3 |  |
| fraiseql-tv | F3 | p50_ms | 4.2 | 4.2 | -0.2 |  |
| fraiseql-tv | F3 | p99_ms | 5.9 | 5.9 | -0.2 |  |
| fraiseql-tv | HC3 | rps | 11559.2 | 11422.3 | -1.2 |  |
| fraiseql-tv | HC3 | p50_ms | 3.4 | 3.5 | +1.2 |  |
| fraiseql-tv | HC3 | p99_ms | 4.8 | 4.9 | +1.7 |  |
| fraiseql-tv | M1 | rps | 1128.0 | 1113.3 | -1.3 |  |
| fraiseql-tv | M1 | p50_ms | 20.3 | 20.7 | +2.2 |  |
| fraiseql-tv | M1 | p99_ms | 182.4 | 181.1 | -0.7 |  |
| fraiseql-tv | M1_APQ | rps | 1119.6 | 1086.0 | -3.0 |  |
| fraiseql-tv | M1_APQ | p50_ms | 20.5 | 20.9 | +2.1 |  |
| fraiseql-tv | M1_APQ | p99_ms | 190.9 | 197.2 | +3.3 |  |
| fraiseql-tv | M1d | rps | 10127.7 | 10179.2 | +0.5 |  |
| fraiseql-tv | M1d | p50_ms | 3.9 | 3.9 | +0.3 |  |
| fraiseql-tv | M1d | p99_ms | 5.9 | 5.8 | -1.5 |  |
| fraiseql-tv | MC1 | rps | 1103.1 | 1104.8 | +0.2 |  |
| fraiseql-tv | MC1 | p50_ms | 20.9 | 21.0 | +0.2 |  |
| fraiseql-tv | MC1 | p99_ms | 192.1 | 187.5 | -2.4 |  |
| fraiseql-tv | Q1 | rps | 9740.5 | 9782.5 | +0.4 |  |
| fraiseql-tv | Q1 | p50_ms | 4.1 | 4.1 | -0.5 |  |
| fraiseql-tv | Q1 | p99_ms | 5.8 | 5.8 | +0.2 |  |
| fraiseql-tv | Q1_APQ | rps | 9262.6 | 9384.6 | +1.3 |  |
| fraiseql-tv | Q1_APQ | p50_ms | 4.3 | 4.2 | -1.4 |  |
| fraiseql-tv | Q1_APQ | p99_ms | 6.0 | 5.9 | -1.2 |  |
| fraiseql-tv | Q2 | rps | 10979.6 | 10958.4 | -0.2 |  |
| fraiseql-tv | Q2 | p50_ms | 3.6 | 3.6 | +0.0 |  |
| fraiseql-tv | Q2 | p99_ms | 5.2 | 5.2 | +0.6 |  |
| fraiseql-tv | Q2b | rps | 9070.1 | 9119.3 | +0.5 |  |
| fraiseql-tv | Q2b | p50_ms | 4.4 | 4.4 | -0.7 |  |
| fraiseql-tv | Q2b | p99_ms | 6.2 | 6.2 | +0.3 |  |
| fraiseql-tv | Q2b_APQ | rps | 8828.5 | 8821.1 | -0.1 |  |
| fraiseql-tv | Q2b_APQ | p50_ms | 4.5 | 4.5 | +0.0 |  |
| fraiseql-tv | Q2b_APQ | p99_ms | 6.3 | 6.3 | -0.3 |  |
| fraiseql-tv | Q3 | rps | 7262.6 | 7257.5 | -0.1 |  |
| fraiseql-tv | Q3 | p50_ms | 5.5 | 5.5 | +0.0 |  |
| fraiseql-tv | Q3 | p99_ms | 7.8 | 7.8 | +0.9 |  |
| fraiseql-tv | T1 | rps | 5746.0 | 5695.1 | -0.9 |  |
| fraiseql-tv | T1 | p50_ms | 6.9 | 7.0 | +0.9 |  |
| fraiseql-tv | T1 | p99_ms | 10.0 | 10.2 | +1.2 |  |
| fraiseql-tv-audit | M1 | rps | 1065.3 | 1067.1 | +0.2 |  |
| fraiseql-tv-audit | M1 | p50_ms | 21.8 | 21.9 | +0.5 |  |
| fraiseql-tv-audit | M1 | p99_ms | 194.1 | 190.5 | -1.8 |  |
| fraiseql-tv-cache | C3 | rps | 11603.7 | 11732.1 | +1.1 |  |
| fraiseql-tv-cache | C3 | p50_ms | 3.4 | 3.4 | -1.2 |  |
| fraiseql-tv-cache | C3 | p99_ms | 4.8 | 4.8 | -0.4 |  |
| fraiseql-tv-cache | F1 | rps | 10406.5 | 10484.7 | +0.8 |  |
| fraiseql-tv-cache | F1 | p50_ms | 3.8 | 3.8 | -0.8 |  |
| fraiseql-tv-cache | F1 | p99_ms | 5.5 | 5.5 | +0.0 |  |
| fraiseql-tv-cache | F2 | rps | 8679.3 | 8739.0 | +0.7 |  |
| fraiseql-tv-cache | F2 | p50_ms | 4.6 | 4.6 | -0.7 |  |
| fraiseql-tv-cache | F2 | p99_ms | 6.5 | 6.3 | -1.7 |  |
| fraiseql-tv-cache | F3 | rps | 9382.9 | 9420.0 | +0.4 |  |
| fraiseql-tv-cache | F3 | p50_ms | 4.2 | 4.2 | -0.5 |  |
| fraiseql-tv-cache | F3 | p99_ms | 6.0 | 5.9 | -0.5 |  |
| fraiseql-tv-cache | HC3 | rps | 11433.2 | 11612.9 | +1.6 |  |
| fraiseql-tv-cache | HC3 | p50_ms | 3.5 | 3.4 | -1.4 |  |
| fraiseql-tv-cache | HC3 | p99_ms | 4.9 | 4.8 | -1.2 |  |
| fraiseql-tv-cache | M1 | rps | 1093.7 | 1099.5 | +0.5 |  |
| fraiseql-tv-cache | M1 | p50_ms | 20.9 | 20.6 | -1.7 |  |
| fraiseql-tv-cache | M1 | p99_ms | 198.1 | 190.6 | -3.8 |  |
| fraiseql-tv-cache | M1_APQ | rps | 1074.7 | 1123.5 | +4.5 |  |
| fraiseql-tv-cache | M1_APQ | p50_ms | 20.9 | 20.3 | -2.9 |  |
| fraiseql-tv-cache | M1_APQ | p99_ms | 204.1 | 190.2 | -6.8 | ⚠ |
| fraiseql-tv-cache | M1d | rps | 9869.6 | 9994.5 | +1.3 |  |
| fraiseql-tv-cache | M1d | p50_ms | 4.0 | 4.0 | -1.2 |  |
| fraiseql-tv-cache | M1d | p99_ms | 6.0 | 6.0 | -0.7 |  |
| fraiseql-tv-cache | MC1 | rps | 1069.5 | 1101.7 | +3.0 |  |
| fraiseql-tv-cache | MC1 | p50_ms | 21.4 | 21.2 | -0.7 |  |
| fraiseql-tv-cache | MC1 | p99_ms | 200.1 | 187.5 | -6.3 | ⚠ |
| fraiseql-tv-cache | Q1 | rps | 9761.2 | 9834.6 | +0.8 |  |
| fraiseql-tv-cache | Q1 | p50_ms | 4.1 | 4.0 | -0.7 |  |
| fraiseql-tv-cache | Q1 | p99_ms | 5.8 | 5.8 | +0.3 |  |
| fraiseql-tv-cache | Q1_APQ | rps | 9247.4 | 9125.7 | -1.3 |  |
| fraiseql-tv-cache | Q1_APQ | p50_ms | 4.3 | 4.3 | +0.9 |  |
| fraiseql-tv-cache | Q1_APQ | p99_ms | 6.0 | 6.1 | +0.2 |  |
| fraiseql-tv-cache | Q2 | rps | 11047.3 | 10976.4 | -0.6 |  |
| fraiseql-tv-cache | Q2 | p50_ms | 3.6 | 3.6 | +0.8 |  |
| fraiseql-tv-cache | Q2 | p99_ms | 5.2 | 5.2 | +0.4 |  |
| fraiseql-tv-cache | Q2b | rps | 9062.9 | 9044.1 | -0.2 |  |
| fraiseql-tv-cache | Q2b | p50_ms | 4.4 | 4.4 | +0.2 |  |
| fraiseql-tv-cache | Q2b | p99_ms | 6.2 | 6.2 | -0.2 |  |
| fraiseql-tv-cache | Q2b_APQ | rps | 8858.7 | 8726.7 | -1.5 |  |
| fraiseql-tv-cache | Q2b_APQ | p50_ms | 4.5 | 4.6 | +1.3 |  |
| fraiseql-tv-cache | Q2b_APQ | p99_ms | 6.3 | 6.4 | +1.3 |  |
| fraiseql-tv-cache | Q3 | rps | 7250.8 | 7189.3 | -0.8 |  |
| fraiseql-tv-cache | Q3 | p50_ms | 5.5 | 5.5 | +0.9 |  |
| fraiseql-tv-cache | Q3 | p99_ms | 7.8 | 7.9 | +0.8 |  |
| fraiseql-tv-cache | T1 | rps | 5710.9 | 5748.3 | +0.7 |  |
| fraiseql-tv-cache | T1 | p50_ms | 6.9 | 6.9 | -0.6 |  |
| fraiseql-tv-cache | T1 | p99_ms | 10.1 | 10.0 | -0.5 |  |
| fraiseql-v-cache | C3 | rps | 11117.5 | 11103.2 | -0.1 |  |
| fraiseql-v-cache | C3 | p50_ms | 3.6 | 3.6 | +0.0 |  |
| fraiseql-v-cache | C3 | p99_ms | 5.0 | 5.0 | +0.2 |  |
| fraiseql-v-cache | F1 | rps | 6230.9 | 6229.1 | -0.0 |  |
| fraiseql-v-cache | F1 | p50_ms | 4.9 | 4.9 | +0.0 |  |
| fraiseql-v-cache | F1 | p99_ms | 32.0 | 32.2 | +0.6 |  |
| fraiseql-v-cache | F2 | rps | 4638.9 | 4628.6 | -0.2 |  |
| fraiseql-v-cache | F2 | p50_ms | 6.2 | 6.3 | +0.8 |  |
| fraiseql-v-cache | F2 | p99_ms | 38.9 | 38.4 | -1.2 |  |
| fraiseql-v-cache | F3 | rps | 8662.0 | 8574.5 | -1.0 |  |
| fraiseql-v-cache | F3 | p50_ms | 4.6 | 4.6 | +1.1 |  |
| fraiseql-v-cache | F3 | p99_ms | 6.6 | 6.6 | +0.3 |  |
| fraiseql-v-cache | HC3 | rps | 11153.8 | 11149.4 | -0.0 |  |
| fraiseql-v-cache | HC3 | p50_ms | 3.6 | 3.6 | +0.3 |  |
| fraiseql-v-cache | HC3 | p99_ms | 5.0 | 5.0 | +0.4 |  |
| fraiseql-v-cache | M1 | rps | 1104.9 | 1096.6 | -0.8 |  |
| fraiseql-v-cache | M1 | p50_ms | 20.6 | 20.7 | +0.3 |  |
| fraiseql-v-cache | M1 | p99_ms | 185.1 | 193.9 | +4.8 |  |
| fraiseql-v-cache | M1_APQ | rps | 1097.2 | 1119.3 | +2.0 |  |
| fraiseql-v-cache | M1_APQ | p50_ms | 20.7 | 20.8 | +0.5 |  |
| fraiseql-v-cache | M1_APQ | p99_ms | 189.7 | 182.2 | -4.0 |  |
| fraiseql-v-cache | MC1 | rps | 1090.5 | 1070.0 | -1.9 |  |
| fraiseql-v-cache | MC1 | p50_ms | 21.4 | 21.0 | -1.7 |  |
| fraiseql-v-cache | MC1 | p99_ms | 187.6 | 202.1 | +7.8 | ⚠ |
| fraiseql-v-cache | Q1 | rps | 8861.6 | 8875.1 | +0.2 |  |
| fraiseql-v-cache | Q1 | p50_ms | 4.5 | 4.5 | -0.2 |  |
| fraiseql-v-cache | Q1 | p99_ms | 6.7 | 6.8 | +1.8 |  |
| fraiseql-v-cache | Q1_APQ | rps | 8351.9 | 8257.9 | -1.1 |  |
| fraiseql-v-cache | Q1_APQ | p50_ms | 4.8 | 4.8 | +1.3 |  |
| fraiseql-v-cache | Q1_APQ | p99_ms | 6.8 | 6.9 | +1.2 |  |
| fraiseql-v-cache | Q2 | rps | 7320.7 | 7205.2 | -1.6 |  |
| fraiseql-v-cache | Q2 | p50_ms | 4.6 | 4.6 | +1.1 |  |
| fraiseql-v-cache | Q2 | p99_ms | 25.4 | 26.2 | +3.4 |  |
| fraiseql-v-cache | Q2b | rps | 5419.3 | 5351.0 | -1.3 |  |
| fraiseql-v-cache | Q2b | p50_ms | 5.8 | 5.8 | +1.4 |  |
| fraiseql-v-cache | Q2b | p99_ms | 33.1 | 32.9 | -0.7 |  |
| fraiseql-v-cache | Q2b_APQ | rps | 5219.3 | 5122.1 | -1.9 |  |
| fraiseql-v-cache | Q2b_APQ | p50_ms | 6.0 | 6.1 | +1.8 |  |
| fraiseql-v-cache | Q2b_APQ | p99_ms | 33.2 | 33.8 | +1.7 |  |
| fraiseql-v-cache | Q3 | rps | 3451.9 | 3442.7 | -0.3 |  |
| fraiseql-v-cache | Q3 | p50_ms | 8.5 | 8.6 | +0.9 |  |
| fraiseql-v-cache | Q3 | p99_ms | 42.5 | 41.9 | -1.5 |  |
| fraiseql-v-cache | T1 | rps | 3319.2 | 3336.8 | +0.5 |  |
| fraiseql-v-cache | T1 | p50_ms | 9.5 | 9.5 | +0.1 |  |
| fraiseql-v-cache | T1 | p99_ms | 38.4 | 37.6 | -2.0 |  |
| fraiseql-v-nocache | C3 | rps | 11189.5 | 11184.0 | -0.0 |  |
| fraiseql-v-nocache | C3 | p50_ms | 3.6 | 3.6 | +0.0 |  |
| fraiseql-v-nocache | C3 | p99_ms | 5.0 | 4.9 | -0.2 |  |
| fraiseql-v-nocache | F1 | rps | 6185.3 | 6285.5 | +1.6 |  |
| fraiseql-v-nocache | F1 | p50_ms | 5.0 | 4.8 | -3.2 |  |
| fraiseql-v-nocache | F1 | p99_ms | 32.0 | 32.8 | +2.6 |  |
| fraiseql-v-nocache | F2 | rps | 4613.6 | 4637.8 | +0.5 |  |
| fraiseql-v-nocache | F2 | p50_ms | 6.3 | 6.2 | -1.8 |  |
| fraiseql-v-nocache | F2 | p99_ms | 38.9 | 39.5 | +1.6 |  |
| fraiseql-v-nocache | F3 | rps | 8615.1 | 8705.8 | +1.1 |  |
| fraiseql-v-nocache | F3 | p50_ms | 4.6 | 4.6 | -1.3 |  |
| fraiseql-v-nocache | F3 | p99_ms | 6.6 | 6.5 | -0.9 |  |
| fraiseql-v-nocache | HC3 | rps | 11254.3 | 11241.2 | -0.1 |  |
| fraiseql-v-nocache | HC3 | p50_ms | 3.5 | 3.5 | +0.0 |  |
| fraiseql-v-nocache | HC3 | p99_ms | 5.0 | 4.9 | -0.4 |  |
| fraiseql-v-nocache | M1 | rps | 1129.3 | 1115.0 | -1.3 |  |
| fraiseql-v-nocache | M1 | p50_ms | 19.8 | 20.7 | +4.8 |  |
| fraiseql-v-nocache | M1 | p99_ms | 190.3 | 188.9 | -0.8 |  |
| fraiseql-v-nocache | M1_APQ | rps | 1120.8 | 1123.6 | +0.2 |  |
| fraiseql-v-nocache | M1_APQ | p50_ms | 20.2 | 20.5 | +1.2 |  |
| fraiseql-v-nocache | M1_APQ | p99_ms | 190.9 | 187.8 | -1.6 |  |
| fraiseql-v-nocache | MC1 | rps | 1109.2 | 1099.3 | -0.9 |  |
| fraiseql-v-nocache | MC1 | p50_ms | 20.5 | 21.0 | +2.3 |  |
| fraiseql-v-nocache | MC1 | p99_ms | 188.5 | 189.3 | +0.4 |  |
| fraiseql-v-nocache | Q1 | rps | 8824.5 | 8954.0 | +1.5 |  |
| fraiseql-v-nocache | Q1 | p50_ms | 4.5 | 4.4 | -2.0 |  |
| fraiseql-v-nocache | Q1 | p99_ms | 6.6 | 6.9 | +4.8 |  |
| fraiseql-v-nocache | Q1_APQ | rps | 8347.6 | 8450.2 | +1.2 |  |
| fraiseql-v-nocache | Q1_APQ | p50_ms | 4.8 | 4.7 | -1.3 |  |
| fraiseql-v-nocache | Q1_APQ | p99_ms | 6.8 | 6.9 | +0.6 |  |
| fraiseql-v-nocache | Q2 | rps | 7251.1 | 7295.4 | +0.6 |  |
| fraiseql-v-nocache | Q2 | p50_ms | 4.6 | 4.5 | -2.2 |  |
| fraiseql-v-nocache | Q2 | p99_ms | 25.5 | 26.5 | +3.8 |  |
| fraiseql-v-nocache | Q2b | rps | 5375.1 | 5435.6 | +1.1 |  |
| fraiseql-v-nocache | Q2b | p50_ms | 5.8 | 5.8 | -0.7 |  |
| fraiseql-v-nocache | Q2b | p99_ms | 33.4 | 33.0 | -1.2 |  |
| fraiseql-v-nocache | Q2b_APQ | rps | 5159.4 | 5187.6 | +0.5 |  |
| fraiseql-v-nocache | Q2b_APQ | p50_ms | 6.0 | 5.9 | -1.5 |  |
| fraiseql-v-nocache | Q2b_APQ | p99_ms | 33.6 | 34.1 | +1.5 |  |
| fraiseql-v-nocache | Q3 | rps | 3452.6 | 3457.9 | +0.2 |  |
| fraiseql-v-nocache | Q3 | p50_ms | 8.4 | 8.4 | +0.1 |  |
| fraiseql-v-nocache | Q3 | p99_ms | 42.8 | 42.6 | -0.3 |  |
| fraiseql-v-nocache | T1 | rps | 3295.9 | 3345.6 | +1.5 |  |
| fraiseql-v-nocache | T1 | p50_ms | 9.5 | 9.4 | -0.9 |  |
| fraiseql-v-nocache | T1 | p99_ms | 38.5 | 37.9 | -1.5 |  |
| hasura | C3 | rps | 1421.4 | 1439.0 | +1.2 |  |
| hasura | C3 | p50_ms | 27.8 | 27.6 | -0.8 |  |
| hasura | C3 | p99_ms | 43.2 | 44.5 | +3.1 |  |
| hasura | F1 | rps | 1450.1 | 1404.5 | -3.1 |  |
| hasura | F1 | p50_ms | 27.5 | 27.8 | +1.1 |  |
| hasura | F1 | p99_ms | 44.4 | 44.9 | +1.2 |  |
| hasura | F2 | rps | 1157.0 | 1194.7 | +3.3 |  |
| hasura | F2 | p50_ms | 34.3 | 32.9 | -4.1 |  |
| hasura | F2 | p99_ms | 52.2 | 53.0 | +1.4 |  |
| hasura | F3 | rps | 1494.9 | 1504.5 | +0.6 |  |
| hasura | F3 | p50_ms | 26.7 | 26.2 | -1.8 |  |
| hasura | F3 | p99_ms | 44.0 | 42.1 | -4.2 |  |
| hasura | HC3 | rps | 1444.3 | 1429.4 | -1.0 |  |
| hasura | HC3 | p50_ms | 27.2 | 27.5 | +1.1 |  |
| hasura | HC3 | p99_ms | 45.7 | 43.1 | -5.7 | ⚠ |
| hasura | M1 | rps | 1856.0 | 1911.9 | +3.0 |  |
| hasura | M1 | p50_ms | 19.6 | 19.6 | +0.3 |  |
| hasura | M1 | p99_ms | 51.0 | 34.9 | -31.7 | ⚠ |
| hasura | MC1 | rps | 945.1 | 516.4 | -45.4 | ⚠ |
| hasura | MC1 | p50_ms | 33.1 | 77.3 | +133.3 | ⚠ |
| hasura | MC1 | p99_ms | 93.8 | 97.5 | +4.0 |  |
| hasura | Q1 | rps | 1542.5 | 1463.0 | -5.2 | ⚠ |
| hasura | Q1 | p50_ms | 25.7 | 27.0 | +5.1 | ⚠ |
| hasura | Q1 | p99_ms | 42.5 | 42.6 | +0.1 |  |
| hasura | Q2 | rps | 1647.2 | 1623.4 | -1.4 |  |
| hasura | Q2 | p50_ms | 24.1 | 24.7 | +2.5 |  |
| hasura | Q2 | p99_ms | 40.1 | 43.1 | +7.4 | ⚠ |
| hasura | Q2b | rps | 1332.0 | 1329.0 | -0.2 |  |
| hasura | Q2b | p50_ms | 29.3 | 30.4 | +3.7 |  |
| hasura | Q2b | p99_ms | 46.6 | 47.5 | +1.8 |  |
| hasura | Q3 | rps | 1071.2 | 1162.6 | +8.5 | ⚠ |
| hasura | Q3 | p50_ms | 37.4 | 33.3 | -10.9 | ⚠ |
| hasura | Q3 | p99_ms | 57.4 | 54.1 | -5.8 | ⚠ |
| hasura | T1 | rps | 845.6 | 930.2 | +10.0 | ⚠ |
| hasura | T1 | p50_ms | 46.8 | 42.4 | -9.5 | ⚠ |
| hasura | T1 | p99_ms | 67.4 | 62.4 | -7.4 | ⚠ |
| mercurius | C3 | rps | 6771.9 | 6666.4 | -1.6 |  |
| mercurius | C3 | p50_ms | 5.5 | 5.6 | +1.8 |  |
| mercurius | C3 | p99_ms | 12.5 | 12.8 | +2.2 |  |
| mercurius | F1 | rps | 4176.2 | 4348.7 | +4.1 |  |
| mercurius | F1 | p50_ms | 8.7 | 8.5 | -1.7 |  |
| mercurius | F1 | p99_ms | 21.1 | 19.6 | -7.3 | ⚠ |
| mercurius | F2 | rps | 3100.5 | 3098.6 | -0.1 |  |
| mercurius | F2 | p50_ms | 11.8 | 11.8 | -0.1 |  |
| mercurius | F2 | p99_ms | 26.1 | 26.2 | +0.5 |  |
| mercurius | F3 | rps | 1452.8 | 1466.1 | +0.9 |  |
| mercurius | F3 | p50_ms | 18.0 | 17.9 | -0.3 |  |
| mercurius | F3 | p99_ms | 76.0 | 74.8 | -1.6 |  |
| mercurius | HC3 | rps | 6884.5 | 6099.8 | -11.4 | ⚠ |
| mercurius | HC3 | p50_ms | 5.4 | 5.9 | +9.3 | ⚠ |
| mercurius | HC3 | p99_ms | 12.4 | 15.5 | +25.5 | ⚠ |
| mercurius | M1 | rps | 4039.1 | 3976.0 | -1.6 |  |
| mercurius | M1 | p50_ms | 9.4 | 9.5 | +1.1 |  |
| mercurius | M1 | p99_ms | 21.1 | 22.8 | +8.2 | ⚠ |
| mercurius | M1_APQ | rps | 3978.9 | 3888.9 | -2.3 |  |
| mercurius | M1_APQ | p50_ms | 9.5 | 9.8 | +2.7 |  |
| mercurius | M1_APQ | p99_ms | 22.1 | 22.1 | -0.4 |  |
| mercurius | MC1 | rps | 1328.0 | 1328.6 | +0.0 |  |
| mercurius | MC1 | p50_ms | 27.3 | 27.4 | +0.3 |  |
| mercurius | MC1 | p99_ms | 54.4 | 54.7 | +0.5 |  |
| mercurius | Q1 | rps | 1452.1 | 1458.3 | +0.4 |  |
| mercurius | Q1 | p50_ms | 17.8 | 17.8 | -0.1 |  |
| mercurius | Q1 | p99_ms | 76.9 | 76.4 | -0.6 |  |
| mercurius | Q1_APQ | rps | 1452.5 | 1452.6 | +0.0 |  |
| mercurius | Q1_APQ | p50_ms | 18.2 | 18.1 | -0.2 |  |
| mercurius | Q1_APQ | p99_ms | 76.0 | 75.8 | -0.3 |  |
| mercurius | Q2 | rps | 4463.5 | 4379.1 | -1.9 |  |
| mercurius | Q2 | p50_ms | 8.2 | 8.4 | +2.6 |  |
| mercurius | Q2 | p99_ms | 19.9 | 19.8 | -0.1 |  |
| mercurius | Q2b | rps | 3043.9 | 3041.7 | -0.1 |  |
| mercurius | Q2b | p50_ms | 12.1 | 12.1 | +0.0 |  |
| mercurius | Q2b | p99_ms | 26.1 | 26.8 | +2.9 |  |
| mercurius | Q2b_APQ | rps | 3028.7 | 3057.6 | +1.0 |  |
| mercurius | Q2b_APQ | p50_ms | 12.2 | 12.0 | -1.2 |  |
| mercurius | Q2b_APQ | p99_ms | 26.3 | 26.5 | +0.9 |  |
| mercurius | Q3 | rps | 931.3 | 903.7 | -3.0 |  |
| mercurius | Q3 | p50_ms | 42.0 | 43.2 | +2.8 |  |
| mercurius | Q3 | p99_ms | 67.6 | 70.7 | +4.6 |  |
| mercurius | T1 | rps | 1777.8 | 1738.6 | -2.2 |  |
| mercurius | T1 | p50_ms | 20.7 | 21.3 | +3.0 |  |
| mercurius | T1 | p99_ms | 40.1 | 41.3 | +3.0 |  |
| postgraphile | C3 | rps | 3648.8 | 3799.5 | +4.1 |  |
| postgraphile | C3 | p50_ms | 10.1 | 9.7 | -3.9 |  |
| postgraphile | C3 | p99_ms | 29.2 | 29.2 | +0.0 |  |
| postgraphile | F1 | rps | 3241.2 | 3405.1 | +5.1 | ⚠ |
| postgraphile | F1 | p50_ms | 11.5 | 11.0 | -4.2 |  |
| postgraphile | F1 | p99_ms | 27.7 | 24.6 | -11.1 | ⚠ |
| postgraphile | F2 | rps | 2545.0 | 2622.1 | +3.0 |  |
| postgraphile | F2 | p50_ms | 14.6 | 14.3 | -2.1 |  |
| postgraphile | F2 | p99_ms | 35.0 | 32.1 | -8.3 | ⚠ |
| postgraphile | F3 | rps | 2914.2 | 3001.9 | +3.0 |  |
| postgraphile | F3 | p50_ms | 12.8 | 12.5 | -2.3 |  |
| postgraphile | F3 | p99_ms | 33.5 | 30.7 | -8.4 | ⚠ |
| postgraphile | HC3 | rps | 3820.7 | 3896.2 | +2.0 |  |
| postgraphile | HC3 | p50_ms | 9.7 | 9.5 | -1.9 |  |
| postgraphile | HC3 | p99_ms | 25.4 | 24.4 | -3.8 |  |
| postgraphile | M1 | rps | 3001.3 | 2967.2 | -1.1 |  |
| postgraphile | M1 | p50_ms | 11.5 | 11.4 | -0.7 |  |
| postgraphile | M1 | p99_ms | 46.8 | 52.6 | +12.5 | ⚠ |
| postgraphile | MC1 | rps | 1366.8 | 1338.0 | -2.1 |  |
| postgraphile | MC1 | p50_ms | 26.1 | 26.0 | -0.1 |  |
| postgraphile | MC1 | p99_ms | 76.0 | 90.0 | +18.5 | ⚠ |
| postgraphile | Q1 | rps | 3153.2 | 3237.3 | +2.7 |  |
| postgraphile | Q1 | p50_ms | 12.2 | 11.7 | -4.4 |  |
| postgraphile | Q1 | p99_ms | 24.2 | 26.2 | +8.3 | ⚠ |
| postgraphile | Q2 | rps | 3685.3 | 3547.8 | -3.7 |  |
| postgraphile | Q2 | p50_ms | 10.3 | 10.4 | +1.6 |  |
| postgraphile | Q2 | p99_ms | 22.2 | 27.4 | +23.7 | ⚠ |
| postgraphile | Q2b | rps | 2658.2 | 2750.5 | +3.5 |  |
| postgraphile | Q2b | p50_ms | 14.2 | 13.7 | -3.4 |  |
| postgraphile | Q2b | p99_ms | 32.4 | 30.9 | -4.8 |  |
| postgraphile | Q3 | rps | 1596.0 | 1584.9 | -0.7 |  |
| postgraphile | Q3 | p50_ms | 23.2 | 23.3 | +0.5 |  |
| postgraphile | Q3 | p99_ms | 53.5 | 54.0 | +1.1 |  |
| postgraphile | T1 | rps | 2075.1 | 2118.3 | +2.1 |  |
| postgraphile | T1 | p50_ms | 17.3 | 16.9 | -2.3 |  |
| postgraphile | T1 | p99_ms | 62.7 | 61.5 | -1.9 |  |
| strawberry | C3 | rps | 1547.2 | 1531.1 | -1.0 |  |
| strawberry | C3 | p50_ms | 24.7 | 25.4 | +3.0 |  |
| strawberry | C3 | p99_ms | 63.0 | 66.0 | +4.8 |  |
| strawberry | F1 | rps | 1255.5 | 1255.4 | -0.0 |  |
| strawberry | F1 | p50_ms | 31.8 | 30.6 | -3.8 |  |
| strawberry | F1 | p99_ms | 74.7 | 68.6 | -8.1 | ⚠ |
| strawberry | F2 | rps | 920.9 | 931.2 | +1.1 |  |
| strawberry | F2 | p50_ms | 41.2 | 48.4 | +17.5 | ⚠ |
| strawberry | F2 | p99_ms | 83.8 | 87.4 | +4.2 |  |
| strawberry | F3 | rps | 953.3 | 961.2 | +0.8 |  |
| strawberry | F3 | p50_ms | 40.2 | 40.0 | -0.7 |  |
| strawberry | F3 | p99_ms | 85.5 | 80.7 | -5.6 | ⚠ |
| strawberry | HC3 | rps | 1531.5 | 1525.8 | -0.4 |  |
| strawberry | HC3 | p50_ms | 24.2 | 24.8 | +2.5 |  |
| strawberry | HC3 | p99_ms | 61.9 | 66.3 | +7.0 | ⚠ |
| strawberry | M1 | rps | 1253.8 | 1268.2 | +1.1 |  |
| strawberry | M1 | p50_ms | 30.4 | 30.5 | +0.4 |  |
| strawberry | M1 | p99_ms | 70.7 | 69.0 | -2.4 |  |
| strawberry | MC1 | rps | 538.5 | 547.9 | +1.7 |  |
| strawberry | MC1 | p50_ms | 74.7 | 89.1 | +19.3 | ⚠ |
| strawberry | MC1 | p99_ms | 129.1 | 150.2 | +16.3 | ⚠ |
| strawberry | Q1 | rps | 967.9 | 976.2 | +0.9 |  |
| strawberry | Q1 | p50_ms | 39.8 | 39.4 | -1.0 |  |
| strawberry | Q1 | p99_ms | 82.5 | 78.9 | -4.4 |  |
| strawberry | Q2 | rps | 1385.0 | 1398.4 | +1.0 |  |
| strawberry | Q2 | p50_ms | 27.5 | 27.9 | +1.5 |  |
| strawberry | Q2 | p99_ms | 60.0 | 65.0 | +8.3 | ⚠ |
| strawberry | Q2b | rps | 984.4 | 980.5 | -0.4 |  |
| strawberry | Q2b | p50_ms | 45.5 | 39.4 | -13.4 | ⚠ |
| strawberry | Q2b | p99_ms | 93.2 | 77.3 | -17.1 | ⚠ |
| strawberry | Q3 | rps | 503.4 | 516.1 | +2.5 |  |
| strawberry | Q3 | p50_ms | 77.5 | 73.8 | -4.8 |  |
| strawberry | Q3 | p99_ms | 137.8 | 138.5 | +0.6 |  |
| strawberry | T1 | rps | 650.3 | 653.1 | +0.4 |  |
| strawberry | T1 | p50_ms | 58.6 | 59.9 | +2.3 |  |
| strawberry | T1 | p99_ms | 105.1 | 106.2 | +1.1 |  |

**Summary**: 70/468 cells flagged (15.0%) — gate limit 25% → **PASS**
