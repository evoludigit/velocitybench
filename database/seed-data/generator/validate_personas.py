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

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Tuple

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

    def _call_vllm(self, prompt: str, system_prompt: str = "") -> str | None:
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

    def _refine_persona(self, persona: Dict, coherence_issue: str) -> Dict | None:
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

    def _validate_with_vllm(self, persona: Dict) -> Tuple[bool, str]:
        """
        Use vLLM to perform semantic coherence analysis of the entire persona.
        Returns (is_coherent, analysis_summary)
        """
        analysis_prompt = f"""
Analyze this persona profile for semantic coherence and realism. Check:
1. Does the title match the experience level? (Junior with 2 years vs Principal with 25 years)
2. Does the background story align with the business domain and company type?
3. Do the communication style and reply style match?
4. Are the expertise areas realistic for this title and domain?
5. Is the geographic region consistent with the name and language background?
6. Do the personality traits support the communication/reply style?

Persona:
- Name: {persona.get('name')}
- Title: {persona.get('title')}
- Years: {persona.get('years_experience')} ({persona.get('experience_level')})
- Region: {persona.get('geographic_region')}
- Language: {persona.get('language_background')}
- Company: {persona.get('company_type')}
- Domain: {persona.get('business_domain')}
- Communication style: {persona.get('communication_style')}
- Reply style: {persona.get('reply_style')}
- Expertise: {', '.join(persona.get('expertise_areas', []))}
- Traits: {', '.join(persona.get('personality_traits', []))}
- Background: {persona.get('background')[:100]}...

Respond with:
COHERENT: yes/no
SCORE: 0-100 (100 = perfect, 0 = completely incoherent)
ISSUES: [list any issues found, or "none" if fully coherent]
SUMMARY: [1-2 sentence explanation]
"""

        system_prompt = """You are a persona coherence expert. Analyze personas for logical consistency,
realism, and internal alignment. Be critical but fair. Focus on semantic coherence, not just data validation."""

        response = self._call_vllm(analysis_prompt, system_prompt)

        if not response:
            return None, "vLLM error"

        # Parse response - handle markdown formatting from vLLM
        text = response.strip().lower()

        # Extract COHERENT status
        is_coherent = None
        # Check various formats that vLLM might use
        if "coherent:" in text:
            coherent_section = text[text.find("coherent:"):text.find("coherent:") + 50]
            if "yes" in coherent_section:
                is_coherent = True
            elif "no" in coherent_section:
                is_coherent = False

        # Extract SCORE
        score = None
        import re
        # Robust pattern matching multiple vLLM formats:
        # - **SCORE:** **95/100** (markdown with asterisks)
        # - score: 85 (plain text with colon)
        # - SCORE:90 (no spaces)
        # - Score: 100 (mixed case)
        score_match = re.search(r'score[\s:*]*\**(\d+)', text, re.IGNORECASE)
        if score_match:
            try:
                score = int(score_match.group(1))
            except ValueError:
                score = None

        # Extract summary (first sentence mentioning coherent, realistic, etc.)
        summary = ""
        if "semantically coherent" in text:
            summary = "Semantically coherent and realistic"
        elif "well-structured" in text:
            summary = "Well-structured profile"
        elif "logical inconsistencies" in text and "no" in text:
            summary = "No logical inconsistencies"

        # If no explicit coherent flag but high score, consider coherent
        if is_coherent is None and score:
            is_coherent = score >= 70

        details = f"Score: {score}/100" if score is not None else "Analysis complete"
        if summary:
            details = f"{details} - {summary}"

        return is_coherent, details

    def validate_persona(self, persona: Dict, persona_id: int, use_vllm: bool = True) -> Tuple[bool, str]:
        """
        Validate a single persona.
        Returns (is_valid, notes)
        """
        # First check local coherence rules
        is_local_coherent, local_issue = self._check_coherence(persona)

        if not is_local_coherent and not use_vllm:
            # Failed local checks, no vLLM
            return False, f"✗ Local validation failed: {local_issue}"

        # If enabled, use vLLM for semantic analysis
        if use_vllm:
            is_vllm_coherent, vllm_analysis = self._validate_with_vllm(persona)

            if is_vllm_coherent:
                self.validated_count += 1
                if is_local_coherent:
                    return True, f"✓ Coherent - {vllm_analysis}"
                else:
                    # vLLM disagrees with local checks - show both
                    return True, f"✓ vLLM coherent (local issue: {local_issue}) - {vllm_analysis}"
            else:
                # vLLM found issues
                self.refined_count += 1
                return False, f"⚠ vLLM found issues - {vllm_analysis}"
        else:
            # No vLLM, just local checks
            if is_local_coherent:
                self.validated_count += 1
                return True, "✓ Coherent"
            else:
                return False, f"✗ {local_issue}"

    def validate_all(
        self,
        input_dir: Path,
        count: int | None = None,
        dry_run: bool = False,
        use_vllm: bool = True,
    ) -> Dict:
        """Validate all personas in input directory."""
        print(f"\n{'='*70}")
        print("PERSONA VALIDATION")
        print(f"{'='*70}")
        print(f"Input directory: {input_dir}")
        print(f"Dry run: {dry_run}")
        print(f"vLLM analysis: {'enabled' if use_vllm and not dry_run else 'disabled'}")
        if count:
            print(f"Limit: {count}")
        print(f"{'='*70}\n")

        results = {
            "validated": 0,
            "incoherent": 0,
            "refined": 0,
            "failed": 0,
            "vllm_analysis_skipped": 0,
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
                # Use vLLM unless in dry-run mode
                is_valid, notes = self.validate_persona(
                    persona, persona_id, use_vllm=use_vllm and not dry_run
                )

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
        print(f"Validated (coherent):      {results['validated']}")
        print(f"Incoherent/Issues:         {results['incoherent']}")
        print(f"Refined:                   {results['refined']}")
        print(f"Failed:                    {results['failed']}")
        if use_vllm and not dry_run:
            print(f"vLLM analysis performed:   yes")
        print(f"{'='*70}\n")

        if results["issues_found"] and results["incoherent"] <= 20:
            print("Issues found:")
            for issue in results["issues_found"][:20]:
                print(f"  - {issue}")
            if len(results["issues_found"]) > 20:
                print(f"  ... and {len(results['issues_found']) - 20} more")
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
    parser.add_argument(
        "--no-vllm",
        action="store_true",
        help="Skip vLLM semantic analysis, only do local validation",
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
        use_vllm=not args.no_vllm,
    )

    # Exit with appropriate code
    if results["failed"] > 0:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
