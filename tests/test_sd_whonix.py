import json
import unittest

from base import SD_VM_Local_Test
from jinja2 import Template


class SD_Whonix_Tests(SD_VM_Local_Test):
    def setUp(self):
        self.vm_name = "sd-whonix"
        self.whonix_apt_list = "/etc/apt/sources.list.d/derivative.list"
        super(SD_Whonix_Tests, self).setUp()
        self.expected_config_keys = {"SD_HIDSERV_HOSTNAME", "SD_HIDSERV_KEY"}

    def test_accept_sd_xfer_extracted_file(self):
        with open("config.json") as c:
            config = json.load(c)
            if len(config["hidserv"]["hostname"]) == 22:
                t = Template("HidServAuth {{ d.hidserv.hostname }}" " {{ d.hidserv.key }}")
                line = t.render(d=config)

            else:
                line = "ClientOnionAuthDir /var/lib/tor/keys"

            self.assertFileHasLine("/usr/local/etc/torrc.d/50_user.conf", line)

    def test_v3_auth_private_file(self):
        with open("config.json") as c:
            config = json.load(c)
            hostname = config["hidserv"]["hostname"].split(".")[0]
            keyvalue = config["hidserv"]["key"]
            line = "{0}:descriptor:x25519:{1}".format(hostname, keyvalue)

            self.assertFileHasLine("/var/lib/tor/keys/app-journalist.auth_private", line)

    def test_sd_whonix_config(self):
        self.assertEqual(
            self.dom0_config["hidserv"]["hostname"], self._vm_config_read("SD_HIDSERV_HOSTNAME")
        )
        self.assertEqual(self.dom0_config["hidserv"]["key"], self._vm_config_read("SD_HIDSERV_KEY"))

    def test_sd_whonix_repo_enabled(self):
        """
        During Whonix 14 -> 15 migration, we removed the apt list file
        (because the repo wasn't serving, due to EOL status). Let's
        make sure it's there, since we're past 14 now.
        """
        assert self._fileExists(self.whonix_apt_list)

    def test_sd_whonix_verify_tor_config(self):
        # User must be debian-tor for v3 Onion, due to restrictive
        # mode on the client keys directory.
        self._run("tor --verify-config", user="debian-tor")

    def test_whonix_torrc(self):
        """
        Ensure Whonix-maintained torrc files don't contain duplicate entries.
        """
        torrc_contents = self._get_file_contents("/etc/tor/torrc")
        duplicate_includes = """%include /etc/torrc.d/
%include /etc/torrc.d/95_whonix.conf"""
        self.assertFalse(
            duplicate_includes in torrc_contents,
            "Whonix GW torrc contains duplicate %include lines",
        )


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_Whonix_Tests)
    return suite
