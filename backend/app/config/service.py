"""
Rule configuration service.
Handles loading, merging, and persisting rule configurations.
"""
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Literal, Optional

import yaml

from .models import Category, Rule, RuleExpected, RuleOverride, Template, UserOverrides


# Type alias for document type IDs
DocumentTypeId = Literal[
    "factsheet", "policy-brief", "issue-note", "working-paper", "publication"
]

# Mapping from document types to base template files
TEMPLATE_MAPPING: Dict[DocumentTypeId, str] = {
    "factsheet": "factsheet.yaml",
    "policy-brief": "brief.yaml",
    "issue-note": "brief.yaml",
    "working-paper": "publication.yaml",
    "publication": "publication.yaml",
}

# Resolve paths relative to backend directory
BACKEND_DIR = Path(__file__).parent.parent.parent
TEMPLATES_DIR = BACKEND_DIR / "templates"
USER_CONFIG_DIR = BACKEND_DIR / "user_config"


class RuleService:
    """
    Service for managing rule configurations.

    Handles:
    - Loading base YAML templates
    - Loading user overrides
    - Merging overrides with defaults
    - Saving user overrides atomically
    - Resetting to defaults
    """

    def __init__(
        self,
        templates_dir: Optional[Path] = None,
        user_config_dir: Optional[Path] = None
    ):
        """
        Initialize the rule service.

        Args:
            templates_dir: Directory containing base YAML templates
            user_config_dir: Directory for user override files
        """
        self.templates_dir = templates_dir or TEMPLATES_DIR
        self.user_config_dir = user_config_dir or USER_CONFIG_DIR

        # Ensure user config directory exists
        self.user_config_dir.mkdir(parents=True, exist_ok=True)

    def _get_template_path(self, document_type: DocumentTypeId) -> Path:
        """Get the path to the base template for a document type."""
        template_file = TEMPLATE_MAPPING.get(document_type)
        if not template_file:
            raise ValueError(f"Unknown document type: {document_type}")
        return self.templates_dir / template_file

    def _get_override_path(self, document_type: DocumentTypeId) -> Path:
        """Get the path to the user override file for a document type."""
        return self.user_config_dir / f"{document_type}.yaml"

    def _load_template(self, document_type: DocumentTypeId) -> Template:
        """
        Load and validate a base YAML template.

        Args:
            document_type: The document type to load

        Returns:
            Validated Template model

        Raises:
            FileNotFoundError: If template file doesn't exist
            ValueError: If template is invalid
        """
        template_path = self._get_template_path(document_type)

        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        with open(template_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Override document_type to match requested type (for shared templates)
        data["document_type"] = document_type

        return Template(**data)

    def _load_overrides(self, document_type: DocumentTypeId) -> Optional[UserOverrides]:
        """
        Load user overrides for a document type if they exist.

        Args:
            document_type: The document type to load overrides for

        Returns:
            UserOverrides model if file exists, None otherwise
        """
        override_path = self._get_override_path(document_type)

        if not override_path.exists():
            return None

        with open(override_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            return None

        return UserOverrides(**data)

    def _merge_overrides(
        self,
        template: Template,
        overrides: Optional[UserOverrides]
    ) -> Template:
        """
        Merge user overrides into a template.

        Only overrides fields that are explicitly set (not None).

        Args:
            template: The base template
            overrides: User overrides to apply (optional)

        Returns:
            Template with overrides applied
        """
        if not overrides:
            return template

        # Deep copy categories for mutation
        merged_categories: Dict[str, Category] = {}

        for cat_id, category in template.categories.items():
            merged_rules: Dict[str, Rule] = {}

            for rule_id, rule in category.rules.items():
                # Check if there's an override for this rule
                cat_overrides = overrides.overrides.get(cat_id, {})
                rule_override = cat_overrides.get(rule_id)

                if rule_override:
                    # Apply overrides
                    merged_rule = self._apply_override(rule, rule_override)
                    merged_rules[rule_id] = merged_rule
                else:
                    merged_rules[rule_id] = rule

            merged_categories[cat_id] = Category(
                name=category.name,
                rules=merged_rules
            )

        return Template(
            version=template.version,
            document_type=template.document_type,
            categories=merged_categories
        )

    def _apply_override(self, rule: Rule, override: RuleOverride) -> Rule:
        """
        Apply a single override to a rule.

        Only applies fields that are not None in the override.

        Args:
            rule: The base rule
            override: The override to apply

        Returns:
            New Rule with override applied
        """
        # Start with current rule values
        enabled = rule.enabled
        severity = rule.severity
        expected_dict = rule.expected.dict()

        # Apply overrides for non-None fields
        if override.enabled is not None:
            enabled = override.enabled

        if override.severity is not None:
            severity = override.severity

        if override.expected is not None:
            # Merge expected fields
            expected_dict.update(override.expected)

        return Rule(
            name=rule.name,
            description=rule.description,
            enabled=enabled,
            severity=severity,
            check_type=rule.check_type,
            expected=RuleExpected(**expected_dict)
        )

    def get_merged_rules(self, document_type: DocumentTypeId) -> Template:
        """
        Get the merged rules for a document type.

        Loads the base template and applies any user overrides.

        Args:
            document_type: The document type to get rules for

        Returns:
            Template with all rules (defaults + overrides merged)
        """
        template = self._load_template(document_type)
        overrides = self._load_overrides(document_type)
        return self._merge_overrides(template, overrides)

    def save_overrides(
        self,
        document_type: DocumentTypeId,
        overrides: UserOverrides
    ) -> None:
        """
        Save user overrides for a document type.

        Uses atomic write (temp file + replace) to prevent corruption.

        Args:
            document_type: The document type to save overrides for
            overrides: The overrides to save
        """
        override_path = self._get_override_path(document_type)

        # Ensure directory exists
        override_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict for YAML serialization
        data = overrides.dict()

        # Atomic write: temp file + replace
        fd, temp_path = tempfile.mkstemp(
            dir=override_path.parent,
            suffix=".yaml"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                yaml.safe_dump(
                    data,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True
                )
            # Atomic replace
            os.replace(temp_path, override_path)
        except Exception:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    def delete_overrides(self, document_type: DocumentTypeId) -> bool:
        """
        Delete user overrides for a document type (reset to defaults).

        Args:
            document_type: The document type to reset

        Returns:
            True if file was deleted, False if it didn't exist
        """
        override_path = self._get_override_path(document_type)

        if override_path.exists():
            override_path.unlink()
            return True

        return False

    def compute_overrides(
        self,
        document_type: DocumentTypeId,
        current: Template
    ) -> UserOverrides:
        """
        Compute minimal overrides by comparing current state to defaults.

        Only includes fields that differ from the original template.

        Args:
            document_type: The document type
            current: The current template state

        Returns:
            UserOverrides containing only changed fields
        """
        original = self._load_template(document_type)

        overrides_dict: Dict[str, Dict[str, RuleOverride]] = {}

        for cat_id, category in current.categories.items():
            if cat_id not in original.categories:
                continue

            original_category = original.categories[cat_id]
            cat_overrides: Dict[str, RuleOverride] = {}

            for rule_id, rule in category.rules.items():
                if rule_id not in original_category.rules:
                    continue

                original_rule = original_category.rules[rule_id]
                rule_override = self._compute_rule_override(original_rule, rule)

                if rule_override:
                    cat_overrides[rule_id] = rule_override

            if cat_overrides:
                overrides_dict[cat_id] = cat_overrides

        return UserOverrides(
            version=current.version,
            overrides=overrides_dict
        )

    def _compute_rule_override(
        self,
        original: Rule,
        current: Rule
    ) -> Optional[RuleOverride]:
        """
        Compute the override for a single rule.

        Returns None if no changes, otherwise returns RuleOverride
        with only changed fields.
        """
        enabled = None
        severity = None
        expected = None

        if current.enabled != original.enabled:
            enabled = current.enabled

        if current.severity != original.severity:
            severity = current.severity

        # Compare expected values
        original_expected = original.expected.dict()
        current_expected = current.expected.dict()

        expected_diff: Dict[str, Any] = {}
        for key, value in current_expected.items():
            if key not in original_expected or original_expected[key] != value:
                expected_diff[key] = value

        if expected_diff:
            expected = expected_diff

        # Return None if no changes
        if enabled is None and severity is None and expected is None:
            return None

        return RuleOverride(
            enabled=enabled,
            severity=severity,
            expected=expected
        )
