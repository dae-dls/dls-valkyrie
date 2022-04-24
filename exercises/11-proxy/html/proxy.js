// This file is very much a prototype!
// TODO:
// - make a javascript class out of the functions
// - use defined constants for the dispatcher strings
// - better error handling

// -------------------------------------------------------------
function send(data)
{
    var url = "http://w-daverb-pc-3:15038";
    var $request = $.ajax(
        {
            url: url,
            cache: false,
            data: data,
            method: "POST",
            processData: false,
            contentType: "application/json"
        }
    );

    // Handle the response when it comes.
    $request.done(function(response) 
    {
        // First, any error obviates anything else.
        var message = response["dls::common::dispatcher::Keywords::ERROR"];

        // Some dispatchers return a confirmation string.
        if (message === undefined)
            message = response["dls::common::dispatcher::Keywords::CONFIRMATION"];

        // A request for incident summaries will reply with a structure.
        if (message === undefined)
        {
            message = response["dls::common::dispatcher::Keywords::INCIDENT_SUMMARIES"];
            if (message !== undefined)
            {
                show_incident_summaries(message);
                message = "got new incident summaries, displayed below";
            }
        }

        if (message === undefined)
            message = "request finished but no error and no confirmation"
        show_response(message);
    });
    
    // Handle the response failure if it comes.
    $request.fail(function(jqXHR, message) 
    {
        show_response(message);
    });
}


// -------------------------------------------------------------
function show_incident_summaries(incident_summaries)
{
    var html = "<table>";
    var first = true;
    for(var tag in incident_summaries)
    {
        var incident_summary = incident_summaries[tag];
        if (first)
        {
            html += "<tr><th>tag</th>"
            for (var col in incident_summary)
            {
                if (col != "count")
                    col += " ms";
                html += "<th>" + col + "</th>";
            }
            html += "</tr>";
            first = false;
        }

        html += "<tr>"
        first = true;
        for (var col in incident_summary)
        {
            if (first)
            {
                html += "<td>" + tag.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;') + "</td>";
                first = false;
            }
            html += "<td>" + incident_summary[col] + "</tdh>";
        }
        html += "</tr>"

    }
    html += "</table>";
    $("#incident_summaries").html(html);
    $("#incident_summaries").show();
}

// -------------------------------------------------------------
function send_arm()
{
    send('{"dls::common::dispatcher::Keywords::COMMAND": "dls::common::dispatcher::Commands::ARM", ' +
      'stream_processor: {' +
      'class_name: sorter, source: "tcp://localhost:15000", ' +
      'xyt_writer: {class_name: none}, ' +
      'rawpackets_writer: {class_name: none}' +
      '}}');
}

// -------------------------------------------------------------
function send_stop()
{
    send('{"dls::common::dispatcher::Keywords::COMMAND": "dls::common::dispatcher::Commands::STOP"}');
}

// -------------------------------------------------------------
function send_exit()
{
    send('{"dls::common::dispatcher::Keywords::COMMAND": "dls::common::dispatcher::Commands::EXIT"}');
}

// -------------------------------------------------------------
function send_get_incident_summaries()
{
    send('{"dls::common::dispatcher::Keywords::COMMAND": "dls::common::dispatcher::Commands::GET_INCIDENT_SUMMARIES"}');
}

// -------------------------------------------------------------
function show_response(text)
{
    $("#response").text(text);
}

// -------------------------------------------------------------
$(document).ready(function()
{
    $("#arm_button").click(function(jquery_event_object) {send_arm();});
    $("#stop_button").click(function(jquery_event_object) {send_stop();});
    $("#get_incident_summaries_button").click(function(jquery_event_object) {send_get_incident_summaries();});
    $("#exit_button").click(function(jquery_event_object) {send_exit();});
    $("BUTTON").button();
});
