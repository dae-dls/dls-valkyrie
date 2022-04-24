class Data:
    memoryview = None

    def __init__(self, buffer_object=None):
        if buffer_object is not None:
            self.memoryview = memoryview(buffer_object)


class MetaKeyword:
    STREAM_ID = "MAXIV_VALKYRIE_STREAM_ID"
    PACKET_TYPE = "MAXIV_VALKYRIE_PACKET_TYPE"
    PACKET_ENQUEUED_TIME = "MAXIV_VALKYRIE_PACKET_ENQUEUED_TIME"
    PACKET_UNIQUE_ID = "MAXIV_VALKYRIE_PACKET_UNIQUE_ID"
    PACKET_SEQUENCE_NUMBER = "MAXIV_VALKYRIE_PACKET_SEQUENCE_NUMBER"
    IMAGE_SEQUENCE_NUMBER = "MAXIV_VALKYRIE_IMAGE_SEQUENCE_NUMBER"
    DATA_LENGTH = "MAXIV_VALKYRIE_DATA_LENGTH"
    DTYPE = "MAXIV_VALKYRIE_DTYPE"
    SHAPE = "MAXIV_VALKYRIE_SHAPE"
    TIMESTAMP = "MAXIV_VALKYRIE_TIMESTAMP"

    # Meta keywords to help the downstream track and display drift.
    ORIGIN_ENQUEUED_TIME = "MAXIV_VALKYRIE_ORIGIN_ENQUEUED_TIME"
    DAQ_RECEIVED_TIME = "MAXIV_VALKYRIE_DAQ_RECEIVED_TIME"
    DAQ_REPUBLISHED_TIME = "MAXIV_VALKYRIE_DAQ_REPUBLISHED_TIME"
    LIVEVIEW_RECEIVED_TIME = "MAXIV_VALKYRIE_LIVEVIEW_RECEIVED_TIME"

class PacketType:
    SERVER_CAME_UP = "MAXIV_VALKYRIE_SERVER_CAME_UP"
    SERVER_WENT_DOWN = "MAXIV_VALKYRIE_SERVER_WENT_DOWN"
    START_OF_SEQUENCE = "MAXIV_VALKYRIE_START_OF_SEQUENCE"
    END_OF_SEQUENCE = "MAXIV_VALKYRIE_END_OF_SEQUENCE"
    EVENT = "MAXIV_VALKYRIE_EVENT"
    FRAME = "MAXIV_VALKYRIE_FRAME"


# ------------------------------------------------------------------------------
def new_WriterInterface(configuration):
    class_name = configuration.get("class_name")
    if class_name is None:
        raise RuntimeError("class_name missing from new_WriterInterface configuration")

    implementation = None
    if class_name == "dls::valkyrie::zmq_pubsub":
        from dls_valkyrie_lib.zmq_pubsub.writer import Writer as ZmqPubsub_Writer

        implementation = ZmqPubsub_Writer(configuration)
    elif class_name == "dls::valkyrie::zmq_pushpull":
        from dls_valkyrie_lib.zmq_pushpull.writer import Writer as ZmqPushpull_Writer

        implementation = ZmqPushpull_Writer(configuration)
    elif class_name == "dls::valkyrie::zmq_pullpush":
        from dls_valkyrie_lib.zmq_pullpush.writer import Writer as ZmqPullpush_Writer

        implementation = ZmqPullpush_Writer(configuration)
    elif class_name == "dls::valkyrie::file":
        from dls_valkyrie_lib.file.writer import Writer as File_Writer

        implementation = File_Writer(configuration)
    elif class_name == "dls::valkyrie::dummy":
        from dls_valkyrie_lib.dummy.writer import Writer as Dummy_Writer

        implementation = Dummy_Writer(configuration)
    elif class_name == "dls::valkyrie::websockets":
        from dls_valkyrie_lib.websockets.writer import Writer as Websockets_Writer

        implementation = Websockets_Writer(configuration)

    if implementation is None:
        raise RuntimeError(
            "class_name %s invalid in new_WriterInterface configuration" % (class_name)
        )

    return implementation


# ------------------------------------------------------------------------------
def new_ReaderInterface(configuration):
    class_name = configuration.get("class_name")
    if class_name is None:
        raise RuntimeError("class_name missing from new_ReaderInterface configuration")

    implementation = None
    if class_name == "dls::valkyrie::zmq_pubsub":
        from dls_valkyrie_lib.zmq_pubsub.reader import Reader as ZmqPubsub_Reader

        implementation = ZmqPubsub_Reader(configuration)
    elif class_name == "dls::valkyrie::zmq_pushpull":
        from dls_valkyrie_lib.zmq_pushpull.reader import Reader as ZmqPushpull_Reader

        implementation = ZmqPushpull_Reader(configuration)
    elif class_name == "dls::valkyrie::zmq_pullpush":
        from dls_valkyrie_lib.zmq_pullpush.reader import Reader as ZmqPullpush_Reader

        implementation = ZmqPullpush_Reader(configuration)
    elif class_name == "dls::valkyrie::dummy":
        from dls_valkyrie_lib.dummy.reader import Reader as Dummy_Reader

        implementation = Dummy_Reader(configuration)
    elif class_name == "dls::valkyrie::websockets":
        from dls_valkyrie_lib.websockets.reader import Reader as Websockets_Reader

        implementation = Websockets_Reader(configuration)

    if implementation is None:
        raise RuntimeError(
            "class_name %s invalid in new_ReaderInterface configuration" % (class_name)
        )

    return implementation
