$(".canon-list>li").click(function(){
    if($(this).hasClass("collapsed")) {
        $(".canon-list>li").addClass("collapsed");
        $(this).removeClass("collapsed");
    }
});
$(".canon-list>li>.wrapper>.collapse-btn").click(function(e){
    if(!$(this).parent().parent().hasClass("collapsed")) {
        $(this).parent().parent().addClass("collapsed");
        e.stopPropagation();
    }
});