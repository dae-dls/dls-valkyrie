// --------------------------------------------------------------------

function dls__common__Base(runtime, classname)
{
    if (arguments.length > 0)
    {
        var F = "dls__common__Base";

        // operate within this environment
        this.runtime = runtime;

        // remember what class we are
        this.classname = classname;
    }
} // end constructor
