$(function() {
  function getToolTip(source) {
    source = $(source);
    tech = source.closest('.tech');
    item = source.closest('.item');
    source = (item.length == 1) ? item : tech;
    return source.children('.tooltip');
  }

  $('.item, .tech').on('mouseover', e => {
    e.stopPropagation();
    getToolTip(e.target).show();
  });

  $('.item, .tech').on('mousemove', e => {
    getToolTip(e.target).css({ top: e.pageY - 50, left: e.pageX + 15 });
  });

  $('.item, .tech').on('mouseout', e => {
    getToolTip(e.target).hide();
  });

  function showTreeUp(tech_name) {
    let tech = $(document.getElementById('tech_' + tech_name));
    tech.removeClass('blurred');
    let prereqs = tech.data('prerequisites');
    if (prereqs === '') {
      return;
    }
    prereqs = prereqs.split(',');
    for (let prereq of prereqs) {
      showTreeUp(prereq);
    }
  }

  function showTreeDown(tech_name) {
    for (let tech of $('.tech')) {
      let prereqs = $(tech).data('prerequisites');
      if (prereqs === '') {
        continue;
      }
      prereqs = prereqs.split(',');
      if (prereqs.includes(tech_name)) {
        $(tech).removeClass('blurred');
        showTreeDown($(tech).data('name'));
      }
    }
  }

  $('.tech').on('click', e => {
    let source = $(e.target).closest('.tech');
    e.stopPropagation();
 
    $('.tech').removeClass('selected').addClass('blurred');
    source.addClass('selected');

    let tech_name = source.data('name');
    showTreeUp(tech_name);
    showTreeDown(tech_name);
  });

  $('body').on('click', e => {
    $('.tech').removeClass('selected').removeClass('blurred');
  });
});
