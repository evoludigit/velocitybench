#!/bin/bash
# Framework warmup script for benchmark testing
# Performs light load testing to warm up caches and JIT compilation

set -e

FRAMEWORK="$1"
PORT="$2"
DURATION="${3:-120}"  # Default 2 minutes
CONCURRENT_USERS="${4:-10}"

if [ -z "$FRAMEWORK" ] || [ -z "$PORT" ]; then
    echo "Usage: $0 <framework> <port> [duration_seconds] [concurrent_users]"
    echo "Example: $0 fraiseql 4000 120 10"
    exit 1
fi

echo "🔥 Starting warmup for $FRAMEWORK on port $PORT"
echo "   Duration: ${DURATION}s"
echo "   Concurrent Users: $CONCURRENT_USERS"

# Create temporary JMeter test plan for warmup with unique names
SCRIPT_PID=$$
WARMUP_PLAN="/tmp/warmup_${FRAMEWORK}_${SCRIPT_PID}.jmx"
RESULTS_FILE="/tmp/warmup_${FRAMEWORK}_${SCRIPT_PID}.jtl"

# Cleanup function to ensure temporary files are removed
cleanup() {
    rm -f "$WARMUP_PLAN" "$RESULTS_FILE"
}

# Set up cleanup on script exit
trap cleanup EXIT

cat > "$WARMUP_PLAN" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.6.3">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="Warmup Test Plan" enabled="true">
      <stringProp name="TestPlan.comments"></stringProp>
      <boolProp name="TestPlan.functional_mode">false</boolProp>
      <boolProp name="TestPlan.tearDown_on_shutdown">true</boolProp>
      <boolProp name="TestPlan.serialize_threadgroups">false</boolProp>
      <elementProp name="TestPlan.user_defined_variables" elementType="Arguments" guiclass="ArgumentsPanel" testclass="Arguments" testname="User Defined Variables" enabled="true">
        <collectionProp name="Arguments.arguments"/>
      </elementProp>
      <stringProp name="TestPlan.user_define_classpath"></stringProp>
    </TestPlan>
    <hashTree>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Warmup Thread Group" enabled="true">
        <stringProp name="ThreadGroup.on_sample_error">continue</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController" guiclass="LoopControllerGui" testclass="LoopController" testname="Loop Controller" enabled="true">
          <boolProp name="LoopController.continue_forever">false</boolProp>
          <stringProp name="LoopController.loops">-1</stringProp>
        </elementProp>
        <stringProp name="ThreadGroup.num_threads">$CONCURRENT_USERS</stringProp>
        <stringProp name="ThreadGroup.ramp_time">10</stringProp>
        <longProp name="ThreadGroup.start_time">1</longProp>
        <longProp name="ThreadGroup.end_time">1</longProp>
        <boolProp name="ThreadGroup.scheduler">true</boolProp>
        <stringProp name="ThreadGroup.duration">$DURATION</stringProp>
        <stringProp name="ThreadGroup.delay"></stringProp>
        <boolProp name="ThreadGroup.same_user_on_next_iteration">true</boolProp>
      </ThreadGroup>
      <hashTree>
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="Warmup Request" enabled="true">
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments" guiclass="HTTPArgumentsPanel" testclass="Arguments" testname="User Defined Variables" enabled="true">
            <collectionProp name="Arguments.arguments"/>
          </elementProp>
          <stringProp name="HTTPSampler.domain">localhost</stringProp>
          <stringProp name="HTTPSampler.port">$PORT</stringProp>
          <stringProp name="HTTPSampler.protocol">http</stringProp>
          <stringProp name="HTTPSampler.contentEncoding"></stringProp>
          <stringProp name="HTTPSampler.path">/graphql</stringProp>
          <stringProp name="HTTPSampler.method">POST</stringProp>
          <boolProp name="HTTPSampler.follow_redirects">true</boolProp>
          <boolProp name="HTTPSampler.auto_redirects">false</boolProp>
          <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
          <boolProp name="HTTPSampler.DO_MULTIPART_POST">false</boolProp>
          <stringProp name="HTTPSampler.embedded_url_re"></stringProp>
          <stringProp name="HTTPSampler.connect_timeout"></stringProp>
          <stringProp name="HTTPSampler.response_timeout"></stringProp>
        </HTTPSamplerProxy>
        <hashTree>
          <HeaderManager guiclass="HeaderPanel" testclass="HeaderManager" testname="HTTP Header Manager" enabled="true">
            <collectionProp name="HeaderManager.headers">
              <elementProp name="" elementType="Header">
                <stringProp name="Header.name">Content-Type</stringProp>
                <stringProp name="Header.value">application/json</stringProp>
              </elementProp>
            </collectionProp>
          </HeaderManager>
          <hashTree/>
        </hashTree>
        <hashTree>
          <JSR223PostProcessor guiclass="TestBeanGUI" testclass="JSR223PostProcessor" testname="GraphQL Payload Generator" enabled="true">
            <stringProp name="cacheKey">true</stringProp>
            <stringProp name="filename"></stringProp>
            <stringProp name="parameters"></stringProp>
            <stringProp name="script">import groovy.json.JsonBuilder

// Simple warmup queries
def queries = [
    '{"query": "{ ping }"}',
    '{"query": "{ users(limit: 5) { id username } }"}',
    '{"query": "{ posts(limit: 3) { id title } }"}'
]

def random = new Random()
vars.put('graphql_payload', queries[random.nextInt(queries.size())])
</stringProp>
            <stringProp name="scriptLanguage">groovy</stringProp>
          </JSR223PostProcessor>
          <hashTree/>
        </hashTree>
        <hashTree>
          <BodyDataSampler guiclass="TestBeanGUI" testclass="BodyDataSampler" testname="GraphQL Body Data" enabled="true">
            <stringProp name="BodyDataSampler.bodyData">\${graphql_payload}</stringProp>
          </BodyDataSampler>
          <hashTree/>
        </hashTree>
      </hashTree>
    </hashTree>
  </hashTree>
</jmeterTestPlan>
EOF

# Run warmup test
echo "⏳ Running warmup test..."
jmeter -n \
    -t "$WARMUP_PLAN" \
    -l "$RESULTS_FILE" \
    -Jthreads="$CONCURRENT_USERS" \
    -Jduration="$DURATION"

# Check results
if [ -f "$RESULTS_FILE" ]; then
    SUCCESS_COUNT=$(grep -c "true" "$RESULTS_FILE" 2>/dev/null || echo "0")
    TOTAL_COUNT=$(wc -l < "$RESULTS_FILE")
    SUCCESS_RATE=$((SUCCESS_COUNT * 100 / TOTAL_COUNT))

    echo "✅ Warmup completed"
    echo "   Requests: $TOTAL_COUNT"
    echo "   Success Rate: ${SUCCESS_RATE}%"
else
    echo "❌ Warmup failed - no results generated"
    exit 1
fi

# Cleanup
rm -f "$WARMUP_PLAN" "$RESULTS_FILE"

echo "🔥 $FRAMEWORK warmup phase completed successfully"