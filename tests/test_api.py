
import pytest

from pmatic import PMException
import pmatic.api
import os

def test_implicit_remote_init_missing_args():
    with pytest.raises(PMException):
        API = pmatic.api.init()


def test_explicit_remote_init_missing_args():
    with pytest.raises(PMException):
        API = pmatic.api.init("remote")


def test_explicit_local_init_but_remote():
    with pytest.raises(PMException):
        API = pmatic.api.init("local")


def test_local_remote_detection():
    orig_uname = os.uname

    os.uname = lambda: ('Linux', 'dev', '3.16.0-4-amd64', '#1 SMP Debian 3.16.7-ckt9-3~deb8u1 (2015-04-24)', 'x86_64')
    assert not pmatic.api.is_ccu()

    os.uname = lambda: ('Linux', 'ccu', '3.4.11.ccu2', '#1 PREEMPT Fri Oct 16 10:43:35 CEST 2015', 'armv5tejl')
    assert pmatic.api.is_ccu()
