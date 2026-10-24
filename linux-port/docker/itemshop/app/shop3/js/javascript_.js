/*
 * classie - class helper functions
 * from bonzo https://github.com/ded/bonzo
 * 
 * classie.has( elem, 'my-class' ) -> true/false
 * classie.add( elem, 'my-new-class' )
 * classie.remove( elem, 'my-unwanted-class' )
 * classie.toggle( elem, 'my-class' )
 */
(function(d) {
    function a(g) {
        return new RegExp("(^|\\s+)" + g + "(\\s+|$)")
    }
    var c, e, f;
    if ("classList" in document.documentElement) {
        c = function(g, h) {
            return g.classList.contains(h)
        };
        e = function(g, h) {
            g.classList.add(h)
        };
        f = function(g, h) {
            g.classList.remove(h)
        }
    } else {
        c = function(g, h) {
            return a(h).test(g.className)
        };
        e = function(g, h) {
            if (!c(g, h)) {
                g.className = g.className + " " + h
            }
        };
        f = function(g, h) {
            g.className = g.className.replace(a(h), " ")
        }
    }

    function b(h, j) {
        var g = c(h, j) ? f : e;
        g(h, j)
    }
    d.classie = {
        hasClass: c,
        addClass: e,
        removeClass: f,
        toggleClass: b,
        has: c,
        add: e,
        remove: f,
        toggle: b
    }
})(window);
jQuery.fn.exists = function() {
    return jQuery(this).length > 0
};
var zs = zs || {};
zs.ev = zs.ev || {};
zs.fn = zs.fn || {};
zs.data = zs.data || {};
zs.module = zs.module || {};
zs.debug = zs.debug || false;
zs.fn.track = zs.fn.track || {};
zs.data.loca = zs.data.loca || {};
zs.data.directPurchaseEnabled = zs.data.directPurchaseEnabled || false;
zs.data.screen = getScreenDimensions();
zs.module.small = zs.module.small || false;
zs.data.textLimit = {
    core: 100,
    "4story": 90
};
zs.data.ttip = zs.data.ttip || {};
zs.data.ttip = {
    delay: 400,
    defaultPosition: "bottom",
    fadeIn: 100,
    attribute: "tooltip-content",
    maxWidth: 300
};

function getScreenDimensions() {
    if (window.innerWidth !== undefined && window.innerHeight !== undefined) {
        var a = window.innerWidth;
        var b = window.innerHeight
    } else {
        var a = document.documentElement.clientWidth;
        var b = document.documentElement.clientHeight
    }
    return {
        w: a,
        h: b
    }
}

function initFocusClear() {
    $("input[type=password], input[type=text], input[type=email], textarea").not("input[name=searchString]").each(function() {
        var a = this.value;
        $(this).focus(function() {
            if (this.value === a) {
                this.value = ""
            }
        });
        $(this).blur(function() {
            if (this.value === "") {
                this.value = a
            }
        })
    })
}

function setItemHover() {
    $("body").delegate(".list-item", "mouseenter.itemhover", function(a) {
        a.preventDefault();
        $(this).addClass("hover")
    }).delegate(".list-item", "mouseleave.itemhover", function(a) {
        a.preventDefault();
        var b = a.target || a.srcElement;
        if ($(b).is("i")) {
            return
        }
        $(this).removeClass("hover");
        $(this).find(".buy-now").removeClass("buy-now").end().find(".btn-buy").css("display", "auto")
    }).delegate(".list-item .btn-price", "click.buynow", function(a) {
        $(this).addClass("buy-now").parent().find(".btn-buy").addClass("buy-now")
    })
}
zs.fn.track.pageload = function() {
    zs.data.timeLoad = (new Date()).getTime();
    var a = (zs.data.timeLoad - zs.data.timeBefore) / 1000;
    new Image().src = shop_url + "/images/this/pixel.gif?page_load=" + a
};
zs.fn.track.timePast = function(b) {
    zs.data.thisTime = (new Date()).getTime();
    var a = (zs.data.thisTime - zs.data.timeBefore) / 1000;
    if (b && console && console.log) {
        console.log(a)
    }
    return a
};
window.onload = function() {
    zs.fn.track.pageload()
};

function cardMargin() {
    $("ul.item-list.card").each(function(a, b) {
        $(b).find("li.shown").each(function(c, d) {
            if (c % 3 === 2) {
                $(d).addClass("last-in-line")
            }
        })
    });
    $("div.no-scroller").each(function(a, b) {
        $(b).find("div.list-item ").each(function(c, d) {
            if (c % 3 === 2) {
                $(d).addClass("last-in-line")
            }
        })
    });
    $(".list h3.subcategory li.shown").first().addClass("first-element")
}

function customScroll() {
    $(".content .scrollable_container").mCustomScrollbar("update")
}

function pseudoSelect(a) {
    a.find(".select-input a").click(function() {
        var c = a;
        var b = c.find(".select-input .account-infos").html().replace(/\s/g, "").replace(/data-[-_\w]+="[^"]*"/g, "");
        c.find(".select-option ul li").show().each(function() {
            if ($(this).find(".account-infos").html().replace(/\s/g, "").replace(/data-[-_\w]+="[^"]*"/g, "") === b) {
                $(this).hide();
                return false
            }
        });
        a.find(".select-option ul").toggle();
        a.find(".select-option ul").mCustomScrollbar()
    });
    a.find(".select-option ul li a").click(function(b) {
        if ($(this).closest(".pseudo-dropdown").hasClass("playerSelection")) {
            b.preventDefault();
            selectPlayer($(this), playerSelectDropdownChanged, closePseudoSelect)
        } else {
            if ($(this).closest(".pseudo-dropdown").hasClass("purchaseSelection")) {
                b.preventDefault();
                selectPlayerForPurchase($(this))
            } else {
                if ($(this).closest(".pseudo-dropdown").hasClass("distributionSelection")) {
                    b.preventDefault();
                    selectPlayerForDistribution($(this))
                } else {
                    if ($(this).closest(".pseudo-dropdown").hasClass("relationType")) {
                        b.preventDefault();
                        zs.fn.selectRecipientType($(this))
                    } else {
                        changePseudoSelect($(this))
                    }
                }
            }
        }
    });
    $(document).bind("click", function(c) {
        var b = $(c.target);
        if (!b.parents().hasClass("pseudo-dropdown")) {
            a.find(".select-option ul").hide()
        }
    })
}

function changePseudoSelect(b) {
    var g = b.find(".account-infos").html(),
        a = b.find(".account-infos p"),
        c = zs.data.currency || 1,
        e, d, f;
    b.closest(".pseudo-dropdown").find(".select-input .account-infos").html(g);
    closePseudoSelect(b);
    e = a.attr("data-server-id");
    d = a.attr("data-player-id");
    f = a.data("data-transaction-id");
    zs.fn.initPurchaseLink(false, false, c, e, d, f)
}

function closePseudoSelect(a) {
    a.closest(".select-option ul").hide()
}

function selectPlayer(e, d, f) {
    var c = e.attr("href") || e.data("url") || false;
    var b = e.data("serverId") || false;
    var a = e.data("playerId") || false;
    if (c === false || b === false || a === false) {
        if (f) {
            f(e)
        }
        return
    }
    $.ajax({
        type: "post",
        url: c,
        data: {
            serverId: b,
            playerId: a
        },
        dataType: "json",
        success: function(g) {
            if (g === true) {
                if (d) {
                    d(e)
                }
            } else {
                if (f) {
                    f(e)
                }
            }
        },
        error: function() {
            if (f) {
                f(e)
            }
        }
    })
}

function selectPlayerForPurchase(j) {
    var f = j.data("serverId") || false,
        d = j.data("playerId") || false,
        a = j.data("purchasingAllowed") || false,
        g = j.data("purchasingReason") || false,
        h = j.data("visibleReason") || false,
        b = (g) ? g : h,
        k = zs.data.loca.LOCA_BUY_NOW_BUTTON || "",
        e = zs.data.loca.LOCA_BUY_BUTTON || "",
        c, l;
    if (typeof b == "boolean") {
        b = ""
    }
    if (f === false || d === false) {
        closePseudoSelect(j)
    }
    if (typeof zs.fn.initPurchaseLink === "function") {}
    if (!zs.data.directPurchaseEnabled) {
        l = $("#buy .btn-price");
        c = $("#buy .btn-buy").hide();
        if (a) {
            c.hide();
            l.removeClass("btn-disabled ttip fancybox fancybox.ajax").html(e).prop("disabled", false).removeAttr("tooltip-content").show();
            $("#tiptip_holder").remove()
        } else {
            c.removeClass("fancybox fancybox.ajax").hide();
            l.addClass("btn-disabled ttip").html(zs.data.loca.LOCA_ITEM_NOT_AVAILABLE).attr("tooltip-content", b).show().tipTip({
                delay: 0,
                defaultPosition: "bottom",
                fadeIn: 100,
                attribute: "tooltip-content",
                maxWidth: 300
            })
        }
    } else {
        c = $("#buy .btn-buy");
        l = $("#buy .btn-price").hide();
        if (a) {
            c.removeClass("btn-disabled ttip").addClass("fancybox fancybox.ajax").html(k).attr("tooltip-content", "").prop("disabled", false).show();
            $("#tiptip_holder").remove()
        } else {
            c.removeClass("fancybox fancybox.ajax").addClass("btn-disabled ttip").html(zs.data.loca.LOCA_ITEM_NOT_AVAILABLE).attr("tooltip-content", b).show().tipTip({
                delay: 0,
                defaultPosition: "bottom",
                fadeIn: 100,
                attribute: "tooltip-content",
                maxWidth: 300
            })
        }
    }
    $("#buy .btn-disabled").click(function(m) {
        m.preventDefault();
        return
    });
    playerSelectDropdownChanged(j)
}

function selectPlayerForDistribution(c) {
    var b = c.data("serverId") || false;
    var a = c.data("playerId") || false;
    if (b === false || a === false) {
        closePseudoSelect(c)
    }
    if (typeof initDistributionLink === "function") {
        initDistributionLink(false, false, b, a)
    }
    changePseudoSelect(c)
}
zs.fn.selectRecipientType = function(c) {
    var b = c.find("p").data("recipientType") || -1;
    var a = false;
    if (!zs.data.directPurchaseEnabled) {
        $("#buy .btn-price, #buy .buy-btn-box").fadeIn();
        $("#buy .btn-buy").hide();
        $("#buy .btn-price").click(function() {
            $("#buy .btn-buy,#buy .buy-btn-box").css("display", "block");
            $("#buy .btn-price").hide()
        })
    }
    $(".character_list.gifting-list > li").show();
    if (b != -1) {
        $(".character_list.gifting-list > li").each(function() {
            if ($(this).data("recipientType") != b) {
                $(this).hide()
            } else {
                if (a === false) {
                    a = $(this)
                }
            }
        });
        if (typeof zs.fn.selectRecipient === "function") {
            if (a !== false) {
                zs.fn.selectRecipient(a);
                $("#buy button.btn").removeClass("btn-disabled");
                $("#buy button.btn").prop("disabled", false)
            } else {
                $("#buy button.btn").addClass("btn-disabled");
                $("#buy button.btn").prop("disabled", true)
            }
        }
    }
    changePseudoSelect(c)
};

function playerSelectDropdownChanged(a) {
    changePseudoSelect(a);
    setMatchingPlayerInList(a)
}

function playerSelectListChanged(a) {
    changeSelectedPlayerInList(a);
    setMatchingPlayerInDropdown(a);
    propagatePlayerSelection(a);
    window.location.href = window.location.href
}

function propagatePlayerSelection(a) {
    $("#slideMenu .account-infos p span.playerName").html(a.data("playerName"));
    $("#slideMenu .account-infos p span.serverName").html(a.data("serverName"))
}

function setMatchingPlayerInDropdown(a) {
    $(".pseudo-dropdown.playerSelection .select-option ul li a").each(function() {
        if ($(this).data("serverId") === a.data("serverId") && $(this).data("playerId") === a.data("playerId")) {
            changePseudoSelect($(this));
            return false
        }
    })
}

function setMatchingPlayerInList(a) {
    $(".character_list.playerSelection li").each(function() {
        if ($(this).data("serverId") === a.data("serverId") && $(this).data("playerId") === a.data("playerId")) {
            changeSelectedPlayerInList($(this));
            return false
        }
    })
}

function changeSelectedPlayerInList(a) {
    a.addClass("chosen").siblings().removeClass("chosen");
    a.find("span.checked").css("display", "block");
    a.siblings().find("span.checked").css("display", "none")
}

function getSelectedValue(a) {
    return $("#" + a).find(".select-input a span.value").html()
}

function calcCustomAmount(d) {
    var a = {
            price: -1,
            mileage: -1
        },
        b = zs.data.variants;
    var e = true;
    for (var c in b) {
        if (e) {
            e = false;
            if (isNaN(Math.round(d / c))) {
                if (console && console.log) {
                    console.log("returning " + a.price)
                }
                return a
            }
        }
        if (c <= d) {
            a.price = b[c].price / c * d;
            a.mileage = b[c].mileage / c * d
        }
    }
    return a
}

function setDisabledBtn(d) {
    var c = $(d + " .btn-price"),
        a = $(d + " .btn-buy"),
        b = c.closest(d);
    if (!c.hasClass("btn-disabled")) {
        c.click(function() {
            var e = $(this).closest(".btn-buy-box");
            e.find(".btn-buy").css("display", "block").end().find(".btn-price").hide()
        });
        a.on("mouseleave", function() {
            var e = $(this).closest(".btn-buy-box");
            window.setTimeout(function() {
                e.find(".btn-price").show().end().find(".btn-buy").hide()
            }, 2000)
        })
    } else {
        b.find(".btn-price").attr("disabled", "disabled").removeClass("btn-price");
        a.remove()
    }
}

function initBtnPrice(d, b) {
    var c = calcCustomAmount(d);
    var e = c.price;
    var a = c.mileage;
    var f = Math.round((parseInt(e) / parseInt(d)));
    if (!b) {
        $("#buy .btn-price, #buy .buy-btn-box").fadeIn();
        $("#buy .btn-buy").hide();
        $("#buy .btn-price").click(function() {
            $("#buy .btn-buy,#buy .buy-btn-box").css("display", "block");
            $("#buy .btn-price").hide()
        })
    }
    $("#buy p span").html(e);
    $("#itemBuy p.bill_sum strong.bill_price").html(e);
    $("#purchaseLink").data("price", e);
    $("#purchaseLink").data("mileage", a);
    $("#itemBuy p.bill_sum strong.bill_amount").text(d);
    $(".unitCount").text(d);
    $("#itemBuy span.coin15px").text(f)
}

function initRoyalSlider(a, b) {
    $(a).royalSlider({
        autoScaleSlider: false,
        addActiveClass: true,
        controlNavigation: "none",
        arrowsNav: true,
        arrowsNavAutoHide: false,
        navigateByClick: false,
        loop: true,
        numImagesToPreload: 3,
        allowCSS3: false,
        controlsInside: false,
        visibleNearby: {
            enabled: true,
            centerArea: b,
            center: false,
            breakpoint: 0,
            breakpointCenterArea: 3,
            navigateByCenterClick: true
        }
    })
}

function scrollBottom() {}

function setSelectedCurrency(d, c) {
    if (!zs.data.selectedCurrencyAction) {
        return
    }
    var a = $(c).attr("data-currency"),
        b = zs.data.selectedCurrencyAction.replace(/selectcurrency\/X/i, "selectcurrency/" + a);
    if ($(c).is(":checked")) {
        $.ajax({
            url: b,
            success: function() {
                window.location.href = window.location.href
            }
        })
    } else {
        d.preventDefault()
    }
}

function setSameHeight(a) {
    var b = 0;
    a.each(function() {
        b = Math.max(b, $(this).height())
    });
    if (b > 0) {
        a.each(function() {
            $(this).css("height", b + "px")
        })
    }
}

function replLocalize(d, c, e, b) {
    e = e || "{$", b = e || "$}";
    for (var a in c) {
        if (c[a]) {
            d = d.replace(new RegExp(e + a + b, "g"), c[a])
        } else {
            d.replace(new RegExp("%%" + a + "%%", "g"), "NO LOCAARG")
        }
    }
    return d
}
zs.fn.cutItemDesc = function(b, a) {
    a = zs.data.textLimit[zs.data.game] || a;
    $(b).each(function() {
        var e = $.trim($(this).html()),
            d = "";
        if (/<br\s*\/?>/i.test(e) && /•/.test(e)) {
            var c = e.split(/<br\s*\/?>/i);
            while (i = c.shift()) {
                if ((d + i).length < a) {
                    d += (/•/.test(i)) ? i.replace(/•\s*/, "<li>") + "</li>" : i + "<br>"
                } else {}
            }
            if (!/<ul/.test(d) && /<li>/.test(d)) {
                d = "<ul>" + d + "</ul>"
            }
        } else {
            if (/•/.test(e)) {
                d += "<ul>" + e.replace(/•\s*/, "<li>") + "</li></ul>"
            } else {
                if (/<li/.test(e)) {
                    d = $.trim(e)
                } else {
                    d = ($.trim(e).length > a) ? $.trim(e).substr(0, a - 10) + "..." : $.trim(e)
                }
            }
        }
        $(this).html(d)
    })
};
zs.fn.cutItemListDesc = function(b, a) {
    $(this).text(function(c, d) {
        return ($.trim(d).length >= a) ? $.trim(d).substr(0, a) + "..." : d
    })
};
zs.fn.initScrollerItems = function(c, r) {
    var k = $(c),
        b, a, n, m, d, p, f, l, q, h, e, o;
    b = k.find(".mCSB_container");
    k.mCustomScrollbar({
        mouseWheelPixels: 200,
        cursorScroll: true,
        axis: "y",
        langDir: "rtl",
        callbacks: {
            onTotalScroll: function() {},
            onTotalScrollOffset: 200
        }
    });

    function g() {
        if (n <= p && b.position().top !== 0) {
            l = b.position().top > -k.height() ? "top" : b.position().top + k.height();
            k.mCustomScrollbar("scrollTo", l, {
                scrollInertia: d
            });
            q.css("height", o)
        } else {
            if (n >= (k.height() - p) && -(Math.floor(b.position().top - k.height())) !== b.height()) {
                k.mCustomScrollbar("scrollTo", b.position().top - k.height(), {
                    scrollInertia: d
                });
                h.css("height", o)
            } else {
                k.mCustomScrollbar("stop");
                e.css("height", 0)
            }
        }
    }

    function j(t) {
        var s = 0;
        if (t.offsetParent) {
            s = t.offsetTop;
            while (t = t.offsetParent) {
                s += t.offsetTop
            }
        }
        return s
    }
};

function updateBalancesAjax() {
    if (!("data" in zs) || !("tokenUrl" in zs.data)) {
        return false
    }
    var a = zs.data.tokenUrl;
    a = a.replace("%controller_method%", "ajax/callback/getbalances");
    $.ajax({
        url: a,
        type: "get",
        dataType: "json",
        success: function(c) {
            if (typeof c != "object") {
                var b;
                try {
                    b = $.parseJSON(c)
                } catch (g) {
                    b = false
                }
            } else {
                b = c
            }
            if (!b || typeof b != "object") {
                return false
            }
            for (var e in b) {
                var j = b[e];
                var h = $("#balances" + e);
                if (!h.length) {
                    continue
                }
                var f = parseInt(h.text());
                var d = new countUp("balances" + e, f, j, 0, 3, {
                    useEasing: true,
                    useGrouping: true,
                    separator: "",
                    decimal: "",
                    prefix: "",
                    suffix: ""
                });
                d.start()
            }
        }
    })
}
$(document).ready(function() {
    $("#header .currency_status [data-toggle=popover]").popover({
        html: true,
        content: function() {
            var g = $(this).attr("data-currency"),
                j = (g === zs.data.selectedCurrency) ? " checked " : "",
                l = replLocalize(zs.data.loca.saveAsDefaultCurrency, {
                    currency: '<span class="currency-name">' + zs.data.currencies[g].loca + "</span>"
                }, "%", "%"),
                f = $('<input type="checkbox" class="float-left" name="favoriteCurrency" data-currency="' + g + '" ' + j + 'onclick="setSelectedCurrency(event, this)" />'),
                h = $('<div class="currency-text"/>').append(l).append("<p>" + zs.data.currencies[g].info + "</p>"),
                k = $("<div />").append(f).append(h);
            return k.html()
        }
    }).on("show.bs.popover", function() {
        $("#header .currency_status .popover-open").popover("hide").removeClass("popover-open");
        $(this).addClass("popover-open")
    }).on("hide.bs.popover", function() {
        $(this).removeClass("popover-open")
    });
    zs.fn.cutItemDesc(".item-text, .item-stats", 100);
    $("body").on("click", function(h) {
        if (!$(".popover-open").exists()) {
            return
        }
        var g = h.target || h.srcElement,
            j = ($(g).is("ul.currency_status li") || $(g).closest("ul.currency_status li").exists()),
            f = ($(g).is(".popover") || $(g).closest(".popover").exists());
        if (!j && !f) {
            $(".popover-open").popover("hide")
        }
    });
    initRoyalSlider(".carousell", zs.module.small ? 0.43 : 0.2999999);
    initRoyalSlider(".carousell-reward", zs.module.small ? 0.52 : 0.44);
    $("#prmoSlider.royalSlider").royalSlider({
        autoPlay: {
            enabled: true,
            pauseOnHover: false,
            delay: 5000
        },
        autoScaleSlider: false,
        arrowsNav: true,
        arrowsNavAutoHide: false,
        fadeinLoadedSlide: false,
        controlNavigationSpacing: 0,
        controlNavigation: "bullets",
        imageScaleMode: "none",
        imageAlignCenter: false,
        blockLoop: true,
        loop: true,
        navigateByClick: false,
        numImagesToPreload: 15,
        transitionType: "fade",
        keyboardNavEnabled: true,
        block: {
            delay: 400
        }
    });
    $(".cancel").click(function() {
        $.fancybox.close()
    });
    setItemHover();
    setDisabledBtn(".only-club");
    if ($("#prmoSlider").exists() && $("#prmoSlider .bContainer").length <= 1) {
        $(".rsBullets").hide()
    }
    customScroll();
    $(".pseudo-dropdown").each(function() {
        pseudoSelect($(this))
    });
    $("a.btn-subcatitem").hover(function() {
        $(this).closest(".has-subnavi").find(".btn-catitem").addClass("active-cat")
    }, function() {
        $(".btn-catitem").removeClass("active-cat")
    });
    $("a.gift-link.ttip").on("click", function() {
        $(".ttip").mouseout()
    });
    cardMargin();
    initFocusClear();
    var b = {
        title: false,
        tpl: {
            closeBtn: '<button title="Close" class="fancybox-item fancybox-close btn-default" href="javascript:;"></button>'
        },
        type: "ajax",
        afterLoad: function(f) {
            $(".cancel").click(function() {
                $.fancybox.close()
            })
        },
        beforeShow: function() {
            initRoyalSlider(".carousell", zs.module.small ? 0.49 : 0.44);
            $(".scrollable_container_fancy").mCustomScrollbar({
                theme: "dark"
            });
            if (!($("html").hasClass("lt-ie7"))) {
                zs.fn.initScrollerItems("#club-membership .scrollable_container", false)
            }
            if ($(".pseudo-dropdown.purchaseSelection").length > 0) {
                pseudoSelect($(".pseudo-dropdown.purchaseSelection"))
            }
            if ($(".pseudo-dropdown.distributionSelection").length > 0) {
                pseudoSelect($(".pseudo-dropdown.distributionSelection"))
            }
            if ($(".pseudo-dropdown.relationType").length > 0) {
                pseudoSelect($(".pseudo-dropdown.relationType"))
            }
        },
        beforeClose: function() {
            updateBalancesAjax();
            if ($("div.fancybox-overlay").hasClass("reload")) {}
        }
    };
    $(".fancybox").fancybox({
        title: false,
        tpl: {
            closeBtn: '<button title="Close" class="fancybox-item fancybox-close btn-default" href="javascript:;"></button>'
        },
        afterLoad: function(h) {
            var f;
            try {
                f = $.parseJSON(h.content)
            } catch (g) {
                f = false
            }
            if (f && f.reload === true) {
                window.location.href = window.location.href;
                return false
            }
            $(".cancel").click(function() {
                $.fancybox.close()
            })
        },
        beforeShow: function() {
            initRoyalSlider(".carousell", zs.module.small ? 0.49 : 0.44);
            $(".scrollable_container_fancy").mCustomScrollbar({
                theme: "dark"
            });
            if (!($("html").hasClass("lt-ie7"))) {
                zs.fn.initScrollerItems("#club-membership .scrollable_container", false)
            }
            if ($(".pseudo-dropdown.purchaseSelection").length > 0) {
                pseudoSelect($(".pseudo-dropdown.purchaseSelection"))
            }
            if ($(".pseudo-dropdown.distributionSelection").length > 0) {
                pseudoSelect($(".pseudo-dropdown.distributionSelection"))
            }
            if ($(".pseudo-dropdown.relationType").length > 0) {
                pseudoSelect($(".pseudo-dropdown.relationType"))
            }
        },
        beforeClose: function() {
            if ($("div.fancybox-overlay").hasClass("reload")) {
                window.location.href = window.location.href
            }
        }
    });
    $(".paymentfancybox").fancybox({
        title: false,
        width: 800,
        height: 602,
        tpl: {
            closeBtn: '<button title="Close" class="fancybox-item fancybox-close btn-default" href="javascript:;"></button>'
        },
        afterLoad: function(h) {
            var f;
            try {
                f = $.parseJSON(h.content)
            } catch (g) {
                f = false
            }
            if (f && f.reload === true) {
                window.location.href = window.location.href;
                return false
            }
            $(".cancel").click(function() {
                $.fancybox.close()
            });
            $(".fancybox-overlay").prop("id", "paymentOverlay");
            $(".fancybox-wrap").prop("id", "paymentOverlayWrap")
        },
        helpers: {
            overlay: {
                closeClick: false
            }
        }
    });
    $(".loginfancybox").fancybox({
        title: false,
        width: 370,
        height: 506,
        tpl: {
            closeBtn: '<button title="Close" class="fancybox-item fancybox-close btn-default" href="javascript:void(0);"></button>'
        },
        beforeLoad: function() {
            var f = $(this.element);
            $(window).on("message", function(g) {
                if (g.originalEvent.data == "reload") {
                    var h = f.data("redirect");
                    if (h.match(/\/ajax\/detail\/displayboxed\//)) {
                        location.href = h.replace(/\?/, "&").replace(/\/ajax\/detail\/displayboxed\//, "/main/start?detail=")
                    } else {
                        location.href = h
                    }
                }
                if (g.originalEvent.data == "close") {
                    $.fancybox.close()
                }
            })
        }
    });
    $(".vaultfancybox").fancybox({
        title: false,
        tpl: {
            closeBtn: '<button title="Close" class="fancybox-item fancybox-close btn-default" href="javascript:void(0);"></button>'
        },
        beforeLoad: function() {}
    });
    if (!($("html").hasClass("lt-ie7"))) {
        zs.fn.initScrollerItems(".content .scrollable_container", true);
        $(".content .scrollable_container").addClass("rendered")
    }
    $(".search-input").keydown(function(f) {
        f = f || window.event;
        if (f.keyCode === 13 || f.which === 13) {
            $(".btn-search").click()
        }
    });
    if (zs.module.small) {
        var a = 130,
            d = $("body").hasClass("rtl"),
            c = $("#searchBar");
        if (d) {
            c.css("left", -50)
        } else {
            c.css("right", -67)
        }
        c.css("visibility", "visible");
        c.hover(function() {
            var g = $(this),
                f = setTimeout(function() {
                    e(g, true, a)
                }, 500);
            g.data("timeout", f)
        }, function() {
            clearTimeout($(this).data("timeout"))
        });
        c.focusout(function() {
            if ($(this).find(".search-input").val().length === 0) {
                e($(this), false, "")
            }
        });

        function e(j, k, f) {
            if (d && $("html").hasClass("lt-ie7")) {
                if (zs.debug) {
                    console.log("no active rtl + ie7")
                }
            } else {
                var g = j.find(".search-input"),
                    h = j.find(".btn-search");
                if (k) {
                    h.css({
                        visibility: "visible"
                    }).animate({
                        opacity: 1
                    }, 600);
                    j.animate({
                        left: d ? 0 : "initial",
                        right: d ? "initial" : 0
                    }, "slow");
                    g.animate({
                        width: f
                    }, "slow", function() {
                        $(this).focus()
                    })
                } else {
                    j.animate({
                        left: d ? -50 : "initial",
                        right: d ? "initial" : -67
                    }, "slow");
                    g.animate({
                        width: "0"
                    }, "slow");
                    h.css({
                        visibility: "hidden"
                    }).animate({
                        opacity: 0
                    }, 600)
                }
            }
        }
    }
    $("table > tbody > tr:odd").addClass("tr-odd");
    $(".character_list > li.chosen, .character_list.gifting-list li.chosen").find("span.checked").css("display", "block");
    $(".character_list > li, .character_list.gifting-list li").click(function() {
        if ($(".character_list").hasClass("playerSelection")) {
            selectPlayer($(this), playerSelectListChanged)
        } else {
            changeSelectedPlayerInList($(this))
        }
    });
    $("#overlayMask").on("click", function() {
        var f = zs.data.dir;
        if (f === "ltr") {
            $("#contentContainer").animate({
                right: "0"
            }, 500, function() {})
        } else {
            $("#contentContainer").animate({
                left: "0"
            }, 500, function() {})
        }
        $("#overlayMask").animate({
            opacity: "0"
        }, 500, function() {
            $(this).hide();
            $("#page").removeClass("slide_menu_active");
            $("#contentContainer").removeClass("open");
            $("#showRightPush").removeClass("active")
        })
    });
    $("#showRightPush").on("click", function() {
        var f = zs.data.dir;
        $(this).toggleClass("active");
        $("#page").toggleClass("slide_menu_active");
        $("#contentContainer").toggleClass("open");
        if ($("#contentContainer").hasClass("open")) {
            $("#overlayMask").show().animate({
                opacity: "0.7"
            }, 500, function() {});
            if (f === "ltr") {
                $("#contentContainer").animate({
                    right: (!zs.module.small) ? "322px" : "222px"
                }, 500, function() {})
            } else {
                $("#contentContainer").animate({
                    left: (!zs.module.small) ? "322px" : "222px"
                }, 500, function() {})
            }
        } else {
            if (f === "ltr") {
                $("#contentContainer").animate({
                    right: "0"
                }, 500, function() {})
            } else {
                $("#contentContainer").animate({
                    left: "0"
                }, 500, function() {})
            }
            $("#overlayMask").animate({
                opacity: "0"
            }, 500, function() {
                $(this).hide()
            })
        }
    });
    $("#prmoSlider").royalSlider("updateSliderSize", true);
    setSameHeight($("#accountContent .row-fluid .inner_box"));
    $(".ttip").tipTip(zs.data.ttip);
    if (zs.data.detailRedirect) {
        $.fancybox.open({
            href: zs.data.detailRedirect,
            title: false
        }, b)
    }
    if ($("#navigation .nav.search").width() >= 720) {
        $("#navigation").addClass("nav-long")
    }

    zs.autocompletecache = {};
    $("input.search-input").autocomplete({
        minLength: 3,
        delay: 300,
        messages: {
            noResults: "",
            results: function() {}
        },
        select: function(b, c) {
            $('input[name="searchString"]').val(c.item.value);
            $(".btn-search").click()
        },
        source: function(e, c) {
            var d = e.term.replace(/#/, "");
            if (d in zs.autocompletecache) {
                c(zs.autocompletecache[d]);
                return
            }
            var b = 12;
            if (zs.module.small) {
                b = 6
            }

			d = d.replace("+", "±");
			
            $.getJSON(shop_url + "search/" + d + "/" + b, {}, function(f) {
                zs.autocompletecache[d] = f;
                c(f)
            });
            $(".ui-helper-hidden-accessible").remove()
        }
    }).autocomplete("instance")._renderItem = function(b, c) {
        return $("<li>").append('<a><img class="ui-icon" src="' + c.image + '" />' + c.name + "</a>").appendTo(b)
    };
});