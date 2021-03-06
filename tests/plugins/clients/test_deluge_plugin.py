import base64
import time
from datetime import datetime
from mock import patch
from ddt import ddt, data
import pytz
import pytz.reference
from tests import DbTestCase
from monitorrent.plugins.clients.deluge import DelugeClientPlugin


@ddt
class DelugePluginTest(DbTestCase):
    def test_settings(self):
        plugin = DelugeClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        self.assertIsNone(plugin.get_settings())
        plugin.set_settings(settings)
        readed_settings = plugin.get_settings()

        self.assertEqual({'host': 'localhost', 'port': None, 'username': 'monitorrent'}, readed_settings)

    @data(True, False)
    @patch('monitorrent.plugins.clients.deluge.DelugeRPCClient')
    def test_check_connection_successfull(self, value, deluge_client):
        rpc_client = deluge_client.return_value
        rpc_client.connected = value

        plugin = DelugeClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        self.assertEqual(value, plugin.check_connection())

        deluge_client.assert_called_with('localhost', DelugeClientPlugin.DEFAULT_PORT, 'monitorrent', 'monitorrent')

        connect_mock = rpc_client.connect
        connect_mock.assert_called_once_with()

    @patch('monitorrent.plugins.clients.deluge.DelugeRPCClient')
    def test_check_connection_failed(self, deluge_client):
        rpc_client = deluge_client.return_value
        rpc_client.connected = True

        plugin = DelugeClientPlugin()

        self.assertFalse(plugin.check_connection())

        deluge_client.assert_not_called()

        connect_mock = rpc_client.connect
        connect_mock.assert_not_called()

    @patch('monitorrent.plugins.clients.deluge.DelugeRPCClient')
    def test_check_connection_connect_exception(self, deluge_client):
        rpc_client = deluge_client.return_value
        rpc_client.connect.side_effect = Exception

        plugin = DelugeClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        self.assertFalse(plugin.check_connection())

        deluge_client.assert_called_with('localhost', DelugeClientPlugin.DEFAULT_PORT, 'monitorrent', 'monitorrent')

        connect_mock = rpc_client.connect
        connect_mock.assert_called_once_with()

    @patch('monitorrent.plugins.clients.deluge.DelugeRPCClient')
    def test_find_torrent(self, deluge_client):
        rpc_client = deluge_client.return_value
        rpc_client.connected = True

        plugin = DelugeClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        date_added = datetime(2015, 10, 9, 12, 3, 55, tzinfo=pytz.reference.LocalTimezone())
        rpc_client.call.return_value = {'name': 'Torrent 1', 'time_added': time.mktime(date_added.timetuple())}

        torrent_hash = 'SomeRandomHashMockString'
        torrent = plugin.find_torrent(torrent_hash)

        self.assertEqual({'name': 'Torrent 1', 'date_added': date_added.astimezone(pytz.utc)}, torrent)

        rpc_client.call.assert_called_once_with('core.get_torrent_status', torrent_hash.lower(),
                                                ['time_added', 'name'])

    @patch('monitorrent.plugins.clients.deluge.DelugeRPCClient')
    def test_find_torrent_without_credentials(self, deluge_client):
        rpc_client = deluge_client.return_value
        rpc_client.connected = True

        plugin = DelugeClientPlugin()

        torrent_hash = 'SomeRandomHashMockString'
        self.assertFalse(plugin.find_torrent(torrent_hash))

        rpc_client.call.assert_not_called()

    @patch('monitorrent.plugins.clients.deluge.DelugeRPCClient')
    def test_find_torrent_connect_exception(self, deluge_client):
        rpc_client = deluge_client.return_value
        rpc_client.connected = True
        rpc_client.connect.side_effect = Exception

        plugin = DelugeClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        torrent_hash = 'SomeRandomHashMockString'
        self.assertFalse(plugin.find_torrent(torrent_hash))

        rpc_client.call.assert_not_called()

    @patch('monitorrent.plugins.clients.deluge.DelugeRPCClient')
    def test_find_torrent_false(self, deluge_client):
        rpc_client = deluge_client.return_value
        rpc_client.connected = True

        plugin = DelugeClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        torrent_hash = 'SomeRandomHashMockString'
        self.assertFalse(plugin.find_torrent(torrent_hash))

        rpc_client.call.assert_called_once_with('core.get_torrent_status', torrent_hash.lower(),
                                                ['time_added', 'name'])

    @patch('monitorrent.plugins.clients.deluge.DelugeRPCClient')
    def test_add_torrent(self, deluge_client):
        rpc_client = deluge_client.return_value
        rpc_client.connected = True

        plugin = DelugeClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        rpc_client.call.return_value = True

        torrent = b'!torrent.content'
        self.assertTrue(plugin.add_torrent(torrent))

        rpc_client.call.assert_called_once_with('core.add_torrent_file', None, base64.encodebytes(torrent), None)

    @patch('monitorrent.plugins.clients.deluge.DelugeRPCClient')
    def test_add_torrent_without_credentials(self, deluge_client):
        rpc_client = deluge_client.return_value
        rpc_client.connected = True

        plugin = DelugeClientPlugin()

        rpc_client.call.return_value = True

        torrent = b'!torrent.content'
        self.assertFalse(plugin.add_torrent(torrent))

        rpc_client.call.assert_not_called()

    @patch('monitorrent.plugins.clients.deluge.DelugeRPCClient')
    def test_add_torrent_call_exception(self, deluge_client):
        rpc_client = deluge_client.return_value
        rpc_client.connected = True
        rpc_client.call.side_effect = Exception

        plugin = DelugeClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        torrent = b'!torrent.content'
        self.assertFalse(plugin.add_torrent(torrent))

        rpc_client.call.assert_called_once_with('core.add_torrent_file', None, base64.encodebytes(torrent), None)

    @patch('monitorrent.plugins.clients.deluge.DelugeRPCClient')
    def test_remove_torrent(self, deluge_client):
        rpc_client = deluge_client.return_value
        rpc_client.connected = True

        plugin = DelugeClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        rpc_client.call.return_value = True

        torrent_hash = 'SomeRandomHashMockString'
        self.assertTrue(plugin.remove_torrent(torrent_hash))

        rpc_client.call.assert_called_once_with('core.remove_torrent', torrent_hash.lower(), False)

    @patch('monitorrent.plugins.clients.deluge.DelugeRPCClient')
    def test_remove_torrent_without_credentials(self, deluge_client):
        rpc_client = deluge_client.return_value
        rpc_client.connected = True

        plugin = DelugeClientPlugin()

        rpc_client.call.return_value = True

        torrent_hash = 'SomeRandomHashMockString'
        self.assertFalse(plugin.remove_torrent(torrent_hash))

        rpc_client.call.assert_not_called()

    @patch('monitorrent.plugins.clients.deluge.DelugeRPCClient')
    def test_remove_torrent_call_exception(self, deluge_client):
        rpc_client = deluge_client.return_value
        rpc_client.connected = True
        rpc_client.call.side_effect = Exception

        plugin = DelugeClientPlugin()
        settings = {'host': 'localhost', 'username': 'monitorrent', 'password': 'monitorrent'}
        plugin.set_settings(settings)

        torrent_hash = 'SomeRandomHashMockString'
        self.assertFalse(plugin.remove_torrent(torrent_hash))

        rpc_client.call.assert_called_once_with('core.remove_torrent', torrent_hash.lower(), False)
