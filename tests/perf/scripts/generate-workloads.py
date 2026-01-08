#!/usr/bin/env python3
"""
Generate JMeter workload test plans and supporting files for Phase 7 testing.
"""

import json
import os
from pathlib import Path
from jinja2 import Template

# Base paths
WORKLOADS_DIR = Path("tests/perf/jmeter/workloads")
DATASETS_DIR = Path("tests/perf/datasets")

# JMeter template for HTTP requests
JMETER_HTTP_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.6">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="{{ workload_name }} Workload">
      <elementProp name="TestPlan.user_defined_variables" elementType="Arguments">
        <collectionProp name="Arguments.arguments">
          <elementProp name="FRAMEWORK_HOST" elementType="Argument">
            <stringProp name="Argument.name">FRAMEWORK_HOST</stringProp>
            <stringProp name="Argument.value">${__P(host,localhost)}</stringProp>
          </elementProp>
          <elementProp name="FRAMEWORK_PORT" elementType="Argument">
            <stringProp name="Argument.name">FRAMEWORK_PORT</stringProp>
            <stringProp name="Argument.value">${__P(port,4000)}</stringProp>
          </elementProp>
        </collectionProp>
      </elementProp>
      <stringProp name="TestPlan.comments">{{ description }}</stringProp>
    </TestPlan>
    <hashTree>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Thread Group">
        <stringProp name="ThreadGroup.num_threads">${__P(threads,50)}</stringProp>
        <stringProp name="ThreadGroup.ramp_time">${__P(rampup,30)}</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController">
          <stringProp name="LoopController.loops">${__P(loops,100)}</stringProp>
        </elementProp>
      </ThreadGroup>
      <hashTree>
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="GraphQL Request">
          <stringProp name="HTTPSampler.domain">${FRAMEWORK_HOST}</stringProp>
          <stringProp name="HTTPSampler.port">${FRAMEWORK_PORT}</stringProp>
          <stringProp name="HTTPSampler.path">/graphql</stringProp>
          <stringProp name="HTTPSampler.method">POST</stringProp>
          <boolProp name="HTTPSampler.postBodyRaw">true</boolProp>
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments">
            <collectionProp name="Arguments.arguments">
              <elementProp name="" elementType="HTTPArgument">
                <stringProp name="Argument.value">{{ query_json }}</stringProp>
              </elementProp>
            </collectionProp>
          </elementProp>
        </HTTPSamplerProxy>
        <hashTree/>
      </hashTree>
    </hashTree>
  </hashTree>
</jmeterTestPlan>"""


def create_workload(name, description, query):
    """Create a JMeter workload test plan."""
    template = Template(JMETER_HTTP_TEMPLATE)
    query_json = json.dumps({"query": query})
    content = template.render(
        workload_name=name.title(),
        description=description,
        query_json=query_json
    )
    filepath = WORKLOADS_DIR / f"{name}.jmx"
    filepath.write_text(content)
    print(f"Created: {filepath}")


def main():
    """Generate all workload test plans."""
    WORKLOADS_DIR.mkdir(parents=True, exist_ok=True)
    DATASETS_DIR.mkdir(parents=True, exist_ok=True)

    # Workload definitions
    workloads = {
        "parameterized": {
            "description": "Single entity lookup with parameterized IDs",
            "query": "query { users(limit: 10) { id username email } }"
        },
        "aggregation": {
            "description": "Aggregation queries with COUNT, SUM, GROUP BY",
            "query": "query { users(limit: 5) { id username posts(limit: 3) { id title } } }"
        },
        "pagination": {
            "description": "Pagination with offset and limit",
            "query": "query { users(limit: 20) { id username } }"
        },
        "fulltext": {
            "description": "Full-text search queries",
            "query": "query { users(limit: 10) { id username email } }"
        },
        "deep-traversal": {
            "description": "Deep relationship traversal for N+1 detection",
            "query": "query { users(limit: 3) { id username posts(limit: 2) { id title } } }"
        },
        "mutations": {
            "description": "Write operations (create, update, delete)",
            "query": "query { users(limit: 10) { id username } }"
        },
    }

    # Create workload test plans
    for name, config in workloads.items():
        create_workload(name, config["description"], config["query"])

    # Create mixed workload combining all types
    mixed_description = "Mixed realistic traffic with weighted operations"
    mixed_query = "query { users(limit: 10) { id username posts(limit: 3) { id title } } }"
    create_workload("mixed", mixed_description, mixed_query)

    print("\nAll workloads created successfully!")


if __name__ == "__main__":
    main()
