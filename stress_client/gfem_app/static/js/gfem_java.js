function updateParamList(object, table_param, chk_param, fields_update, url){
    $(object).change(function(){
        var frm = $(table_param).serialize();
        var chk = $(chk_param).serialize();
        var data = frm +'&' + chk
        $.ajax({
            url: url,
            data: data,
            dataType: 'html',
            success: function(data) {
            $(fields_update).html(data);
//            $(fields_update).html(data['form'])
            }
          });
        });
    }

function senderFunction(url) {
    var frm = $('#parameters-form');
    $.ajax({
        url: url,
        data: frm.serialize(),
        dataType: 'json',
        success: function (data) {
            alert(data["messages"]);
            $("#forces-table tbody").html(data['html']);
            $("#load-to-file").load(data['load_to_file']);
        },
        error: function (data) {
//            console.log(data);
            alert(data.status + "\n" + data.responseJSON.error);
            $("#added-fields").html(data.responseJSON.form);
        }
      });
    }

function postFunction(url, obj) {
   alert("данные отправлены на сервер");
   var formData = new FormData(obj);
   $.ajax({
       type: 'POST',
       url: url,
       data: formData,
       success: function (data) {
            console.log(data);
            alert(data["messages"]);
            $("#added-fields").html(data);
            $("#added-fields").html(data['form']);
            $("#forces-table tbody").html(data['html']);
            $("#load-to-file").load(data['load_to_file']);
           },
       error: function (data) {
            console.log(data);
            alert(data.status + "\n" + data.responseJSON.error);
            },
       cache: false,
       contentType: false,
       processData: false
   })
}

