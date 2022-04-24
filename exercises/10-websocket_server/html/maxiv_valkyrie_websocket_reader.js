// --------------------------------------------------------------------

// inherit the base methods and variables
dls__valkyrie__websocket__Reader.prototype = new dls__common__Base();

// provide an explicit name for the base class
dls__valkyrie__websocket__Reader.prototype.base = dls__common__Base.prototype;

// override the constructor
dls__valkyrie__websocket__Reader.prototype.constructor = dls__valkyrie__websocket__Reader;

// -------------------------------------------------------------------------------
// constructor (functioning as a prototype, this constructor cannot take arguments)

function dls__valkyrie__websocket__Reader(runtime, name, classname)
{
	// we are not doing a prototype construction?
    if (arguments.length > 0)
    {
        var F = "dls__valkyrie__websocket__Reader";

        // call the base class constructor helper 
        dls__valkyrie__websocket__Reader.prototype.base.constructor.call(
            this,
            runtime,
            classname != undefined? classname: F);
    }

    this.is_activated = false;
    this.socket = undefined;
    this.meta = undefined;
    this.data = undefined;
    this.message_queue = new Array();

} // end constructor
                      
// -------------------------------------------------------------------------------
// Connect to server.

dls__valkyrie__websocket__Reader.prototype.activate = function(meta, data)
{
    var F = "dls__valkyrie__websocket__Reader::activate";

    if (this.is_activated === false)
    {
        var endpoint = "ws://localhost:15038";

        console.log(F + ": connecting to endpoint " + endpoint);

        this.socket = new WebSocket(endpoint);
        this.socket.binaryType = "arraybuffer";

        var that = this;

        // Handler for a new message arrived.
        this.socket.onmessage = function(event) 
        {
            event_type = typeof(event.data)
            if (event_type === "string")
            {
                that.data = undefined;
                that.meta = JSON.parse(event.data);
            }
            else
            {
                that.data = new DataView(event.data);

                // Remove any last message hung up in the queue.
                that.message_queue.shift();

                // Add message to queue to be picked up by the next read method.
                that.message_queue.push({meta: that.meta, data: that.data});
            }
        }
    }
  
} // end method
                  
// -------------------------------------------------------------------------------
// Read the next available message.

dls__valkyrie__websocket__Reader.prototype.read = async function(meta, data)
{
    var F = "dls__valkyrie__websocket__Reader::read";

    var that = this;
    return new Promise(
        async function(result, reject)
        {
            i = 0;
            got_message = false;
            while(true)
            {
                // This is the recv_timeout_milliseconds.
                if (i++ >= 2000)
                    break;
                    
                message = that.message_queue.shift();
        
                if (message !== undefined)
                {
                    $.extend(true, meta, message.meta);
                    data.memoryview = message.data;
                    result(message);
                    got_message = true;
                    break;
                }
        
                await new Promise(resolve => setTimeout(resolve, 1));
            }
        
            if (!got_message)
                console.log(F + ": overslept");
        }
    );

} // end method
