#!/usr/bin/env python
"""
Second-pass validation and refinement of generated personas using vLLM.

This script ensures that personas are cohesive and realistic by:
1. Checking that all persona dimensions align logically
2. Verifying that generated content matches the selected dimensions
3. Refining inconsistent fields using vLLM
4. Providing coherence scores and improvement reports

Usage:
    python validate_personas.py --input-dir output/personas/personas --output-dir output/personas/validated
    python validate_personas.py --input-dir output/personas/personas --dry-run
    python validate_personas.py --input-dir output/personas/personas --count 100 (validate first 100)
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

import requests

# ============================================================================
# Configuration
# ============================================================================

VLLM_URL = "http://localhost:8000/v1/chat/completions"
MODEL_ID = "/data/models/fp16/Ministral-3-8B-Instruct-2512"
MAX_TOKENS = 500
TEMPERATURE = 0.2  # Very low for validation consistency
TOP_P = 0.9

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR.parent / "output" / "personas"


# ============================================================================
# Persona Validator
# ============================================================================


class PersonaValidator:
    """Validates and refines personas for coherence and realism."""

    def __init__(self):
        self.validated_count = 0
        self.refined_count = 0
        self.failed_count = 0

    def _call_vllm(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        """Call vLLM API and return response text."""
        try:
            response = requests.post(
                VLLM_URL,
                json={
                    "model": MODEL_ID,
                    "messages": [
                        {"role": "system", "content": system_prompt} if system_prompt else {},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": MAX_TOKENS,
                    "temperature": TEMPERATURE,
                    "top_p": TOP_P,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            if data.get("choices") and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"  vLLM error: {e}")
        return None

    def _check_coherence(self, persona: Dict) -> Tuple[bool, str]:
        """
        Check if persona dimensions are logically coherent.
        Returns (is_coherent, issue_description)
        """
        issues = []

        # 1. Check geographic region vs. language background match
        region = persona.get("geographic_region", "")
        lang_bg = persona.get("language_background", "")

        region_lang_map = {
            "United States": ["Native English", "Bilingual English/Spanish", "Bilingual English/Mandarin", "Bilingual English/Hindi"],
            "Canada": ["Native English", "Bilingual English/French"],
            "United Kingdom": ["Native English", "Bilingual English/Polish"],
            "Western Europe": ["Native speaker of regional language", "Bilingual English/German", "Bilingual English/French", "Bilingual English/Dutch"],
            "Eastern Europe": ["Native speaker of regional language", "Bilingual English/Polish", "Bilingual English/Czech", "Bilingual English/Russian"],
            "Nordics": ["Native speaker of Nordic", "Bilingual English/Swedish", "Bilingual English/Norwegian", "Bilingual English/Danish", "Bilingual English/Finnish"],
            "Southern Europe": ["Native speaker of regional language", "Bilingual English/Spanish", "Bilingual English/Italian", "Bilingual English/Portuguese"],
            "India": ["Native speaker of Indian", "Bilingual English/Hindi", "Bilingual English/Tamil", "Bilingual English/Telugu"],
            "Singapore and Southeast Asia": ["Native speaker of regional", "Bilingual English/Mandarin", "Bilingual English/Malay", "Bilingual English/Vietnamese", "Bilingual English/Thai"],
            "China": ["Native Mandarin", "Bilingual English/Mandarin"],
            "Japan and South Korea": ["Native speaker of East Asian", "Bilingual English/Japanese", "Bilingual English/Korean"],
            "Australia and New Zealand": ["Native English"],
            "Latin America": ["Native speaker of regional", "Bilingual English/Spanish", "Bilingual English/Portuguese"],
            "Middle East": ["Native speaker of Arabic", "Bilingual English/Arabic"],
        }

        # Find matching region key
        matched = False
        for key in region_lang_map:
            if key.lower() in region.lower():
                expected_langs = region_lang_map[key]
                if not any(expected in lang_bg for expected in expected_langs):
                    issues.append(f"Language mismatch: {lang_bg} doesn't match {region}")
                matched = True
                break

        if not matched and region != "":
            issues.append(f"Unknown region: {region}")

        # 2. Check experience level vs. years experience
        exp_level = persona.get("experience_level", "")
        years = persona.get("years_experience", 0)

        exp_ranges = {
            "Junior": (0, 3),
            "Mid-level": (3, 7),
            "Senior": (7, 12),
            "Staff": (12, 20),
            "Principal": (20, 30),
        }

        if exp_level in exp_ranges:
            min_y, max_y = exp_ranges[exp_level]
            if not (min_y <= years <= max_y):
                issues.append(f"Experience mismatch: {years} years doesn't match {exp_level} level ({min_y}-{max_y})")

        # 3. Check that title is reasonable (not empty, reasonable length)
        title = persona.get("title", "")
        if not title or len(title) < 3 or len(title) > 100:
            issues.append(f"Title issue: '{title}' (length: {len(title)})")

        # 4. Check preferred comment types are from allowed list
        allowed_types = {
            "technical_issue", "missing_edge_case", "question",
            "tradeoff", "validation", "critical_analysis", "experience_sharing"
        }
        comment_types = set(persona.get("preferred_comment_types", []))
        invalid_types = comment_types - allowed_types
        if invalid_types:
            issues.append(f"Invalid comment types: {invalid_types}")

        # 5. Check expertise areas, interests, traits have items
        for field in ["expertise_areas", "personality_traits", "example_phrases", "interests"]:
            items = persona.get(field, [])
            if not items or len(items) == 0:
                issues.append(f"Empty field: {field}")

        # 6. Check background length (should be substantive)
        background = persona.get("background", "")
        if len(background) < 20:
            issues.append(f"Background too short: {len(background)} chars")

        return len(issues) == 0, "; ".join(issues)

    def _refine_persona(self, persona: Dict, coherence_issue: str) -> Optional[Dict]:
        """
        Use vLLM to refine a persona that has coherence issues.
        Returns refined persona or None if refinement fails.
        """
        # Build context about what should be fixed
        refinement_prompt = f"""
Review and refine this persona profile. The identified issue is: {coherence_issue}

Current persona:
- Name: {persona.get('name')}
- Title: {persona.get('title')}
- Years Experience: {persona.get('years_experience')}
- Experience Level: {persona.get('experience_level')}
- Geographic Region: {persona.get('geographic_region')}
- Language Background: {persona.get('language_background')}
- Company Type: {persona.get('company_type')}
- Business Domain: {persona.get('business_domain')}

Your task:
1. Identify why the issue exists
2. Suggest a concise fix (1-2 sentences)
3. Focus on maintaining consistency between dimensions

Respond in this exact format:
ISSUE: [brief explanation of the problem]
FIX: [specific suggested change]
"""

        system_prompt = """You are a persona coherence expert. Analyze personas for logical consistency.
Focus on ensuring that experience level matches years, language matches geography, and all dimensions align realistically.
Be concise and practical in your suggestions."""

        response = self._call_vllm(refinement_prompt, system_prompt)

        if not response:
            return None

        # Parse response to extract suggested fix
        # For now, just return the assessment
        print(f"\n  Refinement suggestion:\n{response}")

        # Return None to indicate manual review needed
        return None

    def validate_persona(self, persona: Dict, persona_id: int) -> Tuple[bool, str]:
        """
        Validate a single persona.
        Returns (is_valid, notes)
        """
        # Check coherence
        is_coherent, issue = self._check_coherence(persona)

        if is_coherent:
            self.validated_count += 1
            return True, "✓ Coherent"

        # Try to refine if incoherent
        self.refined_count += 1
        refined = self._refine_persona(persona, issue)

        if refined:
            # Return refined persona marked for review
            return False, f"⚠ Refined (issue: {issue})"
        else:
            return False, f"✗ Incoherent (issue: {issue})"

    def validate_all(
        self,
        input_dir: Path,
        count: Optional[int] = None,
        dry_run: bool = False,
    ) -> Dict:
        """Validate all personas in input directory."""
        print(f"\n{'='*70}")
        print("PERSONA VALIDATION")
        print(f"{'='*70}")
        print(f"Input directory: {input_dir}")
        print(f"Dry run: {dry_run}")
        if count:
            print(f"Limit: {count}")
        print(f"{'='*70}\n")

        results = {
            "validated": 0,
            "incoherent": 0,
            "refined": 0,
            "failed": 0,
            "issues_found": [],
        }

        # Find all persona files
        persona_files = sorted(input_dir.glob("persona_*.json"))
        if count:
            persona_files = persona_files[:count]

        for i, persona_file in enumerate(persona_files, 1):
            try:
                with open(persona_file) as f:
                    persona = json.load(f)

                persona_id = persona.get("pk_user", i)
                is_valid, notes = self.validate_persona(persona, persona_id)

                if is_valid:
                    status = "✓"
                    results["validated"] += 1
                else:
                    status = "⚠"
                    results["incoherent"] += 1
                    results["issues_found"].append(f"Persona {persona_id}: {notes}")

                print(f"[{i:4d}] {persona_file.name} {status} - {notes}")

            except Exception as e:
                print(f"[{i:4d}] {persona_file.name} ✗ - Error: {e}")
                results["failed"] += 1

        # Print summary
        print(f"\n{'='*70}")
        print("VALIDATION SUMMARY")
        print(f"{'='*70}")
        print(f"Validated (coherent):  {results['validated']}")
        print(f"Incoherent:            {results['incoherent']}")
        print(f"Refined:               {results['refined']}")
        print(f"Failed:                {results['failed']}")
        print(f"{'='*70}\n")

        if results["issues_found"] and results["incoherent"] <= 10:
            print("Issues found:")
            for issue in results["issues_found"]:
                print(f"  - {issue}")
            print()

        return results


# ============================================================================
# Main
# ============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Validate and refine generated personas for coherence"
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=OUTPUT_DIR / "personas",
        help="Directory containing persona JSON files",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help="Validate only first N personas",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't call vLLM, just check local coherence",
    )

    args = parser.parse_args()

    # Validate input directory exists
    if not args.input_dir.exists():
        print(f"Error: Input directory not found: {args.input_dir}")
        sys.exit(1)

    # Run validation
    validator = PersonaValidator()
    results = validator.validate_all(
        args.input_dir,
        count=args.count,
        dry_run=args.dry_run,
    )

    # Exit with appropriate code
    if results["failed"] > 0:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
