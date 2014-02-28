var smartfields = {
    setProgress: function($progressbar, percent){
	$progressbar.attr('aria-valuenow', percent)
	    .css('width', percent + "%")
	    .find('span').html(percent + "% Complete");
    }
};

smartfields.FileField = function($elem){
    var $browse_btn = $elem.find('.smartfields-btn-browse').click(function(){return false;});
    var id = $browse_btn.attr('id');
    this.id = id;
    var $delete_btn = $("#" + id + "_delete");
    var $upload_btn = $("#" + id + "_upload");
    var $upload_bar = $("#" + id + "_progressbar_upload");
    var $server_bar = $("#" + id + "_progressbar_server");
    var $current = $("#" + id + "_current");
    var $current_link = $("#" + id + "_link");
    var options = $browse_btn.data('plupload');
    $upload_btn.parent().hide();
    $upload_bar.parent().hide();
    if(!$current.val()){
	if($delete_btn){
	    $delete_btn.parent().hide();
	}
	$current_link.parent().hide();
    }
    $.extend(options, {
	'browse_button': id,
	'container': $elem[0],
	'file_data_name': $browse_btn.attr('name'),
	'multipart_params': {
	    'csrfmiddlewaretoken': $browse_btn.data('csrfToken')
	},
	init: {
	    PostInit: function(up){
		$upload_btn.click(function(){
		    up.start();
		    return false;
		});
		if($delete_btn){
		    $delete_btn.click(function(){
			var post_data = {
			    'csrfmiddlewaretoken': $browse_btn.data('csrfToken')
			};
			post_data[$browse_btn.attr('name') + '-clear'] = "on";
			$.post(options.url, post_data, function(data, textStatus, jqXHR){
			    if(data.status == 'complete'){
				$current.val('');
				$current_link.attr('href', "").parent().hide();
				$delete_btn.parent().hide();
			    }
			});
		    });
		}
	    },
	    FilesAdded: function(up, files){
		$current.val(files[0].name);
		$upload_btn.parent().show();
		$upload_bar.parent().show();
		if($delete_btn){
		    $delete_btn.parent().hide();
		}
		// remove previously selected files from the queue
		up.splice(0, up.files.length-1);
	    },
	    BeforeUpload: function(){
		$upload_btn.parent().hide();
	    },
	    UploadProgress: function(up, file){
		smartfields.setProgress($upload_bar, file.percent);
	    },
	    FileUploaded: function(up, file, data){
		if(data.status == 200){
		    var response = $.parseJSON(data.response);
		    if(response.status == 'complete'){
			if($delete_btn){
			    $delete_btn.parent().show();
			}
			$upload_bar.one('transitionend webkitTransitionEnd oTransitionEnd ' +
					'otransitionend MSTransitionEnd', function() {
					    smartfields.setProgress($upload_bar, 0);
					    $upload_bar.parent().hide();
					});
			$current.val(response.file_name);
			$current_link.attr('href', response.file_url).parent().show();
		    }
		}
	    }
	}
    });

    this.uploader = new plupload.Uploader(options);

    this.uploader.init();
};

smartfields.ImageField = function(){
    smartfields.FileField.apply(this, arguments);
    var $current_preview = $("#" + this.id + "_preview");
    this.uploader.bind('FileUploaded', function(up, file, data){
	if(data.status == 200){
	    var response = $.parseJSON(data.response);
	    if(response.status == 'complete'){
		$current_preview.attr('src', response.file_url);
	    }
	}
    });
};
smartfields.ImageField.prototype = Object.create(smartfields.FileField.prototype);
smartfields.ImageField.constructor = smartfields.ImageField;


$(document).ready(function(){
    $(".smartfields-filefield").each(function(){
	new smartfields.FileField($(this));	
    });
    $(".smartfields-imagefield").each(function(){
	new smartfields.ImageField($(this));	
    });
});
