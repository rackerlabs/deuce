from cafe.drivers.unittest import fixtures
from tests.api.utils import config
from tests.api.utils import client
from tests.api.utils.schema import auth

from collections import namedtuple

import json
import jsonschema
import os
import random
import sha
import string
import urlparse

Block = namedtuple('Block', 'Id Data')


class TestBase(fixtures.BaseTestFixture):
    """
    Fixture for Deuce API Tests
    """

    @classmethod
    def setUpClass(cls):
        """
        Initialization of Deuce Client
        """

        super(TestBase, cls).setUpClass()
        cls.config = config.deuceConfig()
        cls.auth_config = config.authConfig()
        cls.auth_token = None
        if cls.config.use_auth:
            cls.a_client = client.AuthClient(cls.auth_config.base_url)
            cls.a_resp = cls.a_client.get_auth_token(cls.auth_config.user_name,
                                                     cls.auth_config.api_key)
            jsonschema.validate(cls.a_resp.json(), auth.authentication)
            cls.auth_token = cls.a_resp.entity.token
        cls.client = client.BaseDeuceClient(cls.config.base_url,
                                            cls.config.version,
                                            cls.auth_token)

        cls.blocks = []
        cls.api_version = cls.config.version

    @classmethod
    def tearDownClass(cls):
        """
        Deletes the added resources
        """
        super(TestBase, cls).tearDownClass()

    @classmethod
    def id_generator(cls, size):
        """
        Return an alphanumeric string of size
        """

        return ''.join(random.choice(string.ascii_letters +
            string.digits) for _ in range(size))

    def setUp(self):
        super(TestBase, self).setUp()

    def tearDown(self):
        if any(r for r in self._resultForDoCleanups.failures
               if self._custom_test_name_matches_result(self._testMethodName,
                                                        r)):
            self._reporter.stop_test_metrics(self._testMethodName, 'Failed')
        elif any(r for r in self._resultForDoCleanups.errors
                 if self._custom_test_name_matches_result(self._testMethodName,
                                                          r)):
            self._reporter.stop_test_metrics(self._testMethodName, 'ERRORED')
        else:
            super(TestBase, self).tearDown()

    def _custom_test_name_matches_result(self, name, test_result):
        """
        Function used to compare test name with the information in test_result
        Used with Nosetests
        """

        try:
            result = test_result[0]
            testMethodName = result.__str__().split()[0]
        except:
            return False
        return testMethodName == name

    def validate_headers(self, headers, json=False, binary=False):
        """Basic http header validation"""

        self.assertIsNotNone(headers['transaction-id'])
        self.assertIsNotNone(headers['content-length'])
        if json:
            self.assertEqual('application/json; charset=UTF-8',
                             headers['content-type'])
        if binary:
            self.assertEqual('application/binary', headers['content-type'])

    def validate_url(self, url, nextblocklist=False, filelocation=False,
                     nextfileblocklist=False):

        u = urlparse.urlparse(url)
        self.assertIn(u.scheme, ['http', 'https'])
        if nextblocklist:
            self.assertTrue(u.path.startswith('/{0}/{1}/blocks'
                ''.format(self.api_version, self.vaultname)),
                'url: {0}'.format(url))
            query = urlparse.parse_qs(u.query)
            self.assertIn('marker', query, 'url: {0}'.format(url))
            self.assertIn('limit', query, 'url: {0}'.format(url))
        elif filelocation:
            self.assertTrue(u.path.startswith('/{0}/{1}/files'
                ''.format(self.api_version, self.vaultname)),
                'url: {0}'.format(url))
        elif nextfileblocklist:
            self.assertTrue(u.path.startswith('/{0}/{1}/files'
                ''.format(self.api_version, self.vaultname)),
                'url: {0}'.format(url))
            self.assertIn('/blocks', u.path)
            query = urlparse.parse_qs(u.query)
            self.assertIn('marker', query, 'url: {0}'.format(url))
            self.assertIn('limit', query, 'url: {0}'.format(url))

    def _createEmptyVault(self, vaultname=None, size=50):
        """
        Test Setup Helper: Creates an empty vault
        If vaultname is provided, the vault is created using that name.
        If not, an alphanumeric vaultname of a given size is generated
        """

        if vaultname:
            self.vaultname = vaultname
        else:
            self.vaultname = self.id_generator(size)
        resp = self.client.create_vault(self.vaultname)
        return True if 201 == resp.status_code else False

    def createEmptyVault(self, vaultname=None, size=50):
        """
        Test Setup Helper: Creates an empty vault
        If vaultname is provided, the vault is created using that name.
        If not, an alphanumeric vaultname of a given size is generated

        Exception is raised if the operation is not successful
        """
        if not self._createEmptyVault(vaultname, size):
            raise Exception('Failed to create vault')
        self.blocks = []
        self.files = []

    def generateBlockData(self, block_data=None, size=30720):
        """
        Test Setup Helper: Generates block data and adds it to the internal
        block list
        """

        if block_data is not None:
            self.block_data = block_data
        else:
            self.block_data = os.urandom(size)
        self.blockid = sha.new(self.block_data).hexdigest()
        self.blocks.append(Block(Id=self.blockid, Data=self.block_data))

    def _uploadBlock(self, block_data=None, size=30720):
        """
        Test Setup Helper: Uploads a block
        If block_data is used if provided.
        If not, a random block of data of the specified size is used
        """
        self.generateBlockData(block_data, size)
        resp = self.client.upload_block(self.vaultname, self.blockid,
                                        self.block_data)
        return True if 201 == resp.status_code else False

    def uploadBlock(self, block_data=None, size=30720):
        """
        Test Setup Helper: Uploads a block
        If block_data is used if provided.
        If not, a random block of data of the specified size is used

        Exception is raised if the operation is not successful
        """
        if not self._uploadBlock(block_data, size):
            raise Exception('Failed to upload block')

    def _createNewFile(self):
        """
        Test Setup Helper: Creates a file
        """

        resp = self.client.create_file(self.vaultname)
        self.fileurl = resp.headers['location']
        self.fileid = self.fileurl.split('/')[-1]
        self.files.append(self.fileid)
        return True if 201 == resp.status_code else False

    def createNewFile(self):
        """
        Test Setup Helper: Creates a file

        Exception is raised if the operation is not successful
        """

        if not self._createNewFile():
            raise Exception('Failed to create a file')

    def _assignAllBlocksToFile(self):
        """
        Test Setup Helper: Assigns all blocks to the file
        """
        offset = 0
        block_list = list()
        for block_info in self.blocks:
            block_list.append({'id': block_info.Id,
                               'size': len(block_info.Data), 'offset': offset})
            offset += len(block_info.Data)
        block_dict = {'blocks': block_list}
        resp = self.client.assign_to_file(json.dumps(block_dict),
                                          alternate_url=self.fileurl)
        return True if 200 == resp.status_code else False

    def assignAllBlocksToFile(self):
        """
        Test Setup Helper: Assigns all blocks to the file

        Exception is raised if the operation is not successful
        """

        if not self._assignAllBlocksToFile():
            raise Exception('Failed to assign blocks to file')

    def _finalizeFile(self):
        """
        Test Setup Helper: Finalizes the file
        """

        resp = self.client.finalize_file(alternate_url=self.fileurl)
        return True if 200 == resp.status_code else False

    def finalizeFile(self):
        """
        Test Setup Helper: Finalizes the file

        Exception is raised if the operation is not successful
        """

        if not self._finalizeFile():
            raise Exception('Failed to finalize file')
