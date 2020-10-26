$(document).ready(function() {
    $(".collapsible-block > *").hide();
    $(".collapsible-block .collapsible-title").show();
    $(".collapsible-block .collapsible-title").click(function() {
        $(this).parent().children().not(".collapsible-title").toggle(400);
        $(this).parent().children(".collapsible-title").toggleClass("open");
    })
});