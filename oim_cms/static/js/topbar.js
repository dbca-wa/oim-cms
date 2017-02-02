var topbar = {
	var: {
		// Pre defined vairables to use globally.
		'justopenedmenu': 'closed',
		'justopenedprofilemenu': 'closed',
	},
	toggleAppMenu: function(toggletype) {
		// Opens and closes the App Dropdown menu.
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
		// opens and closes the My Profile Dropdown Menu.
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
		// Loads Menu with app list and checks to se the person has a photo and populates the photo on homepage and in the popup window
		var authed = ($('#authed').val());

		if (authed == 'True') {
			var profilepic = common.getCookie("profilepicture");
			if (profilepic) { 
				if (profilepic.length > 0 ) {

					$("#myprofilebutton").attr("src",profilepic);
					$("#myprofileimage2").attr("src",profilepic);
				}
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
		topbar.populateAppMenu();
	

		// This captures mouse click events and check to see where the click came from and ignore the click event if occurs and ignore if it happens with in a dropdown menu.
		$(window).click(function(e) {
			e = e || window.event;
			e = e.target || e.srcElement;
//			alert(e.id);
			if (e.id == 'applist' || e.id == 'appbutton' || e.id == 'apph2' || e.id == 'myprofileinfo' || e.id == 'myprofilebutton'|| e.id == 'myprofileinfosub' || e.id == 'appsdiv' || e.id== 'rightslidermenubutton' || e.id=='meunslidersub' || e.id=='rightslidemenu' || e.id=='oimsearch' || e.id=='menuslider' || e.id =='rightmenuclosebutton') {
				// This check to see a click is from with one of the menu's peventing the menu from closing unless the click comes from outsize the menu unless its a button
			} else {
				topbar.toggleAppMenu('outside');
				topbar.toggleMyProfile('profileoutside');
				if ($('#rightslidemenu').css('display') == 'none') {
				} else {
					topbar.openRightSlideMenu();
				}
			}

		});

	},
	populateAppMenu: function() { 
		// Populates the App Menu with a list of Apps added to json file.
		$.ajax({
			type: 'GET',
			url: '/static/data/appmenu.json',
			data: {},
			dataType: 'json',
			success: function (jsondata) {
				//					alert( jsondata['apps'].length);
				var appmenuhtml = "";
				for(var i = 0; i < jsondata['apps'].length; i++) {
					appmenuhtml += "<div class='appicon' ";
					if (jsondata['apps'][i]['link']) {
						if (jsondata['apps'][i]['link'].length > 3) { 
						    appmenuhtml += " onclick=\"window.location='"+jsondata['apps'][i]['link']+"';\" ";
						}
					}
				    appmenuhtml += ">";
					appmenuhtml += "<div class='appicon-box' >";
					appmenuhtml += "<div class='appicon-img' ><IMG src=\""+jsondata['apps'][i]['image']+"\" ></div>";
					appmenuhtml += "<span class='appicon-text'>"+jsondata['apps'][i]['name']+"</span>";
					appmenuhtml += "</div>";
					appmenuhtml += "</div>";
				}

				$('#applistitems').html(appmenuhtml);
			}
		});


	},
	openRightSlideMenu: function() { 
		    $('#rightslidemenu').animate({width:'toggle'});

	}

}
$( document ).ready(function() {
	topbar.loadProfileTopBar();
	$('#rightslidemenu').hide();
});
