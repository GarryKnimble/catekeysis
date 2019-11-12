$(".paragraph-list>li").click(function(){
    if($(this).hasClass("collapsed")) {
        $(".paragraph-list>li").addClass("collapsed");
        $(this).removeClass("collapsed");
    }
});
$(".paragraph-list>li>.wrapper>.collapse-btn").click(function(e){
    if(!$(this).parent().parent().hasClass("collapsed")) {
        $(this).parent().parent().addClass("collapsed");
        e.stopPropagation();
    }
});