from unittest import mock

import imp
import os
import pytest
import tempfile


SAMPLE_OUTPUT_NO_PRINTER = b"network beh\nnetwork https\nnetwork ipp\nnetwork ipps\nnetwork http\nnetwork\nnetwork ipp14\nnetwork lpd"  # noqa
SAMPLE_OUTPUT_BOTHER_PRINTER = b"network beh\nnetwork https\nnetwork ipp\nnetwork ipps\nnetwork http\nnetwork\nnetwork ipp14\ndirect usb://Brother/HL-L2320D%20series?serial=A00000A000000\nnetwork lpd"  # noqa


# This below stanza is only necessary because the export code is not
# structured as a module. If a Python module were created called
# `securedropexport`, we could simply do `import securedropexport`
path_to_script = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "send-to-usb"
)
securedropexport = imp.load_source("send-to-usb", path_to_script)


def test_exit_gracefully_no_exception(capsys):
    test_msg = 'test'

    with pytest.raises(SystemExit) as sysexit:
        securedropexport.exit_gracefully(test_msg)

    # A graceful exit means a return code of 0
    assert sysexit.value.code == 0

    captured = capsys.readouterr()
    assert captured.err == "{}\n".format(test_msg)
    assert captured.out == ""


def test_exit_gracefully_exception(capsys):
    test_msg = 'test'

    with pytest.raises(SystemExit) as sysexit:
        securedropexport.exit_gracefully(test_msg,
                                         e=Exception('BANG!'))

    # A graceful exit means a return code of 0
    assert sysexit.value.code == 0

    captured = capsys.readouterr()
    assert captured.err == "{}\n<unknown exception>\n".format(test_msg)
    assert captured.out == ""


def test_empty_config(capsys):
    temp_folder = tempfile.mkdtemp()
    metadata = os.path.join(temp_folder, securedropexport.Metadata.METADATA_FILE)
    with open(metadata, "w") as f:
        f.write("{}")
    config = securedropexport.Metadata(temp_folder)
    assert not config.is_valid()


def test_valid_printer_test_config(capsys):
    temp_folder = tempfile.mkdtemp()
    metadata = os.path.join(temp_folder, securedropexport.Metadata.METADATA_FILE)
    with open(metadata, "w") as f:
        f.write('{"device": "printer-test"}')
    config = securedropexport.Metadata(temp_folder)
    assert config.is_valid()
    assert config.encryption_key is None
    assert config.encryption_method is None


def test_valid_printer_config(capsys):
    temp_folder = tempfile.mkdtemp()
    metadata = os.path.join(temp_folder, securedropexport.Metadata.METADATA_FILE)
    with open(metadata, "w") as f:
        f.write('{"device": "printer"}')
    config = securedropexport.Metadata(temp_folder)
    assert config.is_valid()
    assert config.encryption_key is None
    assert config.encryption_method is None


def test_invalid_encryption_config(capsys):
    temp_folder = tempfile.mkdtemp()
    metadata = os.path.join(temp_folder, securedropexport.Metadata.METADATA_FILE)
    with open(metadata, "w") as f:
        f.write(
            '{"device": "disk", "encryption_method": "base64", "encryption_key": "hunter1"}'
        )
    config = securedropexport.Metadata(temp_folder)
    assert config.encryption_key == "hunter1"
    assert config.encryption_method == "base64"
    assert not config.is_valid()


def test_valid_encryption_config(capsys):
    temp_folder = tempfile.mkdtemp()
    metadata = os.path.join(temp_folder, securedropexport.Metadata.METADATA_FILE)
    with open(metadata, "w") as f:
        f.write(
            '{"device": "disk", "encryption_method": "luks", "encryption_key": "hunter1"}'
        )
    config = securedropexport.Metadata(temp_folder)
    assert config.encryption_key == "hunter1"
    assert config.encryption_method == "luks"
    assert config.is_valid()


@mock.patch("subprocess.check_call")
def test_popup_message(mocked_call):
    securedropexport.popup_message("hello!")
    mocked_call.assert_called_once_with([
        "notify-send",
        "--expire-time", "3000",
        "--icon", "/usr/share/securedrop/icons/sd-logo.png",
        "SecureDrop: hello!"
    ])


@mock.patch("subprocess.check_output", return_value=SAMPLE_OUTPUT_BOTHER_PRINTER)
def test_get_good_printer_uri(mocked_call):
    result = securedropexport.get_printer_uri()
    assert result == "usb://Brother/HL-L2320D%20series?serial=A00000A000000"


@mock.patch("subprocess.check_output", return_value=SAMPLE_OUTPUT_NO_PRINTER)
def test_get_bad_printer_uri(mocked_call, capsys):
    expected_message = "USB Printer not found"
    mocked_exit = mock.patch("securedropexport.exit_gracefully", return_value=0)

    with pytest.raises(SystemExit) as sysexit:
        result = securedropexport.get_printer_uri()
        assert result == ""
        mocked_exit.assert_called_once_with(expected_message)

    assert sysexit.value.code == 0
    captured = capsys.readouterr()
    assert captured.err == "{}\n".format(expected_message)
    assert captured.out == ""


@pytest.mark.parametrize('open_office_paths', [
    "/tmp/whatver/thisisadoc.doc"
    "/home/user/Downloads/thisisadoc.xlsx"
    "/home/user/Downloads/file.odt"
    "/tmp/tmpJf83j9/secret.pptx"
])
def test_is_open_office_file(capsys, open_office_paths):
    assert securedropexport.is_open_office_file(open_office_paths)


@pytest.mark.parametrize('open_office_paths', [
    "/tmp/whatver/thisisadoc.doccc"
    "/home/user/Downloads/thisisa.xlsx.zip"
    "/home/user/Downloads/file.odz"
    "/tmp/tmpJf83j9/secret.gpg"
])
def test_is_not_open_office_file(capsys, open_office_paths):
    assert not securedropexport.is_open_office_file(open_office_paths)
