# Test Images for JP2Forge

## License Information

The test images in this directory are licensed under Creative Commons Attribution 4.0 International License (CC BY 4.0), which allows for:
- Sharing, copying and redistribution
- Adaptation and transformation
- Commercial use

When using these images in publications or presentations, please provide appropriate attribution to the original creators.

## Image Attribution

Here are example CC 4.0 licensed images you can use (replace with your actual chosen images):

- `cc_test_image_01.tif`: "Mountain Landscape" by John Smith (CC BY 4.0) from [source URL]
- `cc_test_image_02.tif`: "Coastal Sunset" by Jane Doe (CC BY 4.0) from [source URL]
- `cc_test_image_03.tif`: "Urban Architecture" by Alex Johnson (CC BY 4.0) from [source URL]

## Test Image Organization

The images are organized into subdirectories based on size:
- `small/`: Images less than 2MP
- `medium/`: Images between 2-10MP 
- `large/`: Images between 10-50MP

## Usage

These images are used for testing and benchmarking the JP2Forge library. They provide a standard set of inputs for reproducible performance evaluation.

## For Publishing

These CC 4.0 licensed images can be safely included in published repositories, documentation, and benchmark reports, provided proper attribution is maintained.

## Restricted Images

For development purposes, you may include additional non-CC licensed images in your local copy:

1. Place these images in the same directory structure
2. Do not commit these images to the repository
3. The `.gitignore` file is configured to prevent accidental commits of files not matching the CC sample pattern

## How to Add New CC 4.0 Images

To replace the placeholder images with actual CC 4.0 licensed images:

1. Find suitable CC BY 4.0 licensed images
2. Download and name them according to the convention (cc_test_image_XX.tif)
3. Place them in the appropriate size directory
4. Update this README with proper attribution information including:
   - Image title
   - Creator name
   - License (CC BY 4.0)
   - Source URL

## Converting Image Formats

If your CC 4.0 images are not in TIFF format:

1. Convert them using a tool like ImageMagick:
   ```
   convert source_image.jpg cc_test_image_01.tif
   ```
2. Ensure conversion preserves the image quality and metadata
3. Document any conversion steps in your development notes
