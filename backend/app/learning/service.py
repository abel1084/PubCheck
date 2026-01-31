"""
Service for managing ignored rules persistence.
Uses atomic file writes to prevent corruption.
"""
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from .models import IgnoredRule, IgnoredRulesConfig


# Resolve paths relative to backend directory
BACKEND_DIR = Path(__file__).parent.parent.parent
USER_CONFIG_DIR = BACKEND_DIR / "user_config"
IGNORED_RULES_FILE = USER_CONFIG_DIR / "ignored_rules.json"


class IgnoredRulesService:
    """
    Service for managing ignored rules.

    Handles:
    - Loading ignored rules from JSON file
    - Saving with atomic writes (temp file + replace)
    - Adding and removing ignored rules
    - Filtering rules by document type
    """

    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize the ignored rules service.

        Args:
            config_file: Path to the config file (defaults to user_config/ignored_rules.json)
        """
        self.config_file = config_file or IGNORED_RULES_FILE

        # Ensure user config directory exists
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> IgnoredRulesConfig:
        """
        Load ignored rules from file.

        Returns:
            IgnoredRulesConfig with loaded rules, or empty config if file doesn't exist
        """
        if not self.config_file.exists():
            return IgnoredRulesConfig()

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return IgnoredRulesConfig(**data)
        except (json.JSONDecodeError, ValueError):
            # Return empty config on parse error
            return IgnoredRulesConfig()

    def save(self, config: IgnoredRulesConfig) -> None:
        """
        Save ignored rules to file using atomic write.

        Uses temp file + os.replace pattern to prevent corruption.

        Args:
            config: The configuration to save
        """
        # Ensure directory exists
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict for JSON serialization
        data = config.dict()

        # Atomic write: temp file + replace
        fd, temp_path = tempfile.mkstemp(
            dir=self.config_file.parent,
            suffix=".json"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            # Atomic replace
            os.replace(temp_path, self.config_file)
        except Exception:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    def add_rule(
        self,
        rule_id: str,
        document_type: str,
        reason: Optional[str] = None
    ) -> IgnoredRule:
        """
        Add a rule to the ignored list.

        If the rule already exists for this document type, updates it.

        Args:
            rule_id: The rule ID to ignore
            document_type: The document type context
            reason: Optional reason for ignoring

        Returns:
            The created/updated IgnoredRule
        """
        config = self.load()

        # Check if rule already exists
        existing_index = None
        for i, rule in enumerate(config.ignored):
            if rule.rule_id == rule_id and rule.document_type == document_type:
                existing_index = i
                break

        # Create new rule
        new_rule = IgnoredRule(
            rule_id=rule_id,
            document_type=document_type,
            reason=reason,
            added_date=datetime.now(timezone.utc).isoformat()
        )

        if existing_index is not None:
            # Update existing
            config.ignored[existing_index] = new_rule
        else:
            # Add new
            config.ignored.append(new_rule)

        self.save(config)
        return new_rule

    def remove_rule(self, rule_id: str, document_type: str) -> bool:
        """
        Remove a rule from the ignored list.

        Args:
            rule_id: The rule ID to remove
            document_type: The document type context

        Returns:
            True if rule was found and removed, False otherwise
        """
        config = self.load()

        # Find and remove matching rule
        original_count = len(config.ignored)
        config.ignored = [
            rule for rule in config.ignored
            if not (rule.rule_id == rule_id and rule.document_type == document_type)
        ]

        if len(config.ignored) < original_count:
            self.save(config)
            return True

        return False

    def get_all(self) -> List[IgnoredRule]:
        """
        Get all ignored rules.

        Returns:
            List of all IgnoredRule entries
        """
        config = self.load()
        return config.ignored

    def get_ignored_for_doc_type(self, document_type: str) -> List[str]:
        """
        Get list of rule IDs that are ignored for a specific document type.

        Args:
            document_type: The document type to filter by

        Returns:
            List of rule_id strings for filtering
        """
        config = self.load()
        return [
            rule.rule_id
            for rule in config.ignored
            if rule.document_type == document_type
        ]
