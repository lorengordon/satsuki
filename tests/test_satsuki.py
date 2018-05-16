# test_pyppyn.py

import pytest
import uuid
import os
import github
import platform
import json

from satsuki import Arguments, ReleaseMgr, HASH_FILE
from urllib.request import urlopen, urlretrieve
from string import Template

TEST_VERBOSE = True
TEST_BODY = str(uuid.uuid1())
TEST_SLUG = "YakDriver/satsuki"
TEST_TAG = "Test-v" + TEST_BODY[:6]
TEST_REL_NAME = "Test Release v" + TEST_BODY[:6]
TEST_COMMITISH = "5aacf6b744ec379afafbf3bac2131474a464ee9d"
TEST_FILENAME = 'tests/release-asset.exe'
TEST_DOWNLOAD = 'tests/downloaded-asset'
TEST_DOWNLOAD_SHA = 'tests/downloaded-asset-sha'

def test_blank_arguments():
    """ Returns an Arguments instance with nothing set. """
    with pytest.raises(PermissionError):
        Arguments()


@pytest.fixture
def arguments_base(token):
    """ Basic arguments with authorization (must provide token) """
    return Arguments(
        verbose = TEST_VERBOSE,
        token = token,
        slug = TEST_SLUG,
        tag = TEST_TAG,
        body = TEST_BODY,
        rel_name = TEST_REL_NAME,
        commitish = TEST_COMMITISH
    )


def test_create_release(arguments_base):
    rm = ReleaseMgr(arguments_base)
    rm.execute() # <== should create
    compare_args = Arguments(
        verbose = TEST_VERBOSE,
        token = arguments_base.api_token,
        slug = TEST_SLUG,
        tag = TEST_TAG
    )

    assert compare_args.body == TEST_BODY \
        and compare_args.rel_name == TEST_REL_NAME


def test_get_latest(arguments_base):
    rm = ReleaseMgr(arguments_base)
    rm.execute() # <== should create
    compare_args = Arguments(
        verbose = TEST_VERBOSE,
        token = arguments_base.api_token,
        slug = TEST_SLUG,
        latest = True
    )

    if compare_args.tag == TEST_TAG:
        assert compare_args.tag == TEST_TAG \
            and compare_args.body == TEST_BODY \
            and compare_args.rel_name == TEST_REL_NAME
    else:
        # a real tag has gotten in first, forget the test
        assert True


def test_upload_file(token):
    with open(TEST_FILENAME, 'wb') as fout:
        fout.write(os.urandom(1024000))

    args = Arguments(
        verbose = TEST_VERBOSE,
        token = token,
        slug = TEST_SLUG,
        tag = TEST_TAG,
        file_file = "tests/test.file",
        fila_sha = Arguments.FILE_SHA_SEP_FILE
    )

    ul_rel = ReleaseMgr(args)
    ul_rel.execute()
    assert True


def test_download_file(token):
    """
    Doesn't directly check Satsuki but rather the effects of Satsuki
    and creation of file and SHA hash.
    """

    # github => repo => release => asset_list => asset => url => download

    gh = github.Github(token, per_page=100)
    repo = gh.get_repo(TEST_SLUG, lazy=False)
    release = repo.get_release(TEST_TAG)
    asset_list = release.get_assets()
    sha_filename = Template(HASH_FILE).safe_substitute({
        'platform': platform.system().lower()
    })

    assets_calculated_sha = 'notasha'
    sha_dict = {}

    for check_asset in asset_list:
        if check_asset.name == os.path.basename(TEST_FILENAME):
            # the uploaded asset
            urlretrieve(check_asset.browser_download_url, TEST_DOWNLOAD)
            # recalc hash of downloaded file
            assets_calculated_sha = Arguments.get_hash(TEST_DOWNLOAD)

        elif check_asset.name == sha_filename:
            # the sha hash file
            with urlopen(check_asset.browser_download_url) as url:
                http_info = url.info()
                if http_info.get_content_charset() is None:
                    raw_data = url.read()
                else:
                    raw_data = url.read().decode(http_info.get_content_charset())
            sha_dict = json.loads(raw_data)
            # get hash from the file

    assert assets_calculated_sha == sha_dict[os.path.basename(TEST_FILENAME)]


def test_delete_release(token):

    delete_args = Arguments(
        verbose = TEST_VERBOSE,
        token = token,
        slug = TEST_SLUG,
        tag = TEST_TAG,
        command = Arguments.COMMAND_DELETE,
        include_tag = True
    )

    del_rel = ReleaseMgr(delete_args)
    del_rel.execute()
    assert True
