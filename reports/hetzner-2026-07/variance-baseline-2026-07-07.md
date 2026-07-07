# Run-to-Run Delta Report

**Run A**: reports/hetzner-2026-07/bench-hetzner-2026-07-07-sweep3.json  
**Run B**: reports/hetzner-2026-07/bench-hetzner-2026-07-07-sweep4.json  
**Cell threshold**: ±5%  

| Framework | Query | Metric | A | B | Δ% | |
|-----------|-------|--------|--:|--:|---:|--|
| actix-web-rest | C3 | rps | 10941.3 | 11213.7 | +2.5 |  |
| actix-web-rest | C3 | p50_ms | 3.6 | 3.5 | -1.4 |  |
| actix-web-rest | C3 | p99_ms | 5.0 | 4.3 | -14.3 | ⚠ |
| actix-web-rest | F1 | rps | 8841.2 | 8803.8 | -0.4 |  |
| actix-web-rest | F1 | p50_ms | 4.4 | 4.5 | +1.4 |  |
| actix-web-rest | F1 | p99_ms | 6.2 | 5.8 | -5.7 | ⚠ |
| actix-web-rest | F2 | rps | 3633.4 | 3712.4 | +2.2 |  |
| actix-web-rest | F2 | p50_ms | 10.8 | 10.6 | -1.8 |  |
| actix-web-rest | F2 | p99_ms | 16.3 | 16.3 | +0.2 |  |
| actix-web-rest | F3 | rps | 1290.3 | 1317.8 | +2.1 |  |
| actix-web-rest | F3 | p50_ms | 30.3 | 29.4 | -2.8 |  |
| actix-web-rest | F3 | p99_ms | 40.2 | 39.1 | -2.8 |  |
| actix-web-rest | HC3 | rps | 11017.7 | 11175.1 | +1.4 |  |
| actix-web-rest | HC3 | p50_ms | 3.6 | 3.5 | -1.9 |  |
| actix-web-rest | HC3 | p99_ms | 4.5 | 4.8 | +8.3 | ⚠ |
| actix-web-rest | M1 | rps | 1646.2 | 1837.6 | +11.6 | ⚠ |
| actix-web-rest | M1 | p50_ms | 24.9 | 21.9 | -12.1 | ⚠ |
| actix-web-rest | M1 | p99_ms | 29.0 | 28.2 | -2.9 |  |
| actix-web-rest | MC1 | rps | 954.6 | 990.9 | +3.8 |  |
| actix-web-rest | MC1 | p50_ms | 40.6 | 39.0 | -3.9 |  |
| actix-web-rest | MC1 | p99_ms | 53.6 | 51.9 | -3.2 |  |
| actix-web-rest | Q1 | rps | 1339.4 | 1386.6 | +3.5 |  |
| actix-web-rest | Q1 | p50_ms | 29.2 | 28.1 | -3.6 |  |
| actix-web-rest | Q1 | p99_ms | 40.2 | 37.8 | -6.0 | ⚠ |
| actix-web-rest | Q2 | rps | 8824.5 | 9210.1 | +4.4 |  |
| actix-web-rest | Q2 | p50_ms | 4.4 | 4.3 | -3.4 |  |
| actix-web-rest | Q2 | p99_ms | 6.7 | 5.7 | -14.5 | ⚠ |
| actix-web-rest | Q2b | rps | 4250.2 | 4419.4 | +4.0 |  |
| actix-web-rest | Q2b | p50_ms | 9.2 | 8.8 | -4.1 |  |
| actix-web-rest | Q2b | p99_ms | 13.7 | 11.6 | -15.7 | ⚠ |
| actix-web-rest | Q3 | rps | 3281.4 | 3337.5 | +1.7 |  |
| actix-web-rest | Q3 | p50_ms | 11.9 | 11.8 | -1.1 |  |
| actix-web-rest | Q3 | p99_ms | 15.1 | 14.9 | -0.8 |  |
| actix-web-rest | T1 | rps | 2568.0 | 2567.0 | -0.0 |  |
| actix-web-rest | T1 | p50_ms | 15.4 | 15.4 | -0.2 |  |
| actix-web-rest | T1 | p99_ms | 18.1 | 19.5 | +7.5 | ⚠ |
| apollo-server | C3 | rps | 2330.6 | 2618.8 | +12.4 | ⚠ |
| apollo-server | C3 | p50_ms | 16.3 | 14.7 | -9.6 | ⚠ |
| apollo-server | C3 | p99_ms | 32.6 | 27.8 | -14.9 | ⚠ |
| apollo-server | F1 | rps | 2028.2 | 2073.7 | +2.2 |  |
| apollo-server | F1 | p50_ms | 18.9 | 18.5 | -1.9 |  |
| apollo-server | F1 | p99_ms | 37.9 | 36.7 | -3.1 |  |
| apollo-server | F2 | rps | 1452.1 | 1504.6 | +3.6 |  |
| apollo-server | F2 | p50_ms | 25.8 | 25.2 | -2.4 |  |
| apollo-server | F2 | p99_ms | 54.0 | 49.8 | -7.8 | ⚠ |
| apollo-server | F3 | rps | 1282.8 | 1331.7 | +3.8 |  |
| apollo-server | F3 | p50_ms | 30.8 | 29.7 | -3.5 |  |
| apollo-server | F3 | p99_ms | 49.3 | 46.3 | -6.0 | ⚠ |
| apollo-server | HC3 | rps | 2274.7 | 2579.6 | +13.4 | ⚠ |
| apollo-server | HC3 | p50_ms | 16.7 | 15.0 | -10.5 | ⚠ |
| apollo-server | HC3 | p99_ms | 33.6 | 27.5 | -18.3 | ⚠ |
| apollo-server | M1 | rps | 1631.0 | 1782.2 | +9.3 | ⚠ |
| apollo-server | M1 | p50_ms | 22.3 | 20.8 | -6.9 | ⚠ |
| apollo-server | M1 | p99_ms | 53.8 | 47.8 | -11.0 | ⚠ |
| apollo-server | M1_APQ | rps | 1682.1 | 1729.5 | +2.8 |  |
| apollo-server | M1_APQ | p50_ms | 22.0 | 21.4 | -2.7 |  |
| apollo-server | M1_APQ | p99_ms | 50.9 | 50.8 | -0.3 |  |
| apollo-server | MC1 | rps | 791.3 | 812.1 | +2.6 |  |
| apollo-server | MC1 | p50_ms | 48.1 | 46.8 | -2.6 |  |
| apollo-server | MC1 | p99_ms | 79.9 | 71.7 | -10.3 | ⚠ |
| apollo-server | Q1 | rps | 1295.2 | 1297.4 | +0.2 |  |
| apollo-server | Q1 | p50_ms | 30.3 | 30.4 | +0.1 |  |
| apollo-server | Q1 | p99_ms | 52.7 | 53.1 | +0.8 |  |
| apollo-server | Q1_APQ | rps | 1282.6 | 1332.0 | +3.9 |  |
| apollo-server | Q1_APQ | p50_ms | 30.8 | 29.9 | -2.9 |  |
| apollo-server | Q1_APQ | p99_ms | 50.3 | 46.1 | -8.4 | ⚠ |
| apollo-server | Q2 | rps | 2059.7 | 2020.7 | -1.9 |  |
| apollo-server | Q2 | p50_ms | 18.6 | 18.8 | +1.3 |  |
| apollo-server | Q2 | p99_ms | 37.9 | 39.9 | +5.3 | ⚠ |
| apollo-server | Q2b | rps | 1439.3 | 1512.7 | +5.1 | ⚠ |
| apollo-server | Q2b | p50_ms | 26.3 | 25.0 | -4.9 |  |
| apollo-server | Q2b | p99_ms | 52.8 | 50.9 | -3.7 |  |
| apollo-server | Q2b_APQ | rps | 1503.5 | 1489.0 | -1.0 |  |
| apollo-server | Q2b_APQ | p50_ms | 25.1 | 25.4 | +1.0 |  |
| apollo-server | Q2b_APQ | p99_ms | 51.2 | 51.3 | +0.2 |  |
| apollo-server | Q3 | rps | 495.9 | 501.1 | +1.0 |  |
| apollo-server | Q3 | p50_ms | 79.7 | 78.2 | -1.8 |  |
| apollo-server | Q3 | p99_ms | 129.0 | 127.7 | -1.0 |  |
| apollo-server | T1 | rps | 917.9 | 922.4 | +0.5 |  |
| apollo-server | T1 | p50_ms | 41.6 | 39.9 | -4.3 |  |
| apollo-server | T1 | p99_ms | 72.2 | 73.0 | +1.2 |  |
| async-graphql | C3 | rps | 10722.7 | 10365.8 | -3.3 |  |
| async-graphql | C3 | p50_ms | 3.6 | 3.8 | +7.0 | ⚠ |
| async-graphql | C3 | p99_ms | 6.2 | 5.9 | -5.0 | ⚠ |
| async-graphql | F1 | rps | 6010.4 | 5923.9 | -1.4 |  |
| async-graphql | F1 | p50_ms | 6.3 | 6.7 | +6.7 | ⚠ |
| async-graphql | F1 | p99_ms | 11.8 | 10.7 | -9.8 | ⚠ |
| async-graphql | F2 | rps | 3904.1 | 4019.3 | +3.0 |  |
| async-graphql | F2 | p50_ms | 9.5 | 9.7 | +2.1 |  |
| async-graphql | F2 | p99_ms | 20.9 | 16.7 | -20.3 | ⚠ |
| async-graphql | F3 | rps | 1142.4 | 1213.4 | +6.2 | ⚠ |
| async-graphql | F3 | p50_ms | 22.7 | 21.5 | -5.2 | ⚠ |
| async-graphql | F3 | p99_ms | 73.5 | 70.7 | -3.8 |  |
| async-graphql | HC3 | rps | 10666.9 | 10403.9 | -2.5 |  |
| async-graphql | HC3 | p50_ms | 3.6 | 3.8 | +6.4 | ⚠ |
| async-graphql | HC3 | p99_ms | 6.4 | 5.9 | -8.2 | ⚠ |
| async-graphql | M1 | rps | 6497.7 | 6051.4 | -6.9 | ⚠ |
| async-graphql | M1 | p50_ms | 6.1 | 6.6 | +8.1 | ⚠ |
| async-graphql | M1 | p99_ms | 8.6 | 8.8 | +1.5 |  |
| async-graphql | M1_APQ | rps | 6759.8 | 6186.7 | -8.5 | ⚠ |
| async-graphql | M1_APQ | p50_ms | 5.8 | 6.4 | +9.9 | ⚠ |
| async-graphql | M1_APQ | p99_ms | 8.3 | 8.6 | +3.4 |  |
| async-graphql | MC1 | rps | 1025.1 | 1072.8 | +4.7 |  |
| async-graphql | MC1 | p50_ms | 30.1 | 28.6 | -5.1 | ⚠ |
| async-graphql | MC1 | p99_ms | 67.5 | 65.5 | -3.0 |  |
| async-graphql | Q1 | rps | 1144.5 | 1207.2 | +5.5 | ⚠ |
| async-graphql | Q1 | p50_ms | 22.8 | 21.7 | -4.9 |  |
| async-graphql | Q1 | p99_ms | 73.6 | 71.0 | -3.6 |  |
| async-graphql | Q1_APQ | rps | 1135.3 | 1200.9 | +5.8 | ⚠ |
| async-graphql | Q1_APQ | p50_ms | 22.8 | 21.6 | -5.2 | ⚠ |
| async-graphql | Q1_APQ | p99_ms | 73.8 | 71.2 | -3.5 |  |
| async-graphql | Q2 | rps | 6249.2 | 5976.9 | -4.4 |  |
| async-graphql | Q2 | p50_ms | 6.0 | 6.6 | +10.1 | ⚠ |
| async-graphql | Q2 | p99_ms | 10.8 | 10.5 | -2.8 |  |
| async-graphql | Q2b | rps | 4194.8 | 3445.7 | -17.9 | ⚠ |
| async-graphql | Q2b | p50_ms | 8.7 | 11.0 | +26.0 | ⚠ |
| async-graphql | Q2b | p99_ms | 20.2 | 24.6 | +21.3 | ⚠ |
| async-graphql | Q2b_APQ | rps | 3966.5 | 3860.9 | -2.7 |  |
| async-graphql | Q2b_APQ | p50_ms | 9.4 | 9.7 | +3.5 |  |
| async-graphql | Q2b_APQ | p99_ms | 20.4 | 22.0 | +7.8 | ⚠ |
| async-graphql | Q3 | rps | 1421.1 | 1313.8 | -7.6 | ⚠ |
| async-graphql | Q3 | p50_ms | 27.3 | 29.9 | +9.6 | ⚠ |
| async-graphql | Q3 | p99_ms | 61.9 | 62.0 | +0.3 |  |
| async-graphql | T1 | rps | 3269.9 | 3606.0 | +10.3 | ⚠ |
| async-graphql | T1 | p50_ms | 11.8 | 10.5 | -10.8 | ⚠ |
| async-graphql | T1 | p99_ms | 23.2 | 22.5 | -3.0 |  |
| fraiseql-tv | C3 | rps | 7645.2 | 7496.1 | -2.0 |  |
| fraiseql-tv | C3 | p50_ms | 5.1 | 5.2 | +2.1 |  |
| fraiseql-tv | C3 | p99_ms | 7.8 | 8.0 | +2.0 |  |
| fraiseql-tv | F1 | rps | 6984.1 | 7045.0 | +0.9 |  |
| fraiseql-tv | F1 | p50_ms | 5.6 | 5.6 | -0.4 |  |
| fraiseql-tv | F1 | p99_ms | 8.8 | 8.7 | -1.7 |  |
| fraiseql-tv | F2 | rps | 6001.9 | 6030.6 | +0.5 |  |
| fraiseql-tv | F2 | p50_ms | 6.5 | 6.5 | +0.0 |  |
| fraiseql-tv | F2 | p99_ms | 10.2 | 10.0 | -2.0 |  |
| fraiseql-tv | F3 | rps | 6485.4 | 6526.8 | +0.6 |  |
| fraiseql-tv | F3 | p50_ms | 6.0 | 6.0 | -0.5 |  |
| fraiseql-tv | F3 | p99_ms | 9.6 | 9.4 | -2.0 |  |
| fraiseql-tv | HC3 | rps | 7656.3 | 7748.6 | +1.2 |  |
| fraiseql-tv | HC3 | p50_ms | 5.1 | 5.0 | -1.2 |  |
| fraiseql-tv | HC3 | p99_ms | 7.8 | 7.8 | -0.4 |  |
| fraiseql-tv | M1 | rps | 88.6 | 88.6 | +0.0 |  |
| fraiseql-tv | M1 | p50_ms | 223.0 | 216.2 | -3.1 |  |
| fraiseql-tv | M1 | p99_ms | 3348.7 | 3982.3 | +18.9 | ⚠ |
| fraiseql-tv | M1_APQ | rps | 87.4 | 88.5 | +1.3 |  |
| fraiseql-tv | M1_APQ | p50_ms | 228.7 | 207.5 | -9.2 | ⚠ |
| fraiseql-tv | M1_APQ | p99_ms | 3323.3 | 4099.2 | +23.3 | ⚠ |
| fraiseql-tv | M1d | rps | 6782.9 | 6690.2 | -1.4 |  |
| fraiseql-tv | M1d | p50_ms | 5.8 | 5.9 | +1.5 |  |
| fraiseql-tv | M1d | p99_ms | 9.1 | 9.2 | +1.3 |  |
| fraiseql-tv | MC1 | rps | 89.3 | 87.9 | -1.6 |  |
| fraiseql-tv | MC1 | p50_ms | 223.5 | 206.7 | -7.5 | ⚠ |
| fraiseql-tv | MC1 | p99_ms | 3591.2 | 5247.3 | +46.1 | ⚠ |
| fraiseql-tv | Q1 | rps | 6599.0 | 6549.7 | -0.7 |  |
| fraiseql-tv | Q1 | p50_ms | 5.9 | 6.0 | +1.4 |  |
| fraiseql-tv | Q1 | p99_ms | 9.4 | 9.3 | -1.1 |  |
| fraiseql-tv | Q1_APQ | rps | 6140.7 | 6301.1 | +2.6 |  |
| fraiseql-tv | Q1_APQ | p50_ms | 6.4 | 6.2 | -2.5 |  |
| fraiseql-tv | Q1_APQ | p99_ms | 9.8 | 9.6 | -2.6 |  |
| fraiseql-tv | Q2 | rps | 7193.5 | 7270.6 | +1.1 |  |
| fraiseql-tv | Q2 | p50_ms | 5.4 | 5.4 | -0.7 |  |
| fraiseql-tv | Q2 | p99_ms | 8.5 | 8.4 | -1.9 |  |
| fraiseql-tv | Q2b | rps | 6139.0 | 6259.5 | +2.0 |  |
| fraiseql-tv | Q2b | p50_ms | 6.3 | 6.3 | -0.6 |  |
| fraiseql-tv | Q2b | p99_ms | 10.8 | 9.7 | -10.3 | ⚠ |
| fraiseql-tv | Q2b_APQ | rps | 6161.0 | 6098.7 | -1.0 |  |
| fraiseql-tv | Q2b_APQ | p50_ms | 6.3 | 6.4 | +1.3 |  |
| fraiseql-tv | Q2b_APQ | p99_ms | 9.8 | 9.8 | -0.1 |  |
| fraiseql-tv | Q3 | rps | 3207.4 | 3246.7 | +1.2 |  |
| fraiseql-tv | Q3 | p50_ms | 10.4 | 10.1 | -2.5 |  |
| fraiseql-tv | Q3 | p99_ms | 39.8 | 39.7 | -0.2 |  |
| fraiseql-tv | T1 | rps | 4050.7 | 3926.4 | -3.1 |  |
| fraiseql-tv | T1 | p50_ms | 9.5 | 9.9 | +3.6 |  |
| fraiseql-tv | T1 | p99_ms | 16.2 | 16.5 | +1.5 |  |
| fraiseql-tv-audit | M1 | rps | 91.5 | 89.1 | -2.6 |  |
| fraiseql-tv-audit | M1 | p50_ms | 191.4 | 248.0 | +29.6 | ⚠ |
| fraiseql-tv-audit | M1 | p99_ms | 3745.4 | 3195.6 | -14.7 | ⚠ |
| fraiseql-tv-cache | C3 | rps | 7628.3 | 7527.8 | -1.3 |  |
| fraiseql-tv-cache | C3 | p50_ms | 5.1 | 5.2 | +1.4 |  |
| fraiseql-tv-cache | C3 | p99_ms | 7.9 | 8.0 | +0.9 |  |
| fraiseql-tv-cache | F1 | rps | 6999.0 | 6961.3 | -0.5 |  |
| fraiseql-tv-cache | F1 | p50_ms | 5.6 | 5.6 | +0.4 |  |
| fraiseql-tv-cache | F1 | p99_ms | 8.6 | 8.8 | +1.4 |  |
| fraiseql-tv-cache | F2 | rps | 6041.7 | 5990.9 | -0.8 |  |
| fraiseql-tv-cache | F2 | p50_ms | 6.5 | 6.5 | +0.8 |  |
| fraiseql-tv-cache | F2 | p99_ms | 10.1 | 10.1 | +0.3 |  |
| fraiseql-tv-cache | F3 | rps | 6517.6 | 6361.2 | -2.4 |  |
| fraiseql-tv-cache | F3 | p50_ms | 6.0 | 6.2 | +2.7 |  |
| fraiseql-tv-cache | F3 | p99_ms | 9.3 | 9.5 | +2.0 |  |
| fraiseql-tv-cache | HC3 | rps | 7600.5 | 7628.9 | +0.4 |  |
| fraiseql-tv-cache | HC3 | p50_ms | 5.2 | 5.1 | -0.6 |  |
| fraiseql-tv-cache | HC3 | p99_ms | 7.9 | 7.9 | -0.3 |  |
| fraiseql-tv-cache | M1 | rps | 90.1 | 92.0 | +2.1 |  |
| fraiseql-tv-cache | M1 | p50_ms | 194.8 | 266.6 | +36.9 | ⚠ |
| fraiseql-tv-cache | M1 | p99_ms | 4320.1 | 2721.9 | -37.0 | ⚠ |
| fraiseql-tv-cache | M1_APQ | rps | 93.5 | 91.7 | -1.9 |  |
| fraiseql-tv-cache | M1_APQ | p50_ms | 212.3 | 251.4 | +18.4 | ⚠ |
| fraiseql-tv-cache | M1_APQ | p99_ms | 2840.7 | 2856.8 | +0.6 |  |
| fraiseql-tv-cache | M1d | rps | 6761.1 | 6674.7 | -1.3 |  |
| fraiseql-tv-cache | M1d | p50_ms | 5.8 | 5.9 | +1.2 |  |
| fraiseql-tv-cache | M1d | p99_ms | 9.1 | 9.3 | +2.0 |  |
| fraiseql-tv-cache | MC1 | rps | 92.2 | 94.8 | +2.8 |  |
| fraiseql-tv-cache | MC1 | p50_ms | 211.0 | 270.2 | +28.0 | ⚠ |
| fraiseql-tv-cache | MC1 | p99_ms | 3503.6 | 2205.1 | -37.1 | ⚠ |
| fraiseql-tv-cache | Q1 | rps | 6494.9 | 6676.8 | +2.8 |  |
| fraiseql-tv-cache | Q1 | p50_ms | 6.0 | 5.8 | -2.7 |  |
| fraiseql-tv-cache | Q1 | p99_ms | 9.6 | 9.2 | -4.1 |  |
| fraiseql-tv-cache | Q1_APQ | rps | 6295.6 | 6263.1 | -0.5 |  |
| fraiseql-tv-cache | Q1_APQ | p50_ms | 6.2 | 6.2 | +0.2 |  |
| fraiseql-tv-cache | Q1_APQ | p99_ms | 9.5 | 9.8 | +2.7 |  |
| fraiseql-tv-cache | Q2 | rps | 7217.9 | 7377.6 | +2.2 |  |
| fraiseql-tv-cache | Q2 | p50_ms | 5.4 | 5.3 | -2.2 |  |
| fraiseql-tv-cache | Q2 | p99_ms | 8.5 | 8.3 | -2.6 |  |
| fraiseql-tv-cache | Q2b | rps | 6248.7 | 6340.0 | +1.5 |  |
| fraiseql-tv-cache | Q2b | p50_ms | 6.3 | 6.2 | -1.9 |  |
| fraiseql-tv-cache | Q2b | p99_ms | 9.7 | 9.7 | +0.0 |  |
| fraiseql-tv-cache | Q2b_APQ | rps | 5315.2 | 5879.5 | +10.6 | ⚠ |
| fraiseql-tv-cache | Q2b_APQ | p50_ms | 7.4 | 6.7 | -9.1 | ⚠ |
| fraiseql-tv-cache | Q2b_APQ | p99_ms | 11.8 | 10.1 | -14.1 | ⚠ |
| fraiseql-tv-cache | Q3 | rps | 3176.4 | 3222.9 | +1.5 |  |
| fraiseql-tv-cache | Q3 | p50_ms | 10.2 | 10.2 | +0.4 |  |
| fraiseql-tv-cache | Q3 | p99_ms | 40.7 | 39.8 | -2.3 |  |
| fraiseql-tv-cache | T1 | rps | 4043.9 | 3871.9 | -4.3 |  |
| fraiseql-tv-cache | T1 | p50_ms | 9.6 | 10.0 | +4.7 |  |
| fraiseql-tv-cache | T1 | p99_ms | 16.1 | 16.7 | +3.8 |  |
| fraiseql-v-cache | C3 | rps | 7017.1 | 7628.7 | +8.7 | ⚠ |
| fraiseql-v-cache | C3 | p50_ms | 5.5 | 5.2 | -6.5 | ⚠ |
| fraiseql-v-cache | C3 | p99_ms | 9.4 | 7.7 | -17.4 | ⚠ |
| fraiseql-v-cache | F1 | rps | 4670.0 | 4732.8 | +1.3 |  |
| fraiseql-v-cache | F1 | p50_ms | 6.5 | 6.6 | +1.2 |  |
| fraiseql-v-cache | F1 | p99_ms | 37.8 | 35.6 | -5.9 | ⚠ |
| fraiseql-v-cache | F2 | rps | 3554.7 | 3594.1 | +1.1 |  |
| fraiseql-v-cache | F2 | p50_ms | 8.2 | 8.1 | -1.6 |  |
| fraiseql-v-cache | F2 | p99_ms | 43.9 | 43.2 | -1.5 |  |
| fraiseql-v-cache | F3 | rps | 6348.3 | 6362.9 | +0.2 |  |
| fraiseql-v-cache | F3 | p50_ms | 6.2 | 6.2 | +0.0 |  |
| fraiseql-v-cache | F3 | p99_ms | 9.8 | 9.5 | -2.6 |  |
| fraiseql-v-cache | HC3 | rps | 7412.5 | 7636.6 | +3.0 |  |
| fraiseql-v-cache | HC3 | p50_ms | 5.3 | 5.2 | -2.3 |  |
| fraiseql-v-cache | HC3 | p99_ms | 8.2 | 7.7 | -6.0 | ⚠ |
| fraiseql-v-cache | M1 | rps | 92.4 | 91.4 | -1.1 |  |
| fraiseql-v-cache | M1 | p50_ms | 208.7 | 192.2 | -7.9 | ⚠ |
| fraiseql-v-cache | M1 | p99_ms | 2923.1 | 5147.0 | +76.1 | ⚠ |
| fraiseql-v-cache | M1_APQ | rps | 93.1 | 95.0 | +2.0 |  |
| fraiseql-v-cache | M1_APQ | p50_ms | 206.3 | 251.9 | +22.1 | ⚠ |
| fraiseql-v-cache | M1_APQ | p99_ms | 2893.0 | 2813.8 | -2.7 |  |
| fraiseql-v-cache | MC1 | rps | 92.6 | 90.7 | -2.1 |  |
| fraiseql-v-cache | MC1 | p50_ms | 205.7 | 193.6 | -5.9 | ⚠ |
| fraiseql-v-cache | MC1 | p99_ms | 2949.0 | 4593.2 | +55.8 | ⚠ |
| fraiseql-v-cache | Q1 | rps | 6450.8 | 6503.8 | +0.8 |  |
| fraiseql-v-cache | Q1 | p50_ms | 6.1 | 6.0 | -0.7 |  |
| fraiseql-v-cache | Q1 | p99_ms | 9.8 | 9.8 | -0.8 |  |
| fraiseql-v-cache | Q1_APQ | rps | 5940.2 | 6035.6 | +1.6 |  |
| fraiseql-v-cache | Q1_APQ | p50_ms | 6.6 | 6.5 | -0.5 |  |
| fraiseql-v-cache | Q1_APQ | p99_ms | 10.5 | 9.9 | -5.8 | ⚠ |
| fraiseql-v-cache | Q2 | rps | 5658.6 | 5736.8 | +1.4 |  |
| fraiseql-v-cache | Q2 | p50_ms | 6.0 | 6.1 | +1.2 |  |
| fraiseql-v-cache | Q2 | p99_ms | 28.4 | 26.9 | -5.0 | ⚠ |
| fraiseql-v-cache | Q2b | rps | 4082.0 | 4147.1 | +1.6 |  |
| fraiseql-v-cache | Q2b | p50_ms | 7.5 | 7.5 | +0.0 |  |
| fraiseql-v-cache | Q2b | p99_ms | 39.0 | 37.5 | -3.9 |  |
| fraiseql-v-cache | Q2b_APQ | rps | 3959.4 | 4027.6 | +1.7 |  |
| fraiseql-v-cache | Q2b_APQ | p50_ms | 8.0 | 7.7 | -3.9 |  |
| fraiseql-v-cache | Q2b_APQ | p99_ms | 38.7 | 38.5 | -0.5 |  |
| fraiseql-v-cache | Q3 | rps | 1301.4 | 1303.4 | +0.2 |  |
| fraiseql-v-cache | Q3 | p50_ms | 20.0 | 19.5 | -2.2 |  |
| fraiseql-v-cache | Q3 | p99_ms | 90.4 | 93.7 | +3.6 |  |
| fraiseql-v-cache | T1 | rps | 2091.4 | 2160.2 | +3.3 |  |
| fraiseql-v-cache | T1 | p50_ms | 13.8 | 13.1 | -4.9 |  |
| fraiseql-v-cache | T1 | p99_ms | 56.7 | 56.3 | -0.8 |  |
| fraiseql-v-nocache | C3 | rps | 7484.5 | 7539.8 | +0.7 |  |
| fraiseql-v-nocache | C3 | p50_ms | 5.2 | 5.2 | -0.8 |  |
| fraiseql-v-nocache | C3 | p99_ms | 8.0 | 7.9 | -0.5 |  |
| fraiseql-v-nocache | F1 | rps | 4731.8 | 4608.5 | -2.6 |  |
| fraiseql-v-nocache | F1 | p50_ms | 6.5 | 6.6 | +1.1 |  |
| fraiseql-v-nocache | F1 | p99_ms | 37.0 | 37.9 | +2.5 |  |
| fraiseql-v-nocache | F2 | rps | 3563.3 | 3487.7 | -2.1 |  |
| fraiseql-v-nocache | F2 | p50_ms | 8.1 | 8.3 | +2.8 |  |
| fraiseql-v-nocache | F2 | p99_ms | 44.4 | 44.5 | +0.3 |  |
| fraiseql-v-nocache | F3 | rps | 6267.0 | 6105.3 | -2.6 |  |
| fraiseql-v-nocache | F3 | p50_ms | 6.3 | 6.4 | +2.7 |  |
| fraiseql-v-nocache | F3 | p99_ms | 9.8 | 10.1 | +3.2 |  |
| fraiseql-v-nocache | HC3 | rps | 7526.3 | 7558.1 | +0.4 |  |
| fraiseql-v-nocache | HC3 | p50_ms | 5.2 | 5.2 | -0.2 |  |
| fraiseql-v-nocache | HC3 | p99_ms | 7.9 | 7.9 | -0.1 |  |
| fraiseql-v-nocache | M1 | rps | 90.6 | 90.2 | -0.4 |  |
| fraiseql-v-nocache | M1 | p50_ms | 190.0 | 198.4 | +4.4 |  |
| fraiseql-v-nocache | M1 | p99_ms | 4393.8 | 3608.2 | -17.9 | ⚠ |
| fraiseql-v-nocache | M1_APQ | rps | 90.2 | 93.3 | +3.4 |  |
| fraiseql-v-nocache | M1_APQ | p50_ms | 192.3 | 196.4 | +2.1 |  |
| fraiseql-v-nocache | M1_APQ | p99_ms | 4176.7 | 3472.4 | -16.9 | ⚠ |
| fraiseql-v-nocache | MC1 | rps | 90.1 | 92.4 | +2.6 |  |
| fraiseql-v-nocache | MC1 | p50_ms | 190.9 | 223.6 | +17.1 | ⚠ |
| fraiseql-v-nocache | MC1 | p99_ms | 5225.7 | 2887.4 | -44.7 | ⚠ |
| fraiseql-v-nocache | Q1 | rps | 6412.6 | 6317.4 | -1.5 |  |
| fraiseql-v-nocache | Q1 | p50_ms | 6.1 | 6.2 | +1.6 |  |
| fraiseql-v-nocache | Q1 | p99_ms | 9.8 | 10.0 | +1.8 |  |
| fraiseql-v-nocache | Q1_APQ | rps | 6024.2 | 6084.6 | +1.0 |  |
| fraiseql-v-nocache | Q1_APQ | p50_ms | 6.5 | 6.5 | -0.6 |  |
| fraiseql-v-nocache | Q1_APQ | p99_ms | 10.1 | 9.9 | -1.9 |  |
| fraiseql-v-nocache | Q2 | rps | 5592.0 | 5445.9 | -2.6 |  |
| fraiseql-v-nocache | Q2 | p50_ms | 6.1 | 6.1 | +0.8 |  |
| fraiseql-v-nocache | Q2 | p99_ms | 29.3 | 30.7 | +5.0 | ⚠ |
| fraiseql-v-nocache | Q2b | rps | 4097.1 | 4044.8 | -1.3 |  |
| fraiseql-v-nocache | Q2b | p50_ms | 7.7 | 7.5 | -2.0 |  |
| fraiseql-v-nocache | Q2b | p99_ms | 38.4 | 39.5 | +2.9 |  |
| fraiseql-v-nocache | Q2b_APQ | rps | 3954.7 | 3973.6 | +0.5 |  |
| fraiseql-v-nocache | Q2b_APQ | p50_ms | 7.9 | 7.7 | -2.9 |  |
| fraiseql-v-nocache | Q2b_APQ | p99_ms | 39.3 | 39.6 | +0.8 |  |
| fraiseql-v-nocache | Q3 | rps | 1301.5 | 1279.9 | -1.7 |  |
| fraiseql-v-nocache | Q3 | p50_ms | 19.8 | 20.0 | +1.2 |  |
| fraiseql-v-nocache | Q3 | p99_ms | 90.4 | 92.2 | +2.0 |  |
| fraiseql-v-nocache | T1 | rps | 2117.3 | 2114.1 | -0.2 |  |
| fraiseql-v-nocache | T1 | p50_ms | 13.0 | 13.4 | +2.8 |  |
| fraiseql-v-nocache | T1 | p99_ms | 59.7 | 56.0 | -6.2 | ⚠ |
| hasura | C3 | rps | 969.2 | 988.9 | +2.0 |  |
| hasura | C3 | p50_ms | 41.4 | 41.0 | -0.9 |  |
| hasura | C3 | p99_ms | 57.2 | 57.0 | -0.4 |  |
| hasura | F1 | rps | 981.0 | 981.7 | +0.1 |  |
| hasura | F1 | p50_ms | 40.6 | 40.2 | -1.0 |  |
| hasura | F1 | p99_ms | 56.7 | 56.7 | -0.1 |  |
| hasura | F2 | rps | 940.5 | 891.1 | -5.3 | ⚠ |
| hasura | F2 | p50_ms | 41.2 | 46.1 | +11.9 | ⚠ |
| hasura | F2 | p99_ms | 63.4 | 63.9 | +0.8 |  |
| hasura | F3 | rps | 1060.4 | 1126.3 | +6.2 | ⚠ |
| hasura | F3 | p50_ms | 37.5 | 36.8 | -1.7 |  |
| hasura | F3 | p99_ms | 53.3 | 52.3 | -1.9 |  |
| hasura | HC3 | rps | 981.4 | 957.1 | -2.5 |  |
| hasura | HC3 | p50_ms | 41.0 | 41.6 | +1.5 |  |
| hasura | HC3 | p99_ms | 56.0 | 56.0 | +0.1 |  |
| hasura | M1 | rps | 659.4 | 676.7 | +2.6 |  |
| hasura | M1 | p50_ms | 60.9 | 60.4 | -0.8 |  |
| hasura | M1 | p99_ms | 78.3 | 82.9 | +5.9 | ⚠ |
| hasura | MC1 | rps | 402.2 | 405.0 | +0.7 |  |
| hasura | MC1 | p50_ms | 99.9 | 98.7 | -1.2 |  |
| hasura | MC1 | p99_ms | 118.1 | 116.8 | -1.1 |  |
| hasura | Q1 | rps | 1059.9 | 1083.3 | +2.2 |  |
| hasura | Q1 | p50_ms | 37.6 | 37.5 | -0.4 |  |
| hasura | Q1 | p99_ms | 54.0 | 53.9 | -0.3 |  |
| hasura | Q2 | rps | 1130.3 | 1123.2 | -0.6 |  |
| hasura | Q2 | p50_ms | 35.6 | 35.6 | -0.0 |  |
| hasura | Q2 | p99_ms | 51.9 | 51.3 | -1.1 |  |
| hasura | Q2b | rps | 946.8 | 905.9 | -4.3 |  |
| hasura | Q2b | p50_ms | 43.0 | 43.9 | +2.0 |  |
| hasura | Q2b | p99_ms | 58.8 | 61.1 | +4.0 |  |
| hasura | Q3 | rps | 819.8 | 796.2 | -2.9 |  |
| hasura | Q3 | p50_ms | 49.3 | 50.0 | +1.4 |  |
| hasura | Q3 | p99_ms | 66.2 | 66.9 | +1.1 |  |
| hasura | T1 | rps | 741.5 | 641.0 | -13.6 | ⚠ |
| hasura | T1 | p50_ms | 52.0 | 62.0 | +19.3 | ⚠ |
| hasura | T1 | p99_ms | 79.1 | 84.0 | +6.2 | ⚠ |
| mercurius | C3 | rps | 3860.9 | 4081.7 | +5.7 | ⚠ |
| mercurius | C3 | p50_ms | 9.7 | 9.0 | -6.5 | ⚠ |
| mercurius | C3 | p99_ms | 21.0 | 21.8 | +3.9 |  |
| mercurius | F1 | rps | 2535.9 | 2764.5 | +9.0 | ⚠ |
| mercurius | F1 | p50_ms | 14.1 | 13.4 | -5.2 | ⚠ |
| mercurius | F1 | p99_ms | 34.8 | 31.3 | -10.1 | ⚠ |
| mercurius | F2 | rps | 2062.0 | 2070.2 | +0.4 |  |
| mercurius | F2 | p50_ms | 17.8 | 17.5 | -1.5 |  |
| mercurius | F2 | p99_ms | 39.3 | 40.6 | +3.4 |  |
| mercurius | F3 | rps | 1235.8 | 1286.4 | +4.1 |  |
| mercurius | F3 | p50_ms | 22.3 | 21.3 | -4.4 |  |
| mercurius | F3 | p99_ms | 80.8 | 79.7 | -1.4 |  |
| mercurius | HC3 | rps | 3872.5 | 4057.7 | +4.8 |  |
| mercurius | HC3 | p50_ms | 9.7 | 9.1 | -6.2 | ⚠ |
| mercurius | HC3 | p99_ms | 20.6 | 21.4 | +4.0 |  |
| mercurius | M1 | rps | 2513.7 | 2546.4 | +1.3 |  |
| mercurius | M1 | p50_ms | 14.5 | 14.4 | -0.3 |  |
| mercurius | M1 | p99_ms | 33.8 | 37.9 | +12.0 | ⚠ |
| mercurius | M1_APQ | rps | 2502.1 | 2630.7 | +5.1 | ⚠ |
| mercurius | M1_APQ | p50_ms | 14.6 | 14.1 | -3.0 |  |
| mercurius | M1_APQ | p99_ms | 36.8 | 33.3 | -9.5 | ⚠ |
| mercurius | MC1 | rps | 1081.6 | 1152.0 | +6.5 | ⚠ |
| mercurius | MC1 | p50_ms | 34.3 | 32.9 | -4.2 |  |
| mercurius | MC1 | p99_ms | 63.6 | 57.6 | -9.4 | ⚠ |
| mercurius | Q1 | rps | 1216.3 | 1261.6 | +3.7 |  |
| mercurius | Q1 | p50_ms | 22.4 | 21.4 | -4.6 |  |
| mercurius | Q1 | p99_ms | 81.7 | 79.7 | -2.5 |  |
| mercurius | Q1_APQ | rps | 1233.8 | 1286.8 | +4.3 |  |
| mercurius | Q1_APQ | p50_ms | 22.3 | 21.4 | -4.2 |  |
| mercurius | Q1_APQ | p99_ms | 81.1 | 80.0 | -1.4 |  |
| mercurius | Q2 | rps | 2851.0 | 2850.4 | -0.0 |  |
| mercurius | Q2 | p50_ms | 13.2 | 12.9 | -2.1 |  |
| mercurius | Q2 | p99_ms | 29.1 | 31.2 | +7.3 | ⚠ |
| mercurius | Q2b | rps | 2195.9 | 2269.5 | +3.4 |  |
| mercurius | Q2b | p50_ms | 16.8 | 16.6 | -1.4 |  |
| mercurius | Q2b | p99_ms | 37.9 | 35.3 | -6.9 | ⚠ |
| mercurius | Q2b_APQ | rps | 2161.9 | 2174.9 | +0.6 |  |
| mercurius | Q2b_APQ | p50_ms | 17.2 | 17.0 | -1.5 |  |
| mercurius | Q2b_APQ | p99_ms | 37.8 | 38.3 | +1.4 |  |
| mercurius | Q3 | rps | 677.0 | 664.7 | -1.8 |  |
| mercurius | Q3 | p50_ms | 57.3 | 58.9 | +2.8 |  |
| mercurius | Q3 | p99_ms | 97.0 | 97.3 | +0.4 |  |
| mercurius | T1 | rps | 1214.4 | 1225.9 | +0.9 |  |
| mercurius | T1 | p50_ms | 31.0 | 29.8 | -3.9 |  |
| mercurius | T1 | p99_ms | 57.2 | 59.0 | +3.0 |  |
| postgraphile | C3 | rps | 2453.9 | 2508.0 | +2.2 |  |
| postgraphile | C3 | p50_ms | 15.4 | 15.1 | -1.8 |  |
| postgraphile | C3 | p99_ms | 38.1 | 34.9 | -8.4 | ⚠ |
| postgraphile | F1 | rps | 2081.9 | 2202.9 | +5.8 | ⚠ |
| postgraphile | F1 | p50_ms | 18.0 | 17.1 | -5.0 | ⚠ |
| postgraphile | F1 | p99_ms | 45.6 | 44.7 | -1.9 |  |
| postgraphile | F2 | rps | 1762.1 | 1805.3 | +2.5 |  |
| postgraphile | F2 | p50_ms | 21.3 | 20.8 | -2.6 |  |
| postgraphile | F2 | p99_ms | 49.1 | 49.5 | +0.9 |  |
| postgraphile | F3 | rps | 1977.0 | 2028.0 | +2.6 |  |
| postgraphile | F3 | p50_ms | 19.0 | 18.6 | -2.1 |  |
| postgraphile | F3 | p99_ms | 50.2 | 47.1 | -6.2 | ⚠ |
| postgraphile | HC3 | rps | 2329.8 | 2538.2 | +8.9 | ⚠ |
| postgraphile | HC3 | p50_ms | 16.1 | 15.1 | -6.2 | ⚠ |
| postgraphile | HC3 | p99_ms | 40.7 | 31.8 | -21.9 | ⚠ |
| postgraphile | M1 | rps | 2051.7 | 2222.4 | +8.3 | ⚠ |
| postgraphile | M1 | p50_ms | 17.1 | 15.4 | -10.3 | ⚠ |
| postgraphile | M1 | p99_ms | 71.5 | 66.7 | -6.8 | ⚠ |
| postgraphile | MC1 | rps | 946.3 | 1006.2 | +6.3 | ⚠ |
| postgraphile | MC1 | p50_ms | 38.0 | 34.6 | -9.0 | ⚠ |
| postgraphile | MC1 | p99_ms | 115.4 | 107.3 | -7.0 | ⚠ |
| postgraphile | Q1 | rps | 2048.0 | 2114.7 | +3.3 |  |
| postgraphile | Q1 | p50_ms | 18.8 | 18.1 | -3.8 |  |
| postgraphile | Q1 | p99_ms | 38.9 | 39.4 | +1.4 |  |
| postgraphile | Q2 | rps | 2146.8 | 2345.9 | +9.3 | ⚠ |
| postgraphile | Q2 | p50_ms | 17.6 | 16.0 | -8.7 | ⚠ |
| postgraphile | Q2 | p99_ms | 40.7 | 42.5 | +4.3 |  |
| postgraphile | Q2b | rps | 1953.0 | 1998.6 | +2.3 |  |
| postgraphile | Q2b | p50_ms | 19.7 | 19.1 | -3.0 |  |
| postgraphile | Q2b | p99_ms | 39.9 | 42.7 | +7.1 | ⚠ |
| postgraphile | Q3 | rps | 1177.0 | 1207.6 | +2.6 |  |
| postgraphile | Q3 | p50_ms | 31.4 | 30.6 | -2.4 |  |
| postgraphile | Q3 | p99_ms | 74.8 | 73.1 | -2.3 |  |
| postgraphile | T1 | rps | 1555.5 | 1658.5 | +6.6 | ⚠ |
| postgraphile | T1 | p50_ms | 23.5 | 22.2 | -5.5 | ⚠ |
| postgraphile | T1 | p99_ms | 83.7 | 73.1 | -12.7 | ⚠ |
| strawberry | C3 | rps | 1337.3 | 1337.8 | +0.0 |  |
| strawberry | C3 | p50_ms | 29.1 | 29.1 | +0.1 |  |
| strawberry | C3 | p99_ms | 60.4 | 58.0 | -3.8 |  |
| strawberry | F1 | rps | 1091.3 | 1139.4 | +4.4 |  |
| strawberry | F1 | p50_ms | 30.5 | 33.8 | +10.6 | ⚠ |
| strawberry | F1 | p99_ms | 88.1 | 66.4 | -24.6 | ⚠ |
| strawberry | F2 | rps | 837.1 | 850.0 | +1.5 |  |
| strawberry | F2 | p50_ms | 45.8 | 45.5 | -0.8 |  |
| strawberry | F2 | p99_ms | 80.5 | 81.4 | +1.2 |  |
| strawberry | F3 | rps | 833.2 | 873.3 | +4.8 |  |
| strawberry | F3 | p50_ms | 47.5 | 44.6 | -6.1 | ⚠ |
| strawberry | F3 | p99_ms | 95.8 | 77.2 | -19.4 | ⚠ |
| strawberry | HC3 | rps | 1275.1 | 1338.2 | +4.9 |  |
| strawberry | HC3 | p50_ms | 30.1 | 28.9 | -4.3 |  |
| strawberry | HC3 | p99_ms | 63.3 | 58.0 | -8.4 | ⚠ |
| strawberry | M1 | rps | 1108.1 | 1137.3 | +2.6 |  |
| strawberry | M1 | p50_ms | 34.0 | 33.8 | -0.6 |  |
| strawberry | M1 | p99_ms | 67.1 | 66.8 | -0.4 |  |
| strawberry | MC1 | rps | 474.4 | 500.1 | +5.4 | ⚠ |
| strawberry | MC1 | p50_ms | 80.7 | 77.9 | -3.4 |  |
| strawberry | MC1 | p99_ms | 141.4 | 114.3 | -19.2 | ⚠ |
| strawberry | Q1 | rps | 856.5 | 882.6 | +3.0 |  |
| strawberry | Q1 | p50_ms | 45.1 | 44.8 | -0.6 |  |
| strawberry | Q1 | p99_ms | 78.5 | 80.2 | +2.1 |  |
| strawberry | Q2 | rps | 1256.3 | 1262.4 | +0.5 |  |
| strawberry | Q2 | p50_ms | 30.7 | 30.6 | -0.4 |  |
| strawberry | Q2 | p99_ms | 59.4 | 57.1 | -3.9 |  |
| strawberry | Q2b | rps | 852.9 | 905.5 | +6.2 | ⚠ |
| strawberry | Q2b | p50_ms | 39.0 | 42.8 | +9.9 | ⚠ |
| strawberry | Q2b | p99_ms | 98.8 | 72.8 | -26.4 | ⚠ |
| strawberry | Q3 | rps | 461.6 | 485.4 | +5.2 | ⚠ |
| strawberry | Q3 | p50_ms | 80.2 | 79.1 | -1.3 |  |
| strawberry | Q3 | p99_ms | 152.3 | 156.6 | +2.9 |  |
| strawberry | T1 | rps | 570.0 | 597.6 | +4.8 |  |
| strawberry | T1 | p50_ms | 68.0 | 65.0 | -4.3 |  |
| strawberry | T1 | p99_ms | 113.0 | 101.7 | -10.0 | ⚠ |

**Summary**: 135/468 cells flagged (28.8%) — gate limit 25% → **FAIL**
