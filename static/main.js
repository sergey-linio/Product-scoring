$(document).ready(function () {

  $('.b-select__btn').click(function () {
    window.location.href = $('.b-select__form').val();
  });

  $('.b-input-float').on('input', function() {
    this.value = this.value.replace(/[^0-9.-]/g, '').replace(/(\..*)\./g, '$1').replace(/(.+)\-/g, '$1');
  });

  $('.b-submit').click(function () {
    $.ajax({
      url: '/api/send_scores/' + $('.breadcrumb li.active').data('id'),
      type: 'POST',
      data: $('.b-form').serialize(),
      success: function () {
        $('.b-alert').fadeIn('slow');
      }
    })
  });

})
