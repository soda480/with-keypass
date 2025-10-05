import os
import sys
import unittest
import argparse
from mock import patch
from mock import call
from mock import Mock
from with_keepass.__main__ import sys_exit
from with_keepass.__main__ import parse_args
from with_keepass.__main__ import _env_from_group
from with_keepass.__main__ import _env_from_entry
from with_keepass.__main__ import get_env_keepass
from with_keepass.__main__ import get_password
from with_keepass.__main__ import _main
from with_keepass.__main__ import DEFAULT_DB_PATH, DEFAULT_PATH

class TestWithKeePass(unittest.TestCase):
    
    @patch('with_keepass.__main__.sys.exit')
    @patch('builtins.print')
    def test__sys_exit(self, print_patch, exit_patch, *patches):
        sys_exit('a message', exit_code=2, stderr=True)
        print_patch.assert_called_once_with('a message', file=sys.stderr)
        exit_patch.assert_called_once_with(2)

    @patch('with_keepass.__main__.sys.exit')
    @patch('builtins.print')
    def test__sys_exit_no_stderr(self, print_patch, exit_patch, *patches):
        sys_exit('a message', stderr=False)
        print_patch.assert_called_once_with('a message')
        exit_patch.assert_called_once_with(0)

    @patch.dict(os.environ, {}, clear=True)
    @patch('with_keepass.__main__.sys.argv', ['prog', '--dry-run'])
    def test__parse_args_defaults(self):
        args = parse_args()
        self.assertEqual(args.db_path, DEFAULT_DB_PATH)
        self.assertEqual(args.path, DEFAULT_PATH)
        self.assertTrue(args.dry_run)
        self.assertEqual(args.command, [])

    @patch.dict(
        os.environ,
        {
            'KEEPASS_DB_PATH': '/tmp/test.kdbx',
            'KEEPASS_PATH': '/Root/Secrets/Entry1'
        },
        clear=True)
    @patch('with_keepass.__main__.sys.argv', ['prog', '--', 'my-command'])
    def test__parse_args_env(self):
        args = parse_args()
        self.assertEqual(args.db_path, '/tmp/test.kdbx')
        self.assertEqual(args.path, '/Root/Secrets/Entry1')
        self.assertFalse(args.dry_run)
        self.assertEqual(args.command, ['my-command'])

    @patch.dict(os.environ, {}, clear=True)
    @patch('with_keepass.__main__.sys.argv', ['prog'])
    @patch('with_keepass.__main__.argparse.ArgumentParser')
    def test__parse_args_parser_error(self, argument_parser_patch, *patches):
        parser_mock = Mock()
        parser_mock.parse_args.return_value = argparse.Namespace(command=[], dry_run=False)
        argument_parser_patch.return_value = parser_mock
        parse_args()
        parser_mock.error.assert_called_once()

    def test__env_from_group(self, *patches):
        entry1_mock = Mock(title='key1')
        entry1_mock.get_custom_property.return_value = 'value1'
        entry2_mock = Mock(title='key2')
        entry2_mock.get_custom_property.return_value = 'value2'
        group_mock = Mock(entries=[entry1_mock, entry2_mock])
        result = _env_from_group(group_mock, '/path')
        expected_result = {
            'key1': 'value1',
            'key2': 'value2'
        }
        self.assertEqual(result, expected_result)

    @patch('with_keepass.__main__.sys_exit')
    def test__env_from_group_no_titles(self, sys_exit_patch, *patches):
        entry1_mock = Mock(title='')
        entry1_mock.get_custom_property.return_value = 'value1'
        entry2_mock = Mock(title='')
        entry2_mock.get_custom_property.return_value = 'value2'
        group_mock = Mock(entries=[entry1_mock, entry2_mock])
        _env_from_group(group_mock, '/path')
        sys_exit_patch.assert_called_once()

    @patch('with_keepass.__main__.sys_exit')
    def test__env_from_group_no_values(self, sys_exit_patch, *patches):
        entry1_mock = Mock(title='key1')
        entry1_mock.get_custom_property.return_value = ''
        entry2_mock = Mock(title='key2')
        entry2_mock.get_custom_property.return_value = ''
        group_mock = Mock(entries=[entry1_mock, entry2_mock])
        _env_from_group(group_mock, '/path')
        sys_exit_patch.assert_called_once()

    def test__env_from_entry_custom_properties(self, *patches):
        entry_mock = Mock(custom_properties={'k1': 'v1'})
        result = _env_from_entry(entry_mock, '/path')
        expected_result = {'k1': 'v1'}
        self.assertEqual(result, expected_result)

    @patch('with_keepass.__main__.sys_exit')
    def test__env_from_entry_no_custom_properties(self, sys_exit_patch, *patches):
        entry_mock = Mock(custom_properties='')
        _env_from_entry(entry_mock, '/path')
        sys_exit_patch.assert_called_once()

    @patch('with_keepass.__main__.sys_exit')
    @patch('with_keepass.__main__.PyKeePass')
    def test__get_env_keepass_pykeepass_error(self, pykeepass_patch, sys_exit_patch, *patches):
        pykeepass_patch.side_effect = Exception('error')
        with self.assertRaises(UnboundLocalError):
            get_env_keepass('db_path', 'password', 'path')
        sys_exit_patch.assert_called_once_with('Failed to open KeePass DB: error', exit_code=1)

    @patch('with_keepass.__main__.sys_exit')
    @patch('with_keepass.__main__.PyKeePass')
    def test__get_env_keepass_no_group_no_entry(self, pykeepass_patch, sys_exit_patch, *patches):
        pykeepass_mock = Mock()
        pykeepass_mock.find_groups_by_path.return_value = None
        pykeepass_mock.find_entries_by_path.return_value = None
        pykeepass_patch.return_value = pykeepass_mock
        get_env_keepass('db_path', 'password', 'path')
        sys_exit_patch.assert_called_once_with('The path path was neither a group or entry', exit_code=2)

    @patch('with_keepass.__main__._env_from_group')
    @patch('with_keepass.__main__.PyKeePass')
    def test__get_env_keepass_group(self, pykeepass_patch, env_from_group_patch, *patches):
        pykeepass_mock = Mock()
        pykeepass_mock.find_groups_by_path.return_value = Mock()
        pykeepass_patch.return_value = pykeepass_mock
        result = get_env_keepass('db_path', 'password', 'path')
        self.assertEqual(result, env_from_group_patch.return_value)

    @patch('with_keepass.__main__._env_from_entry')
    @patch('with_keepass.__main__.PyKeePass')
    def test__get_env_keypass_entry(self, pykeepass_patch, env_from_entry_patch, *patches):
        pykeepass_mock = Mock()
        pykeepass_mock.find_groups_by_path.return_value = None
        pykeepass_mock.find_entries_by_path.return_value = Mock()
        pykeepass_patch.return_value = pykeepass_mock
        result = get_env_keepass('db_path', 'password', 'path')
        self.assertEqual(result, env_from_entry_patch.return_value)

    @patch.dict(os.environ, {}, clear=True)
    @patch('with_keepass.__main__.getpass.getpass')
    def test__get_password_getpass(self, getpass_patch, *patches):
        result = get_password()
        self.assertEqual(result, getpass_patch.return_value)

    @patch.dict(os.environ, {'KEEPASS_PASSWORD': 'env-password'}, clear=True)
    @patch('with_keepass.__main__.getpass.getpass')
    def test__get_password_getenv(self, getpass_patch, *patches):
        result = get_password()
        self.assertEqual(result, 'env-password')

    @patch.dict(os.environ, {'k1': 'v1', 'k2': 'v2'}, clear=True)
    @patch('with_keepass.__main__.get_password', return_value='p123')
    @patch('with_keepass.__main__.os.execvpe')
    @patch('with_keepass.__main__.get_env_keepass')
    @patch('with_keepass.__main__.parse_args')
    def test__main(self, parse_args_patch, get_env_keepass_patch, execvpe_patch, *patches):
        parse_args_patch.return_value = argparse.Namespace(
            db_path='/fake/db.kdbx',
            path='/Root/Fake',
            dry_run=False,
            command=['aws', 's3', 'ls'])
        get_env_keepass_patch.return_value = {'k3': 'v4'}
        _main()
        execvpe_patch.assert_called_once_with('aws', ['aws', 's3', 'ls'], {'k1': 'v1', 'k2': 'v2', 'k3': 'v4'})

    @patch.dict(os.environ, {'k1': 'v1', 'k2': 'v2'}, clear=True)
    @patch('with_keepass.__main__.get_password', return_value='p123')
    @patch('builtins.print')
    @patch('with_keepass.__main__.os.execvpe')
    @patch('with_keepass.__main__.get_env_keepass')
    @patch('with_keepass.__main__.parse_args')
    def test__main_dry_run(self, parse_args_patch, get_env_keepass_patch, execvpe_patch, print_patch, *patches):
        parse_args_patch.return_value = argparse.Namespace(
            db_path='/fake/db.kdbx',
            path='/Root/Fake',
            dry_run=True,
            command=[])
        get_env_keepass_patch.return_value = {'k3': 'v4'}
        with self.assertRaises(SystemExit):
            _main()
        print_patch.assert_called()

    @patch('builtins.print')
    @patch('with_keepass.__main__.get_password')
    def test__main_password_error(self, get_password_patch, *patches):
        get_password_patch.side_effect = [EOFError('error')]
        with self.assertRaises(SystemExit):
            _main()
