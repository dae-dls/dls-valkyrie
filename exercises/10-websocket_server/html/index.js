
// -------------------------------------------------------------
// Run the read-and-process loop.

async function async_loop(runtime)
{
    var F = "async_loop";
    console.log("constructing reader");
    reader = new dls__valkyrie__websocket__Reader(runtime);
    reader.activate()
    console.log("activated reader");

    while(true)
    {
        meta = {}
        data = {}
        await reader.read(meta, data);
        console.log(F + ": got meta " + JSON.stringify(meta));
        console.log(F + ": got data length " + data.memoryview.byteLength);
    }
}

var runtime = {};

// -------------------------------------------------------------
// All elements on the page ready.

$(document).ready(function()
{
    var F = "document.ready()";
      
    // Run the read-and-process loop.
    async_loop(runtime);

});
