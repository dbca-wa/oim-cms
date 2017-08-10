var notification = {

	topbar: function(type, message) { 
		var htmlcontent = '';
		 $('#notification-topbar').hide();
		 $('#notification-topbar').html("");
		 document.getElementById('notification-topbar').setAttribute("class", "");
		if (type == 'success') {
			$( '#notification-topbar' ).addClass("topbarsuccess");
			if (message.length > 0 ) { 
			} else {
				message = 'Successfully Completed';
			}
			htmlcontent = "<div><span><b>Success:</b></span><span>&nbsp;&nbsp;"+message+"</span></div>";
		} else if (type == 'error' ) {
			$( '#notification-topbar' ).addClass("topbarerror");
			if (message.length > 0 ) {
			} else {
				message = 'Successfully Completed';
			}
			htmlcontent = "<div><span><b>Error:</b></span><span>&nbsp;&nbsp;"+message+"</span></div>";

		} else if (type == 'warning') { 
			$( '#notification-topbar' ).addClass("topbarwarning");
			if (message.length > 0 ) {
			} else {
				message = 'Successfully Completed';
			}
			htmlcontent = "<div><span><b>Warning:</b></span><span>&nbsp;&nbsp;"+message+"</span></div>";
		}

		$('#notification-topbar').html(htmlcontent);
		$('#notification-topbar').show();
		messageTimeout = setTimeout(function(){$('#notification-topbar').fadeOut('slow');},6000);

	}

}
