import argparse
import json
import zmq

import dls_valkyrie_lib


# ----------------------------------------------------------
def version():
    """
    Current version.
    """

    return dls_valkyrie_lib.__version__

# ----------------------------------------------------------
def meta(given_meta=None):
    """
    Returns version information as a dict.
    Adds version information to given meta, if any.
    """
    s = {}
    s["dls_valkyrie_lib"] = version()

    s["zmq_version"] = zmq.zmq_version()
    s["pyzmq_version"] = zmq.pyzmq_version()

    try:
        import websockets
        s["websockets"] = websockets.__version__
    except Exception as exception:
        s["websockets"] = str(exception)

    if given_meta is not None:
        given_meta.update(s)
    else:
        given_meta = s
    return given_meta


# ----------------------------------------------------------
def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--json",
        action="store_true",
        help="Print version stack in json.",
    )

    # -------------------------------------------------------------------------
    given_args, remaining_args = parser.parse_known_args()

    if given_args.json:
        print(json.dumps(meta(), indent=4))
    else:
        print(version())


# ----------------------------------------------------------
if __name__ == "__main__":
    main()
