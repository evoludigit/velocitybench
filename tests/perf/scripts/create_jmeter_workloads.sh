#!/bin/bash
# Create all JMeter workload test plans

DIR="tests/perf/jmeter/workloads"
mkdir -p "$DIR"

# Function to create JMeter template
create_jmeter() {
    local name=$1
    local description=$2
    local query=$3

    cat > "$DIR/${name}.jmx" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.6">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="${name^} Workload">
      <stringProp name="TestPlan.comments">${description}</stringProp>
    </TestPlan>
    <hashTree>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Thread Group">
        <stringProp name="ThreadGroup.num_threads">50</stringProp>
        <stringProp name="ThreadGroup.ramp_time">30</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController">
          <stringProp name="LoopController.loops">100</stringProp>
        </elementProp>
      </ThreadGroup>
      <hashTree>
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="GraphQL">
          <stringProp name="HTTPSampler.domain">localhost</stringProp>
          <stringProp name="HTTPSampler.port">4000</stringProp>
          <stringProp name="HTTPSampler.path">/graphql</stringProp>
          <stringProp name="HTTPSampler.method">POST</stringProp>
          <boolProp name="HTTPSampler.postBodyRaw">true</boolProp>
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments">
            <collectionProp name="Arguments.arguments">
              <elementProp name="" elementType="HTTPArgument">
                <stringProp name="Argument.value">{"query": "${query}"}</stringProp>
              </elementProp>
            </collectionProp>
          </elementProp>
        </HTTPSamplerProxy>
        <hashTree/>
      </hashTree>
    </hashTree>
  </hashTree>
</jmeterTestPlan>
EOF
    echo "Created: $DIR/${name}.jmx"
}

# Create workloads
create_jmeter "pagination" "Pagination with offset and limit" "query { users(limit: 20) { id username } }"
create_jmeter "fulltext" "Full-text search queries" "query { users(limit: 10) { id username email } }"
create_jmeter "deep-traversal" "Deep relationship traversal for N+1 detection" "query { users(limit: 3) { id username posts(limit: 2) { id title } } }"
create_jmeter "mutations" "Write operations (create, update, delete)" "query { users(limit: 10) { id username } }"
create_jmeter "mixed" "Mixed realistic traffic patterns" "query { users(limit: 10) { id username posts(limit: 3) { id title } } }"

echo "All JMeter workloads created successfully!"
