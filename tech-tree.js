var current = null;
$(document).ready(function() {
  $(".item").click(function(e){
    if (e.which != 1) return;
    e.stopPropagation();

    if (current == this) {
      current = null;
      $(".tech").removeClass("selected selected2 blurred");
      $(".item").removeClass("selected blurred");
      $(".path").removeClass("selected2 blurred2");
      return;
    }

    current = this;

    $(".item").removeClass("selected");
    $(this).addClass("selected");
    $(".tech").removeClass("selected selected2").addClass("blurred");
    $(".path").removeClass("selected2").addClass("blurred2");

    unblurItem($(this).attr("id"));
  });
  $(".tech").click(function(e){

    if (e.which != 1) return;
    if (current == this) return;

    current = this;
    e.stopPropagation();

    var id = $(this).attr("id");
    $(".tech").removeClass("selected selected2");
    $(this).addClass("selected");
    $(".tech").addClass("blurred");
    $(".item").removeClass("selected");
    $(".path").removeClass("selected2").addClass("blurred2");
    unblurBack(id);
    unblurForward(id);		

  });
  $(document).click(function(e) {
    if (e.which != 1) return;

    current = null;
    $(".tech").removeClass("selected blurred");
    $(".item").removeClass("selected blurred");
    $(".path").removeClass("selected2 blurred2");
  });

  $(".item, .tech").on("mouseover", function(e){
    e.stopPropagation();
    setToolTip($(e.target))
    $("#tooltip").show();
  });

  $(".item, .tech").on("mousemove", function(e){
    $("#tooltip").css({ top:e.pageY - 50, left:e.pageX + 15 });
  }); 

  $(".item, .tech").on("mouseout", function(e){
    $('#tooltip').hide();
  }); 

  $(".bonus").on("mouseover", function(e){
    e.stopPropagation();
    setToolTip2($(e.target))
    $("#tooltip2").show();
  }); 

  $(".bonus").on("mousemove", function(e){
    $("#tooltip2").css({ top:e.pageY - 10, left:e.pageX + 15 });
  }); 

  $(".bonus").on("mouseout", function(e){
    $('#tooltip2').hide();
  }); 

});

function unblurBack(id) {
  var tech = $("#"+id);
  if (!tech.length) return;

  if (tech.hasClass("selected2")) return;
  tech.addClass("selected2");
  if (tech.data("prereqs") == "") return;

  var prereqs = tech.data("prereqs").split(",");
  for (var i = 0; i < prereqs.length; i++) {
    unblurBack(prereqs[i]);
    $("#" + tech.attr('id') + "_" + prereqs[i]).addClass("selected2");
  }
}

function unblurForward(id) {
  $("#"+id).addClass("selected2");
  $(".path").each(function(){
    var pid = $(this).attr("id");
    if (pid.substring(pid.length - id.length - 1) == "_" + id) {
      if ($(this).hasClass("selected2")) return;
      $(this).addClass("selected2");
      unblurForward(pid.substring(0, pid.length - id.length - 1));
    }
  });
}

function unblurItem(id) {
  var obj = $("#"+id);
  if (obj.length == 0) return;

  var parent = obj.closest(".tech");
  unblurBack(parent.attr("id"));
  if (!obj.data("prereqs")) return;

  var prereqs = obj.data("prereqs").split(",");
  for (var i = 0; i < prereqs.length; i++) {
    unblurItem("item_"+prereqs[i]);
  }
}

function setToolTip(source) {
  if (!source.hasClass("item")) source = source.closest(".tech")

  $("#tooltiptitle").text(source.data("title"));

  if (source.data("ingredients")) {
    var ingredients = source.data("ingredients").split(",");
    $("#tooltipingredients").empty();
    for (var i = 0; i < ingredients.length; i += 2) {
      var item = $("#item_"+ingredients[i]);
      var node = $('<div class="tiplist"/>');
      var hoveritem = $('<span class="hoveritem"/>');
      hoveritem.css({ backgroundImage: $("#item_"+ingredients[i]).css("backgroundImage") })
      node.append(hoveritem);
      var boldtext = $('<strong/>')
      boldtext.append(ingredients[i+1])
      if (ingredients[i] == "time") {
        boldtext.append(' s')
      } else {
        boldtext.append(' x');
      }
      node.append(boldtext)
      var itemname = ""
      if (item.data("name")) {
        itemname = " " + item.data("name");
      }
      node.append(itemname)
      $("#tooltipingredients").append(node);
    }
    $("#tooltipingredientsheading").show();
    $("#tooltipingredients").show();
  } else {
    $("#tooltipingredientsheading").hide();
    $("#tooltipingredients").hide();
  }
}

function setToolTip2(source) {
  $("#tooltip2 > div").text(source.data("title"));
}
