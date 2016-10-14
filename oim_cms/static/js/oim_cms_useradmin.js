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
        $.ajax
            ({
                type: "GET",
            url: "/api/itsystemreq/",
            //json object to sent to the authentication url
            data:'reqid=194' ,
            success: function (resp) {
        
                var data = JSON.parse(resp);
                $('#reqid').val(data[0]['reqid']);
                $('#reqlabval').html(data[0]['reqid']);
                $('#reqname').val(data[0]['reqname']);
                $('#reqdescription').val(data[0]['reqdescription']);
                $('#reqid').val(data[0]['reqid']);
                

                // $('#reqcustodian').val(data[0]['fields']['custodian']); 
                //               $('#reqcustodian').html("<option value='"+escape(data[0]['reqcustodianid'])+"' selected>"+data[0]['labelfield']+"</option>");
                $('#reqcustodian').html("<option value='"+data[0]['reqcustodianid']+"' selected='selected'>"+data[0]['labelfield']+"</option>");
                useradminforms.var.given_name = data[0]['given_name'];
                useradminforms.var.surname = data[0]['surname'];
                useradminforms.var.title = data[0]['title'];
                useradminforms.var.id = data[0]['custodianid'];
                useradminforms.var.labelfield = data[0]['labelfield'];
                useradminforms.var.searchfield = data[0]['searchfield'];

                $('#reqcustodian').selectize({
                    valueField: 'id',
                    labelField: 'labelfield',
                    searchField: 'searchfield',
                    options: [{'given_name': useradminforms.var.given_name, 'surname': useradminforms.var.surname,'title': useradminforms.var.title, 'id': useradminforms.var.id, 'labelfield': useradminforms.var.labelfield, 'searchfield': useradminforms.var.searchfield }],
                    //                    preload: true,
                    //                    items: [{'given_name': useradminforms.var.given_name, 'surname': useradminforms.var.surname,'title': useradminforms.var.title, 'id': useradminforms.var.id } ],
                    //                   lastValue: useradminforms.var.id,
                    create: false,
                    render: {
                        option: function(item, escape) {
                            //  console.log(item);
                            //var orgpeople = [];
                            //for (var i = 0, n = item.length; i < n; i++) {
                            //    orgpeople.push('<span>' + escape(item[i].surname) + '</span>');
                            //}

                            if (item.title != undefined ) {

                                return '<div>' +
                                    //                  '<img src="' + escape(item.posters.thumbnail) + '" alt="">' +
                                    '<span class="title">' +
                                    '<span class="name">' + escape(item.given_name + ' ' + item.surname) + '</span>' +
                                    '<span class="decription" style="display:block;  font-style: italic; font-size: 11px;">&nbsp;&nbsp;' + escape(item.title) + '</span>'+
                                    '</span>' +
                                    //            '<span class="description">' + escape(item.synopsis || 'No synopsis available at this time.') + '</span>' +
                                    //          '<span class="actors">' + (actors.length ? 'Starring ' + actors.join(', ') : 'Actors unavailable') + '</span>' +
                                    '</div>';
                            }
                        }
                    },
                    load: function(query, callback) {
                        if (!query.length) return callback();
                        $.ajax({
                            url: 'http://kens-xenmate-dev:4545/api/peoplelist/',
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

                // Preload some data.




            }
            })


        //        $('#reqcustodian').selectize().setValue(useradminforms.var.id);
        //            $('#reqcustodian').html("<option value='"+data[0]['reqcustodianid']+"' selected='selected'>"+data[0]['labelfield']+"</option>");



        //        $.ajax({ "/api/itsystemreq/", 

        //           success: function( data ) {
        //        $('#reqid').val(data[0]['pk']); 
        //
        //      $('#reqlabval').html(data[0]['pk']);
        //          alert('test');
        //    $('#reqname').val(data[0]['fields']['name']);
        //  $('#reqdescription').val(data[0]['fields']['description']);
        //  $('#reqcustodian').val(data[0]['fields']['custodian']);

        //           console.log(data[0]['feilds']['date_created']);
        //            console.log('Name:'+data[0]['fields']['name']);
        //            $.each( data[0]['fields'], function( key, val ) {
        //              if (key == 'name') {
        //                console.log(data[0]['fields'][key]);
        //                 alert(key+":"+val);
        //        }
        //                    items.push( "<li id='" + key + "'>" + val + "</li>" );
        //         });

        //        });

    },
    saveITSystemReq: function() {
        var csrftoken = $("#csrftoken").val();
        var reqcustodian =  $('#reqcustodian').val();
        var reqname = $('#reqname').val();
        var reqdescription = $('#reqdescription').val();
        var reqid = $('#reqid').val();
        $.ajax({
            url: '/api/saveitreq/',
            type: 'POST',
            dataType: 'html',
            data: {
                csrfmiddlewaretoken: csrftoken,
                reqid: reqid,
                reqcustodian: reqcustodian,
                reqname: reqname,
                reqdescription: reqdescription
            },
            error: function() {
                $('#formnotify').html('<div style="width:50%; padding: 5px; background-color: red;">Error Saving</div>');
            },
            success: function() {
               $('#formnotify').html('<div style="width:50%; padding: 5px; background-color: #1ed925;">Successfully Saved</div>'); 
            }
        });

    }

    };

    useradminforms.ITSystemReq();

    window.onload = function () { 
        $('#reqcustodian').focus();
        $('#reqcustodian-selectized').focus();
        $('#reqname').focus();
    }


    //                      var selectize = $select[0].selectize;
    //                                 selectize.setValue(useradminforms.var.id);

