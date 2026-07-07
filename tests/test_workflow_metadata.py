"""Workflow-level tests: supervised metrics and XMP metadata embedding.

These exercise the full StandardWorkflow pipeline and therefore require
ExifTool; they are skipped when it is not installed.
"""

import shutil

import pytest

from core.types import CompressionMode, DocumentType, WorkflowConfig, WorkflowStatus
from workflow.standard import StandardWorkflow

requires_exiftool = pytest.mark.skipif(
    shutil.which("exiftool") is None,
    reason="ExifTool is required for metadata embedding",
)

# Standard JP2 XMP UUID box identifier (also the BnF-required UUID)
XMP_UUID = bytes.fromhex("BE7ACFCB97A942E89C71999491E3AFAC")


def make_workflow(tmp_path, **overrides):
    config = WorkflowConfig(
        output_dir=str(tmp_path / "output"),
        report_dir=str(tmp_path / "reports"),
        document_type=DocumentType.PHOTOGRAPH,
        num_resolutions=6,
        **overrides,
    )
    return StandardWorkflow(config)


@requires_exiftool
class TestStandardMetadata:
    def test_supervised_run_embeds_xmp(self, photo_tif, tmp_path):
        workflow = make_workflow(
            tmp_path, compression_mode=CompressionMode.SUPERVISED)
        result = workflow.process_file(photo_tif)

        assert result.status in (WorkflowStatus.SUCCESS, WorkflowStatus.WARNING)
        assert result.error is None
        assert result.metrics is not None
        for key in ("psnr", "ssim", "mse", "quality_passed"):
            assert key in result.metrics

        data = open(result.output_file, "rb").read()
        # XMP was previously written to a JSON sidecar, never into the JP2
        assert XMP_UUID in data
        assert b"W5M0MpCehiHzreSzNTczkc9d" in data  # xpacket id

    def test_no_sidecar_files(self, photo_tif, tmp_path):
        workflow = make_workflow(
            tmp_path, compression_mode=CompressionMode.SUPERVISED)
        result = workflow.process_file(photo_tif)
        sidecars = list((tmp_path / "output").glob("*.xmp"))
        assert result.output_file
        assert sidecars == []


@requires_exiftool
class TestBnFMetadata:
    def test_bnf_run_embeds_dcterms(self, photo_tif, tmp_path):
        workflow = make_workflow(
            tmp_path,
            compression_mode=CompressionMode.BNF_COMPLIANT,
            bnf_compliant=True,
        )
        result = workflow.process_file(photo_tif)

        assert result.status in (WorkflowStatus.SUCCESS, WorkflowStatus.WARNING)
        assert result.error is None

        data = open(result.output_file, "rb").read()
        assert XMP_UUID in data
        assert b"isPartOf" in data
        assert "Bibliothèque nationale de France".encode() in data

    def test_bnf_metadata_override(self, photo_tif, tmp_path):
        workflow = make_workflow(
            tmp_path,
            compression_mode=CompressionMode.BNF_COMPLIANT,
            bnf_compliant=True,
        )
        result = workflow.process_file(
            photo_tif, metadata={"dcterms:isPartOf": "NUM_CUSTOM_042"})
        data = open(result.output_file, "rb").read()
        assert b"NUM_CUSTOM_042" in data
