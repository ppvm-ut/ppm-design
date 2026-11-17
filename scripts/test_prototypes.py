import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_prototypes import collect, build

class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        (self.root/'prototypes').mkdir()
    def tearDown(self): self.tmp.cleanup()
    def page(self, name, text):
        p=self.root/'prototypes'/name
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(text)
    def test_catalog_entry_point_exists_without_service_page_cards(self):
        self.page('example/index.html', '<title>Example</title><meta name="prototype-kind" content="example">')
        self.page('flow.html', '<title>Flow</title>')
        records = build(self.root)
        html = (self.root / 'prototypes/index.html').read_text()
        self.assertEqual([record['path'] for record in records], ['flow.html'])
        self.assertIn('href="flow.html"', html)
        self.assertNotIn('href="example/index.html"', html)
        self.assertEqual(collect(self.root), records)

    def test_new_nested_html_is_discovered_and_catalog_excluded(self):
        self.page('index.html','<title>Catalog</title>')
        self.page('new-flow/index.html','<title>New flow</title><meta name="prototype-status" content="review">')
        data=collect(self.root)
        self.assertEqual(len(data),1)
        self.assertEqual(data[0]['url'],'new-flow/index.html')
        self.assertEqual(data[0]['status'],'review')
    def test_defaults_and_html_escape(self):
        self.page('a & b.html','<title>&lt;unsafe&gt;</title><meta name="description" content="&lt;script&gt;">')
        data=collect(self.root)
        self.assertEqual(data[0]['status'],'draft')
        self.assertEqual(data[0]['url'],'a%20%26%20b.html')
    def test_invalid_status_fails_publication(self):
        self.page('bad.html','<meta name="prototype-status" content="unknown">')
        with self.assertRaises(ValueError): collect(self.root)
    def test_unsafe_metadata_link_fails(self):
        self.page('bad.html','<meta name="prototype-task" content="javascript:alert(1)">')
        with self.assertRaises(ValueError): collect(self.root)
    def test_approved_requires_real_link_field(self):
        self.page('ready.html','<meta name="prototype-status" content="approved">')
        with self.assertRaises(ValueError): collect(self.root)
        self.page('ready.html','<meta name="prototype-status" content="approved"><meta name="prototype-approval" content="https://tracker.yandex.ru/PPT-123">')
        self.assertEqual(collect(self.root)[0]['status'],'approved')
    def test_symlinks_and_hidden_files_not_published_in_catalog(self):
        self.page('.hidden.html','<title>hidden</title>')
        (self.root/'outside.html').write_text('<title>outside</title>')
        (self.root/'prototypes/link.html').symlink_to(self.root/'outside.html')
        self.assertEqual(collect(self.root),[])

if __name__=='__main__': unittest.main()
