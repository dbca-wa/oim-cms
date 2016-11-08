var validation = { 

	validateURL: function(url) { 
			if (url == null) {
				return true;
			}
			if (url.length == 0 ) {
				return true;
			}
			var RegExp = /(ftp|http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?/;

			if(RegExp.test(url)){
				return true;
			}else{
				return false;
			}

	},
	validateDate: function(dateval) {
		var dtRegex = new RegExp(/\b\d{1,2}[\/]\d{1,2}[\/]\d{4}\b/);
		return dtRegex.test(dateval);
	}

};
