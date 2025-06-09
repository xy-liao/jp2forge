# JP2Forge BnF Compliance

This document details JP2Forge's support for BnF (Bibliothèque nationale de France) compliance standards for JPEG2000 conversion.

## Table of Contents

1. [Overview](#1-overview)
2. [BnF Standards](#2-bnf-standards)
3. [Compression Parameters](#3-compression-parameters)
4. [Metadata Requirements](#4-metadata-requirements)
5. [Usage](#5-usage)
6. [Validation](#6-validation)
7. [Notation Conventions](#7-notation-conventions)

## 1. Overview

The BnF (Bibliothèque nationale de France) has established technical specifications for JPEG2000 conversion to ensure long-term preservation and interoperability of digital images. JP2Forge implements these specifications to support archival-quality digitization workflows.

### Key BnF Requirements

- Fixed compression ratios based on document type
- Specific JPEG2000 encoding parameters
- XMP metadata in UUID box format
- Quality control and fallback mechanisms
- Robustness markers for error recovery

## 2. BnF Standards

### Document Classification

The BnF defines different document types with specific compression requirements:

| Document Type | BnF Category | Compression Ratio | Use Case |
|---------------|--------------|-------------------|----------|
| Specialized Documents | Documents « spécialisé » | 1:4 | Prints, photographs, glass plates |
| Exceptional Documents | Documents « exceptionnel » | 1:4 | Manuscripts with illuminations |
| Printed Documents | Documents « imprimé » | 1:6 | Standard printed materials |
| Transparent Documents | Documents « transparent » | 1:16 | Grayscale transparent materials |

### Quality Control

- **Compression Ratio Tolerance**: 5% (configurable)
- **Fallback Mechanism**: Lossless compression if ratio tolerance exceeded
- **Quality Validation**: PSNR, SSIM, and MSE metrics

## 3. Compression Parameters

### JPEG2000 Encoding Parameters

When using BnF compliance mode, JP2Forge applies these technical parameters:

```yaml
Compression Type: Irreversible (lossy)
Wavelet Transform: 9-7 floating point
Color Transform: ICT (Irreversible Component Transform)
Resolution Levels: 10
Quality Levels: 10
Progression Order: RPCL (Resolution-Position-Component-Layer)
Code Block Size: 64x64 pixels
Tile Size: 1024x1024 pixels
Precinct Size: {256,256}, {256,256}, {128,128}
```

### Robustness Markers

BnF specifications require specific markers for error recovery:

- **SOP**: Start Of Packet markers
- **EPH**: End of Packet Header markers
- **PLT**: Packet Length markers in tile-part header

### Fallback to Lossless

If the target compression ratio cannot be achieved within tolerance:

```yaml
Compression Type: Reversible (lossless)
Wavelet Transform: 5-3 integer
Color Transform: RCT (Reversible Component Transform)
```

## 4. Metadata Requirements

### Required XMP Fields

BnF compliance requires specific XMP metadata fields embedded in a UUID box:

#### Dublin Core Terms (dcterms)

- **dcterms:isPartOf**: Document identifier
  - Format: "NUM_XXXXXX" or "IFN_XXXXXX"
  - Example: "NUM_123456"

- **dcterms:provenance**: Document owner
  - Default: "Bibliothèque nationale de France"
  - Can include partner institutions

#### Dublin Core (dc)

- **dc:relation**: ARK identifier
  - Format: "ark:/12148/cbXXXXXXXXX"
  - Example: "ark:/12148/cb123456789"

- **dc:source**: Original document call number
  - Example: "FOL-Z-123"

#### Technical Metadata

- **tiff:Model**: Scanning equipment model
- **tiff:Make**: Equipment manufacturer
- **aux:SerialNumber**: Equipment serial number
- **xmp:CreatorTool**: Software used for digitization
- **xmp:CreateDate**: File creation date (ISO-8601)
- **xmp:ModifyDate**: Last modification date (ISO-8601)
- **tiff:Artist**: Digitization operator

### XMP Structure

The metadata is embedded in a UUID box with identifier:
`BE7ACFCB97A942E89C71999491E3AFAC`

Example XMP structure:

```xml
<?xpacket begin="ufeff" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
 <rdf:Description
 xmlns:xmp="http://ns.adobe.com/xap/1.0/"
 xmlns:tiff="http://ns.adobe.com/tiff/1.0/"
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 xmlns:dcterms="http://purl.org/dc/terms/"
 xmlns:aux="http://ns.adobe.com/exif/1.0/aux/"
 rdf:about=""
 tiff:Model="Scanner Model"
 tiff:Make="Scanner Manufacturer"
 tiff:Artist="Operator Name"
 aux:SerialNumber="123456789"
 xmp:CreatorTool="JP2Forge"
 xmp:CreateDate="2023-05-25T12:00:00Z"
 xmp:ModifyDate="2023-05-25T12:00:00Z">
 <dcterms:isPartOf>
  <rdf:Bag>
   <rdf:li>NUM_123456</rdf:li>
  </rdf:Bag>
 </dcterms:isPartOf>
 <dcterms:provenance>
  <rdf:Bag>
   <rdf:li>Bibliothèque nationale de France</rdf:li>
  </rdf:Bag>
 </dcterms:provenance>
 <dc:relation>
  <rdf:Bag>
   <rdf:li>ark:/12148/cb123456789</rdf:li>
  </rdf:Bag>
 </dc:relation>
 <dc:source>
  <rdf:Bag>
   <rdf:li>FOL-Z-123</rdf:li>
  </rdf:Bag>
 </dc:source>
 </rdf:Description>
</rdf:RDF>
</x:xmpmeta>
<?xpacket end="r"?>
```

## 5. Usage

### Basic BnF Compliance

Enable BnF compliance mode:

```bash
python -m cli.workflow input_dir/ output_dir/ --bnf-compliant
```

### Specify Document Type

Set appropriate document type for correct compression ratio:

```bash
# For photographs (1:4 ratio)
python -m cli.workflow input_dir/ output_dir/ \
  --bnf-compliant \
  --document-type photograph

# For printed documents (1:6 ratio)
python -m cli.workflow input_dir/ output_dir/ \
  --bnf-compliant \
  --document-type color

# For grayscale documents (1:16 ratio)
python -m cli.workflow input_dir/ output_dir/ \
  --bnf-compliant \
  --document-type grayscale
```

### Custom Compression Tolerance

Adjust compression ratio tolerance:

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --bnf-compliant \
  --compression-ratio-tolerance 0.03  # 3% tolerance
```

### With Metadata File

Provide BnF-compliant metadata:

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --bnf-compliant \
  --metadata-file bnf_metadata.json
```

Example `bnf_metadata.json`:

```json
{
  "dcterms:isPartOf": "NUM_123456",
  "dcterms:provenance": "Bibliothèque nationale de France",
  "dc:relation": "ark:/12148/cb123456789",
  "dc:source": "FOL-Z-123",
  "tiff:Model": "Phase One P45+",
  "tiff:Make": "Phase One",
  "aux:SerialNumber": "1234567890",
  "xmp:CreatorTool": "JP2Forge",
  "tiff:Artist": "Digital Imaging Specialist"
}
```

### Using Kakadu for Strict Compliance

For maximum BnF compliance, use Kakadu:

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --bnf-compliant \
  --use-kakadu \
  --kakadu-path /path/to/kdu_compress
```

### API Usage

```python
from core.types import WorkflowConfig, DocumentType, CompressionMode
from core.metadata import get_metadata_handler
from workflow.standard import StandardWorkflow

# Create BnF metadata
bnf_handler = get_metadata_handler(bnf_compliant=True)
metadata = bnf_handler.create_bnf_compliant_metadata(
    identifiant="NUM_123456",
    provenance="Bibliothèque nationale de France",
    ark_identifiant="ark:/12148/cb123456789",
    cote="FOL-Z-123",
    scanner_model="Phase One P45+",
    scanner_make="Phase One",
    serial_number="1234567890",
    operator="Digital Imaging Specialist"
)

# Configure for BnF compliance
config = WorkflowConfig(
    output_dir="output/",
    report_dir="reports/",
    document_type=DocumentType.PHOTOGRAPH,
    compression_mode=CompressionMode.BNF_COMPLIANT,
    bnf_compliant=True,
    compression_ratio_tolerance=0.05,
    include_bnf_markers=True
)

# Process files
workflow = StandardWorkflow(config)
result = workflow.process_file("input.tif", metadata=metadata)
```

## 6. Validation

### Automatic Validation

JP2Forge automatically validates BnF compliance:

- Compression ratio verification
- Metadata completeness check
- JPEG2000 parameter validation
- Quality metrics analysis

### Using JPylyzer

JP2Forge integrates with JPylyzer for comprehensive validation:

```bash
# JPylyzer validation is automatically run after processing
python -m cli.workflow input_dir/ output_dir/ --bnf-compliant
```

Results are saved in the reports directory as `info_jpylyzer.json`.

### Manual Validation

Validate existing JP2 files:

```python
from core.metadata.bnf_handler import BnFMetadataHandler

bnf_handler = BnFMetadataHandler()
is_compliant, issues = bnf_handler.validate_bnf_compliance("file.jp2")

if is_compliant:
    print("File is BnF compliant")
else:
    print("Issues found:")
    for issue in issues:
        print(f"- {issue}")
```

## 7. Notation Conventions

### Compression Ratio Notation

**Important**: BnF documentation and JP2Forge use different notation conventions:

| Format | BnF Notation | JP2Forge Notation | Meaning |
|--------|--------------|-------------------|---------|
| Specialized | 1:4 | 4.0 or 4:1 | Original is 4x larger than compressed |
| Printed | 1:6 | 6.0 or 6:1 | Original is 6x larger than compressed |
| Transparent | 1:16 | 16.0 or 16:1 | Original is 16x larger than compressed |

**BnF Notation**: "1:4" means "1 part compressed to 4 parts original"
**JP2Forge Notation**: "4.0" means "4 parts original to 1 part compressed"

Both represent the same compression ratio, just expressed differently.

### Example Calculations

For a 100MB original file:
- BnF 1:4 ratio = JP2Forge 4:1 ratio = 25MB compressed file
- BnF 1:6 ratio = JP2Forge 6:1 ratio = 16.7MB compressed file
- BnF 1:16 ratio = JP2Forge 16:1 ratio = 6.25MB compressed file

## Reference Documents

JP2Forge's BnF compliance is based on these official documents:

1. **BnF Referential (2015)**: "Référentiel de format de fichier image v2"
   - [PDF Link](https://www.bnf.fr/sites/default/files/2018-11/ref_num_fichier_image_v2.pdf)

2. **BnF Documentation (2021)**: "Formats de données pour la préservation à long terme"
   - [PDF Link](https://www.bnf.fr/sites/default/files/2021-04/politiqueFormatsDePreservationBNF_20210408.pdf)

These documents provide the technical specifications that JP2Forge implements for BnF-compliant JPEG2000 conversion.
