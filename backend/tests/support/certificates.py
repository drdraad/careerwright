"""Throwaway test certificates for the fetcher's proxy mode: a CA and a certificate it signs for
one name, valid for a day either side of now. Generated per test; never a real identity."""

import datetime
from dataclasses import dataclass
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID


@dataclass(frozen=True)
class ThrowawayCa:
    key: ec.EllipticCurvePrivateKey
    cert: x509.Certificate

    @property
    def pem(self) -> bytes:
        return self.cert.public_bytes(serialization.Encoding.PEM)

    def bundle(self, path: Path) -> Path:
        path.write_bytes(self.pem)
        return path


def _validity(builder: x509.CertificateBuilder) -> x509.CertificateBuilder:
    now = datetime.datetime.now(datetime.UTC)
    return (
        builder.serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=1))
    )


def make_ca() -> ThrowawayCa:
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Careerwright test CA")])
    usage = x509.KeyUsage(
        digital_signature=True,
        content_commitment=False,
        key_encipherment=False,
        data_encipherment=False,
        key_agreement=False,
        key_cert_sign=True,
        crl_sign=True,
        encipher_only=False,
        decipher_only=False,
    )
    cert = (
        _validity(x509.CertificateBuilder().subject_name(name).issuer_name(name))
        .public_key(key.public_key())
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(usage, critical=True)
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), critical=False)
        .sign(key, hashes.SHA256())
    )
    return ThrowawayCa(key, cert)


def make_leaf(ca: ThrowawayCa, host: str, directory: Path) -> tuple[Path, Path]:
    """A certificate for `host` signed by `ca`, and its key, written as PEM files."""
    key = ec.generate_private_key(ec.SECP256R1())
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, host)])
    cert = (
        _validity(x509.CertificateBuilder().subject_name(subject).issuer_name(ca.cert.subject))
        .public_key(key.public_key())
        .add_extension(x509.SubjectAlternativeName([x509.DNSName(host)]), critical=False)
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(ca.key.public_key()),
            critical=False,
        )
        .sign(ca.key, hashes.SHA256())
    )
    cert_path, key_path = directory / "leaf.pem", directory / "leaf.key"
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    return cert_path, key_path
