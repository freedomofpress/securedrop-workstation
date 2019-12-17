import unittest
import json
from jinja2 import Template


from base import SD_VM_Local_Test


def skip_if_v3_is_missing():
    """
    Returns True if v3 address is not setup
    """
    with open("config.json") as c:
        config = json.load(c)
        if len(config["hidserv"]["hostname"]) == 22:
            return True
        else:
            return False


class SD_Whonix_Tests(SD_VM_Local_Test):
    def setUp(self):
        self.vm_name = "sd-whonix"
        self.whonix_apt_list = "/etc/apt/sources.list.d/whonix.list"
        super(SD_Whonix_Tests, self).setUp()

    def test_accept_sd_xfer_extracted_file(self):
        with open("config.json") as c:
            config = json.load(c)
            if len(config["hidserv"]["hostname"]) == 22:
                t = Template(
                    "HidServAuth {{ d.hidserv.hostname }}" " {{ d.hidserv.key }}"
                )
                line = t.render(d=config)

            else:
                line = "ClientOnionAuthDir /var/lib/tor/keys"

            self.assertFileHasLine("/usr/local/etc/torrc.d/50_user.conf", line)

    @unittest.skipIf(skip_if_v3_is_missing(), "Onion v3 address is not setup")
    def test_v3_auth_private_file(self):
        with open("config.json") as c:
            config = json.load(c)
            hostname = config["hidserv"]["hostname"].split(".")[0]
            keyvalue = config["hidserv"]["key"]
            line = "{0}:descriptor:x25519:{1}".format(hostname, keyvalue)

            self.assertFileHasLine(
                "/var/lib/tor/keys/app-journalist.auth_private", line
            )

    def test_sd_whonix_repo_enabled(self):
        """
        During Whonix 14 -> 15 migration, we removed the apt list file
        (because the repo wasn't serving, due to EOL status). Let's
        make sure it's there, since we're past 14 now.
        """
        assert self._fileExists(self.whonix_apt_list)


def load_tests(loader, tests, pattern):
    suite = unittest.TestLoader().loadTestsFromTestCase(SD_Whonix_Tests)
    return suite
