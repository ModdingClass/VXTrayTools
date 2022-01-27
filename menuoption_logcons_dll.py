import fileinput

def switch_logcons(path):
    for line in fileinput.input(path, inplace=True):
        trimmed = line.strip()
        newline = line
        if "logcons.dll" in trimmed:
            if trimmed.startswith("#"):
                newline = "logcons.dll\n"
            else:
                newline = "#logcons.dll\n"
        print('{}'.format(newline), end='') # for Python 3
    fileinput.close()


def read_logcons_dll_status(path):
    result = "VX Logs > ERR"
    for line in fileinput.input(path):
        trimmed = line.strip()
        if "logcons.dll" in trimmed:
            if trimmed.startswith("#"):
                result = "VX Logs "+"\u2B9E"+" file"
            else:
                result = "VX Logs "+"\u2B9E"+" console"
    #
    fileinput.close()
    return result

