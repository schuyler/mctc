$(document).ready(function() {
    $('table tbody tr').bind("click", function() {
        var elem = $(this).find("a");
        if (elem.length != 0) {
            window.location = elem.attr("href");
        };
    return false;
    });   
    $("#search input").labelify();
});
