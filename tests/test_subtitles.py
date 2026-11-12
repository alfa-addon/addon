"""Offline checks: run with python -m unittest discover -s tests."""
import ast
import io
import os
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import traceback
import zipfile
from urllib import parse


ROOT = Path(__file__).resolve().parents[1] / 'plugin.video.alfa'


def load_function(path, name, namespace):
    # Load the real function without importing Kodi or starting addon services.
    tree = ast.parse((ROOT / path).read_text(encoding='utf-8'))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), namespace)
    return namespace[name]


class SubtitleTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.data = self.root / 'data'
        self.library = self.root / 'library'
        self.temp = self.root / 'temp' / 'alfa_subtitles'
        self.settings = {}
        self.playing = False
        self.config = SimpleNamespace(
            get_data_path=lambda: str(self.data),
            get_videolibrary_path=lambda: str(self.library),
            get_setting=lambda name, default=None: self.settings.get(name, default),
            set_setting=lambda name, value: self.settings.update({name: value}),
            get_kodi_setting=lambda name: self.settings.get(name, ''),
            get_temp_file=self.temp_file,
        )
        self.config.get_subtitles_path = load_function(
            'platformcode/config.py', 'get_subtitles_path', {'get_temp_file': self.temp_file})
        self.filetools = SimpleNamespace(
            join=os.path.join, translatePath=lambda p: p, basename=os.path.basename,
            exists=os.path.exists, mkdir=lambda p: os.makedirs(p, exist_ok=True),
            write=self.write, remove=lambda p, **kw: os.remove(p),
        )
        self.logger = Mock()
        self.namespace = dict(config=self.config, filetools=self.filetools,
                              logger=self.logger, traceback=traceback,
                              xbmc=SimpleNamespace(Player=lambda: SimpleNamespace(
                                  isPlaying=lambda: self.playing)))
        self.clean = load_function('platformcode/custom_code.py', 'clean_subtitles', self.namespace)

    def temp_file(self, name):
        path = self.root / 'temp' / name
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    def write(self, path, data):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_bytes(data)
        return True

    def create(self, relative):
        path = self.root / relative
        self.write(path, b'subtitle')
        return path

    def test_startup_cleans_temp_and_old_files_once(self):
        old = [self.create(p) for p in (
            'temp/alfa_subtitles/current.srt', 'library/subtitles/nested/old.SRT',
            'data/temp_subtitles/session-old/file.srt', 'data/sub_flashx.srt',
            'data/subtitulo_areadocu.srt')]
        kept = [self.create(p) for p in (
            'library/subtitles/movie.nfo', 'library/subtitles/keep.bin',
            'data/subtitles/Movies/manual.srt', 'library/video/movie.srt')]
        self.clean()
        self.assertTrue(self.settings['old_subtitles_cleaned'])
        self.assertTrue(all(not p.exists() for p in old))
        self.assertTrue(all(p.exists() for p in kept))
        later = self.create('library/subtitles/later.srt')
        temporary = self.create('temp/alfa_subtitles/later.srt')
        self.clean()
        self.assertTrue(later.exists())
        self.assertFalse(temporary.exists())

    def test_playing_skips_everything(self):
        path = self.create('temp/alfa_subtitles/active.srt')
        self.playing = True
        self.clean()
        self.assertTrue(path.exists())
        self.assertNotIn('old_subtitles_cleaned', self.settings)

    def test_absent_directories_are_success(self):
        self.clean()
        self.assertTrue(self.settings['old_subtitles_cleaned'])
        self.assertTrue(Path(self.config.get_subtitles_path()).is_dir())

    def test_custom_and_manual_paths_are_protected(self):
        for setting in ('subtitles.custompath', 'subtitlepath_folder',
                        'subtitlepath_keyboard', 'subtitlepath_file'):
            with self.subTest(setting=setting):
                self.settings.clear()
                path = self.create('library/subtitles/nested/manual.srt')
                self.settings[setting] = str(path if setting.endswith('_file') else path.parent)
                self.clean()
                self.assertTrue(path.exists())
                self.assertTrue(self.settings['old_subtitles_cleaned'])

    def test_failed_old_cleanup_retries(self):
        old = self.create('library/subtitles/old.srt')
        with patch('os.remove', side_effect=OSError('locked')):
            self.clean()
        self.assertNotIn('old_subtitles_cleaned', self.settings)
        self.assertTrue(old.exists())
        self.clean()
        self.assertFalse(old.exists())
        self.assertTrue(self.settings['old_subtitles_cleaned'])

    def test_failed_temp_cleanup_does_not_mark_complete(self):
        path = self.create('temp/alfa_subtitles/locked.srt')
        with patch.object(shutil, 'rmtree', side_effect=OSError('locked')):
            self.clean()
        self.assertTrue(path.exists())
        self.assertNotIn('old_subtitles_cleaned', self.settings)

    def test_remote_legacy_path_is_excluded(self):
        self.config.get_videolibrary_path = lambda: 'smb://server/library'
        self.clean()
        self.assertTrue(self.settings['old_subtitles_cleaned'])
        self.logger.info.assert_called()

    def test_legacy_symlink_does_not_delete_target(self):
        outside = self.create('outside/keep.srt')
        parent = self.library / 'subtitles'
        parent.mkdir(parents=True)
        try:
            (parent / 'linked').symlink_to(outside.parent, target_is_directory=True)
        except OSError:
            self.skipTest('Symlinks are unavailable on this system')
        self.clean()
        self.assertTrue(outside.exists())

    def downloader(self):
        response = SimpleNamespace(sucess=True, data=b'downloaded')
        self.namespace.update(
            urlparse=parse, kwargs={},
            httptools=SimpleNamespace(obtain_domain=lambda url: parse.urlparse(url).netloc,
                                     downloadpage=Mock(return_value=response)),
            get_from_subscene=Mock(), get_from_subdivx=Mock(), get_from_subdl=Mock())
        return load_function('platformcode/subtitletools.py', 'download_subtitles', self.namespace)

    def test_direct_download_uses_temp_and_local_path_is_untouched(self):
        download = self.downloader()
        item = SimpleNamespace(subtitle='https://example.com/movie.srt?token=abc', headers={})
        download(item)
        self.assertEqual(Path(item.subtitle), self.temp / 'movie.srt')
        self.assertEqual(Path(item.subtitle).read_bytes(), b'downloaded')
        item.subtitle = str(self.root / 'manual.srt')
        download(item)
        self.assertEqual(item.subtitle, str(self.root / 'manual.srt'))

    def test_provider_receives_common_path_and_preserves_multiple_subtitles(self):
        download = self.downloader()
        files = [str(self.temp / name) for name in ('spanish.srt', 'english.srt')]
        def provider(url, data, directory, item):
            self.assertEqual(Path(directory), self.temp)
            for filename in files:
                self.write(filename, b'provided')
            return files
        self.namespace['get_from_subdl'].side_effect = provider
        item = SimpleNamespace(subtitle='https://subdl.com/subtitle/movie', headers={})
        download(item)
        self.assertEqual(item.subtitle, files)
        self.assertTrue(all(Path(p).exists() for p in files))

    def test_opensubtitles_zip_and_explicit_destination(self):
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, 'w') as output:
            output.writestr('movie.srt', b'captions')
        selected = {'SubFileName': 'movie.srt', 'ZipDownloadLink': 'https://example.com/sub.zip'}
        http = Mock()
        http.downloadpage.side_effect = lambda url, **kw: SimpleNamespace(
            sucess=True, data=archive.getvalue(), json=[selected])
        self.namespace.update(
            Item=SimpleNamespace, httptools=http,
            _mejor_subtitulo=lambda *args: selected,
            jsontools=SimpleNamespace(load=lambda data: [selected]))
        function = load_function('platformcode/subtitletools.py', 'get_from_opensubtitles', self.namespace)
        def extract(filename, destination):
            with zipfile.ZipFile(filename) as source:
                source.extractall(destination)
        ziptools = SimpleNamespace(ziptools=lambda: SimpleNamespace(extract=extract))
        with patch.dict('sys.modules', {'core': SimpleNamespace(ziptools=ziptools)}):
            for destination in ('', str(self.root / 'explicit')):
                with self.subTest(destination=destination):
                    result = function('tt1234567', sub_dir=destination)
                    self.assertEqual(Path(result), Path(destination or self.temp) / 'movie.srt')
                    self.assertEqual(Path(result).read_bytes(), b'captions')
                    self.assertFalse(Path(result + '.zip').exists())


if __name__ == '__main__':
    unittest.main()
