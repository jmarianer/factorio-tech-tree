$(function() {
  function getToolTip(source) {
    source = $(source);
    tech = source.closest('.tech');
    item = source.closest('.item');
    source = (item.length == 1) ? item : tech;
    return source.children('.tooltip');
  }

  $(".item, .tech").on("mouseover", e => {
    e.stopPropagation();
    getToolTip(e.target).show();
  });

  $(".item, .tech").on("mousemove", function(e){
    getToolTip(e.target).css({ top: e.pageY - 50, left: e.pageX + 15 });
  });

  $(".item, .tech").on("mouseout", function(e){
    getToolTip(e.target).hide();
  });
});
