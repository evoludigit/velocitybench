#!/usr/bin/env python
"""
Layer 3: Persona Correction System

Takes vLLM coherence analysis and automatically corrects identified issues.

This script:
1. Analyzes each persona for coherence issues using vLLM
2. For each identified issue, generates targeted correction prompts
3. Applies corrections to specific fields
4. Re-validates to ensure improvements
5. Generates before/after reports

Usage:
    python correct_personas.py --input-dir output/personas/personas --output-dir output/personas/corrected
    python correct_personas.py --input-dir output/personas/personas --count 50 (correct first 50)
    python correct_personas.py --input-dir output/personas/personas --dry-run (analyze only)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import requests

# ============================================================================
# Configuration
# ============================================================================

VLLM_URL = "http://localhost:8000/v1/chat/completions"
MODEL_ID = "/data/models/fp16/Ministral-3-8B-Instruct-2512"
MAX_TOKENS = 300
TEMPERATURE = 0.1  # Very low for targeted corrections
TOP_P = 0.9

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR.parent / "output" / "personas"


# ============================================================================
# Persona Corrector
# ============================================================================


class PersonaCorrector:
    """Corrects personas based on vLLM coherence analysis."""

    def __init__(self):
        self.analyzed_count = 0
        self.corrected_count = 0
        self.failed_count = 0
        self.improvements_made = []

    def _call_vllm(self, prompt: str, system_prompt: str = "") -> str | None:
        """Call vLLM API and return response text."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = requests.post(
                VLLM_URL,
                json={
                    "model": MODEL_ID,
                    "messages": messages,
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

    def _analyze_persona(self, persona: Dict) -> Tuple[bool, int, List[str]]:
        """
        Analyze persona for coherence issues.
        Returns (is_coherent, score, issues_list)
        """
        analysis_prompt = f"""
Analyze this persona profile for semantic coherence and realism. Check:
1. Does the title match the experience level?
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

Respond ONLY with structured lines (one per line):
COHERENT: yes/no
SCORE: <number>
ISSUES: <issue1> | <issue2> | <issue3>
"""

        system_prompt = """You are a persona coherence expert. Analyze personas and respond with structured data only.
Use EXACTLY this format - no explanations, no extra text."""

        response = self._call_vllm(analysis_prompt, system_prompt)

        if not response:
            return None, None, []

        text = response.strip().lower()
        issues = []

        # Extract COHERENT
        is_coherent = None
        if "coherent:" in text:
            coherent_section = text[text.find("coherent:") : text.find("coherent:") + 50]
            is_coherent = "yes" in coherent_section

        # Extract SCORE
        score = None
        score_match = re.search(r'score[:\*]* *\*?(\d+)', text)
        if score_match:
            try:
                score = int(score_match.group(1))
            except ValueError:
                pass

        # Extract ISSUES
        if "issues:" in text:
            issues_section = text[text.find("issues:") : text.find("issues:") + 500]
            # Split by | or newline
            issue_parts = re.split(r'\||\n', issues_section)
            for part in issue_parts:
                part = part.strip()
                if part and part != "issues:" and len(part) > 5:
                    issues.append(part)

        return is_coherent, score, issues[:5]  # Max 5 issues

    def _correct_field(
        self, persona: Dict, field_name: str, issue_description: str
    ) -> Optional:
        """
        Generate a correction for a specific field.
        Returns corrected value (str, list, or None) based on field type.
        """
        current_value = persona.get(field_name)
        if not current_value:
            return None

        is_array = isinstance(current_value, list)
        array_format = "(comma-separated list)" if is_array else ""

        correction_prompt = f"""
Field to fix: {field_name}
Current value: {current_value}
Issue: {issue_description}
Format: {array_format}

Context:
- Title: {persona.get('title')}
- Experience: {persona.get('years_experience')} years ({persona.get('experience_level')})
- Domain: {persona.get('business_domain')}
- Company: {persona.get('company_type')}
- Region: {persona.get('geographic_region')}
- Language: {persona.get('language_background')}

Generate a corrected value for '{field_name}' that fixes the issue.
Respond with ONLY the corrected value, no explanation.{' For arrays, use comma-separated format.' if is_array else ''}"""

        system_prompt = (
            f"You are fixing a '{field_name}' field in a professional persona.\n"
            "Respond with ONLY the corrected value. Keep it concise and realistic."
        )

        corrected = self._call_vllm(correction_prompt, system_prompt)

        if corrected:
            corrected = corrected.strip()
            # Remove quotes if present
            if corrected.startswith('"') and corrected.endswith('"'):
                corrected = corrected[1:-1]

            if len(corrected) > 0:
                # If field was originally an array, convert back to array
                if is_array:
                    # Parse comma-separated values
                    items = [item.strip() for item in corrected.split(",")]
                    return items

                return corrected

        return None

    def _map_issue_to_field(self, persona: Dict, issue: str) -> tuple[str, str] | None:
        """
        Map an issue description to a specific field and correction strategy.
        Returns (field_name, correction_type)
        """
        issue_lower = issue.lower()

        # Title/Experience mismatch
        if any(
            x in issue_lower
            for x in ["title", "experience level", "years don't match"]
        ):
            return ("title", "title_experience_alignment")

        # Expertise/Title mismatch
        if any(x in issue_lower for x in ["expertise", "skills don't match"]):
            return ("expertise_areas", "expertise_domain_alignment")

        # Communication style mismatch
        if any(x in issue_lower for x in ["communication", "reply style"]):
            return ("communication_style", "communication_alignment")

        # Background/Domain mismatch
        if any(x in issue_lower for x in ["background", "domain", "story align"]):
            return ("background", "background_domain_alignment")

        # Geographic/Language mismatch
        if any(x in issue_lower for x in ["geographic", "language", "region"]):
            return ("language_background", "geographic_language_alignment")

        # Personality/Communication mismatch
        if any(x in issue_lower for x in ["personality", "trait", "character"]):
            return ("personality_traits", "personality_communication_alignment")

        return None

    def correct_persona(
        self, persona: Dict, persona_id: int, dry_run: bool = False
    ) -> Tuple[Dict, List[str]]:
        """
        Analyze and correct a single persona.
        Returns (corrected_persona, list_of_corrections_made)
        """
        self.analyzed_count += 1
        corrections_made = []

        # Analyze persona
        is_coherent, score, issues = self._analyze_persona(persona)

        if is_coherent:
            return persona, []  # Already coherent

        if not issues or len(issues) == 0:
            return persona, []  # No specific issues found

        # Make corrections
        corrected_persona = persona.copy()

        for issue in issues:
            mapping = self._map_issue_to_field(persona, issue)
            if not mapping:
                continue

            field_name, correction_type = mapping

            if dry_run:
                corrections_made.append(f"Would correct {field_name}: {issue}")
            else:
                corrected_value = self._correct_field(persona, field_name, issue)

                if corrected_value:
                    old_value = corrected_persona.get(field_name)
                    corrected_persona[field_name] = corrected_value

                    corrections_made.append(
                        f"Corrected {field_name}: {issue[:50]}... ({old_value[:30]}... → {corrected_value[:30]}...)"
                    )
                    self.corrected_count += 1

        return corrected_persona, corrections_made

    def process_all(
        self,
        input_dir: Path,
        output_dir: Path | None = None,
        count: int | None = None,
        dry_run: bool = False,
    ) -> Dict:
        """Process all personas for correction."""
        print(f"\n{'='*70}")
        print("PERSONA CORRECTION (LAYER 3)")
        print(f"{'='*70}")
        print(f"Input directory: {input_dir}")
        print(f"Dry run: {dry_run}")
        if output_dir and not dry_run:
            print(f"Output directory: {output_dir}")
            output_dir.mkdir(parents=True, exist_ok=True)
        if count:
            print(f"Limit: {count}")
        print(f"{'='*70}\n")

        results = {
            "analyzed": 0,
            "corrected": 0,
            "unchanged": 0,
            "failed": 0,
            "total_corrections": 0,
            "summary": [],
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
                corrected_persona, corrections = self.correct_persona(
                    persona, persona_id, dry_run
                )

                results["analyzed"] += 1

                if corrections:
                    results["corrected"] += 1
                    results["total_corrections"] += len(corrections)

                    status = "↻" if dry_run else "✓"
                    corrections_summary = "; ".join(corrections[:2])
                    if len(corrections) > 2:
                        corrections_summary += f"; +{len(corrections)-2} more"

                    print(f"[{i:4d}] {persona_file.name} {status}")
                    for corr in corrections[:2]:
                        print(f"       - {corr}")
                    if len(corrections) > 2:
                        print(f"       ... and {len(corrections)-2} more corrections")

                    results["summary"].append(
                        {
                            "persona_id": persona_id,
                            "corrections": len(corrections),
                            "details": corrections,
                        }
                    )

                    # Save corrected persona if not dry-run
                    if not dry_run and output_dir:
                        output_file = output_dir / persona_file.name
                        with open(output_file, "w") as f:
                            json.dump(corrected_persona, f, indent=2)

                else:
                    results["unchanged"] += 1

            except Exception as e:
                print(f"[{i:4d}] {persona_file.name} ✗ - Error: {e}")
                results["failed"] += 1

        # Print summary
        print(f"\n{'='*70}")
        print("CORRECTION SUMMARY")
        print(f"{'='*70}")
        print(f"Analyzed:              {results['analyzed']}")
        print(f"Corrected:             {results['corrected']}")
        print(f"Unchanged (coherent):  {results['unchanged']}")
        print(f"Failed:                {results['failed']}")
        print(f"Total corrections:     {results['total_corrections']}")
        if results["corrected"] > 0:
            avg_corrections = results["total_corrections"] / results["corrected"]
            print(f"Avg corrections/persona: {avg_corrections:.1f}")
        print(f"{'='*70}\n")

        if results["summary"] and results["corrected"] <= 20:
            print("Correction details (first 20 personas):")
            for item in results["summary"][:20]:
                print(f"\n  Persona {item['persona_id']}:")
                for detail in item["details"]:
                    print(f"    - {detail}")
            if len(results["summary"]) > 20:
                print(f"\n  ... and {len(results['summary']) - 20} more personas corrected")

        return results


# ============================================================================
# Main
# ============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Correct personas based on vLLM coherence analysis"
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=OUTPUT_DIR / "personas",
        help="Directory containing persona JSON files",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR / "corrected",
        help="Directory to save corrected personas",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help="Correct only first N personas",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyze without making corrections",
    )

    args = parser.parse_args()

    # Validate input directory
    if not args.input_dir.exists():
        print(f"Error: Input directory not found: {args.input_dir}")
        sys.exit(1)

    # Run correction
    corrector = PersonaCorrector()
    results = corrector.process_all(
        args.input_dir,
        output_dir=args.output_dir,
        count=args.count,
        dry_run=args.dry_run,
    )

    # Exit with appropriate code
    if results["failed"] > 0:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
