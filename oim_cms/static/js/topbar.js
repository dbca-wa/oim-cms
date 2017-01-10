var topbar = {
	var: {
		'justopenedmenu': 'closed',
		'justopenedprofilemenu': 'closed',
	},
	toggleAppMenu: function(toggletype) {
		if (topbar.var.justopenedmenu == 'pending' && toggletype == 'outside') {
			return;
		}
		topbar.var.justopenedmenu = 'pending';

		if ($('#appmenu').css('display') == 'none' &&  toggletype != 'outside') {
			$('#appmenu').fadeIn().css("display","block");
			$('#appmenu').css({'position': 'absolute'});
			setTimeout("topbar.var.justopenedmenu = 'open';",500);
		} else {
			topbar.var.justopenedmenu = 'closed';
			$('#appmenu').fadeOut();
		}
	},

	toggleMyProfile: function(toggletype) {

		var authed = ($('#authed').val());

		if (authed != 'True') {
			if (toggletype != 'profileoutside') {
				alert('Sorry you need to be logged in.');
			}
			return;
		}
		if (topbar.var.justopenedprofilemenu == 'pending' && toggletype == 'outside') {
			return;
		}


		topbar.var.justopenedprofilemenu = 'pending';
		if ($('#myprofileinfo').css('display') == 'none' && toggletype != 'profileoutside' ) {
			$('#myprofileinfo').fadeIn().css("display","block");
			setTimeout("topbar.var.justopenedprofilemenu = 'open';",500);

		} else {
			$('#myprofileinfo').fadeOut();
			topbar.var.justopenedprofilemenu = 'closed';
		}
	},
	loadProfileTopBar: function() {
		var authed = ($('#authed').val());

		if (authed == 'True') {
			var profilepic = common.getCookie("profilepicture");
			if (profilepic.length > 0 ) {

				$("#myprofilebutton").attr("src",profilepic);
				$("#myprofileimage2").attr("src",profilepic);
			}


			$.ajax({
				type: 'GET',
				url: '/api/profile/',
				data: {},
				dataType: 'json',
				success: function (jsondata) {
					if (jsondata['objects']['0']['photo'].length > 1) {
						common.setCookie("profilepicture", jsondata['objects']['0']['photo']);
						$("#myprofilebutton").attr("src",jsondata['objects']['0']['photo']);
						$("#myprofileimage2").attr("src",jsondata['objects']['0']['photo']);
					} else {
						common.setCookie("profilepicture","");
					}

				}
			});
		}



		$(window).click(function(e) {
			e = e || window.event;
			e = e.target || e.srcElement;
			if (e.id == 'applist' || e.id == 'appbutton' || e.id == 'apph2' || e.id == 'myprofileinfo' || e.id == 'myprofilebutton'|| e.id == 'myprofileinfosub') {
			} else {
				topbar.toggleAppMenu('outside');
				topbar.toggleMyProfile('profileoutside');
			}

		});

	}





}
$( document ).ready(function() {

	topbar.loadProfileTopBar();
});
