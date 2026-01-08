# Université Brest E2E Testing Strategy
## Integration with PrintOptim ETL Remote Server

**Date**: 2026-01-08
**Dataflow Identifier**: `univ-brest.r2qenvmnqb@printoptim.fr`
**Email Address**: `univ-brest.r2qenvmnqb@printoptim.fr`
**Environment**: Production (printoptim.io) + Test (printoptim.dev)

---

## Current Status

### ✅ Existing Configuration
```
Database:     printoptim_db_production (printoptim.io)
Dataflow:     univ-brest.r2qenvmnqb@printoptim.fr (configured in v_dataflow)
Organization: Université Brest
Email Inbox:  univ-brest.r2qenvmnqb@printoptim.fr
Credentials:  Available in pass (password store)
```

### ❌ Current Limitations
```
No emails ingested yet (etl_ingest.tb_email_received is empty)
Dataflow exists in production DB only (not in test DB)
No test data seeded for univ-brest
No E2E test emails configured
```

---

## Two-Path Strategy

### **Path A: Use Production Dataflow + Test Database** (RECOMMENDED)

This approach leverages the existing univ-brest production configuration while testing against the prepared test database on printoptim.dev.

#### Steps:

**1. Copy Production Dataflow to Test Database**

```bash
# On printoptim.io, export univ-brest dataflow
psql -d printoptim_db_production \
  -c "SELECT * FROM v_dataflow WHERE identifier = 'univ-brest.r2qenvmnqb@printoptim.fr'" \
  > /tmp/univ-brest-dataflow.csv

# Transfer to test server
scp /tmp/univ-brest-dataflow.csv lionel@printoptim.dev:/tmp/

# On printoptim.dev, insert into test database
# (Need to determine correct target table - likely central.tb_dataflow or similar)
```

**2. Create Test Emails with Univ-Brest Data**

Since we don't have real emails yet, create synthetic test emails that match univ-brest's expected format:

```python
# tests/e2e/test_univ_brest_real_dataflow.py

@pytest.mark.e2e
async def test_univ_brest_email_with_real_dataflow(greenmail_smtp, greenmail_imap):
    """
    Test: Full E2E pipeline with univ-brest dataflow

    Validates:
    - Email sent with univ-brest credentials
    - Dataflow recognized and field mapping applied
    - Meter data loaded to appropriate tables
    - Volumes calculated correctly
    """

    # 1. Create test Excel matching univ-brest format
    excel_bytes = create_univ_brest_excel(
        num_machines=10,
        num_readings=12  # One year of monthly readings
    )

    # 2. Send email from univ-brest address
    await send_test_email(
        from_addr="univ-brest.r2qenvmnqb@printoptim.fr",
        to_addr="etl@printoptim.local",
        subject="Relevés de consommation janvier-décembre 2025",
        body="Cf. pièce jointe",
        attachments=[("releves_2025.xlsx", excel_bytes)]
    )

    # 3. Fetch and process via EmailProcessingService
    service = EmailProcessingService()
    result = await service.process_unread_emails(
        dataflow_identifier="univ-brest.r2qenvmnqb@printoptim.fr"
    )

    # 4. Verify results
    assert result['emails_processed'] == 1
    assert result['attachments_extracted'] == 1
    assert result['files_processed'] == 1
    assert result['meters_loaded'] > 0
    assert result['meters_failed'] == 0

    # 5. Verify data in database
    # Check tb_meter tables for univ-brest data
    # Check volume calculations
```

**3. Define Univ-Brest Test Data Format**

```python
# tests/e2e/univ_brest_data_generator.py

class UnivBrestDataGenerator:
    """Generate test data matching Université Brest's expected format"""

    @staticmethod
    def create_standard_excel(num_machines=10, num_readings=12):
        """
        Université Brest format expectations:
        - Columns: Machine_ID, Date, Mono_Count, Color_Count
        - Dates: Monthly readings
        - Machines: Campus printers (naming convention?)
        """
        df = pd.DataFrame({
            'Machine_ID': ['BREST-PRINT-001'] * num_readings +
                          ['BREST-PRINT-002'] * num_readings,
            'Date': (list(pd.date_range('2025-01-01', periods=num_readings, freq='MS')) *
                    (num_machines // 1 + 1))[:num_machines * num_readings],
            'Mono_Count': np.random.randint(10000, 50000, num_machines * num_readings),
            'Color_Count': np.random.randint(5000, 25000, num_machines * num_readings),
        })
        # Convert to Excel with proper formatting
        return df_to_excel_bytes(df)
```

**4. Configure Field Mapping for Univ-Brest**

Query existing field mapping from production:

```bash
ssh lionel@printoptim.io "psql -d printoptim_db_production -c \
  \"SELECT * FROM v_dataflow_etl WHERE identifier = 'univ-brest.r2qenvmnqb@printoptim.fr'\" "
```

Then create test configuration:

```python
# tests/e2e/conftest.py - add fixture for univ-brest dataflow

@pytest.fixture
async def univ_brest_dataflow():
    """Mock Université Brest dataflow with real field mappings"""
    return UnivBrestDataflow(
        identifier="univ-brest.r2qenvmnqb@printoptim.fr",
        field_mappings={
            "Machine_ID": "machine_serial_number",
            "Date": "meter_date",
            "Mono_Count": "meter_mono",
            "Color_Count": "meter_color",
        },
        fk_customer_org=123,  # Université Brest org ID
    )
```

---

### **Path B: Connect to Production Email Server** (ALTERNATIVE)

Actually fetch real emails from production univ-brest inbox:

```bash
# Configuration for production connection
DATABASE_URL=postgresql://user:pass@printoptim.io/printoptim_db_production
IMAP_SERVER=mail.printoptim.fr (or internal mail system)
IMAP_EMAIL=univ-brest.r2qenvmnqb@printoptim.fr
IMAP_PASSWORD=<from pass store>
```

**Advantages**:
- Tests real email infrastructure
- Uses actual meter data if emails exist

**Disadvantages**:
- Slower (real IMAP connections)
- Requires credentials in test environment
- May affect production mailbox
- Need real emails in inbox

---

## Implementation Plan

### Phase 1: Setup (1-2 hours)

1. **Retrieve Production Configuration**
   ```bash
   ssh lionel@printoptim.io "psql -d printoptim_db_production -c \
     \"SELECT * FROM v_dataflow WHERE identifier LIKE '%brest%'\" "
   ```

2. **Create Univ-Brest Test Data Generator**
   - Analyze expected column names from production dataflow
   - Create realistic meter data (campus machines, monthly readings)
   - Support various file formats (Excel, CSV)

3. **Seed Test Database**
   - Copy univ-brest dataflow to test DB
   - Copy organization/customer data to test DB
   - Verify field mappings work in test environment

### Phase 2: E2E Tests (2-3 hours)

1. **Create Univ-Brest Test Suite**
   - `test_univ_brest_single_email.py` - Single file processing
   - `test_univ_brest_multiple_emails.py` - Multiple emails/files
   - `test_univ_brest_monthly_batch.py` - Realistic monthly batch
   - `test_univ_brest_volume_calculation.py` - Volume aggregation
   - `test_univ_brest_error_scenarios.py` - Error handling

2. **Database Integration Tests**
   - Verify meters loaded to correct year-partition
   - Verify volume calculations
   - Verify FK relationships maintained
   - Test idempotent loading (same email twice)

3. **Field Mapping Validation**
   - Verify column name transformation
   - Verify data type conversions
   - Verify NULL handling

### Phase 3: Production Readiness (1 hour)

1. **CI/CD Integration**
   - Add univ-brest tests to pytest suite
   - Create daily email fetch scheduled task
   - Set up monitoring/alerting

2. **Documentation**
   - Document univ-brest email format
   - Document expected meter readings
   - Create troubleshooting guide

---

## Recommended Approach

**Use Path A with GreenMail**:

1. Create `UnivBrestDataGenerator` that mimics real univ-brest format
2. Send test emails via GreenMail with univ-brest credentials
3. Test full pipeline including dataflow field mapping
4. Verify database loading with test data
5. Later, can connect to production mailbox for real data validation

**Why**:
- ✅ Fast (no real email latency)
- ✅ Deterministic (same test data every time)
- ✅ No production dependencies
- ✅ Can test error scenarios
- ✅ Sets up for Phase 4 (real production testing)

---

## Test Data Requirements

### Expected Univ-Brest Format

Need to determine from production:

```bash
# Find example column names from production dataflow
ssh lionel@printoptim.io "psql -d printoptim_db_production -c \
  \"SELECT field_mapping FROM v_dataflow WHERE identifier = 'univ-brest.r2qenvmnqb@printoptim.fr'\""
```

Likely format:
```
Column Headers (needs confirmation):
- Machine_Serial / Machine_ID / Equipment_ID
- Date / Reading_Date / Meter_Date
- Mono / Mono_Count / Mono_Reading
- Color / Color_Count / Color_Reading
```

Monthly readings scenario:
```
12 months × 10-20 machines = 120-240 meter records per year
Dates: Monthly (1st of each month, or last day?)
Values: Typical office/educational institution meter counts
```

---

## Implementation Files Needed

1. **tests/e2e/univ_brest_data_generator.py**
   - `UnivBrestDataGenerator` class
   - Create Excel with proper format
   - Create CSV variations
   - Support different date formats

2. **tests/e2e/test_univ_brest_real_dataflow.py**
   - Full E2E with real dataflow
   - Field mapping validation
   - Database integration

3. **tests/e2e/conftest.py** (update)
   - `univ_brest_dataflow` fixture
   - Mock dataflow with real field mappings

4. **src/printoptim_etl/domain/models/univ_brest.py** (optional)
   - UnivBrestMeter domain model
   - Validation rules specific to univ-brest

---

## Questions to Answer First

Before implementation, need to confirm:

1. **Exact column names in univ-brest emails?**
   - Check production dataflow configuration
   - Look at field_mapping in v_dataflow_etl

2. **What date range/frequency?**
   - Monthly? Daily? Weekly?
   - How far back in history?

3. **Machine naming convention?**
   - Serial numbers?
   - Campus locations?
   - Department codes?

4. **Expected meter count ranges?**
   - Min/max values
   - Realistic usage patterns

5. **Any special handling?**
   - Multi-site reading aggregation?
   - Department-level summaries?
   - Any calculated fields?

---

## Next Steps

1. **Retrieve Production Config** (~5 min)
   ```bash
   ssh lionel@printoptim.io "psql -d printoptim_db_production -c \
     \"SELECT pk_dataflow, identifier, fk_customer_org FROM v_dataflow \
      WHERE identifier = 'univ-brest.r2qenvmnqb@printoptim.fr'\""
   ```

2. **Analyze Real Format** (~15 min)
   - Check field mappings in production
   - Determine expected column names
   - Understand data validation rules

3. **Create Generator** (~30 min)
   - Build `UnivBrestDataGenerator`
   - Create Excel templates
   - Support multiple machines/dates

4. **Implement Tests** (~2 hours)
   - Create test suite
   - Verify dataflow loading
   - Test database integration

5. **Deploy to Remote** (~10 min)
   - Copy files to printoptim.dev
   - Run tests
   - Verify all 44 + new tests pass

---

**Total Time to Full Univ-Brest E2E Testing**: ~3-4 hours

---

Generated: 2026-01-08 @ 09:00 UTC
