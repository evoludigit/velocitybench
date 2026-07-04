//! Configuration cache for trigger functions.
//!
//! Provides a backend-local cache for identifier and path configuration,
//! with manual invalidation via `reload_config()`.
//!
//! This cache avoids per-row SPI overhead during trigger execution while
//! remaining refreshable for configuration updates without server restart.

use std::sync::atomic::{AtomicBool, Ordering};

/// Dirty flag for config cache invalidation.
/// When set to true, the cache should be cleared on next access.
/// This is set by `reload_config()` to invalidate cached entries.
static CONFIG_DIRTY: AtomicBool = AtomicBool::new(false);

/// Mark the config cache as dirty (needing reload).
/// Called by `reload_config()` to invalidate cached configuration.
pub fn mark_dirty() {
    CONFIG_DIRTY.store(true, Ordering::SeqCst);
}

/// Check if the config cache is dirty and needs reload.
/// Returns true if `reload_config()` was called since last check.
/// Used by trigger functions to check cache validity.
#[allow(dead_code)] // Used by trigger functions
pub fn is_dirty() -> bool {
    CONFIG_DIRTY.load(Ordering::SeqCst)
}

/// Clear the dirty flag after reloading config.
/// Called after refreshing cached configuration from the catalog.
/// Used by trigger functions after reloading configuration.
#[allow(dead_code)] // Used by trigger functions
pub fn clear_dirty() {
    CONFIG_DIRTY.store(false, Ordering::SeqCst);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_config_cache_dirty_flag() {
        clear_dirty();
        assert!(!is_dirty(), "Cache should not be dirty initially");

        mark_dirty();
        assert!(is_dirty(), "Cache should be dirty after marking");

        clear_dirty();
        assert!(!is_dirty(), "Cache should not be dirty after clearing");
    }
}
