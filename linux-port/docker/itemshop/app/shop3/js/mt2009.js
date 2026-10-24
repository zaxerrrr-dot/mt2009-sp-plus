/* MT2009_PLUS_ITEMSHOP_V3_V2: the card's quantity choice (the price on the button and the purchase link follow
   it) and the list's sort choice, as on the big servers' shop. */
(function ($) {
	// the stylesheet hides the home page's carousel until the slider is built (the big servers' script shows it)
	$(window).on('load', function () { $('.carousell').css('visibility', 'visible'); });
	$(document).on('click', '.list-item .dropdown-option.mt-qty', function (e) {
		e.preventDefault();
		var opt = $(this), item = opt.closest('.list-item'), price = parseInt(opt.attr('data-price'), 10);
		item.find('.dropdown-selection').text(opt.attr('data-text')).attr('data-count', opt.attr('data-count'));
		item.find('.btn-price .end-price').text(price.toLocaleString('de-DE')).attr('data-value', price);
		item.find('.btn-buy').attr('href', opt.attr('data-href'));
		item.find('.btn-buy').hide();
		item.find('.btn-price').show();
		opt.closest('.zs-dropdown').removeClass('open');
	});
	$(document).on('click', '#formArticlesSort .sort-option', function (e) {
		e.preventDefault();
		var mode = $(this).attr('data-value');
		$('#formArticlesSort .sort-option').removeClass('active');
		$(this).addClass('active');
		$('#formArticlesSort .buttonText').text($(this).text());
		$(this).closest('.dropdown').removeClass('open');
		$('.item-list').each(function () {
			var list = $(this), items = list.children('.list-item').get();
			items.sort(function (a, b) {
				var A = $(a), B = $(b);
				if (mode === 'name-up' || mode === 'name-down') {
					var r = A.attr('data-sort-name').localeCompare(B.attr('data-sort-name'), 'pl');
					return mode === 'name-up' ? r : -r;
				}
				if (mode === 'price-up' || mode === 'price-down') {
					var d = parseInt(A.attr('data-sort-price'), 10) - parseInt(B.attr('data-sort-price'), 10);
					return mode === 'price-up' ? d : -d;
				}
				return parseInt(A.attr('data-sort-sort'), 10) - parseInt(B.attr('data-sort-sort'), 10);
			});
			$.each(items, function (i, el) {
				$(el).toggleClass('last-in-line', (i + 1) % 3 === 0);
				list.append(el);
			});
		});
	});
})(jQuery);
