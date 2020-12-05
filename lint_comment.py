import base64
import itertools
import json
import os
from urllib import request

import attr
from pylint import lint


@attr.s(frozen=True, slots=True)
class GithubClient:
    username = attr.ib()
    token = attr.ib()
    owner = attr.ib()
    repo = attr.ib()
    pull_number = attr.ib()

    def request(self, method, path, data=None, page=1, per_page=100):
        # pylint: disable=too-many-arguments
        credentials = '{}:{}'.format(self.username, self.token)
        encoded_credentials = base64.b64encode(credentials.encode('ascii'))

        req = request.Request(
            url='https://api.github.com{}?page={}&per_page={}'.format(
                path,
                page,
                per_page,
            ),
            method=method,
            data=json.dumps(data or {}).encode('utf-8'),
            headers={
                'Authorization': 'Basic %s' % encoded_credentials.decode("ascii"),
                'Accept': 'application/vnd.github.v3+json',
            },
        )

        with request.urlopen(req) as file:
            return json.loads(file.read().decode('utf-8'))

    def list(self, path):
        per_page = 100
        for page in itertools.count(1):
            page_results = self.request('GET', path, page=page, per_page=per_page)
            yield from page_results

            if len(page_results) < per_page:
                break

    def post(self, path, data):
        return self.request('POST', path, data=data)

    def list_pull_request_files(self):
        yield from self.list('/repos/{self.owner}/{self.repo}/pulls/{self.pull_number}/files'.format(self=self))


@attr.s(frozen=True, slots=True)
class PyLint:
    @staticmethod
    def lint(path):
        lint.Run([path], exit=False)


def main():
    client = GithubClient(
        username='taliastocks',
        token=os.environ['GITHUB_TOKEN'],
        owner='Sibilance',
        repo='compiler',
        pull_number=4,
    )
    for file in client.list_pull_request_files():
        print(json.dumps(file))
        filename = file['filename']
        if filename.endswith('.py'):
            PyLint.lint(file['filename'])


if __name__ == '__main__':
    main()
