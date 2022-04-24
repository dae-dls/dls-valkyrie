# Valkyrie Protocol Libraray

## Summary

Python library which implements a simple carrier-independent interface for unidirectional data flow.

The data acquisition developer needs a way to transfer streaming data from point of acquisition to a receiver for processing or saving.
It is important that different sending and receiving programs talk the same protocol, and that this be robust, reliable and reusable.
This library implements a high level layer for fast data transfer which which wraps details of the underlying carrier.

This is a Python library with API with methods for client and server to connect and data transfer to take place.

## Usage

```python
from dls_valkyrie_lib.valkyrie import new_ReaderInterface
from dls_valkyrie_lib.valkyrie import new_WriterInterface
from dls_valkyrie_lib.valkyrie import Data as ValkyrieData

# Create the configuration for reader and writer.
reader_configuration = {"class_name": "dls_::valkyrie::zmq_pubsub", "endpoint": "tcp://localhost:15000"}
writer_configuration = {"class_name": "dls_::valkyrie::zmq_pubsub", "endpoint": "tcp://*:15000"}

# Create a reader.
reader = new_ReaderInterface(configuration)

# Activate the reader which the writers will connect to.
reader.activate()

# Wait for data to arrive.
meta = {}
data = ValkyrieData()
reader.read(meta, data)

# Now access the bytes in the wrapper's memoryview member.
print("data length is %d" % (data.memoryview.nbytes))

...

# Create a writer.
writer = new_WriterInterface(configuration)

# Activate the writer to make connection to the reader.
writer.activate()

# Create meta data to send with the packet.
meta = {"some": "thing"}

# Make a data array.
mybytes = bytearray(1000)

# Wrap a valkyrie data wrapper memoryview around the raw data.
data = ValkyrieData(mybytes)

# Write the data.
writer.write(meta, data)
```


## Requirements

For brief design document, see [valkyrie API brainstorm result June 2019](https://gitlab.dls.lu.se/daverb/documents-and-presentations/-/blob/master/Valkyrie/valkyrie%20API%20brainstorm%20result%20June%202019.pdf)

This library implements a simple interface for unidirectional data flow.

Its use case is in a detector-filewriter network pair, where large amounts of data flow from detector to filewriter.

As of current writing, Valkyrie is implemented on these underlying carriers
1. zmq (publish/subscribe) Writer and Reader - Publish/subscribe. One sender, many receivers. No delivery garuantee
1. zmq (push/pull) Writer and Reader - Push/pull. One sender, one or more receivers. Round Robin.
1. zmq (pull/push) Writer and Reader - Pull/push. One receiver, many senders. Gather scheme.
1. file Writer - Writes bytes to a file.
1. dummy Writer and Reader - Does nothing.


## Installation
- yum install lib-dls-common-python (automatic dependency in the setup.py)
- pip install pyzmq==18.0.1
- pip install numpy 

## Docker for Development
- https://gitlab.dls.lu.se/kits-dls/docker-playground/tree/master/ce7-py36
- available on docker.dls.lu.se/docker-playground-ce7-py36

## API

### Overview TBD: REWORK THIS BASED ON ACTUAL USE CASES FROM EXPERIENCE
Valkyrie implements one way flow only.  
Valkyrie data is packetized.  
Each packet is composed of a meta part (json) and a data part (raw bytes);
Each packet as atomic: you get all parts of the packet or none of it.  
Servers are tolerant of no clients connected and runs anyway.  
Servers provide zero buffering so a missed packet is missed forever.  
Clients are tolerant (will wait) if server not running.  
Like FedEx, this API ships packets only but does not look in them.  
The Writer publishes packets.
The Reader connects to the writer and listens for packets.  
Multiple Readers may connect to the same Writer.  
In some cases, all Readers are presented with the same set of packets, in others, packets are shared in round-robin fashion.
Delivery guarantee depends on the type of communication.
If no Reader has connected, the Writer drops the packets.  
If the Reader is too slow to process all packets, the Writer will drop the ones which cannot be received in time.  
All metadata is encoded as JSON.  Valkyrie imposes no specification on the JSON.  The writer and reader must agree on the keywords to be used.  
Valkyrie considers all data to be bytes.  The writer and reader must agree on the mapping of the byte stream to structures or arrays.  
The Python implementation of Valkyrie uses memoryview as the mechanism to map the bytes for transfer.  For purposes of mutability in the API, the memoryview is a public member in a Valkyrie Data object.  

### Common to Reader and Writer

#### configuration
- shall be a Dict object
- shall have class_name string item
- shall typically also have endpoint string item

#### class_name 
- shall be one of a known set of strings
- current set is:
  * `zmq_pubsub` - Publish/Subscribe pattern. Communication per topic, or on all topics
  * `zmq_pushpull` - One Pusher and one-or-many Pullers
  * `zmq_pullpush` - One or many Pullers and one Pusher
  * `file` - Outputs stream to file
  * `dummy` - Outputs stream to console

#### endpoint 
- shall be specific to the class_name
- for example, zmq_pubsub expects a format like: tcp://localhost:15081
- future carriers may have different endpoint formats

#### meta
- shall be a Dict object
- furthermore, all items shall be serializable by json.dumps
- an empty Dict is an acceptable meta
- contents of meta is not specified here, but meant to be understood between writer and reader

#### ValkyrieData object
- shall be an object containing a public instance variable named memoryview
- memoryview shall be a Python memoryview interface
- a value of None is acceptable and treated as a zero-length memoryview

### Writer API 

#### Specification
##### new_WriterInterface(configuration)
- returns constructed object instance of writer
- shall not do any network activities
- shall throw exception if an instance cannot be created

##### writer.activate()
- shall open/bind/listen or otherwise prepare network to allow Reader connection
- shall not immediately send any data on the connection

##### write(meta, data)
- shall put the meta and the data on the wire
- shall not block
- any unsent packets already queued to a Reader shall be deleted without sending
- meta object with no items is acceptable
- data shall be a ValkyrieData object, whose memoryview instance is set to the data
- data.memoryview of None is acceptable, and will be treated like zero-length data
- zero-length data.memoryview is acceptable

#### Annotated Example
```
from dls_valkyrie_lib.valkyrie import new_WriterInterface
from dls_valkyrie_lib.valkyrie import Data as ValkyrieData

# Specify the desired underlying carrier.
class_name = "dls_::valkyrie::zmq_pubsub"

# Specify the network address.
endpoint = "tcp://*:15000"

# Create the configuration.
configuration = {"class_name": class_name, "endpoint": endpoint, "log": {"level": "DEBUG"}}

# Create a writer.
writer = new_WriterInterface(configuration)

# Activate the writer to begin accepting connections from readers.
writer.activate()

# Create meta data to send with the packet.
meta = {"some": "thing"}

# Make a data array.
mybytes = bytearray(1000)

# Wrap a valkyrie data wrapper memoryview around the raw data.
data = ValkyrieData(mybytes)

# Write the data.
writer.write(meta, data)
```

### Reader API

#### Specification
##### new_ReaderInterface( configuration)
- returns constructed object instance of reader
- shall not do any network activities
- shall throw exception if an instance cannot be created

##### reader.activate()
- shall connect/open/create or otherwise attempt to contact Writer
- shall not immediately send any data on the connection
- shall not fail if Writer cannot immediately be contacted

##### read(meta, data)
- shall read the meta and the data from the wire
- shall block until message is received
- meta object will have items replaced or added to it from the received meta data 
- data shall be a ValkyrieData object
- data.memoryview will be returned as a memoryview to the data received
- a returned zero-length data.memoryview is possible if the caller sent no data

#### Annotated Example
```
from dls_valkyrie_lib.valkyrie import new_ReaderInterface
from dls_valkyrie_lib.valkyrie import Data as ValkyrieData

# Specify the desired underlying carrier.
class_name = "dls_::valkyrie::zmq_pubsub"

# Specify the network address.
endpoint = "tcp://localhost:15000"

# Create the configuration.
configuration = {"class_name": class_name, "endpoint": endpoint, "log": {"level": "DEBUG"}}

# Create a reader.
reader = new_ReaderInterface(configuration)

# Activate the reader to connect to the Writer.
reader.activate()

# Read the data.
meta = {}
data = ValkyrieData()
reader.read(meta, data)

# Now access the bytes in the wrapper's memoryview member.
print("data length is %d" % (data.memoryview.nbytes))

```

## EXAMPLES
Please see the test and example programs for samples of usage.

## TESTS
### make run-test-01-writer_reader
This shows a simple writer thread and reader thread with one message sent.

### make run-test-02-missed_unthreaded
This sets up a writer and reader in the same thread, with the writer giving more messages than the reader can handle.
	
### make run-test-03-missed_threaded
This sets up a writer and reader in their own threads, with the writer giving more messages than the reader can handle.

### make run-test-04-dataless
This verifies that the messages can transmit even if no data.

### make run-test-05-speed
This runs a timed test with writer running at full speed, and reader eating up as much as possible.  A timing report is issued at the end.

## PROTOCOL DETAILS

### ZMQ_PUBSUB Protocol
The protocol is very simple:
1. each message shall have two parts
1. part 1 shall either be zero-length or be a string encoded in JSON
1. part 2 shall either be zero-length or shall be data bytes
1. the sender shall set minimum highwater mark for sending

## Recommended practices

### Sending an Image Sequence

These are recommendations for meta contents for a sequence of images:
#### First packet in sequence
    {
        MAXIV_VALKYRIE_PACKET_TYPE: "MAXIV_VALKYRIE_START_OF_SEQUENCE",
        MAXIV_VALKYRIE_PACKET_ENQUEUED_TIME: 13402532354.235262,
        MAXIV_VALKYRIE_PACKET_SEQUENCE_NUMBER: 1
    }

#### Image packets
    {
        MAXIV_VALKYRIE_PACKET_TYPE: "MAXIV_VALKYRIE_FRAME",
        MAXIV_VALKYRIE_PACKET_SEQUENCE_NUMBER: 2,
        MAXIV_VALKYRIE_IMAGE_SEQUENCE_NUMBER: 1,
        MAXIV_VALKYRIE_DATA_LENGTH: 1023462,
        MAXIV_VALKYRIE_DTYPE: "uint32",
        MAXIV_VALKYRIE_SHAPE: {1035, 1060}
    }

#### Last packet in sequence
    {
        MAXIV_VALKYRIE_PACKET_TYPE: "MAXIV_VALKYRIE_END_OF_SEQUENCE",
        MAXIV_VALKYRIE_PACKET_SEQUENCE_NUMBER: 23452
    }



## TODO
### TODO overall
- improve test coverage
- improve performance in cases where meta-only is being sent, by reducing multipart to 1
- verify the zmq recv_timeout in the face multipart message receive
- add tests for multiple clients receiving from one server
- hook logging into standard python logger
- add tests for Dummy and File