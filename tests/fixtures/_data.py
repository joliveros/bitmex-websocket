import alog
import os
import json


class TestData():
    def get(self, key):
        filename = self.fixture_file_name(key)
        with open(filename) as json_file:
            return json.load(json_file)

    def set(self, key, data):
        filename = self.fixture_file_name(key)

        with open(filename, 'w') as json_file:
            json.dumps(data, jsonfile)

    def fixture_file_name(self, key):
        return os.path.abspath('./tests/fixtures/%s.json' % key)
