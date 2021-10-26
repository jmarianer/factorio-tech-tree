$(function() {
  // Tooltip for technologies and items
  let toolTipDiv = $("#tooltip");
  function setToolTip(source) {
    source = $(source);
    tech = source.closest('.tech');
    item = source.closest('.item');

    source = (item.length == 1) ? item : tech;
    toolTipDiv.text(source.data('title'));
  }

  $(".item, .tech").on("mouseover", e => {
    e.stopPropagation();
    setToolTip(e.target);
    toolTipDiv.show();
  });

  $(".item, .tech").on("mousemove", function(e){
    toolTipDiv.css({ top: e.pageY - 50, left: e.pageX + 15 });
  });

  $(".item, .tech").on("mouseout", function(e){
    toolTipDiv.hide();
  });
});
