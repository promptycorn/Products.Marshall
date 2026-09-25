"""ATXML and binary export contracts independent of a site profile."""
import binascii
from io import BytesIO
from types import SimpleNamespace
import unittest
from xml.etree.ElementTree import ParseError
from zipfile import ZipFile

from Products.Archetypes.public import BaseObject, ObjectField, Schema
from Products.Archetypes.ClassGen import generateMethods
from Products.Marshall import config
from Products.Marshall.export import Export
from Products.Marshall.handlers.atxml import ATXMLMarshaller
from Products.Marshall.namespaces.uuns import UUAttribute


class Content(BaseObject):
    schema = Schema((ObjectField('payload'),))


generateMethods(Content, Content.schema.fields())


class ATXMLBoundaryTests(unittest.TestCase):
    def test_binary_protocol_preserves_blob_payload(self):
        class BinaryValue:
            mimetype = 'application/octet-stream'

            def __bytes__(self):
                return bytes(range(256))

            def __str__(self):
                raise AssertionError('Binary values must not be coerced to text')

        source, target = Content('source'), Content('target')
        source.setPayload(BinaryValue())
        marshaller = ATXMLMarshaller()
        _, _, data = marshaller.marshall(source, use_namespaces=[config.AT_NS])
        marshaller.demarshall(target, data)
        self.assertEqual(target.getPayload(), bytes(range(256)))

    def test_roundtrip_text_empty_whitespace_binary_and_control_chars(self):
        marshaller = ATXMLMarshaller()
        for value in ('ASCII', 'Grün 日本', '', '  text\n\t ',
                      'Grün\x00日本', b'', bytes(range(256))):
            with self.subTest(value=value):
                source, target = Content('source'), Content('target')
                source.setPayload(value)
                content_type, length, data = marshaller.marshall(
                    source, use_namespaces=[config.AT_NS])
                self.assertEqual(content_type, 'text/xml')
                self.assertIsInstance(data, bytes)
                self.assertEqual(length, len(data))
                marshaller.demarshall(target, data)
                self.assertEqual(target.getPayload(), value)

    def test_old_base64_document_remains_readable(self):
        source = ('<metadata xmlns="%s"><field name="payload" '
                  'transfer_encoding="base64">AP8=\n</field></metadata>'
                  % config.AT_NS).encode()
        target = Content('target')
        ATXMLMarshaller().demarshall(target, source)
        self.assertEqual(target.getPayload(), b'\x00\xff')

    def test_invalid_xml_is_rejected(self):
        with self.assertRaises(ParseError):
            ATXMLMarshaller().demarshall(Content('target'), b'<metadata>')

    def test_invalid_base64_is_rejected(self):
        source = ('<metadata xmlns="%s"><field name="payload" '
                  'transfer_encoding="base64">%%%s</field></metadata>'
                  % (config.AT_NS, '%%')).encode()
        with self.assertRaises(binascii.Error):
            ATXMLMarshaller().demarshall(Content('target'), source)

    def test_uu_and_base64_binary_roundtrip(self):
        attribute = UUAttribute('payload')
        for value in (b'', b'ASCII', bytes(range(256))):
            self.assertEqual(attribute.uudecode(attribute.uuencode(value)), value)
            self.assertEqual(attribute.base64decode(attribute.base64encode(value)), value)

    def test_export_marshalling_preserves_bytes_and_utf8_text(self):
        obj = SimpleNamespace(REQUEST=SimpleNamespace(RESPONSE=object()))
        for value in (b'', bytes(range(256)), 'Grün 日本'):
            marshaller = SimpleNamespace(marshall=lambda *a, **kw: ('text/plain', 0, value))
            result = Export().marshall(obj, marshaller).read()
            self.assertEqual(result, value.encode() if isinstance(value, str) else value)

    def test_zip_contains_original_binary_and_metadata(self):
        class FixtureExport(Export):
            def marshall_data(self, obj):
                return BytesIO(b'\x00\xff')

            def marshall_metadata(self, obj):
                return BytesIO('<metadata>Grün</metadata>'.encode())

        context = SimpleNamespace(restrictedTraverse=lambda path: object())
        result = FixtureExport().export(context, ['Grün/日本.dat'])
        with ZipFile(result) as archive:
            self.assertEqual(archive.read('Grün/日本.dat'), b'\x00\xff')
            self.assertEqual(archive.read('Grün/.metadata/日本.dat'),
                             '<metadata>Grün</metadata>'.encode())
