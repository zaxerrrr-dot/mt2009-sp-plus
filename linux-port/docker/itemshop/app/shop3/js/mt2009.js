/* MT2009_PLUS_ITEMSHOP_V3_V2: the card's quantity choice (the price on the button and the purchase link follow
   it) and the list's sort choice, as on the big servers' shop. */
(function ($) {
	/* MT2009_PLUS_ITEMSHOP_V3_V3: native scrolling instead of the shop's scrollbar plugin (mCustomScrollbar). In the
	   game's browser (IE11) the plugin moved the list a few pixels per wheel turn and animated every step over the
	   whole page; the browser's own scrolling is fast and smooth. Every call of the plugin lands here: options ->
	   the box scrolls natively; "scrollTo" / "update" / "stop" / "destroy" are answered the native way. */
	$.fn.mCustomScrollbar = function (opt, to) {
		if (typeof opt === 'string') {
			if (opt === 'scrollTo')
				this.each(function () {
					if (to === 'top') this.scrollTop = 0;
					else if (to === 'bottom') this.scrollTop = this.scrollHeight;
					else if (typeof to === 'number') this.scrollTop = Math.abs(to);
				});
			return this;
		}
		return this.addClass('mt-native-scroll');
	};

	// the lists (and the categories beside them) fill the window down to its bottom edge - the shop's fixed height
	// left a band under the last row in a 655 px window and cut the row off in a smaller one
	function fit() {
		var winH = $(window).height();
		$('.content .scrollable_container, #accountContent .scrollable_container, #landing.scrollable_container').each(function () {
			var box = $(this), top = box.offset().top;
			box.addClass('mt-native-scroll').css('height', Math.max(140, winH - top - 8) + 'px');
		});
		$('#subnavi.mt-subnavi').each(function () {
			var nav = $(this);
			nav.css('max-height', Math.max(140, winH - nav.offset().top - 8) + 'px');
		});
	}
	$(fit);
	$(window).on('load resize', fit);

	// the stylesheet hides the home page's carousel until the slider is built (the big servers' script shows it)
	$(window).on('load', function () { $('.carousell').css('visibility', 'visible'); });

	// a quantity menu opened near the bottom of the list scrolls the list so the whole menu shows
	$(document).on('click', '.list-item .zs-dropdown .dropdown-toggle', function () {
		var menu = $(this).siblings('.dropdown-menu'), box = $(this).closest('.scrollable_container');
		setTimeout(function () {
			if (!menu.is(':visible') || !box.length)
				return;
			var over = (menu.offset().top + menu.outerHeight()) - (box.offset().top + box.innerHeight()) + 8;
			if (over > 0)
				box.scrollTop(box.scrollTop() + over);
		}, 0);
	});

	$(document).on('click', '.list-item .dropdown-option.mt-qty', function (e) {
		e.preventDefault();
		var opt = $(this), item = opt.closest('.list-item'), price = parseInt(opt.attr('data-price'), 10);
		item.find('.dropdown-selection').text(opt.attr('data-text')).attr('data-count', opt.attr('data-count'));
		item.find('.btn-price .end-price').text(String(price).replace(/\B(?=(\d{3})+(?!\d))/g, '.')).attr('data-value', price);
		// MT2009_PLUS_ITEMSHOP_V3_V4: the price button opens the item's window with this quantity chosen
		item.find('.btn-price.mt-price-info').attr('href', opt.attr('data-href'));
		// MT2009_PLUS_ITEMSHOP_V3_V3: back to the price button by the shop's own classes - the inline display:none
		// this put on "Kup" before won over the stylesheet's .buy-now, so after a quantity the price button vanished
		// and no "Kup" came (the owner: 20 Zwojow Blogoslawienstwa, nothing happened).
		item.find('.buy-now').removeClass('buy-now');
		item.find('.btn-buy, .btn-price').css('display', '');
		opt.closest('.zs-dropdown').removeClass('open');
	});
	// MT2009_PLUS_ITEMSHOP_V3_V4: the card's price button opens the item's window (fancybox) - not the shop's own
	// "price turns into Kup" step (javascript_.js setItemHover, bound on the body when the page is ready).
	$(function () {
		$('body').undelegate('.list-item .btn-price', 'click.buynow');
	});

	// MT2009_PLUS_ITEMSHOP_V3_V5: a group's subcategories in the panel right of the category strip (the big servers'
	// shop): opens on hover and on a click of the group's tile (hover alone is not sure in the game's browser), closes a
	// moment after the mouse leaves tile and panel, on a click elsewhere, on scrolling or resizing. The panel is fixed
	// (the strip's own scrolling would cut it off), placed here beside the tile and kept inside the window.
	var flyTimer = null;
	function flyClose(li) {
		(li || $('#subnavi li.mt-fly-open')).removeClass('mt-fly-open');
	}
	function flyOpen(li) {
		clearTimeout(flyTimer);
		flyClose($('#subnavi li.mt-fly-open').not(li));
		var tile = li.children('.btn-catitem'), panel = li.children('.mt-flyout'), off = tile.offset(),
			top = off.top - $(window).scrollTop(), left = off.left - $(window).scrollLeft() + tile.outerWidth();
		li.addClass('mt-fly-open');
		var h = panel.outerHeight(), winH = $(window).height();
		if (top + h > winH - 4)
			top = Math.max(4, winH - h - 4);
		panel.css({ top: top + 'px', left: left + 'px' });
	}
	$(document).on('mouseenter', '#subnavi li.mt-has-sub', function () {
		flyOpen($(this));
	});
	$(document).on('mouseleave', '#subnavi li.mt-has-sub', function () {
		var li = $(this);
		clearTimeout(flyTimer);
		flyTimer = setTimeout(function () { flyClose(li); }, 300);
	});
	$(document).on('click', '#subnavi li.mt-has-sub > .btn-catitem', function (e) {
		e.preventDefault();
		var li = $(this).parent();
		if (li.hasClass('mt-fly-open') && !li.data('mtJustOpened'))
			flyClose(li);
		else
			flyOpen(li);
	});
	// a click right after the hover opened it keeps it open (the hover and the click of one movement)
	$(document).on('mouseenter', '#subnavi li.mt-has-sub', function () {
		var li = $(this);
		li.data('mtJustOpened', true);
		setTimeout(function () { li.data('mtJustOpened', false); }, 400);
	});
	$(document).on('click', function (e) {
		if (!$(e.target).closest('#subnavi li.mt-has-sub').length)
			flyClose();
	});
	$(window).on('resize', function () { flyClose(); });
	$(function () {
		$('#subnavi.mt-subnavi').on('scroll', function () { flyClose(); });
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
