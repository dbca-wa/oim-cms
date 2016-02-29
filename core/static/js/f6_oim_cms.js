$(document).ready(function () {
    $(document).foundation();
    $.ajaxSetup({
        xhrFields: {
            withCredentials: true
        }
    });

    // force all external links to open in a new tab
    $('a[href^="http"]:not([href*="'+document.location.hostname+'"])').attr("target","_blank");
    // hack for relative links in wagtail to convert /./#anchortag to just #anchortag
    $('a[href*="/./#"]').each(function() {
        var href = $(this).attr("href").replace("/./#", "#");
        $(this).attr("href", href);
    });

    $.urlParam = function(name, url) {
        if (!url) {
         url = window.location.href;
        }
        var results = new RegExp('[\\?&]' + name + '=([^&#]*)').exec(url);
        if (!results) { 
            return undefined;
        }
        return results[1] || undefined;
    }

    // On draft pages highlight top and add edit link, also adjust links to also point to drafts
    if (document.location.pathname.search("/admin/pages") == 0) {
        $('a[href^="/"]').each(function() {
            $(this).attr("href", "/draft"+$(this).attr("href"));
        });
        $(".draft-bg-change").css({"background-color":"rgb(252, 175, 62)"});
        $(".draft-content").html("<a href='"+document.location.pathname.replace("view_draft", "edit")+"'><h2>Draft Preview (Edit)</h2></a>");
    }


    // unbreak wagtail user bar
    window.fixwtub = setInterval(function() {
        $("#wagtail-userbar").removeAttr("style").length && clearInterval(fixwtub);
    }, 100);

    window.loadDatalist = function(listid) {
        if ($("#"+listid).length == 1) { return; }
        if (localStorage.getItem("list_"+listid)) {
            var datalist = $("<datalist/>", {id: listid});
            $.each(JSON.parse(localStorage.getItem("list_"+listid)), function(index, value) {
                $("<option/>").text(value).appendTo(datalist);
            });
            $("body").append(datalist);
        } 
        $.get("/api/options?list=" + listid, function(data) {
            localStorage.setItem("list_"+listid, JSON.stringify(data.objects));
            loadDatalist(listid);
        });
    }

    // form upgrades
    window.upgradeForms = function() {
        $("input[type=date]").fdatepicker({format: "dd/mm/yyyy"}).attr({placeholder: "dd/mm/yyyy"});
        // Find all inputs on the DOM which are bound to a datalist via their list attribute.
        $('input[list]').on("change", function() {
            // use the setCustomValidity function of the Validation API
            // to provide an user feedback if the value does not exist in the datalist
            var value = this.value;
            if ($.grep(this.list.options, function(opt) {return opt.text == value}).length == 1) {
              this.setCustomValidity('');
            } else {
              this.setCustomValidity('Please select a valid value.');
            }
        }).each(function() { 
            if (this.list == null) { loadDatalist($(this).attr("list")); }
        });
    }

    $(document).ready(upgradeForms);

    window._renderHandlebars = function(tmpl, data, callback) {
        tmpl.after(data);
        window[callback]();
    }

    window.renderHandlebars = function() {
        $("script[data-url]").each(function() {
            var tmpl = $(this);
            var url = tmpl.attr("data-url");
            var callback = tmpl.attr("data-onload");
            localforage.getItem(url).then(function(data) {
                if (data) { _renderHandlebars(tmpl, data, callback) }
                $.get(url, function(rawdata) {
                    var data = Handlebars.compile(tmpl.html())(rawdata);
                    localforage.setItem(url, data);
                    if (!data) { _renderHandlebars(tmpl, data, callback) }
                });
            });
        });
    }

    $(document).ready(renderHandlebars);

    var egg = new Egg("up,up,down,down,left,right,left,right,b,a", function() {
        s=document.createElement('script');
        s.src="//static.dpaw.wa.gov.au/static/js/kh.js";
        document.body.appendChild(s)
    }).listen();
});
