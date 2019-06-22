import imp
import os
import pytest


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