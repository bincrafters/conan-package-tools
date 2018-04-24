import unittest
import sys

from conans.client.conan_api import ConanAPIV1

from cpt import __version__ as version

from conans.client import tools
from cpt.test.integration.base import BaseTest, PYPI_TESTING_REPO, CONAN_UPLOAD_URL, \
    CONAN_UPLOAD_PASSWORD, CONAN_LOGIN_UPLOAD
from cpt.packager import ConanMultiPackager


class DockerTest(BaseTest):

    @unittest.skipUnless(sys.platform.startswith("linux"), "Requires Linux")
    def test_docker(self):
        self.deploy_pip()
        api, _, _ = ConanAPIV1.factory()

        conanfile = """from conans import ConanFile
import os

class Pkg(ConanFile):
    settings = "os", "compiler", "build_type", "arch"

"""
        self.save_conanfile(conanfile)
        the_version = version.replace("-", ".")  # Canonical name for artifactory repo
        pip = "--extra-index-url %s/simple conan-package-tools==%s " % (PYPI_TESTING_REPO, the_version)
        with tools.environment_append({"CONAN_USE_DOCKER": "1",
                                       "CONAN_PIP_PACKAGE": pip,
                                       "CONAN_LOGIN_USERNAME": CONAN_LOGIN_UPLOAD,
                                       "CONAN_USERNAME": "lasote",
                                       "CONAN_UPLOAD": CONAN_UPLOAD_URL,
                                       "CONAN_PASSWORD": CONAN_UPLOAD_PASSWORD}):
            self.packager = ConanMultiPackager("--build missing -r conan.io",
                                               channel="mychannel",
                                               gcc_versions=["6"],
                                               archs=["x86", "x86_64"],
                                               build_types=["Release"],
                                               reference="zlib/1.2.2")
            self.packager.add_common_builds()
            self.packager.run()

        # Remove from remote
        try:
            api.remote_add("upload_testing", CONAN_UPLOAD_URL)
        except:
            pass

        self.assertEquals(len(api.search_recipes("zlib*", remote="upload_testing")), 1)
        self.assertEquals(len(api.search_packages("zlib/1.2.2@lasote/testing",
                                                  remote="upload_testing")), 2)

        api.authenticate(name=CONAN_LOGIN_UPLOAD, password=CONAN_UPLOAD_PASSWORD,
                         remote="upload_testing")
        api.remove("zlib*", remote="upload_testing", force=True)
        self.assertEquals(api.search_recipes("zlib*"), [])

        # Try upload only when stable, shouldn't upload anything
        with tools.environment_append({"CONAN_USE_DOCKER": "1",
                                       "CONAN_PIP_PACKAGE": pip,
                                       "CONAN_LOGIN_USERNAME": CONAN_LOGIN_UPLOAD,
                                       "CONAN_USERNAME": "lasote",
                                       "CONAN_UPLOAD": CONAN_UPLOAD_URL,
                                       "CONAN_PASSWORD": CONAN_UPLOAD_PASSWORD,
                                       "CONAN_UPLOAD_ONLY_WHEN_STABLE": 1}):
            self.packager = ConanMultiPackager("--build missing -r conan.io",
                                               channel="mychannel",
                                               gcc_versions=["6"],
                                               archs=["x86", "x86_64"],
                                               build_types=["Release"],
                                               reference="zlib/1.2.2")
            self.packager.add_common_builds()
            self.packager.run()

        self.assertEquals(len(api.search_recipes("zlib*", remote="upload_testing")), 0)
