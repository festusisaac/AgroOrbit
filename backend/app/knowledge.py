"""Knowledge base loader for crop traits, rotation libraries, and soil modifiers.

Strictly adheres to Section 7 of AGROORBIT_PLAN_v2.md:
- Validates per-trait schema (value, verified, source).
- Rejects verified:true when source is null or empty.
- Computes verified_share dynamically.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator

from app.config import DATA_DIR
from app.models import CropItem, LocationItem

CROPS_FILE = DATA_DIR / "crops.json"
ROTATIONS_FILE = DATA_DIR / "rotations.json"
SOIL_MODIFIERS_FILE = DATA_DIR / "soil_modifiers.json"
LOCATIONS_FILE = DATA_DIR / "locations.json"


class KnowledgeBaseError(Exception):
    """Base exception for knowledge base errors."""
    pass


class KnowledgeValidationError(KnowledgeBaseError):
    """Raised when data files fail validation rules."""
    pass


class TraitValue(BaseModel):
    """Container for individual crop traits with provenance tracking."""
    value: Any
    verified: bool
    source: Optional[str] = None

    @model_validator(mode="after")
    def validate_source_if_verified(self):
        """CRITICAL RULE: verified:true is strictly prohibited without a non-empty source."""
        if self.verified and (self.source is None or not str(self.source).strip()):
            raise ValueError("A trait marked verified=True must provide a valid citation/source string.")
        return self


class CropRecord(BaseModel):
    """Internal representation of a crop in the agronomic knowledge base."""
    id: str
    name: str
    family: str
    traits: Dict[str, TraitValue]
    pest_disease_notes: TraitValue

    def get_verified_share(self) -> float:
        """Calculates share of verified traits across all defined traits."""
        all_traits = list(self.traits.values()) + [self.pest_disease_notes]
        if not all_traits:
            return 0.0
        verified_count = sum(1 for t in all_traits if t.verified)
        return round(verified_count / len(all_traits), 2)


class RotationRecord(BaseModel):
    """Candidate or library crop sequence."""
    id: str
    name: str
    sequence: List[str]
    description: str


def load_crops(file_path: Path = CROPS_FILE) -> Dict[str, CropRecord]:
    """Loads and strictly validates crops.json."""
    if not file_path.exists():
        raise KnowledgeBaseError(f"Crops file not found at {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except Exception as e:
        raise KnowledgeBaseError(f"Failed to parse {file_path}: {e}")

    if not isinstance(raw_data, list):
        raise KnowledgeValidationError(f"Expected a list of crops in {file_path}, got {type(raw_data).__name__}")

    crops_dict: Dict[str, CropRecord] = {}
    for item in raw_data:
        if not isinstance(item, dict):
            raise KnowledgeValidationError(f"Invalid crop entry: {item}")
        crop_id = item.get("id")
        if not crop_id:
            raise KnowledgeValidationError("Crop entry missing 'id'")

        # Ensure all traits have value, verified, and source
        traits = item.get("traits", {})
        if not isinstance(traits, dict) or not traits:
            raise KnowledgeValidationError(f"Crop '{crop_id}' must contain a non-empty 'traits' dictionary")

        for trait_name, trait_data in traits.items():
            if not isinstance(trait_data, dict):
                raise KnowledgeValidationError(f"Trait '{trait_name}' in crop '{crop_id}' must be a dictionary")
            for req_field in ["value", "verified", "source"]:
                if req_field not in trait_data:
                    raise KnowledgeValidationError(
                        f"Crop '{crop_id}' trait '{trait_name}' is missing mandatory field '{req_field}'"
                    )

        try:
            record = CropRecord(**item)
            crops_dict[record.id] = record
        except Exception as e:
            raise KnowledgeValidationError(f"Validation error for crop '{crop_id}': {e}")

    return crops_dict


def load_rotations(file_path: Path = ROTATIONS_FILE) -> List[RotationRecord]:
    """Loads and validates candidate rotations library."""
    if not file_path.exists():
        raise KnowledgeBaseError(f"Rotations file not found at {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except Exception as e:
        raise KnowledgeBaseError(f"Failed to parse {file_path}: {e}")

    if not isinstance(raw_data, list):
        raise KnowledgeValidationError(f"Expected a list in {file_path}")

    rotations: List[RotationRecord] = []
    for item in raw_data:
        try:
            rotations.append(RotationRecord(**item))
        except Exception as e:
            raise KnowledgeValidationError(f"Invalid rotation record: {item}. Error: {e}")

    return rotations


def load_soil_modifiers(file_path: Path = SOIL_MODIFIERS_FILE) -> Dict[str, Any]:
    """Loads and validates soil modifiers heuristic table."""
    if not file_path.exists():
        raise KnowledgeBaseError(f"Soil modifiers file not found at {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise KnowledgeBaseError(f"Failed to parse {file_path}: {e}")

    # Validate mandatory categories
    required_categories = ["texture", "drainage", "organic_matter", "water_source", "slope"]
    for cat in required_categories:
        if cat not in data:
            raise KnowledgeValidationError(f"Soil modifiers file missing category '{cat}'")

    return data


def load_locations(file_path: Path = LOCATIONS_FILE) -> List[LocationItem]:
    """Loads preset demo locations."""
    if not file_path.exists():
        raise KnowledgeBaseError(f"Locations file not found at {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except Exception as e:
        raise KnowledgeBaseError(f"Failed to parse {file_path}: {e}")

    return [LocationItem(**loc) for loc in raw_data]


def get_crops_api_summary(file_path: Path = CROPS_FILE) -> List[CropItem]:
    """Returns CropItem summaries matching Section 9 API contract with dynamically computed verified_share."""
    crops_dict = load_crops(file_path)
    summary_list: List[CropItem] = []

    for crop in crops_dict.values():
        # Build traits summary dictionary (e.g. key: formatted value)
        summary_dict = {}
        for t_name, t_obj in crop.traits.items():
            val = t_obj.value
            if isinstance(val, dict) and "min" in val and "max" in val:
                summary_dict[t_name] = f"{val['min']}-{val['max']}"
            else:
                summary_dict[t_name] = val

        summary_list.append(
            CropItem(
                id=crop.id,
                name=crop.name,
                family=crop.family,
                traits_summary=summary_dict,
                verified_share=crop.get_verified_share(),
            )
        )

    return summary_list
