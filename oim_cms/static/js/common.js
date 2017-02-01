var common = {
	setCookie: function(key, value) {
		var expires = new Date();
		expires.setTime(expires.getTime() + (1 * 24 * 60 * 60 * 1000));
		document.cookie = key + '=' + value + ';expires=' + expires.toUTCString();
	},

	getCookie: function(key) {
		var keyValue = document.cookie.match('(^|;) ?' + key + '=([^;]*)(;|$)');
		return keyValue ? keyValue[2] : null;
	},
	setContentAreaHeight: function() {

		var maincontentareaheight = $('#maincontentarea').height();
		var contentareaheight= $(window).height();

		if (contentareaheight > maincontentareaheight) {
			contentareaheight = contentareaheight - 156;
		$('#maincontentarea').css({'min-height':contentareaheight+'px'});
		}

	}
}
$( document ).ready(function() {
common.setContentAreaHeight();
common.setCookie('force_template','f6');

});

$(window).resize(function() {
common.setContentAreaHeight();
});
