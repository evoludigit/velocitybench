#[allow(unused_imports)]
use pgrx::prelude::*;
use std::collections::HashSet;
use unicode_normalization::UnicodeNormalization;

pgrx::pg_module_magic!();

pgrx::extension_sql_file!("../sql/bootstrap.sql", name = "bootstrap", bootstrap);

// Declare the treekey schema so pgrx validates `schema = "treekey"` attributes.
// The actual CREATE SCHEMA is in bootstrap.sql; this declaration is pgrx-internal only.
#[pg_schema]
mod treekey {}

mod bootstrap;
mod config_cache;
mod flat_identifiers;
mod management_functions;
mod path_management;
mod trigger_functions;

/// Converts text to a slug using ligature expansion, NFKD decomposition, and separator normalization.
///
/// # Arguments
/// * `input` - The text to convert to a slug
/// * `separator` - The character to use for word separation (typically "-" or ".")
///
/// # Panics
/// Panics if `separator` is empty
#[pg_extern(schema = "treekey")]
#[must_use]
pub fn slugify(input: &str, separator: &str) -> String {
    let mut result = String::new();

    // Step 1: Apply ligature mappings before NFKD
    let with_ligatures = expand_ligatures(input);

    // Step 2: NFKD decompose
    let decomposed = with_ligatures.nfkd().collect::<String>();

    // Step 3: Process decomposed string: strip combining marks, lowercase, handle separators
    let mut in_separator_run = false;

    for c in decomposed.chars() {
        if is_word_character(c) {
            if in_separator_run && !result.is_empty() {
                result.push_str(separator);
            }
            in_separator_run = false;
            result.push_str(&c.to_lowercase().collect::<String>());
        } else if !is_combining_mark(c) {
            // Non-word character triggers separator
            in_separator_run = true;
        }
        // Skip combining marks entirely
    }

    // Trim leading and trailing separators
    let sep_char = if separator.len() == 1 {
        separator.chars().next().unwrap()
    } else {
        ' ' // fallback for multi-char separators
    };
    result.trim_matches(sep_char).to_string()
}

/// Generates a unique identifier by adding numeric suffixes to avoid collisions.
///
/// If `base` is not in `taken`, returns `base`. Otherwise returns `base` with
/// a numeric suffix (`#2`, `#3`, etc.) that doesn't exist in `taken`.
/// Fills gaps in the numbering (if `x` and `x#3` are taken, returns `x#2`).
///
/// # Arguments
/// * `base` - The base identifier to use
/// * `taken` - Array of identifiers already in use
#[must_use]
pub fn identifier_next(base: &str, taken: &[&str]) -> String {
    identifier_next_impl(base, taken)
}

#[pg_extern(schema = "treekey", name = "identifier_next")]
#[must_use]
#[allow(clippy::needless_pass_by_value)]
fn identifier_next_sql(base: &str, taken: Vec<String>) -> String {
    let taken_refs: Vec<&str> = taken.iter().map(String::as_str).collect();
    identifier_next_impl(base, &taken_refs)
}

fn identifier_next_impl(base: &str, taken: &[&str]) -> String {
    // Convert taken array to HashSet for O(1) lookup
    let taken_set: HashSet<&str> = taken.iter().copied().collect();

    // If base is not taken, return it
    if !taken_set.contains(base) {
        return base.to_string();
    }

    // Otherwise, find the first available numbered suffix
    let mut n = 2;
    loop {
        let candidate = format!("{base}#{n}");
        if !taken_set.contains(candidate.as_str()) {
            return candidate;
        }
        n += 1;
    }
}

/// Removes a scope prefix from an identifier if it matches.
///
/// If `identifier` starts with `scope` followed by '|', returns the remainder.
/// Otherwise returns the identifier unchanged.
///
/// # Arguments
/// * `identifier` - The identifier to process
/// * `scope` - The scope prefix to strip
#[pg_extern(schema = "treekey", name = "scope_strip")]
#[must_use]
fn scope_strip_sql(identifier: &str, scope: &str) -> String {
    scope_strip(identifier, scope).to_string()
}

#[must_use]
pub fn scope_strip<'a>(identifier: &'a str, scope: &str) -> &'a str {
    // Check if identifier starts with "scope|"
    if let Some(remainder) = identifier.strip_prefix(scope) {
        if let Some(stripped) = remainder.strip_prefix('|') {
            return stripped;
        }
    }
    identifier
}

/// Expand ligature characters to their multi-character equivalents.
/// This is applied before NFKD decomposition to handle ligatures that don't decompose.
fn expand_ligatures(input: &str) -> String {
    input
        .chars()
        .flat_map(|c| match c {
            // Ligatures
            'ﬁ' => "fi".chars().collect::<Vec<_>>(), // fi ligature -> fi
            'ﬂ' => "fl".chars().collect::<Vec<_>>(), // fl ligature -> fl
            'ﬃ' => "ffi".chars().collect::<Vec<_>>(), // ffi ligature -> ffi
            'ﬄ' => "ffl".chars().collect::<Vec<_>>(), // ffl ligature -> ffl
            'ﬅ' => "ft".chars().collect::<Vec<_>>(), // ft ligature -> ft
            'ﬆ' => "st".chars().collect::<Vec<_>>(), // st ligature -> st
            // Stroked letters
            'ø' => "o".chars().collect::<Vec<_>>(), // o with stroke -> o
            'Ø' => "O".chars().collect::<Vec<_>>(), // o with stroke uppercase -> O
            'ł' => "l".chars().collect::<Vec<_>>(), // l with stroke -> l
            'Ł' => "L".chars().collect::<Vec<_>>(), // l with stroke uppercase -> L
            'đ' | 'ð' => "d".chars().collect::<Vec<_>>(), // d with stroke/eth -> d
            'Đ' | 'Ð' => "D".chars().collect::<Vec<_>>(), // d with stroke/eth uppercase -> D
            // Ash ligature (explicit, though NFKD also handles)
            'æ' => "ae".chars().collect::<Vec<_>>(), // ash -> ae
            'Æ' => "Ae".chars().collect::<Vec<_>>(), // ash uppercase -> Ae
            // OE ligature
            'œ' => "oe".chars().collect::<Vec<_>>(), // oe ligature -> oe
            'Œ' => "Oe".chars().collect::<Vec<_>>(), // oe ligature uppercase -> Oe
            // Old English
            'þ' => "th".chars().collect::<Vec<_>>(), // thorn -> th
            'Þ' => "Th".chars().collect::<Vec<_>>(), // thorn uppercase -> Th
            // German
            'ß' => "ss".chars().collect::<Vec<_>>(), // German sharp s -> ss
            _ => vec![c],
        })
        .collect()
}

/// Check if a character is a word character (alphabetic or numeric).
fn is_word_character(c: char) -> bool {
    c.is_alphabetic() || c.is_numeric()
}

/// Check if a character is a combining mark (Unicode category Mark).
const fn is_combining_mark(c: char) -> bool {
    // Unicode combining marks are in the Mark category (Mn, Mc, Me)
    // We can check for common combining marks by their ranges
    matches!(c as u32,
        0x0300..=0x036F |    // Combining Diacritical Marks
        0x1AB0..=0x1AFF |    // Combining Diacritical Marks Extended
        0x1DC0..=0x1DFF |    // Combining Diacritical Marks Supplement
        0x20D0..=0x20FF      // Combining Diacritical Marks for Symbols
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_slugify_ascii_passthrough() {
        assert_eq!(slugify("hello", "-"), "hello");
    }

    #[test]
    fn test_slugify_accented_characters() {
        assert_eq!(slugify("Ile-de-France", "-"), "ile-de-france");
    }

    #[test]
    fn test_slugify_combining_marks() {
        // "nino" with combining tilde
        let input = "nino\u{0303}";
        assert_eq!(slugify(input, "-"), "nino");
    }

    #[test]
    fn test_slugify_separator_collapsing() {
        assert_eq!(slugify("a - - b", "-"), "a-b");
    }

    #[test]
    fn test_slugify_leading_trailing_separator_trimming() {
        assert_eq!(slugify(" hello ", "-"), "hello");
    }

    #[test]
    fn test_slugify_custom_separator() {
        assert_eq!(slugify("a b", "."), "a.b");
    }

    #[test]
    fn test_slugify_oeuvre_ligature() {
        // œuvre with oe ligature (U+0153)
        assert_eq!(slugify("œuvre", "-"), "oeuvre");
    }

    #[test]
    fn test_slugify_ae_ligature() {
        // Aerosol with AE ligature (U+00C6 -> ae)
        assert_eq!(slugify("Aerosol", "-"), "aerosol");
    }

    #[test]
    fn test_slugify_german_ss_ligature() {
        // Strasse with German sharp s (U+00DF -> ss)
        assert_eq!(slugify("Strasse", "-"), "strasse");
    }

    #[test]
    fn test_slugify_eth_ligature() {
        // edh with U+00F0 (-> d)
        assert_eq!(slugify("ðe", "-"), "de");
    }

    #[test]
    fn test_slugify_thorn_ligature() {
        // thorn with U+00FE (-> th)
        assert_eq!(slugify("þorn", "-"), "thorn");
    }

    #[test]
    fn test_slugify_ash_ligature() {
        // æsop with ash (U+00E6 -> ae)
        assert_eq!(slugify("æsop", "-"), "aesop");
    }

    #[test]
    fn test_slugify_fi_ligature() {
        // ﬁnish with fi ligature (U+FB01 -> fi)
        assert_eq!(slugify("ﬁnish", "-"), "finish");
    }

    #[test]
    fn test_slugify_fl_ligature() {
        // ﬂower with fl ligature (U+FB02 -> fl)
        assert_eq!(slugify("ﬂower", "-"), "flower");
    }

    #[test]
    fn test_slugify_ffi_ligature() {
        // raﬃng with ffi ligature (U+FB03 -> ffi)
        assert_eq!(slugify("raﬃng", "-"), "raffing");
    }

    #[test]
    fn test_slugify_ffl_ligature() {
        // shuﬄe with ffl ligature (U+FB04 -> ffl)
        assert_eq!(slugify("shuﬄe", "-"), "shuffle");
    }

    #[test]
    fn test_slugify_stroked_o() {
        // løren with ø (U+00F8 -> o)
        assert_eq!(slugify("løren", "-"), "loren");
    }

    #[test]
    fn test_slugify_stroked_l() {
        // łódź with ł (U+0142 -> l)
        assert_eq!(slugify("łódź", "-"), "lodz");
    }

    #[test]
    fn test_slugify_stroked_d() {
        // đông with đ (U+0111 -> d)
        assert_eq!(slugify("đông", "-"), "dong");
    }

    #[test]
    fn test_scope_strip_matching_scope() {
        assert_eq!(scope_strip("acme|model.SN123", "acme"), "model.SN123");
    }

    #[test]
    fn test_scope_strip_non_matching_scope() {
        assert_eq!(scope_strip("other|x", "acme"), "other|x");
    }

    #[test]
    fn test_scope_strip_matching_scope_short_remainder() {
        assert_eq!(scope_strip("acme|x", "acme"), "x");
    }

    #[test]
    fn test_scope_strip_matching_scope_empty_remainder() {
        assert_eq!(scope_strip("acme|", "acme"), "");
    }

    #[test]
    fn test_scope_strip_no_pipe() {
        assert_eq!(scope_strip("acme", "acme"), "acme");
    }

    #[test]
    fn test_identifier_next_empty_taken() {
        assert_eq!(identifier_next("x", &[]), "x");
    }

    #[test]
    fn test_identifier_next_single_conflict() {
        assert_eq!(identifier_next("x", &["x"]), "x#2");
    }

    #[test]
    fn test_identifier_next_multiple_conflicts() {
        assert_eq!(identifier_next("x", &["x", "x#2"]), "x#3");
    }

    #[test]
    fn test_identifier_next_multiple_conflicts_three() {
        assert_eq!(identifier_next("x", &["x", "x#2", "x#3"]), "x#4");
    }

    #[test]
    fn test_identifier_next_gap_filling() {
        assert_eq!(identifier_next("x", &["x", "x#3"]), "x#2");
    }

    #[test]
    fn test_identifier_next_base_already_suffixed() {
        assert_eq!(identifier_next("x#2", &["x#2"]), "x#2#2");
    }
}
