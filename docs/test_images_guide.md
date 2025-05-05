# Test Images Guide for JP2Forge

## Overview

This document provides guidance on obtaining, using, and managing test images for JP2Forge development and benchmarking.

## Recommended Test Images

### CC 4.0 Licensed Images (Preferred for Publishing)

For public repositories, documentation, and published benchmarks, use only **Creative Commons Attribution 4.0 (CC BY 4.0)** licensed images. We recommend:

1. Three diverse test images covering typical use cases:
   - A detailed image with fine textures
   - An image with smooth gradients and solid areas
   - An image with text or sharp edges

2. Images in different size categories:
   - Small: < 2MP
   - Medium: 2-10MP
   - Large: 10-50MP

3. The images should be stored as uncompressed TIFFs for consistent testing.

### Naming Convention

For CC 4.0 images:
- Use the prefix `cc_test_image_` followed by a number
- Example: `cc_test_image_01.tif`, `cc_test_image_02.tif`, etc.

## Benchmark Testing Procedure

1. **Standard Benchmark Setup**:
   - Each benchmark configuration should be tested with all three CC 4.0 images
   - Run each test at least twice (rep_1, rep_2) to account for system variability

2. **Directory Organization**:
   ```
   benchmark/
     output_dir/
       config_1_rep_1/
         cc_test_image_01.jp2
         cc_test_image_01.jp2.xmp
         // Additional output files
       config_1_rep_2/
         // Repeat with same images
       // Additional configurations
     results/
       // Generated benchmark charts and graphs
     reports/
       summary_report.md
   ```

3. **Metadata Requirements**:
   - All output JP2 files should preserve image metadata
   - Additional JP2-specific metadata should be added as per the project standards

## Using Personal Test Collections

Developers may use additional (non-CC) test images for personal development, but:

1. **Never commit** personal test images to the repository
2. Store personal test images in a separate directory not tracked by Git
3. Configure `.gitignore` to prevent accidental commits
4. For sharing results based on personal collections, describe the image characteristics rather than including the actual images

## Getting CC 4.0 Licensed Images

### Sources for CC 4.0 Images:

- [Wikimedia Commons](https://commons.wikimedia.org/wiki/Main_Page) (filter by CC BY 4.0)
- [Creative Commons Search](https://search.creativecommons.org/)
- [Flickr](https://www.flickr.com/creativecommons/) (filter by CC BY 4.0)
- [Unsplash](https://unsplash.com/) (check specific license terms)

### Verifying Licenses

Always verify the license by:
1. Checking the image metadata or description page
2. Documenting the source URL and creator information
3. Ensuring the license is specifically CC BY 4.0

## Image Preparation

1. **Conversion to TIFF**:
   ```bash
   convert source_image.jpg cc_test_image_01.tif
   ```

2. **Adding/Preserving Metadata**:
   ```bash
   exiftool -Artist="Original Creator Name" -Copyright="CC BY 4.0" cc_test_image_01.tif
   ```

3. **Resizing Images** (if needed for specific size categories):
   ```bash
   convert original.tif -resize 1024x768 cc_test_image_small_01.tif
   ```

## Updating the Image README

When adding new CC 4.0 images, update the `/images/README.md` file with:

1. Image filename
2. Original title
3. Creator name and source URL
4. Confirmation of CC BY 4.0 license

## Publishing Benchmark Results

When publishing benchmark results:

1. Include only results from CC 4.0 licensed images
2. Properly attribute all images used
3. Make the benchmark configurations reproducible
4. Consider providing download links to the original CC 4.0 images used

## Special Considerations for Automated Tests

For CI/CD pipelines and automated testing:
1. Package small CC 4.0 test images with the test suite
2. Use mock images for basic functionality tests
3. Provide a script to download full-size CC 4.0 test images for comprehensive testing