from unittest import TestCase
from webtest import TestApp
from deuce.tests import FunctionalTest


class TestRootController(FunctionalTest):

    def dummy_test(self):
        assert True

    def test_get(self):
        response = self.app.get('/')
        assert response.status_int == 200

    def test_get_10(self):
        response = self.app.get('/v1.0')

    def test_get_not_found(self):
        response = self.app.get('/a/bogus/url', expect_errors=True)
        assert response.status_int == 404
