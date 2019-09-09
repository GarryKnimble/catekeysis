$(".search-form input").keypress(function(e){
    if(e.which == 13){
        e.preventDefault();
        $(".search-form").submit();
    }
});