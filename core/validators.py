from pathlib import Path

from django.core.exceptions import ValidationError


MAX_EVIDENCE_SIZE = 5 * 1024 * 1024
EVIDENCE_SIGNATURES = {
    '.jpg': lambda header: header.startswith(b'\xff\xd8\xff'),
    '.jpeg': lambda header: header.startswith(b'\xff\xd8\xff'),
    '.png': lambda header: header.startswith(b'\x89PNG\r\n\x1a\n'),
    '.webp': lambda header: (
        header.startswith(b'RIFF') and header[8:12] == b'WEBP'
    ),
    '.pdf': lambda header: header.startswith(b'%PDF-'),
}


def validate_evidence_file(uploaded_file):
    if uploaded_file.size > MAX_EVIDENCE_SIZE:
        raise ValidationError('Evidence files must be 5 MB or smaller.')

    extension = Path(uploaded_file.name).suffix.lower()
    signature_check = EVIDENCE_SIGNATURES.get(extension)
    if signature_check is None:
        raise ValidationError(
            'Upload evidence as a JPG, PNG, WEBP, or PDF file.'
        )

    try:
        uploaded_file.seek(0)
        header = uploaded_file.read(12)
    finally:
        uploaded_file.seek(0)

    if not signature_check(header):
        raise ValidationError(
            'The file contents do not match the selected evidence file type.'
        )
