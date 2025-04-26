"""
Color profile handling utilities for JPEG2000 workflow.

This module provides utilities for handling color profiles and 
color space conversions for JPEG2000 images.
"""

import os
import logging
import io
from typing import Optional, Tuple, Dict, Any, Union
from PIL import Image, ImageCms

logger = logging.getLogger(__name__)

# Common color profiles
SRGB_PROFILE = None
GRAY_PROFILE = None

# Try to find standard profiles
PROFILE_PATHS = [
    # Standard locations for ICC profiles
    "/usr/share/color/icc",
    "/usr/local/share/color/icc",
    "/Library/ColorSync/Profiles",
    "/System/Library/ColorSync/Profiles",
    os.path.expanduser("~/Library/ColorSync/Profiles"),
]

def initialize_profiles():
    """Initialize standard ICC profiles."""
    global SRGB_PROFILE, GRAY_PROFILE
    
    if SRGB_PROFILE is not None and GRAY_PROFILE is not None:
        return
    
    # Try to find profiles in common locations
    for profile_dir in PROFILE_PATHS:
        if not os.path.isdir(profile_dir):
            continue
            
        # Look for sRGB profile
        for filename in os.listdir(profile_dir):
            filepath = os.path.join(profile_dir, filename)
            if SRGB_PROFILE is None and "srgb" in filename.lower():
                try:
                    SRGB_PROFILE = ImageCms.getOpenProfile(filepath)
                    logger.debug(f"Found sRGB profile at {filepath}")
                except Exception:
                    pass
                    
            if GRAY_PROFILE is None and "gray" in filename.lower():
                try:
                    GRAY_PROFILE = ImageCms.getOpenProfile(filepath)
                    logger.debug(f"Found Gray profile at {filepath}")
                except Exception:
                    pass
    
    # If profiles couldn't be found, we'll use internal defaults
    if SRGB_PROFILE is None:
        logger.warning("No sRGB profile found, using default")
        SRGB_PROFILE = ImageCms.createProfile("sRGB")
        
    if GRAY_PROFILE is None:
        logger.warning("No Gray profile found, using default")
        GRAY_PROFILE = ImageCms.createProfile("Gray")


def get_embedded_icc_profile(image: Image.Image) -> Optional[bytes]:
    """
    Get embedded ICC profile from an image.
    
    Args:
        image: PIL Image object
        
    Returns:
        bytes: ICC profile data or None if not found
    """
    try:
        return image.info.get('icc_profile')
    except Exception as e:
        logger.warning(f"Error getting ICC profile: {str(e)}")
        return None


def get_profile_bytes(profile) -> bytes:
    """
    Get bytes representation of an ICC profile, compatible with different Pillow versions.
    
    Args:
        profile: ICC profile object from ImageCms
        
    Returns:
        bytes: Profile data
    """
    try:
        # Modern Pillow: Try to get the raw profile data directly from profile object
        if hasattr(profile, 'tobytes'):
            return profile.tobytes()
        
        # For Pillow versions with profile_tobytes
        elif hasattr(ImageCms, 'profile_tobytes'):
            return ImageCms.profile_tobytes(profile)
            
        # For very old Pillow versions (fallback)
        elif hasattr(ImageCms, 'getProfileString'):
            return ImageCms.getProfileString(profile)
            
        # Last resort - generate a simple profile
        else:
            logger.warning("Could not convert profile to bytes using available methods")
            if hasattr(ImageCms, 'createProfile'):
                # Try recreating profile and extracting bytes
                mode = ImageCms.getProfileName(profile).lower()
                if 'rgb' in mode:
                    new_profile = ImageCms.createProfile('sRGB')
                    if hasattr(new_profile, 'tobytes'):
                        return new_profile.tobytes()
                elif 'gray' in mode:
                    new_profile = ImageCms.createProfile('Gray')
                    if hasattr(new_profile, 'tobytes'):
                        return new_profile.tobytes()
                        
            # If all else fails, return None safely
            return None
            
    except Exception as e:
        logger.warning(f"Error converting profile to bytes: {str(e)}")
        return None


def normalize_colorspace(image: Image.Image) -> Tuple[Image.Image, Optional[bytes]]:
    """
    Normalize image colorspace for JPEG2000 processing.
    
    JP2000 works best with standard RGB and grayscale color spaces.
    This function converts unusual color spaces to sRGB or gray
    and returns the original ICC profile for later embedding.
    
    Args:
        image: PIL Image object
        
    Returns:
        tuple: (normalized image, original ICC profile data)
    """
    # Initialize profiles if needed
    initialize_profiles()
    
    # Get original ICC profile
    original_profile = get_embedded_icc_profile(image)
    
    try:
        mode = image.mode
        
        # Handle different color modes
        if mode in ['RGB', 'RGBA']:
            # RGB modes are fine, but ensure sRGB profile if not specified
            if original_profile is None:
                return image, None
                
            # If profile exists, validate it and convert if needed
            try:
                # Test if profile is valid
                src_profile = ImageCms.getOpenProfile(io.BytesIO(original_profile))
                # Check if profile is RGB type
                if ImageCms.getProfileInfo(src_profile).lower().find('rgb') >= 0:
                    # Profile is valid and RGB, we can use it
                    return image, original_profile
                else:
                    # Profile is not RGB, convert to sRGB
                    logger.info("Converting non-RGB profile to sRGB")
                    try:
                        transform = ImageCms.buildTransform(
                            src_profile, SRGB_PROFILE, 
                            mode, mode, 
                            ImageCms.INTENT_RELATIVE_COLORIMETRIC
                        )
                        converted = ImageCms.applyTransform(image, transform)
                        return converted, get_profile_bytes(SRGB_PROFILE)
                    except Exception as e:
                        logger.warning(f"Failed to convert profile: {str(e)}")
                        return image, original_profile
            except Exception as e:
                logger.warning(f"Invalid ICC profile, defaulting to sRGB: {str(e)}")
                return image, None
                
        elif mode in ['L', 'LA']:
            # Grayscale modes are fine
            return image, original_profile
            
        elif mode == 'P':
            # Palette mode, convert to RGB
            logger.info("Converting palette image to RGB")
            converted = image.convert('RGB')
            return converted, None
            
        elif mode == 'CMYK':
            # CMYK mode, convert to RGB
            logger.info("Converting CMYK image to RGB")
            if original_profile:
                try:
                    # Try to use embedded profile for conversion
                    src_profile = ImageCms.getOpenProfile(io.BytesIO(original_profile))
                    transform = ImageCms.buildTransform(
                        src_profile, SRGB_PROFILE, 
                        'CMYK', 'RGB', 
                        ImageCms.INTENT_RELATIVE_COLORIMETRIC
                    )
                    converted = ImageCms.applyTransform(image, transform)
                    return converted, get_profile_bytes(SRGB_PROFILE)
                except Exception as e:
                    logger.warning(f"Failed to convert CMYK with profile: {str(e)}")
            
            # Fallback to Pillow's conversion
            converted = image.convert('RGB')
            return converted, None
            
        elif mode in ['I', 'F']:
            # 32-bit integer or float modes, convert to RGB or L depending on bands
            if len(image.getbands()) == 1:
                logger.info(f"Converting {mode} image to L")
                converted = image.convert('L')
                return converted, None
            else:
                logger.info(f"Converting {mode} image to RGB")
                converted = image.convert('RGB')
                return converted, None
                
        else:
            # Other modes, try generic conversion to RGB
            logger.warning(f"Unsupported mode {mode}, attempting conversion to RGB")
            try:
                converted = image.convert('RGB')
                return converted, None
            except Exception as e:
                logger.error(f"Failed to convert image mode {mode}: {str(e)}")
                # Return original as last resort
                return image, original_profile
    
    except Exception as e:
        logger.error(f"Error normalizing colorspace: {str(e)}")
        return image, original_profile


def ensure_jp2_compatible_profile(image: Image.Image) -> Image.Image:
    """
    Ensure image has a color profile compatible with JPEG2000.
    
    Args:
        image: PIL Image object
        
    Returns:
        Image.Image: Image with compatible color profile
    """
    try:
        # Normalize colorspace first
        normalized_img, original_profile = normalize_colorspace(image)
        
        # Handle profile embedding for JP2
        if normalized_img.mode in ['RGB', 'RGBA'] and not original_profile:
            # Embed sRGB profile if no profile
            initialize_profiles()
            profile_data = get_profile_bytes(SRGB_PROFILE)
            if profile_data:
                normalized_img.info['icc_profile'] = profile_data
            
        elif normalized_img.mode in ['L', 'LA'] and not original_profile:
            # Embed Gray profile if no profile
            initialize_profiles()
            profile_data = get_profile_bytes(GRAY_PROFILE)
            if profile_data:
                normalized_img.info['icc_profile'] = profile_data
            
        return normalized_img
        
    except Exception as e:
        logger.error(f"Error ensuring JP2 compatible profile: {str(e)}")
        return image


def detect_image_colorspace(image: Image.Image) -> Dict[str, Any]:
    """
    Detect and return information about image colorspace.
    
    Args:
        image: PIL Image object
        
    Returns:
        dict: Information about the image colorspace
    """
    result = {
        "mode": image.mode,
        "bands": image.getbands(),
        "has_alpha": image.mode in ['RGBA', 'LA'],
        "is_grayscale": image.mode in ['L', 'LA', '1'],
        "has_icc_profile": False,
        "profile_type": None,
        "profile_description": None
    }
    
    # Check for ICC profile
    icc_profile = get_embedded_icc_profile(image)
    if icc_profile:
        result["has_icc_profile"] = True
        try:
            profile = ImageCms.getOpenProfile(io.BytesIO(icc_profile))
            info = ImageCms.getProfileInfo(profile)
            result["profile_description"] = info
            
            # Try to detect profile type
            info_lower = info.lower()
            if "rgb" in info_lower:
                result["profile_type"] = "RGB"
            elif "gray" in info_lower:
                result["profile_type"] = "Gray"
            elif "cmyk" in info_lower:
                result["profile_type"] = "CMYK"
            else:
                result["profile_type"] = "Unknown"
        except Exception as e:
            result["profile_type"] = "Invalid"
            result["profile_error"] = str(e)
    
    return result
