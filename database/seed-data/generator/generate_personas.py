#!/usr/bin/env python
"""
Generate diverse personas for blog comment generation.

Creates ~2000 unique personas with:
- Name and background
- Expertise areas
- Communication style
- Topics they like to comment on
- Typical comment patterns
- Strict JSON schema validation (Trinity Pattern: pk_user + id UUID)
- Individual persona files with optional resume capability

Usage:
    python generate_personas.py --count 2000
    python generate_personas.py --count 100 --dry-run
    python generate_personas.py --resume  (continue from latest ID)
    python generate_personas.py --count 2000 --resume
"""

import argparse
import json
import random
import sys
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

import requests
import yaml
from jsonschema import Draft7Validator, ValidationError

from logger_config import setup_logging
from .exceptions import VLLMTimeoutError, VLLMConnectionError, VLLMError

# ============================================================================
# Configuration
# ============================================================================

VLLM_URL = "http://localhost:8000/v1/chat/completions"
MODEL_ID = "/data/models/fp16/Ministral-3-8B-Instruct-2512"
MAX_TOKENS = 800
TEMPERATURE = 0.3  # Lower for structured output (JSON/YAML)
TOP_P = 0.9

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR.parent / "output" / "personas"

# Topic domains for variety
TOPIC_DOMAINS = [
    "database design",
    "API architecture",
    "security",
    "performance optimization",
    "deployment strategies",
    "testing practices",
    "code patterns",
    "DevOps",
    "cloud infrastructure",
    "frontend development",
    "backend development",
    "distributed systems",
    "data structures",
    "caching strategies",
    "monitoring",
    "team dynamics",
]

PROFESSIONAL_TITLES = [
    # Backend & Core Engineering
    "Senior Backend Engineer",
    "Backend Software Engineer",
    "Distributed Systems Engineer",
    "Database Architect",
    "Database Administrator",
    "Systems Engineer",
    "Core Platform Engineer",

    # Frontend & Full Stack
    "Frontend Engineer",
    "Senior Frontend Engineer",
    "Full Stack Developer",
    "React Specialist",
    "TypeScript Specialist",

    # DevOps & Infrastructure
    "DevOps Engineer",
    "Senior DevOps Engineer",
    "Platform Engineer",
    "Infrastructure Engineer",
    "Cloud Architect",
    "Site Reliability Engineer",
    "Infrastructure Architect",

    # Data & Analytics
    "Data Engineer",
    "Senior Data Engineer",
    "Data Scientist",
    "Analytics Engineer",
    "Machine Learning Engineer",
    "ML/AI Specialist",
    "Big Data Engineer",

    # Security
    "Security Engineer",
    "Application Security Engineer",
    "Infrastructure Security Engineer",
    "Security Architect",
    "Incident Response Engineer",

    # Leadership & Architecture
    "Software Architect",
    "Solutions Architect",
    "Tech Lead",
    "Engineering Manager",
    "Staff Engineer",
    "Principal Engineer",
    "VP Engineering",
    "Engineering Director",

    # Quality & Reliability
    "Quality Assurance Engineer",
    "QA Automation Engineer",
    "Test Automation Engineer",
    "Performance Engineer",
    "Reliability Engineer",

    # Other Specializations
    "Mobile Engineer",
    "iOS Engineer",
    "Android Engineer",
    "Graphics Engineer",
    "Game Developer",
    "Embedded Systems Engineer",
    "Firmware Engineer",
    "Network Engineer",
    "Database Specialist",
    "Search Infrastructure Engineer",
    "Build Systems Engineer",
    "Compilers Engineer",
]

# Communication/Reply styles
REPLY_STYLES = [
    "direct and concise",
    "friendly and encouraging",
    "questioning and exploratory",
    "analytical and detailed",
    "supportive and collaborative",
    "technical and precise",
    "pragmatic and solution-focused",
    "experienced and wise",
    "enthusiastic and energetic",
    "cautious and thorough",
]

# Gender-neutral names for diversity
FIRST_NAMES = [
    "Alex", "Jordan", "Casey", "Morgan", "Riley", "Taylor", "Madison", "Quinn",
    "Adrian", "Cameron", "Blake", "Drew", "Evan", "Jamie", "Logan", "Reese",
    "Skylar", "Charlie", "Avery", "Sydney", "Casey", "Dakota", "River", "Phoenix",
    "Sam", "Bailey", "Emerson", "Finley", "Harper", "Parker", "Scout", "Tatum",
]

LAST_NAMES = [
    "Anderson", "Bennett", "Brooks", "Campbell", "Chen", "Cohen", "Davis", "Drake",
    "Edwards", "Foster", "Garcia", "Greene", "Hansen", "Harris", "Jackson", "James",
    "Johnson", "Jones", "Khan", "Kim", "Klein", "Kumar", "Lee", "Lewis",
    "Martinez", "Miller", "Moore", "Murphy", "Nelson", "O'Brien", "Parker", "Patel",
    "Peterson", "Phillips", "Quinn", "Ramirez", "Roberts", "Robinson", "Rogers", "Ross",
    "Santos", "Scott", "Shah", "Shaw", "Smith", "Stevens", "Stewart", "Sullivan",
    "Taylor", "Thompson", "Torres", "Turner", "Vargas", "Wagner", "Walker", "Walsh",
    "Wang", "Warren", "Washington", "Watson", "Webb", "Weber", "Webster", "Wheeler",
    "White", "Williams", "Wilson", "Wright", "Wu", "Yang", "Young", "Zhang",
]

# Experience levels with year ranges
EXPERIENCE_LEVELS = [
    ("Junior", 0, 3),      # Junior: 0-3 years
    ("Mid-level", 3, 7),   # Mid-level: 3-7 years
    ("Senior", 7, 12),     # Senior: 7-12 years
    ("Staff", 12, 20),     # Staff: 12-20 years
    ("Principal", 20, 30), # Principal: 20+ years
]

# Company types/sizes
COMPANY_TYPES = [
    "Fortune 500 corporation",
    "large tech company (1000+ employees)",
    "mid-size company (100-1000 employees)",
    "startup (20-100 employees)",
    "early-stage startup (5-20 employees)",
    "open source project",
    "bootstrapped company",
    "consulting firm",
]

# Business domain/vertical focus
BUSINESS_DOMAINS = [
    # Finance & Banking
    "financial services and banking",
    "cryptocurrency and blockchain",
    "fintech and payment processing",
    "insurance technology",

    # Healthcare & Life Sciences
    "healthcare and medical technology",
    "pharmaceutical research and development",
    "telemedicine and health monitoring",
    "medical device manufacturing",

    # Retail & Commerce
    "e-commerce and retail",
    "supply chain and logistics",
    "inventory management systems",
    "point of sale systems",

    # Communications & Media
    "social media and communications",
    "video streaming and content delivery",
    "advertising and marketing technology",
    "messaging and collaboration tools",

    # Infrastructure & Cloud
    "cloud infrastructure and platforms",
    "containerization and orchestration",
    "serverless computing",
    "content delivery networks",

    # Security & Compliance
    "cybersecurity and compliance",
    "identity and access management",
    "threat detection and response",
    "data privacy and GDPR",

    # Data & Analytics
    "data science and analytics",
    "business intelligence and reporting",
    "machine learning and AI",
    "real-time data processing",

    # Enterprise & B2B
    "enterprise resource planning (ERP)",
    "customer relationship management (CRM)",
    "human resources technology",
    "accounting and finance software",

    # Developer Tools
    "version control and collaboration",
    "CI/CD and automation",
    "monitoring and observability",
    "API management and integration",

    # Consumer & Mobile
    "consumer mobile applications",
    "mobile game development",
    "fitness and wellness apps",
    "travel and hospitality apps",

    # Hardware & Embedded
    "IoT and embedded systems",
    "robotics and automation",
    "autonomous vehicles",
    "smart home technology",

    # Media & Entertainment
    "gaming and entertainment",
    "music streaming and distribution",
    "podcast and audio production",
    "augmented and virtual reality",

    # Education & Training
    "education technology (EdTech)",
    "online learning platforms",
    "corporate training systems",
    "skill assessment platforms",

    # Other Domains
    "legal technology and compliance",
    "real estate and property management",
    "energy and utilities",
    "manufacturing and industrial IoT",
    "agriculture and agritech",
    "transportation and logistics",
    "restaurant and food service technology",
]

# Geographic regions (affects communication style, timezone awareness, etc.)
GEOGRAPHIC_REGIONS = [
    "United States (West Coast)",
    "United States (East Coast)",
    "United States (Central/Mountain)",
    "Canada",
    "United Kingdom",
    "Western Europe (Germany, France, Netherlands, etc.)",
    "Eastern Europe (Poland, Czech Republic, etc.)",
    "Nordics (Sweden, Norway, Denmark, Finland)",
    "Southern Europe (Spain, Italy, Portugal)",
    "India",
    "Singapore and Southeast Asia",
    "China",
    "Japan and South Korea",
    "Australia and New Zealand",
    "Latin America (Brazil, Mexico, etc.)",
    "Middle East (UAE, Saudi Arabia, etc.)",
]

# Language backgrounds mapped by geographic region
# Maps region to appropriate language backgrounds with (language_description, is_native_english)
LANGUAGE_BACKGROUNDS_BY_REGION = {
    "United States (West Coast)": [
        ("Native English speaker", True),
        ("Bilingual English/Spanish", False),
        ("Bilingual English/Mandarin", False),
    ],
    "United States (East Coast)": [
        ("Native English speaker", True),
        ("Bilingual English/Spanish", False),
        ("Bilingual English/Hindi", False),
    ],
    "United States (Central/Mountain)": [
        ("Native English speaker", True),
        ("Bilingual English/Spanish", False),
    ],
    "Canada": [
        ("Native English speaker", True),
        ("Bilingual English/French", False),
    ],
    "United Kingdom": [
        ("Native English speaker", True),
        ("Bilingual English/Polish", False),
    ],
    "Western Europe (Germany, France, Netherlands, etc.)": [
        ("Native speaker of regional language, fluent English", False),
        ("Bilingual English/German", False),
        ("Bilingual English/French", False),
        ("Bilingual English/Dutch", False),
    ],
    "Eastern Europe (Poland, Czech Republic, etc.)": [
        ("Native speaker of regional language, fluent English", False),
        ("Bilingual English/Polish", False),
        ("Bilingual English/Czech", False),
        ("Bilingual English/Russian", False),
    ],
    "Nordics (Sweden, Norway, Denmark, Finland)": [
        ("Native speaker of Nordic language, fluent English", False),
        ("Bilingual English/Swedish", False),
        ("Bilingual English/Norwegian", False),
        ("Bilingual English/Danish", False),
        ("Bilingual English/Finnish", False),
    ],
    "Southern Europe (Spain, Italy, Portugal)": [
        ("Native speaker of regional language, fluent English", False),
        ("Bilingual English/Spanish", False),
        ("Bilingual English/Italian", False),
        ("Bilingual English/Portuguese", False),
    ],
    "India": [
        ("Native speaker of Indian language, fluent English", False),
        ("Bilingual English/Hindi", False),
        ("Bilingual English/Tamil", False),
        ("Bilingual English/Telugu", False),
    ],
    "Singapore and Southeast Asia": [
        ("Native speaker of regional language, fluent English", False),
        ("Bilingual English/Mandarin", False),
        ("Bilingual English/Malay", False),
        ("Bilingual English/Vietnamese", False),
        ("Bilingual English/Thai", False),
    ],
    "China": [
        ("Native Mandarin speaker, fluent English", False),
        ("Bilingual English/Mandarin", False),
    ],
    "Japan and South Korea": [
        ("Native speaker of East Asian language, fluent English", False),
        ("Bilingual English/Japanese", False),
        ("Bilingual English/Korean", False),
    ],
    "Australia and New Zealand": [
        ("Native English speaker", True),
    ],
    "Latin America (Brazil, Mexico, etc.)": [
        ("Native speaker of regional language, fluent English", False),
        ("Bilingual English/Spanish", False),
        ("Bilingual English/Portuguese", False),
    ],
    "Middle East (UAE, Saudi Arabia, etc.)": [
        ("Native speaker of Arabic, fluent English", False),
        ("Bilingual English/Arabic", False),
    ],
}


# ============================================================================
# Persona Generator
# ============================================================================


class PersonaGenerator:
    """Generates diverse personas for comment generation."""

    def __init__(self, output_dir: Path = OUTPUT_DIR) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.generated_count = 0
        self.failed_count = 0
        self.start_time = time.time()

        # Load and cache schema for validation
        schema_file = SCRIPT_DIR / "persona_schema.json"
        with open(schema_file) as f:
            self.schema = json.load(f)
        self.validator = Draft7Validator(self.schema)

    def find_latest_persona_id(self) -> int:
        """Find the highest persona ID already generated."""
        personas_dir = self.output_dir / "personas"
        if not personas_dir.exists():
            return 0

        max_id = 0
        try:
            # Look for individual persona files: persona_000001.json, persona_000002.json, etc.
            for persona_file in personas_dir.glob("persona_*.json"):
                # Extract ID from filename: persona_000123.json -> 123
                try:
                    file_id = int(persona_file.stem.split("_")[1])
                    max_id = max(max_id, file_id)
                except (ValueError, IndexError):
                    pass
        except Exception as e:
            print(f"Warning: Error scanning personas directory: {e}")

        return max_id

    def _generate_field(self, field_name: str, field_description: str) -> str:
        """Generate a single field using vLLM.

        Args:
            field_name: Name of the field
            field_description: Description of what to generate

        Returns:
            Generated field value as string
        """
        system_prompt = "You are a data generator. Respond with ONLY the requested value. No explanations, no markdown, no extra text."
        prompt = f"{field_description}\n\nRespond with ONLY the value:"

        try:
            response = self._call_vllm(prompt, system_prompt)
            if response:
                return response.strip()
        except Exception:
            pass

        return ""

    def generate_single_persona(self, persona_id: int, dry_run: bool = False) -> Optional[Dict]:
        """Generate a single persona by requesting individual fields and assembling them.

        Args:
            persona_id: ID for the persona
            dry_run: Use dummy generation without vLLM
        """
        if dry_run:
            return self._create_dummy_persona(persona_id)

        # ===== SELECT PERSONA DIMENSIONS =====
        # These are selected once per persona to ensure consistency
        topics = random.sample(TOPIC_DOMAINS, k=random.randint(2, 4))
        topics_str = ", ".join(topics)

        # Select experience level and corresponding year range
        exp_level, exp_min, exp_max = random.choice(EXPERIENCE_LEVELS)
        years_exp_range = random.randint(exp_min, exp_max)

        # Select other dimensions
        reply_style = random.choice(REPLY_STYLES)
        company_type = random.choice(COMPANY_TYPES)
        business_domain = random.choice(BUSINESS_DOMAINS)
        geographic_region = random.choice(GEOGRAPHIC_REGIONS)
        # Select language background appropriate for the region
        lang_bg, is_native = random.choice(LANGUAGE_BACKGROUNDS_BY_REGION[geographic_region])

        try:
            # Generate each field individually with explicit constraints
            # Name generation includes geographic/cultural context
            name = self._generate_field("name", f"Generate a realistic full name for a {geographic_region} person. Respond with ONLY the name, nothing else. Example: Alice Johnson")

            # Title selection from available list
            selected_titles = random.sample(PROFESSIONAL_TITLES, min(15, len(PROFESSIONAL_TITLES)))
            titles_str = ", ".join(selected_titles)
            title = self._generate_field("title", f"Respond with ONLY one title from this list: {titles_str}")

            # Years of experience with appropriate range for their level
            years_exp = self._generate_field("years_experience", f"Respond with ONLY a single number between {exp_min} and {exp_max}. Example: {years_exp_range}")

            # Background includes company context and domain
            background = self._generate_field("background", f"Respond with 1-2 sentences about technical career working in {business_domain} at a {company_type}. No extra text.")

            # Expertise in selected topics
            expertise = self._generate_field("expertise_areas", f"Respond with ONLY 2-3 items from this list, separated by commas: {topics_str}. No other text.")

            # Communication style that matches reply style
            comm_style = self._generate_field("communication_style", f"Respond with 1-2 sentences describing a {reply_style} communication style. No extra text.")

            # Personality traits
            traits = self._generate_field("personality_traits", "Respond with ONLY 2-3 traits separated by commas. Example: pragmatic, detail-oriented, collaborative")

            # Preferred comment types
            comment_types = self._generate_field("preferred_comment_types", "Respond with ONLY 1-2 values separated by commas. Choose from: technical_issue, missing_edge_case, question, tradeoff, validation, critical_analysis, experience_sharing")

            # Example phrases - adjust for language background
            if is_native:
                phrases_prompt = "Respond with ONLY 2-3 short phrases separated by commas. Example: In my experience..., I've seen this..."
            else:
                phrases_prompt = "Respond with ONLY 2-3 short phrases (slightly formal, precise) separated by commas. Example: Based on my experience..., From what I've observed..."
            phrases = self._generate_field("example_phrases", phrases_prompt)

            # Interests in selected topics
            interests = self._generate_field("interests", f"Respond with ONLY 2-3 items from this list separated by commas: {topics_str}. No other text.")

            # Validate essential fields
            if not all([name, title, background]):
                return None

            # Parse years_experience
            try:
                years_exp_int = int(years_exp.split()[0]) if years_exp else 5
            except (ValueError, IndexError):
                years_exp_int = 5

            # Parse list fields (comma-separated)
            def parse_list(value: str, max_items: int = 3) -> list:
                if not value:
                    return []
                return [x.strip() for x in value.split(",") if x.strip()][:max_items]

            # Debug: Print raw field values
            if False:  # Set to True to debug
                print(f"\n  DEBUG - Raw fields:")
                print(f"    name: {repr(name)}")
                print(f"    title: {repr(title)}")
                print(f"    comment_types: {repr(comment_types)}")
                print(f"    traits: {repr(traits)}")
                print(f"    expertise: {repr(expertise)}")

            # Assemble into persona dict
            persona = {
                # Core fields
                "name": name,
                "title": title,
                "years_experience": years_exp_int,
                "background": background,
                "expertise_areas": parse_list(expertise, 3),
                "communication_style": comm_style,
                "personality_traits": parse_list(traits, 3),
                "preferred_comment_types": parse_list(comment_types, 2),
                "example_phrases": parse_list(phrases, 3),
                "interests": parse_list(interests, 3),

                # Persona dimensions (for diversity and realism)
                "reply_style": reply_style,
                "experience_level": exp_level,
                "company_type": company_type,
                "business_domain": business_domain,
                "geographic_region": geographic_region,
                "language_background": lang_bg,
            }

            # Add Trinity Pattern fields
            persona["pk_user"] = persona_id
            persona["id"] = str(uuid.uuid4())
            persona["generated_at"] = time.time()

            # Validate against schema
            self._validate_persona(persona, persona_id)
            return persona

        except (ValidationError, ValueError) as e:
            # Validation or assembly failed
            print(f"\n  Validation error: {e}")
            return None
        except Exception as e:
            # Unexpected error
            print(f"\n  Unexpected error: {e}")
            return None

    def _create_dummy_persona(self, persona_id: int) -> Dict:
        """Create a dummy persona for dry-run mode."""
        roles = [
            "Senior Backend Engineer",
            "DevOps Engineer",
            "Security Engineer",
            "Database Architect",
            "Tech Lead",
            "Software Architect",
            "Performance Engineer",
            "Distributed Systems Expert",
        ]
        names = [
            f"Alex{persona_id}",
            f"Jordan{persona_id}",
            f"Casey{persona_id}",
            f"Morgan{persona_id}",
            f"Taylor{persona_id}",
        ]

        return {
            "pk_user": persona_id,
            "id": str(uuid.uuid4()),
            "name": random.choice(names),
            "title": random.choice(roles),
            "years_experience": random.randint(3, 20),
            "background": "Experienced technical professional",
            "expertise_areas": random.sample(TOPIC_DOMAINS, random.randint(2, 3)),
            "communication_style": "direct and technical",
            "personality_traits": ["pragmatic", "detail-oriented"],
            "preferred_comment_types": ["critical_analysis", "experience_sharing"],
            "example_phrases": ["In my experience...", "I've seen this..."],
            "interests": random.sample(TOPIC_DOMAINS, random.randint(2, 3)),
            "generated_at": time.time(),
        }

    def generate_batch(
        self,
        count: int = 2000,
        dry_run: bool = False,
        resume: bool = False,
    ) -> Dict:
        """Generate multiple personas.

        Args:
            count: Number of personas to generate. When not resuming, this is the total count.
                   When resuming, this is the number of ADDITIONAL personas to generate.
            dry_run: Use dummy generation
            resume: Continue from latest persona ID
        """
        start_id = 1
        end_id = count

        # If resuming, find the latest ID and continue from there
        if resume:
            latest_id = self.find_latest_persona_id()
            if latest_id > 0:
                start_id = latest_id + 1
                end_id = latest_id + count  # count is now the number of ADDITIONAL personas
                print(f"\n{'='*70}")
                print(f"RESUMING PERSONA GENERATION")
                print(f"{'='*70}")
                print(f"Found {latest_id} existing personas")
                print(f"Resuming from persona ID: {start_id}")
                print(f"Generating {count} additional personas (ID range: {start_id}-{end_id})")
                print(f"{'='*70}\n")

        results = {
            "generated": 0,
            "failed": 0,
            "duration": 0,
            "resumed_from": start_id - 1,
        }

        print(f"\n{'='*70}")
        print(f"PERSONA GENERATION")
        print(f"{'='*70}")
        print(f"Target personas: {end_id}")
        print(f"Starting from: {start_id}")
        print(f"Dry run: {dry_run}")
        print(f"{'='*70}\n")

        personas = []

        for i in range(start_id, end_id + 1):
            print(f"[{i:5d}/{end_id:5d}] Generating persona", end="", flush=True)

            persona = self.generate_single_persona(i, dry_run=dry_run)

            if persona:
                personas.append(persona)
                results["generated"] += 1
                print(f" ✓ ({persona.get('title', 'Unknown')})")
            else:
                results["failed"] += 1
                print(f" ✗")

            # Checkpoint every 100 personas
            if i % 100 == 0:
                elapsed = time.time() - self.start_time
                rate = i / elapsed
                remaining = (end_id - i) / rate if rate > 0 else 0
                self._save_personas(personas)
                print(f"  ✓ Saved {len(personas)} personas ({rate:.1f} personas/sec, ~{remaining/60:.0f}min remaining)\n")

        # Save final batch
        self._save_personas(personas)

        results["duration"] = time.time() - self.start_time

        # Print summary
        print(f"\n{'='*70}")
        print("SUMMARY")
        print(f"{'='*70}")
        print(f"Generated:       {results['generated']:,}")
        print(f"Failed:          {results['failed']:,}")
        print(f"Duration:        {results['duration']/60:.1f} min")
        if results["generated"] > 0:
            print(f"Throughput:      {results['generated']/results['duration']:.1f} personas/sec")
        print(f"Output file:     {self.output_dir / 'personas.json'}")
        print(f"{'='*70}\n")

        return results

    def _validate_persona(self, persona: Dict, persona_id: int) -> None:
        """Validate persona against schema. Raises ValidationError if invalid."""
        try:
            self.validator.validate(persona)
        except ValidationError as e:
            raise ValidationError(f"Invalid persona {persona_id}: {e.message}")

    def _save_personas(self, personas: list[dict]) -> None:
        """Save personas to individual JSON files and create index."""
        # Create personas subdirectory
        personas_dir = self.output_dir / "personas"
        personas_dir.mkdir(parents=True, exist_ok=True)

        # Save each persona to individual file
        for persona in personas:
            persona_id = persona.get("pk_user")
            if persona_id:
                file_path = personas_dir / f"persona_{persona_id:06d}.json"
                with open(file_path, "w") as f:
                    json.dump(persona, f, indent=2)

        # Create index file for convenient bulk loading
        index_file = personas_dir / "index.json"
        index_data = {
            "count": len(personas),
            "generated_at": time.time(),
            "personas": [
                {"pk_user": p.get("pk_user"), "id": p.get("id"), "name": p.get("name")}
                for p in personas
            ],
        }
        with open(index_file, "w") as f:
            json.dump(index_data, f, indent=2)

        # Also save legacy single file format for backwards compatibility
        legacy_file = self.output_dir / "personas.json"
        with open(legacy_file, "w") as f:
            json.dump(
                {
                    "count": len(personas),
                    "generated_at": time.time(),
                    "personas": personas,
                },
                f,
                indent=2,
            )

    def _extract_structured_from_response(self, response: str) -> Optional[Dict]:
        """Extract structured data (JSON or YAML) from response and return as dict."""
        if not response:
            return None

        response = response.strip()

        # Try 1: Direct JSON parse
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try 2: Direct YAML parse
        try:
            result = yaml.safe_load(response)
            if isinstance(result, dict):
                return result
        except yaml.YAMLError:
            pass

        # Try 3: Extract from ```json ... ``` or ```yaml ... ```
        for marker in ["```json", "```yaml", "```"]:
            try:
                if marker in response:
                    start = response.find(marker) + len(marker)
                    end = response.find("```", start)
                    if end > start:
                        extracted = response[start:end].strip()
                        # Try JSON first
                        try:
                            return json.loads(extracted)
                        except json.JSONDecodeError:
                            # Try YAML
                            result = yaml.safe_load(extracted)
                            if isinstance(result, dict):
                                return result
            except (json.JSONDecodeError, yaml.YAMLError):
                pass

        # Try 4: Extract lines that look like YAML (key: value)
        try:
            # Find first line that looks like YAML
            lines = response.split("\n")
            yaml_start = 0
            for i, line in enumerate(lines):
                if ":" in line and not line.strip().startswith("#"):
                    yaml_start = i
                    break

            if yaml_start < len(lines):
                yaml_content = "\n".join(lines[yaml_start:])
                result = yaml.safe_load(yaml_content)
                if isinstance(result, dict):
                    return result
        except yaml.YAMLError:
            pass

        return None

    def _call_vllm(self, prompt: str, system_prompt: str) -> Optional[str]:
        """Call vLLM API."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        payload = {
            "model": MODEL_ID,
            "messages": messages,
            "max_tokens": MAX_TOKENS,
            "temperature": TEMPERATURE,
            "top_p": TOP_P,
        }

        try:
            response = requests.post(VLLM_URL, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()

            if result.get("choices"):
                return result["choices"][0]["message"]["content"].strip()

        except requests.exceptions.Timeout:
            raise VLLMTimeoutError("Request timed out after 60s") from None
        except requests.exceptions.ConnectionError:
            raise VLLMConnectionError("Cannot connect to vLLM server at localhost:8000") from None
        except Exception as e:
            raise VLLMError(f"vLLM error: {e}") from e

        return None

    def analyze_personas(self, personas_file: Path) -> None:
        """Analyze generated personas."""
        with open(personas_file) as f:
            data = json.load(f)

        personas = data.get("personas", [])

        print(f"\n{'='*70}")
        print("PERSONA ANALYSIS")
        print(f"{'='*70}")
        print(f"Total personas: {len(personas)}")

        if not personas:
            return

        # Analyze expertise areas
        all_areas = []
        for persona in personas:
            all_areas.extend(persona.get("expertise_areas", []))

        area_counts = {}
        for area in all_areas:
            area_counts[area] = area_counts.get(area, 0) + 1

        print(f"\nTop expertise areas:")
        for area, count in sorted(area_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            pct = 100 * count / len(personas)
            print(f"  {area:30s}: {count:4d} personas ({pct:5.1f}%)")

        # Analyze communication styles
        styles = {}
        for persona in personas:
            style = persona.get("communication_style", "unknown")
            styles[style] = styles.get(style, 0) + 1

        print(f"\nCommunication styles:")
        for style, count in sorted(styles.items(), key=lambda x: x[1], reverse=True)[:5]:
            pct = 100 * count / len(personas)
            print(f"  {style:30s}: {count:4d} personas ({pct:5.1f}%)")

        # Analyze experience levels
        experiences = [p.get("years_experience", 0) for p in personas]
        avg_exp = sum(experiences) / len(experiences) if experiences else 0

        print(f"\nExperience levels:")
        print(f"  Average:  {avg_exp:.1f} years")
        print(f"  Min:      {min(experiences)} years")
        print(f"  Max:      {max(experiences)} years")

        # Sample personas
        print(f"\nSample personas:")
        for persona in personas[:3]:
            print(f"\n  {persona['name']} ({persona['title']})")
            print(f"    Experience: {persona['years_experience']} years")
            print(f"    Expertise: {', '.join(persona.get('expertise_areas', [])[:2])}")
            print(f"    Style: {persona.get('communication_style', 'unknown')}")

        print(f"\n{'='*70}\n")


# ============================================================================
# CLI
# ============================================================================


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate personas for comment generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate 2000 personas (full run)
  python generate_personas.py --count 2000

  # Generate 100 personas (test)
  python generate_personas.py --count 100

  # Dry run (no vLLM calls)
  python generate_personas.py --count 50 --dry-run

  # Analyze existing personas
  python generate_personas.py --analyze personas.json
        """,
    )

    parser.add_argument(
        "--count",
        type=int,
        default=2000,
        help="Number of personas to generate (default: 2000)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate dummy personas without calling vLLM",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DIR,
        help="Output directory for personas",
    )

    parser.add_argument(
        "--analyze",
        type=Path,
        help="Analyze existing personas file",
    )

    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from the latest generated persona ID (auto-detects highest pk_user)",
    )

    args = parser.parse_args()

    # Set up structured logging
    logger = setup_logging(__name__)
    logger.info("Starting persona generation")

    # Handle analysis mode
    if args.analyze:
        generator = PersonaGenerator(output_dir=args.output)
        generator.analyze_personas(args.analyze)
        return

    # Check vLLM is running (unless dry run)
    if not args.dry_run:
        try:
            response = requests.get("http://localhost:8000/v1/models", timeout=5)
            response.raise_for_status()
            logger.info("vLLM server is running")
        except (requests.RequestException, requests.Timeout) as e:
            logger.error("vLLM server not running at localhost:8000")
            logger.error(f"Details: {e}")
            logger.info("Start it with: vllm-switch implementer")
            sys.exit(1)

    # Generate personas
    generator = PersonaGenerator(output_dir=args.output)
    results = generator.generate_batch(count=args.count, dry_run=args.dry_run, resume=args.resume)

    sys.exit(0 if results["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
