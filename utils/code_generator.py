import logging
import random
import string
from typing import Set

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.repository import GameRepository

logger = logging.getLogger(__name__)

# Available prefixes for game codes
PREFIXES = ["SANTA", "XMAS", "GIFT", "SNOW", "JOLLY", "MERRY"]

# Characters for random suffix (uppercase letters and digits)
SUFFIX_CHARS = string.ascii_uppercase + string.digits

# Code configuration
MIN_SUFFIX_LENGTH = 2
MAX_SUFFIX_LENGTH = 4
MAX_GENERATION_ATTEMPTS = 100


async def generate_game_code(
    session, prefix_list, suffix_length):
    """
    Generate a unique game code for Secret Santa
    
    Format: PREFIX + random alphanumeric suffix
    Examples: SANTA42, XMAS7K, GIFT9Z2, MERRY1A3
    """
    repository = GameRepository(session)
    prefixes = prefix_list or PREFIXES

    for attempt in range(1, MAX_GENERATION_ATTEMPTS + 1):
        # Generate code
        code = _generate_code(prefixes, suffix_length)

        # Check uniqueness
        existing_game = await repository.get_game_by_code(code)
        
        if existing_game is None:
            logger.info(f"Generated unique game code: {code} (attempt {attempt})")
            return code
        
        logger.debug(f"Code collision: {code} (attempt {attempt})")

    # If we reach here, we failed to generate a unique code
    error_msg = f"Failed to generate unique game code after {MAX_GENERATION_ATTEMPTS} attempts"
    logger.error(error_msg)
    raise RuntimeError(error_msg)


def _generate_code(prefixes, suffix_length):
    """
    Internal function to generate a single game code without uniqueness check
    """
    # Choose random prefix
    prefix = random.choice(prefixes)

    # Determine suffix length
    if suffix_length is None:
        length = random.randint(MIN_SUFFIX_LENGTH, MAX_SUFFIX_LENGTH)
    else:
        length = max(MIN_SUFFIX_LENGTH, min(suffix_length, MAX_SUFFIX_LENGTH))

    # Generate random suffix
    suffix = ''.join(random.choices(SUFFIX_CHARS, k=length))

    return f"{prefix}{suffix}"


def validate_game_code_format(code: str) -> bool:
    """
    Validate if a string matches the expected game code format
    """
    if not code or not isinstance(code, str):
        return False
    
    # Check total length
    if len(code) < 6 or len(code) > 10:
        return False
    
    # Check if starts with valid prefix
    code_upper = code.upper()
    has_valid_prefix = any(code_upper.startswith(prefix) for prefix in PREFIXES)
    
    if not has_valid_prefix:
        return False
    
    # Extract suffix and validate
    for prefix in PREFIXES:
        if code_upper.startswith(prefix):
            suffix = code[len(prefix):]
            
            # Check suffix length
            if len(suffix) < MIN_SUFFIX_LENGTH or len(suffix) > MAX_SUFFIX_LENGTH:
                return False
            
            # Check suffix contains only allowed characters
            if not all(c in SUFFIX_CHARS for c in suffix.upper()):
                return False
            
            return True
    
    return False

    
