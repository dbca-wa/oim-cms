var utils = { 
	scrollToFocus: function(elementid) { 
		$('html, body').animate({
			scrollTop: $("#"+elementid).offset().top - 100
		}, 500);
		$('#'+elementid).focus();

	}



}
