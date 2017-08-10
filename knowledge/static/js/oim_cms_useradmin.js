var useradminforms = {
	var: {
		'given_name': '',
		'surname': '',
		'title' : '',
		'id' : '',
		'labelfield' : '',
		'searchfield' : ''

	},

	ITSystemReq: function() {
		var reqid = $("#reqid").val();
		if (reqid) {
		} else {
			alert('No Request Id Provided');
		}
		$.ajax
			({
				type: "GET",
				url: "/knowledge/itsystemreq/",
				//json object to sent to the authentication url
				data:'reqid='+reqid ,
				success: function (resp) {
					var data = JSON.parse(resp);
					$('#reqid').val(data[0]['reqid']);
					$('#reqlabval').html(data[0]['reqid']);
					$('#reqname').val(data[0]['reqname']);
					$('#reqdescription').val(data[0]['reqdescription']);
					$('#reqid').val(data[0]['reqid']);

					$('#reqnotes').val(data[0]['reqnotes']);
					$('#reqdocumentation').val(data[0]['reqdocumentation']);
					$('#reqtechnical_documentation').val(data[0]['reqtechnical_documentation']);
					$('#reqsystem_reqs').val(data[0]['reqsystem_reqs']);
					$('#reqworkaround').val(data[0]['reqworkaround']);
					$('#reqrecovery_docs').val(data[0]['reqrecovery_docs']);
					$('#reqsystem_creation_date').val(data[0]['reqsystem_creation_date']);
					$('#reqcritical_period').val(data[0]['reqcritical_period']);
					$('#reqalt_processing').val(data[0]['reqalt_processing']);
					$('#reqtechnical_recov').val(data[0]['reqtechnical_recov']);
					$('#reqpost_recovery').val(data[0]['reqpost_recovery']);
					$('#requser_notification').val(data[0]['requser_notification']);
					$('#requnique_evidence').val(data[0]['requnique_evidence']);
					$('#reqpoint_of_truth').val(data[0]['reqpoint_of_truth']);
					$('#reqlegal_need_to_retain').val(data[0]['reqlegal_need_to_retain']);
					//alert(data[0]['reqsystem_creation_date']);
					// $('#reqcustodian').val(data[0]['fields']['custodian']);
					//				 $('#reqcustodian').html("<option value='"+escape(data[0]['reqcustodianid'])+"' selected>"+data[0]['labelfield']+"</option>");
					$('#reqcustodian').html("<option value='"+data[0]['reqcustodianid']+"' selected='selected'>"+data[0]['labelfield']+"</option>");
					useradminforms.var.given_name = data[0]['given_name'];
					useradminforms.var.surname = data[0]['surname'];
					useradminforms.var.title = data[0]['title'];
					useradminforms.var.id = data[0]['custodianid'];
					useradminforms.var.labelfield = data[0]['labelfield'];
					useradminforms.var.searchfield = data[0]['searchfield'];

					var $select = $('#reqcustodian').selectize({
						valueField: 'id',
						labelField: 'labelfield',
						searchField: 'searchfield',
						options: [{'given_name': useradminforms.var.given_name, 'surname': useradminforms.var.surname,'title': useradminforms.var.title, 'id': useradminforms.var.id, 'labelfield': useradminforms.var.labelfield, 'searchfield': useradminforms.var.searchfield }],
						//					  preload: true,
						//					  items: [{'given_name': useradminforms.var.given_name, 'surname': useradminforms.var.surname,'title': useradminforms.var.title, 'id': useradminforms.var.id } ],
						//					 lastValue: useradminforms.var.id,
						create: false,
						render: {
							option: function(item, escape) {
								//	console.log(item);
								//var orgpeople = [];
								//for (var i = 0, n = item.length; i < n; i++) {
								//	  orgpeople.push('<span>' + escape(item[i].surname) + '</span>');
								//}

								if (item.title != undefined ) {

									return '<div>' +
						//					'<img src="' + escape(item.posters.thumbnail) + '" alt="">' +
										'<span class="title">' +
										'<span class="name">' + escape(item.given_name + ' ' + item.surname) + '</span>' +
										'<span class="decription" style="display:block;  font-style: italic; font-size: 11px;">&nbsp;&nbsp;' + escape(item.title) + '</span>'+
										'</span>' +
										//			  '<span class="description">' + escape(item.synopsis || 'No synopsis available at this time.') + '</span>' +
										//			'<span class="actors">' + (actors.length ? 'Starring ' + actors.join(', ') : 'Actors unavailable') + '</span>' +
										'</div>';
								}
							}
						},
						load: function(query, callback) {
							if (!query.length) return callback();
							$.ajax({
								url: '/api/peoplelist/',
								type: 'GET',
								dataType: 'json',
								data: {
									keyword: query,
								page_limit: 10,
								},
								error: function() {
									//callback();
								},
								success: function(res) {
									callback(res);
								}
							});
						}
					});
					var control = $select[0].selectize;
					control.setValue(useradminforms.var.id);


					// Create Selectise Dropdown mens and Set Values
					var ArrayOfDropdownIDs = ["requnique_evidence","reqpoint_of_truth","reqlegal_need_to_retain"];
					var ArrayOfDropdownIDsLength = ArrayOfDropdownIDs.length;
					for (var i = 0; i < ArrayOfDropdownIDsLength; i++) {


						var $select = $('#'+ArrayOfDropdownIDs[i]).selectize({
							delimiter: ',',
							persist: false,
							items: null,
							create: function(input) {
								return {
									value: input,
							text: input
								}
							}
						});
						var control = $select[0].selectize;
						control.setValue(String(data[0][ArrayOfDropdownIDs[i]]));
					}


					$('#reqsystem_creation_date').fdatepicker({
						closeButton: false,
						format: 'dd/mm/yyyy'
					});
					$('#reqsystem_creation_date').css("display", "inline");
					$('#reqsystem_creation_date_picker img').css("border", "none");
					$('#dateicon').on('click', function() {

								$('#reqsystem_creation_date').focus();
					});

				},


			})


		//		  $('#reqcustodian').selectize().setValue(useradminforms.var.id);
		//			  $('#reqcustodian').html("<option value='"+data[0]['reqcustodianid']+"' selected='selected'>"+data[0]['labelfield']+"</option>");



		//		  $.ajax({ "/knowledge/itsystemreq/",

		//			 success: function( data ) {
		//		  $('#reqid').val(data[0]['pk']);
		//
		//		$('#reqlabval').html(data[0]['pk']);
		//			alert('test');
		//	  $('#reqname').val(data[0]['fields']['name']);
		//	$('#reqdescription').val(data[0]['fields']['description']);
		//	$('#reqcustodian').val(data[0]['fields']['custodian']);

		//			 console.log(data[0]['feilds']['date_created']);
		//			  console.log('Name:'+data[0]['fields']['name']);
		//			  $.each( data[0]['fields'], function( key, val ) {
		//				if (key == 'name') {
		//				  console.log(data[0]['fields'][key]);
		//				   alert(key+":"+val);
		//		  }
		//					  items.push( "<li id='" + key + "'>" + val + "</li>" );
		//		   });

		//		  });

	},
	saveITSystemReq: function() {
		var csrftoken = $("#csrftoken").val();
		var reqcustodian =	$('#reqcustodian').val();
		var reqname = $('#reqname').val();
		var reqdescription = $('#reqdescription').val();
		var reqid = $('#reqid').val();

		var reqnotes = $('#reqnotes').val();
		var reqdocumentation = $('#reqdocumentation').val();
		var reqtechnical_documentation = $('#reqtechnical_documentation').val();
		var reqsystem_reqs = $('#reqsystem_reqs').val();
		var reqworkaround = $('#reqworkaround').val();
		var reqrecovery_docs = $('#reqrecovery_docs').val();
		var reqsystem_creation_date = $('#reqsystem_creation_date').val();
		var reqcritical_period = $('#reqcritical_period').val();
		var reqalt_processing = $('#reqalt_processing').val();
		var reqtechnical_recov = $('#reqtechnical_recov').val();
		var reqpost_recovery = $('#reqpost_recovery').val();
		var requser_notification = $('#requser_notification').val();
		var requnique_evidence = $('#requnique_evidence').val();
		var reqpoint_of_truth = $('#reqpoint_of_truth').val();
		var reqlegal_need_to_retain = $('#reqlegal_need_to_retain').val();

		if (validation.validateDate(reqsystem_creation_date) == false) {
			notification.topbar('error', '<b>System Creation Date</B>: Invalid Date Format,   Changes not saved');
			utils.scrollToFocus('reqsystem_creation_date');
			return;
		}

		if (validation.validateURL(reqdocumentation) == false) {
			notification.topbar('error', '<b>Documentation</B>: Invalid URL Format,   Changes not saved');
			utils.scrollToFocus('reqdocumentation');
			return;
		}

		if (validation.validateURL(reqtechnical_documentation) == false) {
			notification.topbar('error', '<b>Technical Documentation</B>: Invalid URL Format,   Changes not saved');
			utils.scrollToFocus('reqtechnical_documentation');
			return;
		}

		if (validation.validateURL(reqrecovery_docs) == false) {
			notification.topbar('error', '<b>Recovery Docs</B>: Invalid URL Format,   Changes not saved');
			utils.scrollToFocus('reqrecovery_docs');
			return;
		}
		// Check form values...
		//		validation.validateURL(



		$.ajax({
			url: '/api/saveitreq/',
		type: 'POST',
		dataType: 'html',
		data: {
			csrfmiddlewaretoken: csrftoken,
		reqid: reqid,
		reqcustodian: reqcustodian,
		reqname: reqname,
		reqdescription: reqdescription,
		reqnotes: reqnotes,
		reqdocumentation: reqdocumentation,
		reqtechnical_documentation: reqtechnical_documentation,
		reqsystem_reqs: reqsystem_reqs,
		reqworkaround: reqworkaround,
		reqrecovery_docs: reqrecovery_docs,
		reqsystem_creation_date: reqsystem_creation_date,
		reqcritical_period: reqcritical_period,
		reqalt_processing: reqalt_processing,
		reqtechnical_recov: reqtechnical_recov,
		reqpost_recovery: reqpost_recovery,
		requser_notification: requser_notification,
		requnique_evidence: requnique_evidence,
		reqpoint_of_truth: reqpoint_of_truth,
		reqlegal_need_to_retain: reqlegal_need_to_retain
		},
		error: function() {
			notification.topbar('error','Error Saving Changes');
			//				$('#formnotify').html('<div style="width:50%; padding: 5px; background-color: red;">Error Saving</div>');
		},
		success: function() {
			notification.topbar('success','Successfully Saved Changes');
			//				$('#formnotify').html('<div style="width:50%; padding: 5px; background-color: #1ed925;">Successfully Saved</div>');
		}
		});

	},
	loadITSystemReq: function() {
		useradminforms.ITSystemReq();

		window.onload = function () {
			$('#reqcustodian').focus();
			$('#reqcustodian-selectized').focus();
			$('#reqname').focus();
		}
	}


	};


	//						var selectize = $select[0].selectize;
	//								   selectize.setValue(useradminforms.var.id);

