# Intellectual Property Considerations

## JP2Forge and Intellectual Property

JP2Forge is designed with careful consideration for intellectual property rights, particularly with respect to the JPEG2000 standard implementation and the BnF technical specifications.

### Project Implementation

1. **Independent Implementation**: JP2Forge is an original implementation of functionality to generate JPEG2000 files according to BnF specifications. The codebase does not reuse, derive from, or incorporate code from other JPEG2000 libraries such as OpenJPEG, JasPer, or similar implementations.

2. **Underlying Libraries**: For actual JPEG2000 encoding/decoding:
   - We primarily use Pillow, a permissively licensed Python imaging library
   - Optionally, users can integrate with Kakadu (which must be separately licensed and installed)

3. **BnF Specifications**: Our implementation follows the technical specifications published by the Bibliothèque nationale de France (BnF) in their document "Référentiel de format de fichier image v2" (2015). These specifications describe technical requirements for JPEG2000 files but do not contain actual code.

### Third-Party Software

#### Pillow
- Pillow is used under its permissive HPND/PIL License
- JP2Forge does not modify Pillow's source code
- JP2Forge includes proper attribution for Pillow in requirements and documentation

#### Kakadu (Optional)
- Kakadu is a commercial JPEG2000 implementation that is NOT included with JP2Forge
- Users must separately acquire, license, and install Kakadu software
- JP2Forge only provides an interface to use Kakadu if the user has it installed
- No Kakadu code, binaries, or proprietary assets are distributed with JP2Forge

#### OpenJPEG
- JP2Forge does NOT use, incorporate, or derive from OpenJPEG's code
- Both JP2Forge (MIT) and OpenJPEG (BSD 2-Clause) use permissive licenses that would be compatible if integrations were needed in the future
- Users are free to use OpenJPEG as an alternative JPEG2000 implementation outside of JP2Forge

### JPEG2000 Standard

The JPEG2000 image compression standard (ISO/IEC 15444) itself is an open standard. However, specific implementations of the standard may be subject to patents or other intellectual property restrictions. JP2Forge implements functionality to create JPEG2000 files according to this standard using established libraries (Pillow or optionally Kakadu) rather than implementing the compression algorithms directly.

## License and Copyright Information

JP2Forge is released under the MIT License, which permits commercial and private use, modification, and distribution with minimal restrictions beyond maintaining copyright notices.

### Specific IP Clarifications

- **BnF Specifications**: The technical specifications from BnF remain their intellectual property. JP2Forge implements these specifications but does not claim ownership over them.

- **JPEG2000 Standard**: JP2Forge does not claim any rights over the JPEG2000 standard itself, which is maintained by ISO/IEC.

- **Metadata Formats**: XMP and other metadata standards implemented in JP2Forge are industry standards that JP2Forge implements but does not claim ownership over.

## Compliance Recommendations

When using JP2Forge, we recommend:

1. If redistributing JP2Forge as part of your project, maintain the original LICENSE file and copyright notices.

2. If using JP2Forge with Kakadu integration, ensure you have properly licensed Kakadu according to their terms.

3. Do not remove or alter the acknowledgments of BnF specifications or other attributions in the codebase.
