import warnings


def warn_deprecated_resource_api(old_path: str, new_path: str) -> None:
    """Warn about a deprecated root method moved to Resource API."""
    warnings.warn(
        f"`{old_path}` is deprecated; use `{new_path}`.",
        DeprecationWarning,
        stacklevel=3,
    )
